# Troubleshooting

Every error I actually hit while setting this up, and how I fixed it. Ordered
roughly by when they show up.

---

### `conda` is not recognized

**When:** after installing Miniconda.
**Cause:** Miniconda wasn't added to PATH, or PowerShell wasn't reopened.
**Fix:** Re-run the Miniconda installer and tick "Add Miniconda3 to my PATH." Then
close and open a new PowerShell window (PATH changes only apply to new windows).

---

### `Set-ExecutionPolicy : A parameter cannot be found that matches parameter name 'Bypass'`

**Cause:** wrong syntax — `Bypass` is a *value*, not its own switch.
**Fix:**
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Or, to set it persistently for your user (recommended):
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### `CondaToSNonInteractiveError: Terms of Service have not been accepted`

**When:** running `SetupEnv.ps1` or `conda create`.
**Cause:** recent conda versions require accepting channel Terms of Service first.
**Fix:**
```
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2
```
Then re-run the setup.

---

### `. : File ...\profile.ps1 cannot be loaded because running scripts is disabled`

**When:** opening PowerShell after `conda init powershell`.
**Cause:** `conda init` added a startup snippet to your PowerShell profile, but the
execution policy blocks it from loading — which also stops `conda activate` from
working.
**Fix:**
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Close and reopen PowerShell. The error should be gone and the prompt should show
`(base)`.

---

### airsim install fails: `ModuleNotFoundError: No module named 'numpy'`

**When:** `pip install --no-build-isolation airsim`.
**Cause (subtle):** the error paths point at `...miniconda3\Lib\site-packages`
(the **base** conda), not `...miniconda3\envs\carlaAir\...`. Your shell isn't
actually in the `carlaAir` environment, so pip is using base — where numpy isn't
installed — and airsim's build step can't find it.
**Fix:** make activation actually work, then verify before installing:
```
conda activate carlaAir
python -c "import sys; print(sys.executable)"
```
The path must contain `envs\carlaAir`. If it doesn't, run `conda init powershell`,
reopen PowerShell, and try again. Once it's right, install with `python -m pip ...`
(the `python -m` form guarantees it targets the active env).

---

### `ModuleNotFoundError: No module named 'dotenv'`

**When:** running `gemini_airsim_agent.py`.
**Cause:** `python-dotenv` isn't part of the simulator's environment setup.
**Fix:**
```
python -m pip install python-dotenv
```

---

### `ERROR: Could not find a version that satisfies the requirement googlegenai`

**Cause:** the hyphen got dropped — the package is `google-genai`, not `googlegenai`.
**Fix:**
```
python -m pip install google-genai
```
Type the hyphen manually if pasting keeps eating it.

---

### `.env` crash: `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`

**When:** running the agent, in `load_dotenv()`.
**Cause:** the `.env` file was created with `echo "..." > .env`, which on Windows
writes UTF-16. dotenv expects UTF-8. (The `0xff` is the UTF-16 byte-order mark.)
**Fix:** recreate it as ASCII, and make sure it includes the `GEMINI_API_KEY=`
prefix, not just the key:
```
del .env
Set-Content -Path .env -Value "GEMINI_API_KEY=YOUR_KEY" -Encoding ascii
type .env
```

---

### `404 NOT_FOUND ... model models/gemini-2.5-flash is no longer available`

**Cause:** Google retired that model name for new accounts.
**Fix:** use `gemini-flash-latest` (an alias that stays current). It's set once in
`gemini_airsim_agent.py`. To see what your key can access:
```
python -c "from google import genai; c=genai.Client(); [print(m.name) for m in c.models.list()]"
```

---

### `Vehicle API for 'Drone1' is not available ... this vehicle does not exist`

**When:** running the agent with multiple drones.
**Cause:** the running simulator has no vehicle named `Drone1`. By default CARLA-Air
names its launch drone `SimpleFlight`. Check with:
```
python -c "import airsim; c=airsim.MultirotorClient(port=41451); c.confirmConnection(); print(c.listVehicles())"
```
**Fix:** rename the default drone to `Drone1` in both `settings.json` files (see
Step 7 of the setup guide), then restart the simulator so it loads the new name.
Confirm with `listVehicles()` — it should print `['Drone1']`.

---

### Too many drones spawn (asked for 2, got 3)

**Cause:** CARLA-Air's built-in drone plus the two the script spawns = three, with
the built-in one sitting idle.
**Fix:** rename the built-in drone to `Drone1` (Step 7) so the script only needs to
add `Drone2` and up. After the fix, the script spawns from `Drone2`, and the count
comes out right.

---

### Simulator stutters, crashes on load, or runs very slowly

**Cause:** CARLA-Air is heavy, and traffic (30 vehicles + 50 pedestrians by default)
plus a 4 GB GPU is a lot.
**Fix:** launch with less or no traffic:
```
.\CarlaAir.ps1 Town10HD --no-traffic
.\CarlaAir.ps1 Town10HD --traffic-vehicles 10 --traffic-walkers 10
```
Also keep the laptop plugged in and make sure your NVIDIA drivers are up to date —
outdated drivers are the most common cause of Vulkan launch failures.

---

### Known upstream quirk: switching the follow-camera between drones doesn't work

Noted by the original author too. It's documented CARLA-Air / AirSim behavior, not a
bug in this code. Workaround: press `M` in the sim window for a free camera and fly
around manually.

---

## Local LLM issues (llama / mistral agents)

### `ModuleNotFoundError: No module named 'ollama'`

**Fix:** `python -m pip install ollama` in the `carlaAir` environment.

---

### `Error: couldn't reach the model '...'`

**Cause:** Ollama isn't running, or the model wasn't pulled.
**Fix:** make sure Ollama is installed and running, then:
```
ollama pull llama3.1:8b
ollama pull mistral-nemo
```

---

### The local model drops steps (says "hover then land" but only hovers)

**Cause:** with plain JSON output the model collapses a multi-step request into a
single action object, e.g. `{"action": "hover", "params": {"duration": 3}}`, and
drops the rest. Both the 8B and 12B models did this.
**Fix:** the local agents pass a **JSON schema** (`PLAN_SCHEMA`) to Ollama instead
of `format="json"`, which forces a `{"plan": [...]}` array of steps. This fixed
both models. Prompt tweaks and temperature alone did not. See
[LOCAL_LLM.md](LOCAL_LLM.md) for the full write-up.

---

### The local model runs very slowly / drains the battery

**Cause:** the model runs on the CPU (so the GPU stays free for the simulator),
and CPU inference is heavy. Running the simulator at the same time is a lot of
combined load.
**Fix:** keep the laptop plugged in. A smaller model (`llama3.2:3b`) is much
lighter if speed/heat is a problem. The model only works hard during planning
(before takeoff), not continuously.

---

## Flight behavior issues

### `Vehicle API for 'Drone1' is not available ... this vehicle does not exist`

**Cause:** the running simulator has no `Drone1`. The default drone is named
`SimpleFlight`, and the rename in settings.json can get reset on a sim restart.
**Fix:** the agents now spawn `Drone1` at runtime if it isn't already there
(`runtime_spawn_swarm` starts from Drone1 and skips any that exist), so this
self-heals. If you'd rather have exactly the drones you asked for with no extra
idle one, rename `SimpleFlight` to `Drone1` in both settings.json files and
restart the sim.

---

### The drone flies through the ground when landing / lands in mid-air

**Cause:** the CARLA-Air drone doesn't collide with the terrain — it passes
straight through. So "descend until it hits the ground" never triggers, and
`landAsync` misreads a hovering drone as already landed and stops mid-air.
**Fix:** landing records the drone's ground height *before* takeoff and descends
back to it: fast from high up, a brief settle to kill momentum, then a slow gentle
final approach. The ground height varies by spawn location, so it must be recorded
per run, not assumed to be Z=0.
