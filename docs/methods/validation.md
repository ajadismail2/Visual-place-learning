---
title: Validation & troubleshooting
description: An evidence-led checklist for the apparatus, recording, tracking, and behavioural interpretation.
---
## Current validation priorities

The apparatus and analysis have developed through several iterations. The priority is a traceable chain from physical stimulus to measured behaviour: controller command, observed state, video frame, individual trajectory, analysis event, and reported outcome.

| Area | Evidence needed | Why it matters |
| --- | --- | --- |
| Thermal field | Spatial and temporal measurements across all target states | Drive level alone does not establish temperature |
| Visual cues | Physical mapping, angles, brightness, transition timing | Nominal pixels may not reproduce the intended stimulus |
| Mechanics | Level arena and stable camera/lighting through a session | Tilt and drift can introduce behavioural or measurement changes |
| Recording | Verified frame rate, frame count, and geometry | Incorrect timing or scale propagates into every metric |
| Identity | Reviewed interactions and quantified errors | Swaps can distort individual learning curves |
| Analysis | Documented parameters, coverage, exclusions, and event definitions | Results depend on the operational definition |
| Biology | Replicate sessions, controls, and cohort metadata | Engineering functionality is not itself a learning result |

## Tracking symptoms

| Symptom | First checks | Interpretation boundary |
| --- | --- | --- |
| Flies disappear at the edge | Contrast, crop boundary, examples in training data, model confidence | Missing detection is not proof the animal left the arena |
| IDs exchange during contact | Video before/after crossing, association history, appearance evidence | More pose annotations alone may not solve identity |
| Head and abdomen swap | Orientation annotations and body resolution | Direction error may occur without an identity error |
| Same apparent colour on two animals | Actual stored IDs and overlay colour mapping | Colour alone is not a definitive identity diagnostic |
| Large path-length spikes | Per-frame displacements and identity continuity | A jump may be tracking error rather than locomotion |
| No detection for a frame | Source video, thresholds, preprocessing, frame integrity | Avoid assuming stable illumination guarantees detection |

## Resource and execution failures

### SLEAP GPU memory

Large inference batches and crops caused GPU out-of-memory errors during development. Start from a configuration that fits the machine and benchmark a representative short segment. Keep prediction quality and identity review separate from throughput. A successful short segment does not certify memory use or identity continuity throughout a long interaction-rich recording.

### AMADEUS refinement memory

The October run encountered Windows virtual-memory exhaustion at direction-segment correction after embedding processing. Reducing worker count and checking memory availability were proposed recovery measures. Completed intermediate stages should be preserved when resuming; only skip a stage when its outputs have actually completed and match the run configuration.

### Long Windows paths

An earlier AMADEUS stage failed while writing `assign_type_history.pkl` under a deeply nested output path. A short project/output root can reduce this failure mode, but a changed root must retain the relationship to existing outputs and configuration. Do not label the run complete until final outputs and logs confirm completion.

## Before interpreting a learning curve

Check that trial start and duration match the video, each target letter matches its physical region, scale units are correct, and non-reached flies remain in the outcome record. Inspect trials with unexpected improvements or regressions instead of treating every change as learning.

For the current 916 px / 20 cm example, **45.8 px/cm** is the correct scale. Entering 0.218 as cm/px would inflate distances and speeds tenfold.

## Acceptance record to retain

For a release intended for other laboratories, publish a fixed hardware/firmware revision, assembly dimensions, measured thermal and visual performance, a representative raw recording, calibration, a reviewed tracking subset, the analysis configuration, and expected outputs. Record known limitations and the operating conditions under which the checks were performed.

The website removes earlier unsupported claims of guaranteed stimulus equivalence, complete identity preservation, and ready-to-run host software. Its [development record](../resources/updates.md) states what is present and what remains unresolved.
