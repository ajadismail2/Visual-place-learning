---
title: Equipment and materials
description: Identify the parts by function before wiring them together.
section: Hardware
---
Use this list to identify the components in the apparatus. It is a functional equipment list; purchasing specifications must be checked against the exact module and supply ratings.

## Temperature system

| Component | Quantity or arrangement | Why it is needed |
| --- | --- | --- |
| Background Peltier modules | 60 in the documented series circuit | Form the common temperature background |
| Target Peltier modules | Four | Provide independently selected cooling locations |
| Bidirectional drivers | One per target | Reverse and regulate current through each target |
| Background power stage | One controlled output | Switch load power for the background circuit |
| TMP117 sensor | Background feedback sensor | Reports temperature to the background controller |
| Ring heater, sensor and MOSFET stage | Separate thermal loop | Regulate the perimeter at the sensor location |
| Target heat sinks | Proposed separate lower sinks | Carry rejected heat away from the target undersides |
| Fan | Match to the fitted heat-removal arrangement | Move air through the heat sinks |

A Peltier's current rating, its intended voltage and the rating of its driver must be considered together. The number of modules alone is not enough to select a supply. Record the actual part labels before making the final power connections.

## Controllers and display

| Component | Role |
| --- | --- |
| Target ESP32 | Runs timing, four target outputs and display messages |
| Display ESP32 | Produces the HUB75 visual pattern |
| Background and ring Arduino boards | Run the supplied temperature-control sketches |
| Eight P4 HUB75 panels | Display around the arena, with 4 mm pixel pitch |
| Signal cables and labelled connectors | Connect controller outputs to their destinations |
| Rated load supplies and suitable distribution wiring | Carry power independently of signal pins |

<figure class="photo-slot" data-photo-id="equipment-components"><div class="photo-space" aria-label="Blank component inventory photograph"></div><figcaption><span>Photo to add · H07</span><strong>Component inventory</strong><p>Lay out one example of each controller, driver, sensor, Peltier and connector with its model label visible.</p></figcaption></figure>

## Imaging and mechanical parts

The recording setup needs a behaviour camera, a suitable lens, infrared illumination and a stable overhead mount. An MLX90640 and its ESP32 interface provide temperature measurements. Keep the thermal-camera viewing requirements separate from those of the behaviour camera.

The physical assembly includes the base, carrier, ring, glass cover, panel enclosure and printed fixtures. Exact base material, thicknesses, fasteners and printed-part dimensions should be entered with the assembly photographs and [CAD records](../cad/index.md).

## Before assembly

Label each controller and load, group the cables by subsystem, and check the supply information printed on each device. Keep the target drivers, background power stage and ring power stage distinguishable. Their similar-looking terminals do not imply identical electrical requirements.

[Start the wiring guide](wiring.md) · [Arena and dimensions](arena.md)
