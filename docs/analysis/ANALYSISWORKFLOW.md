---
title: Analysis Workflow
description: Identity tracking, target registration and reproducible analysis of the visual place-learning experiment.
section: Analysis
---
AMADEUS produces identity-labelled tracks. The arena GUI aligns them with the cooling schedule to calculate target-reaching time, occupancy and movement.

Target success requires the tracked centre to remain inside the selected region for three continuous seconds, with movement allowed. Occupancy, path length and speed are calculated over the full trial.

Mark all four regions using the pre-experiment mask beforehand, with the same camera framing, image dimensions and target labels as the recording.

## Reproducibility

Save the reviewed CSV, matching video, target-box JSON and analysis metadata together in folder. The Metadata records IDs, timing, scale, target order and file hashes.

[Download the analysis GUI(../downloads/analysis/fly_target_time_gui_amadeus.py) · [Installation and use](analysisgui.md)
