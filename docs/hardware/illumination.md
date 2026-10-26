---
title: Illumination
description: Low-cost infrared LED arrays with printed lampshades and PVC supports for behaviour recording.
section: Hardware
---
We use four inexpensive, generic infrared LED arrays to illuminate the arena for behaviour recording. Each array sits inside a 3D-printed lampshade mounted on a PVC pipe. A diffuser over the array spreads the light across the walking surface.

The [generic IR array module linked here](https://www.amazon.in/Generic-Array-Infrared-Module-Camera/dp/B0DPKYDQDS) is the type used in this build. The brand is not essential. Similar low-cost IR arrays can work when their wavelength matches the camera's sensitivity and they provide even, stable illumination at the required exposure.

## Why infrared illumination?

The surrounding green LED panels provide the experimental visual pattern. The IR arrays provide the light needed by the recording camera. Keeping these roles separate allows flies to remain visible in recordings as the panorama changes. This illumination is reflected near-infrared light, not the thermal radiation measured by the MLX90640.

An ordinary camera with strong IR-blocking filters may give a poor image under these lights. Test the camera, lens and light together before choosing a replacement. An IR label alone does not establish the brightness or image quality in the assembled arena.

## Printed shade and PVC stand

The lampshade locates the array and supports the diffuser. The PVC pipe sets the light's height, with printed fittings holding the shade at the required angle. This arrangement uses a standard pipe and a small number of printed parts instead of a specialised laboratory lamp mount. A printed tube can replace the PVC pipe.

Fix the stand securely so its angle does not change during recording. Leave room for the array to dissipate heat and route the cable down the support with strain relief. The diffuser must transmit the array's infrared wavelength; judge its effect in the camera image rather than by how it looks to the eye.

[IR stand and lampshade CAD](../cad/index.md#03-infrared-light-stand) · [Download the STEP model](../downloads/cad/ir-light-stand.step)

<figure class="photo-slot" data-photo-id="illumination-assembly"><div class="photo-space" aria-label="Space for a photograph of the IR array, diffuser, printed lampshade and PVC stand"></div><figcaption><strong>IR array, diffuser and printed shade on the PVC stand</strong></figcaption></figure>

## Power and positioning

Use the voltage and polarity marked on the particular IR module, with a supply rated for the combined load. Connect the arrays through their power inputs, not directly to ESP32 GPIO pins. The IR lights and HUB75 visual panels have separate power requirements.

Arrange the four lights around the arena and aim them toward the walking surface. Adjust one light at a time while watching the behaviour camera. Avoid bright reflections from the glass cover or carrier, dark regions at the perimeter and supports that obstruct the camera. Increasing brightness alone will not remove glare.

## Check before recording

| Check | What a suitable setup provides |
| --- | --- |
| Centre and edge | Flies remain distinguishable across the full arena |
| Nearby flies | Separate body boundaries are visible while flies approach each other |
| Movement | Exposure is short enough to avoid blurred fly outlines |
| Stability | No obvious brightness pulsing or changes during a trial |
| Reflections | No saturated patches that hide flies or resemble them in tracking |
| Heating | Lights and their mounts do not introduce unwanted arena warming |

Use fixed exposure and gain where available, and save a short test recording with the final arrangement. Examine moving flies and close encounters at full image resolution. A low-cost array is suitable when it passes these checks; a particular seller or brand is not required.

[Camera selection and recording](imaging.md) · [Tracking with AMADEUS](../analysis/tracking.md)
