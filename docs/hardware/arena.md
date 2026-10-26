---
title: Arena and dimensions
description: The walking surface, perimeter, cover and supporting structure.
section: Hardware
---
A ring and glass cover enclose the temperature-controlled walking surface, with an LED panorama around it and a camera above.

## Current arena specification

| Feature | Documented configuration |
| --- | --- |
| Walking-area inner diameter | **200 mm** |
| Background | 60 Peltier modules operated as one circuit |
| Targets | Four separately driven modules, A–D |
| Visual enclosure | Eight P4 HUB75 panels, 64 × 32 pixels each |
| Pixel pitch | 4 mm |
| Cover | Glass cover above the walking surface |
| Background sensor setpoint | 34.8 °C in the supplied sketch |
| Ring sensor setpoint | 45 °C in the supplied sketch |
| Target cooling interval | 300 s for each selected target |

The **200 mm inner diameter** defines the walking area and image scale. Fabrication dimensions should follow measured components and CAD.

<figure class="photo-slot" data-photo-id="arena-top"><div class="photo-space" aria-label="Blank top-view arena photograph"></div><figcaption><span>Photo · A02</span><strong>Walking surface and target positions</strong></figcaption></figure>

## Walking surface and target tiles

Mount targets flush with the background, with no accessible gaps.

Label targets A–D using the tested driver mapping, and retain these labels in recordings and analysis.

## Base and mounts

Mount the carrier on a rigid, level base. Supports and cables must not tilt the floor or obstruct the camera.

See [CAD and printed parts](../cad/index.md) for the component overview.

## Fabrication

Measure component dimensions and hole spacing before machining or printing mounts.

Check one printed fitting against the hardware before producing the remaining parts.

Machine and deburr carrier openings to measured tolerances. Use printed parts for supports and conductive material at Peltier thermal interfaces.

<figure class="photo-slot" data-photo-id="arena-side"><div class="photo-space" aria-label="Blank side-view photograph of arena clearances"></div><figcaption><span>Photo · A03</span><strong>Ring, cover and supporting structure</strong></figcaption></figure>

## Ring and cover

The ring and glass cover enclose the walking surface. Fit the cover without disturbing the ring or sensor wiring; clearance depends on the assembly.

The ring uses independent temperature feedback. See [thermal ring](../hardware/ring.md).

## Aluminium carrier

The proposed aluminium carrier has four target openings. Targets must remain supported, flush and thermally separated from the surrounding floor.

Separate target heat sinks are proposed to reduce heating of the carrier. See [heat removal](thermal-coupling.md).

## Check the mechanical setup

Check floor level, mount stability, door clearance and full camera coverage after assembly.
