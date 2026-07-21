import airsim
import time

# Prints the drone's position while you fly it by hand, so you can note down
# coordinates for other scripts. Doesn't take API control, so manual flying
# still works.


def main():
    client = airsim.MultirotorClient()
    client.confirmConnection()

    print("\nFly the drone manually. Coordinates update below.")
    print("Ctrl+C to stop.\n")
    print(f"{'X (fwd/back)':<18}{'Y (left/right)':<18}{'Z (altitude)':<18}")
    print("-" * 54)

    try:
        while True:
            state = client.getMultirotorState()
            position = state.kinematics_estimated.position

            # end="\r" overwrites the same line instead of printing
            # thousands of them.
            print(f"{position.x_val:<18.3f}"
                  f"{position.y_val:<18.3f}"
                  f"{position.z_val:<18.3f}", end="\r")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
