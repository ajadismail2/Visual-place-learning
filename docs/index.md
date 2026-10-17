---
title: Visual place-learning apparatus
description: Equipment, assembly, temperature control and firmware for the arena.
section: Overview
---
The apparatus consists of a circular arena with a **measured inner diameter of 20 cm**, a heated background of 60 Peltier modules, four cooling targets and eight LED panels. The targets are controlled independently, and the LED pattern changes with the selected target.

## System operation

Temperature feedback regulates the background and thermal ring. During a trial, one target cools while the other three heat. Separate ESP32 boards control the target sequence and display. A thermal camera records the temperature distribution.

## Documentation

<div class="chapter-list" markdown="1">

[**Published arena specifications**<br><span>Reference dimensions, materials and components from the original paper.</span>](build/published-specifications.md)

[**Equipment and materials**<br><span>Thermal components, electronics and fabricated parts.</span>](build/equipment.md)

[**Arena assembly**<br><span>Base, aluminium carrier and printed mounts.</span>](build/arena.md)

[**PCB and wiring**<br><span>Power connections, ESP32 pin assignments and diagrams.</span>](build/pcb.md)

[**Temperature control**<br><span>Background feedback, target cooling and heat removal.</span>](build/peltier.md)

[**Visual display**<br><span>Panel distance, bar width and angular calibration.</span>](build/visual-angle.md)

[**Operating procedure**<br><span>Controller setup, trial sequence and shutdown.</span>](operation.md)

[**Code and downloads**<br><span>Programs for control, measurement and component tests.</span>](firmware/index.md)

</div>
