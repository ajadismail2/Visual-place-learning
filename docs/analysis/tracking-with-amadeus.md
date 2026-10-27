---
title: Tracking with AMADEUS
description: How AMADEUS learns from the recording and why it fits this arena's position-based analysis.
section: Analysis
---
AMADEUS learns from unlabelled recordings and represents each animal with an oriented bounding box.

## Choice of tracker

The tracker requires stable identities and centre coordinates, rather than detailed poses. Our earlier SLEAP workflow showed identity swaps during contact and missed detections near the edge. AMADEUS supports recording-specific training, synthetic interactions and identity review.

This choice is not a measured accuracy comparison. Review AMADEUS identities around occlusions. [SLEAP](https://sleap.ai/) remains an option for pose analysis.

See the [AMADEUS manual](https://amadeus.jpmyrmecol.com/Manual_EN.html) for installation and current controls.

<figure markdown="1" style="border: 1px solid #d6d6d6; padding: 12px; margin: 24px 0; text-align: center;">

![Amadeus tracking workflow](images/amadeusworkflow%28shouldciteinpage%29.png)

<figcaption>Amadeus tracking workflow.</figcaption>

</figure>

## Tracking data for analysis

The GUI expects a wide CSV with `frame` and paired centre columns (`cx0, cy0, cx1, cy1`, etc.). Width, height and heading are optional; original IDs are retained.

[Continue to the analysis GUI](the-analysis-gui.md)
