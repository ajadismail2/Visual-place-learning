---
title: Analysis Workflow
description: Identity tracking, target registration and reproducible analysis of the visual place-learning experiment.
section: Analysis
---
AMADEUS produces identity-labelled tracks. The arena GUI aligns them with the cooling schedule to calculate target-reaching time, occupancy and movement.

<div class="chapter-list" markdown="1">

[**01 · Track the flies with AMADEUS**<br><span>Separate animals from the background, train on the recording and review identities.</span>](tracking-with-amadeus.md)

[**02 · Use the arena analysis GUI**<br><span>Load tracks, register the four targets, set the trial schedule and inspect playback.</span>](using-the-analysis-gui.md)

[**03 · Understand and export the results**<br><span>Definitions, missing data, trajectory plots and reproducible output files.</span>](measurements-and-outputs.md)

</div>

## Workflow

| Stage | Input | Output |
| --- | --- | --- |
| AMADEUS tracking | Behaviour video | Positions and identities across frames |
| Tracking review | Overlay video and tracks | Reviewed identities and corrected tracking CSV |
| Arena analysis GUI | Reviewed CSV, matching video, four target regions and trial settings | Behavioural measurements, plots and annotated video |

Review identities before analysis. The GUI uses AMADEUS coordinates and does not detect flies or correct identities.

## What the experiment measures

Target success requires the tracked centre to remain inside the selected region for **three continuous seconds**, with movement allowed. Occupancy, path length and speed are calculated over the full trial.

Register all four regions using the [pre-experiment mask](../cad/parts-and-step-files.md#05-cool-spot-registration-mask), with the same camera framing, image dimensions and target labels as the recording.

## Reproducibility

Keep the reviewed CSV, matching video, target-box JSON and analysis metadata together. Metadata records IDs, timing, scale, target order and file hashes.

[Download the analysis GUI, version 1.3.0](../downloads/analysis/fly_target_time_gui_amadeus.py) · [Installation and use](analysisgui.md)
