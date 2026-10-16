---
title: Building a visual place-learning apparatus
description: A makerspace replication using standard Peltier modules, LED panels, printed fixtures, and custom controller boards.
section: Build overview
---
This is the construction record of our replication of the visual place-learning apparatus described by [Ofstad, Zuker and Reiser (2011)](https://doi.org/10.1038/nature10131). The work was in making the parts fit, controlling the temperature, and matching the visual display to the four targets using equipment and fabrication tools available in the makerspace.

The arena has a **20 cm inner diameter**, a warm background made from **60 Peltier modules**, and **four separately controlled target modules**. Eight standard P4 LED panels surround it. The background and targets share a mechanical assembly, so their temperatures cannot be treated independently.

## How the build came together

We made a wooden base and used Onshape and 3D printing for the thermal ring, illumination stands, camera case, and later mounting revisions. KiCad work covered the controller layout and ESP32 footprints. Wiring, soldering, and individual component tests connected these parts into an apparatus. The printed fixtures and standard modules let us change one part without remaking the whole assembly.

The difficult work happened between those steps: a sensor could not stay on the walking surface; cooling a target warmed its underside; different ESP32 boards needed different footprints; a display that worked over USB did not yet work reliably from the standalone supply. The pages below follow those problems and the changes made in response.

<div class="chapter-list" markdown="1">

[**01 · Making the arena**<br><span>Wooden base, CAD, printed fixtures, supports, and panel access.</span>](build/arena.md)

[**02 · Why Peltier modules**<br><span>Reversible heat flow, sensor placement, and the move to staged drive.</span>](build/peltier.md)

[**03 · PCB and connections**<br><span>ESP32 footprints, power routing, and testing the assembled boards.</span>](build/pcb.md)

[**04 · Four separate channels**<br><span>The actual pin map, individual heating values, and trial coordination.</span>](build/four-channels.md)

[**05 · Setting the visual angle**<br><span>From millimetres and viewing distance to pixels and paper templates.</span>](build/visual-angle.md)

[**06 · Where the heat goes**<br><span>How a cooling target changes the thermal load of the whole arena.</span>](build/thermal-coupling.md)

</div>

## Keeping the build affordable

The inexpensive parts were generic Peltier modules, standard HUB75 display panels, ESP32 boards, driver modules, and locally made fixtures. The savings came from adapting these components and reusing the makerspace's tools. The Thorlabs camera and breadboard remain part of the equipment cost, even when already available in the lab. We have not assigned an unsupported total price or percentage saving.

The build combined mechanical modelling, printing, basic woodworking, electronics assembly, firmware, and temperature measurements. Reviewing the apparatus with lab members connected the fabrication work to the requirements of the experiment. This record concentrates on that work; the original study supplies the research background.

<p class="source-note">Build notes compiled through 16 October 2026. Firmware details refer to the supplied 15 October revisions. <a href="resources/sources/">Sources and revision record →</a></p>
