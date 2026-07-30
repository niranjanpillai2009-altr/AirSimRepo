# Natural-Language Drone Control in CARLA-Air

Control one or more simulated drones by typing instructions in plain English. An
LLM turns the instruction into a short list of flight actions, the actions are
validated, and each drone flies its plan — one drone or several at once.

This started as a replication of Ryle Traub's
[AirSimRepo](https://github.com/rylet23/AirSimRepo), rewritten from scratch to
understand it end to end and get it running on a new machine.

## Example

```
$ python gemini_airsim_agent.py

How many drones do you want? 2
Press Enter once the map has loaded...

What should Drone1 do? fly up and go forward for 5 seconds
What should Drone2 do? hover for 5 seconds then fly forward

[Gemini] Planning for Drone1...
  2 step(s): fly_straight {'duration': 5.0}, hover {'duration': 2.0}
[Gemini] Planning for Drone2...
  2 step(s): hover {'duration': 5.0}, fly_straight {'duration': 3.0}

[Coordinator] Done. 2 finished, 0 failed.
```

## How it works

The LLM is restricted to a fixed set of actions (`fly_to`, `fly_straight`,
`fly_backward`, `fly_left`, `fly_right`, `hover`, `set_altitude`, `land`), each
with fixed parameters. Keeping the vocabulary small and structured means the
output is predictable and can be checked before any drone leaves the ground.
Multiple drones run on separate threads so they fly simultaneously.

## Cloud or local — three planners

The same program runs with either a cloud model or a local one:

| Script | Planner | Runs on |
|---|---|---|
| `gemini_airsim_agent.py` | Gemini | Google's servers (needs API key) |
| `llama_airsim_agent.py` | Llama 3.1 8B | Your machine (Ollama, offline) |
| `mistral_airsim_agent.py` | Mistral-Nemo 12B | Your machine (Ollama, offline) |

The local versions need no API key or internet once the model is downloaded. See
**[LOCAL_LLM.md](LOCAL_LLM.md)** for setup, how they compare, and what it took to
get local models producing reliable multi-step plans.

## Getting started

**New to this project? Start with [SETUP_GUIDE.md](SETUP_GUIDE.md)** — a complete
from-scratch walkthrough: downloading the simulator, setting up the environment,
and running your first flight. If you hit an error, [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
lists every problem encountered during setup and its fix.

Quick version, once everything's installed:

```
# Window 1 (CarlaAir folder):   conda activate carlaAir; .\CarlaAir.ps1 Town10HD
# Window 2 (this repo folder):  conda activate carlaAir; python gemini_airsim_agent.py
```

## The scripts

| File | What it does |
|---|---|
| `gemini_airsim_agent.py` | Main program (Gemini) — English → LLM → drone commands, single or multi-drone |
| `llama_airsim_agent.py` | Same, using a local Llama 3.1 8B model via Ollama |
| `mistral_airsim_agent.py` | Same, using a local Mistral-Nemo 12B model via Ollama |
| `Multiple.py` | Runs several drones concurrently, one thread each |
| `test_flight.py` | Plain takeoff / forward / land, no AI. Run this first to check the connection. |
| `test_fly_forward.py` | Fixed-altitude forward flight along the world X axis |
| `move_to_coord.py` | Fly to a coordinate set in the file |
| `give_coords.py` | Print the drone's live position while flying manually (to find coordinates) |

## Requirements

Windows 11, an NVIDIA GPU with Vulkan support, and a Google Gemini API key. Full
details and versions are in the setup guide.

## Notes

- **Coordinates are NED:** `z` is negative going up (`z = -8` is 8 m altitude).
- **Ports:** AirSim `41451`, CARLA `2000`.
- The CARLA-Air simulator binary is not included here — it's downloaded separately
  (see the setup guide). Only the drone-control code lives in this repo.
- Some demo videos of gemini and llama airsim agents working: https://www.mediafire.com/folder/ta9erqa13mxja/AI+AirSim+Vids

## Roadmap

- [x] Replicate the original scripts and get them running
- [x] Multi-drone flight from natural-language instructions
- [x] Swap the cloud LLM (Gemini) for a local open-source model (Llama, Mistral)
- [x] Expanded action set (landing, directional movement, altitude)
- [ ] Add turning / heading control
