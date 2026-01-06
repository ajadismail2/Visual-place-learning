# LED Display

The visual panorama is generated using a chain of inexpensive, generic LED matrix panels commonly available from Chinese manufacturers.  
Although these panels are typically sold with proprietary controllers intended for signage applications, we bypass the stock control hardware and drive the panels directly.

This approach allows the visual display to be tightly integrated with the rest of the experimental system while keeping costs low and component availability high.

---

## Hardware Choice

The display consists of multiple HUB75-compatible LED panels arranged horizontally to form a continuous panoramic stimulus.  
These panels are widely used in commercial displays and are inexpensive, robust, and easy to replace.

Compared to the custom or modular LED display systems used in earlier implementations, this setup significantly reduces cost while still providing sufficient spatial resolution and brightness for Drosophila visual experiments.

---

## Control Architecture

Instead of relying on the original controller supplied with the panels, the display is driven directly by an ESP32 microcontroller.  
The ESP32 streams pixel data to the panels using a parallel interface designed for HUB75 matrices, allowing precise control over timing, brightness, and displayed patterns.

To achieve stable, flicker-free output across multiple chained panels, the system makes use of the ESP32’s DMA (Direct Memory Access) capabilities.  
This allows the microcontroller to continuously refresh the display without occupying the main processor, resulting in reliable performance even at larger display sizes.

---

## Visual Patterns

All panels in the chain can display identical or coordinated visual elements, making it straightforward to present repeated patterns or simple landmarks across the panorama.  
This matches the experimental requirement of providing consistent visual cues while keeping the stimulus design easy to understand and reproduce.

The static and deterministic nature of the display also simplifies synchronization with other parts of the system, such as thermal control and behavioral tracking.

---

## Comparison to Prior Implementations

Earlier visual place learning arenas relied on purpose-built or modular LED display systems that offer excellent performance but can be costly and difficult to reproduce outside specialized labs.  

By using generic LED panels and an open microcontroller-based control scheme, this setup achieves the same functional goals while remaining accessible, repairable, and adaptable.  
The display resolution and refresh characteristics are sufficient for the task, and the reduced complexity makes the system easier to modify for alternative experimental designs.

---

## Notes

This design prioritizes practicality and reproducibility over maximal display sophistication, aligning with the goal of making visual place learning hardware easier to build and maintain in typical laboratory settings.
