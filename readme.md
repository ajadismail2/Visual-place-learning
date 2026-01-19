# Visual Place Learning in Drosophila melanogaster

This repository contains code and analysis pipelines for studying visual place learning in *Drosophila melanogaster* using a cost-effective and accessible experimental and computational framework.

The project aims to reproduce key behavioral signatures of visual place learning using simplified hardware, open-source tools, and modular analysis scripts. The framework is designed to be easily adopted in small laboratories, teaching environments, and resource-limited settings.

Project website:  
https://ajadismail2.github.io/Visual-place-learning/

---

## Repository Structure and Usage

### Closed_Loop_Thermal_Camera

This folder contains all necessary scripts to implement closed-loop temperature control of Peltier plates using an Adafruit PyBadge and an Adafruit MLX90640 IR thermal camera.

The code can be adapted to work with any sufficiently powerful development board and compatible IR camera.

**Calibration_tool.py**  
This script is used to determine the coordinates of the four Peltier plates from the thermal image. After calibration:

1. Save the detected coordinates in a file named `coordinates.txt`
2. Run `pid_control_pybadge.py`

**pid_control_pybadge.py**  
This script should be uploaded to the PyBadge. It implements PID-based closed-loop temperature control and UART communication between the PyBadge and an ESP32.

Important: Ensure that the correct TX and RX pins are assigned for UART communication between the PyBadge and ESP32.

---

### Test_UART_communication_between_PyBadge_and_ESP32

This folder contains scripts to test UART communication between the PyBadge and ESP32 before implementing the full closed-loop control system.

---

### LED_Display

This folder contains scripts to generate and display the visual stimulation patterns described in the associated paper using generic P4 LED panels.

---

### Master-Slave-Codes

This folder contains firmware for a distributed ESP32 architecture:

- Master ESP32: Controls the LED display
- Slave ESP32: Controls the four Peltier plates

---

### GUI

This folder contains Tkinter-based graphical user interface scripts for easier control of the entire experimental setup.

Two versions of the GUI are provided:

- Generic camera GUI using OpenCV for camera access and tracking
- Thorlabs camera GUI, which requires installation of the Thorlabs SDK and command-line access to the camera

---

## Design Philosophy

- Low-cost and accessible hardware
- Modular and open-source software
- Easy replication and extension
- Suitable for education, small laboratories, and rapid prototyping

---

