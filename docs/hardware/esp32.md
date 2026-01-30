# ESP32 Microcontroller System

The arena uses two ESP32 microcontrollers to manage thermal control and visual display independently. This distributed control architecture provides modularity, real-time performance, and simplified debugging compared to a single-controller approach.

![ESP32 System Architecture](images/esp32_system_diagram.jpg)
*Dual ESP32 architecture: Thermal Controller + Display Controller*

---

## System Architecture

### Why Two ESP32s?

**Thermal Control ESP32** and **Display Control ESP32** operate independently but coordinate through commands from the Raspberry Pi (or main computer).

**Advantages of distributed control**:
- **Parallel processing**: PID temperature control runs continuously without interference from display refresh
- **Modularity**: Each subsystem can be developed, tested, and debugged independently
- **Real-time guarantees**: Display DMA refresh isn't interrupted by temperature calculations
- **Fault isolation**: If one controller crashes, the other continues operating
- **Development flexibility**: Two people can work on thermal and visual systems simultaneously

---

## ESP32 #1: Thermal Control

### Responsibilities

![Thermal Control ESP32](images/esp32_thermal_block_diagram.jpg)
*Thermal controller connections and data flow*

**Primary functions**:
1. **PID temperature control**: Continuously reads temperature sensors and adjusts Peltier power
2. **Quadrant management**: Controls which 4 Peltier plates receive cooling (the "cool tile")
3. **Thermal ring control**: Maintains heated perimeter barrier
4. **Safety monitoring**: Prevents overheating and implements thermal limits

### Hardware Connections

**Inputs**:
- **Temperature sensors** (DS18B20 or thermal camera): Connected via 1-Wire protocol or I²C
- **Serial commands** from Raspberry Pi: USB connection (115200 baud)

**Outputs**:
- **H-bridge motor driver** (IBT-2): Controls 4 precision Peltier plates (PWM signal)
- **Relay/SSR**: Controls 60-plate bulk thermal array (on/off)
- **Thermal ring**: PWM control via MOSFET (optional dimming)
- **Status LEDs**: Visual feedback for system state

**Pin assignments** (example):
- GPIO 4: DS18B20 temperature sensor (1-Wire)
- GPIO 25: H-bridge PWM output (Peltier control)
- GPIO 26: Relay control (bulk thermal on/off)
- GPIO 27: Thermal ring PWM
- GPIO 2: Status LED

### Operating Modes

**Mode 1: Bulk warming** (all trials)
- Activate all 60 Peltier plates to maintain 36°C background
- Simple on/off control via relay

**Mode 2: Precision cooling** (during trials)
- PID algorithm adjusts power to 4 specific Peltier plates
- Target: 25°C ± 0.5°C
- Update rate: 10-50 Hz (fast enough for stable control)

**Mode 3: Quadrant rotation** (between trials)
- Switch which 4 plates are actively cooled
- Coordinate with visual display rotation
- Brief heating pulse (60 seconds) to disperse flies from previous cool tile

### PID Control Loop

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  Read Temperature → PID Calculation → PWM Out  │
│         ▲                                │      │
│         │                                │      │
│         └────── Feedback Loop ───────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Loop timing**:
- Temperature read: Every 100ms (10 Hz)
- PID update: Every 100ms
- PWM frequency: 5 kHz (smooth Peltier control)

**Parameters stored in EEPROM**:
- PID gains (Kp, Ki, Kd)
- Temperature setpoints (25°C cool, 36°C warm)
- Calibration offsets for sensors
- Safety limits (max 45°C to prevent damage)

### Serial Command Interface

**Receives commands from Raspberry Pi or computer**:
- `SET_TEMP:25` - Set target temperature to 25°C
- `COOL_TILE:2` - Activate cooling in quadrant 2 (Q3, 180°)
- `BULK_ON` - Enable bulk thermal array
- `BULK_OFF` - Disable bulk thermal array
- `GET_STATUS` - Request current temperatures and system state

**Sends responses**:
- `OK:TEMP_SET` - Command acknowledged
- `STATUS:25.3,36.1` - Current temperatures (cool tile, bulk)
- `ERROR:SENSOR_FAIL` - Sensor disconnected or reading invalid

### Startup Sequence

1. **Initialize hardware**: Configure GPIO pins, start PWM channels
2. **Read calibration**: Load PID parameters from EEPROM
3. **Sensor check**: Verify all temperature sensors respond
4. **Self-test**: Brief activation of each output to verify connections
5. **Wait for commands**: Enter idle state, ready to receive instructions
6. **Status LED**: Blink pattern indicates "ready"

---

## ESP32 #2: Visual Display Control

### Responsibilities

![Display Control ESP32](images/esp32_display_block_diagram.jpg)
*Display controller managing 8 LED panels via HUB75 interface*

**Primary functions**:
1. **Real-time display refresh**: Drive 8× P4 LED panels at >180 Hz (flicker-free)
2. **Pattern generation**: Create visual landmarks (vertical/horizontal/diagonal bars)
3. **Rotation control**: Synchronize pattern rotation with cool tile position
4. **Brightness management**: Adjust intensity for optimal fly visibility

### Hardware Connections

**Inputs**:
- **Serial commands** from Raspberry Pi: USB connection (115200 baud)

**Outputs**:
- **HUB75 interface**: 16 GPIO pins connected to LED panel chain
  - R1, G1, B1, R2, G2, B2 (RGB data for upper/lower halves)
  - A, B, C, D (row address selection)
  - CLK (pixel clock)
  - LAT (latch signal)
  - OE (output enable / brightness PWM)

**Pin assignments** (example for ESP32-HUB75-MatrixPanel-DMA library):
- GPIO 25, 26, 27: R1, G1, B1
- GPIO 14, 12, 13: R2, G2, B2
- GPIO 23, 19, 5, 18: A, B, C, D
- GPIO 15: CLK
- GPIO 32: LAT
- GPIO 33: OE

### DMA-Driven Refresh

**Why DMA is critical**:
- **Flicker-free display**: Continuous refresh without CPU intervention
- **High frame rate**: Achieves >200 Hz refresh (above fly flicker fusion at 200-250 Hz)
- **Smooth patterns**: No visible tearing or flickering during rotation
- **CPU available**: Main processor free for serial communication and pattern updates

**How DMA works**:
```
Frame Buffer (RAM) → I2S Peripheral → DMA Controller → GPIO Pins → LED Panels
         ▲                                                              │
         │                                                              │
         └───────────── Circular buffer loops ─────────────────────────┘
```

The ESP32's I2S peripheral (normally for audio) is repurposed to stream pixel data via DMA:
- Frame buffer holds entire display state (512×32 pixels)
- DMA continuously reads buffer and outputs to GPIO pins
- No CPU cycles required for refresh (runs in background)
- Double buffering: Draw to back buffer while front buffer displays

### Visual Pattern Library

**Pre-defined patterns**:
1. **Vertical bars**: 15° wide bars, vertical orientation
2. **Horizontal bars**: 15° wide bars, horizontal orientation  
3. **Diagonal bars (45°)**: 15° wide bars, diagonal orientation
4. **Diagonal bars (135°)**: 15° wide bars, opposite diagonal
5. **Solid white**: Calibration/testing
6. **Blank**: All LEDs off

**Pattern rotation**:
- Patterns stored as pixel arrays in memory
- Rotation = shift pixel data by offset (modulo 512 pixels)
- 90° rotation = 128-pixel shift (512 pixels / 4 quadrants)
- Instant rotation updates between trials (<100ms)

### Synchronization with Thermal System

**Coupled mode** (standard experimental protocol):
1. Raspberry Pi sends command: `COOL_TILE:2` to Thermal ESP32
2. Raspberry Pi sends command: `ROTATE:180` to Display ESP32
3. Both ESP32s execute simultaneously
4. Cool tile appears in Q3 (180°) with matching visual landmark

**Timing coordination**:
- Thermal ESP32 responds: `OK:COOL_TILE_ACTIVE` (~200ms)
- Display ESP32 responds: `OK:ROTATED` (~50ms, nearly instant)
- Total coordination time: <500ms
- Trial starts after both confirmations received

### Brightness Control

**Adaptive brightness**:
- Default: 50% brightness (128/255 PWM)
- Higher for pilot studies (verify flies see patterns)
- Lower for long experiments (reduce LED heating)

**PWM frequency**: 1-5 kHz via OE pin (invisible to flies, smooth to cameras)

### Startup Sequence

1. **Initialize DMA**: Configure I2S peripheral for GPIO output
2. **Allocate frame buffers**: Reserve RAM for double buffering
3. **Load default pattern**: Display vertical bars at 0° rotation
4. **Start continuous refresh**: Begin DMA-driven display loop
5. **Wait for commands**: Enter idle state, ready to rotate patterns
6. **Status indicator**: Displays test pattern on successful initialization

---

## Inter-ESP32 Coordination

### Master-Slave vs. Peer-to-Peer

**Current implementation**: Peer-to-peer with Raspberry Pi orchestration

```
     Raspberry Pi (Orchestrator)
           │         │
      Command A  Command B
           │         │
           ▼         ▼
    Thermal ESP   Display ESP
           │         │
      Response    Response
           │         │
           └────┬────┘
                ▼
        Synchronized Action
```

**Alternative**: Direct ESP32-to-ESP32 communication
- Thermal ESP32 = Master (sends rotation commands to Display ESP32)
- Reduces latency (no round-trip through Raspberry Pi)
- More complex firmware (requires additional serial connection)

### Command Timing

**Typical experiment sequence**:

| Time | Raspberry Pi → Thermal ESP32 | Raspberry Pi → Display ESP32 |
|------|------------------------------|------------------------------|
| 0:00 | `BULK_ON` | `ROTATE:0` |
| 0:10 | `COOL_TILE:0` | (no change) |
| 5:10 | `COOL_TILE:NONE` (heating pulse) | (no change) |
| 5:20 | `COOL_TILE:1` | `ROTATE:90` |
| 10:20 | `COOL_TILE:NONE` | (no change) |
| 10:30 | `COOL_TILE:3` | `ROTATE:270` |
| ... | (continue for 10 trials) | ... |

**Synchronization tolerance**: Commands sent within 50ms of each other appear simultaneous to flies.

---

## Power Management

### ESP32 Power Consumption

**Typical current draw**:
- **Thermal ESP32**: 150-250 mA (PID calculations + sensor reads)
- **Display ESP32**: 200-400 mA (DMA active, display refresh)

**Power sources**:
- **Option 1**: USB power from Raspberry Pi (if using web control)
- **Option 2**: Dedicated 5V regulator from Meanwell PSU
- **Option 3**: USB power adapter (5V 1A minimum per ESP32)

**Advantage of USB power from Raspberry Pi**:
- Serial communication + power in single cable
- Automatic ESP32 reset when Pi reboots
- Simplified wiring

### Heat Dissipation

ESP32s generate minimal heat (<1W each), but consider:
- **Add heatsink** if enclosing in small case
- **Ventilation** if operating in warm environment (near Peltier hot side)
- **Monitor temperature**: ESP32 has internal temperature sensor (check if >60°C)

---

## Firmware Architecture

### Thermal ESP32 Firmware Structure

**Main loop** (simplified flow):
```
Setup:
  - Initialize pins, sensors, PID controller
  - Load calibration from EEPROM
  - Verify hardware connections

Loop:
  - Read temperature sensors (every 100ms)
  - Calculate PID output
  - Update PWM to H-bridge
  - Check for serial commands
  - Send status updates (if requested)
  - Monitor safety limits
```

**Critical sections**:
- Temperature reading must not be interrupted (use mutex if FreeRTOS)
- PID calculation uses floating-point math (ensure sufficient stack size)
- EEPROM writes only during calibration (not every loop, causes wear)

### Display ESP32 Firmware Structure

**Main loop** (simplified flow):
```
Setup:
  - Initialize DMA and I2S peripheral
  - Allocate frame buffers
  - Load default pattern
  - Start continuous refresh (background task)

Loop:
  - Check for serial commands
  - If rotation requested:
    - Update back buffer with rotated pattern
    - Swap buffers (atomically)
  - Monitor DMA status
  - Adjust brightness if commanded
```

**Multi-tasking** (FreeRTOS):
- **Task 1 (Core 0)**: DMA refresh (highest priority, never blocks)
- **Task 2 (Core 1)**: Serial communication and pattern updates

### Memory Management

**RAM usage**:
- **Thermal ESP32**: ~50 KB (PID state, sensor buffers, command parsing)
- **Display ESP32**: ~150-200 KB (frame buffers for 512×32 display)

**ESP32 has 520 KB SRAM** - plenty of headroom for both applications

**Flash usage**:
- Firmware: ~500 KB - 1 MB (including libraries)
- Pattern data: ~10-50 KB (pre-computed patterns)
- ESP32 has 4 MB flash - adequate for complex applications

---

## Debugging and Diagnostics

### Serial Monitor

Both ESP32s continuously output debug information via Serial:

**Thermal ESP32**:
```
[THERMAL] Initializing...
[THERMAL] DS18B20 found: 28:AA:BB:CC:DD:EE:FF
[THERMAL] PID: Kp=50.0, Ki=1.0, Kd=2.5
[THERMAL] Target: 25.0°C, Current: 24.8°C, Output: 45%
[THERMAL] Command received: COOL_TILE:2
[THERMAL] Activating quadrant 2 (180°)
```

**Display ESP32**:
```
[DISPLAY] DMA initialized, refresh rate: 210 Hz
[DISPLAY] Frame buffer allocated: 512x32 pixels
[DISPLAY] Current pattern: VERTICAL_BARS, rotation: 0°
[DISPLAY] Command received: ROTATE:90
[DISPLAY] Pattern rotated to 90°, frame swap complete
```

### Status LEDs

**Thermal ESP32**:
- Solid: System ready, PID active
- Slow blink (1 Hz): Waiting for temperature to stabilize
- Fast blink (5 Hz): Error condition (sensor failure, overheat)
- Off: Not powered or crashed

**Display ESP32**:
- Solid: Display refreshing normally
- Slow blink: Waiting for commands
- Fast blink: DMA error or panel connection issue
- Off: Not powered or crashed

### Common Issues

**Thermal ESP32 not responding**:
- Check USB cable connection
- Verify power LED on ESP32 board
- Try manual reset button
- Inspect H-bridge connections (incorrect wiring can damage ESP32)

**Display ESP32 not refreshing**:
- Verify all 16 HUB75 pins properly connected
- Check power to LED panels (5V must be stable)
- Inspect ribbon cables (loose connection common)
- Try single panel (isolate chain issues)

---

## Upgrades and Extensions

### Adding More Sensors

**Temperature sensors**:
- DS18B20: Up to 127 sensors on single 1-Wire bus
- MLX90640 thermal camera: I²C interface (add Wire library)

**Humidity sensor** (DHT22):
- Monitor arena humidity (affects fly behavior)
- ESP32 has spare GPIO pins

### Data Logging to SD Card

**Add microSD card module**:
- SPI interface (4 pins)
- Log temperature, commands, timestamps
- Useful for post-experiment analysis

### WiFi Telemetry

**ESP32 has built-in WiFi**:
- Stream temperature data to laptop/phone in real-time
- Remote monitoring without Raspberry Pi
- WebSocket-based live charts

**Example use case**: Monitor temperature stability from outside dark room during long experiments.

---

## Bill of Materials (ESP32 System)

| Component | Quantity | Cost (USD) |
|-----------|----------|------------|
| ESP32 DevKit V1 | 2 | $10-20 |
| USB cables (micro-USB) | 2 | $5-10 |
| Jumper wires (M-M, M-F) | 40 pcs | $5-10 |
| Breadboard (for prototyping) | 2 | $5-10 |
| **Total** | | **$25-50** |

**Optional**:
- PCB for permanent installation: $10-20 (per board)
- Enclosures: $5-10 (per ESP32)
- Heatsinks: $2-5 (if needed)

---

## Summary

The dual-ESP32 architecture provides:

✅ **Reliability**: Independent subsystems reduce single points of failure  
✅ **Performance**: PID and DMA run without interfering  
✅ **Modularity**: Easy to develop and debug separately  
✅ **Scalability**: Can add more ESP32s for additional sensors/actuators  
✅ **Cost-effective**: ~$10-15 per controller vs. $100+ for industrial PLCs  

This design leverages the ESP32's dual-core architecture, ample RAM, and rich peripheral set to create a professional research instrument at consumer electronics pricing.

---
