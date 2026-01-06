# Peltier Plates

The Peltier plates are used to heat and cool the arena floor, creating the thermal conditions required for the visual place learning task.  
As in previously published implementations, temperature differences across the arena define the behavioral target, but the specific hardware choices here emphasize simplicity and cost.

---

## Design Approach

Rather than using specialized or custom thermoelectric modules, this setup uses **generic, commercially available Peltier plates**.  
These modules are inexpensive, easy to source, and have proven sufficient for reliably generating the required temperature contrast in the arena.

In practice, the performance of these Peltiers has been comparable for our purposes, while significantly reducing overall system cost and replacement difficulty.

---

## Control Strategy

Early versions of the system were operated manually, with individual Peltier elements set to heating or cooling modes during experiments.  
This approach was useful during initial testing and validation of the arena layout.

To streamline operation and improve repeatability, the thermal control was later integrated with the visual stimulation system.  
Each visual pattern presented in the arena is now associated with a corresponding thermal configuration, allowing temperature changes to be applied automatically as part of the experimental sequence.

The Peltiers are driven by an H-bridge motor driver and controlled by an embedded microcontroller, enabling bidirectional current flow and straightforward switching between heating and cooling modes.

---

## Current Implementation

The current setup uses a small number of Peltier plates arranged beneath the arena floor, each controlled independently.  
This provides sufficient flexibility to reproduce the thermal conditions required for the task while keeping the electronics simple and easy to debug.

The design prioritizes transparency and accessibility over tight temperature regulation, which aligns with the exploratory and prototyping nature of the system.

---

## Notes on Reliability

**PS:** We have observed that low-cost Peltier modules can have a shorter operational lifespan compared to higher-grade alternatives.  
To address this, the system has been extended with a closed-loop Peltier control scheme, which is described in a later section.
