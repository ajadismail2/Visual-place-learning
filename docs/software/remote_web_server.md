---
title: Remote control development notes
description: Separating an experimental control interface from the research website and from completed software releases.
---
## Earlier interface concept

The original documentation described a Raspberry Pi web server for wireless operation of the apparatus. A complete, tested server implementation was not present in the reviewed repository. This page preserves the design context while removing instructions that implied a ready-to-run service.

## Current control boundary

The research website explains the experiment and provides reference material. Its trial explorer is a **simulation of protocol states** and does not connect to or actuate laboratory hardware.

The supplied LED firmware receives ESP-NOW state commands and supports serial preview. Thermal actuation, trial timing, emergency stop behaviour, and device acknowledgement belong to the actual experimental controller and need a separately tested implementation.

## Requirements for a future remote interface

A future interface should display actual connection status, distinguish requested and observed state, log trial transitions, prevent conflicting concurrent commands, and provide a defined stop state. Camera recording and controller events should share an auditable time relationship. The device address, network configuration, and credentials should be configured outside publicly served website files.

These are implementation requirements, not features claimed to be delivered by this website. See [controllers](../hardware/esp32.md) and [development status](../resources/updates.md).
