
import carla
import random
import os
import json

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    # Connect to CARLA
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    blueprint_library = world.get_blueprint_library()

    # Choose a random vehicle blueprint (just as placeholder for wheelchair)
    vehicle_bp = blueprint_library.filter("vehicle.*")[0]

    # Spawn vehicle
    spawn_point = random.choice(world.get_map().get_spawn_points())
    vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)

    if vehicle is None:
        print("Failed to spawn vehicle. Try restarting simulation.")
        return

    # --- Attach wheelchair height RGB camera ---
    camera_bp = blueprint_library.find("sensor.camera.rgb")
    camera_bp.set_attribute("image_size_x", "800")
    camera_bp.set_attribute("image_size_y", "600")
    camera_bp.set_attribute("fov", "90")

    camera_transform = carla.Transform(carla.Location(x=0.5, z=1.0))  # ~1m high
    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

    # --- Attach top-down BEV camera ---
    bev_bp = blueprint_library.find("sensor.camera.semantic_segmentation")
    bev_bp.set_attribute("image_size_x", "800")
    bev_bp.set_attribute("image_size_y", "800")

    bev_transform = carla.Transform(carla.Location(z=50), carla.Rotation(pitch=-90))
    bev = world.spawn_actor(bev_bp, bev_transform, attach_to=vehicle)

    # --- Metadata storage ---
    metadata = {"frames": []}

    # Save RGB + BEV frames
    def save_rgb(image):
        filename = f"{OUTPUT_DIR}/rgb_{image.frame}.png"
        image.save_to_disk(filename)
        save_metadata(image.frame)

    def save_bev(image):
        filename = f"{OUTPUT_DIR}/bev_{image.frame}.png"
        image.save_to_disk(filename)

    def save_metadata(frame_id):
        transform = vehicle.get_transform()
        data = {
            "frame": frame_id,
            "x": transform.location.x,
            "y": transform.location.y,
            "z": transform.location.z,
            "yaw": transform.rotation.yaw
        }
        metadata["frames"].append(data)

        # Write continuously so progress is saved
        with open(f"{OUTPUT_DIR}/waypoint_path.json", "w") as f:
            json.dump(metadata, f, indent=2)

    # Listen to sensor streams
    camera.listen(lambda img: save_rgb(img))
    bev.listen(lambda img: save_bev(img))

    print("Collecting data... press Ctrl+C to stop")
    try:
        while True:
            world.wait_for_tick()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping and cleaning up...")
        camera.stop()
        bev.stop()
        vehicle.destroy()

if __name__ == "__main__":
    main()

