"""
PyBadge MLX90640 PID Sender
FIXED SCALE + CORRECT ORIENTATION + COLOR BAR + GRID OVERLAY
"""

import time
import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
from simpleio import map_range
import adafruit_mlx90640

# ================= CONSTANTS =================
WIDTH, HEIGHT = 32, 24
PELTIER_W, PELTIER_H = 4, 3
COLOR_DEPTH = 64
SCALE = 4
SEND_INTERVAL = 0.5   # 2 Hz

T_MIN = 20.0
T_MAX = 40.0

GRID_COLOR = 45   # palette index for grid outline

# ================= UART =================
uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=0.01)

# ================= MLX90640 =================
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
frame = [0] * (WIDTH * HEIGHT)

# ================= DISPLAY =================
display = board.DISPLAY
root = displayio.Group()
display.root_group = root

offset_y = (display.height - HEIGHT * SCALE) // 2

# ================= PALETTE =================
palette = displayio.Palette(COLOR_DEPTH)
for i in range(COLOR_DEPTH):
    r = int(map_range(i, 0, 63, 0, 255))
    g = int(map_range(i, 0, 63, 0, 128))
    b = int(map_range(i, 0, 63, 255, 0))
    palette[i] = (r << 16) | (g << 8) | b

# ================= THERMAL IMAGE =================
bitmap = displayio.Bitmap(WIDTH, HEIGHT, COLOR_DEPTH)
tile = displayio.TileGrid(bitmap, pixel_shader=palette)
img = displayio.Group(scale=SCALE, y=offset_y)
img.append(tile)
root.append(img)

# ================= COLOR BAR =================
BAR_WIDTH = 6
BAR_X = display.width - BAR_WIDTH - 2
BAR_Y = offset_y
BAR_HEIGHT = HEIGHT * SCALE

bar_bitmap = displayio.Bitmap(BAR_WIDTH, BAR_HEIGHT, COLOR_DEPTH)
bar_grid = displayio.TileGrid(bar_bitmap, pixel_shader=palette, x=BAR_X, y=BAR_Y)
root.append(bar_grid)

for y in range(BAR_HEIGHT):
    t = map_range(BAR_HEIGHT - 1 - y, 0, BAR_HEIGHT - 1, T_MIN, T_MAX)
    idx = int(map_range(t, T_MIN, T_MAX, 0, COLOR_DEPTH - 1))
    for x in range(BAR_WIDTH):
        bar_bitmap[x, y] = idx

label_hot = label.Label(
    terminalio.FONT, text="40C", color=0xFFFFFF,
    x=BAR_X - 20, y=BAR_Y + 4
)
label_cold = label.Label(
    terminalio.FONT, text="20C", color=0xFFFFFF,
    x=BAR_X - 20, y=BAR_Y + BAR_HEIGHT - 6
)
root.append(label_hot)
root.append(label_cold)

# ================= STATUS =================
status = label.Label(
    terminalio.FONT, text="INIT", color=0xFFFF00,
    x=5, y=5
)
root.append(status)

info = label.Label(
    terminalio.FONT, text="---", color=0xFFFFFF,
    x=5, y=display.height - 12
)
root.append(info)

# ================= COORDINATES =================
peltier_pixels = {}

def load_coordinates():
    try:
        with open("/coordinates.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lbl, px, py = line.split(":")
                peltier_pixels[lbl] = (int(px), int(py))
        return len(peltier_pixels) == 4
    except:
        return False

# ================= HELPERS =================
def hottest_pixel_in_region(px0, py0):
    max_t = -100.0
    for dy in range(PELTIER_H):
        for dx in range(PELTIER_W):
            px = px0 + dx
            py = py0 + dy
            if px < WIDTH and py < HEIGHT:
                t = frame[py * WIDTH + px]
                if t > max_t:
                    max_t = t
    return max_t

# Horizontal flip (DISPLAY ONLY)
def fx(x):
    return WIDTH - 1 - x

def draw_peltier_outline(px0, py0):
    for dx in range(PELTIER_W):
        x = px0 + dx
        if x < WIDTH:
            bitmap[fx(x), py0] = GRID_COLOR
            bitmap[fx(x), min(py0 + PELTIER_H - 1, HEIGHT - 1)] = GRID_COLOR
    for dy in range(PELTIER_H):
        y = py0 + dy
        if y < HEIGHT:
            bitmap[fx(px0), y] = GRID_COLOR
            bitmap[fx(min(px0 + PELTIER_W - 1, WIDTH - 1)), y] = GRID_COLOR

# ================= UART =================
def send_temperatures():
    msg = "TEMP:"
    for lbl in ["A", "B", "C", "D"]:
        px, py = peltier_pixels[lbl]
        t = hottest_pixel_in_region(px, py)
        msg += f"{lbl}:{t:.2f},"
    msg = msg.rstrip(",") + "\n"
    uart.write(msg.encode())
    time.sleep(0.01)

def process_uart():
    if uart.in_waiting:
        try:
            cmd = uart.readline().decode().strip()
            if cmd == "REQUEST_CALIB":
                uart.write(b"CALIB_OK\n")
        except:
            pass

# ================= STARTUP =================
if not load_coordinates():
    status.text = "ERROR"
    while True:
        time.sleep(1)

uart.write(b"PYBADGE_READY\n")
status.text = "READY"
status.color = 0x00FF00

last_send = 0

# ================= MAIN LOOP =================
while True:
    try:
        mlx.getFrame(frame)
    except:
        continue

    # ---- THERMAL IMAGE ----
    for y in range(HEIGHT):
        for x in range(WIDTH):
            t = frame[y * WIDTH + x]
            if t < T_MIN:
                t = T_MIN
            elif t > T_MAX:
                t = T_MAX
            idx = int(map_range(t, T_MIN, T_MAX, 0, COLOR_DEPTH - 1))
            bitmap[fx(x), y] = idx

    # ---- GRID OVERLAY (PERMANENT) ----
    for lbl in peltier_pixels:
        px, py = peltier_pixels[lbl]
        draw_peltier_outline(px, py)

    process_uart()

    now = time.monotonic()
    if now - last_send >= SEND_INTERVAL:
        send_temperatures()
        info.text = (
            f"A:{hottest_pixel_in_region(*peltier_pixels['A']):.1f} "
            f"B:{hottest_pixel_in_region(*peltier_pixels['B']):.1f} "
            f"C:{hottest_pixel_in_region(*peltier_pixels['C']):.1f} "
            f"D:{hottest_pixel_in_region(*peltier_pixels['D']):.1f}"
        )
        last_send = now

    display.refresh()
    time.sleep(0.25)
