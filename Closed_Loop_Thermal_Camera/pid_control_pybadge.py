"""
PyBadge MLX90640 PID Sender (PIXEL-BASED, FINAL – UART FIXED)
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

palette = displayio.Palette(COLOR_DEPTH)
for i in range(COLOR_DEPTH):
    r = int(map_range(i, 0, 63, 0, 255))
    g = int(map_range(i, 0, 63, 0, 128))
    b = int(map_range(i, 0, 63, 255, 0))
    palette[i] = (r << 16) | (g << 8) | b

bitmap = displayio.Bitmap(WIDTH, HEIGHT, COLOR_DEPTH)
tile = displayio.TileGrid(bitmap, pixel_shader=palette)
img = displayio.Group(scale=SCALE, y=offset_y)
img.append(tile)
root.append(img)

status = label.Label(terminalio.FONT, text="INIT", color=0xFFFF00, x=5, y=5)
root.append(status)

info = label.Label(
    terminalio.FONT,
    text="---",
    color=0xFFFFFF,
    x=5,
    y=display.height - 12
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

# ================= UART =================
def send_temperatures():
    msg = "TEMP:"
    for lbl in ["A", "B", "C", "D"]:
        px, py = peltier_pixels[lbl]
        t = hottest_pixel_in_region(px, py)
        msg += f"{lbl}:{t:.2f},"

    msg = msg.rstrip(",") + "\n"
    uart.write(msg.encode())
    time.sleep(0.01)  # ⭐ REQUIRED for ESP32 framing

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

    tmin, tmax = min(frame), max(frame)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            bitmap[x, y] = int(
                map_range(frame[y * WIDTH + x], tmin, tmax, 0, COLOR_DEPTH - 1)
            )

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
