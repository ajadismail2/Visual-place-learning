"""
Peltier Calibration Tool for PyBadge - FINAL VERSION
File: calibration_tool.py

PURPOSE: One-time calibration to find A, B, C, D coordinates
- Detects zones >33°C
- Press ANY button to lock hottest zone
- Saves coordinates to coordinates.txt
- Run this ONCE, then use pid_control.py for operations

WORKFLOW:
1. Heat Peltier A above 33°C
2. Press any button → locks as A
3. Wait for A to cool
4. Heat Peltier B above 33°C
5. Press any button → locks as B
6. Repeat for C and D
7. Coordinates saved to CIRCUITPY/coordinates.txt

AFTER CALIBRATION:
- Upload pid_control.py as code.py
- System will read coordinates automatically
"""

import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_mlx90640
from simpleio import map_range
from digitalio import DigitalInOut, Direction, Pull

# --- I2C & MLX90640 ---
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

# --- All Buttons (any button works) ---
# PyBadge buttons: D5 (A), D6 (B), D2 (Start), D3 (Select)
buttons = []
button_pins = [board.D5, board.D6, board.D2, board.D3]
button_names = ["A", "B", "Start", "Select"]

for pin in button_pins:
    btn = DigitalInOut(pin)
    btn.direction = Direction.INPUT
    btn.pull = Pull.UP
    buttons.append(btn)

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

instruction_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=5, y=DISP_H - 15, scale=1)
main_group.append(instruction_label)

# --- Grid Configuration ---
PELTIER_W, PELTIER_H = 4, 3
GRID_X, GRID_Y = 8, 8
THRESHOLD_TEMP = 33.0

frame = [0] * (WIDTH * HEIGHT)
peltier_coords = {}
calibration_sequence = ['A', 'B', 'C', 'D']
current_index = 0

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

def find_hottest_above_threshold(frame, threshold):
    """Find hottest grid zone above threshold temperature"""
    max_temp = threshold
    hot_gx, hot_gy = -1, -1
    
    for gy in range(GRID_Y):
        for gx in range(GRID_X):
            temp = get_block_temp(frame, gx, gy)
            if temp > max_temp:
                max_temp = temp
                hot_gx, hot_gy = gx, gy
    
    return hot_gx, hot_gy, max_temp

def any_button_pressed():
    """Check if any button is pressed and return which one"""
    for i, btn in enumerate(buttons):
        if not btn.value:  # Active low
            return True, button_names[i]
    return False, None

def save_coordinates():
    """Save coordinates to file"""
    try:
        with open("/coordinates.txt", "w") as f:
            f.write("# Peltier Plate Coordinates\n")
            f.write("# Format: LABEL:GRID_X:GRID_Y\n")
            for label in ['A', 'B', 'C', 'D']:
                if label in peltier_coords:
                    gx, gy = peltier_coords[label]
                    f.write(f"{label}:{gx}:{gy}\n")
        print("Coordinates saved to /coordinates.txt")
        return True
    except Exception as e:
        print(f"Error saving coordinates: {e}")
        return False

# === Main Calibration Loop ===
print("=" * 40)
print("PELTIER CALIBRATION TOOL - FINAL")
print("=" * 40)
print("Instructions:")
print("1. Heat each Peltier above 33°C")
print("2. Press ANY button to lock position")
print("   (A, B, Start, or Select button)")
print("3. Let it cool before heating next one")
print("4. Coordinates saved to coordinates.txt")
print("=" * 40)

status_label.text = "CALIB"
status_label.color = 0xFFFF00

last_button_time = 0
calibration_complete = False

while not calibration_complete:
    # Get current label
    if current_index >= len(calibration_sequence):
        calibration_complete = True
        break
    
    current_label = calibration_sequence[current_index]
    instruction_label.text = f"Heat {current_label}>33C, press btn"
    
    # Capture frame
    try:
        mlx.getFrame(frame)
    except:
        time.sleep(0.1)
        continue
    
    t_min, t_max = min(frame), max(frame)
    
    # Update thermal image
    for y in range(HEIGHT):
        for x in range(WIDTH):
            val = frame[y * WIDTH + x]
            idx = int(map_range(val, t_min, t_max, 0, COLOR_DEPTH - 1))
            bitmap[x, y] = idx
    
    max_label.text = f"{t_max:.1f}C"
    min_label.text = f"{t_min:.1f}C"
    
    # Find hottest zone above threshold
    hot_gx, hot_gy, hot_temp = find_hottest_above_threshold(frame, THRESHOLD_TEMP)
    
    # Highlight zones above threshold
    for gy in range(GRID_Y):
        for gx in range(GRID_X):
            temp = get_block_temp(frame, gx, gy)
            if temp > THRESHOLD_TEMP:
                if gx == hot_gx and gy == hot_gy:
                    draw_box(bitmap, gx, gy, 63)  # White = hottest
                else:
                    draw_box(bitmap, gx, gy, 20)  # Yellow = above threshold
    
    # Draw already locked positions
    for lbl, (gx, gy) in peltier_coords.items():
        draw_box(bitmap, gx, gy, 40)  # Green = locked
    
    # Button press detection with debouncing
    current_time = time.monotonic()
    
    btn_pressed, btn_name = any_button_pressed()
    if btn_pressed and (current_time - last_button_time > 0.5):
        if hot_gx >= 0 and hot_gy >= 0:
            # Lock position
            peltier_coords[current_label] = (hot_gx, hot_gy)
            print(f"\n✓ {current_label} locked at Grid ({hot_gx}, {hot_gy}) - {hot_temp:.1f}°C")
            print(f"  (Button {btn_name} pressed)")
            
            # Move to next
            current_index += 1
            
            if current_index < len(calibration_sequence):
                next_label = calibration_sequence[current_index]
                print(f"→ Let {current_label} cool, then heat {next_label}")
            
            last_button_time = current_time
        else:
            print(f"✗ No zone above {THRESHOLD_TEMP}°C detected!")
            last_button_time = current_time
    
    display.refresh()
    time.sleep(0.3)

# === Calibration Complete ===
status_label.text = "DONE!"
status_label.color = 0x00FF00
instruction_label.text = "See Serial for coords"

print("\n" + "=" * 40)
print("CALIBRATION COMPLETE!")
print("=" * 40)
print("\nCoordinates:")
for label in ['A', 'B', 'C', 'D']:
    if label in peltier_coords:
        gx, gy = peltier_coords[label]
        print(f"  Peltier {label}: Grid ({gx}, {gy})")

# Save to file
if save_coordinates():
    print("\n✓ Saved to /coordinates.txt")
    print("\nNEXT STEPS:")
    print("1. Remove this calibration_tool.py")
    print("2. Upload pid_control.py as code.py")
    print("3. Upload esp32_command_pid.ino to ESP32")
    print("4. System will read coordinates automatically")
    print("\nREADY FOR OPERATIONS!")
else:
    print("\n✗ Error saving file")
    print("Copy these coordinates manually:")
    for label in ['A', 'B', 'C', 'D']:
        if label in peltier_coords:
            gx, gy = peltier_coords[label]
            print(f"{label}:{gx}:{gy}")

print("=" * 40)

# Display final result
while True:
    # Show all locked positions on thermal image
    try:
        mlx.getFrame(frame)
    except:
        time.sleep(0.1)
        continue
    
    t_min, t_max = min(frame), max(frame)
    
    for y in range(HEIGHT):
        for x in range(WIDTH):
            val = frame[y * WIDTH + x]
            idx = int(map_range(val, t_min, t_max, 0, COLOR_DEPTH - 1))
            bitmap[x, y] = idx
    
    max_label.text = f"{t_max:.1f}C"
    min_label.text = f"{t_min:.1f}C"
    
    # Draw all calibrated positions
    for lbl, (gx, gy) in peltier_coords.items():
        draw_box(bitmap, gx, gy, 40)  # Green boxes
    
    display.refresh()
    time.sleep(1)
