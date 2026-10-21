---
title: Software
description: How the controller programs cooperate and how to load and operate them.
section: Software
---
The apparatus uses several small programs rather than one program controlling everything. Each controller keeps running its own sketch while powered. The experiment controller coordinates the four targets and display; the background and ring regulate temperature independently.

## Follow one experiment through the system

1. You send a target order to the experiment controller through a USB serial connection.
2. The experiment controller starts the preheat interval, then selects each target in turn.
3. The selected driver's output cools its tile. The other target outputs heat.
4. The experiment controller sends the target letter to the display ESP32, which chooses the corresponding panorama position.
5. The background and ring controllers keep reading their own sensors and adjusting their own outputs.
6. Recording software captures behaviour and temperature data. The supplied experiment controller does not save the behavioural video or receive target-temperature feedback.

This separation matters when testing and stopping the apparatus: a response from the experiment controller does not show that every sensor or recorder is working.

## Start here

<div class="chapter-list" markdown="1">

[**Install and upload**<br><span>Board selection, libraries, sketch folders and pairing the display.</span>](../software/upload.md)

[**Run an experiment**<br><span>Pre-run checks, target order, recording and shutdown.</span>](../operation.md)

[**Checks and troubleshooting**<br><span>Observable tests for each controller and load.</span>](../software/checks.md)

</div>

## Programs for the main setup

| Program | Board and job | What it does not do |
| --- | --- | --- |
| [Experiment_Controller](experiment.md) | Target ESP32; timing and four drivers | Does not regulate target output from measured target temperature |
| [Display_Controller](display.md) | Display ESP32; visual pattern | Does not power the Peltier drivers |
| [Closedloop_60peltier](background.md) | Arduino; background temperature loop | One sensor does not measure all 60 module temperatures separately |
| [Thermal_ring](ring.md) | Arduino; perimeter heater loop | Does not stop when the experiment controller receives STOP |
| [thermal_camera](camera.md) | ESP32; thermal-image stream | Does not save a file on the computer by itself |

## Diagnostic and alternative programs

[SinglePanelTest](panel-test.md) checks one display panel before connecting the full chain. Uploading it replaces the display controller program on that board, so restore the display program before running an experiment.

[4_peltier_mosfet_hbridge](four-peltier.md) is an alternative bench-control program. Its pin assignments and commands differ from the main setup. Use its own wiring table.

## Three terms used throughout

**Setpoint** is the temperature requested from a feedback controller. **Measured temperature** is what a sensor reports at its location. **PWM output** is the electrical drive setting. These are different quantities: a setpoint or PWM table is not proof that the whole walking surface reached a particular temperature.

## Source files and configuration

The full code is available under a collapsible section on each program page. Read the operating explanation and connection table before changing the source. Local experiment controller settings belong in `local_config.h`; the published example deliberately contains no working device address or private password.

Use the separate syntax-corrected ring file for compilation. The original uploaded file is retained alongside it. The background and ring sketches use Arduino pin assignments; the ESP32 conversion is a proposed adaptation.

[Download all programs](../downloads/arena-firmware-2026-10-17.zip) · [Settings record](../downloads/protocol.json) · [Wiring guide](../build/wiring.md)
