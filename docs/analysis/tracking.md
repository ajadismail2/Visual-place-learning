---
title: Tracking with AMADEUS
description: How AMADEUS learns from the recording and why it fits this arena's position-based analysis.
section: Analysis
---
AMADEUS learns to locate animals from the recording itself, without manually labelled training frames. It represents each animal with an **oriented bounding box**, a rectangle that follows the body's position and angle.

## How tracking works

First, segmentation separates animals from the background. Isolated animals provide training examples; movement supplies initial direction labels. Copies of these examples are combined into synthetic crossings and clusters. A YOLO detector learns to recognise animals in these arrangements, then temporal association links detections into individual tracks. Direction and identity refinement are separate from simply detecting a body. [Method and preprint](https://www.biorxiv.org/content/10.64898/2026.09.19.752854v1).

![How isolated animal images become training examples and reviewed identity tracks](../assets/analysis/tracking-method.svg)

*Method diagram, not an experimental recording.*

## Why we use it for this arena

The main requirement is to keep each fly's identity attached to its path, especially when similar-looking flies meet. Detailed limb poses are not needed to measure entry into a cool target. Our earlier SLEAP workflow showed identity swaps during close contact and missed detections near the arena edge. AMADEUS provides a practical fit through recording-specific training, synthetic interaction examples and an identity-review workflow.

| Requirement | AMADEUS in this workflow | SLEAP |
| --- | --- | --- |
| Main representation | Body box and centre position | User-defined body keypoints and pose |
| Training preparation | Examples generated from segmented video | A labelled pose dataset |
| Arena measurements | Centre coordinates feed directly into the target GUI | Pose coordinates require a chosen tracking point |

This is a workflow choice, not a measured accuracy ranking. SLEAP remains useful for pose-based questions. AMADEUS tracks also need review around occlusions; a plausible box does not prove that its identity is correct. [SLEAP documentation](https://sleap.ai/).

## Tracking sequence

1. Open **Easy Tracking**, select the video and session, then **Launch Segmentation**.
2. Adjust foreground extraction so complete isolated flies are blue/cyan. Contacting flies, fragments and other outliers should be orange. Check several frames, including the arena edge.
3. Process segmentation, enter the animal count and select overlap severity and backward-motion settings.
4. Run training and tracking. **Advanced Tracking** exposes the individual stages. Very heavy overlap adds contrastive identity verification, with extra processing cost.
5. Review the overlay in **Refinement**, correct remaining errors and retain the final reviewed CSV.

Use the [official AMADEUS manual](https://amadeus.jpmyrmecol.com/Manual_EN.html) for the current installation and control names. In this workflow, stable lighting, a fixed camera and clean isolated examples are the starting conditions for useful training.

## Hand-off to the arena GUI

Keep the exact video geometry used by AMADEUS. The analysis loader expects a wide CSV with a `frame` column and paired centre columns such as `cx0, cy0, cx1, cy1`. Box width, height and heading columns are optional. Original AMADEUS IDs are preserved.

[Continue to the analysis GUI](gui.md)
