# Model Comparison Results (hard set)

Each prompt run 3 times per model. A plan is *correct* only if
its action sequence exactly matches the expected one (no missing or
extra steps). Timings exclude model load (each model was warmed up).

## Summary

| Model | Correct runs | Fully-correct prompts | Consistent prompts | Avg extra steps | Avg time/plan |
|---|---|---|---|---|---|
| llama3.1:8b | 19/30 (63%) | 6/10 | 8/10 | 0.47 | 10.1s |
| mistral-nemo | 24/30 (80%) | 8/10 | 10/10 | 0.40 | 15.6s |

*Correct runs* = accuracy. *Consistent prompts* = same answer every run (reliability). *Avg extra steps* = hallucinated actions not asked for (lower is better).

## Per-prompt detail

### "fly forward for 3 seconds, then do the exact same thing again"
Expected: `['fly_straight', 'fly_straight']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 0/3 | no | `['fly_straight', 'fly_to', 'land', 'fly_straight', 'fly_to', 'land']` |
| mistral-nemo | 3/3 | yes | `['fly_straight', 'fly_straight']` |

### "go forward for 2 seconds then backward for 2 seconds, and repeat that one more time (four moves total)"
Expected: `['fly_straight', 'fly_backward', 'fly_straight', 'fly_backward']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_straight', 'fly_backward', 'fly_straight', 'fly_backward']` |
| mistral-nemo | 3/3 | yes | `['fly_straight', 'fly_backward', 'fly_straight', 'fly_backward']` |

### "fly a square, 2 seconds per side: forward, then right, then backward, then left"
Expected: `['fly_straight', 'fly_right', 'fly_backward', 'fly_left']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_straight', 'fly_right', 'fly_backward', 'fly_left']` |
| mistral-nemo | 3/3 | yes | `['fly_straight', 'fly_right', 'fly_backward', 'fly_left']` |

### "ascend to 18 meters, cruise straight ahead for 4 seconds, then set it down gently"
Expected: `['set_altitude', 'fly_straight', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['set_altitude', 'fly_straight', 'land']` |
| mistral-nemo | 3/3 | yes | `['set_altitude', 'fly_straight', 'land']` |

### "before flying forward for 5 seconds, hover in place for 2 seconds"
Expected: `['hover', 'fly_straight']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 1/3 | no | `['hover', 'fly_straight']` |
| mistral-nemo | 3/3 | yes | `['hover', 'fly_straight']` |

### "climb higher, then drop back down, then climb up again, and finally land"
Expected: `['set_altitude', 'set_altitude', 'set_altitude', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 0/3 | yes | `['set_altitude', 'fly_backward', 'set_altitude', 'fly_backward', 'land']` |
| mistral-nemo | 0/3 | yes | `['set_altitude', 'hover', 'fly_to', 'set_altitude', 'hover', 'fly_to', 'land']` |

### "hover in place for 2 seconds, three times in a row"
Expected: `['hover', 'hover', 'hover']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['hover', 'hover', 'hover']` |
| mistral-nemo | 3/3 | yes | `['hover', 'hover', 'hover']` |

### "strafe left for 2 seconds, then mirror that move to the right"
Expected: `['fly_left', 'fly_right']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['fly_left', 'fly_right']` |
| mistral-nemo | 3/3 | yes | `['fly_left', 'fly_right']` |

### "take off, do a quick lap: forward 3s, right 3s, back to start, then touch down"
Expected: `['fly_straight', 'fly_right', 'fly_to', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 0/3 | yes | `['fly_to', 'fly_straight', 'fly_right', 'fly_backward', 'land']` |
| mistral-nemo | 0/3 | yes | `['fly_to', 'fly_straight', 'fly_right', 'fly_to', 'land']` |

### "rise up, hover a moment, come back down to start, and settle on the ground"
Expected: `['set_altitude', 'hover', 'fly_to', 'land']`

| Model | Correct | Consistent | Example plan |
|---|---|---|---|
| llama3.1:8b | 3/3 | yes | `['set_altitude', 'hover', 'fly_to', 'land']` |
| mistral-nemo | 3/3 | yes | `['set_altitude', 'hover', 'fly_to', 'land']` |
