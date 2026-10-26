---
title: Cameras
description: Set up behaviour recording and temperature measurements as separate data streams.
section: Hardware
---
The behaviour camera records where the flies move. The thermal camera measures surface temperature. Their files answer different questions, and one cannot replace the other: a normal video does not show whether the cooling target reached its intended temperature.

## Behaviour camera: Thorlabs CS165MU

We use a **Thorlabs CS165MU**, a 1.6 MP monochrome CMOS camera, to record the arena under infrared illumination. It records reflected light from the flies and floor; it does not measure their temperature. [Manufacturer specifications](https://www.thorlabs.com/item/CS165MU).

An expensive scientific camera is not a requirement. A lower-cost camera can be used if it is sensitive to the illumination wavelength and produces clear, stable recordings of the full arena. The lens, camera height, exposure and lighting matter as much as the camera model.

## Choosing a lower-cost camera

The practical test is whether individual flies remain distinguishable when they are close together. Look at full-resolution video of approaches, crossings and departures, including near the arena edge. A sharp still image of an isolated fly is not enough.

| Requirement | What to check in a test video |
| --- | --- |
| Infrared sensitivity | The sensor, lens and any filters pass enough of the IR illumination |
| Resolution at the arena | Nearby bodies retain separate outlines where physically visible |
| Exposure and motion blur | Walking flies remain sharp rather than streaked |
| Frame timing | Movement can be followed between frames without recording gaps |
| Full-field focus | Both the centre and perimeter remain usable for tracking |
| Recording access | Original video can be saved with known timing and limited compression artefacts |

A camera that meets these requirements can replace the CS165MU. Higher price does not guarantee better tracking, and higher pixel count alone does not compensate for poor optics or blur. Even clear video cannot guarantee identity through complete overlap; review close interactions in the tracking output.

## Position the behaviour camera

Mount the camera above the arena with the walking area centred in the image. Adjust the lens and height until the entire circular floor is visible, including its edge. Tighten the support only after confirming that the camera remains stable and that no mount blocks the view.

<figure class="photo-slot" data-photo-id="camera-view"><div class="photo-space" aria-label="Blank photograph of the overhead camera and illumination"></div><figcaption><span>Photo · H06</span><strong>Camera and IR illumination</strong></figcaption></figure>

Focus at the walking surface, then inspect the centre and edge of the image. Keep the same camera position and lens settings across recordings that share a spatial calibration. Moving the camera changes the number of image pixels corresponding to a centimetre.

## Illumination for the behaviour camera

Four generic infrared LED arrays illuminate the walking area. Printed shades, diffusers and PVC stands position the lights without requiring specialised lamp mounts. Follow the separate [Illumination chapter](illumination.md) for assembly, power and reflection checks.

## Calibrate distance and time

Measure the inner arena diameter in a frame and divide that pixel diameter by **20 cm** to obtain pixels per centimetre. Measure the walking-area boundary rather than the outer ring. An angled view can distort the circle, so correct the camera alignment before relying on a single scale factor.

Check the actual recorded frame rate and timestamps. Do not assume a video exported from another program has the same timing as the original. Keep the original recording and note the frame or time at which the first cooling step begins; the experiment controller's preheat is not the first cooling trial.

## Set up the thermal camera

[![Thermal-camera wiring and four schematic target regions](../assets/setup/measurement-setup.svg)](../assets/setup/measurement-setup.svg)

We use an **MLX90640 thermal infrared array** to examine the temperature distribution across the arena. Its 32 × 24 sensing elements provide 768 temperature values per image. The sensor detects emitted thermal radiation and uses its calibration data to estimate surface temperatures. It does not require the IR LED arrays used for behaviour recording. [Melexis sensor documentation](https://www.melexis.com/en/product/mlx90640/far-infrared-thermal-sensor-array).

The MLX90640 connects to its ESP32 over I²C. The supplied ESP32 program reads thermal frames and forwards them over USB to the computer. Its coarse image is useful for comparing target and background regions, not for distinguishing individual flies.

The sensor needs a direct view of the measured surface in thermal infrared. Ordinary glass does not provide the same transmission for thermal imaging as it does for visible or near-infrared behaviour recording. A measurement through the cover can represent the cover and reflected radiation rather than the floor. Establish suitable optical access without changing the experimental thermal conditions. [Thermal-camera viewing limitations](https://www.flir.com/discover/home-outdoor/can-thermal-imaging-see-through-walls/).

Shiny metal can reflect surrounding thermal radiation and has low emissivity, so an apparent hot or cold patch may not represent its true temperature. Check the measurement surface and emissivity assumptions against a contact reference. [Emissivity guidance](https://www.flir.com/discover/professional-tools/how-does-emissivity-affect-thermal-imaging/).

Use repeatable regions over A, B, C and D and over representative background areas. Identify the target letters by testing each physical tile. The positions in the diagram are schematic. Keep regions away from boundaries where a measurement may combine a target and its surroundings.

## Record enough to interpret a trial

Record temperatures before cooling, during the full 300-second interval and after switching away from the target. Keep the elapsed time and target order with the temperature file. A single minimum temperature cannot show whether a tile stayed cool throughout the trial or whether the arena background warmed over repeated trials.

Check thermal readings against an independent contact reference at suitable accessible locations. Store the unprocessed data as well as plots. The [camera program](../firmware/camera.md) describes the binary stream; it is not a ready-made video or a complete computer-side recorder.
