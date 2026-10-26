---
title: LED matrix library
description: How ESP32-HUB75-MatrixPanel-DMA drives the arena display and how its settings relate to the supplied sketch.
section: Software
---
[ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/) drives the eight-panel panorama. See [Hardware](../hardware/led-panels.md) for panel selection.

## Panel scanning

A conventional 64 × 32, 1/16-scan panel addresses two rows at a time across 16 positions. RGB data are shifted, latched and displayed for timed intervals.

| Connection | Role |
| --- | --- |
| R1, G1, B1 and R2, G2, B2 | Colour data for the two row groups |
| A–D | Row-address selection for the 1/16-scan panel |
| CLK | Shifts data into the panel |
| LAT | Transfers shifted data to the display outputs |
| OE | Enables or blanks the light output |

A **DMA buffer** supplies scan signals directly to the ESP32 peripheral, leaving the processor available for commands and drawing. [1](#references)

**Binary-code modulation** encodes intensity through timed bit planes. Colour depth, chain length and refresh timing therefore interact; the library adjusts bit-plane scheduling toward the requested refresh rate. [2](#references)

## Panorama mapping

Eight chained panels form a 512 × 32 physical strip. The sketch's `putV()` function maps the **256 × 64 virtual panorama** onto the rotated panels.

`putV()` applies and wraps the horizontal offset, selects the panel, transforms orientation and calls `dma->drawPixel()`. Shape helpers draw the stimulus bars.

| Function in the arena sketch | Role |
| --- | --- |
| `putV()` | Convert a panorama coordinate to a physical panel pixel |
| `drawPanorama()` | Clear and redraw the complete bar pattern |
| `applyState()` | Select the A–D offset and redraw |
| `clearDisplay()` | Write a blank image |
| `handleCommand()` | Interpret a received state or OFF command |

ESP-NOW sends state commands, not pixels. DMA scans the image until the buffer changes; the target controller supplies trial timing.

## Settings in the published display program

Extract from the supplied sketch:

```cpp
HUB75_I2S_CFG mxconfig(64, 32, PANELS_IN_CHAIN, pins);
mxconfig.driver           = HUB75_I2S_CFG::FM6126A;
mxconfig.clkphase         = false;
mxconfig.min_refresh_rate = 1000;
mxconfig.double_buff      = false;

dma = new MatrixPanel_I2S_DMA(mxconfig);
dma->begin();
dma->setBrightness8(120);
```

| Setting | Meaning for this arena |
| --- | --- |
| `64, 32, PANELS_IN_CHAIN` | Physical panel dimensions and eight-panel chain length |
| `pins` | The supplied display-board GPIO map, not the library's default wiring |
| `FM6126A` | Driver initialisation selected by this sketch; verify it for replacement panels |
| `clkphase = false` | Selected clock phase; not a brightness or refresh control |
| `min_refresh_rate = 1000` | Requested minimum scan refresh, not an optical measurement |
| `double_buff = false` | Draw into one buffer to conserve memory |
| `setBrightness8(120)` | Global brightness command on a 0–255 scale, not calibrated luminance |

The stimulus uses `color565(0, 255, 0)` and black, with global brightness applied separately. These values are not calibrated light intensity.

## Refresh, colour depth and memory

Longer chains increase row-transfer time; more bit planes increase memory and display time. The library estimates refresh from the clock, row count and schedule. Raising `min_refresh_rate` cannot exceed hardware limits. [2](#references)

`calculated_refresh_rate` reports an estimate after initialisation, not an optical measurement. Check its availability in the installed version. [2, 3](#references)

Single-buffer drawing can overlap scanning. Double buffering separates drawing and display at added memory cost. This sketch does not call `flipDMABuffer()`; enabling double buffering also requires changes to drawing. [3](#references)

Keep contrast and measured timing consistent across runs.

## Install and bring up the display

1. Install the library and Adafruit GFX dependency. The sketch includes `ESP32-HUB75-MatrixPanel-I2S-DMA.h`.
2. Use the supported original ESP32. ESP32-C3 is not a compatible substitute. [1](#references)
3. Follow the [pin map](../hardware/wiring.md#display-board-pin-map), connect external power and common ground, then run the [single-panel test](../firmware/panel-test.md).
4. Connect the full chain, upload the [display program](../firmware/display.md) and test A–D over serial before wireless pairing.
5. [Measure display timing](../hardware/led-panels.md#check-the-assembled-display). Record library and board-package versions, brightness and driver configuration.

For blank panels, check power, IN/OUT orientation, pin mapping and driver compatibility. For repeated rows or columns, check scan type, dimensions and mapping. Faint duplicates may require latch-blanking adjustment, which also affects brightness. [1](#references)

## References

1. [Library README: installation, supported hardware, drawing and troubleshooting](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA#readme).
2. [Library implementation: DMA scheduling, refresh calculation and brightness](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/blob/master/src/ESP32-HUB75-MatrixPanel-I2S-DMA.cpp).
3. [Library header: configuration, buffers and public methods](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/blob/master/src/ESP32-HUB75-MatrixPanel-I2S-DMA.h).
