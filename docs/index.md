---
title: The visual place-learning arena
description: A practical build and operating manual for a temperature-controlled behavioural arena.
section: Overview
---
A guide to assembling, connecting and operating the arena. Start with the physical components, then load the controller programs and check each subsystem before running an experiment.

<div class="section-cards" markdown="1">

[**01 · HARDWARE**<br><span>Arena, temperature control, ESP32 and Arduino wiring, visual display and cameras.</span>](hardware/index.md)

[**02 · SOFTWARE**<br><span>Install the programs, pair the controllers, test responses and run a sequence.</span>](firmware/index.md)

[**03 · CAD**<br><span>Printed components and their positions in the assembly.</span>](cad/index.md)

</div>

<figure class="photo-slot hero-photo" data-photo-id="overview-arena"><div class="photo-space" aria-label="Blank space for the assembled arena photograph"></div><figcaption><span>Photo · A01</span><strong>The assembled arena</strong></figcaption></figure>

## How the system works

The walking area is **20 cm in diameter**. Sixty Peltier modules form the heated background, and four target modules are controlled separately. During a trial, one target cools while the remaining targets heat. Eight LED panels surround the arena and display the visual pattern associated with the selected target.

The target ESP32 runs the sequence and sends the corresponding state to the display ESP32. Separate temperature controllers regulate the background and perimeter ring. A behaviour camera records movement; temperature measurements check whether the intended thermal conditions were achieved.

## If you are starting from scratch

Read [Hardware](hardware/index.md) first to identify the components and distinguish signal wiring from load power. Then follow [Install and upload](software/upload.md), test each part, and use the [experiment procedure](operation.md). Keep the wiring labels and temperature records with the video.

## How to use this manual

Each hardware chapter explains the component's role, its connections, and what to observe during a first test. The software chapters explain commands in plain language before showing the downloadable source code.

The documented pin maps follow the supplied sketches. Proposed changes are marked where they occur. Temperature setpoints describe what a controller requests; they are not experimental temperature readings.
