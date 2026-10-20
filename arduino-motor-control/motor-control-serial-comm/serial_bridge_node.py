#!/usr/bin/env python3
import math
import serial
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from geometry_msgs.msg import Twist
import pyrealsense2 as rs

class SerialWheelBridge(Node):
    def __init__(self):
        super().__init__('serial_wheel_bridge')

        # Parameters you should set for your chair
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('wheel_radius_m', 0.10)     # change
        self.declare_parameter('track_width_m', 0.55)      # change (wheel-to-wheel distance)
        self.declare_parameter('steps_per_rev', 200)       # most steppers
        self.declare_parameter('microsteps', 16)           # TB6600 DIP setting
        self.declare_parameter('gear_ratio', 1.0)          # if geared
        self.declare_parameter('max_steps_per_sec', 6000)  # must match Arduino clamp
        self.declare_parameter('send_hz', 30.0)

        port = self.get_parameter('port').value
        baud = int(self.get_parameter('baud').value)

        # Serial open
        self.ser = serial.Serial(port=port, baudrate=baud, timeout=0.0)
        self.get_logger().info(f"Opened serial {port} @ {baud}")

        # Last received cmd_vel
        self.last_twist = Twist()
        self.last_twist.linear.x = 0.0
        self.last_twist.angular.z = 0.0

        self.sub = self.create_subscription(Twist, '/cmd_vel', self.on_cmd_vel, 10)

        send_hz = float(self.get_parameter('send_hz').value)
        self.timer = self.create_timer(1.0 / send_hz, self.on_timer)

    def on_cmd_vel(self, msg: Twist):
        self.last_twist = msg

    def clamp(self, v, lo, hi):
        return max(lo, min(hi, v))

    def twist_to_steps_per_sec(self, v_mps: float, w_rps: float):
        r = float(self.get_parameter('wheel_radius_m').value)
        L = float(self.get_parameter('track_width_m').value)
        steps_per_rev = int(self.get_parameter('steps_per_rev').value)
        microsteps = int(self.get_parameter('microsteps').value)
        gear_ratio = float(self.get_parameter('gear_ratio').value)
        max_sps = int(self.get_parameter('max_steps_per_sec').value)

        # Differential drive wheel linear velocities
        vL = v_mps - (w_rps * L / 2.0)
        vR = v_mps + (w_rps * L / 2.0)

        # Wheel angular vel (rad/s)
        wL = vL / r
        wR = vR / r

        # steps/s = (rad/s) * (rev/rad) * (steps/rev) * microsteps * gear
        steps_per_rad = (steps_per_rev * microsteps * gear_ratio) / (2.0 * math.pi)
        spsL = int(wL * steps_per_rad)
        spsR = int(wR * steps_per_rad)

        spsL = self.clamp(spsL, -max_sps, max_sps)
        spsR = self.clamp(spsR, -max_sps, max_sps)
        return spsL, spsR

    def on_timer(self):
        # Send AUTO command
        v = float(self.last_twist.linear.x)
        w = float(self.last_twist.angular.z)

        spsL, spsR = self.twist_to_steps_per_sec(v, w)
        line = f"AUTO {spsL} {spsR}\n".encode('utf-8')
        try:
            self.ser.write(line)
        except Exception as e:
            self.get_logger().error(f"Serial write failed: {e}")

        # Read any incoming status lines (non-blocking)
        try:
            while self.ser.in_waiting > 0:
                resp = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if resp:
                    # Example: "STAT AUTO 1200 1200" or "STAT MANUAL 0 0"
                    self.get_logger().info(resp)
        except Exception as e:
            self.get_logger().warn(f"Serial read issue: {e}")

class IntelRealSense():
    def __init__(self):
        super.__init__(IntelRealSense, self)
        self.pipeline = rs.pipeline()
        # visual slam
    def stream(self):
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frames()
                if not depth_frame:
                    continue

                width, height = depth_frame.get_width(), depth_frame.get_height()
                dist = depth_frame.get_distance(width//2, height//2)
                print(f"Camera is facing object {dist:.3f} meters away")

        finally:
            self.pipeline.stop()

class MapSubscriber():
    def __init__(self):
        super.__init__("map_subscriber")
        self.subscription = self.create_subscription(
            OccupancyGrid,
            "/rtabmap/map",
            self.map_callback,
            10
        )
    
    def map_callback(self, msg):
        # setting up ROS 2
        # NOTE: ROS Nodes need to be implemented, unable to do on my end
        self.get_logger().info(f"Recieved Map: {msg.info.width}x{msg.info.height}")

def main():
    rclpy.init()
    node = SerialWheelBridge()
    camera = IntelRealSense()
    slam = MapSubscriber()
    try:
        camera.stream()
        rclpy.spin(node)
        rclpy.spin(slam)
    finally:
        try:
            node.ser.close()
            slam.ser.close()
        except Exception:
            pass
        node.destroy_node()
        slam.destory_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
