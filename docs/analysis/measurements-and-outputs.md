---
title: Measurements and outputs
description: Exact definitions of target success, movement, occupancy and exported files in the supplied analysis GUI.
section: Analysis
---
Measurements are calculated per fly and trial. Exported trajectories stop at first success; movement statistics cover the full available trial.

## First success at the cool target

Success requires the centre to remain inside the target rectangle for three continuous seconds: 72 frames at 24 fps. Movement within the region is allowed. Exit resets dwell; completed success is retained.

Time to target runs from trial start to the **end of the frame completing dwell**. The CSV also records the dwell-start frame.

**Team time** is the latest individual success time; simultaneous occupancy is not required. Team time and the **all-fly mean** remain blank unless every included fly succeeds. Non-reaching flies are not assigned zero or 300 seconds.

## Movement and occupancy

| Measurement | Calculation and interpretation |
| --- | --- |
| Path length | Sum of distances between consecutive valid positions within a trial, divided by px/cm |
| Mean tracked speed | Mean step speed over valid consecutive-frame intervals |
| Median and maximum speed | Distribution summaries of those valid step speeds |
| Trial-averaged speed | Observed path length divided by the available trial duration |
| Time moving | Valid intervals above the selected speed threshold; default 0.2 cm/s |
| Percentage moving | Moving intervals as a percentage of valid movement intervals |
| Occupancy A–D | Observed frames in each region divided by FPS |
| Net displacement | Distance between the first and last valid positions |
| Tracking coverage | Valid positions as a percentage of available trial frames |

Without scale, target timing remains available but physical movement metrics do not. Missing positions are not treated as stationary; paths do not bridge missing frames or trial boundaries.

## Missing data and review

**Missing-data gap = 0** requires strict continuity. A nonzero tolerance bridges short gaps only if the fly reappears inside the target, assuming continuous dwell. Bridged frames are logged separately and excluded from observed occupancy.

Coverage is marked complete, partial or absent. Partial recordings cannot establish complete-trial failure; inspect missing positions even when the full frame span is present.

Jump review flags displacements above the selected threshold (default **0.5 cm/frame**). Flagged points remain in calculations. The GUI does not smooth, interpolate or reassign identities.

## Exports

| Output | Contents |
| --- | --- |
| `per_fly_trial_metrics.csv` | Target success, occupancy, movement, coverage and jump counts for each fly and trial |
| `trial_summary.csv` | Group completion, all-fly mean when available, reached count and trial summaries |
| `framewise_tracks.csv` | Original coordinates, timing, target membership, dwell, speed and validity at each frame |
| `jump_review.csv` | Flagged steps with frame numbers for review |
| `fly_color_key.csv` | Original AMADEUS IDs and display colours |
| `trial_tracks/` and `fly_tracks/` | All-fly and individual trajectories, ending at first success |
| Time-to-target plots | Individual trial plots, combined plots and group summary |
| `analysis_metadata.json` | Settings, definitions, included/excluded IDs, input hash and selected-output hashes |
| `READ_ME.txt` | Workflow and measurement definitions |
| Annotated MP4 | Tracking overlay; exported trails and markers stop at success within each trial |

Plots are **JPEG**, with full-experiment time axes of 0–300 seconds. CSVs retain floating-point values. Exported MP4 trails and markers stop at success; live playback continues.

## Reproducible analysis

Keep the CSV, box JSON, metadata and video together; document exclusions. Changing included flies changes group results. The source includes 47 numerical checks for timing, gaps, trial boundaries and exports; these do not validate tracking identities.

[Download the exact analysis source](../downloads/analysis/fly_target_time_gui_amadeus.py) · [Return to the GUI workflow](analysisgui.md)
