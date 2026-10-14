---
title: From trajectories to interpretable metrics
description: Explicit target rules, transparent denominators, and a distinction between playback, plotted paths, and full-trial measurements.
---
## Analysis workflow

The latest reviewed AMADEUS analysis file identifies itself as **version 1.3.0**. It reads OBB-centre trajectories, aligns them to the source video, segments trials, assigns target regions, and exports individual and trial-level summaries. The website documents these definitions; it does not run the desktop analysis or claim to have validated its numerical outputs on the experimental dataset.

A typical workflow is: load tracking data → select the exact matching video → set fps and spatial scale → define target boxes → specify trial-1 start and target order → choose included flies → calculate → review → export.

## Target regions and frame browsing

The box editor allows A, B, C, and D to be drawn in any order. Drawing again replaces the selected box; a separate action deletes the selected box. A video slider, step controls, and direct frame entry allow reference frames to be chosen throughout the video while the box coordinates remain fixed in the original image geometry.

All target regions must be finalized before analysis. Overlapping regions should be avoided. In the reviewed source, rectangle edges are inclusive and a shared boundary is assigned by A–D order. Document this convention if positions lie exactly on a shared edge.

## Time to target

**Time to target** is the time from the planned trial start to the first completion of at least 3.0 seconds in the target. Walking inside it is allowed. The dwell entry frame and completion frame are distinct outputs.

For zero-based completion frame f, trial-start frame f₀, and rate r:

**Latency = (f − f₀ + 1) / r**.

An observed position outside the target resets the dwell. Optional missing-frame tolerance can bridge a short unobserved gap only after the same fly is seen inside the target again. The number of bridged samples is retained in the output. There is no positional interpolation.

### Group completion and averages

| Output | Definition | Missing-outcome rule |
| --- | --- | --- |
| Individual latency | First qualifying completion for that ID | Missing if success is not observed |
| Team completion | Maximum individual latency over included IDs | Available only if every included ID succeeds |
| All-fly mean | Arithmetic mean of included individual latencies | Available only if all included IDs succeed |
| Reached count | Number of included IDs with observed success | Always report alongside the population size |

A team event means every included fly has succeeded at least once; it does not require simultaneous occupancy. Excluding flies changes the team being measured and must therefore be reported explicitly.

## Trajectories and locomotion

The analysis separates the path shown in a search plot from the full interval used for movement metrics.

| View or measurement | Behaviour after first success |
| --- | --- |
| Main GUI playback | Continues following the current fly position |
| Per-fly trajectory JPEG | Search path ends at the first completed dwell, including that frame |
| Exported MP4 trail | Trail freezes at success within each trial, according to the reviewed source |
| Movement metrics | Continue over the full available trial |
| Occupancy accumulation | Uses valid observed positions across the analysed interval |

A fly without observed success has a plotted path through the available trial end. Missing positions break the path; plotted segments do not connect across missing samples or trial boundaries.

### Path length

For consecutive valid within-trial positions, step distance is the Euclidean displacement between frames. **Path length in cm = sum of valid step distances in pixels / px-per-cm**. A jump after an identity swap can greatly inflate this value. The current jump flags identify candidates for review but do not automatically remove those displacements.

### Mean speed

For valid consecutive-frame steps, **speed = step distance in cm × fps**. The mean over valid steps describes tracked movement. A separate trial-averaged value divides observed path length by available trial duration. These denominators differ when data are missing, so the two outputs must not share an ambiguous “mean speed” label.

### Time moving

The GUI compares valid step speeds with a configurable movement threshold. **Time moving (%) = 100 × count of valid speeds above the threshold / count of valid steps**. Missing steps are excluded from this denominator. Retain both the threshold and tracking coverage to make comparisons interpretable.

### Occupancy

Occupancy is accumulated from valid frame samples assigned to each region. Each sample contributes 1/fps seconds. The sum of occupied target regions need not equal trial duration because an animal can be outside all boxes or untracked. Cumulative occupancy is different from the first uninterrupted dwell that defines success.

## Choosing the analysed population

The current GUI includes one checkbox per fly. Deselected IDs are omitted from calculations, plots, and exports. Original fly numbers and colours remain unchanged. Recalculate after changing the selection.

Retain imported IDs, included IDs, excluded IDs, and reasons for exclusion. A missing or difficult track should not be excluded simply because its outcome weakens a desired learning trend. Criteria should be defined and applied consistently across sessions.

## Complete, partial, and missing trials

A complete trial covers the planned 300-second interval. A partial trial has only some of those data. A trial with no data must remain distinct from both. The reviewed analysis labels a non-success in a partial interval as “not observed in available data” rather than treating it as an observed 300-second failure.

For a complete trial without success, the latency is censored at the observation limit rather than measured as exactly 300 s. Showing a plotting marker at that limit can be useful only if it is clearly labelled as censored/non-reached and excluded from an ordinary success-latency mean unless a separately justified estimator is used.

## Export record

The current source provides selectable exports and records numerical values without rounding them to display precision. Relevant outputs include per-fly metrics, trial summaries, target-event times, occupancy, trajectory windows, tracking coverage, settings, identity mappings, and input-file SHA-256 hashes. JPEG exports support individual flies and trial-level plots.

A useful export package should retain:

- Exact source video and tracking file identifiers, hashes, and frame relationship.
- Arena scale, target regions, target sequence, trial start, and actual fps.
- Included population, dwell threshold, missing-gap tolerance, and movement threshold.
- Partial-trial status, coverage, flagged jumps, and explicit non-reach outcomes.
- Per-fly data alongside any aggregate plot, with figure axes capped at the relevant trial duration.

## Statistical interpretation

Repeated trials from one fly are paired observations, and flies in the same arena share a session. Choose an analysis appropriate to repeated measures and the experimental unit. A preliminary set of eight trial summaries cannot establish a population learning effect by itself. Avoid manufacturing error bars when replicate-level data and denominators are unavailable.

See [preliminary observations](../research/observations.md) and [validation](validation.md).
