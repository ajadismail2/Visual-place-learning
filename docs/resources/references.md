---
title: Scientific & technical references
description: Primary sources and project records, kept distinct so that apparatus claims and published findings can be traced.
---
## Foundational place-learning study

**Ofstad, T. A., Zuker, C. S. & Reiser, M. B. (2011).** *Visual place learning in Drosophila melanogaster*. Nature 474, 204–207. [doi:10.1038/nature10131](https://doi.org/10.1038/nature10131).

Source for the thermal–visual assay logic, coupled and uncoupled conditions, probe tests, and the published neural-circuit findings. The current project adapts this paradigm; its engineering and preliminary data should not be treated as reproducing every original experimental result.

## Sociability reference

**Lobato-Rios, V., Lam, T. K. C. & Ramdya, P. (2024).** *Conspecific sociability is regulated by associative learning circuits*. bioRxiv, version posted 25 November 2024. [doi:10.1101/2024.11.25.624845](https://doi.org/10.1101/2024.11.25.624845) · [Selected version](https://www.biorxiv.org/content/10.1101/2024.11.25.624845v1).

This is the version selected for the sociability project. It is identified as a preprint version here even if subsequent versions or journal publications exist. Any later methodological changes should be reviewed explicitly before updating the assay specification.

## Tracking software

**SLEAP.** [Official website](https://sleap.ai/) · [Documentation](https://docs.sleap.ai/) · [Neural-network package](https://nn.sleap.ai/) · [Source](https://github.com/talmolab/sleap).

SLEAP provides multi-animal pose estimation and tracking workflows. The project uses a top-down centroid/centred-instance pair. Refer to the installed version's help and documentation for command syntax, rather than assuming commands from a different release remain identical.

**AMADEUS.** [Official project](https://amadeus.jpmyrmecol.com/) · [Source](https://github.com/jpmyrmecol/AMADEUS) · [2026 preprint](https://doi.org/10.64898/2026.09.19.752854).

The official project describes annotation-free training from isolated-animal examples and synthetic interactions, oriented-box detection, direction estimation, and identity tracking. Its capabilities are distinct from the observed success or failure of a particular local run. The custom target-analysis GUI described here is a separate project tool.

## Display and website implementation

**ESP32 HUB75 DMA library.** [ESP32-HUB75-MatrixPanel-DMA](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA). The supplied LED sketch includes `ESP32-HUB75-MatrixPanel-I2S-DMA.h` and selects configuration values documented in the [controller page](../hardware/esp32.md).

**MkDocs.** [Official documentation](https://www.mkdocs.org/). The website retains the repository's Markdown-based documentation workflow with a custom local theme and a GitHub Pages build workflow.

## Project-source record

| Source record | Used for |
| --- | --- |
| Repository baseline `66070df6887bdfe19dbc417cf7f097b902363425` | Existing code, early documentation, and original apparatus imagery |
| `LED_Slave.ino`, supplied October 2026 | Pixel extents, panel mapping, pin map, and display-state commands |
| `fly_target_time_gui_amadeus.py`, v1.3.0, reviewed October 2026 | Current analysis definitions and interface capabilities |
| `fly_target_time_gui_v6_clean.py`, reviewed October 2026 | Earlier SLEAP GUI conventions and trial sequence |
| Project notes, September–October 2026 | Apparatus revisions, thermal programme, calibration measurements, and troubleshooting history |
| Trial values supplied 7 October 2026 | Preliminary eight-trial descriptive record |
| Supplied CAD snapshots | Prototype mechanical resources with attribution preserved where present |

Published references support the assay background. Supplied source files support statements about implemented code. Project notes support descriptions of local development, with measured performance and validation status stated separately.

## Attribution and reuse

The repository's original CAD image is retained with its project context. The new arena illustration is a conceptual diagram, and the preliminary chart is generated from the transcribed values. The parametric butt-hinge source credits **Rohin Gosling**; that attribution remains in the file. No new blanket software or CAD licence is asserted by this documentation update.
