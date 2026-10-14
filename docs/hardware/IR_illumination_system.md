---
title: Infrared illumination
description: Stable imaging contrast without using the visual panorama as the recording light source.
---
## Current configuration

The project uses **850 nm IR rings powered at 12 V**, with a later configuration using **four rings**. These illuminate the flies for the overhead monochrome camera while the LED surround supplies the experimental landmarks. Earlier notes reported approximately 0.6–0.7 A for a tested IR setup; this is not a guaranteed current specification for every four-ring assembly.

## Uniformity and reflections

Evaluate the entire walking surface in the captured image. Glass, aluminium, fasteners, arena edges, and printed parts can create reflections or shadows that resemble animals or hide them. A ring arrangement should be assessed using fixed camera settings, including the corners of target regions and the perimeter.

For a useful illumination validation record, retain an empty-arena frame, representative animal frames, and images of the most reflective areas. Compare contrast at several positions, and check whether moving the target or changing the visual display produces imaging artefacts.

## Mechanical support

The IR assembly has been developed with a PVC support, a lampshade or surrounding fixture, and printed holders. The latest mechanical work addresses a support that peeled away under the moment from the pipe and lighting load. The problem is a complete load path—from fixture through pipe and base to the table—not simply the size of a fillet.

The project preference is a stable adhesive-supported base where feasible. Validate resistance to tipping and peel under the assembled load before experiments, and preserve a fixed camera/illumination relationship throughout a session. See [mechanical design](../software/3d_CAD.md) for the current development record.

## Imaging checks

- No clipped bright regions on the animal bodies at the chosen exposure.
- No persistent dark zones near the arena edge or target.
- No changing shadows from moving cables, panel doors, or the experimenter.
- Stable frame brightness over the full recording, not just a short preview.
- Sufficient contrast for both isolated flies and touching animals.

Illumination quality influences detection; it does not by itself establish individual identity. A well-lit crossing can still be ambiguous when two animals have indistinguishable appearances.
