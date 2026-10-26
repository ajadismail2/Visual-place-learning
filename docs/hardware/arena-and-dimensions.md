---
title: Arena and dimensions
description: The walking surface, perimeter, glass cover and supporting structure.
section: Hardware
---
A ring and glass cover enclose the temperature-controlled walking surface, with an LED panorama around it and a camera above.

## Current arena specification

| Feature | Documented configuration |
| --- | --- |
| Walking-area inner diameter | **200 mm** |
| Background | 60 Peltier modules operated as one circuit |
| Cooling Peltier plates | Four separately driven Peltier plates, A–D |
| Visual enclosure | Eight P4 HUB75 panels, 64 × 32 pixels each |
| Pixel pitch | 4 mm |
| Glass cover | Above the walking surface |
| Background sensor setpoint | 34.8 °C in the supplied sketch |
| Ring sensor setpoint | 45 °C in the supplied sketch |
| Peltier-plate cooling interval | 300 s for each selected Peltier plate |

The **200 mm inner diameter** defines the walking area and image scale. Fabrication dimensions should follow measured components and CAD.


## Walking surface and Peltier plates

Mount the four Peltier plates flush with the background, with no accessible gaps.

Label the Peltier plates A–D using the tested driver mapping, and retain these labels in recordings and analysis.

## Base and mounts

Mount the carrier on a rigid, level base. Supports and cables must not tilt the floor or obstruct the camera.

See [CAD and printed parts](../cad/parts-and-step-files.md) for the component overview.


## Ring and glass cover

The ring and glass cover enclose the walking surface. See [Glass cover](glass-cover.md) for fit and handling.

The ring uses independent temperature feedback. See [thermal ring](thermal-ring.md).

## Check the mechanical setup

Check floor level, mount stability, door clearance and full camera coverage after assembly.
