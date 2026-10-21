---
title: Checks and troubleshooting
description: Use an observable response to check each stage before running an experiment.
section: Software
---
Test one subsystem at a time. First establish that the controller runs, then check its signals, then add the load. This keeps a wiring problem from being mistaken for a software problem.

## First-run checks

| Check | What you should be able to observe | If it does not happen |
| --- | --- | --- |
| Controller connection | The selected board appears on a computer port | Check the data cable, board selection and USB connection |
| Program upload | The IDE reports completion and the board restarts | Read the first compiler or upload error; confirm the intended board and port |
| Temperature sensor | A plausible reading that responds to a gentle temperature change | Check sensor power, ground and the data pins before enabling heating |
| Single target | The commanded physical tile changes temperature in the intended direction | Check the letter-to-channel mapping, enable signals and Peltier polarity |
| Single LED panel | The panel test shows expected colours and edges | Check input connector, ribbon orientation, power and the sketch's pin map |
| Whole display | Each target letter produces the expected panorama state | Check the panel chain, radio destination and controller program |
| Recording | A saved file opens and contains the expected time span | Check recording software, port ownership, frame rate and available storage |

## A command does nothing

Confirm which board owns the open serial port. A master command is not necessarily a valid command on the display or ring. Check the baud rate and line ending, then try the simplest command documented for that board. Close other applications that may already hold the same serial port.

## A tile heats when it should cool

Peltier heat flow depends on current direction. The master uses LPWM for heating and RPWM for cooling with its documented wiring. The alternative bench controller uses different pin assignments and direction conventions. Stop the output, identify the active sketch, and check the driver connections before changing the setup.

## Temperature changes over repeated trials

Look at the complete temperature trace, not only the minimum. Check whether the underside is accumulating heat, whether airflow is obstructed and whether a sensor has moved. The target master follows preset PWM values; it does not correct those outputs from measured target temperatures. Changes in room temperature or heat-sink conditions can therefore change the achieved temperature.

## Stopping one controller leaves another warm

The background and ring are independent. The master `STOP` command stops target drive and blanks the display; it does not stop their thermal loops. Use the shutdown sequence on the [run page](../operation.md#stop-and-shut-down).

## Record the working configuration

Keep the controller labels, sketch filenames, board-package versions, library versions, supply ratings, target mapping and a photograph of the final wiring together. After changing one of these, repeat the relevant component check before collecting behavioural data.
