---
title: Where the heat goes
description: Separate electrical control does not isolate the four targets from the rest of the thermal assembly.
section: 06 / Whole-arena behaviour
---
## Cooling the top warms the other side

In cooling mode, a target module pumps heat away from its top face. Its underside releases that heat together with the electrical energy supplied to the module:

<div class="equation">Q<sub>hot</sub> = Q<sub>cold</sub> + P<sub>electrical</sub></div>

These quantities are heat-flow rates and power, measured in watts. With PWM, the electrical input is the time-average of voltage × current; a command fraction alone does not tell us the watts. The relation follows the [thermoelectric energy balance](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref11/).

## The four targets share a thermal environment

The targets, surrounding modules, aluminium support, thermal ring, and enclosed air exchange heat. A colder target can draw heat laterally from the warm floor. Its rejected heat can also raise the support temperature if the assembly cannot remove it fast enough. The rise of the bottom reading during the March cooling test is consistent with this mechanism; it does not, by itself, measure how much each neighbouring region warmed.

During a normal training trial, **one target cools and three heat**. They are four selectable cooling locations, not four simultaneous cooling loads. Changing the selected target changes both the location of heat extraction and the recent heating history of the assembly.

If all four were commanded to cool, their rejected heat rates would add at the receiving side. The floor might cool locally while the shared support warmed. Whether the walking surface as a whole became warmer or colder would depend on heat removal, contact, background drive, and time—not just the number of targets labelled “cool”.

## What the early overheating taught us

The early background test reached the intended warm temperature, then continued warming under the covered arena. The later work therefore separated several questions: what the target surface was doing, what the supporting plate was doing, and whether the enclosed environment was accumulating heat.

The glass cover and heated boundary were part of that system. A single sensor could not describe every region. Nor could equal PWM commands establish that A, B, C, and D behaved identically. Per-target heating values and the post-cooling recovery stage address differences in drive history; they do not eliminate physical heat transfer between targets.

<div class="build-sheet" markdown="1">

### The comparison needed for the assembled arena

Record the background, active target, adjacent region, and support temperature on the same time axis. Compare an all-warm baseline with A, B, C, and D cooling in turn, under the same cover, supply, and starting conditions. Repeat the actual trial order to capture accumulated heat.

This is the measurement needed to quantify the interaction. A complete set of these curves is not yet in the available build record, so the site does not assign an invented temperature rise to the neighbouring tiles.

</div>

## Heat sinking is part of the apparatus

A heat sink must reject the pumped heat and the module's electrical losses. If its temperature rises, cooling performance changes. Heatsinks, external airflow, and revised temperature sensing were explored during troubleshooting. The record does not establish a final validated heatsink configuration. [Ferrotec's heat-sink guidance](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref05/) explains this dependency; applying it to this arena requires measurements of the actual assembly.

<p class="source-note">Early overheating reports: February 2026. Top/bottom cooling observations: March 2026. Background/target interaction revisited: July 2026. The heat-flow explanation is a physical interpretation, not a fitted thermal model of this apparatus.</p>
