---
title: Four separate Peltier channels
description: A, B, C, and D have independent driver connections and heating settings, coordinated by one master controller.
section: 04 / Wiring and control
---
## Separate outputs, one experiment clock

The master ESP32 controls the four target drivers. A second ESP32 drives the LED panels and receives display-state messages over ESP-NOW. This split keeps panel drawing on the display board while the master handles the heating and cooling sequence.

Each target has its own driver outputs and control pins. The master can therefore cool one target while heating the other three. The 60-module background circuit is a separate branch; the four-target command does not describe its control.

## Pin map from the current master

The physical target name, manual alias, and driver channel are different labels. Reading the executable mapping in the supplied **15 October master** gives:

| Target | Manual alias | Driver channel | RPWM | LPWM | R_EN | L_EN |
| --- | --- | --- | --- | --- | --- | --- |
| A | T1 | 2 | GPIO 25 | GPIO 26 | GPIO 13 | GPIO 15 |
| B | T4 | 4 | GPIO 19 | GPIO 18 | GPIO 2 | GPIO 16 |
| C | T3 | 1 | GPIO 32 | GPIO 33 | GPIO 4 | GPIO 5 |
| D | T2 | 3 | GPIO 27 | GPIO 14 | GPIO 22 | GPIO 23 |

Each row drives a separate module, with that module's two switched outputs connected to its Peltier. The code uses **20 kHz, 8-bit PWM**. In its heating function, LPWM is set to zero before RPWM is driven; cooling does the reverse. The physical hot/cold direction still depends on the installed Peltier polarity.

## Why all four do not use one heating value

A target that has just been cooled has a different starting condition from a target that has remained warm. The revised controller keeps a separate value for each target before its first cooling cycle and after it has cooled. It also applies **PWM 50 for 17 seconds** immediately after a target finishes cooling, before returning it to its ordinary heating value.

| Target | Preheat / before first cooling | After cooling |
| --- | --- | --- |
| A | 41 | 40 |
| B | 40 | 41 |
| C | 40 | 39 |
| D | 39 | 38 |

These are firmware defaults, not temperatures or transferable calibration values.

<div class="build-sheet" markdown="1">

### Cooling stages in the reviewed revision

| Time in a 300 s cooling trial | PWM |
| --- | --- |
| 0–10 s | 100 |
| 10–20 s | 90 |
| 20–30 s | 80 |
| 30–300 s | 70 |

The earlier 80→75→65→55 sequence belongs to an older revision. The figures above come from the newer supplied source.

</div>

## Coordinating the target and the display

The current `EXP` command accepts **exactly eleven A–D letters**. After a three-minute preheat, trials 1–10 cool the selected target for five minutes each. Trial 11 displays its specified pattern while **all four targets heat**. It is not an eleventh cooling trial. The programmed duration is 58 minutes including preheat.

For example, `EXP B-C-D-C-B-A-D-C-B-A-B` uses B for the final display state. The master sends `STATE:A`, `STATE:B`, `STATE:C`, or `STATE:D`; the display board applies the corresponding rotation. A radio acknowledgement confirms delivery, not the temperature or visual state of the apparatus. `LED A` is a standalone preview that cancels the experiment and stops the target outputs in this revision.

<p class="source-note">Derived from the current supplied Master_Controller.ino, reviewed against its pin arrays, nodeToIdx mapping, timing constants, and trial functions. <a href="../../downloads/protocol.json">Download the extracted build parameters</a>.</p>
