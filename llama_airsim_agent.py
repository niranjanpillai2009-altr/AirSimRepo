import os
import json
import time
import airsim
import ollama

# Same program as gemini_airsim_agent.py, but the planning is done by a local
# Llama model through Ollama instead of Google's Gemini API. No API key, no
# internet needed once the model is downloaded.

ALTITUDE = -8.0        # default flying height, negative is up
SPACING = 4.0          # metres between drones when they spawn
MOVE_SPEED = 5.0       # m/s for directional moves
MODEL = "llama3.1:8b"  # the local model Ollama runs


class AgenticAirSimDrone:
    """One drone. Connects, takes off, and runs a list of actions."""

    def __init__(self, vehicle_name=""):
        self.vehicle_name = vehicle_name
        self.client = None
        # The height the drone holds while moving. set_altitude and fly_to
        # update this so later moves keep whatever height it's at.
        self.altitude = ALTITUDE

    def initialize_systems(self):
        print(f"[{self.vehicle_name}] Connecting...")
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()

        self.client.enableApiControl(True, vehicle_name=self.vehicle_name)
        self.client.armDisarm(True, vehicle_name=self.vehicle_name)

        print(f"[{self.vehicle_name}] Taking off...")
        self.client.takeoffAsync(vehicle_name=self.vehicle_name).join()

        # takeoff barely leaves the ground, so climb to a set height. Every
        # drone starting at the same altitude keeps the swarm level.
        self.client.moveToZAsync(
            z=self.altitude, velocity=3.0, vehicle_name=self.vehicle_name
        ).join()
        print(f"[{self.vehicle_name}] Ready at {self.altitude} m.")

    def get_telemetry(self):
        state = self.client.getMultirotorState(vehicle_name=self.vehicle_name)
        position = state.kinematics_estimated.position
        print(f"  -> [{self.vehicle_name}] X: {position.x_val:.2f}, "
              f"Y: {position.y_val:.2f}, Z: {position.z_val:.2f}")
        return position

    # --- movement helper ---

    def _move(self, vx, vy, duration, label):
        """Fly in a direction for a set time, holding the current altitude.

        MaxDegreeOfFreedom + a fixed yaw of 0 means the drone keeps facing
        the same way (north) and strafes in the requested direction, so
        backward/left/right work without the drone spinning around.
        """
        print(f"  |__ [{self.vehicle_name}] {label} for {duration}s")
        self.client.moveByVelocityZAsync(
            vx=vx,
            vy=vy,
            z=self.altitude,
            duration=duration,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=False, yaw_or_rate=0),
            vehicle_name=self.vehicle_name
        ).join()

        # Velocity commands don't brake on their own.
        self.client.hoverAsync(vehicle_name=self.vehicle_name).join()

    # --- actions ---

    def execute_fly_to(self, x, y, z, speed=4.0):
        print(f"  |__ [{self.vehicle_name}] Flying to ({x}, {y}, {z})")
        self.client.moveToPositionAsync(
            x, y, z, speed, vehicle_name=self.vehicle_name
        ).join()
        self.altitude = z  # hold this height for later moves

    def execute_fly_straight(self, duration):
        self._move(MOVE_SPEED, 0.0, duration, "Forward")

    def execute_fly_backward(self, duration):
        self._move(-MOVE_SPEED, 0.0, duration, "Backward")

    def execute_fly_left(self, duration):
        # y is "right" in NED, so left is negative y.
        self._move(0.0, -MOVE_SPEED, duration, "Left")

    def execute_fly_right(self, duration):
        self._move(0.0, MOVE_SPEED, duration, "Right")

    def execute_hover(self, duration):
        print(f"  |__ [{self.vehicle_name}] Hovering {duration}s")
        self.client.hoverAsync(vehicle_name=self.vehicle_name).join()
        time.sleep(duration)

    def execute_set_altitude(self, z):
        print(f"  |__ [{self.vehicle_name}] Changing altitude to {z}")
        self.altitude = z
        self.client.moveToZAsync(
            z, 3.0, vehicle_name=self.vehicle_name
        ).join()

    def execute_land(self):
        print(f"  |__ [{self.vehicle_name}] Landing...")

        # Stage 1: fast descent while there's height to lose. A position move
        # to 2 m above the take-off ground, at 5 m/s.
        self.client.moveToZAsync(
            -2.0, 5.0, vehicle_name=self.vehicle_name
        ).join()

        # Stage 2: slow, soft final descent. We command a target well below any
        # ground and let the drone ease down until the ground physically stops
        # it. We don't use landAsync here because it misreads the hovering drone
        # as already landed and returns mid-air. Instead we watch the vertical
        # velocity: once the ground halts the descent (velocity ~ 0), it has
        # actually touched down, so we cut the motors to keep it there.
        print(f"  |__ [{self.vehicle_name}] Easing down to the ground...")
        self.client.moveToZAsync(10.0, 0.7, vehicle_name=self.vehicle_name)
        time.sleep(1.0)  # let it start moving before we watch for a stop

        for _ in range(300):  # safety net: give up after ~30 s
            vz = self.client.getMultirotorState(
                vehicle_name=self.vehicle_name
            ).kinematics_estimated.linear_velocity.z_val
            if abs(vz) < 0.05:  # stopped descending = on the ground
                break
            time.sleep(0.1)

        self.client.armDisarm(False, vehicle_name=self.vehicle_name)
        print(f"  |__ [{self.vehicle_name}] Landed.")
        self.altitude = 0.0

    def interpret_user_prompt(self, user_prompt):
        system_instruction = (
            "You are a drone flight planner in a simulator.\n"
            "Turn the user's instruction into a JSON array of actions.\n\n"
            "These are the ONLY actions you may use:\n"
            "1. {'action': 'fly_to', 'params': {'x': float, 'y': float, 'z': float}}\n"
            "2. {'action': 'fly_straight', 'params': {'duration': float}}   (forward)\n"
            "3. {'action': 'fly_backward', 'params': {'duration': float}}\n"
            "4. {'action': 'fly_left', 'params': {'duration': float}}\n"
            "5. {'action': 'fly_right', 'params': {'duration': float}}\n"
            "6. {'action': 'hover', 'params': {'duration': float}}\n"
            "7. {'action': 'set_altitude', 'params': {'z': float}}   (go higher/lower)\n"
            "8. {'action': 'land', 'params': {}}\n\n"
            "RULES:\n"
            f"- Z is altitude and NEGATIVE means up. Normal height is {ALTITUDE}.\n"
            "- To go higher, use set_altitude with a MORE negative z (e.g. -15).\n"
            "  To go lower, use a less negative z (e.g. -3).\n"
            f"- 'go home' / 'return' / 'come back' means fly_to x=0.0, y=0.0, z={ALTITUDE}.\n"
            "- 'land' or 'touch down' means the land action, and it should be last.\n"
            "- Write repeated actions out one at a time. No loops.\n"
            "- Durations are seconds and must be greater than 0.\n"
            "- Include ONE action for EVERY thing the user asks for. Do not skip\n"
            "  any part. If the user mentions landing, you MUST end with a land\n"
            "  action. If they mention going back, you MUST include a fly_to.\n"
            "- ALWAYS reply with a JSON array, even for a single action.\n"
            "- No markdown, no explanation, just the array."
        )

        # Few-shot examples: showing the model real input -> output pairs works
        # far better than describing them, especially for a small local model
        # that otherwise drops parts of the instruction.
        examples = [
            ("hover for 2 seconds then land",
             '[{"action": "hover", "params": {"duration": 2.0}}, '
             '{"action": "land", "params": {}}]'),
            ("fly backward for 3 seconds, return home, then land",
             '[{"action": "fly_backward", "params": {"duration": 3.0}}, '
             '{"action": "fly_to", "params": {"x": 0.0, "y": 0.0, "z": -8.0}}, '
             '{"action": "land", "params": {}}]'),
            ("go up to 15 meters and hover for 3 seconds",
             '[{"action": "set_altitude", "params": {"z": -15.0}}, '
             '{"action": "hover", "params": {"duration": 3.0}}]'),
        ]

        messages = [{"role": "system", "content": system_instruction}]
        for ex_in, ex_out in examples:
            messages.append({"role": "user", "content": ex_in})
            messages.append({"role": "assistant", "content": ex_out})
        messages.append({"role": "user", "content": user_prompt})

        # format="json" constrains the model to valid JSON. temperature 0 makes
        # it follow the instruction literally instead of getting creative and
        # dropping steps, which small models tend to do.
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            format="json",
            options={"num_gpu": 0, "temperature": 0},
        )

        raw = response["message"]["content"]
        data = json.loads(raw)

        actions = extract_actions(data)
        if actions is None:
            raise ValueError(f"No list of actions in the model's reply: {raw}")

        return check_task_list(actions)

    def execute_mission(self, task_list):
        print(f"\n[{self.vehicle_name}] Starting mission, {len(task_list)} steps.")

        for i, step in enumerate(task_list, start=1):
            print(f"\n[{self.vehicle_name} - Step {i}/{len(task_list)}]")
            self.get_telemetry()

            action = step["action"]
            params = step.get("params", {})

            if action == "fly_to":
                self.execute_fly_to(params["x"], params["y"], params["z"])
            elif action == "fly_straight":
                self.execute_fly_straight(params["duration"])
            elif action == "fly_backward":
                self.execute_fly_backward(params["duration"])
            elif action == "fly_left":
                self.execute_fly_left(params["duration"])
            elif action == "fly_right":
                self.execute_fly_right(params["duration"])
            elif action == "hover":
                self.execute_hover(params["duration"])
            elif action == "set_altitude":
                self.execute_set_altitude(params["z"])
            elif action == "land":
                self.execute_land()

        print(f"[{self.vehicle_name}] Mission complete.")

    def shutdown(self):
        if self.client is None:
            return

        try:
            self.client.armDisarm(False, vehicle_name=self.vehicle_name)
            self.client.enableApiControl(False, vehicle_name=self.vehicle_name)
            print(f"[{self.vehicle_name}] Control released.")
        except Exception as e:
            # If control doesn't get released the next run fails and it isn't
            # obvious why.
            print(f"[{self.vehicle_name}] Couldn't release control: {e}")


NEEDED_PARAMS = {
    "fly_to": ["x", "y", "z"],
    "fly_straight": ["duration"],
    "fly_backward": ["duration"],
    "fly_left": ["duration"],
    "fly_right": ["duration"],
    "hover": ["duration"],
    "set_altitude": ["z"],
    "land": [],
}


def extract_actions(data):
    """Pull the list of actions out of whatever shape the model returned.

    Gemini reliably returned a clean array. A local model is messier - it might
    return the array directly, wrap it in an object like {"actions": [...]},
    return a single action object instead of a list, or nest it a level deeper.
    This handles all of those. Returns a list, or None if nothing usable.
    """
    # Already a list of steps.
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # A single action object, not wrapped in a list.
        if "action" in data:
            return [data]

        # A value that is the list we want, e.g. {"actions": [...]}.
        for value in data.values():
            if isinstance(value, list):
                return value

        # The list is nested one level deeper, e.g. {"plan": {"steps": [...]}}.
        for value in data.values():
            if isinstance(value, dict):
                found = extract_actions(value)
                if found is not None:
                    return found

    return None


def check_task_list(task_list):
    """Checks the model's plan before any of it gets flown.

    By the time a mission runs the drone is already in the air, so a missing
    value would crash the script mid-flight with the drone still up. This
    matters even more with a local model, which is messier than Gemini.
    """
    if not isinstance(task_list, list):
        raise ValueError("Expected a list of actions")

    if len(task_list) == 0:
        raise ValueError("The model returned an empty plan")

    for i, step in enumerate(task_list, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"Step {i} isn't in the right format")

        action = step.get("action")
        if action not in NEEDED_PARAMS:
            raise ValueError(f"Step {i}: don't know how to do '{action}'")

        params = step.get("params", {})

        for key in NEEDED_PARAMS[action]:
            if key not in params:
                raise ValueError(f"Step {i} ({action}): missing '{key}'")

            # The model sometimes sends "5" instead of 5.
            try:
                params[key] = float(params[key])
            except (TypeError, ValueError):
                raise ValueError(f"Step {i} ({action}): '{key}' isn't a number")

        if "duration" in params and params["duration"] <= 0:
            raise ValueError(f"Step {i} ({action}): duration must be positive")

    return task_list


def update_airsim_settings(num_agents):
    """Writes settings.json listing every drone.

    AirSim only reads this when the simulator starts, so changing the number
    of drones means restarting the simulator.
    """
    settings_dir = os.path.join(os.path.expanduser("~"), "Documents", "AirSim")
    os.makedirs(settings_dir, exist_ok=True)
    settings_path = os.path.join(settings_dir, "settings.json")

    camera_settings = {
        "0": {
            "CaptureSettings": [
                {"ImageType": 0, "Width": 1280, "Height": 960}
            ],
            "X": 0.5, "Y": 0.0, "Z": 0.1,
            "Pitch": 0.0, "Roll": 0.0, "Yaw": 0.0
        },
        "front_center": {
            "CaptureSettings": [
                {"ImageType": 0, "Width": 1280, "Height": 960, "FOV_Degrees": 90}
            ],
            "X": 0.2, "Y": 0.0, "Z": -0.1,
            "Pitch": 0.0, "Roll": 0.0, "Yaw": 0.0
        }
    }

    vehicles = {}
    for i in range(2, num_agents + 1):
        vehicles[f"Drone{i}"] = {
            "VehicleType": "SimpleFlight",
            "AutoCreate": True,
            "X": i * SPACING,
            "Y": 0.0,
            "Z": 0.0,
            "Cameras": camera_settings
        }

    settings_data = {
        "SeeDocsAt": "https://github.com/microsoft/AirSim/blob/main/docs/settings.md",
        "SettingsVersion": 1.2,
        "SimMode": "Multirotor",
        "Vehicles": vehicles
    }

    with open(settings_path, "w") as f:
        json.dump(settings_data, f, indent=4)

    print(f"[Config] Wrote {num_agents} drone(s) to {settings_path}")


def runtime_spawn_swarm(num_agents):
    """Adds any drones that aren't already in the map.

    Normally does nothing, since update_airsim_settings listed them all. This
    is for adding drones without restarting the simulator.
    """
    if num_agents < 1:
        return

    client = airsim.MultirotorClient()
    client.confirmConnection()

    existing = client.listVehicles()

    for i in range(2, num_agents + 1):
        vehicle_name = f"Drone{i}"

        if vehicle_name in existing:
            continue

        print(f"[Swarm] Adding {vehicle_name}...")
        client.simAddVehicle(
            vehicle_name=vehicle_name,
            vehicle_type="SimpleFlight",
            pose=airsim.Pose(
                airsim.Vector3r(i * SPACING, 0.0, 0.0),
                airsim.Quaternionr(0.0, 0.0, 0.0, 1.0)
            )
        )


def main():
    # Quick check that Ollama is running and the model is available before we
    # get the simulator involved.
    try:
        ollama.show(MODEL)
    except Exception:
        print(f"Error: couldn't reach the model '{MODEL}'.")
        print("Make sure Ollama is installed and running, and that you've run:")
        print(f"    ollama pull {MODEL}")
        return

    try:
        num_agents = int(input("How many drones do you want? "))
    except ValueError:
        print("That needs to be a whole number.")
        return

    if num_agents < 1:
        print("Need at least 1 drone.")
        return

    update_airsim_settings(num_agents)

    print("\nIf you changed the number of drones, restart Town10HD now.")
    input("Press Enter once the map has loaded and you can see the drone...")

    runtime_spawn_swarm(num_agents)

    # All the planning happens before anything takes off, so a bad
    # instruction gets caught while the drones are still on the ground.
    planner = AgenticAirSimDrone()

    fleet_tasks = {}

    for i in range(1, num_agents + 1):
        drone_name = f"Drone{i}"

        while True:
            user_prompt = input(f"What should {drone_name} do? ").strip()

            if not user_prompt:
                print("  Can't be empty.")
                continue

            print(f"[Llama] Planning for {drone_name}...")

            try:
                task_list = planner.interpret_user_prompt(user_prompt)
            except Exception as e:
                print(f"  Couldn't make a plan: {e}")
                print("  Try wording it differently.")
                continue

            print(f"  {len(task_list)} step(s):")
            for step in task_list:
                print(f"    {step['action']} {step.get('params', {})}")

            fleet_tasks[drone_name] = task_list
            break

    if num_agents == 1:
        drone = AgenticAirSimDrone(vehicle_name="Drone1")
        try:
            drone.initialize_systems()
            drone.execute_mission(fleet_tasks["Drone1"])
        finally:
            drone.shutdown()
    else:
        from Multiple import MultiAgentCoordinator

        coordinator = MultiAgentCoordinator(AgenticAirSimDrone, fleet_tasks)
        coordinator.deploy_swarm()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
