# Running the Planner on a Local LLM

The original agent uses Google's Gemini API (cloud). This document covers the
local versions, which do the same planning with an open-source model running
entirely on your own machine — no API key, no internet needed once the model is
downloaded.

There are three agent scripts, all otherwise identical:

| Script | Planner | Where it runs |
|---|---|---|
| `gemini_airsim_agent.py` | Gemini (`gemini-flash-latest`) | Google's servers (needs API key) |
| `llama_airsim_agent.py` | Llama 3.1 8B | Your machine, via Ollama |
| `mistral_airsim_agent.py` | Mistral-Nemo 12B | Your machine, via Ollama |

Keeping all three lets you compare a cloud model against two local ones on the
exact same task.

---

## Setup

### 1. Install Ollama

Ollama runs local models and exposes a small local API the script calls.

Download from https://ollama.com/download and install. It runs in the
background (a small icon in the system tray). Verify in a new terminal:

```
ollama --version
```

### 2. Pull the models

```
ollama pull llama3.1:8b
ollama pull mistral-nemo
```

These are ~5 GB and ~7 GB downloads. One-time.

### 3. Install the Python library

In the `carlaAir` environment:

```
python -m pip install ollama
```

(The Gemini agent additionally needs `python-dotenv` and `google-genai` plus a
`.env` API key — see the main setup guide. The local agents need none of that.)

---

## Running

Same as the Gemini agent — sim in one window, agent in another:

```
python llama_airsim_agent.py
python mistral_airsim_agent.py
```

Enter a drone count, press Enter once the map is loaded, and type an instruction
in plain English.

**Expect the first response to be slow.** The model loads into memory on the
first call (a few seconds), then subsequent calls are quicker. The 12B model is
slower than the 8B.

### Why the model runs on the CPU

The scripts pass `options={"num_gpu": 0}`, which forces the model onto the CPU.
This is deliberate: the simulator already uses the whole GPU (4 GB VRAM on the
test machine), and an 8–12B model won't fit alongside it. Running the model on
the CPU keeps the GPU free for the simulator. Planning happens before takeoff,
so the slower CPU speed doesn't affect flight.

This means a local model wants a decent amount of **system RAM** — 16 GB is
comfortable for the 8–12B models plus the simulator.

---

## The action set

The planner can use eight actions. The model is restricted to exactly these:

| Action | Params | Meaning |
|---|---|---|
| `fly_to` | x, y, z | Fly to an absolute coordinate |
| `fly_straight` | duration | Fly forward |
| `fly_backward` | duration | Fly backward |
| `fly_left` | duration | Strafe left |
| `fly_right` | duration | Strafe right |
| `hover` | duration | Hold position |
| `set_altitude` | z | Climb or descend (negative z is higher) |
| `land` | — | Controlled landing to the ground |

Every plan is validated before any drone takes off — unknown actions, missing
parameters, non-numeric values, and non-positive durations are all rejected.

---

## What we learned (the interesting part)

### Local models drop steps unless you force structure

The first attempts failed in a specific way: given "hover for 3 seconds and then
land," both Llama 8B **and** Mistral 12B returned only the hover step and dropped
the land. Prompt tweaks, examples, and lowering the temperature didn't fix it.

Printing the model's raw output showed the real cause. With plain JSON mode, the
model was returning a **single action object**:

```json
{"action": "hover", "params": {"duration": 3.0}}
```

instead of a list. It was collapsing the whole request into one action.

The fix was to stop asking for "json" and instead pass a **JSON schema** that
requires a `{"plan": [ ... ]}` array of steps. This forces the model to produce a
list, so it can't collapse a multi-step request into one action:

```python
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": [ ...the 8 actions... ]},
                    "params": {"type": "object"},
                },
                "required": ["action", "params"],
            },
        }
    },
    "required": ["plan"],
}
```

This fixed **both** models at once. The takeaway: it was never a model-capability
problem — the local models just need stricter output structure than the cloud
model did. The schema's `enum` also prevents the model from inventing actions
that don't exist.

### Gemini vs local, in short

- **Gemini** produced clean multi-step arrays from the start, with no schema
  needed. It's the most forgiving.
- **The local models** needed the JSON schema to be reliable, but once given it,
  both handle the same multi-step instructions correctly.
- **8B vs 12B:** with the schema in place, both work. Without it, both failed
  identically — so for this task, output structure mattered far more than model
  size.

---

## Notes on the flight behavior

A couple of things specific to CARLA-Air that the flight code works around:

- **The drone passes through the ground** (no terrain collision), so "land" can't
  wait for a physical touchdown. Instead each drone records its ground height
  before takeoff and descends back to it: fast from high up, then a slow, gentle
  final approach.
- **Movement holds heading** — backward/left/right strafe without the drone
  spinning to face its direction of travel.
