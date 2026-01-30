# Visual Place Learning Arena for *Drosophila melanogaster*

An open-source, low-cost implementation of a thermal-visual arena for studying spatial memory in fruit flies.

![Arena Overview](images/full.png)

---

## About This Project

This documentation describes a practical, reproducible visual place learning apparatus based on the paradigm established by Ofstad, Zuker, and Reiser (2011). Our implementation uses commercially available components and open-source control systems to make this powerful behavioral assay accessible to laboratories with limited budgets.

**Key features**:
- Generic hardware replaces specialized components
- Open-source firmware and control software
- Multiple assembly options for different lab setups
- Detailed documentation with troubleshooting guides

---

## System Components

The arena integrates four subsystems to create controlled behavioral experiments:

### Thermal Control
Peltier plates create a temperature landscape (36°C warm background, 25°C cool target) that motivates flies to navigate and learn spatial locations.

### Visual Display
P4 LED panels provide panoramic visual landmarks that flies use to remember the location of the rewarding cool tile.

### Behavioral Tracking
Infrared illumination and camera systems record fly positions throughout experiments for offline analysis.

### Remote Control
Web-based interface (via Raspberry Pi) enables wireless experiment control and monitoring.

---

## Documentation Structure

**Hardware Systems**:
- [Complete System Overview](complete_system_overview.md) - Architecture, assembly guide, cost analysis
- [Thermal Control System](thermal_control_system.md) - Peltier arrays, PID control, thermal ring
- [Visual Display System](visual_display_system.md) - P4 LED panels, ESP32 control, pattern generation
- [IR Illumination System](ir_illumination_system.md) - Lighting for behavioral tracking

**Electronics & Control**:
- [ESP32 Microcontrollers](esp32.md) - Dual-controller architecture, system coordination
- [Web-Based Control](web_server.md) - Raspberry Pi server for remote operation

**Tracking & Analysis**:
- [Monochrome Camera Selection](monochrome_camera.md) - Camera requirements by tracking method
- Behavioral Tracking (coming soon) - CTRAX vs. SLEAP implementation

---

## Design Philosophy

**Accessibility**: Uses generic components available from standard suppliers, eliminating dependence on specialized vendors.

**Transparency**: Complete documentation of hardware choices, control algorithms, and assembly procedures.

**Modularity**: Each subsystem can be built and tested independently, simplifying troubleshooting and modification.

**Scientific validity**: Maintains the core experimental logic of the original implementation while reducing cost.

---

## Getting Started

1. Review the website to understand the architecture
2. **Check the cost of materials** to assess component availability and cost
3. **Follow the assembly guide** for step-by-step construction
4. **Consult individual subsystem documentation** for detailed specifications

---

## Current Status

This is an **active research project**. The documentation reflects our current implementation and will be updated as we refine the system and conduct experiments.

## Contributing

This project is shared to support transparency and reuse within the research community. We welcome:
- Bug reports and troubleshooting insights
- Design improvements and alternative implementations
- Validation data from independent laboratories

**GitHub Repository**: [github.com/ajadismail2/Visual-place-learning](https://github.com/ajadismail2/Visual-place-learning)

## Contact

For questions or collaboration inquiries, please open an issue on the GitHub repository.

---

*This documentation is intended for research and educational use and is shared to support reproducibility and open science practices.*
