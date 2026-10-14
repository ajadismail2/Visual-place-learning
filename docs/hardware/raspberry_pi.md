---
title: Raspberry Pi development notes
description: Historical coordination architecture and its relationship to the current ESP-NOW display interface.
---
## Role in earlier designs

Earlier project documentation proposed a Raspberry Pi as a host for serial communication, remote web control, and experiment coordination. This remains a possible host architecture, but the supplied current LED source uses ESP-NOW commands from a master controller rather than requiring a Raspberry Pi connection.

The current documentation therefore treats Raspberry Pi hosting as an **earlier or optional integration**, not as a validated dependency of every experiment.

## What a host would need to record

A reproducible host implementation should retain the requested target sequence, command timestamps, acknowledged states where supported, video start time, and errors. A remote button labelled “cool” is not sufficient evidence of which channel was driven or what temperature it reached.

The host should preserve a run identifier linking firmware, video, calibration, tracking, and analysis outputs. Hardware-specific commands must follow the actual master firmware interface; the LED slave's commands alone cannot run the full thermal experiment.

## Source availability

The repository's earlier `Master-Slave-Codes/Master.py`, `Master-Slave-Codes/Slave.py`, and `GUI/Generic_camera_version.py` were empty placeholders at the audit baseline. They should not be described as complete working host applications.

See the [current controller interface](esp32.md) and [software resource inventory](../resources/files.md).
