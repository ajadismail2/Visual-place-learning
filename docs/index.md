---
title: Visual place learning in Drosophila
description: Studying visually guided navigation with a makerspace-built thermal arena, accessible electronics and individual fly tracking.
section: Home
---

# Visual place learning in Drosophila

<div class="home-intro" markdown="1">

<div markdown="1">

We study visual place learning in *Drosophila* using a heated walking arena, a cool target and surrounding visual landmarks.

This site documents our adaptation of the assay: apparatus, controller programs, CAD files and behavioural analysis.

[Explore the apparatus](hardware/index.md){: .home-link } [Follow the analysis](analysis/index.md){: .home-link }

</div>

<figure class="home-figure arena-photo"><img src="hardware/images/LED.jpg" alt="Overhead photograph of the circular arena surrounded by green LED panels" width="187" height="185"><figcaption>The arena inside the eight-panel visual display.</figcaption></figure>

</div>

<div class="home-facts"><span><strong>20 cm</strong> walking arena</span><span><strong>4</strong> selectable targets</span><span><strong>8</strong> LED panels</span><span><strong>Individual</strong> fly trajectories</span></div>

## Visual place learning

Flies learn the location of a cool target relative to surrounding visual cues.

Ofstad, Zuker and Reiser linked this behaviour to the **ellipsoid body**. Silencing specific ring-neuron populations impaired place learning while sparing several sensory and motor functions; the mushroom-body manipulations tested did not produce the same deficit. [1](#reference)

## Experimental basis

In the original assay, the target and panorama moved together between trials. Flies reached the target faster and by shorter routes during training. Learning weakened in darkness or with uncoupled cues. During an uncooled probe trial, trained flies searched where the panorama predicted the target. [1](#reference)

Target-reaching time alone does not establish visual memory; cue relationships and control conditions are essential.

## Apparatus

The build uses standard electronics and locally fabricated supports.

<div markdown="1">

<div markdown="1">

**Temperature.** Sixty Peltier modules heat the background; four independently driven tiles provide cooling targets. Underside cooling removes heat from the modules.

**Display.** Eight 64 × 32 LED panels form an octagon, with printed supports and a hinged access panel.

**Control and structure.** ESP32 and Arduino boards control the display and thermal circuits. A wooden base supports the arena; PVC and printed fittings hold the infrared lights. Editable CAD files are provided.

</div>


</div>

## What we measure

An overhead camera records flies under infrared illumination. AMADEUS supplies individual tracks; the analysis GUI aligns them with the video and target schedule.

Outputs include target-reaching time, trajectories, distance, speed and occupancy. Target success requires three continuous seconds inside the selected region, with movement allowed. Tracks are reviewed against the video before analysis.

<figure class="home-figure analysis-photo"><a href="assets/analysis/analysis-gui.png"><img src="assets/analysis/analysis-gui.png" alt="Arena analysis application showing individual fly tracks, four target regions and trial controls" loading="lazy" width="1950" height="1345"></a><figcaption>The analysis interface links each fly's movement to the target selected for that trial.</figcaption></figure>

## Build and analysis documentation

<div class="section-cards" markdown="1">

[**01 · HARDWARE**<br><span>Arena construction, thermal control, wiring, visual display and imaging.</span>](hardware/index.md)

[**02 · SOFTWARE**<br><span>Controller programs, installation, operating procedures and checks.</span>](firmware/index.md)

[**03 · ANALYSIS**<br><span>AMADEUS tracking, target registration and behavioural measurements.</span>](analysis/index.md)

[**04 · CAD**<br><span>Editable STEP files and the role of each fabricated part.</span>](cad/index.md)

</div>

<p class="source-note" id="reference"><strong>1 · Reference</strong><br>Ofstad, T. A., Zuker, C. S. &amp; Reiser, M. B. <em>Visual place learning in Drosophila melanogaster.</em> Nature 474, 204–207 (2011). <a href="https://doi.org/10.1038/nature10131">doi:10.1038/nature10131</a> · <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3169673/">Full text</a></p>
