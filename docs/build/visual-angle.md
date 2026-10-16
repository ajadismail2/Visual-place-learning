---
title: From visual angle to LED pixels
description: We connected the paper's angular dimensions to the real panel pitch, viewing distance, and full-size paper patterns.
section: 05 / Display geometry
---
## Start with the viewing position

The panels have a **4 mm pixel pitch**. A bar width specified in degrees therefore had to become a physical width, then a pixel count. We explored several panel distances in the design calculations; a distance discussed in a calculation is not automatically the final measured distance of the built arena.

For a bar centred at the fly's height and viewed square-on, the width is:

<div class="equation">W = 2D tan(θ / 2)</div>

Here **D** is the distance from the chosen viewing position to the panel plane, **θ** is the angular width, and **W** is the physical bar width. D is not the gap from the arena edge. A moving fly also changes its distance and viewing direction, so a centre-based calibration defines a reference geometry rather than a constant angle everywhere on the floor.

## What eleven pixels actually means

Eleven pixel pitches give a **44 mm bar footprint**. At **160 mm** distance and zero elevation, that subtends about **15.66°**. A 15° bar at the same distance is **42.13 mm**, or **10.53 pixel pitches**. Rounding to an integer pixel count is a real geometric change, not just a drawing preference.

Conversely, a 44 mm bar subtends 15° at approximately **167.1 mm** under the same assumptions. If the bar is above fly height, the endpoints must be measured in three dimensions. In the 16-pixel elevation example, the centre is **64 mm higher**, which changes the angular width.

<details class="calculation" markdown="1">
<summary>Check the horizontal width for a different geometry</summary>
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

## Width and diagonal tilt were separate problems

The older sketch shifted a diagonal by 11 pixels over a 31-pixel height. That is about **19.5° from vertical**, not 45°. The later renderer shifts one pixel sideways per row, giving a **45° slope on the panel**.

The updated code uses **11-pixel bars and 11-pixel gaps**, four vertical bars, and two horizontal bars. The horizontal section is 86 columns long: **344 mm** at P4 pitch. The two horizontal bars occupy rows 0–10 and 22–32, with an 11-row gap. Pattern drawing uses continuous coordinates across panel joints rather than restarting at each panel.

An 11-pixel width measured along a row is not an 11-pixel width perpendicular to a 45° diagonal. Its perpendicular footprint is **44 / √2 ≈ 31.1 mm**. This is why equal code widths should not be described as equal 15° apparent thicknesses for every orientation.

<div class="build-sheet" markdown="1">

### Paper before another hardware revision

Full-size paper patterns made it possible to inspect bar lengths, gaps, clipped diagonals, and transitions before another panel or fixture change. The work moved from angular-width mockups to templates matching the real pixel pitch. Physical-size printing uses 100% scale; fitting a page to the printer margins changes the geometry.

</div>

<p class="source-note">Project geometry and print-template discussions, 11–15 October 2026; pattern dimensions checked against the current supplied LED_Slave(3).ino. Angles are calculations, not photometric measurements of the finished display.</p>
