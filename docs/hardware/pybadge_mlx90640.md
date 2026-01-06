# PyBadge Thermal Camera (MLX90640)

The PyBadge equipped with an MLX90640 thermal sensor is used as an **optional tool** for monitoring and validating the thermal behavior of the arena.  
It provides a simple way to visualize temperature patterns without physically contacting the arena surface.

This makes it especially useful during setup, calibration, and troubleshooting.

---

## Purpose

The primary role of the thermal camera is to confirm that the Peltier plates beneath the arena are heating and cooling as expected.  
By viewing the temperature distribution across the arena in real time, it is possible to quickly identify uneven heating, inactive elements, or wiring issues.

This non-contact measurement avoids disturbing the arena and reduces the risk of damage during testing.

---

## Optional Use

The PyBadge thermal camera is **not required for routine experiments**.  
Once the thermal system is configured and verified, the arena can be operated without the camera.

Its inclusion is intended to support initial setup, system validation, and occasional checks rather than continuous use.

---

## Closed-Loop Control (Optional)

In addition to visualization, the thermal camera can be used as part of a closed-loop temperature control scheme.  
In this mode, temperature measurements from the arena are used to adjust the Peltier plates automatically, helping maintain stable thermal conditions over time.

This functionality is described in the software section and can be enabled if tighter temperature regulation is desired.

---

## Why Use the PyBadge Platform

The PyBadge was chosen because it integrates a microcontroller, display, and power management in a single, compact device.  
This makes it easy to deploy as a standalone thermal monitor without additional computers or specialized equipment.

The MLX90640 sensor provides sufficient spatial resolution to observe temperature patterns relevant to the arena, while remaining affordable and easy to replace.

