import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#e94560"
TEXT = "#eaeaea"
MUTED = "#8892a0"
SUCCESS = "#4caf6e"

STEPS = [
    "1. Load Video",
    "2. Define Arena",
    "3. Rotate Quadrants",
    "4. Add 4 Grids",
    "5. Set Scale",
    "6. Export"
]

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# ── GRID VALIDATION ─────────────────────────
def validate_grids(grids):
    issues = []
    for g in grids:
        pts = g["corners_px"]

        if len(pts) != 4:
            issues.append(f"{g['name']}: not 4 points")
            continue

        # width/height
        w = dist(pts[0], pts[1])
        h = dist(pts[1], pts[2])

        if w < 10 or h < 10:
            issues.append(f"{g['name']}: too small")

        # crossing check
        diag1 = dist(pts[0], pts[2])
        diag2 = dist(pts[1], pts[3])

        if diag1 < diag2 * 0.5:
            issues.append(f"{g['name']}: bad ordering")

    return issues


class ArenaCalibrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arena Calibrator – Pro UI")
        self.geometry("1300x800")
        self.configure(bg=BG)

        self.cap = None
        self.raw_frame = None

        self.arena_center = None
        self.arena_radius = None
        self.drag_start = None

        self.quadrant_rotation = 0

        self.current_grid = []
        self.peltier_grids = []

        self.scale_pt1 = None
        self.scale_pt2 = None
        self.px_per_cm = None

        self.mode = "none"

        self._build_ui()

    # ── UI ─────────────────────────────
    def _build_ui(self):
        self.sidebar = tk.Frame(self, bg=PANEL, width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Arena Tool",
                 bg=PANEL, fg=ACCENT, font=("Helvetica", 14, "bold")
        ).pack(pady=10)

        self.step_labels = []
        for s in STEPS:
            lbl = tk.Label(self.sidebar, text=s,
                           bg=PANEL, fg=MUTED, anchor="w")
            lbl.pack(fill=tk.X, padx=15, pady=2)
            self.step_labels.append(lbl)

        ttk.Separator(self.sidebar).pack(fill=tk.X, pady=10)

        self.instr = tk.StringVar(value="Load a video to begin.")
        tk.Label(self.sidebar, textvariable=self.instr,
                 bg=PANEL, fg=TEXT, wraplength=220,
                 justify="left").pack(padx=10)

        ttk.Separator(self.sidebar).pack(fill=tk.X, pady=10)

        self.info = tk.StringVar(value="")
        tk.Label(self.sidebar, textvariable=self.info,
                 bg=PANEL, fg=SUCCESS, justify="left").pack(padx=10)

        # MAIN
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        bar = tk.Frame(self.main, bg=BG)
        bar.pack(fill=tk.X)

        def btn(txt, cmd):
            tk.Button(bar, text=txt, command=cmd,
                      bg=ACCENT, fg=TEXT).pack(side=tk.LEFT, padx=4, pady=4)

        btn("Load", self.load_video)
        btn("Arena", self.mode_circle)
        btn("Rotate", self.rotate_quads)
        btn("Grid", self.mode_grid)
        btn("Scale", self.mode_scale)
        btn("Export", self.export)

        # NEW RESET BUTTONS
        btn("Reset Arena", self.reset_arena)
        btn("Undo Grid", self.undo_grid)
        btn("Clear Grids", self.clear_grids)
        btn("Reset Scale", self.reset_scale)
        btn("Reset Rot", self.reset_rotation)

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)

    # ── UI HELPERS ─────────────────────
    def set_step(self, i):
        for idx, lbl in enumerate(self.step_labels):
            lbl.config(fg=SUCCESS if idx <= i else MUTED)

    def set_instr(self, text):
        self.instr.set(text)

    def update_info(self):
        lines = []
        if self.arena_center:
            lines.append(f"Arena: {self.arena_center}")
        lines.append(f"Grids: {len(self.peltier_grids)}/4")
        if self.px_per_cm:
            lines.append(f"Scale: {self.px_per_cm:.2f}")
        self.info.set("\n".join(lines))

    # ── RESET FUNCTIONS ─────────────────
    def reset_arena(self):
        self.arena_center = None
        self.arena_radius = None
        self.render()

    def undo_grid(self):
        if self.peltier_grids:
            self.peltier_grids.pop()
            self.render()

    def clear_grids(self):
        self.peltier_grids = []
        self.current_grid = []
        self.render()

    def reset_scale(self):
        self.px_per_cm = None
        self.scale_pt1 = None
        self.scale_pt2 = None

    def reset_rotation(self):
        self.quadrant_rotation = 0
        self.render()

    # ── VIDEO ─────────────────────────
    def load_video(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.cap = cv2.VideoCapture(path)
        ret, frame = self.cap.read()
        if ret:
            self.raw_frame = frame
            self.render()

        self.set_step(0)
        self.set_instr("Drag from center → edge")

    # ── MODES ─────────────────────────
    def mode_circle(self):
        self.mode = "circle"

    def rotate_quads(self):
        self.quadrant_rotation = (self.quadrant_rotation + 90) % 360
        self.render()

    def mode_grid(self):
        if len(self.peltier_grids) >= 4:
            messagebox.showinfo("Done", "4 grids done")
            return

        self.mode = "grid"
        self.current_grid = []
        self.set_instr("Click Top-left")

    def mode_scale(self):
        self.mode = "scale"
        self.set_instr("Click 2 points")

    # ── EVENTS ────────────────────────
    def click(self, e):
        x, y = e.x, e.y

        if self.mode == "circle":
            self.drag_start = (x, y)

        elif self.mode == "grid":
            labels = ["Top-left","Top-right","Bottom-right","Bottom-left"]
            self.current_grid.append((x, y))

            if len(self.current_grid) < 4:
                self.set_instr(f"Click {labels[len(self.current_grid)]}")
            else:
                self.peltier_grids.append({
                    "name": f"grid_{len(self.peltier_grids)+1}",
                    "corners_px": self.current_grid.copy()
                })
                self.current_grid = []
                self.mode = "none"
                self.set_instr("Grid saved ✓")

        elif self.mode == "scale":
            if not self.scale_pt1:
                self.scale_pt1 = (x,y)
            else:
                self.scale_pt2 = (x,y)
                self.ask_scale()

        self.render()
        self.update_info()

    def drag(self, e):
        if self.mode == "circle" and self.drag_start:
            cx, cy = self.drag_start
            self.arena_center = (cx, cy)
            self.arena_radius = dist((cx, cy), (e.x, e.y))
            self.render()

    def release(self, e):
        self.drag_start = None
        self.set_step(1)

    # ── SCALE ─────────────────────────
    def ask_scale(self):
        d = dist(self.scale_pt1, self.scale_pt2)

        win = tk.Toplevel(self)
        tk.Label(win, text=f"{d:.1f} px").pack()

        entry = tk.Entry(win)
        entry.insert(0, "20.32")
        entry.pack()

        def ok():
            self.px_per_cm = d / float(entry.get())
            win.destroy()

        tk.Button(win, text="OK", command=ok).pack()

    # ── RENDER ────────────────────────
    def render(self):
        if self.raw_frame is None:
            return

        frame = self.raw_frame.copy()

        if self.arena_center and self.arena_radius:
            cx, cy = map(int, self.arena_center)
            r = int(self.arena_radius)

            cv2.circle(frame, (cx, cy), r, (0,255,0), 2)

            for i in range(4):
                a = np.deg2rad(self.quadrant_rotation + i*90)
                x = int(cx + r*np.cos(a))
                y = int(cy + r*np.sin(a))
                cv2.line(frame, (cx, cy), (x, y), (255,255,255), 1)

                mid = a + np.pi/4
                tx = int(cx + r*0.6*np.cos(mid))
                ty = int(cy + r*0.6*np.sin(mid))
                cv2.putText(frame, f"Q{i+1}", (tx-10, ty+5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255,255,255), 2)

        for g in self.peltier_grids:
            pts = np.array(g["corners_px"], np.int32)
            cv2.polylines(frame, [pts], True, (255,0,0), 2)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    # ── EXPORT ────────────────────────
    def export(self):
        issues = validate_grids(self.peltier_grids)

        if issues:
            messagebox.showwarning("Grid Issues", "\n".join(issues))
            return

        if len(self.peltier_grids) != 4:
            messagebox.showerror("Error", "Need 4 grids")
            return

        config = {
            "arena": {
                "center_px": self.arena_center,
                "radius_px": self.arena_radius,
                "quadrant_rotation_deg": self.quadrant_rotation
            },
            "peltier_grids": self.peltier_grids,
            "calibration": {
                "px_per_cm": self.px_per_cm
            }
        }

        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return

        with open(path, "w") as f:
            json.dump(config, f, indent=2)

        messagebox.showinfo("Saved", "Config saved!")

if __name__ == "__main__":
    app = ArenaCalibrator()
    app.mainloop()