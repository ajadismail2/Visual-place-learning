---
title: Thermal control
description: Target temperatures, staged open-loop drive, and the distinction between a command and a measured thermal landscape.
---
## A warm background and a cool target

The assay uses a thermal contrast: an approximately **36 °C warm background** and a **23–25 °C cool target**. Four controlled target channels are labelled A, B, C, and D. The target selected for a trial is driven through a cooling programme while the remaining thermal landscape provides the warm background.

The current project record uses an **ESP32 with BTS7960 drivers**. Earlier versions used L298N drivers and closed-loop PID control. These are distinct hardware/control revisions and should not be combined into one wiring description.

!!! warning "Setpoints are not temperature measurements"
    A PWM command specifies electrical drive, not floor temperature. Actual temperature depends on supply voltage, heat sinking, contact resistance, ambient conditions, and time since the previous state. Measure the complete thermal cycle on the assembled apparatus.

## Current staged cooling programme

The latest specified target programme uses an 8-bit PWM range, 0–255:

| Phase | Trial interval | Duration | Cooling PWM | Fraction of full-scale command |
| --- | --- | --- | --- | --- |
| 1 | 0–5 s | 5 s | 80 | 31.4% |
| 2 | 5–15 s | 10 s | 75 | 29.4% |
| 3 | 15–25 s | 10 s | 65 | 25.5% |
| 4 | 25–300 s | 275 s | 55 | 21.6% |

The durations sum to **300 s**, exactly one training trial. This replaces the earlier 140 PWM / 20 s followed by 90 PWM / 280 s programme in the project specification. PWM values are specific to the tested configuration and are not portable temperature prescriptions.

Ten-minute `HOT ALL` periods before and after training were requested in the trial plan. They are separate from the 50-minute training block; their execution and timing should be established from the actual controller log.

## Control evolution

| Revision | Function | Current interpretation |
| --- | --- | --- |
| L298N / sensor experiments | Initial reversible heating and cooling experiments | Historical hardware development |
| PyBadge + MLX90640 + ESP32 | Thermal image calibration and PID feedback | Code exists in the repository; not the current open-loop protocol |
| ESP32 + BTS7960 | Four independent target channels | Latest project configuration reported |
| Staged PWM | Timed drive levels without temperature feedback | Current protocol specification; requires measured thermal verification |

PID uses the difference between measured and desired temperature to adjust drive. Open-loop staged PWM instead follows a time-dependent command. The latter is simpler to execute when direct sensing is constrained, but does not automatically correct temperature drift.

## Perimeter heating

A nichrome ring driven through a low-side MOSFET was developed as a thermal boundary. Project tests reported approximately **20 V and 0.9–1.0 A**, with a target near **45 °C** in the measured boundary environment. That value must be associated with the actual sensor location: wire, wall, air, and walking surface temperatures are not interchangeable.

The ring should be characterized independently from the floor and cool target. Record temperature gradients near the edge, as perimeter conditions can change both occupancy and tracking visibility.

## Temperature measurement record

Experiments included TMP117 sensors, an SHT40, and MLX90640 thermal imaging. Communication or frame-acquisition problems were reported, including a second TMP117 address not responding and MLX90640 frame errors. Sensor detection on a bus is not proof of a valid temperature measurement at the fly's location.

For each thermal validation run, retain:

- Sensor type, location, calibration reference, and sampling interval.
- Ambient temperature and humidity, supply voltage, and cooling/heat-sink arrangement.
- Warm-floor spatial uniformity, target temperature, and transition time for every channel.
- Repeatability across the complete trial sequence, including heating history.
- Raw measurements and the exact firmware revision that generated the command sequence.

## Existing source code

The repository's [closed-loop thermal directory](https://github.com/ajadismail2/Visual-place-learning/tree/main/Closed_Loop_Thermal_Camera) contains calibration and PID development scripts. These remain available as historical implementations. A complete, validated release of the latest thermal master firmware and wiring diagram is still needed for independent replication.

See [controller mapping](esp32.md) and [validation](../methods/validation.md).
