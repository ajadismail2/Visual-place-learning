---
title: LED panels
description: P4 panel selection, visual stimulus timing and affordable alternatives for the arena.
section: Hardware
---
Eight P4 RGB LED panels surround the walking arena. They show green bars against a dark background, providing visual landmarks whose position changes with the selected cooling target. The display ESP32 continuously refreshes the panels while the pattern remains fixed within a trial.

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

Waveshare specifies up to 20 W per P4 panel and a 5 V / 4 A supply rating. These are component ratings, not measurements of our green-bar pattern. Panel power comes from the supply, not from ESP32 pins or its USB connection. [1](#references)

## Why use a fast LED display?

The experimental stimulus is the spatial pattern of bars. Unintended flicker would add a second visual stimulus. Reiser and Dickinson developed LED arenas specifically for controlled insect vision experiments, discussing the limitations of conventional display timing for fast insect visual systems. [2](#references)

Fly vision does not have one fixed temporal cutoff. Juusola and Hardie found that Drosophila photoreceptor responses become faster as illumination increases; their companion study showed that temperature also changes response bandwidth. Timing therefore needs to be assessed under the experiment's lighting and thermal conditions. [3, 4](#references)

Our display sketch requests `min_refresh_rate = 1000`, or a nominal one-millisecond refresh period. This is a design target intended to keep scanning rapid while the landmarks remain stable. It is not a measured 1000 Hz optical output, and the literature does not establish this particular panel and setting as biologically optimal.

Three different rates matter:

| Rate | What changes |
| --- | --- |
| Panel refresh | Repeated electrical scanning of the existing image |
| Pattern update | A new A–D visual state is drawn at a trial transition |
| Camera frame rate | Behaviour images are recorded for tracking |

A 24 fps behaviour recording cannot establish that an LED display refreshes at 1000 Hz.

## Pixel pitch and visible landmarks

Refresh rate controls temporal presentation. Pixel pitch and viewing distance determine spatial sampling. Faster refresh does not make individual pixels more spatially resolvable to the fly.

For a centred view of a flat panel, a 4 mm pitch spans approximately **1.43° at 160 mm**. An 11-pixel bar spans 44 mm, or **15.66°** at that distance. These are geometric calculations, not measurements of fly visual acuity. The relevant stimulus is the multi-pixel bar and its contrast with the background. The place-learning assay uses the relationship between the visual panorama and the target location. [5](#references)

P4 provides a practical pixel grid for these broad bars without needing a fine-pitch video wall. The animal's viewing angle changes as it walks, so calculate dimensions from the installed enclosure rather than treating the centre example as valid everywhere. Use the [geometry chapter and calculator](../build/visual-angle.md) for bar width and elevation.

## Affordable alternatives

**Waveshare is not required.** A lower-cost panel from another supplier can serve the same role. Expensive video-wall controllers and finer pixel pitches are unnecessary for reproducing the documented bar patterns, provided the replacement gives the required geometry, contrast and timing.

For the least disruption, choose a **64 × 32, P4, 1/16-scan panel with a driver chip supported by ESP32-HUB75-MatrixPanel-DMA**. Confirm the chip and row-addressing arrangement with the seller. The library documents both supported and unsupported panel families; some newer panels with their own PWM engines are incompatible despite having a HUB75-style connector. [6](#references)

| Check before substitution | Why it matters |
| --- | --- |
| Driver chip and scan arrangement | Determines whether the library can drive the panel |
| Pitch, dimensions and mounting holes | Determines the enclosure geometry and printed supports |
| Panel resolution and orientation | Must match the firmware's coordinate mapping |
| Supply rating and logic levels | Must match the power wiring and ESP32 interface |
| Actual light output | Brightness, contrast and temporal modulation must be checked |

Compatibility is necessary, but it does not by itself make two panels equivalent visual stimuli. A pitch change requires a new angle calculation; a different chip may require a different driver setting.

## Check the assembled display

Test one panel first, then the complete eight-panel chain. Check the A–D states, continuity across panel boundaries and any ghost pixels. Keep brightness fixed during comparisons.

For a timing check, place a fast photodiode facing a lit area and record its signal with an oscilloscope. Inspect the pulse train and any slower brightness modulation on several rows and panels, using the actual pattern and brightness setting. Record a pattern transition as well as a steady state. A library timing estimate is useful for diagnosis; the photodiode measures emitted light. Phone video or the behaviour camera can reveal some artefacts but cannot certify their absence.

[Library operation and settings](../software/led-library.md) · [Display wiring](../build/wiring.md#display-board-pin-map) · [Display controller code](../firmware/display.md)

## References

1. [Waveshare: RGB-Matrix-Px-64x32 specifications](https://docs.waveshare.com/RGB-Matrix-Px-64x32).
2. Reiser & Dickinson. [A modular display system for insect behavioral neuroscience](https://doi.org/10.1016/j.jneumeth.2007.07.019). Journal of Neuroscience Methods (2008).
3. Juusola & Hardie. [Light adaptation in Drosophila photoreceptors I: response dynamics and signaling efficiency](https://doi.org/10.1085/jgp.117.1.3). Journal of General Physiology (2001).
4. Juusola & Hardie. [Light adaptation in Drosophila photoreceptors II: rising temperature increases the bandwidth of reliable signaling](https://doi.org/10.1085/jgp.117.1.27). Journal of General Physiology (2001).
5. Ofstad, Zuker & Reiser. [Visual place learning in Drosophila melanogaster](https://doi.org/10.1038/nature10131). Nature (2011).
6. [ESP32-HUB75-MatrixPanel-DMA: supported panels and driver chips](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA#readme).
