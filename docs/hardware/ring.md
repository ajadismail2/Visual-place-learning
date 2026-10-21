---
title: Thermal ring
description: How the perimeter heater, temperature sensor and controller work together.
section: Hardware
---
The ring surrounds the walking area. Its heater is controlled separately from the floor, so the perimeter temperature can be adjusted without changing the four target outputs. The ring controller responds to its own temperature sensor; it does not measure the temperature of every point in the enclosure.

<figure class="photo-slot" data-photo-id="ring-heater"><div class="photo-space" aria-label="Blank photograph of the ring heater and sensor"></div><figcaption><span>Photo to add · H05</span><strong>Ring, heater and sensor mounting</strong><p>Show where the heater is attached, how it is electrically insulated and where the sensor touches the ring.</p></figcaption></figure>

## What each part does

The heater converts electrical power into heat. A MOSFET power stage acts as an electronically controlled switch between the heater and its supply. The Arduino sends a PWM signal to this stage, so heater power can be varied without passing heater current through the Arduino.

The OneWire sensor sends a temperature reading back to the controller. The program compares this reading with its target and changes the PWM output. This is a closed loop: measurement changes the next output. Without feedback, the same power setting could give different temperatures as room conditions or airflow change.

## Wire and mount the ring

1. Fit the ring support so the perimeter stays fixed relative to the walking surface. Check the glass-cover fit and fly clearance against the actual assembly.
2. Secure the heater using the intended electrical insulation and mounting method. Keep exposed conductors away from metal parts they are not meant to contact.
3. Fix the sensor at a reproducible position with reliable thermal contact. A loose sensor may read cooler than the ring and cause excessive heater drive.
4. Connect sensor data to Arduino pin 2 and the power-stage control input to Arduino pin 9. Use the [wiring guide](../build/wiring.md#background-ring-and-camera) for power and ground connections.
5. Check a plausible sensor reading before enabling heater power. Observe the reading and an independent temperature reference as the ring warms.

## Setpoint and cutoff

The supplied code targets **45 °C at the sensor** and stops heating above **57 °C**. It can resume after the reading falls again. This cutoff is not a separate, latching hardware protection, and the sensor temperature should not be described as the temperature of all enclosed air.

The sensor model, insulation thickness, wire routing and exact ring dimensions still need assembly records. Keep these fields with the ring's future photographs and CAD files.

## Stopping the heater

Stopping an experiment on the master does not stop this controller. The supplied ring sketch has no `STOP` command. Switch off its heater supply separately and verify cooling before handling it. Use the syntax-corrected ring sketch when uploading; the [program page](../firmware/ring.md) explains the correction and serial commands.
