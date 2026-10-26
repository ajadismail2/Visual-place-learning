---
title: Install and upload the programs
description: Put the correct program on each controller and check its response before connecting loads.
section: Software
---
Upload each program to its labelled controller using Arduino IDE.

## 1. Prepare the computer

Install Arduino IDE. Connect one board with a data-capable USB cable and select its model and port.

For ESP32 boards, install the [Espressif board package](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html). For Arduino boards, select the matching model and package. Record working package and library versions.


## 2. Open one sketch at a time

Extract the [controller bundle](../downloads/arena-firmware-2026-10-17.zip). Place each `.ino` in a matching sketch folder and open the program for the connected board.

| Board | Upload this program | Extra libraries |
| --- | --- | --- |
| Peltier-plate ESP32 | Experiment_Controller | Uses ESP32 board-package networking and PWM support |
| Display ESP32 | Display_Controller | ESP32-HUB75-MatrixPanel-I2S-DMA |
| Background Arduino | Closedloop_60peltier | PID_v1 |
| Ring Arduino | Thermal_ring_syntax_fixed | OneWire and DallasTemperature |
| Thermal-camera ESP32 | thermal_camera | Adafruit_MLX90640 and its dependencies |

Install the listed libraries using Library Manager or their documented installers. `Wire`, WiFi and ESP-NOW come with the relevant board package. See the [display library documentation](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA).

The Peltier-plate controller requires the pin-based `ledcAttach`/`ledcWrite` API. Confirm compilation with the selected ESP32 package; these sketches are not a validated compiled release. Background and ring pin assignments require adaptation for ESP32 hardware.

## 3. Pair the Peltier-plate controller and display

Pair the Peltier-plate controller with the display ESP32's MAC address.

1. Upload `Display_Controller` first.
2. Read its startup MAC address in Serial Monitor at **115200 baud**; reset if needed.
3. Copy `local_config.example.h` to `local_config.h` in the Peltier-controller folder.
4. Enter the display address and network settings, then remove the `#error` line. Keep this file local.
5. Upload the Peltier-plate program and retain the radio configuration expected by both sketches.
6. Send `A` directly to the display. With Peltier-plate load power disconnected, test a short sequence and verify the wireless display change after preheat. End with `STOP`.

ESP-NOW transmits A–D states between boards. Verify the destination address, panel orientation and physical Peltier-plate mapping.

## 4. Compile, upload and read a response

Select **Verify** and resolve compiler errors, then **Upload**. Confirm completion in the IDE.

Open Serial Monitor at the program's baud rate and send commands with a line ending.

Peltier-plate, display, background and ring controllers use **115200 baud**. The thermal camera uses **921600 baud** and binary packets, which are not readable as temperature text in Serial Monitor.


## 5. Test before connecting all loads

Test one panel or driver channel at a time. Confirm Peltier-plate mapping and temperature response. Restore experiment firmware after diagnostics, then follow the [operating procedure](operation.md).

[Arduino upload guide](https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE) · [Troubleshooting](checks.md)
