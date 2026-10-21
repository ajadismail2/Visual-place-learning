---
title: Arena and dimensions
description: The walking surface, perimeter, cover and supporting structure.
section: Hardware
---
The arena provides a level walking surface with a controlled thermal pattern. Its ring and cover define the space available to the flies. The surrounding display supplies visual information, while the camera views the walking area from above.

## Current arena specification

| Feature | Documented configuration |
| --- | --- |
| Walking-area inner diameter | **200 mm** |
| Background | 60 Peltier modules operated as one circuit |
| Targets | Four separately driven modules, A–D |
| Visual enclosure | Eight P4 HUB75 panels, 64 × 32 pixels each |
| Pixel pitch | 4 mm |
| Cover | Glass cover above the walking surface |
| Background sensor setpoint | 34.8 °C in the supplied sketch |
| Ring sensor setpoint | 45 °C in the supplied sketch |
| Target cooling interval | 300 s for each selected target |

The 200 mm measurement is the inner walking diameter. Use it for image scaling and arena layout. Ring height, cover clearance, module dimensions, carrier thickness and mounting-hole positions must be recorded from the actual components before machining or printing. Do not infer these from a photograph.

<figure class="photo-slot" data-photo-id="arena-top"><div class="photo-space" aria-label="Blank top-view arena photograph"></div><figcaption><span>Photo to add · A02</span><strong>Walking surface and target positions</strong><p>Top view with the inner diameter and the physical A–D labels identified.</p></figcaption></figure>

## Walking surface and target tiles

The background and targets must meet without a step or an accessible gap. A fly should encounter the intended temperature difference rather than an unintended obstacle. Check the surface after mounting the modules, not only when the empty carrier is level.

Label the physical targets A–D after testing their driver channels. Keep that same mapping in photographs, temperature regions, commands and analysis files. The controller's channel number is not the same as its target letter.

## Base and mounts

Fit the supports to a stable base, check that their mounting faces sit evenly, and then place the carrier. Check level in more than one direction. Mount the LED enclosure and overhead components so they do not pull or tilt the arena through cables or shared supports.

The [CAD section](../cad/index.md) reserves a record for each printed component. The actual print material, fastening details and fit measurements will be added with those part records.

## Work through the makerspace build

Measure the purchased components before drawing their mounts. A ruler establishes the overall layout; callipers are useful for hole spacing, module edges and close-fitting features. Record which dimensions are fixed by a component and which can be adjusted during assembly.

Use CAD to check the relationships between the floor, panel enclosure and recording mounts. Print a small fit sample or one mounting piece first, check it against the hardware, then produce the remaining pieces. This reduces wasted material when a hole or clearance needs changing. Keep the version that fits with the matching component photograph.

For the carrier, transfer the measured layout into a machining drawing. Use the workshop's CNC or conventional machine tools for controlled openings and mounting features. Deburr edges, inspect the finished dimensions and test the assembly without power before fitting the full thermal circuit. Printing is useful for fixtures and supports; the thermal contact beneath a Peltier needs a suitable heat-conducting part.

The low-cost approach depends on checking each interface before making the next part. Standard panels, controller boards and drivers can be tested independently while the mounts are being refined. Exact costs and workshop settings will be added only from the actual build records.

<figure class="photo-slot" data-photo-id="arena-side"><div class="photo-space" aria-label="Blank side-view photograph of arena clearances"></div><figcaption><span>Photo to add · A03</span><strong>Ring, cover and supporting structure</strong><p>Side view showing the cover clearance and how the arena is supported.</p></figcaption></figure>

## Ring and cover

The ring fixes the perimeter of the walking area. The cover limits vertical movement while leaving a clear recording view. Check that the cover rests as intended and that its placement does not disturb the ring or sensor cables. Clearance is an assembly dimension to measure and record, not a value specified here.

The ring heater has its own sensor and controller. Its sensor reading does not establish the temperature everywhere inside the chamber. See [thermal-ring setup](../hardware/ring.md).

## Aluminium carrier

The proposed carrier uses four machined openings for the target modules. CNC milling or conventional machining can produce the required openings, but the toolpath must come from measured dimensions and tolerances. Fit each target level with the surrounding surface and provide rigid support without bridging the intended thermal separation.

Separate finned heat sinks beneath the target hot sides are a proposed way to reduce heat returning into the carrier. Confirm this arrangement against the actual build before adopting it. The [heat-removal chapter](thermal-coupling.md) explains the heat path.

## Check the mechanical setup

Confirm that the walking surface is level, all parts remain fixed during cable handling, the access panel can open without moving the arena, and the complete floor remains visible to the camera. Record the final dimensions and take top, side and underside photographs before covering the wiring.
