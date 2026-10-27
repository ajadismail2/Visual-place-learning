---
title: Cameras
description: Cameras for behaviour recording and surface-temperature measurements.
section: Hardware
---
## Behaviour camera

A Thorlabs CS165MU monochrome camera records the flies under infrared illumination. Mount it vertically above the arena, with the full walking surface in focus. A lower-cost IR-sensitive camera can also work if individual flies remain distinguishable across the image.

## Thermal camera

The MLX90640 measures surface temperature on a 32 × 24 pixel grid. An ESP32 reads it over I²C and sends frames to the computer over USB.

Use it to follow the background and Peltier-plate temperatures throughout the experiment. Check readings against a contact thermometer.

[Thermal-camera program](../software/5-thermal-camera-stream.md)
