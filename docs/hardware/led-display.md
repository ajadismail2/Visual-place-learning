---
title: LED display
description: Panel configuration, visual geometry and display timing.
section: Hardware
---
Eight inward-facing Waveshare P4 RGB panels form the visual enclosure. The display shows green bars on black and rotates the panorama when the selected Peltier plate changes.


## Panel configuration

| Property | Configuration |
| --- | --- |
| Panel | Waveshare RGB-Matrix-P4-64x32 |
| Resolution | 64 × 32 pixels per panel |
| Pixel pitch | 4 mm |
| Panel dimensions | 256 × 128 mm |
| Interface and scan | HUB75, 1/16 scan |
| Supply | External 5 V |
| Enclosure | Eight panels facing inward |

The manufacturer's maximum rating is 20 W per panel (5 V, 4 A); actual draw depends on the displayed pattern. Power the panels separately from the ESP32. [Waveshare specifications](https://docs.waveshare.com/RGB-Matrix-Px-64x32).

## Panel chain and drawing

Connect each panel OUT to the next panel IN. The [ESP32-HUB75-MatrixPanel-DMA library](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA) drives the eight-panel chain as a 512 × 32 physical strip. It uses the ESP32's DMA peripheral to scan the panels after a pattern is drawn; the controller does not need to redraw every frame. The arena sketch's `putV()` maps a **256 × 64** virtual panorama to the rotated panels. This rotation is implemented in the sketch.

The supplied display sketch selects the FM6126A driver configuration, `clkphase = false`, one DMA buffer and `setBrightness8(120)`. Confirm driver compatibility for replacement panels. Library brightness is a 0–255 command, not a light measurement. [Library settings and code](../software/led-matrix-library.md).

Centre the panels around the arena and leave clearance for the hinged access panel. Verify panel order, orientation and A–D panorama rotations before pairing the Peltier-plate controller.


## Setting the bar width

Measure the distance **D** from the reference viewing position to the panel plane. For angular width **θ**, calculate physical bar width **W**, then divide by the 4 mm pixel pitch:

<div class="equation">W = 2D tan(θ / 2)</div>

At D = 160 mm, a 15° bar spans **42.13 mm (10.53 pixels)**. Eleven pixels span 44 mm, or **15.66°**. This calculation assumes a centred bar on a flat panel; apparent width varies with fly position and elevation.


<details class="calculation" markdown="1">
<summary>Angular-width calculator</summary>
<div class="angle-calculator" data-angle-calculator>
  <div class="calc-inputs">
    <label>Distance to panel plane (mm)<input id="distance-mm" type="number" min="1" value="160" step="1"></label>
    <label>Pattern centre above fly (mm)<input id="height-mm" type="number" value="0" step="1"></label>
    <label>Angular width (degrees)<input id="angle-deg" type="number" min="0.1" max="89" value="15" step="0.1"></label>
  </div>
  <p id="angle-result" class="calc-result" role="status">42.13 mm · 10.53 pixel pitches at 4 mm pitch</p>
  <p class="calc-note">Example geometry for a flat panel viewed along its normal.</p>
</div>
</details>

## Pattern and timing

The included program draws diagonals at about **19.5° from vertical**. The archived 45° design uses a different pattern. The horizontal region spans **344 mm**, with bars 11 and 10 rows thick.

The sketch requests `min_refresh_rate = 1000`, a minimum scan-refresh setting. It is not a measured optical refresh rate. The library's estimated refresh depends on chain length, clock and colour depth. A–D pattern updates occur at trial transitions, separately from continuous scanning; the 24 fps behaviour video cannot measure panel refresh. See the [library documentation](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA) and [arena sketch](../software/led-display-controller.md).

## Check the display

Test one panel, then the full chain at fixed brightness. Check A–D states, seams and ghosting. For optical refresh, measure light from several rows and panels with a fast photodiode and oscilloscope during steady display and transitions.

Replacement panels must match the scan arrangement, supported driver, geometry, supply and firmware mapping. A HUB75 connector alone does not establish compatibility. [Display wiring](esp32-and-arduino-wiring.md#display-board-pin-map) · [Single-panel test](../software/single-panel-test.md).
