---
title: Visual display geometry
description: Setting the bar width from panel distance and pixel pitch.
section: Hardware
---
Eight P4 HUB75 panels, each 64 × 32 pixels at **4 mm pitch**, surround the arena. Bar angle varies with viewing distance.

## Assemble and test the enclosure

Centre the panels around the arena, facing inward, with clearance for the access door.

Chain panel OUT to IN and power panels through their supply connectors. See [display wiring](wiring.md#display-board-pin-map).

The sketch maps the rotated panels to a **256 × 64** panorama. Verify panel order and A–D rotations before wireless operation.

<div class="photo-pair"><figure class="photo-slot" data-photo-id="led-enclosure"><div class="photo-space" aria-label="Blank photograph of the LED enclosure"></div><figcaption><span>Photo · V01</span><strong>Panel enclosure and cable order</strong></figcaption></figure><figure class="photo-slot" data-photo-id="led-pattern"><div class="photo-space" aria-label="Blank photograph of the displayed visual pattern"></div><figcaption><span>Photo · V02</span><strong>Displayed visual pattern</strong></figcaption></figure></div>

## Setting the bar width

1. Measure the distance **D** from the reference viewing position to the panel plane.
2. Calculate the width **W** for the required angular width **θ** using the equation below.
3. Divide the width by 4 mm to obtain the pixel count. Recalculate the angle after rounding.

<div class="equation">W = 2D tan(θ / 2)</div>

D is measured from the viewing position. The equation assumes a centred bar on a flat panel.

At D = 160 mm, a 15° bar spans **42.13 mm (10.53 pixels)**. Rounding to 11 pixels gives 44 mm and **15.66°**.

![Viewing geometry and calculated pixel width for a 15-degree bar](../assets/setup/display-geometry.svg)

Use measured panel distance and elevation. The example is not a fixed apparatus dimension or a whole-arena optical calibration.

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

The horizontal region spans **344 mm**, with bars 11 and 10 rows thick. Angular width varies with fly position.

## Verify the pattern before a run

Check rotation, bar count and continuity across panel seams for A–D. Verify pixel dimensions in code and viewing distances on the apparatus.

Measure optical refresh independently of behaviour-camera frame rate.

[Panel choice and refresh](../hardware/led-panels.md) · [Read the display code](../firmware/display.md)
