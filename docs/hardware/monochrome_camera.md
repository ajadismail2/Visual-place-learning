---
title: Imaging & spatial calibration
description: Fixed overhead recording, a traceable pixel-to-distance scale, and frame-accurate experimental timing.
---
## Current recording configuration

The main project recordings use a **Thorlabs CS165MU monochrome camera** viewing the arena from above under infrared illumination. A **24 fps** dataset is the primary analysis reference; 30 fps and a 10 fps test have also been discussed. Use the actual frame rate of each source video rather than applying one setting to all recordings.

Tamron 16 mm C-mount and Navitar 3.5 mm lenses were evaluated during development. Lens choice, working distance, focus, and crop determine how many pixels describe each fly. A camera model alone does not establish sufficient detail for identity or head–abdomen discrimination.

## Spatial scale

The confirmed physical inner diameter is **20 cm**. One recorded image measurement was **916 pixels across the inner arena**, giving:

- **916 / 20 = 45.8 px/cm**.
- **20 / 916 = 0.021834 cm/px**.
- Equivalently **0.21834 mm/px**.

The mm/px and cm/px values differ by a factor of ten. The historical shorthand “0.218 cm/px” is incorrect for this measurement. Another recording was measured at 1033 pixels; at the same physical diameter, that corresponds to 51.65 px/cm. These scales cannot be interchanged after resizing or changing the camera field of view.

<div class="calculator" data-scale-calculator>
  <div class="calc-inputs">
    <label>Inner arena diameter in image (pixels)<input id="diameter-px" type="number" min="1" step="1" value="916"></label>
    <label>Physical inner diameter (cm)<input id="diameter-cm" type="number" min="0.1" step="0.1" value="20"></label>
    <label>Video frame rate (fps)<input id="video-fps" type="number" min="0.1" step="0.001" value="24"></label>
  </div>
  <p class="calc-result" id="scale-result" role="status">45.800 px/cm · 0.02183 cm/px · 0.2183 mm/px</p>
  <p class="calc-caption" id="frame-result">At 24 fps, one five-minute trial is 7,200 frames; three seconds of frame occupancy is 72 samples.</p>
</div>

## Calibration procedure

1. Work from the same pixel coordinate system used for tracking. Keep the crop and resolution fixed.
2. Identify the inner walking boundary, not the outer support or display enclosure.
3. Measure a known distance in the arena plane, preferably the inner diameter. Repeat in different directions to reveal perspective or lens distortion.
4. Store the measured pixel span and its physical length, alongside the resulting px/cm scale.
5. Draw target regions on the correct video frames, and record which region corresponds to A, B, C, and D.
6. Check a known distance after export to catch unit, crop, or coordinate mismatches.

A single scale factor assumes approximately uniform image scale in the plane. If different axes or regions disagree materially, correct the camera alignment or document an appropriate geometric calibration.

## Time and frame conventions

At 24 fps, 300 seconds contains **7,200 frame samples** and the ten-trial training block contains **72,000 samples**. Specify whether a frame index is zero-based or one-based and whether trial intervals include the end frame. The recommended interval notation is start-inclusive, end-exclusive.

For a zero-based start frame **f₀**, trial k spans **[f₀ + (k−1)7200, f₀ + k7200)** at exactly 24 fps. If a source ends early, report that trial's actual observed duration rather than treating it as complete.

## Video preparation

Keep the original recording and document every transformation. Spatial cropping can simplify tracking; resizing changes the scale. Frame interpolation, speed changes, and dropped or duplicated frames can change temporal interpretation. Preserve the original frame rate and use a video export with sufficient quality to retain small fly features.

H.264 MP4 has been used for manageable file sizes. Its practical suitability should be judged by whether the exported footage preserves positions, body shape, edge contrast, and timing at the intended tracking resolution. Compare representative exported frames to the source before a long inference run.

## Recording metadata

Archive camera and lens identifiers, image dimensions, frame rate or time base, exposure, gain, IR arrangement, arena diameter, crop rectangle, codec/export settings, and recording duration. Include fly count, genotype, sex, age, housing, and session identifiers when available. Missing metadata should remain explicitly unknown.

See [infrared illumination](IR_illumination_system.md) and [tracking](../software/Behavioural_tracking.md).
