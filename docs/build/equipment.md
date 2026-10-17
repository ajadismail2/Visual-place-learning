---
title: Equipment and materials
description: Components used in the arena and its control system.
section: Assembly
---
The tables below describe this build. For the original apparatus, see [Published arena specifications](published-specifications.md).

## Thermal components

| Component | Arrangement |
| --- | --- |
| Background Peltier modules | 60 modules in one series circuit |
| Target Peltier modules | Four independently controlled targets, A–D |
| Bidirectional drivers | One per target |
| TMP117 sensor | Background temperature feedback |
| Ring heater and OneWire sensor | Separate temperature-control loop |
| Heat sinks and lower fan | Proposed heat removal beneath the targets |

## Electronics and imaging

| Component | Use |
| --- | --- |
| ESP32 boards | Target control, display control and thermal-camera interface |
| Eight P4 HUB75 panels | 64 × 32 pixels per panel; 4 mm pitch |
| MLX90640 | 32 × 24 temperature measurements per frame |
| IR illumination and camera | Behaviour recording |
| Controller PCB, headers and wiring | Connections between boards and drivers |
| Regulated power supplies | Separate rated supplies for logic and loads |

Supply ratings and connector sizes must match the installed modules. Use the [wiring tables](pcb.md) to assign the controller signals.

## Fabricated parts

The mechanical assembly uses a wooden base, an aluminium carrier, and printed supports for the arena, thermal ring, illumination, camera and LED panels. CAD defines the mounting geometry; KiCad defines the controller symbols and PCB footprints.

[Arena assembly](arena.md) · [Heat-sink arrangement](thermal-coupling.md)
