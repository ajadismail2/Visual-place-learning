---
title: Files & reproducibility
description: An explicit inventory of source code, design files, example data, and the information needed to reproduce an experiment.
---
## Start with the methods

Read the [system architecture](../complete_system_overview.md), [trial protocol](../methods/protocol.md), and [metric definitions](../methods/analysis.md) before using a code or CAD snapshot. Files are labelled by purpose and validation status; source availability does not establish measured hardware performance or validated biological conclusions.

## Current project downloads

| File | Contents | Status |
| --- | --- | --- |
| [protocol.json](../downloads/protocol.json) | Trial order, timing, target aliases, display offsets, and staged cooling specification | Reference metadata; not executable thermal firmware |
| [preliminary_trial_times.csv](../downloads/preliminary_trial_times.csv) | Eight reported times with original `nr` annotations | Preliminary transcribed summaries, not raw experimental data |
| [run_manifest_template.csv](../downloads/run_manifest_template.csv) | Fields for recording a reproducible acquisition and analysis run | Blank template; values must be filled from the actual experiment |

## Analysis application reference

The separately maintained `fly_target_time_gui_amadeus.py` (version 1.3.0) is documented here but is not distributed by this public website. For an existing project copy, the desktop application requires Python 3.10 or later with Tkinter, NumPy, OpenCV, and Pillow. In an appropriate Python environment:

```text
python -m pip install numpy opencv-python pillow
python fly_target_time_gui_amadeus.py --self-test
python fly_target_time_gui_amadeus.py
```

A command-line CSV check is also available:

```text
python fly_target_time_gui_amadeus.py --check-csv YOUR_TRACKING_FILE.csv
```

Use the exact video geometry associated with the tracking CSV. The application is separate from AMADEUS itself; it does not train the tracking model or repair individual identities. Review all outputs before scientific interpretation.

## Mechanical design inventory

| File | Project role | Validation boundary |
| --- | --- | --- |
| `Hinge_PrintInPlaceV2_VC.stp` | Hinge design reference | Not certified for fit to the current panel assembly |
| `butt_hinge_3.8.scad` | Parametric butt-hinge reference | Source header credits Rohin Gosling, version 3.8 (2021) |
| `Octagon_Holder.step` | Display enclosure fixture | Prototype design snapshot |
| `PVC_IR_STANDE.step` | IR support assembly | Stability development in progress |
| `PVC_PIPE.step` | Pipe geometry | Component snapshot |
| `PVC_Pipe_Holder.step` | Pipe mounting component | Adhesive/load-path fit checks remain necessary |
| `supports.stl` | Arena support print | Validate units, fit, and assembled level before use |

These supplied design files are listed as project references; they are not publicly downloadable from this website. They must not all be attributed as original designs by this project. Retain source-specific attribution and licensing information when reusing them; the website does not assign a blanket new licence to third-party material.

## Existing repository code

The [GitHub repository](https://github.com/ajadismail2/Visual-place-learning) also retains the earlier implementations:

| Path | What is present | How to interpret it |
| --- | --- | --- |
| `analysis/arena_calibrator.py` | Earlier arena calibration tool | Historical analysis workflow; compare conventions with current documentation |
| `analysis/place_learning_analysis.py` | Earlier place-learning analysis script | Does not automatically inherit newer GUI rules |
| `analysis/DOCUMENTATION.md` | Earlier pipeline documentation | Version-specific record; some defaults differ from current experiment |
| `Closed_Loop_Thermal_Camera/` | Thermal calibration, PID, and communication development | Earlier closed-loop design, distinct from staged open-loop operation |
| `Master-Slave-Codes/` | Empty Python placeholders at the audit baseline | Not a complete master/slave release |
| `LED-Display/LED_Pattern_Code.py` | Empty placeholder at the audit baseline | The documented panorama was checked against the separately supplied display sketch |
| `GUI/Generic_camera_version.py` | Empty placeholder at the audit baseline | Not a working acquisition GUI release |

The original source files remain intact. The redesigned documentation replaces outdated descriptions rather than silently modifying the older numerical pipelines.

## Reproducibility package for each run

A complete run package should connect the following records with one run identifier:

1. Animal cohort, handling, and session metadata.
2. Hardware and firmware revisions with thermal/display calibration.
3. Original video and transformations, including crop, frame rate, and frame offset.
4. Tracking software versions, model/configuration, raw outputs, and identity review.
5. Spatial calibration, target regions, trial boundaries, and included IDs.
6. Analysis settings, exact output definitions, per-fly tables, and figures.

The manifest template supplies fields for these records without fabricating missing metadata. Never overwrite a raw video or tracking output merely to prepare a presentation.

## Not yet released as validated datasets

The current resource package does not include complete raw experiment videos, trained SLEAP weights, a fully reviewed identity ground truth, a measured thermal-uniformity dataset, a final itemized bill of materials with prices, or a replicated biological outcome dataset. These are the next additions required for a complete independent replication record.

## Maintaining this website

The site uses MkDocs with a custom local theme. Build and validate it with the repository's `requirements-site.txt` and verification scripts; see the repository README. Content is written in Markdown and assets are served locally. Search, trial exploration, and geometry calculators run in the visitor's browser; the website does not control the physical apparatus.
