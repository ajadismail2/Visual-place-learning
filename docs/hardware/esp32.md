# ESP32

The ESP32 acts as the central coordinator of the visual place learning apparatus.  
Rather than serving as a complex computing platform, it is used here as a **reliable, low-cost controller** that links together the main hardware components of the system.

Its role is to ensure that visual stimuli, thermal conditions, and timing are applied in a consistent and repeatable way during experiments.

---

## Role in the System

In this setup, the ESP32 functions as a simple integration layer between different subsystems.  
It controls the LED display, manages the thermal elements beneath the arena, and provides a single point of coordination for experimental states.

By using one controller for multiple tasks, the system remains compact and easier to reason about during setup and troubleshooting.

---

## Why Use an ESP32

The ESP32 was chosen because it is inexpensive, widely available, and well supported by open-source tools.  
It provides enough processing capability to handle display updates and hardware control without requiring a full computer.

Importantly, the ESP32 can operate independently once configured, which reduces reliance on external software during experiments and helps ensure stable, repeatable behavior.

---

## Interaction with Other Components

The ESP32 communicates directly with the LED display panels and the thermal control hardware.  
These interactions are deterministic: when a particular experimental condition is selected, the corresponding visual and thermal settings are applied together.

This makes it straightforward to link visual landmarks with thermal states, which is central to the visual place learning task.

---

## Practical Considerations

Using a microcontroller rather than a general-purpose computer reduces system complexity and power consumption.  
It also minimizes background processes and software dependencies that can introduce unintended variability.

From a practical perspective, the ESP32-based design is easy to replicate across setups and can be adapted incrementally as experimental needs change.