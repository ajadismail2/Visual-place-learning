---
title: Peltier temperature system
description: Temperature control for the 60-Peltier background and four cooling Peltier plates.
section: Hardware
---
The arena uses 60 Peltier modules for the background and four independently driven Peltier plates at positions A–D. The background uses temperature feedback. The four Peltier plates follow timed PWM commands.

## Background of 60 Peltier modules

The 60 Peltier modules form one series circuit with a single power-control output. An Arduino reads a TMP117 sensor over I²C and drives the external power stage from pin 9.

Peltier current direction determines heat-flow direction. The achieved surface temperature depends on current, thermal contact and heat dissipation. Verify polarity and temperature on the assembled arena.

<figure class="photo-slot" data-photo-id="background-sensor"><div class="photo-space" aria-label="Blank photograph of the 60 Peltier modules and temperature sensor"></div><figcaption><span>Photo · H08</span><strong>Background circuit and sensor position</strong></figcaption></figure>

### Set the background temperature

Open the background Arduino in Serial Monitor at **115200 baud** with a newline ending. Set the required sensor temperature with:

```text
SET 34.8
```

The controller replies with the accepted temperature. Send `STATUS` to check the sensor reading, setpoint and PWM output. The command is not stored after a restart; the firmware then returns to its **34.8 °C** default.

This command changes the temperature used by the feedback loop. The TMP117 records only its own location, so confirm the arena surface temperature independently.

Defaults: **34.8 °C**, **150/255 maximum PWM**, **100 ms sensor interval**, and PID gains **60 / 4 / 5**.

## Four cooling Peltier plates

One ESP32 drives four BTS7960 bridges. LPWM heats each Peltier plate and RPWM cools it. The opposite output is zeroed before reversal.

### Peltier-plate controller pin map {#target-controller-pin-map}

| Peltier plate | Manual number | Driver channel | RPWM | LPWM | R_EN | L_EN |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1 | 3 | 27 | 14 | 23 | 22 |
| B | 2 | 2 | 25 | 26 | 13 | 15 |
| C | 3 | 4 | 19 | 18 | 2 | 16 |
| D | 4 | 1 | 32 | 33 | 4 | 5 |

The outputs use **20 kHz, 8-bit PWM**. Connect each Peltier plate across its driver output and verify the installed polarity under temperature monitoring.

![Four separate driver channels connected to the Peltier-plate ESP32](../assets/target-wiring.svg)

Wire with power disconnected using the [connection guide](wiring.md#power-and-peltier-plate-connections). Label both ends of each cable A–D and retain these labels in the video and analysis.

<figure class="photo-slot" data-photo-id="target-four"><div class="photo-space" aria-label="Blank photograph of the four cooling Peltier plates"></div><figcaption><span>Photo · H09</span><strong>Four cooling Peltier plates</strong></figcaption></figure>

### Trial sequence {#trial-sequence}

The Peltier-plate controller heats all four Peltier plates for five minutes before the first trial. During each 300-second trial, one Peltier plate cools while the other three heat.

| Stage | Output |
| --- | --- |
| Initial cooling | PWM 150 for 23 s |
| Remaining 277 s | PWM 106 on first selection; 120 on a repeat |
| Preheat | Heating at PWM 30 for 300 s |
| Peltier plates not yet cooled | Heating at PWM 29 |
| Peltier plates previously cooled | Heating at PWM 24 |
| Return to heating | PWM 50 for 17 s, then 24 |

![Programmed cooling and return-to-heating outputs over one trial](../assets/setup/target-pwm.svg)

These are programmed outputs rather than measured temperatures. The selected Peltier plate should reach **23–25 °C**; confirm this from recorded surface temperatures.

## Temperature change across 10–11 trials

The four Peltier plates add heat to the arena while the 60-Peltier background is operating. Measure this cumulative temperature rise over the complete run.

1. Stabilise the empty arena and record room temperature, TMP117 temperature, background surface temperature and Peltier-plate temperatures.
2. Record a reference run with the 60-Peltier background operating for the same duration, without the four-Peltier-plate sequence.
3. Run the complete five-minute preheat followed by 10 or 11 trials. Keep airflow, glass-cover position and starting temperature unchanged.
4. For each trial, calculate the mean background temperature and the temperatures of Peltier plates A–D. Also retain the minimum temperature of the cooling Peltier plate and the final background temperature.
5. Calculate the additional heating at each time point:

<div class="equation">additional heating = full-run temperature − reference-run temperature</div>

A 10-trial run lasts **55 minutes** including preheat; an 11-trial run lasts **60 minutes**. Report both the TMP117 reading and spatial surface measurements because one sensor cannot describe the entire arena.

<figure class="photo-slot" data-photo-id="peltier-temperature-series"><div class="photo-space" aria-label="Reserved space for a plot of background and Peltier-plate temperatures over 10 or 11 trials"></div><figcaption><span>Plot · to be added</span><strong>Background and Peltier-plate temperatures across the complete experiment</strong></figcaption></figure>

<figure class="photo-slot" data-photo-id="peltier-temperature-rise"><div class="photo-space" aria-label="Reserved space for a plot of additional heating relative to the reference run"></div><figcaption><span>Plot · to be added</span><strong>Additional heating relative to the background-only reference</strong></figcaption></figure>

If the background temperature rises consistently, adjust the `SET` temperature in a later validation run and measure the result again. Report the commanded temperature, sensor location and measured surface temperatures together.

[Background controller](../firmware/background.md) · [Four-Peltier controller](../firmware/target-controller.md) · [Operating procedure](../operation.md) · [Thermal imaging](imaging.md#set-up-the-thermal-camera)
