import airsim
import time

# Use give_coords.py to find the coordinates of somewhere you want to go.

TARGET_X = 130.0
TARGET_Y = -10.0
TARGET_Z = -2.6   # negative is up, don't set this to 0


def main():
    client = airsim.MultirotorClient()
    client.confirmConnection()

    client.enableApiControl(True)
    client.armDisarm(True)

    # World coordinates, not a distance from where the drone is now.
    print(f"Flying to ({TARGET_X}, {TARGET_Y}, {TARGET_Z})...")
    client.moveToPositionAsync(
        x=TARGET_X,
        y=TARGET_Y,
        z=TARGET_Z,
        velocity=4.0
    ).join()

    print("Arrived. Hovering to settle...")
    client.hoverAsync().join()
    time.sleep(2.0)

    position = client.getMultirotorState().kinematics_estimated.position
    print(f"Actual position: {position.x_val:.1f}, "
          f"{position.y_val:.1f}, {position.z_val:.1f}")

    print("Landing...")
    client.landAsync().join()

    client.armDisarm(False)
    client.enableApiControl(False)
    print("Done.")


if __name__ == "__main__":
    main()
