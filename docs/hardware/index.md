---
title: Hardware
description: Understand each part before connecting the complete apparatus.
section: Hardware
---
The arena combines a temperature-controlled walking surface, a surrounding visual display and an overhead recording system. These parts have different jobs. Understanding them separately makes the complete setup easier to assemble and test.

## What happens during an experiment?

The floor has a warm background and four independently driven target tiles. During each step, one target is cooled while the others are heated. A pattern on the surrounding LED panels gives the animal a visual reference. The camera records its movement while separate temperature measurements check the thermal conditions.

The target controller changes both the selected tile and the display state. The background and ring controllers continue to regulate their own temperatures. Starting or stopping the target sequence therefore does not start or stop every part of the apparatus.

<figure class="photo-slot" data-photo-id="hardware-complete"><div class="photo-space" aria-label="Blank space for a photograph of the complete apparatus"></div><figcaption><span>Photo · H01</span><strong>Complete apparatus</strong></figcaption></figure>

## Follow the build in this order

| Stage | What to understand | What to check before continuing |
| --- | --- | --- |
| [Arena](../hardware/arena.md) | How the floor, ring and cover define the walking space | Level surface, secure supports and no gaps around target tiles |
| [Wiring](../hardware/wiring.md) | Which wires carry power and which carry instructions | Controller identity, pin labels and supply ratings |
| [Temperature control](../hardware/peltier.md) | How sensors and power drivers regulate heat | Plausible sensor readings and correct heating direction |
| [Four targets](../hardware/four-channels.md) | How A–D are controlled separately | Each command acts on the intended physical tile |
| [Visual display](../hardware/visual-angle.md) | How the panel chain forms the panorama | Panel order, orientation and measured bar width |
| [Illumination](illumination.md) | How generic IR arrays, printed shades and PVC stands light the arena | Even lighting, secure mounts and limited reflections |
| [Cameras](imaging.md) | How movement and temperature are recorded | Focus, reflections, calibration and recording time |

## A few useful terms

**Controller:** a small programmable board that sends commands or reads sensors. The ESP32 and Arduino boards are controllers.

**Driver:** the power-handling circuit between a controller and a load. A controller pin tells the driver what to do; it does not supply enough power to run a Peltier module.

**Load:** the component that uses electrical power, such as a Peltier module, heater, LED panel or fan.

**Feedback:** a measurement returned to the controller so it can correct its output. **Open-loop control** follows preset output values without making this correction from temperature measurements.

## Configuration

The pin maps and timing tables follow the supplied programs. The target heat-sink arrangement and conversion of the thermal controllers to ESP32 are proposed changes. Supply ratings and detailed fabrication dimensions are not specified in this manual.

[Equipment list](../hardware/equipment.md) · [Software setup](../software/upload.md) · [CAD parts](../cad/index.md)
