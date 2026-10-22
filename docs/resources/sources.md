---
title: Downloads and references
description: Controller programs, CAD availability and technical references.
section: Software
---
## Code downloads

[Download all controller programs](../downloads/arena-firmware-2026-10-17.zip) · [Individual programs](../firmware/index.md) · [Download checksums](../downloads/SHA256SUMS)

The [current settings](../downloads/protocol.json) match the included programs. The [archived configuration](../downloads/protocol-2026-10-15.json) uses a different final-trial protocol and display pattern.

Network credentials are excluded. A separate [thermal-ring correction](../firmware/ring.md) removes a syntax error from the original file.

## Website QR code

[QR code PNG](../downloads/website-dynamic-qr.png) · [Print-ready SVG](../downloads/website-dynamic-qr.svg)

The code opens the [website redirect](../go/index.html). Its destination can be updated without replacing a printed QR code.

## Analysis software

[AMADEUS tracking and analysis workflow](../analysis/index.md) · [Download the arena analysis GUI](../downloads/analysis/fly_target_time_gui_amadeus.py)

## CAD files

Six editable STEP models are available in [CAD and fabricated parts](../cad/index.md).

## Original experiment

Ofstad, Zuker and Reiser. **Visual place learning in Drosophila melanogaster.** [Original paper](https://doi.org/10.1038/nature10131) · [PubMed record](https://pubmed.ncbi.nlm.nih.gov/21654803/).

The [arena chapter](../build/arena.md) contains the dimensions and configuration used in this build. Temperature settings are documented beside the relevant controller.

## Technical references

- [Ferrotec: Peltier principles](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref02/)
- [Ferrotec: heat sinks](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref05/)
- [Ferrotec: module mounting](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref06/)
- [Espressif: ESP32 board connections](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)
- [Espressif: Arduino-ESP32 installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Espressif: PWM output interface](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html)
- [HUB75 display library](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA)
