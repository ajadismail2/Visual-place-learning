---
title: PCB and connections
description: Moving the controller from loose wiring to a board meant matching real ESP32 hardware, separating power paths, and testing each connection.
section: 03 / Electronics build
---
## Make the footprint fit the board

KiCad was used for the schematic and footprint work. The project involved both **30-pin and 38-pin ESP32 boards**, so a generic name was not enough to select the correct footprint. Custom symbols and footprints were made around the actual boards and their enclosure dimensions.

These files solve different problems. The symbol identifies electrical connections; the footprint determines the physical header positions; a 3D model helps check enclosure clearance. A convincing 3D view does not correct a misplaced pad or a wrong pin assignment.

The makerspace work also included soldering and wire-and-jumper assembly. By October, the display ESP32 was reported mounted on a PCB and supplied independently of the computer. The available record does not specify whether that PCB was milled, etched, or ordered, so no manufacturing process is claimed here.

## Keep control signals and load current distinct

The ESP32 tells the drivers what to do. The external power circuit supplies the Peltier current. Each target has its own bidirectional driver path; its two leads connect to that driver's two switched outputs. They are not four loads wired in series, and a Peltier lead should not be treated as a permanently grounded return when an H-bridge reverses its polarity.

| Connection | Role in the assembly |
| --- | --- |
| ESP32 → driver logic | Separate PWM and enable signals for each target |
| Supply → driver power inputs | Carries the target's load current |
| Driver outputs → Peltier pair | Reverses current through that target |
| Logic ground → driver reference ground | Gives the control signals a common electrical reference |
| Display supply → LED panels and controller supply arrangement | Must support standalone operation as well as USB testing |

The regulated input and logic levels must match the actual boards. The current [pin map](four-channels.md#pin-map-from-the-current-master) describes the master firmware, not a substitute for the assembled PCB schematic.

## Why the driver changed

The earlier control work used L298N bridges. Their transistor voltage drop consumes part of the supply voltage and dissipates power in the driver. Later versions used BTS7960-based modules for the four target channels. This made the driver choice part of the thermal budget as well as the wiring design. The [L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf) and [BTS7960 datasheet](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf) describe the different power stages; a module's headline current rating is not an assembled-board rating.

<div class="build-sheet" markdown="1">

### Debugging the assembled display board

The display worked when a command was entered directly on the slave. Master-side commands initially produced flashing or disappearing patterns. The revised firmware holds the requested state, queues received commands, and prevents an older `OFF` request from following a newer state.

Later logs showed a radio acknowledgement and a slave message confirming the displayed state. That narrowed the investigation: command delivery was observed, while operation from the PCB's standalone supply still needed checking. The USB-connected test and the independently powered test were different conditions.

</div>

<p class="source-note">KiCad and board-model work: January 2026. PCB-mounted slave and command-path tests: October 2026. The source board files and fabrication settings are not part of this public documentation; no trace width or power rating is inferred from a photograph or firmware file.</p>
