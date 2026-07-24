# Setup Guide — Natural-Language Drone Control in CARLA-Air

This is a complete, from-scratch walkthrough for getting this project running on a
fresh Windows machine. It's written from the experience of actually setting it up,
so the parts that commonly go wrong are called out inline. If you hit an error,
check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — every problem I ran into is listed
there with its fix.

**What you'll have at the end:** the CARLA-Air simulator running, and a Python
script that takes a plain-English instruction ("fly up and go forward for 5
seconds"), sends it to an LLM, and flies one or more drones accordingly.

---

## 0. What you need first

- **Windows 11 (x86_64).** There's a Linux build too, but this guide is for Windows.
- **An NVIDIA GPU with Vulkan support.** This is Unreal Engine — it will not run on
  integrated graphics or a Mac. (Developed and tested on an RTX 3050 Ti Laptop,
  4 GB VRAM. It runs, but 4 GB is the low end — see the note on traffic in Step 8.)
- **About 15 GB free disk space** (≈7 GB download + extraction).
- **A Google Gemini API key** (free) — https://aistudio.google.com/apikey.

Everything else (Python, the libraries) gets installed along the way.

---

## 1. Download the CARLA-Air simulator

The simulator is **not** in this repo — it's a ~7 GB prebuilt binary, hosted by
its authors. Get the **Windows** build from the official GitHub release:

**https://github.com/louiszengCN/CarlaAir/releases/tag/v0.1.7-win11-x86_64**

GitHub caps file size at 2 GB, so the zip is split into four parts. Download all
five files into one folder:

- `CarlaAir-v0.1.7-Windows11-x86_64_release.zip.part001`
- `...part002`
- `...part003`
- `...part004`
- `SHA256SUMS.txt`

### Reassemble the parts

Open **Command Prompt** (not PowerShell) in the download folder and run:

```
copy /b CarlaAir-v0.1.7-Windows11-x86_64_release.zip.part001+CarlaAir-v0.1.7-Windows11-x86_64_release.zip.part002+CarlaAir-v0.1.7-Windows11-x86_64_release.zip.part003+CarlaAir-v0.1.7-Windows11-x86_64_release.zip.part004 CarlaAir-v0.1.7-Windows11-x86_64_release.zip
```

That merges the four parts into one zip (~7 GB, takes a minute).

### (Optional) Verify it downloaded cleanly

A corrupted download wastes a lot of time later. In PowerShell:

```
certutil -hashfile CarlaAir-v0.1.7-Windows11-x86_64_release.zip SHA256
```

Compare the result against the hash in `SHA256SUMS.txt`. They should match exactly.

### Extract

Right-click the zip → **Extract All**. Put it on your **main SSD**, not an external
drive. You'll get a `CarlaAir-v0.1.7-Windows11-x86_64` folder containing:

- `CarlaAir.ps1` — the launcher
- `WindowsNoEditor/` — the actual simulator
- `AirSimConfig/` — holds `settings.json` (defines the drones)
- `env_setup/` — `SetupEnv.ps1` and `TestEnv.ps1`
- `PythonAPI/` — the custom `carla` Python module

---

## 2. Install Miniconda

The environment setup uses a conda environment called `carlaAir`.

1. Download **Miniconda (Windows 64-bit)** from
   https://www.anaconda.com/download/success
2. Run the installer, accept defaults, **but on the "Advanced Options" screen tick
   "Add Miniconda3 to my PATH environment variable."** It warns this isn't
   recommended — tick it anyway; it's what makes `conda` work in PowerShell.
3. **Close PowerShell completely and open a new window** (PATH changes only apply to
   new windows). Verify:

```
conda --version
```

If it prints a version, you're good. If it says "not recognized," the PATH option
wasn't ticked — re-run the installer.

---

## 3. Set up the Python environment

Open PowerShell **inside the `CarlaAir-v0.1.7-Windows11-x86_64` folder** (in File
Explorer, click the address bar, type `powershell`, Enter).

### 3a. Allow scripts to run

Windows blocks unsigned scripts by default. Allow them for your user:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Type `Y` if prompted. (Note the exact syntax: `-ExecutionPolicy RemoteSigned`, not
`-RemoteSigned`.)

### 3b. Make conda work with PowerShell

Fresh Miniconda needs one initialization step so `conda activate` works:

```
conda init powershell
```

Then **close and reopen PowerShell** (back in the CarlaAir folder). Your prompt
should now start with `(base)`.

> If you see a red error about `profile.ps1 cannot be loaded` when reopening, that's
> the execution policy — make sure you ran the command in 3a.

### 3c. Accept conda's Terms of Service

Recent conda versions refuse to create environments until you accept the channel
Terms of Service:

```
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2
```

### 3d. Run the setup script

```
.\env_setup\SetupEnv.ps1
```

This creates the `carlaAir` environment and installs `numpy`, `airsim`, `pygame`,
`opencv`, and the custom `carla` module. It takes a few minutes.

> **Important:** the `carla` module here is a *custom build* that ships with the
> simulator. Do **not** `pip install carla` from the internet — it's a different,
> incompatible package and will break things.

### 3e. Verify the environment

```
conda activate carlaAir
python -c "import carla, airsim, pygame, numpy, cv2; print('all good')"
```

If it prints `all good`, the environment is complete — skip to Step 4.

**If `SetupEnv.ps1` stopped early or an import fails**, finish it manually. First
confirm you're actually in the environment:

```
conda activate carlaAir
python -c "import sys; print(sys.executable)"
```

That path **must** contain `envs\carlaAir`. If it shows plain `miniconda3\python.exe`,
your shell isn't in the env and pip will install to the wrong place — re-check
Step 3b. Once the path is right:

```
python -m pip install numpy msgpack-rpc-python
python -m pip install --no-build-isolation airsim
python -m pip install pygame opencv-python pillow
python -m pip install --force-reinstall PythonAPI\carla\dist\carla-0.9.16-cp310-cp310-win_amd64.whl
```

Then re-run the `import` check above.

---

## 4. Get the drone code

Download this repo (green **Code** button → **Download ZIP**, or `git clone`).
You'll get an `AirSimRepo-main` folder with the Python scripts.

### Install the two extra libraries the agent needs

With `carlaAir` active:

```
python -m pip install python-dotenv google-genai
```

(Watch the hyphen in `google-genai` — pasting sometimes drops it, and
`googlegenai` is not a real package.)

---

## 5. Add your Gemini API key

In the `AirSimRepo-main` folder, create a file called `.env` holding your key.

**Use this exact command** — replace `YOUR_KEY` with your actual key:

```
Set-Content -Path .env -Value "GEMINI_API_KEY=YOUR_KEY" -Encoding ascii
```

> **Do not** use `echo "..." > .env`. On Windows that writes the file in UTF-16,
> and the app crashes with a `UnicodeDecodeError`. `Set-Content -Encoding ascii`
> avoids it.

Verify it looks right (full line, no odd characters):

```
type .env
```

It should read `GEMINI_API_KEY=` followed by your key.

---

## 6. Check the model name

Gemini retires old model names over time. This project uses `gemini-flash-latest`,
an alias that always points to the current fast model, so it won't go stale. If you
ever get a `404 ... model is no longer available` error, list what your key can use:

```
python -c "from google import genai; c=genai.Client(); [print(m.name) for m in c.models.list()]"
```

and pick a current `flash` model. The model name is set once inside
`gemini_airsim_agent.py`.

---

## 7. Make the simulator's drone match the code

CARLA-Air spawns one drone at launch. By default it's named `SimpleFlight`, but the
multi-drone code expects the first drone to be `Drone1`. Rename it in **both**
settings files so the two agree (this changes only the drone's name, not its type):

```
(Get-Content "AirSimConfig\settings.json" -Raw) -replace '"SimpleFlight": \{','"Drone1": {' | Set-Content "AirSimConfig\settings.json"
(Get-Content "$env:USERPROFILE\Documents\AirSim\settings.json" -Raw) -replace '"SimpleFlight": \{','"Drone1": {' | Set-Content "$env:USERPROFILE\Documents\AirSim\settings.json"
```

(The first path is inside the CarlaAir folder; run these from there, or use full
paths. If `Documents\AirSim\settings.json` doesn't exist yet, launch the sim once
first — Step 8 — then run the second command.)

---

## 8. Run it

You need **two PowerShell windows**, both with `carlaAir` activated: one runs the
simulator, the other runs the drone scripts.

### Window 1 — launch the simulator

In the **CarlaAir folder**:

```
conda activate carlaAir
.\CarlaAir.ps1 Town10HD
```

Wait until the city fully loads and you can see a drone. It also spawns traffic
(cars + pedestrians), which is the heaviest load on the GPU.

> **On a 4 GB card, if it stutters or crashes on load,** relaunch with less traffic:
> `.\CarlaAir.ps1 Town10HD --no-traffic` (or `--traffic-vehicles 10 --traffic-walkers 10`).

> **Keep the laptop plugged in.** Running the sim under GPU load can drain the
> battery faster than the charger refills it.

### Window 2 — test the connection first

In the **AirSimRepo-main folder**:

```
conda activate carlaAir
python test_flight.py
```

This is a plain takeoff / fly-forward / land with no AI. If the drone flies, your
whole stack works. Confirm the sim knows the drone by the right name:

```
python -c "import airsim; c=airsim.MultirotorClient(port=41451); c.confirmConnection(); print(c.listVehicles())"
```

Should print `['Drone1']`.

### Window 2 — run the agent

```
python gemini_airsim_agent.py
```

1. Enter how many drones (start with `1`).
2. Press Enter once the map is loaded.
3. Type an instruction in plain English, e.g. `fly up and go forward for 5 seconds`.

The script prints the plan it got back from the LLM, then flies it. For multiple
drones, it spawns the extras (Drone2, Drone3…) automatically and flies them at the
same time.

---

## Reference

**Ports:** AirSim `41451`, CARLA `2000`. Different servers — mixing them up gives a
confusing connection error.

**Coordinates (NED):** `x` = forward, `y` = right, `z` = **down**. So altitude is
negative — `z = -8` is 8 metres up. Positive z is underground.

**Simulator camera** (click the window first): `M` unlocks a free camera, arrow keys
move, Page Up/Down change height. The follow-camera only tracks the first drone.

**Coming back later:** everything is saved. Just reopen PowerShell in each folder,
`conda activate carlaAir`, launch the sim, and run your scripts.
