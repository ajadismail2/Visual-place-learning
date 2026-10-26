---
title: Four-target control
description: Wiring and timing for the four cooling targets.
section: Hardware
---
One ESP32 drives four Peltiers independently: one cools while three heat. Background control is separate.

## Drivers

Connect each Peltier across its driver's output pair. ESP32 signals drive RPWM, LPWM, R_EN and L_EN; an external supply powers the Peltier.

## Target controller pin map

| Target | Manual number | Driver channel | RPWM | LPWM | R_EN | L_EN |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1 | 3 | 27 | 14 | 23 | 22 |
| B | 2 | 2 | 25 | 26 | 13 | 15 |
| C | 3 | 4 | 19 | 18 | 2 | 16 |
| D | 4 | 1 | 32 | 33 | 4 | 5 |

GPIO assignments above use **LPWM for heating and RPWM for cooling**, with 20 kHz, 8-bit PWM. Verify installed polarity.

![Four separate driver channels connected to the target ESP32](../assets/target-wiring.svg)

## Wire and identify one channel first

Wire with power disconnected using the [connection guide](wiring.md#power-and-target-connections). Label both ends of each cable.

Test each channel while measuring temperature. Manual target 1 selects A on driver channel 3.

Use identical A–D labels in the controller, video and analysis. Stop and check polarity if heating and cooling are reversed.

<figure class="photo-slot" data-photo-id="target-four"><div class="photo-space" aria-label="Blank photograph of all four target channels"></div><figcaption><span>Photo · H09</span><strong>The four target channels</strong></figcaption></figure>

## Trial sequence

The experiment controller preheats all targets for five minutes. Each selected target then cools for 300 seconds.

| Stage | Output |
| --- | --- |
| Initial cooling | PWM 150 for 23 s |
| Remaining 277 s | PWM 106 on first selection; 120 on a repeat |
| Preheat | Heating at PWM 30 for 300 s |
| Other targets, not yet cooled | Heating at PWM 29 |
| Other targets, previously cooled | Heating at PWM 24 |
| Return to heating | PWM 50 for 17 s, then 24 |

![Programmed cooling and return-to-heating outputs over one target interval](../assets/setup/target-pwm.svg)

Programmed PWM, not measured temperature. Repeat selections use the higher hold output.

The intended target range is **23–25 °C**; verify it from recorded surface temperatures.

Every step in this program cools a target.

## Thermal coupling

Heat rejected by a cooling target can warm the shared carrier and neighbouring tiles.

Compare cooling, hold and recovery for A–D with simultaneous background measurements. A measured comparison is not yet available.

[Four-Peltier controller](../firmware/target-controller.md) · [Operating procedure](../operation.md) · [Wiring](wiring.md)
