---
title: Development record
description: What changed, what is available, and what still needs experimental validation.
---
## October 2026: current update

This edition brings the website into line with the latest project record and replaces the earlier generic documentation template. It separates the research question, apparatus, methods, analysis, preliminary observations, and reusable resources.

| Area | Latest incorporated change | Evidence/status |
| --- | --- | --- |
| Display firmware | ESP-NOW slave, 256 × 64 canvas, exact state offsets and pin map | Supplied `LED_Slave.ino` reviewed for documentation |
| Stimulus geometry | Exact lit-pixel extents, diagonal slope, height-aware angle calculations | Derived from source and stated geometry |
| Trial schedule | B–C–D–C–B–A–D–C–B–A; 300 s each | Current experiment specification; also present in analysis source |
| Thermal control | BTS7960 channels and staged 80/75/65/55 PWM cooling | Latest project configuration and requested programme |
| Scale | 916 px over 20 cm = 45.8 px/cm | Arithmetic correction; per-video calibration remains necessary |
| Tracking | Latest n=88 SLEAP model pair and AMADEUS evaluation | Model names and processing history recorded |
| Analysis GUI | Movement permitted during dwell; selected fly population; flexible ROI editing | Present in reviewed AMADEUS GUI v1.3.0 |
| Playback | Current fly positions continue after success | Present in reviewed GUI; exported trail behaviour documented separately |
| Mechanical access | Hinged panel with opposite-side releasable closure | Design development; hardware fit not established here |
| IR support | PVC mount stability and load-path refinements | Ongoing mechanical work |
| Sociability | Dedicated page tied to the November 2024 reference version | Distinct development direction |
| Preliminary results | Eight reported values with `nr` annotations retained | Descriptive record; metadata and validation incomplete |

## September–October: tracking and analysis

The tracking workflow progressed through several SLEAP training sets as image conditions and annotations changed. The October n=88 centroid and centred-instance pair is the latest model pair identified for the full-experiment request. Close-contact identity swaps remained a central concern, motivating evaluation of AMADEUS.

The analysis interface evolved to define success by target occupancy rather than immobility, support selective fly inclusion, allow target boxes to be drawn and deleted independently, and browse video frames during ROI selection. Main playback now follows flies after target success, while search-path exports retain the first-success stopping rule.

## September–October: mechanical and optical development

Work included level breadboard supports, a stronger PVC/IR mounting arrangement, a door-style LED panel, diffusion, enclosure materials, and a separate small Delrin arena. Prototype files are indexed as design references, not certified final assemblies.

## Earlier development retained in the repository

The early repository contains thermal-camera calibration and PID experiments, a Raspberry Pi/web-control architecture description, and an earlier SLEAP analysis pipeline. Current documentation labels these versions explicitly. Empty placeholder scripts are no longer presented as completed applications.

## Validation still open

The next substantive research milestones are a revisioned thermal master release, measured thermal and visual calibration, identity-review statistics, a complete reproducibility package for each run, and replicated behavioural comparisons. No date or outcome is invented for those milestones.

## How evidence is labelled

**Supplied source** means a file was inspected. **Project record** means a value or design decision was recorded during development. **Preliminary** means observations are available but metadata, review, or replication is incomplete. **Proposed/development** means the feature or assay should not be presented as an experimentally validated result.

For scientific background, use [references](references.md). For actual downloads, use the [resource index](files.md).
