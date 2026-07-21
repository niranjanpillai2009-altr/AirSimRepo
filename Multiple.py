import threading
import time


class MultiAgentCoordinator:
    """Flies several drones at the same time, one thread each."""

    def __init__(self, drone_class, tasks_by_drone):
        # drone_class is passed in rather than imported, because
        # gemini_airsim_agent.py imports this file. Importing back from
        # there would be a circular import.
        self.drone_class = drone_class
        self.tasks_by_drone = tasks_by_drone
        self.threads = []
        self.errors = {}

    def fly_one_drone(self, drone_name, task_list):
        drone = self.drone_class(vehicle_name=drone_name)

        try:
            drone.initialize_systems()
            drone.execute_mission(task_list)
        except Exception as e:
            # Errors inside a thread don't reach the main program, so they'd
            # disappear silently without this.
            print(f"\n[{drone_name}] Error: {e}")
            self.errors[drone_name] = str(e)
        finally:
            # If control doesn't get released the next run can't take it.
            drone.shutdown()

    def deploy_swarm(self):
        print(f"\n[Coordinator] Starting {len(self.tasks_by_drone)} drones...")

        for drone_name, task_list in self.tasks_by_drone.items():
            t = threading.Thread(
                target=self.fly_one_drone,
                args=(drone_name, task_list),
                name=f"Thread-{drone_name}"
            )
            self.threads.append(t)
            t.start()

            # Opening all the connections at once makes some of them fail.
            time.sleep(0.25)

        # Without this the main program ends while the drones are flying.
        for t in self.threads:
            t.join()

        finished = len(self.tasks_by_drone) - len(self.errors)
        print(f"\n[Coordinator] Done. {finished} finished, {len(self.errors)} failed.")

        for drone_name, error in self.errors.items():
            print(f"  {drone_name}: {error}")
