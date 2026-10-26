---
title: Checks and troubleshooting
description: Use an observable response to check each stage before running an experiment.
section: Software
---
Test each subsystem separately: controller, signals, then load.

## First-run checks

| Check | What you should be able to observe | If it does not happen |
| --- | --- | --- |
| Controller connection | The selected board appears on a computer port | Check the data cable, board selection and USB connection |
| Program upload | The IDE reports completion and the board restarts | Read the first compiler or upload error; confirm the intended board and port |
| Temperature sensor | A plausible reading that responds to a gentle temperature change | Check sensor power, ground and the data pins before enabling heating |
| Single Peltier plate | The commanded Peltier plate changes temperature in the intended direction | Check the A–D mapping, enable signals and Peltier polarity |
| Single LED panel | The panel test shows expected colours and edges | Check input connector, ribbon orientation, power and the sketch's pin map |
| Whole display | Each A–D letter produces the expected panorama state | Check the panel chain, radio destination and controller program |
| Recording | A saved file opens and contains the expected time span | Check recording software, port ownership, frame rate and available storage |

## A command does nothing

Check the board, serial port, baud rate and line ending. Use a command supported by that board, and close other applications using the port.

## A Peltier plate heats when it should cool

Stop the output and check the active sketch, driver wiring and Peltier polarity. The Peltier-plate controller uses LPWM for heating and RPWM for cooling; the alternative bench controller uses different assignments and conventions.

## Temperature changes over repeated trials

Inspect the full temperature trace for heat accumulation, obstructed airflow or a displaced sensor. Peltier-plate PWM is preset, without temperature feedback; ambient and heat-sink conditions affect the achieved temperature.

## Stopping one controller leaves another warm

Peltier-plate `STOP` disables the four Peltier plates and blanks the display. Background and ring controllers remain active. Follow the [shutdown sequence](run-an-experiment.md#stop-and-shut-down).

## Record the working configuration

Save board labels, sketch filenames, package and library versions, supply ratings, Peltier-plate mapping and a wiring photograph. Repeat affected checks after changes.
