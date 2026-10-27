---
title: Downloads and references
description: Controller programs, CAD availability and technical references.
section: Resources
---
## Code downloads

[Download all controller programs](../downloads/arena-firmware-2026-10-17.zip) · [Individual programs](../software/how-the-codes-work.md) · [Download checksums](../downloads/SHA256SUMS)

[Current settings](../downloads/protocol.json) match the supplied programs. The [archived configuration](../downloads/protocol-2026-10-15.json) has a different final trial and display pattern.

Network credentials are excluded. A separate [thermal-ring correction](../software/4-thermal-ring.md) removes a syntax error from the original file.

## Analysis software

[Download the arena analysis GUI](../downloads/analysis/fly_target_time_gui_amadeus.py)

## CAD files

Six editable STEP models are available in [CAD and fabricated parts](../cad/parts-and-step-files.md).

## Original experiment

Ofstad, Zuker and Reiser. Visual place learning in Drosophila melanogaster. [Original paper](https://doi.org/10.1038/nature10131) · [PubMed record](https://pubmed.ncbi.nlm.nih.gov/21654803/).

[Arena dimensions](../hardware/arena-and-dimensions.md) · Temperature settings accompany each controller.

## Technical references

- [TEC 04811-5L31-09CK](https://customthermoelectric.com/media/wysiwyg/TEC_spec_sheets/04811-5L31-09CK_spec_sht.pdf)
- [Ferrotec: module mounting](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref06/)
- [Espressif: ESP32 board connections](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)
- [Espressif: Arduino-ESP32 installation](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Espressif: PWM output interface](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html)
- [HUB75 display library](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA)
