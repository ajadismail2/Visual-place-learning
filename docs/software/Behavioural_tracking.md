---
title: Tracking flies without losing identity
description: Detection, pose estimation, temporal association, and the limits imposed by visually similar animals.
---
## Three different questions

**Detection** asks where an animal is in one frame. **Pose estimation** locates body landmarks or an oriented representation. **Identity tracking** links observations of the same animal across frames. Good detection does not guarantee stable identity, especially when visually similar flies touch and cross.

The main project challenge has been identity continuity during close interactions, alongside missed detections near the arena boundary and occasional head–abdomen flips. These errors affect behavioural interpretation differently and should be reviewed separately.

## SLEAP workflow

The project uses a top-down combination of a **centroid model** and a **centred-instance model**. The first proposes animal locations; the second estimates body landmarks within animal-centred crops. Tracking then associates instances across time.

### Model record

| Date / training set label | Centroid model | Centred-instance model |
| --- | --- | --- |
| 8 September; n=52 | `260908_193132.centroid.n=52` | `260908_202849.centered_instance.n=52` |
| 18 September; n=276 | `260918_062546.centroid.n=276` | `260918_101030.centered_instance.n=276` |
| 3–4 October; n=72 | `261003_230320.centroid.n=72` | `261004_004353.centered_instance.n=72` |
| 5 October; n=88 | `261005_221922.centroid.n=88` | `261005_231413.centered_instance.n=88` |

The labels identify model directories from the development record. They are not independent performance scores, and the larger historical label count is not proof of a better model under new recording conditions. The latest pair used for the full-video request is the **n=88 pair**. Weights are not included in this repository.

### Temporal association settings

The later selected SLEAP tracking configuration used optical flow, local candidate queues, a five-frame history, centroid features, Euclidean distance, and Hungarian assignment, with a maximum of ten tracks. Optical flow estimates image motion; Hungarian assignment finds a minimum-cost matching between candidate identities and observations. Neither guarantees identity when the available image evidence is ambiguous.

| Setting | Recorded later choice |
| --- | --- |
| Candidate method | `local_queues` |
| Tracking window | 5 frames |
| Features / cost | `centroids` / `euclidean_dist` |
| Matching | `hungarian` |
| Motion assistance | `use_flow`, image scale 1.0 |
| Planned count | 10 instances / 10 tracks |

Kalman-assisted tracking was also evaluated earlier with a 20-frame history. The choice of motion model does not create an appearance cue that is absent from the recording.

### Detection and orientation failures

Boundary losses may arise from training coverage, crop geometry, contrast, or model thresholds. Include representative edge frames and interacting animals when reviewing annotations. Head–abdomen flips are pose-direction errors; an identity switch is a change in which animal owns the track. Improving one does not necessarily fix the other.

The development machine used an RTX 5080 with 16 GB VRAM. Larger inference batches caused out-of-memory errors; batch size 1 was used in several successful command configurations. Record the actual software versions and command for each run because SLEAP command-line interfaces change between releases. The project log includes `sleap-nn 0.3.3`.

## AMADEUS evaluation

AMADEUS learns from the input video using isolated-animal examples and synthetic interactions. It detects oriented bounding boxes and performs temporal identity association; optional direction estimation and refinement address body orientation and difficult identity segments. Official documentation describes review and correction of the resulting video and CSV as part of the workflow.

An **oriented bounding box (OBB)** represents body position, dimensions, and angle. The current custom analysis GUI uses **OBB centres** for target and movement calculations. It does not require reliable head direction for these position-based metrics.

A completed detection or association stage is not equivalent to a fully reviewed trajectory dataset. The October project log includes completed embedding work followed by a refinement failure during direction-segment correction from Windows virtual-memory exhaustion. Earlier processing also encountered a long output-path failure. These are documented execution problems, not biological outcomes.

## Identity quality review

Review annotated video around pairwise contacts, three-fly clusters, wall passages, sudden colour changes, duplicated labels, disappearances, and implausibly long jumps. Compare frames before and after each ambiguous interaction.

For a validation subset, record reviewed frames or encounters, confirmed identity switches, missed detections, unresolved cases, and the inclusion criteria. Do not describe the final data as identity-validated without this record.

## File and coordinate consistency

SLEAP `.slp` and AMADEUS `_id_resolved.csv` are different output formats. Preserve the identity mapping and original frame numbering when importing either. A temporal offset can align frames; it cannot correct a different spatial crop, resize, rotation, or frame rate.

For the AMADEUS GUI, **video frame = CSV frame − video offset**, with zero-based CSV frame numbers. The original identities are retained. The analysis does not automatically repair identity switches, smooth trajectories, or interpolate missing positions.

See [analysis definitions](../methods/analysis.md), [troubleshooting](../methods/validation.md), and the [official references](../resources/references.md).
