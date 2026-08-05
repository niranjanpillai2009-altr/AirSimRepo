# Environment & Reproducibility — v0.1-open-loop-baseline

This records the exact environment the open-loop baseline was developed and run
on, so it can be reproduced on another machine. Together with
[SETUP_GUIDE.md](SETUP_GUIDE.md) (install steps) and
[TROUBLESHOOTING.md](TROUBLESHOOTING.md) (fixes for common errors), a new student
should be able to clone this repo and reproduce the baseline flights without help.

Recorded: from the development machine, in the `carlaAir` conda environment.

---

## Hardware

| Component | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096 MiB (4 GB) VRAM |
| GPU driver | 576.80 |
| System RAM | 16 GB (16,866,893,824 bytes ≈ 15.7 GiB) |
| CPU | Intel 11th-gen (Tiger Lake), x86_64 |

A discrete NVIDIA GPU with Vulkan support is required to run the simulator. The
4 GB VRAM is the practical minimum; local LLMs are therefore run on the CPU (see
below) so they don't compete with the simulator for VRAM.

## Operating system

| | |
|---|---|
| OS | Windows 11 (x86_64) |
| Build | 10.0.26200.0 |

## Simulator

| | |
|---|---|
| Simulator | CARLA-Air v0.1.7, Windows 11 x86_64 prebuilt binary |
| Source | https://github.com/louiszengCN/CarlaAir/releases/tag/v0.1.7-win11-x86_64 |
| Underlying | CARLA 0.9.16 + AirSim 1.8.1 in one Unreal Engine 4.26 process |
| Map used | Town10HD |
| Ports | CARLA RPC 2000, AirSim RPC 41451 |

The simulator binary is **not** in this repository (it is ~7 GB and gitignored).
It is downloaded separately; see SETUP_GUIDE.md.

## Python

| | |
|---|---|
| Python | 3.10.20 |
| Environment manager | Miniconda, conda env named `carlaAir` |

The `carla` Python module is the **custom build shipped with CARLA-Air**
(installed from `PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-win_amd64.whl`),
not the public PyPI `carla` package. Its wheel SHA-256 is:
`f255c0fa2c89cdbd7b194546a45c03be45009033e4fece8c7021d13d9727fc33`

## LLMs

**Cloud (Gemini):**
| | |
|---|---|
| Provider | Google Gemini API (via `google-genai`) |
| Model identifier | `gemini-flash-latest` |
| Auth | `GEMINI_API_KEY` in a local `.env` file (not committed) |

**Local (Ollama):**
| | |
|---|---|
| Ollama version | 0.32.5 |
| Model 1 | `llama3.1:8b` — ID `46e0c10c039e`, 4.9 GB |
| Model 2 | `mistral-nemo:latest` — ID `e7e06d107c6c`, 7.1 GB |
| Inference device | CPU (`options={"num_gpu": 0}`), so the GPU stays free for the sim |
| Output format | JSON schema (`PLAN_SCHEMA`) forcing a `{"plan": [...]}` array |

## Environment variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini auth; set in `.env` next to the scripts (gitignored) |

## AirSim settings

`settings.json` (at `~/Documents/AirSim/settings.json`, and the copy the
simulator loads from its `AirSimConfig/`):

- `SimMode`: `Multirotor`
- Vehicles: `SimpleFlight` type. The default vehicle is renamed from
  `SimpleFlight` to `Drone1` so the multi-drone code can address it; additional
  drones (`Drone2`, ...) are added at runtime via `simAddVehicle`.
- Each vehicle carries two cameras (`0` and `front_center`), 1280x960.

Ground level varies by spawn location and the drone does not collide with the
CARLA terrain, so landing records the pre-takeoff Z and descends back to it.

---

## Exact startup procedure (reproduce a baseline flight)

Assumes the install in SETUP_GUIDE.md is complete (simulator downloaded, conda
env created, models pulled, `.env` created, `Drone1` rename applied).

**Two PowerShell windows, both with the env active:**

Window 1 — launch the simulator (from the CarlaAir folder):
```
conda activate carlaAir
.\CarlaAir.ps1 Town10HD
```
Wait until Town10HD is loaded and a drone is visible.

Window 2 — run an agent (from this repo folder):
```
conda activate carlaAir
python test_flight.py          # sanity check: takeoff / forward / land, no LLM
python gemini_airsim_agent.py  # cloud planner
python llama_airsim_agent.py   # local Llama planner
python mistral_airsim_agent.py # local Mistral planner
```
For an agent: enter the number of drones, press Enter once the map is loaded,
then type a plain-English instruction per drone.

**Model comparison (no simulator needed):**
```
python compare_models.py         # standard prompt set
python hard_compare_models.py    # hard prompt set
```

---

## Full package list (`pip freeze`, carlaAir env)

```
airsim==1.8.1
annotated-types==0.7.0
anyio==4.14.2
build==1.5.0
carla @ file:///C:/Users/Owner/Documents/Carla_Air/CarlaAir-v0.1.7-Windows11-x86_64/PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-win_amd64.whl#sha256=f255c0fa2c89cdbd7b194546a45c03be45009033e4fece8c7021d13d9727fc33
certifi==2026.7.22
cffi==2.1.0
charset-normalizer==3.4.9
colorama==0.4.6
cryptography==49.0.0
distro==1.9.0
exceptiongroup==1.3.1
google-auth==2.56.2
google-genai==2.13.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.18
msgpack-python==0.5.6
msgpack-rpc-python==0.4.1
numpy==2.2.6
ollama==0.6.2
opencv-contrib-python==5.0.0.93
opencv-python==5.0.0.93
packaging==26.0
pillow==12.3.0
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==3.0
pydantic==2.13.4
pydantic_core==2.46.4
pygame==2.6.1
pyproject_hooks==1.2.0
python-dotenv==1.2.2
requests==2.34.2
sniffio==1.3.1
tenacity==9.1.4
tomli==2.4.1
tornado==4.5.3
typing-inspection==0.4.2
typing_extensions==4.16.0
urllib3==2.7.0
websockets==16.1.1
```

> Note: the `carla` line points at a local wheel from the CARLA-Air build, so
> `pip install -r` won't reproduce it on another machine — install `carla` from
> the CarlaAir `PythonAPI` as in SETUP_GUIDE.md instead. The Gemini agent also
> needs `python-dotenv` and `google-genai`; the local agents need `ollama`.
