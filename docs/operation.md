---
title: Run an experiment
description: Prepare the apparatus, record a sequence and stop each independent subsystem.
section: Software
---
This procedure follows the supplied master and LED programs. Test the mechanical setup, sensor readings and individual outputs before introducing animals. A complete run needs the target controller, display, thermal controllers and recording system prepared separately.

## Before a run

1. **Check the assembly.** The arena is level, the cover is seated as intended, the camera sees the entire floor, and the underside airflow is unobstructed.
2. **Check the controller identities.** Confirm the correct program is loaded on each labelled board and that the computer ports match those labels.
3. **Check target mapping.** Use the physical A–D labels and the [wiring table](build/four-channels.md#target-controller-pin-map). Confirm the corresponding display states before starting a sequence.
4. **Check temperature readings.** Verify background and ring sensor responses. Measure the target surfaces separately; the master has no target-temperature feedback.
5. **Allow conditions to settle.** Record the starting temperatures and wait for reproducible conditions rather than relying only on elapsed warm-up time.
6. **Prepare recording.** Set focus, exposure and frame rate, choose the output folder, and make a short recording to confirm that files are saved correctly.

<figure class="photo-slot" data-photo-id="run-ready"><div class="photo-space" aria-label="Blank photograph of the prepared recording setup"></div><figcaption><span>Photo · S03</span><strong>Ready-to-run setup</strong></figcaption></figure>

## Start a sequence

Open the master's serial connection at **115200 baud**. Start behaviour and temperature recording before issuing the sequence, then record the command time. For example:

```text
EXP A-D-C-D
```

The letters give the order in which targets are selected. This example selects A, then D, then C, then D again. The program accepts **1–16 selections**. Each cooling interval lasts **300 seconds**, preceded by **300 seconds of preheating** for all targets. The example therefore lasts 25 minutes including preheat.

The first cooling trial starts after preheat. Record this boundary in the video or timing notes so the subsequent analysis does not treat warm-up frames as trial 1.

## What to observe during a step

The selected tile receives an initial cooling boost and then a lower hold output. The display receives the selected target letter. Other tiles heat, with a short boost when a tile returns from cooling. The [PWM plot](build/four-channels.md#trial-sequence) shows these output commands.

Observe the temperature traces as well as the controller messages. If the intended tile does not cool or the background drifts, the command sequence alone is not evidence of a valid temperature condition. Check the thermal and wiring setup before continuing data collection.

## Keep a record with each experiment

| Record | Why it matters |
| --- | --- |
| Target order and physical mapping | Connects the command letters to locations in the video |
| Preheat start and first cooling start | Aligns video, controller timing and temperature data |
| Original video and actual frame rate | Preserves the time basis for analysis |
| Temperature traces and measurement locations | Shows the conditions experienced during each trial |
| Controller filenames and settings | Identifies the software and outputs used |
| Camera position and spatial calibration | Relates image distances to the 200 mm walking diameter |
| Changes to airflow, mounting or illumination | Helps explain differences between runs |

## Stop and shut down

Send `STOP` to the master to stop the four target outputs and blank the display. The program also stops these outputs when its sequence finishes.

The background and ring remain independent. Send `STOP` to the background controller through its own serial connection. The supplied ring program has no `STOP` command, so switch off the ring heater supply separately. Check that the loads are off and allow the hot undersides to cool before switching off the fan or handling the assembly.

Stop the recordings and open the saved files to check that the intended interval was captured. Keep the raw recordings; plots and processed tracks should be saved separately.

[Software checks](software/checks.md) · [Thermal-camera data format](firmware/camera.md)
