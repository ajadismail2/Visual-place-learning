---
title: Equipment and materials
description: Identify the parts by function before wiring them together.
section: Hardware
---
Components are grouped by function. Confirm specifications against the installed modules and supply ratings.

## Temperature system

| Component | Specification | Function |
| --- | --- | --- |
| Background Peltier modules | 60, wired in series | Establish a uniform background temperature |
| Cooling Peltier plates | 4 (A-D) | Create independently addressable cool-spot targets |
| Bidirectional drivers | 1 per cooling plate | Control the magnitude and polarity of plate current |
| TMP117 temperature sensor | 1, background loop | Provides feedback for closed-loop background control |
| Ring heater, sensor and MOSFET stage | Independent control loop | Regulates perimeter temperature |
| Fan | 120 mm | Drives airflow across the aluminium plate to remove waste heat |

Match supplies and drivers to the Peltier modules' voltage and current ratings.

## Controllers and display

| Component | Role |
| --- | --- |
| Peltier-plate ESP32 | Handles experiment timing, drives the four Peltier-plate outputs and sends display commands |
| Display ESP32 | Generates the HUB75 visual pattern |
| Background and ring Arduino boards | Execute the supplied temperature-control sketches |
| Eight P4 HUB75 panels | Present the visual landmarks around the arena at 4 mm pixel pitch |
| Signal cables and labelled connectors | Route controller outputs to their targets |
| Rated power supplies and distribution wiring | Deliver power independently of controller signal pins |


## Imaging and mechanical parts

Behaviour recording requires an IR-sensitive camera, lens, illumination and overhead mount. An MLX90640 with ESP32 provides thermal measurements.


[Start the wiring guide](esp32-and-arduino-wiring.md) · [Arena and dimensions](arena-and-dimensions.md)
