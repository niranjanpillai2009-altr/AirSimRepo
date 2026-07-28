# Model Comparison Results

Each prompt run 3 times per model. A plan is *correct* only if
its action sequence exactly matches the expected one (no missing or
extra steps). Timings exclude model load (each model was warmed up).

## Summary

| Model | Correct runs | Fully-correct prompts | Consistent prompts | Avg extra steps | Avg time/plan |
|---|---|---|---|---|---|
| llama3.1:8b | 30/30 (100%) | 10/10 | 10/10 | 0.00 | 7.1s |
| mistral-nemo | 30/30 (100%) | 10/10 | 10/10 | 0.00 | 10.3s |

*Correct runs* = accuracy. *Consistent prompts* = same answer every run (reliability). *Avg extra steps* = hallucinated actions not asked for (lower is better).

## Per-prompt detail

### "fly forward for 5 seconds"
Expected: `['fly_straight']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_straight']` |
| mistral-nemo | 3/3 | yes | `['fly_straight']` |

### "hover for 3 seconds then land"
Expected: `['hover', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['hover', 'land']` |
| mistral-nemo | 3/3 | yes | `['hover', 'land']` |

### "fly backward for 4 seconds then land"
Expected: `['fly_backward', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_backward', 'land']` |
| mistral-nemo | 3/3 | yes | `['fly_backward', 'land']` |

### "fly left for 3 seconds then fly right for 3 seconds"
Expected: `['fly_left', 'fly_right']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_left', 'fly_right']` |
| mistral-nemo | 3/3 | yes | `['fly_left', 'fly_right']` |

### "fly forward for 5 seconds then return home"
Expected: `['fly_straight', 'fly_to']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_straight', 'fly_to']` |
| mistral-nemo | 3/3 | yes | `['fly_straight', 'fly_to']` |

### "go up to 20 meters then hover for 3 seconds"
Expected: `['set_altitude', 'hover']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['set_altitude', 'hover']` |
| mistral-nemo | 3/3 | yes | `['set_altitude', 'hover']` |

### "hover for 2 seconds, fly forward for 4 seconds, then land"
Expected: `['hover', 'fly_straight', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['hover', 'fly_straight', 'land']` |
| mistral-nemo | 3/3 | yes | `['hover', 'fly_straight', 'land']` |

### "fly backward for 3 seconds, return home, and land"
Expected: `['fly_backward', 'fly_to', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_backward', 'fly_to', 'land']` |
| mistral-nemo | 3/3 | yes | `['fly_backward', 'fly_to', 'land']` |

### "go up to 15 meters, fly forward for 5 seconds, then land"
Expected: `['set_altitude', 'fly_straight', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['set_altitude', 'fly_straight', 'land']` |
| mistral-nemo | 3/3 | yes | `['set_altitude', 'fly_straight', 'land']` |

### "fly right for 2 seconds, hover for 2 seconds, then come back and land"
Expected: `['fly_right', 'hover', 'fly_to', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_right', 'hover', 'fly_to', 'land']` |
| mistral-nemo | 3/3 | yes | `['fly_right', 'hover', 'fly_to', 'land']` |
