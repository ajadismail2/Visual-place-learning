"""
Peltier PID Control System for PyBadge - FINAL VERSION
File: pid_control.py (rename to code.py after calibration)

PURPOSE: Continuous PID control with thermal camera feedback
- Reads coordinates from coordinates.txt
- Sends temperature data to ESP32 via UART at 2 Hz
- Provides visual feedback on PyBadge display
- Responds to ESP32 status commands

PREREQUISITE:
- Run calibration_tool.py first to generate coordinates.txt
- Coordinates file must exist at /coordinates.txt

ESP32 COMMANDS SUPPORTED:
- HEAT, HEAT A/B/C/D
- COOL A/B/C/D
- PATTERN:B-C-D-A (max 8 cycles)
- STOP

TARGETS:
- HEAT: 35°C ±0.5°C
- COOL: 25°C ±0.5°C
"""

import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_mlx90640
from simpleio import map_range

# --- I2C & MLX90640 ---
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

# --- Serial UART to ESP32 ---
# PyBadge TX (A1) → ESP32 RX (GPIO 16)
# PyBadge RX (A0) → ESP32 TX (GPIO 17)
# PyBadge GND → ESP32 GND
uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=0.01)

# --- Display Setup ---
display = board.DISPLAY
main_group = displayio.Group()
display.root_group = main_group

WIDTH, HEIGHT = 32, 24
COLOR_DEPTH = 64
SCALE = 4
DISP_W, DISP_H = display.width, display.height
BAR_W = 12
offset_x = 0
offset_y = (DISP_H - (HEIGHT * SCALE)) // 2

# --- Color Palette ---
palette = displayio.Palette(COLOR_DEPTH)
for i in range(COLOR_DEPTH):
    if i < 10:
        r, g, b = 0, 0, int(map_range(i, 0, 10, 0, 128))
    elif i < 20:
        r, g, b = int(map_range(i, 10, 20, 0, 128)), 0, 255
    elif i < 40:
        r, g, b = 255, int(map_range(i, 20, 40, 0, 128)), 0
    elif i < 56:
        r, g, b = 255, int(map_range(i, 40, 56, 128, 255)), 0
    else:
        r, g, b = 255, 255, int(map_range(i, 56, 63, 0, 255))
    palette[i] = (r << 16) | (g << 8) | b

# --- Thermal Image ---
bitmap = displayio.Bitmap(WIDTH, HEIGHT, COLOR_DEPTH)
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
image_group = displayio.Group(scale=SCALE, x=offset_x, y=offset_y)
image_group.append(tile_grid)
main_group.append(image_group)

# --- Color Bar ---
bar_x = DISP_W - BAR_W
bar_bitmap = displayio.Bitmap(BAR_W, DISP_H, COLOR_DEPTH)
for y in range(DISP_H):
    idx = int(map_range(y, 0, DISP_H - 1, COLOR_DEPTH - 1, 0))
    for x in range(BAR_W):
        bar_bitmap[x, y] = idx
bar_grid = displayio.TileGrid(bar_bitmap, pixel_shader=palette, x=bar_x, y=0)
main_group.append(bar_grid)

# --- Labels ---
max_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=bar_x - 40, y=10)
min_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=bar_x - 40, y=DISP_H - 10)
main_group.append(max_label)
main_group.append(min_label)

status_label = label.Label(terminalio.FONT, text="INIT", color=0xFFFF00, x=5, y=5)
main_group.append(status_label)

# --- Grid Configuration ---
PELTIER_W, PELTIER_H = 4, 3
GRID_X, GRID_Y = 8, 8

frame = [0] * (WIDTH * HEIGHT)
peltier_coords = {}

# === Functions ===
def get_block_temp(frame, gx, gy):
    """Get average temperature of a 4x3 pixel block"""
    temps = []
    for py in range(PELTIER_H):
        for px in range(PELTIER_W):
            x = gx * PELTIER_W + px
            y = gy * PELTIER_H + py
            if x < WIDTH and y < HEIGHT:
                temps.append(frame[y * WIDTH + x])
    return sum(temps) / len(temps) if temps else 0.0

def draw_box(bitmap, gx, gy, color_idx=63):
    """Draw outline around grid cell"""
    x0, y0 = gx * PELTIER_W, gy * PELTIER_H
    for x in range(x0, min(x0 + PELTIER_W, WIDTH)):
        if y0 < HEIGHT: bitmap[x, y0] = color_idx
        if y0 + PELTIER_H - 1 < HEIGHT: bitmap[x, y0 + PELTIER_H - 1] = color_idx
    for y in range(y0, min(y0 + PELTIER_H, HEIGHT)):
        if x0 < WIDTH: bitmap[x0, y] = color_idx
        if x0 + PELTIER_W - 1 < WIDTH: bitmap[x0 + PELTIER_W - 1, y] = color_idx

def load_coordinates():
    """Load coordinates from file"""
    try:
        with open("/coordinates.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) == 3:
                        label = parts[0]
                        gx = int(parts[1])
                        gy = int(parts[2])
                        peltier_coords[label] = (gx, gy)
                        print(f"Loaded {label}: Grid ({gx}, {gy})")
        
        if len(peltier_coords) == 4:
            print("✓ All coordinates loaded successfully")
            return True
        else:
            print(f"✗ Error: Only {len(peltier_coords)}/4 coordinates loaded")
            return False
    except Exception as e:
        print(f"✗ Error loading coordinates: {e}")
        print("Run calibration_tool.py first!")
        return False

def send_calibration():
    """Send coordinate mapping to ESP32"""
    # Format: CALIB:A:2:1,B:5:1,C:5:5,D:2:5\n
    calib_str = "CALIB:"
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            calib_str += f"{label}:{gx}:{gy},"
    calib_str = calib_str.rstrip(',') + "\n"
    
    try:
        uart.write(calib_str.encode())
        print(f"Sent calibration to ESP32")
        return True
    except Exception as e:
        print(f"Error sending calibration: {e}")
        return False

def send_temps():
    """Send temperature readings via UART at 2 Hz"""
    # Format: TEMP:A:35.2,B:36.1,C:35.8,D:36.3\n
    temp_str = "TEMP:"
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            temp = get_block_temp(frame, gx, gy)
            temp_str += f"{label}:{temp:.1f},"
    temp_str = temp_str.rstrip(',') + "\n"
    
    try:
        uart.write(temp_str.encode())
    except:
        pass  # Ignore UART errors (ESP32 may not be ready)

def process_uart_commands():
    """Read and display commands from ESP32"""
    if uart.in_waiting:
        try:
            incoming = uart.readline()
            if incoming:
                cmd = incoming.decode('utf-8').strip()
                # Update status based on command
                if "HEAT_ALL" in cmd or "HEAT ALL" in cmd:
                    status_label.text = "HEAT ALL"
                    status_label.color = 0xFF0000
                elif "HEAT_" in cmd:
                    status_label.text = cmd[:7]  # "HEAT_A", etc.
                    status_label.color = 0xFF8800
                elif "COOL_" in cmd:
                    status_label.text = cmd[:7]  # "COOL_A", etc.
                    status_label.color = 0x00FFFF
                elif "READY" in cmd or "STABLE" in cmd:
                    status_label.text = "STABLE"
                    status_label.color = 0x00FF00
        except:
            pass

# === Main Program ===
print("=" * 40)
print("PELTIER PID CONTROL SYSTEM - FINAL")
print("=" * 40)
print("Targets: HEAT=35°C, COOL=25°C")
print("Update Rate: 2 Hz")

# Load coordinates from file
print("\nLoading coordinates from /coordinates.txt...")
if not load_coordinates():
    status_label.text = "ERROR"
    status_label.color = 0xFF0000
    print("\n✗ FATAL ERROR: Cannot load coordinates")
    print("Please run calibration_tool.py first!")
    print("=" * 40)
    while True:
        time.sleep(1)

# Wait for ESP32
print("\nWaiting for ESP32...")
time.sleep(2)

# Send ready signal
try:
    uart.write(b"PYBADGE_READY\n")
    print("Sent PYBADGE_READY signal")
except:
    print("Warning: Could not send ready signal")

# Send calibration data
time.sleep(1)
if send_calibration():
    print("✓ Calibration data sent to ESP32")
else:
    print("✗ Warning: Could not send calibration")

status_label.text = "READY"
status_label.color = 0x00FF00

print("\n✓ System ready - starting PID control loop")
print("Sending temperatures at 2 Hz...")
print("=" * 40)

# === Main Control Loop ===
last_send_time = 0
frame_count = 0

while True:
    # Capture thermal frame
    try:
        mlx.getFrame(frame)
    except:
        time.sleep(0.1)
        continue
    
    t_min, t_max = min(frame), max(frame)
    
    # Update thermal image display
    for y in range(HEIGHT):
        for x in range(WIDTH):
            val = frame[y * WIDTH + x]
            idx = int(map_range(val, t_min, t_max, 0, COLOR_DEPTH - 1))
            bitmap[x, y] = idx
    
    max_label.text = f"{t_max:.1f}C"
    min_label.text = f"{t_min:.1f}C"
    
    # Draw boxes around Peltier zones with color coding
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            temp = get_block_temp(frame, gx, gy)
            
            # Color based on temperature
            if 24.5 <= temp <= 25.5:  # Cooling target (25°C ±0.5)
                color = 10  # Blue
            elif 34.5 <= temp <= 35.5:  # Heating target (35°C ±0.5)
                color = 50  # Yellow
            else:
                color = 63  # White (out of range)
            
            draw_box(bitmap, gx, gy, color)
    
    # Process incoming commands from ESP32
    process_uart_commands()
    
    # Send temperatures every 0.5 seconds (2 Hz)
    current_time = time.monotonic()
    if current_time - last_send_time >= 0.5:
        send_temps()
        last_send_time = current_time
        frame_count += 1
        
        # Print to console for debugging (every 4th frame = every 2 seconds)
        if frame_count % 4 == 0:
            temps = []
            for l in ['A', 'B', 'C', 'D']:
                if l in peltier_coords:
                    temps.append(get_block_temp(frame, *peltier_coords[l]))
                else:
                    temps.append(0.0)
            print(f"A:{temps[0]:.1f} B:{temps[1]:.1f} C:{temps[2]:.1f} D:{temps[3]:.1f}")
    
    display.refresh()
    time.sleep(0.5)  # 2 Hz frame rate