---
title: Sources and revision record
description: The papers, component documentation, and project records behind these build notes.
section: Project record
---
## Original experiment

Ofstad, T. A., Zuker, C. S. & Reiser, M. B. (2011). **Visual place learning in Drosophila melanogaster.** Nature 474, 204–207. [doi:10.1038/nature10131](https://doi.org/10.1038/nature10131).

This site documents a replication build. The original paper supplies the assay background; local construction choices and controller revisions are identified as this project's work.

## Technical sources

- [Ferrotec: basic thermoelectric principles](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref02/) — module construction and heat transport.
- [Ferrotec: module energy balance](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref11/) — pumped heat, electrical input, and rejected heat.
- [Ferrotec: heat-sink considerations](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref05/) — the receiving side of the thermal system.
- [ST: L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf) and [Infineon: BTS7960 datasheet](https://www.infineon.com/assets/row/public/documents/10/57/infineon-bts7960-ds-en.pdf) — the driver architectures considered during development.

## How the record developed

| Period | Build work and finding |
| --- | --- |
| Late 2025–January 2026 | Panel arrangement, Onshape models, wooden base, printed fixtures, KiCad symbols and footprints, early controller integration |
| February–March 2026 | Background heating tests, overheating under the covered arena, sensor-placement constraints, and different top/bottom responses during cooling |
| Mid-2026 | Driver and wiring revisions; independent target control and manual temperature tests |
| September–October 2026 | Support and hinge revisions, illumination-mount stability, physical display geometry, and paper patterns |
| 15–16 October 2026 | Updated master/slave source, individual heating values, an all-heating final trial, and command/power-path debugging |

## Source versions used here

The controller details were checked against the supplied **Master_Controller.ino** revised on 15 October and the current **LED_Slave(3).ino**. These supersede the earlier cooling values and diagonal renderer documented in the first website draft. [protocol.json](../downloads/protocol.json) records the extracted parameters without distributing the private source files or board identifiers.

Project conversations supply the construction history and reported bench observations. Suggestions from troubleshooting are not treated as completed modifications. The records establish KiCad work and a PCB-mounted controller, but not the board's manufacturing process, copper specification, or final bill of materials.

The original repository's hardware and analysis source directories remain available in [GitHub](https://github.com/ajadismail2/Visual-place-learning). Their older settings should be read in the context of their revision.
