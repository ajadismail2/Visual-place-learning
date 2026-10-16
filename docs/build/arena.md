---
title: Making the arena
description: The physical assembly developed through a wooden base, CAD models, printed fixtures, and repeated fit checks.
section: 01 / Mechanical build
---
## Start with parts that can be changed

The early makerspace build used a wooden baseplate and printed parts for the thermal ring, infrared-light stands, and thermal-camera case. The LED surround was assembled from eight standard panels. Onshape brought the panel dimensions and mounting geometry into the same model before the fixtures were printed.

This divided the work into replaceable parts. A holder could be revised without replacing a display panel; a stand could be remade without rebuilding the thermal floor. It also made dimensions at the interfaces—the screw positions, support heights, and cable clearance—more important than a polished enclosure.

## The floor and its support are different parts

The walking region is a **20 cm diameter arena** under a glass cover. The thermal design uses 60 background Peltier modules and four separate targets. The build notes also record acrylic support material and a later **4 mm aluminium plate, 220 × 225 mm**. These are revisions to the supporting assembly, not different measurements of the inner arena.

Aluminium has a thermal role as well as a structural one: it conducts heat between the modules and their support. Printed parts position the assembly, but their dimensions alone cannot establish the floor's temperature distribution. The [heat-flow page](thermal-coupling.md) explains why that distinction mattered during testing.

<div class="build-sheet" markdown="1">

### Build sheet · supporting the arena

| Part or operation | What the project record establishes |
| --- | --- |
| Base construction | A wooden baseplate was made in the makerspace |
| CAD and printing | Thermal ring, light stands, thermal-camera case, and mounting parts |
| Later support design | Four approximately 100 mm supports for a Thorlabs breadboard |
| Screw fit | A screw diameter of 5.42 mm was measured; this does not specify its thread |
| Assembly check | Equal seating and an arena that does not rock or tilt |

</div>

## Making access easier

Opening the LED surround initially meant removing screws. The next design used a hinge on one edge of a panel and a removable pin or catch on the opposite edge. The first practical obstacle was simple: a panel cannot swing while its other edge is still rigidly screwed to the adjacent panel.

The work then moved to hinge clearance, repeatable closure, and access to the retaining pin. Separate printed standoffs to raise the assembly by **16 mm** were requested in the later revision. These access and height changes remain design iterations until their assembled fit is checked; they are not a second arena design.

## Mounting the illumination

A PVC support with a light assembly exposed another limit of a cheap attachment: the taped holder did not stay fixed under the overhanging load. This became a support-design problem involving the footprint and load path, not just the amount of tape. A revised printed support was explored; a final stable mounting is not established in the available record.

<p class="source-note">Project construction account, January 2026; arena and support notes, September–October 2026; hinge and standoff revisions through 16 October. Laser cutting was part of the makerspace skill set, but no specific cutting process is assigned to these parts without a fabrication record.</p>
