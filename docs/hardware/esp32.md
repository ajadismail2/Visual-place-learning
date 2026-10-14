---
title: Controllers & synchronization
description: The current display interface, target mapping, and the evidence needed to align the thermal and visual experiment.
---
## Two coordinated responsibilities

Thermal actuation and LED refresh have different timing and electrical requirements. The latest display source receives commands from a separate master controller over **ESP-NOW**, while the ESP32 display board refreshes the HUB75 chain. All experimental timing is delegated to the master in this source snapshot.

Earlier documentation described Raspberry Pi coordination and alternative master/slave assignments. The table below records the actual interface in the supplied October 2026 `LED_Slave.ino`.

## Display states

| Target/state | Incoming wireless command | Virtual horizontal offset | Fraction of the panorama |
| --- | --- | --- | --- |
| A | `STATE:A` | 192 px | 3/4 |
| B | `STATE:B` | 0 px | 0 |
| C | `STATE:C` | 64 px | 1/4 |
| D | `STATE:D` | 128 px | 1/2 |
| Blank | `OFF` | Not applicable | All pixels cleared |

These offsets describe virtual coordinates. Physical clockwise/anticlockwise direction depends on panel mounting and chain reversal. Verify it on the assembled octagon rather than inferring it from the sign of an offset.

## Current HUB75 pin assignment

| Signal | GPIO | Signal | GPIO |
| --- | --- | --- | --- |
| R1 | 2 | R2 | 16 |
| G1 | 15 | G2 | 27 |
| B1 | 4 | B2 | 17 |
| A | 5 | B | 18 |
| C | 19 | D | 21 |
| E | 12 | CLK | 22 |
| LAT | 25 | OE | 26 |

**This is the pin map in the supplied October display firmware.** It supersedes the earlier single-panel test map for documentation of this source file. It does not establish compatibility with every ESP32 board or panel driver.

## Source configuration

| Setting | Value in supplied source |
| --- | --- |
| ESP-NOW channel | 1 |
| Serial baud rate | 115200 |
| Native panel chain | 8 panels, 64 × 32 each |
| Virtual coordinates | 256 × 64 |
| Chain reversal | Enabled (`REVERSE_CHAIN = 1`) |
| Rotation flag | `ROTATE_CW = 0` |
| Driver selection | `FM6126A` |
| Brightness command | 120 / 255 |
| Requested minimum refresh | 250 Hz |

The configured refresh value is a library request, not a photodiode measurement. Record actual refresh and stimulus timing when validating the display.

## Standalone test

With the display firmware loaded, send **A**, **B**, **C**, **D**, or **OFF** through a serial monitor at 115200 baud. Confirm each panorama state physically and check that panel boundaries join as expected. The wireless interface accepts `STATE:A` through `STATE:D`, whereas standalone serial testing accepts the single-letter commands.

Both boards must use the same ESP-NOW channel. The slave prints its MAC address on startup for configuration in the master; no installation-specific MAC address is embedded in the published snapshot.

## Thermal channel aliases

The latest requested manual mapping is:

| Manual alias | Target label |
| --- | --- |
| T1 | A |
| T2 | D |
| T3 | C |
| T4 | B |

Accepting both letter labels and T1–T4 was requested for the thermal master. The supplied LED slave does not implement this alias mapping. Validate the physical target, driver channel, master command, and display state together before recording data.

## Synchronization record

Log intended transition time, command delivery or acknowledgement where available, observed display transition, and measured thermal response. ESP-NOW reception does not make thermal equilibration instantaneous. Assign trial boundaries using a documented timing convention and preserve the relation between controller time and video frames.

The separately supplied `LED_Slave.ino` was reviewed as an input to this documentation. It is not distributed by this public website; hardware compilation and operation were not tested during the website update.
