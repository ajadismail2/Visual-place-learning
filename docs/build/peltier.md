---
title: Background temperature control
description: Peltier operation and temperature feedback for the 60-module background.
section: Thermal system
---
A Peltier module transfers heat between its two faces. Reversing the current reverses the heat flow, allowing the walking surface to be heated or cooled.

The hot side rejects the heat extracted from the cold side plus the electrical input. This heat must be removed from beneath the arena.

## Background circuit

The 60 background modules form one series circuit. A TMP117 sensor measures temperature, and the controller changes PWM to reduce the difference between that reading and the setpoint.

## Why closed-loop control is used

Room temperature, airflow and heat from the cooling targets change the heating requirement. Feedback adjusts the power as these conditions change. PID control uses the current temperature error, accumulated error and rate of change to set the output.

The background code starts at **34.8 °C** and limits PWM to **150/255**. These values define the controller settings. Surface measurements are needed to determine the temperature distribution across all 60 modules.

[Background code](../firmware/background.md) · [Four-target control](four-channels.md) · [Heat removal](thermal-coupling.md)
