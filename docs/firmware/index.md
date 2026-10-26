---
title: Software
description: How the controller programs cooperate and how to load and operate them.
section: Software
---
The Peltier-plate controller coordinates four Peltier plates and the display. Background and ring controllers run independent temperature loops.

## Experiment sequence

1. Send the Peltier-plate order over USB serial.
2. The Peltier-plate controller preheats all four Peltier plates, then cools the selected Peltier plate and heats the others.
3. ESP-NOW sends the corresponding panorama state to the display.
4. Background and ring feedback loops run independently.
5. Record behaviour and temperature separately; the Peltier-plate controller does not log video or use temperature feedback.

## Start here

<div class="chapter-list" markdown="1">

[**Install and upload**<br><span>Board selection, libraries, sketch folders and pairing the display.</span>](../software/upload.md)

[**Run an experiment**<br><span>Pre-run checks, Peltier-plate order, recording and shutdown.</span>](../operation.md)

[**Checks and troubleshooting**<br><span>Observable tests for each controller and load.</span>](../software/checks.md)

</div>

## Programs for the main setup

| Program | Function |
| --- | --- |
| [Experiment_Controller](target-controller.md) | Four Peltier-plate outputs and display timing; no plate-temperature feedback |
| [Display_Controller](display.md) | Panorama generation on the display ESP32 |
| [Closedloop_60peltier](background.md) | Background feedback from one temperature sensor |
| [Thermal_ring](ring.md) | Independent perimeter-heater feedback |
| [thermal_camera](camera.md) | Thermal-image stream; requires computer-side recording |

## Diagnostic program

[SinglePanelTest](panel-test.md) checks panel wiring and orientation. Restore the display sketch after testing.

## Source files and configuration

Each program page includes its source. Store device addresses and network settings in local `local_config.h`.

Use the corrected ring sketch. Background and ring programs retain Arduino pin assignments; their ESP32 conversion is proposed.

[Download all programs](../downloads/arena-firmware-2026-10-17.zip) · [Settings record](../downloads/protocol.json) · [Wiring guide](../hardware/wiring.md)
