import airsim
import time

ALTITUDE = -8.0   # NED, so negative is up


def main():
    client = airsim.MultirotorClient()
    client.confirmConnection()

    client.enableApiControl(True)
    client.armDisarm(True)

    print("Taking off...")
    client.takeoffAsync().join()

    # takeoff only gets a couple of metres up, which isn't enough to clear
    # things in the CARLA map.
    print("Climbing...")
    client.moveToZAsync(z=ALTITUDE, velocity=3.0).join()
    time.sleep(2.0)

    # moveByVelocityZAsync holds the given altitude. Plain moveByVelocity
    # lets it sag while it tilts forward.
    print("Flying forward...")
    client.moveByVelocityZAsync(
        vx=5.0,
        vy=0.0,
        z=ALTITUDE,
        duration=10.0,
        drivetrain=airsim.DrivetrainType.ForwardOnly,
        yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0)
    ).join()

    print("Hovering...")
    client.hoverAsync().join()
    time.sleep(2.0)

    print("Landing...")
    client.landAsync().join()

    client.armDisarm(False)
    client.enableApiControl(False)
    print("Flight complete!")


if __name__ == "__main__":
    main()
