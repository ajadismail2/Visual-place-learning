import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_mlx90640
from simpleio import map_range

# ==============================
# MLX90640 Setup
# ==============================
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

# ==============================
# Display Setup
# ==============================
display = board.DISPLAY
root = displayio.Group()
display.root_group = root

WIDTH, HEIGHT = 32, 24
SCALE = 4
COLOR_DEPTH = 64
BAR_W = 12

offset_y = (display.height - HEIGHT * SCALE) // 2

# ==============================
# Color Palette
# ==============================
palette = displayio.Palette(COLOR_DEPTH)
for i in range(COLOR_DEPTH):
    r = int(map_range(i, 0, 63, 0, 255))
    g = int(map_range(i, 0, 63, 0, 128))
    b = int(map_range(i, 0, 63, 255, 0))
    palette[i] = (r << 16) | (g << 8) | b

# ==============================
# Thermal Image
# ==============================
bitmap = displayio.Bitmap(WIDTH, HEIGHT, COLOR_DEPTH)
grid = displayio.TileGrid(bitmap, pixel_shader=palette)
img = displayio.Group(scale=SCALE, y=offset_y)
img.append(grid)
root.append(img)

# ==============================
# Labels
# ==============================
hot_label = label.Label(
    terminalio.FONT,
    text="NO HOTSPOT ≥35C",
    color=0x00FF00,
    x=5,
    y=display.height - 12
)
root.append(hot_label)

max_label = label.Label(
    terminalio.FONT,
    text="",
    color=0xFFFFFF,
    x=display.width - 50,
    y=10
)
root.append(max_label)

# ==============================
# Config
# ==============================
THRESHOLD = 35.0
PELTIER_W = 4
PELTIER_H = 3

frame = [0] * (WIDTH * HEIGHT)

# ==============================
# Drawing helpers
# ==============================
def draw_cross(bitmap, px, py, color=63):
    for dx in (-1, 0, 1):
        if 0 <= px + dx < WIDTH:
            bitmap[px + dx, py] = color
    for dy in (-1, 0, 1):
        if 0 <= py + dy < HEIGHT:
            bitmap[px, py + dy] = color

def draw_block(bitmap, gx, gy, color=40):
    x0 = gx * PELTIER_W
    y0 = gy * PELTIER_H
    for x in range(x0, min(x0 + PELTIER_W, WIDTH)):
        bitmap[x, y0] = color
        bitmap[x, min(y0 + PELTIER_H - 1, HEIGHT - 1)] = color
    for y in range(y0, min(y0 + PELTIER_H, HEIGHT)):
        bitmap[x0, y] = color
        bitmap[min(x0 + PELTIER_W - 1, WIDTH - 1), y] = color

# ==============================
# Main Loop
# ==============================
while True:
    try:
        mlx.getFrame(frame)
    except:
        continue

    # Find hottest pixel
    max_temp = -100.0
    max_index = 0
    for i, t in enumerate(frame):
        if t > max_temp:
            max_temp = t
            max_index = i

    px = max_index % WIDTH
    py = max_index // WIDTH

    gx = px // PELTIER_W
    gy = py // PELTIER_H

    # Render thermal image (visual only)
    t_min = min(frame)
    t_max = max(frame)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = int(map_range(frame[y * WIDTH + x], t_min, t_max, 0, COLOR_DEPTH - 1))
            bitmap[x, y] = idx

    max_label.text = f"{max_temp:.1f}C"

    if max_temp >= THRESHOLD:
        draw_cross(bitmap, px, py, 63)
        draw_block(bitmap, gx, gy, 45)

        hot_label.text = (
            f"HOT px({px},{py})  "
            f"grid({gx},{gy})  "
            f"{max_temp:.1f}C"
        )
        hot_label.color = 0xFF0000
    else:
        hot_label.text = "NO HOTSPOT ≥35C"
        hot_label.color = 0x00FF00

    display.refresh()
    time.sleep(0.2)
