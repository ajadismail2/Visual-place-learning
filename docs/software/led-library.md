---
title: LED matrix library
description: How ESP32-HUB75-MatrixPanel-DMA drives the arena display and how its settings relate to the supplied sketch.
section: Software
---
[ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/) turns pixel data in ESP32 memory into the timed electrical signals required by HUB75 panels. The arena's display sketch uses this library to draw and maintain the visual panorama. Panel selection belongs in [Hardware](../hardware/led-panels.md); drawing, memory and refresh settings are described here.

## From a pixel to an illuminated panel

A HUB75 panel is scanned rather than illuminated as one continuous image. On a conventional 64 × 32, 1/16-scan panel, two rows are addressed together and the scan cycles through 16 row positions. RGB data are shifted into the panel, latched and displayed for controlled intervals.

| Connection | Role |
| --- | --- |
| R1, G1, B1 and R2, G2, B2 | Colour data for the two row groups |
| A–D | Row-address selection for the 1/16-scan panel |
| CLK | Shifts data into the panel |
| LAT | Transfers shifted data to the display outputs |
| OE | Enables or blanks the light output |

The library prepares these signals in a **DMA buffer**, a block of memory read directly by the ESP32's display-capable peripheral. DMA means direct memory access. Repeated scanning is handled by hardware, leaving the processor available for commands and drawing. [1](#references)

The library also represents colour intensity using timed bit planes, called **binary-code modulation**. Different bits contribute different illumination durations. This explains why colour precision, panel-chain length and refresh timing are linked. The implementation adjusts bit-plane scheduling when trying to meet a requested refresh rate. [2](#references)

## How our sketch uses it

The library sees eight 64 × 32 panels in a chain, equivalent to a 512 × 32 physical pixel strip. Our own `putV()` function maps a **256 × 64 virtual panorama** onto those rotated panels. This coordinate conversion belongs to the arena sketch, not to an automatic octagon-detection feature.

`putV()` adds the selected horizontal offset, wraps it around the panorama, chooses the panel and converts the pixel to that panel's orientation. It then calls `dma->drawPixel()`. The rectangle and parallelogram helpers build the vertical, horizontal and diagonal bars from those pixels.

| Function in the arena sketch | Role |
| --- | --- |
| `putV()` | Convert a panorama coordinate to a physical panel pixel |
| `drawPanorama()` | Clear and redraw the complete bar pattern |
| `applyState()` | Select the A–D offset and redraw |
| `clearDisplay()` | Write a blank image |
| `handleCommand()` | Interpret a received state or OFF command |

ESP-NOW delivers the state message separately. It does not stream every pixel. Once drawn, the DMA hardware keeps scanning the image until the buffer changes. Trial timing remains with the four-Peltier controller.

## Settings in the published display program

The following is an extract from the existing sketch, not a second firmware download:

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

The colour values are full green, `color565(0, 255, 0)`, and black. Global brightness is applied separately. Neither the RGB value nor the brightness number establishes the light intensity reaching a fly.

## Refresh, colour depth and memory

Each additional panel increases the data shifted for a row. More colour bit planes require more memory and display time. The library calculates a refresh estimate from the clock, row count and bit-plane schedule, then adjusts its scheduling toward `min_refresh_rate`. There is a limit to what a given chain and clock can achieve. Raising the requested number cannot remove that limit. [2](#references)

The upstream implementation exposes `calculated_refresh_rate` after initialisation. This is a calculated diagnostic, not a photodiode reading. Check the API in the installed library version before adding diagnostic output. [2, 3](#references)

With one buffer, a pattern can be partly redrawn while scanning continues. Double buffering uses separate drawing and display buffers and a buffer swap, at the cost of additional memory. Our supplied program uses one buffer and does not call `flipDMABuffer()`. Enabling double buffering would therefore require changes to the drawing sequence, not just changing the flag. [3](#references)

For this green-and-black stimulus, smooth colour gradients are not the experimental goal. Stable contrast and verified timing are more relevant than maximum RGB colour depth. Keep the tested settings consistent across runs.

## Install and bring up the display

1. Install the library through Arduino Library Manager and its documented Adafruit GFX dependency. The header used by the sketch is `ESP32-HUB75-MatrixPanel-I2S-DMA.h`, despite the shorter GitHub repository name.
2. Select the correct board. The library supports the original ESP32 used here; support should not be assumed for every ESP32 variant. In particular, ESP32-C3 is not a substitute for this display driver. [1](#references)
3. Follow the [display-board pin map](../build/wiring.md#display-board-pin-map), connect the panel's external supply and common ground, and run the [single-panel test](../firmware/panel-test.md).
4. Connect the full chain in the documented order and load the [display controller](../firmware/display.md). Test A, B, C and D over serial before pairing the wireless controller.
5. Check the light output using the [hardware timing procedure](../hardware/led-panels.md#check-the-assembled-display). Record the library version, board package, brightness and panel-driver configuration with the experiment settings.

If a panel stays blank, first check power, IN/OUT orientation, pin mapping and driver compatibility. If rows or columns repeat, check scan type, panel dimensions and mapping. Faint duplicate pixels can require latch-blanking adjustment, which blanks output around row switching and can affect brightness. Do not treat every display fault as a need for a more expensive panel. [1](#references)

## References

1. [Library README: installation, supported hardware, drawing and troubleshooting](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA#readme).
2. [Library implementation: DMA scheduling, refresh calculation and brightness](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/blob/master/src/ESP32-HUB75-MatrixPanel-I2S-DMA.cpp).
3. [Library header: configuration, buffers and public methods](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/blob/master/src/ESP32-HUB75-MatrixPanel-I2S-DMA.h).
