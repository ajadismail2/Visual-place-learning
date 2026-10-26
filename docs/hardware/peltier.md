---
title: Background temperature control
description: Peltier operation and temperature feedback for the 60-module background.
section: Hardware
---
Sixty Peltier modules regulate the background temperature independently of the four cooling targets.

## Heat transfer

Peltier current direction determines heat-flow direction. Cooling the walking face requires heat removal from the underside.

Achieved temperature depends on current, thermal contact and heat dissipation. Verify polarity by measuring the installed module.

## Background circuit

Sixty modules form one series circuit with a single power-control output.

An Arduino reads the TMP117 over I²C and drives the external power stage from pin 9.

<figure class="photo-slot" data-photo-id="background-sensor"><div class="photo-space" aria-label="Blank photograph of the background modules and temperature sensor"></div><figcaption><span>Photo · H08</span><strong>Background circuit and sensor position</strong></figcaption></figure>

## PID control

PID feedback adjusts the background output using the TMP117 reading.

Tune gains against measured stability at the installed sensor position.

## Feedback loops

![Independent background and thermal-ring temperature feedback loops](../assets/setup/feedback-loops.svg)

The background and ring use separate feedback loops. The four targets follow timed PWM commands; thermal-camera measurements do not feed back to their controller.

## Connect and check the background

1. Secure the sensor against the controlled surface.
2. Connect sensor supply, GND, SDA and SCL; connect Arduino pin 9 to the power stage. See [wiring](wiring.md#supplied-arduino-thermal-controllers).
3. Upload and check readings with load power disconnected; control starts automatically at power-up.
4. Verify supply ratings and Peltier polarity before enabling power.
5. Record warm-up and a full trial sequence, including centre and perimeter temperatures.

Defaults: **34.8 °C setpoint**, **150/255 maximum PWM**, and **100 ms sensor interval** with filtering. The setpoint applies at the sensor location.

## Measure the whole floor

Map target and background temperatures across a complete sequence to assess gradients and thermal drift.

See [thermal imaging](../hardware/imaging.md#set-up-the-thermal-camera) for measurement details.

[Background code](../firmware/background.md) · [Four-target control](four-channels.md) · [Heat removal](thermal-coupling.md)
