import airsim
import time

# AirSim is on 41451, CARLA is on 2000.
client = airsim.MultirotorClient(ip="127.0.0.1", port=41451)
client.confirmConnection()
print("Connected.")

client.enableApiControl(True)
client.armDisarm(True)

print("Taking off...")
client.takeoffAsync().join()
time.sleep(3)

forward_speed = 3.0
fly_duration = 5.0

# Body frame, so vx is forward relative to the way the drone is facing.
print("Flying forward...")
client.moveByVelocityBodyFrameAsync(
    vx=forward_speed,
    vy=0,
    vz=0,
    duration=fly_duration
).join()

# Velocity commands don't brake, they just run out. Hovering stops it.
print("Stopping...")
client.hoverAsync().join()
time.sleep(2)

print("Landing...")
client.landAsync().join()

client.armDisarm(False)
client.enableApiControl(False)
print("Flight complete!")
