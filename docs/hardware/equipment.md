---
title: Equipment and materials
description: Identify the parts by function before wiring them together.
section: Hardware
---
Components are grouped by function. Confirm specifications against the installed modules and supply ratings.

## Temperature system

| Component | Quantity or arrangement | Why it is needed |
| --- | --- | --- |
| Background Peltier modules | 60 in the documented series circuit | Form the common temperature background |
| Cooling Peltier plates | Four | Provide independently selected cooling locations |
| Bidirectional drivers | One per Peltier plate | Reverse and regulate current through each Peltier plate |
| TMP117 sensor | Background feedback sensor | Reports temperature to the background controller |
| Ring heater, sensor and MOSFET stage | Separate thermal loop | Regulate the perimeter at the sensor location |
| Peltier-plate heat sinks | Proposed separate lower sinks | Carry rejected heat away from the Peltier-plate undersides |
| Fan | Match to the fitted heat-removal arrangement | Move air through the heat sinks |

Match supplies and drivers to the Peltier modules' voltage and current ratings.

## Controllers and display

| Component | Role |
| --- | --- |
| Peltier-plate ESP32 | Runs timing, four Peltier-plate outputs and display messages |
| Display ESP32 | Produces the HUB75 visual pattern |
| Background and ring Arduino boards | Run the supplied temperature-control sketches |
| Eight P4 HUB75 panels | Display around the arena, with 4 mm pixel pitch |
| Signal cables and labelled connectors | Connect controller outputs to their destinations |
| Rated load supplies and suitable distribution wiring | Carry power independently of signal pins |

<figure class="photo-slot" data-photo-id="equipment-components"><div class="photo-space" aria-label="Blank component inventory photograph"></div><figcaption><span>Photo · H07</span><strong>Component inventory</strong></figcaption></figure>

## Imaging and mechanical parts

Behaviour recording requires an IR-sensitive camera, lens, illumination and overhead mount. An MLX90640 with ESP32 provides thermal measurements.

The physical assembly includes the base, carrier, ring, glass cover, panel enclosure and printed fixtures.

[Start the wiring guide](wiring.md) · [Arena and dimensions](arena.md)
