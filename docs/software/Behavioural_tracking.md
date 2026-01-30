# Behavioral Tracking Pipeline

## Overview

Accurate behavioral tracking is a critical component of the visual place learning arena. Tracking quality directly affects downstream analyses such as trajectory reconstruction, path length, time-to-target, and learning indices. This document outlines the evolution of the tracking approach, the limitations encountered with classical methods, and the motivation and requirements for transitioning to an AI-based tracking framework.

---

## Initial Tracking Approach: CTRAX

### What is CTRAX

CTRAX is a well-established, open-source tracking software widely used for *Drosophila* behavior analysis.

* Official website: [https://ctrax.sourceforge.net/](https://ctrax.sourceforge.net/)
* Classical computer vision–based approach
* Primarily uses **centroid tracking** to follow animals over time

### Why CTRAX Was Initially Chosen

CTRAX was selected during the early phase of the project because:

* It is robust for **single-fly** or **sparse multi-fly** experiments
* Works reliably with modest camera resolutions
* Well-documented and widely validated in the literature
* Integrates easily with IR-illuminated arenas

For early validation experiments, CTRAX performed well and enabled rapid iteration of the arena design and behavioral protocol.

### Key Limitation of CTRAX

The main limitation of CTRAX arises from its reliance on centroid-based identity assignment:

* When **flies come close together or collide**, individual identities are lost
* After separation, identities may be reassigned incorrectly
* This results in:

  * Track fragmentation
  * Identity swapping between flies
  * Trial-to-trial inconsistencies

In the context of visual place learning experiments:

* Social interactions increase as flies converge on the cool tile
* Identity loss between trials alters trajectory statistics
* Pattern changes across trials make post hoc correction difficult

As a result, CTRAX becomes unreliable for **dense multi-fly experiments across repeated trials**, especially when individual-level learning metrics are required.

---

## Transition to AI-Based Tracking: SLEAP

### Why SLEAP

To overcome the limitations of centroid tracking, we aim to transition to **SLEAP (Social LEAP Estimates Animal Poses)**:

* Official website: [https://sleap.ai/](https://sleap.ai/)
* Deep learning–based, multi-animal tracking framework
* Uses **pose estimation and identity tracking**, not just centroids

This transition aligns strongly with the broader goals of the project.

### Alignment With Project Goals

This project is funded by **Mphasis**, a technology-driven AI-focused company. Accordingly:

* Emphasis is placed on **AI and machine learning methodologies**
* Moving from classical CV to deep learning strengthens the technical narrative
* Enables exploration of:

  * Pose-level behavioral features
  * Robust identity preservation
  * Scalable analysis pipelines

SLEAP is therefore not only a technical improvement, but also a strategic one.

### Advantages of SLEAP Over CTRAX

SLEAP offers several decisive advantages:

* **Identity preservation** even during close interactions and overlaps
* Robust tracking when multiple flies cluster at the cool tile
* Supports:

  * Multi-animal experiments
  * Long-duration trials
  * Trial-to-trial continuity
* Extensible to future analyses (e.g., posture, orientation, social behavior)

In practice, this means that SLEAP does **not lose track of individual flies** when they come together, solving the primary failure mode observed with CTRAX.

---

## Camera and Resolution Requirements (Critical Caveat)

### Why Resolution Matters for SLEAP

Unlike centroid-based methods, SLEAP relies on learning visual features of the animal:

* Body shape
* Orientation
* Relative position of keypoints

This makes **image resolution a critical constraint**, especially in large arenas.

In our setup:

* The arena diameter is relatively large
* Flies occupy a small fraction of the field of view
* Each fly must span **sufficient pixels** for the neural network to distinguish individuals

If the fly occupies too few pixels:

* Keypoints cannot be resolved
* Identity tracking degrades
* Model performance drops sharply

### Practical Pixel Requirements

Empirically and based on SLEAP best practices:

* A fly should occupy **at least 20–30 pixels in body length**
* Higher is strongly preferred (40–60 pixels) for multi-animal tracking

This requirement directly informs camera selection.

---

## Recommended Camera Specifications

### Minimum Viable Configuration

* **Resolution**: 1920 × 1080 (Full HD)
* **Sensor**: Monochrome or IR-sensitive CMOS
* **Frame rate**: ≥ 30 fps (60 fps preferred)
* **Lens**: Adjustable C-mount or CS-mount

This configuration may work for small arenas or reduced field-of-view imaging, but is borderline for large arenas.

### Recommended Configuration (Preferred)

For reliable SLEAP performance in a large arena:

* **Resolution**: 4K (3840 × 2160)
* **Sensor**: Global shutter preferred (rolling shutter acceptable)
* **Bit depth**: ≥ 8-bit (10–12 bit ideal)
* **Frame rate**: 30–60 fps
* **Lens**:

  * Narrower field of view to maximize pixel density
  * Low distortion

### Example Camera Options

* Industrial USB cameras (e.g., FLIR / Basler / Arducam industrial line)
* Raspberry Pi HQ Camera with high-quality C-mount lens
* Machine-vision monochrome cameras with IR sensitivity

### Illumination Considerations

* Uniform **IR illumination** is essential
* Avoid shadows and reflections from the glass cover
* High signal-to-noise ratio improves SLEAP training and inference

---
