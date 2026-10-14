---
title: The visual panorama
description: Eight P4 LED panels, explicit pixel geometry, and a calibrated relationship between physical width and visual angle.
---
## Display construction

Eight **64 × 32 HUB75 P4 panels** form an octagonal surround. The native chain is 512 × 32 pixels. Rotating the physical panels into the project arrangement gives a **256 × 64 virtual canvas**. P4 denotes a nominal 4 mm pixel pitch.

The supplied firmware draws green landmarks on a black background and moves the entire virtual panorama by 64-pixel quarter-turn increments. The web overview's panorama preview reproduces that source's virtual pixels; its colours are adapted to the website and are not a photometric simulation.

## What the current firmware actually draws

Inclusive pixel endpoints matter: a bar running from x = 11 through x = 21 is **11 pixels wide**, not ten.

| Landmark | Coordinates in supplied firmware | Actual extent |
| --- | --- | --- |
| Panel 1 vertical bar | x = 11…21, y = 0…30 | 11 px wide, 31 px high |
| Panel 2 vertical bars | x = 0…10 and 21…31, y = 0…30 | Two 11 px bars, separated by 10 unlit columns |
| Panel 8 vertical bar | x = 22…31, y = 0…30 | 10 px wide, 31 px high |
| Horizontal stripes | y = 0…10 and 22…31 | 11 px and 10 px high, separated by 11 unlit rows |
| Diagonal bars | 11 px horizontal width; x shift −11 over y = 0…31 | Straight, rasterized parallelograms |
| Upper virtual rows | y = 32…63 | Unlit in this source snapshot |

The diagonal displacement is 11 horizontal pixels over 31 vertical intervals. With equal physical pixel pitch, its underlying centreline is approximately **19.5° from vertical**, or **70.5° from horizontal**. It is not a 45° diagonal. Integer pixel steps make its edges jagged; they do not make it a curved bar.

The subsequent paper-mockup brief requested the code’s bar counts and arrangement, widths adjusted to 15°, smooth 45° diagonals, and a full 360° panorama across three A4 sheets without labels. Treat that as a separate stimulus prototype: it does not change the uploaded firmware automatically.

## Visual angle is geometry dependent

For a centred horizontal extent of width **w**, on a flat panel a perpendicular distance **d** from the fly and with its midpoint at the same height, the angle between the two edge rays is:

**θ = 2 arctan(w / 2d)**, so **w = 2d tan(θ / 2)**.

The half-angle arises because the two equal right triangles meet at the bar's centreline. At a 4 mm pitch, an 11-pixel width is nominally 44 mm; its apparent width changes as the fly moves.

If the pattern midpoint is **h** above the fly, horizontal and vertical angular extents are different. For a centred horizontal span, replace d by √(d² + h²). For a vertical span, use **θ = arctan((h + w/2)/d) − arctan((h − w/2)/d)**. The calculator solves these geometries separately.

<div class="calculator" data-angle-calculator>
  <div class="calc-inputs">
    <label>Perpendicular distance to panel (cm)<input id="distance-cm" type="number" min="0.1" step="0.1" value="16"></label>
    <label>Pattern midpoint above fly (cm)<input id="height-cm" type="number" step="0.1" value="6.4"></label>
    <label>Pixel pitch (mm)<input id="pitch-mm" type="number" min="0.1" step="0.1" value="4"></label>
    <label>Desired angular extent (degrees)<input id="angle-deg" type="number" min="0.1" max="88.9" step="0.1" value="15"></label>
  </div>
  <p class="calc-result" id="angle-result" role="status">Enable JavaScript to calculate horizontal and vertical pixel extents.</p>
  <p class="calc-caption">Default elevation: 16 pixels × 4 mm = 64 mm. Outputs are continuous geometric widths; integer pixel choices should be checked at their realised angles.</p>
</div>

The calculation assumes a fly centred laterally in front of one flat panel. An octagonal surround is not a circular arc, and the angular size varies with fly position, panel orientation, and the direction in which bar width is measured. For a truly circular arc centred on the observer, arc length is **s = rθ**, with θ in radians; this is a different geometry.

## Matching a stimulus to a paper

Compare the original paper's angular conventions, landmark arrangement, arena geometry, and elevation before assigning a claimed angular width. A raw number of lit pixels is not enough to assert equivalence. Retain both the intended angle and the exact rendered pixels in the experiment record.

## Diffusion and enclosure

White PLA diffusion and a dark enclosure were explored to reduce discrete LED appearance and unwanted reflections. Final diffuser thickness, spacing, brightness uniformity, and angular contrast have not been established here as validated specifications. Check the completed optical stack from the fly's position, including the glass cover and panel seams.

For stimulus comparison, record brightness setting, colour channel, panel mapping, geometry, diffuser configuration, and the firmware revision. See [controller details](esp32.md), [mechanical design](../software/3d_CAD.md), and [references](../resources/references.md).
