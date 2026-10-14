---
title: Mechanical design & fabrication
description: Level supports, repeatable arena access, and fixtures that preserve experimental geometry.
---
## Design priorities

Mechanical design supports measurement quality. Arena tilt can change behaviour, movement of the camera changes calibration, and an unstable light mount changes image contrast. Components should be rigid during acquisition and repeatable after opening or reassembly.

The current design record includes a 20 cm inner arena, glass cover, a 4 mm aluminium base plate (220 × 225 mm), an octagonal LED surround, and printed supports. The separate sociability development uses a 5 cm Delrin arena; it is not the same geometry as the place-learning apparatus.

## Breadboard supports

Four approximately **100 mm long supports** were requested for mounting to a Thorlabs aluminium breadboard. A screw was measured at approximately **5.42 mm diameter**. That measurement alone does not identify its thread standard or determine a finished printed-hole tolerance.

For alignment, the support contact faces, seating, fastener clearance, and plate stiffness matter together. Check all four support heights and the installed arena plane. Print a small fit coupon before a full set, and verify that tightening does not introduce tilt.

## A panel that opens like a door

The access concept uses **a hinge on one vertical side** and **a releasable pin or catch on the other**. Top and bottom hinge features share one axis. Rigidly fastening the opposite edge prevents the panel swinging, even when the hinge side is free.

The design objectives are:

- Retain mounting regions for the panel's existing screws.
- Open without repeatedly unscrewing the panel from its neighbours.
- Provide repeatable closure and preserve the intended panel alignment.
- Leave clearance for the moving panel, neighbouring faces, ribbon cables, and power leads.
- Keep the top and bottom hinge axes coaxial.

A zero-gap appearance in the closed position must be reconciled with the swept volume of the panel during opening. The actual hinge offset and clearance require a fit check against the real panel dimensions.

## Current CAD record

| Design item | Source design recorded | Release status |
| --- | --- | --- |
| Panel hinge | `Hinge_PrintInPlaceV2_VC.stp` | Project source reference; fit and print validation not established here |
| Parametric hinge | `butt_hinge_3.8.scad` | Reference by Rohin Gosling; not publicly hosted here |
| Octagon fixture | `Octagon Holder.step`, `Octagon Holder(1).stl` | Design iterations recorded |
| PVC illumination support | `PVC IR STANDE.step`, `PVC PIPE.step`, `PVC Pipe Holder.step` | Stability refinements in progress |
| Breadboard supports | `supports.stl` | Design recorded; installed levelling check required |

The [resource index](../resources/files.md) lists the supplied STEP, SCAD, and STL design references. These project source files are not publicly hosted here. A design file does not establish fit, material suitability, or print validation.

## Small Delrin arena

The sociability development includes a **5 cm Delrin arena on acrylic**. The attachment must preserve a flat, repeatable contact and avoid introducing spatially uneven edges, residues, or odour cues. A fixture or adhesive choice should be assessed using the assembled arena and the specific behavioural protocol rather than assumed neutral from its generic material name.

## Fabrication record for reproducibility

Record CAD revision, units, material, print orientation, layer height, wall count, infill, supports, clearances, and any post-processing. Keep photographs of the assembled part and the fit test. A downloadable STEP or STL is useful, but it does not replace tolerance and assembly information.

See [architecture](../complete_system_overview.md), [illumination](../hardware/IR_illumination_system.md), and [validation](../methods/validation.md).
