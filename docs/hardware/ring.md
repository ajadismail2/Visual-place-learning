---
title: Thermal ring
description: How the perimeter heater, temperature sensor and controller work together.
section: Hardware
---
The perimeter heater has its own temperature sensor and controller, independent of the floor and four Peltier plates.

<figure class="photo-slot" data-photo-id="ring-heater"><div class="photo-space" aria-label="Blank photograph of the ring heater and sensor"></div><figcaption><span>Photo · H05</span><strong>Ring, heater and sensor mounting</strong></figcaption></figure>

## Control

An Arduino regulates heater PWM through a MOSFET using OneWire temperature feedback.

## Wire and mount the ring

1. Fit the ring and check glass cover clearance.
2. Insulate and secure the heater.
3. Fix the sensor in reliable thermal contact; detachment can cause excessive heating.
4. Connect sensor data to Arduino pin 2 and MOSFET control to pin 9. See [wiring](../hardware/wiring.md#background-ring-and-camera).
5. Verify readings against an independent thermometer during warm-up.

## Setpoint and cutoff

Setpoint: **45 °C at the sensor**. Heating stops above **57 °C** and can resume after cooling. The cutoff is software-based and does not latch.

## Stopping the heater

The sketch has no `STOP` command. Switch off the ring supply separately from Peltier-plate control. Use the [syntax-corrected sketch](../firmware/ring.md).
