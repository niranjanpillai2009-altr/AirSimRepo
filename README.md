# AirSim Drone Scripts

My version of the CARLA-Air drone scripts. Type an instruction in plain English
and Gemini turns it into drone commands.

## What you need first

Pull the latest code for AirSim and this repo.

You need your own Google Gemini API key. Get one at
https://aistudio.google.com/apikey.

Make a file called `.env` next to the Python scripts with your key in it:

```
GEMINI_API_KEY=your_key_here
```

Install the packages:

```
pip install airsim python-dotenv google-genai
```

## Running the main script

**Step 1.** Open PowerShell and start the script:

```
python .\gemini_airsim_agent.py
```

**Step 2.** Type how many drones you want and press Enter.

**Step 3.** Open the simulator (Town10HD) in a separate window. Wait until the
map finishes loading and you can see the first drone.

**Step 4.** Go back to the terminal and press Enter. Any extra drones get added
to the map side by side.

**Step 5.** Type what you want each drone to do, in plain English:

- Drone 1: "fly up and go straight for 5 seconds"
- Drone 2: "hover for 5 seconds then fly forward"

The plan gets printed before anything flies, so you can check it looks right.

**Step 6.** Watch them fly.

## Camera controls

The camera only follows Drone 1. Inside the simulator window:

- **M** unlocks the camera so you can fly around and see the whole swarm
- **Arrow keys** move around
- **Page Up / Page Down** go higher and lower

Switching the camera between drones doesn't work. Ryle ran into this too.

## The other scripts

Run these to test things separately. None of them need a Gemini key.

| Script | What it does |
|---|---|
| `test_flight.py` | Take off, fly forward, land. Run this first to check the connection works. |
| `test_fly_forward.py` | Same but holds a fixed altitude and flies along the world X axis. |
| `give_coords.py` | Prints the drone's position while you fly it manually. Use it to find coordinates. |
| `move_to_coord.py` | Flies to coordinates set at the top of the file. |

## Notes

**Negative Z is up.** AirSim uses NED coordinates (north, east, down) so the
third number points at the ground. `z = -8` is 8 metres in the air. Positive z
is underground.

**Two different ports.** AirSim is 41451, CARLA is 2000. They're separate
servers and mixing them up gives a confusing error.

**Velocity commands don't stop on their own.** After `moveByVelocityZAsync`
runs out it keeps drifting, so every one is followed by `hoverAsync()` to brake.

## Things I did differently to Ryle

Flagging these in case there was a reason for the original way that I've missed.

- **`settings.json` lists every drone.** In the original,
  `update_airsim_settings` takes a drone count but only ever writes `Drone1` —
  the count isn't used. Every other drone gets added afterwards with
  `simAddVehicle`. Listing them upfront seemed simpler, but maybe runtime
  spawning is deliberate so you can add drones without a restart.
- **The settings path isn't hardcoded.** It pointed at
  `C:\CarlaAir\CarlaAir-v0.1.7-Windows11-x86_64\AirSimConfig`. Mine writes to
  `~/Documents/AirSim`, which is where AirSim looks by default. If the CarlaAir
  build reads it from somewhere else, that's the line to change.
- **Gemini's plan gets checked before takeoff** (`check_task_list`). The
  original reads `params['x']` straight from the reply, so a missing value is a
  `KeyError` partway through a mission with the drone already in the air.
- **All the planning happens before any drone takes off**, so a bad instruction
  gets caught while everything is still on the ground and you can retype it.

## Status

Not flown yet — I don't have the CarlaAir simulator build. Everything here is
from reading the original and the AirSim docs, so it needs testing once I can
run it.
