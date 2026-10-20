# Jdable Navilo: Autonomous Wheelchair

An open source autonomous wheelchair from [Jdable](https://jdable.org), built to give wheelchair users safer, more independent mobility. Indian patent application published (202511095332 A).

Built by the Jdable team: [@Umang3211](https://github.com/Umang3211), [@Failure-Tech](https://github.com/Failure-Tech) and [@Ventengo1](https://github.com/Ventengo1).

## What's in here

| Folder | What it does |
|---|---|
| `arduino-motor-control/motor-control-serial-comm` | Arduino firmware for two TB6600 stepper drivers with a 4 button joystick for manual override and a serial command protocol, plus a ROS 2 node (`serial_bridge_node.py`) that reads the RTAB-Map occupancy grid and an Intel RealSense depth camera, plans with A* (`AStar.py`), and sends drive commands over serial |
| `arduino-motor-control/one-motor-controll`, `two-motor-controll` | Earlier single and dual motor test sketches |
| `base_auto/api` | Say where you want to go: speech recognition turns a spoken address into a Google Maps walking route and waypoints. Also a CARLA simulator bridge |
| `base_auto/autonomous` | A behavioral cloning CNN trained on the Udacity self driving dataset (`cnnautonomous.pt`) |
| `base_auto/chauffeurnet` | A PyTorch take on ChauffeurNet: bird's eye view rasterizer, feature network and agent RNN (work in progress) |
| `base_auto/obj_detection` | YOLOv5 obstacle detection |
| `base_auto/raspberrypi` | Runs the driving CNN on a Raspberry Pi camera feed |

## Hardware

Wheelchair frame · 2x stepper motors + TB6600 drivers · Arduino · Raspberry Pi · Intel RealSense depth camera · 4 button joystick

## Running pieces of it

```bash
# voice destination -> walking route
pip install googlemaps SpeechRecognition folium
export GOOGLEMAPS_API=your_key
cd base_auto/api && python mapsApi.py

# obstacle detection (weights download automatically)
pip install torch torchvision opencv-python
python base_auto/obj_detection/yolov.py
```

Flash `arduino-motor-control/motor-control-serial-comm/motor.ino` to the Arduino, then run `serial_bridge_node.py` inside a ROS 2 workspace with RTAB-Map running.
