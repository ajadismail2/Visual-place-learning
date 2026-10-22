---
title: From video to behavioural measurements
description: Identity tracking, target registration and reproducible analysis of the visual place-learning experiment.
section: Analysis
---
Analysis links each fly's position to the cooling-target schedule. AMADEUS produces identity-labelled tracks; the arena analysis GUI converts those tracks into target-reaching times, occupancy and movement measurements.

<div class="chapter-list" markdown="1">

[**01 · Track the flies with AMADEUS**<br><span>Separate animals from the background, train on the recording and review identities.</span>](tracking.md)

[**02 · Use the arena analysis GUI**<br><span>Load tracks, register the four targets, set the trial schedule and inspect playback.</span>](gui.md)

[**03 · Understand and export the results**<br><span>Definitions, missing data, trajectory plots and reproducible output files.</span>](measurements.md)

</div>

## Two programs, two jobs

| Stage | Input | Output |
| --- | --- | --- |
| AMADEUS tracking | Behaviour video | Positions and identities across frames |
| Tracking review | Overlay video and tracks | Reviewed identities and corrected tracking CSV |
| Arena analysis GUI | Reviewed CSV, matching video, four target regions and trial settings | Behavioural measurements, plots and annotated video |

The analysis GUI does not detect flies or repair their identities. It uses the original AMADEUS coordinates, so identity review comes before behavioural interpretation.

## What the experiment measures

A fly reaches the target when its tracked centre stays inside the selected cool region for **three continuous seconds**, with movement allowed. This produces an individual first-success time for each trial. Occupancy measures time spent in a region, while path length and speed describe movement throughout the trial.

The four regions are registered from the [pre-experiment mask](../cad/index.md#05-cool-spot-registration-mask). The camera framing, image dimensions and target labels must match the recording used for tracking.

## Keep the measurement traceable

Retain the reviewed tracking CSV, matching video, target-box JSON and analysis metadata together. The metadata records the included IDs, timing, scale, target order and file hashes. This makes an exported result traceable to its input and settings.

[Download the analysis GUI, version 1.3.0](../downloads/analysis/fly_target_time_gui_amadeus.py) · [Installation and use](gui.md)
