---
title: Why Peltier modules
description: Reversible heating and cooling made standard modules useful; heat removal and measurement determined whether the arrangement worked.
section: 02 / Thermal method
---
## One component, two directions of heat flow

A Peltier module contains p-type and n-type semiconductor elements between ceramic faces. Electrical current transports heat through these elements; reversing the current reverses the direction of heat pumping. That gave us a way to make the same target surface warm or cool without changing the mechanical part. The [manufacturer's explanation](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref02/) describes the underlying construction.

The module also generates resistive heat. Its cold face absorbs heat from the target, while its hot face must release that heat **plus the electrical input**. A cold spot on top therefore does not mean that the complete assembly is losing heat.

## Separate the background from the targets

The project used **60 modules in a series-connected background circuit** and **four targets with separate control**. In an early test, the background string drew approximately **0.30 A at 20 V**. That is about **6 W of electrical input to the whole string**, not 6 W per module and not a measurement of heat delivered to the walking surface.

Generic modules made a tiled floor possible with standard parts. Their common current in the series string did not guarantee equal surface temperatures: contact, position, and heat flow still differed across the assembly.

## Why sensing became a design problem

A temperature probe on the top face could obstruct the flies, so we investigated thermal imaging and sensors away from the walking surface. An early MLX90640 test reported a nearly unchanged reading while the target was physically cooling. The measurement location and the controlled surface therefore had to be checked before relying on feedback.

An especially useful March test showed the two sides moving in opposite directions: the reported top reading fell from **32.59 to 30.25 °C**, while the bottom rose from **33.10 to 40.26 °C**. Those readings belong to that bench test. They explain why a fixed bottom-to-top temperature offset could not be assumed for every PWM level or heating history.

<div class="build-sheet" markdown="1">

### What changed in the controller

**Early approach:** sensor feedback and PID adjusted the electrical drive against a measured temperature.

**Constraint:** the sensor could not remain on the target during the experiment, and an underside reading was not automatically a top-surface reading.

**Later approach:** manual heat/cool tests led to timed drive stages and separate settings for each target. The current master follows those stages without temperature feedback.

</div>

## A timed command is not a temperature

The intended warm surface is around **36 °C**, with the selected target around **23–25 °C**. In the supplied October controller, the cooling command decreases in stages to limit prolonged high drive. A separate short heating boost returns a just-cooled target toward the warm state.

This is an empirical control approach. A particular PWM value depends on the supply, mounting, room conditions, and starting temperature. The [four-channel record](four-channels.md) gives the current code settings; the [shared-heat discussion](thermal-coupling.md) explains why measurements of the full assembly are still needed.

<p class="source-note">Project tests: February–March 2026; manual-control requests: August 2026; controller reviewed: 15 October 2026. Temperature values above are reported bench observations, not a replicated performance specification.</p>
