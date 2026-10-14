---
title: Experimental protocol
description: The current ten-trial training sequence, target mappings, and timing conventions.
---
## Protocol snapshot

| Parameter | Current specification |
| --- | --- |
| Organism | Adult *Drosophila melanogaster* |
| Planned population | 10 flies; actual included IDs recorded per analysis |
| Arena inner diameter | 20 cm |
| Training block | 10 trials × 300 s = 50 min |
| Target order | B → C → D → C → B → A → D → C → B → A |
| Main dataset frame rate | 24 fps; verify per video |
| Success rule | At least 3.0 s continuously inside the selected target; movement permitted |
| Primary latency convention | Time at which the dwell criterion is completed |
| Warm / cool operating targets | Approximately 36 °C / 23–25 °C |

This is the project protocol specification, not a claim that every recording has complete timing, thermal verification, or all ten animals successfully tracked.

## Training schedule

Times below start at the onset of trial 1. The video may contain a pre-training period, so the video frame origin must be set separately.

| Trial | Training interval | Cool target | Manual alias | LED offset |
| --- | --- | --- | --- | --- |
| 1 | 00:00–05:00 | B | T4 | 0 px |
| 2 | 05:00–10:00 | C | T3 | 64 px |
| 3 | 10:00–15:00 | D | T2 | 128 px |
| 4 | 15:00–20:00 | C | T3 | 64 px |
| 5 | 20:00–25:00 | B | T4 | 0 px |
| 6 | 25:00–30:00 | A | T1 | 192 px |
| 7 | 30:00–35:00 | D | T2 | 128 px |
| 8 | 35:00–40:00 | C | T3 | 64 px |
| 9 | 40:00–45:00 | B | T4 | 0 px |
| 10 | 45:00–50:00 | A | T1 | 192 px |

Within each trial, the latest cooling drive is **80 PWM for 5 s → 75 for 10 s → 65 for 10 s → 55 for 275 s**. The [thermal page](../hardware/thermal_control_system.md) explains why this drive sequence must be checked against measured temperature.

## Before acquisition

Confirm arena geometry, floor level, thermal state, display mapping, IR illumination, focus, and the number of animals. Record the cohort and session metadata. Ensure the four physical target regions match A–D in the controller and analysis interface.

Record a clear synchronization event or maintain an auditable relationship between the experiment controller and video. Check the first target change and a later change; an offset at the start can otherwise shift every trial boundary.

The requested schedule includes 10 minutes of `HOT ALL` before and after training. These periods are outside the 50-minute block. If included in the recording, mark their boundaries explicitly; do not count them as additional training trials or assume that every dataset contains them.

## Defining target success

A fly can walk inside the target for the entire qualifying interval. It does **not** have to stop moving. A valid observed position outside the target resets the dwell counter. The success time is the first completion of a qualifying dwell, rather than the first entry that eventually qualifies.

At 24 fps, a 3 s frame-occupancy threshold is **72 samples**. With zero-based frame indices, completion at frame f within a trial starting at f₀ is recorded as **(f − f₀ + 1) / fps** in the reviewed GUI. This convention counts one frame-duration per occupied sample and is explicitly different from subtracting timestamps without the final frame duration.

## Missing observations

The analysis can allow a short tracking gap as an explicit assumption. Such a gap contributes to dwell only after the same ID is observed inside the same target again. A pending gap never triggers success by itself. An observed exit resets the counter even when missing-frame tolerance is enabled.

Report the tolerance with the results and check sensitivity to it. A tracking gap is not a measured continuous stay inside the target. A strict analysis can use zero tolerance.

## Group and individual outcomes

An individual reaches the target when its first qualifying dwell is completed. Group completion is the **maximum of the included individuals' first success times**, available only if every included fly succeeds. The animals need not all occupy the target simultaneously.

The corresponding all-fly mean is available only if every included fly has a success time. If a fly does not reach within the observed trial, retain that outcome rather than silently dropping it from the mean. Missing portions of a video must also be distinguished from an observed complete-trial non-reach.

## After acquisition

Retain the original video, controller record, calibration, target regions, tracking outputs, inclusion set, and analysis settings. Review representative isolated movement, interactions, boundary passages, and all unusually large displacements. The [validation guide](validation.md) lists the current unresolved checks.

A probe or uncoupled control requires its own explicitly documented protocol. Neither should be inferred from this ten-trial schedule.
