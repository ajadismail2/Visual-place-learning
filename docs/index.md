---
title: Visual place learning in Drosophila
description: A custom-built system for studying visually guided place learning in individual Drosophila.
section: Home
---

# Visual place learning in Drosophila

<div class="home-intro" markdown="1">

<div markdown="1">

This custom-built system is used to study how individual *Drosophila* learn the location of a cool target from surrounding visual cues. It adapts the place-learning assay described by Ofstad, Zuker and Reiser using accessible electronics and locally fabricated parts. [1](#reference)

The documentation covers:

- **Experimental procedure:** preparing the apparatus, running trials and recording the experiment.
- **Hardware and assembly:** the arena, Peltier temperature system, visual display, illumination and cameras.
- **Controller software:** installation, configuration and operation of the Arduino and ESP32 programs.
- **Tracking and analysis:** AMADEUS tracking, target registration and behavioural measurements.

[Explore the hardware](hardware/index.md){: .home-link } [Run an experiment](operation.md){: .home-link } [Follow the analysis](analysis/index.md){: .home-link }

</div>

<figure class="home-figure arena-photo"><img src="hardware/images/LED.jpg" alt="Overhead photograph of the arena surrounded by green LED panels" width="187" height="185"><figcaption>The visual place-learning arena.</figcaption></figure>

</div>

This documentation describes the current apparatus and will be updated as the system develops.

## Documentation

<div class="section-cards" markdown="1">

[**HARDWARE**<br><span>Components, construction, wiring and imaging.</span>](hardware/index.md)

[**SOFTWARE**<br><span>Controller programs, installation and operation.</span>](firmware/index.md)

[**ANALYSIS**<br><span>Tracking, target registration and behavioural measurements.</span>](analysis/index.md)

[**CAD**<br><span>Editable STEP files for fabricated parts.</span>](cad/index.md)

</div>

<p class="source-note" id="reference"><strong>1 · Reference</strong><br>Ofstad, T. A., Zuker, C. S. &amp; Reiser, M. B. <em>Visual place learning in Drosophila melanogaster.</em> Nature 474, 204–207 (2011). <a href="https://doi.org/10.1038/nature10131">doi:10.1038/nature10131</a> · <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3169673/">Full text</a></p>
