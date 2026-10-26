---
title: LED panels
description: P4 panel selection, visual stimulus timing and affordable alternatives for the arena.
section: Hardware
---
Eight P4 RGB panels display green landmarks on black. The panorama changes with target selection and remains fixed within each trial.

![The green visual pattern surrounding the arena](images/LED.jpg)

## Panels used in this build

| Property | Configuration |
| --- | --- |
| Panel | Waveshare RGB-Matrix-P4-64x32 |
| Resolution | 64 × 32 pixels per panel |
| Pixel pitch | 4 mm between pixel centres |
| Panel dimensions | 256 × 128 mm |
| Interface and scan | HUB75, 1/16 scan |
| Supply | External 5 V supply |
| Enclosure | Eight panels, with their display faces inward |

Waveshare rates each P4 panel at up to 20 W (5 V / 4 A). Supply panel power separately from the ESP32. These ratings do not represent measured consumption of the bar pattern. [1](#references)

## Display timing

Rapid refresh reduces unintended flicker during visual stimulation. Reiser and Dickinson describe LED arenas developed for controlled insect-vision experiments. [2](#references)

Drosophila photoreceptor bandwidth increases with illumination and temperature, so timing must be assessed under experimental conditions. [3, 4](#references)

The sketch requests `min_refresh_rate = 1000`. Actual optical refresh remains unmeasured; this setting is not an established biological optimum.

| Rate | What changes |
| --- | --- |
| Panel refresh | Repeated electrical scanning of the existing image |
| Pattern update | A new A–D visual state is drawn at a trial transition |
| Camera frame rate | Behaviour images are recorded for tracking |

A 24 fps behaviour recording cannot establish that an LED display refreshes at 1000 Hz.

## Pixel pitch and visible landmarks

Pixel pitch and viewing distance determine spatial sampling; refresh rate determines temporal presentation.

At 160 mm, a 4 mm pitch subtends **1.43°** and an 11-pixel bar subtends **15.66°**. These are geometric values, not visual-acuity measurements. The assay uses the panorama's relation to target position. [5](#references)

P4 provides sufficient sampling for the specified bars. Calculate angles from the installed geometry; they vary as the fly moves. See [display geometry](../hardware/visual-angle.md).

## Affordable alternatives

Equivalent low-cost panels can replace Waveshare panels if geometry, contrast and timing are maintained.

Choose **64 × 32, P4, 1/16-scan panels with supported driver chips**. HUB75 connectors alone do not establish compatibility; some panels with integrated PWM engines are unsupported. [6](#references)

| Check before substitution | Why it matters |
| --- | --- |
| Driver chip and scan arrangement | Determines whether the library can drive the panel |
| Pitch, dimensions and mounting holes | Determines the enclosure geometry and printed supports |
| Panel resolution and orientation | Must match the firmware's coordinate mapping |
| Supply rating and logic levels | Must match the power wiring and ESP32 interface |
| Actual light output | Brightness, contrast and temporal modulation must be checked |

A different pitch requires recalculating visual angles; a different driver may require firmware changes.

## Check the assembled display

Test one panel, then the full chain. Check A–D states, panel seams and ghosting at fixed brightness.

Measure light output with a fast photodiode and oscilloscope at the experimental brightness. Sample several rows and panels during steady display and transitions. Camera recordings cannot verify a 1000 Hz refresh rate.

[Library operation and settings](../software/led-library.md) · [Display wiring](../hardware/wiring.md#display-board-pin-map) · [Display controller code](../firmware/display.md)

## References

1. [Waveshare: RGB-Matrix-Px-64x32 specifications](https://docs.waveshare.com/RGB-Matrix-Px-64x32).
2. Reiser & Dickinson. [A modular display system for insect behavioral neuroscience](https://doi.org/10.1016/j.jneumeth.2007.07.019). Journal of Neuroscience Methods (2008).
3. Juusola & Hardie. [Light adaptation in Drosophila photoreceptors I: response dynamics and signaling efficiency](https://doi.org/10.1085/jgp.117.1.3). Journal of General Physiology (2001).
4. Juusola & Hardie. [Light adaptation in Drosophila photoreceptors II: rising temperature increases the bandwidth of reliable signaling](https://doi.org/10.1085/jgp.117.1.27). Journal of General Physiology (2001).
5. Ofstad, Zuker & Reiser. [Visual place learning in Drosophila melanogaster](https://doi.org/10.1038/nature10131). Nature (2011).
6. [ESP32-HUB75-MatrixPanel-DMA: supported panels and driver chips](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA#readme).
