---
title: Install and upload the programs
description: Put the correct program on each controller and check its response before connecting loads.
section: Software
---
The **Arduino IDE** is the computer application used to compile and transfer a program to a board. A **sketch** is the program, usually stored in an `.ino` file. **Uploading** copies the compiled program into the board's memory; after upload, the board runs it whenever it is powered.

## 1. Prepare the computer

Install Arduino IDE and connect one controller using a USB cable that supports data. Some cables only provide power. Select the board model and its port in the IDE. The port identifies the connected device; it is not the experiment's target number.

For ESP32 boards, install Espressif's ESP32 board package through Boards Manager. Its [installation guide](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html) lists the package URL and setup steps. For Arduino boards, select the actual model and the appropriate board package. Record the working package and library versions with the build rather than changing them immediately before an experiment.

<figure class="photo-slot" data-photo-id="ide-board-port"><div class="photo-space" aria-label="Blank screenshot of Arduino IDE board and port selection"></div><figcaption><span>Screenshot · S01</span><strong>Board and port selection</strong></figcaption></figure>

## 2. Open one sketch at a time

Download and extract the [controller bundle](../downloads/arena-firmware-2026-10-17.zip). Each `.ino` belongs in its own matching sketch folder. Open the program for the board you have physically connected. Keep the board labelled while programming it.

| Board | Upload this program | Extra libraries |
| --- | --- | --- |
| Target ESP32 | Master_Controller | Uses ESP32 board-package networking and PWM support |
| Display ESP32 | LED_Slave | ESP32-HUB75-MatrixPanel-I2S-DMA |
| Background Arduino | Closedloop_60peltier | PID_v1 |
| Ring Arduino | Thermal_ring_syntax_fixed | OneWire and DallasTemperature |
| Thermal-camera ESP32 | thermal_camera | Adafruit_MLX90640 and its dependencies |

Install the required libraries through Library Manager or the library's documented method. `Wire` supplies the sensor-bus interface; WiFi and ESP-NOW support come from the ESP32 board package. Do not install unrelated libraries to resolve a missing-header error. Use the name in the sketch and the [display library's documentation](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA).

The master uses the pin-based `ledcAttach` and `ledcWrite` interface. Select a compatible ESP32 package and confirm compilation; the supplied set of sketches has not been compiled as a validated release in this documentation. The background and ring programs retain Arduino pin assignments and must be adapted before moving them to ESP32 hardware.

## 3. Pair the master and display

The display receives short wireless messages from the master. Its **MAC address** identifies the destination device. It is different from a Wi-Fi password or a serial port.

1. Upload `LED_Slave` to the display ESP32 first.
2. Open its Serial Monitor at **115200 baud** and read the address printed at startup. Reset the board if you need to see the startup message again.
3. In the master sketch folder, copy `local_config.example.h` to `local_config.h`.
4. Enter that display address and the local network settings required by the example. Remove its `#error` line after filling in the values. Keep this file local.
5. Upload the master program to the target ESP32. Keep the boards on the radio configuration expected by the supplied sketches.
6. Send `A` directly to the display board and verify the visible pattern. Then, with target load power disconnected, run a short master sequence to check the wireless state change after preheat. End the check with `STOP` on the master.

ESP-NOW sends the target state directly between boards. A successful upload does not confirm that the destination address, panel orientation or physical target mapping is correct; those are separate checks.

## 4. Compile, upload and read a response

The **Verify** button compiles the sketch. Fix any compiler error before uploading. The **Upload** button sends it to the selected board. Watch the IDE's completion message rather than assuming the board's power light means upload succeeded.

Open Serial Monitor after upload. Set its baud rate to the value on the relevant program page. A baud rate is the serial communication speed; a mismatch can make messages unreadable. Send commands with a line ending so the controller receives a complete command.

The master, display, background and ring use **115200 baud**. The thermal camera uses **921600 baud** and sends binary packets. Its output will not appear as ordinary temperature text in Serial Monitor.

<figure class="photo-slot" data-photo-id="serial-commands"><div class="photo-space" aria-label="Blank screenshot of the serial monitor"></div><figcaption><span>Screenshot · S02</span><strong>A successful command and response</strong></figcaption></figure>

## 5. Test before connecting all loads

Start with one panel or one driver channel. Confirm which tile and display state respond, then restore the intended experiment firmware if a diagnostic program was used. Keep temperature measurement running while testing a Peltier output. Follow the [operating procedure](../operation.md) only after the individual checks pass.

[Arduino upload guide](https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE) · [Troubleshooting](checks.md)
