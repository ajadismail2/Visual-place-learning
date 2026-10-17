---
title: Visual display geometry
description: Setting the bar width from panel distance and pixel pitch.
section: Display
---
The panels have a **4 mm pixel pitch**. Bar width is calculated from the viewing distance and then rounded to a whole number of pixels.

Original display specifications are listed in the [reference design](published-specifications.md).

## Setting the bar width

1. Measure the distance **D** from the reference viewing position to the panel plane.
2. Calculate the width **W** for the required angular width **θ** using the equation below.
3. Divide the width by 4 mm to obtain the pixel count. Recalculate the angle after rounding.

<div class="equation">W = 2D tan(θ / 2)</div>

Measure from the viewing position rather than the arena edge. This calculation assumes a bar centred on the viewing direction.

At 160 mm, a 15° bar is **42.13 mm**, or **10.53 pixel pitches**. An 11-pixel bar is 44 mm and subtends about 15.66°. Full-size paper templates provided a dimensional check before display programming.

<details class="calculation" markdown="1">
<summary>Angular-width calculator</summary>
<div class="angle-calculator" data-angle-calculator>
  <div class="calc-inputs">
    <label>Distance to panel plane (mm)<input id="distance-mm" type="number" min="1" value="160" step="1"></label>
    <label>Pattern centre above fly (mm)<input id="height-mm" type="number" value="0" step="1"></label>
    <label>Angular width (degrees)<input id="angle-deg" type="number" min="0.1" max="89" value="15" step="0.1"></label>
  </div>
  <p id="angle-result" class="calc-result" role="status">42.13 mm · 10.53 pixel pitches at 4 mm pitch</p>
  <p class="calc-note">Example geometry. Assumes a centred horizontal span on a flat panel viewed along its normal; elevation is included. It is not a whole-arena optical calibration.</p>
</div>
</details>

## Display pattern geometry

The included LED program draws diagonals at about **19.5° from vertical**. The archived 45° design uses a different pattern.

The horizontal region is **344 mm long**. Its bars are 11 and 10 rows thick in the supplied sketch. A moving fly sees a changing angle, so the centre-based calculation is a reference, not a constant across the arena.

[Read the display code](../firmware/display.md)
