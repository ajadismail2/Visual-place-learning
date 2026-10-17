---
title: Controller programs
description: Programs and libraries for the arena controllers.
section: Code
---
Each controller runs a separate program. The master controls the targets, the LED controller sets the visual pattern, and the background and ring controllers regulate temperature. The thermal-camera program sends measurements to a computer.

## Controller files

| Code | Purpose |
| --- | --- |
| [Master_Controller](master.md) | Four target tiles and experiment timing |
| [Closedloop_60peltier](background.md) | Background temperature control |
| [LED_Slave](display.md) | Eight-panel visual panorama |
| [Thermal_ring](ring.md) | Ring heater and temperature feedback |
| [thermal_camera](camera.md) | Thermal-image stream |
| [SinglePanelTest](panel-test.md) | Display PCB and panel test |
| [4_peltier_mosfet_hbridge](four-peltier.md) | Alternative target bench controller |
| [hot_slave](hot-slave.md) | Alternative UART heating controller |

## Program setup

1. Open the program in its own sketch folder and select the board connected to the computer.
2. Install the libraries used by that program. WiFi, ESP-NOW and Wire are provided by the relevant board package.
3. For the master, copy `local_config.example.h` to `local_config.h`, enter the network and display settings, then remove the example's `#error` line.
4. Compile and upload to the corresponding controller. Use the command and pin tables on its code page.

| Program | Additional libraries |
| --- | --- |
| Background | PID_v1 |
| LED display and panel test | ESP32-HUB75-MatrixPanel-I2S-DMA |
| Thermal ring | OneWire, DallasTemperature |
| Thermal camera | Adafruit_MLX90640 |

The background and ring programs still require conversion to the [proposed ESP32 pins](../build/pcb.md#background-ring-and-camera) and PWM APIs. The master's ESP32 APIs must match the installed board package.

[**Download all code**](../downloads/arena-firmware-2026-10-17.zip) · [Settings](../downloads/protocol.json)

Alternative controllers have different pin assignments. Use the separately labelled syntax-corrected ring file when compiling; the original is retained for reference.

[Operating procedure](../operation.md) · [ESP32 wiring](../build/pcb.md)
