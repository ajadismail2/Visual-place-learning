---
title: Checks and troubleshooting
description: Use an observable response to check each stage before running an experiment.
section: Software
---
Test each subsystem separately: controller, signals, then load.

## A command does nothing

Check the board, serial port, baud rate and line ending. Use a command supported by that board, and close other applications using the port.

## A Peltier plate heats when it should cool

Stop the output and check the active sketch, driver wiring and Peltier polarity. The Peltier-plate controller uses LPWM for heating and RPWM for cooling; the alternative bench controller uses different assignments and conventions.

## Temperature changes over repeated trials

Inspect the full temperature trace for heat accumulation, obstructed airflow or a displaced sensor. Peltier-plate PWM is preset, without temperature feedback; ambient and heat-sink conditions affect the achieved temperature.

## Stopping one controller leaves another warm

Peltier-plate `STOP` disables the four Peltier plates and blanks the display. Background and ring controllers remain active. Follow the [shutdown sequence](how-to-run-an-experiment.md#stop-and-shut-down).

## Record the working configuration

Save board labels, sketch filenames, package and library versions, supply ratings, Peltier-plate mapping and a wiring photograph. Repeat affected checks after changes.
