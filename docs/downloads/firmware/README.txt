# Arena firmware — supplied 17 October 2026

Eight supplied sketches are kept in separate Arduino sketch folders. They are separate programs, not tabs of one program. The website explains their roles and incompatible revisions.

Master_Controller + LED_Slave form the supplied ESP-NOW pair. Closedloop_60peltier and Thermal_ring are independent temperature controllers. thermal_camera streams measurements to a host. SinglePanelTest is a display diagnostic. 4_peltier_mosfet_hbridge and hot_slave are alternative control implementations, not additional boards commanded by this master.

Publication changes:
- Master_Controller: private MAC/AP values removed. Copy local_config.example.h to local_config.h, fill the values, and remove its #error before compiling. Keep that file private. Control logic is unchanged.
- Thermal_ring: the supplied file is preserved, including the stray `3` after `float Kd = 150;` which prevents compilation. Thermal_ring_syntax_fixed is an optional copy with only that character removed.
- A comment label in LED_Slave and SinglePanelTest is generalized because it matched the private AP name. Other source contents are retained. Line endings may be normalized to LF.

The supplied master has a five-minute preheat, variable 1–16-step sequence, and cooling in EVERY step. It has no special all-hot eleventh trial or LED A command. See the website before using settings from another revision.

Exact board-package/library versions were not supplied. The firmware has been source-reviewed, not compiled against the hardware toolchain or tested on the apparatus during website preparation. Setpoints and PWM values are settings, not proof of achieved temperatures.
