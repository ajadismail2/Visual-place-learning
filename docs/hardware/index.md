---
title: Hardware
description: Arena, thermal control, visual display and recording.
section: Hardware
---
The apparatus combines a heated walking arena, four cooling targets, an LED panorama and overhead video recording.

## Experimental setup

One target cools during each trial while the other three heat. The target ESP32 synchronises target selection with the visual panorama; the background and ring run independent temperature-control loops.

<figure class="photo-slot" data-photo-id="hardware-complete"><div class="photo-space" aria-label="Blank space for a photograph of the complete apparatus"></div><figcaption><span>Photo · H01</span><strong>Complete apparatus</strong></figcaption></figure>

## Assembly

| Component | Assembly checks |
| --- | --- |
| [Arena](../hardware/arena.md) | Level floor, secure supports, sealed tile edges |
| [Wiring](../hardware/wiring.md) | Board labels, pin assignments, supply ratings |
| [Background control](../hardware/peltier.md) | Sensor response and heating polarity |
| [Four targets](../hardware/four-channels.md) | A–D mapping and temperature response |
| [LED display](led-panels.md) | Panel order, orientation, bar dimensions |
| [Glass cover](glass-cover.md) | Fit, clearance, camera view |
| [Illumination](illumination.md) | Uniformity, mounting, reflections |
| [Cameras](imaging.md) | Focus, calibration, timing |

## Configuration

Pin maps and timings match the published sketches. Supply ratings and fabrication tolerances depend on the installed components.

[Equipment list](../hardware/equipment.md) · [Software setup](../software/upload.md) · [CAD parts](../cad/index.md)
