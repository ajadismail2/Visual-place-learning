# Arena firmware — supplied 17 October 2026

Seven controller sketches are kept in separate Arduino sketch folders. They are separate programs, not tabs of one program. The website explains their roles and incompatible revisions.

Experiment_Controller + Display_Controller form the supplied ESP-NOW pair. Closedloop_60peltier and Thermal_ring are independent temperature controllers. thermal_camera streams measurements to a host. SinglePanelTest is a display diagnostic. 4_peltier_mosfet_hbridge is an alternative bench-control program with its own pin assignments.

Publication changes:
- Experiment_Controller: private MAC/AP values removed. Copy local_config.example.h to local_config.h, fill the values, and remove its #error before compiling. Keep that file private. Control logic is unchanged.
- Thermal_ring: the supplied file is preserved, including the stray `3` after `float Kd = 150;` which prevents compilation. Thermal_ring_syntax_fixed is an optional copy with only that character removed.
- A comment label in Display_Controller and SinglePanelTest is generalized because it matched the private AP name. Controller filenames, comments, serial-log labels and internal identifiers use experiment/display terminology. Control commands and logic are unchanged. Line endings may be normalized to LF.

The supplied experiment controller has a five-minute preheat, variable 1–16-step sequence, and cooling in EVERY step. It has no special all-hot eleventh trial or LED A command. See the website before using settings from another revision.

Exact board-package/library versions were not supplied. The firmware has been source-reviewed, not compiled against the hardware toolchain or tested on the apparatus during website preparation. Setpoints and PWM values are settings, not proof of achieved temperatures.
