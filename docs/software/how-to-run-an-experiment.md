---
title: Run an experiment
description: Prepare the apparatus, record a sequence and stop each independent subsystem.
section: Software
---
Prepare and test each controller, the thermal system and recording equipment before introducing animals.

## Before a run

1. Level the arena, seat the glass cover, clear the underside airflow and check the full camera view.
2. Confirm board programs and serial-port assignments.
3. Verify physical A–D labels against the [wiring table](../hardware/peltier-temperature-system.md#target-controller-pin-map) and display states.
4. Check background and ring sensors. Measure the four Peltier-plate surfaces separately; their controller has no temperature feedback.
5. Wait for stable conditions and record starting temperatures.
6. Set focus, exposure, frame rate and output folder; confirm a test recording saves correctly.


## Start a sequence

Open the Peltier-plate controller at 115200 baud. Start behaviour and temperature recording, then log the command time:

```text
EXP A-D-C-D
```

`EXP A-D-C-D` selects A, D, C, then D. Commands accept 1–16 selections, each cooled for 300 seconds, after a single 300-second preheat. This example lasts 25 minutes.

Mark the first cooling onset in the recording or timing log; analysis trial 1 starts after preheat.

## During a trial

The selected Peltier plate receives a cooling boost followed by a lower hold output. The other Peltier plates heat, with a brief boost after cooling. The display receives the corresponding letter. See the [PWM settings](../hardware/peltier-temperature-system.md#trial-sequence).

Monitor measured temperatures. Stop data collection if the selected Peltier plate fails to cool or the background drifts.

## Experiment record

| Record | Why it matters |
| --- | --- |
| Peltier-plate order and physical mapping | Connects the command letters to locations in the video |
| Preheat start and first cooling start | Aligns video, controller timing and temperature data |
| Original video and actual frame rate | Preserves the time basis for analysis |
| Temperature traces and measurement locations | Shows the conditions experienced during each trial |
| Controller filenames and settings | Identifies the software and outputs used |
| Camera position and spatial calibration | Relates image distances to the 200 mm walking diameter |
| Changes to airflow, mounting or illumination | Helps explain differences between runs |

## Stop and shut down

Send `STOP` to the Peltier-plate controller to disable all four Peltier plates and blank the display. These outputs also stop at sequence completion.

Send `STOP` separately to the background controller. The ring program has no `STOP` command: switch off its heater supply. Confirm loads are off, and let the hot undersides cool before stopping the fan or handling the assembly.

Check the saved recording interval. Retain raw files separately from processed tracks and plots.

[Software checks](checks-and-troubleshooting.md) · [Thermal-camera data format](5-thermal-camera-stream.md)
