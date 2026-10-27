---
title: LED matrix library
description: Library and settings used by the ESP32 display.
section: Software
---
The display uses mrcodetastic's ESP32-HUB75-MatrixPanel-DMA library with Adafruit GFX. DMA keeps the panels scanning while the ESP32 handles drawing and incoming commands.

Eight 64 × 32 panels form a 512 × 32 chain. The arena sketch maps this to a 256 × 64 panorama and changes the pattern position when it receives A–D over ESP-NOW.

## Settings

The supplied sketch uses the FM6126A driver setting, `clkphase = false`, one display buffer and brightness `120` on a 0–255 scale. It requests a minimum refresh rate of 1000 Hz; the actual optical refresh has not been measured.

Install the library, follow the [display pin map](../hardware/esp32-and-arduino-wiring.md#display-board-pin-map), and run the [single-panel test](6-single-panel-test.md) before connecting the full chain.

[Display program](2-secondary-esp32-the-led-display-controller.md)
