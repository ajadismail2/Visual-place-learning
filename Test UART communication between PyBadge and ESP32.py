"""
UART Temperature Test for PyBadge
File: test_uart.py (upload as code.py)

PURPOSE: Test UART communication between PyBadge and ESP32
- Reads coordinates from coordinates.txt
- Sends temperature data every 0.5 seconds
- Simple test to verify data transfer is working

PREREQUISITE:
- Run calibration_tool.py first to create coordinates.txt
- UART must be connected: TX→RX, RX→TX, GND→GND

WIRING:
- PyBadge TX (A1) → ESP32 RX (GPIO 16)
- PyBadge RX (A0) → ESP32 TX (GPIO 17)
- PyBadge GND → ESP32 GND
"""

import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_mlx90640
from simpleio import map_range

print("=" * 50)
print("UART TEMPERATURE TEST - PyBadge Side")
print("=" * 50)

# --- I2C & MLX90640 ---
print("Initializing MLX90640 thermal camera...")
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
print("✓ Thermal camera ready")

# --- Serial UART to ESP32 ---
print("Initializing UART...")
uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=0.01)
print("✓ UART ready (115200 baud)")

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

status_label = label.Label(terminalio.FONT, text="TEST", color=0x00FF00, x=5, y=5)
main_group.append(status_label)

temp_display_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=5, y=DISP_H - 15, scale=1)
main_group.append(temp_display_label)

# --- Grid Configuration ---
PELTIER_W, PELTIER_H = 4, 3
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
    print("\nLoading coordinates from /coordinates.txt...")
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
                        print(f"  {label}: Grid ({gx}, {gy})")
        
        if len(peltier_coords) == 4:
            print("✓ All 4 coordinates loaded")
            return True
        else:
            print(f"✗ Error: Only {len(peltier_coords)}/4 coordinates found")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  Run calibration_tool.py first!")
        return False

# === Load Coordinates ===
if not load_coordinates():
    status_label.text = "ERROR"
    status_label.color = 0xFF0000
    print("\n" + "=" * 50)
    print("FATAL ERROR: Cannot load coordinates")
    print("Please run calibration_tool.py first!")
    print("=" * 50)
    while True:
        time.sleep(1)

# === Send Initial Handshake ===
print("\nSending handshake to ESP32...")
time.sleep(1)
try:
    uart.write(b"PYBADGE_TEST_READY\n")
    print("✓ Handshake sent")
except Exception as e:
    print(f"✗ UART error: {e}")

print("\n" + "=" * 50)
print("STARTING TEMPERATURE TRANSMISSION")
print("=" * 50)
print("Format: TEMP:A:XX.X,B:XX.X,C:XX.X,D:XX.X")
print("Rate: 2 Hz (every 0.5 seconds)")
print("\nCheck ESP32 Serial Monitor to see received data")
print("=" * 50)

# === Main Loop ===
last_send_time = 0
send_count = 0

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
    
    # Draw boxes around Peltier zones
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            draw_box(bitmap, gx, gy, 50)  # Yellow boxes
    
    # Get current temperatures
    temps = {}
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            temps[label] = get_block_temp(frame, gx, gy)
    
    # Send temperatures every 0.5 seconds (2 Hz)
    current_time = time.monotonic()
    if current_time - last_send_time >= 0.5:
        # Format: TEMP:A:35.2,B:36.1,C:35.8,D:36.3\n
        temp_str = "TEMP:"
        for label in ['A', 'B', 'C', 'D']:
            if label in temps:
                temp_str += f"{label}:{temps[label]:.1f},"
        temp_str = temp_str.rstrip(',') + "\n"
        
        # Send via UART
        try:
            uart.write(temp_str.encode())
            send_count += 1
            
            # Print to PyBadge serial (USB)
            print(f"[{send_count:04d}] Sent: {temp_str.strip()}")
            
            # Update display
            temp_display_label.text = f"Sent:{send_count}"
            
        except Exception as e:
            print(f"UART Error: {e}")
            status_label.text = "UART ERR"
            status_label.color = 0xFF0000
        
        last_send_time = current_time
    
    display.refresh()
    time.sleep(0.5)
