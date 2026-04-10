"""
Arena Calibrator  –  v2.0
Scientific thermal-arena annotation tool
"""

import json, math, sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

# ── PALETTE ────────────────────────────────────────────────────────────────────
BG        = "#0d1117"
PANEL     = "#161b22"
PANEL2    = "#1c2230"
BORDER    = "#30363d"
ACCENT    = "#f0883e"        # amber — instrument-orange
ACCENT2   = "#388bfd"        # electric blue for secondary actions
SUCCESS   = "#3fb950"
WARN      = "#d29922"
DANGER    = "#f85149"
TEXT      = "#e6edf3"
MUTED     = "#6e7681"
DIM       = "#3d444d"

GRID_COLORS = ["#f0883e", "#388bfd", "#3fb950", "#bc8cff"]   # one per Peltier
GRID_NAMES  = ["Peltier A", "Peltier B", "Peltier C", "Peltier D"]

CORNER_LABELS = ["Top-left", "Top-right", "Bottom-right", "Bottom-left"]

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def validate_grids(grids):
    issues = []
    for g in grids:
        pts = g["corners_px"]
        if len(pts) != 4:
            issues.append(f"{g['name']}: not 4 points"); continue
        w = dist(pts[0], pts[1])
        h = dist(pts[1], pts[2])
        if w < 10 or h < 10:
            issues.append(f"{g['name']}: grid too small")
        d1 = dist(pts[0], pts[2]); d2 = dist(pts[1], pts[3])
        if d1 < d2 * 0.5:
            issues.append(f"{g['name']}: corner ordering looks wrong")
    return issues


# ── STYLED WIDGETS ─────────────────────────────────────────────────────────────
def styled_button(parent, text, cmd, color=ACCENT, width=None):
    kw = dict(text=text, command=cmd, bg=color, fg=BG,
              relief="flat", bd=0, padx=10, pady=5,
              font=("Courier", 9, "bold"), cursor="hand2",
              activebackground=TEXT, activeforeground=BG)
    if width: kw["width"] = width
    return tk.Button(parent, **kw)

def section_label(parent, text):
    f = tk.Frame(parent, bg=PANEL)
    tk.Label(f, text=text.upper(), bg=PANEL, fg=MUTED,
             font=("Courier", 8, "bold")).pack(side=tk.LEFT, padx=12, pady=(10,2))
    tk.Frame(f, bg=BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10), pady=(10,2))
    f.pack(fill=tk.X)

def separator(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=10, pady=6)


# ── MAIN APP ───────────────────────────────────────────────────────────────────
class ArenaCalibrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arena Calibrator  ·  v2.0")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self.option_add("*Font", "Courier 10")

        # ── state
        self.cap          = None
        self.raw_frame    = None
        self.disp_frame   = None       # scaled for canvas
        self.scale_ratio  = 1.0        # raw→display

        self.arena_center  = None
        self.arena_radius  = None
        self.drag_start    = None

        self.quadrant_rotation = 0

        self.current_grid  = []
        self.peltier_grids = []

        self.scale_pt1 = None
        self.scale_pt2 = None
        self.px_per_cm = None

        self.mode          = "none"
        self.hover_pos     = (0, 0)

        self._build_ui()
        self._bind_keys()

    # ── BUILD UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── left sidebar
        self.sidebar = tk.Frame(self, bg=PANEL, width=270)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── right: canvas + status bar
        right = tk.Frame(self, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_toolbar(right)

        self.canvas = tk.Canvas(right, bg="#050810", highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._build_statusbar(right)

        self.canvas.bind("<Button-1>",        self.click)
        self.canvas.bind("<B1-Motion>",       self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Motion>",          self.mouse_move)
        self.canvas.bind("<Configure>",       lambda e: self._fit_canvas())

    def _build_sidebar(self):
        # ── Logo / header
        hdr = tk.Frame(self.sidebar, bg=ACCENT, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="▣  Arena Calibrator", bg=ACCENT, fg=BG,
                 font=("Courier", 12, "bold")).pack(expand=True)

        # ── Workflow steps
        section_label(self.sidebar, "Workflow")
        steps_frame = tk.Frame(self.sidebar, bg=PANEL)
        steps_frame.pack(fill=tk.X, padx=10)

        STEPS = [
            ("1", "Load Video",      self.load_video),
            ("2", "Define Arena",    self.mode_circle),
            ("3", "Rotate Quadrants",self.rotate_quads),
            ("4", "Add Grids",       self.mode_grid),
            ("5", "Set Scale",       self.mode_scale),
            ("6", "Export JSON",     self.export),
        ]
        self.step_frames = []
        for num, label, cmd in STEPS:
            row = tk.Frame(steps_frame, bg=PANEL, pady=2)
            row.pack(fill=tk.X)
            badge = tk.Label(row, text=num, bg=DIM, fg=MUTED,
                             width=2, font=("Courier", 9, "bold"))
            badge.pack(side=tk.LEFT, padx=(0,8))
            lbl = tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                           anchor="w", font=("Courier", 10))
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            btn = styled_button(row, "▶", cmd, color=DIM)
            btn.pack(side=tk.RIGHT)
            self.step_frames.append((badge, lbl, btn))

        # ── Instruction box
        separator(self.sidebar)
        section_label(self.sidebar, "Instructions")
        self.instr_var = tk.StringVar(value="Load a video to begin.\n\nKeyboard:\n  L – Load\n  A – Arena\n  G – Grid\n  S – Scale\n  R – Rotate\n  E – Export\n  Z – Undo Grid")
        self.instr_box = tk.Label(self.sidebar, textvariable=self.instr_var,
                                  bg=PANEL2, fg=TEXT, justify="left",
                                  wraplength=230, padx=10, pady=8,
                                  font=("Courier", 9))
        self.instr_box.pack(fill=tk.X, padx=10)

        # ── Grid slots
        separator(self.sidebar)
        section_label(self.sidebar, "Peltier Grids")
        self.grid_slots_frame = tk.Frame(self.sidebar, bg=PANEL)
        self.grid_slots_frame.pack(fill=tk.X, padx=10)
        self._refresh_grid_slots()

        # ── Calibration info
        separator(self.sidebar)
        section_label(self.sidebar, "Calibration State")
        self.info_frame = tk.Frame(self.sidebar, bg=PANEL2, padx=10, pady=8)
        self.info_frame.pack(fill=tk.X, padx=10)
        self.arena_info  = tk.StringVar(value="Arena:  —")
        self.scale_info  = tk.StringVar(value="Scale:  —")
        self.rot_info    = tk.StringVar(value="Rotation:  0°")
        for v in [self.arena_info, self.scale_info, self.rot_info]:
            tk.Label(self.info_frame, textvariable=v, bg=PANEL2, fg=SUCCESS,
                     anchor="w", font=("Courier", 9)).pack(fill=tk.X)

        # ── Reset group
        separator(self.sidebar)
        section_label(self.sidebar, "Reset")
        reset_frame = tk.Frame(self.sidebar, bg=PANEL)
        reset_frame.pack(fill=tk.X, padx=10, pady=4)
        resets = [
            ("Reset Arena",   self.reset_arena,    DANGER),
            ("Undo Last Grid", self.undo_grid,      WARN),
            ("Clear All Grids",self.clear_grids,    DANGER),
            ("Reset Scale",   self.reset_scale,     WARN),
            ("Reset Rotation",self.reset_rotation,  WARN),
        ]
        for txt, cmd, col in resets:
            styled_button(reset_frame, txt, cmd, color=col, width=22).pack(
                pady=2, anchor="w")

        # ── spacer + version
        tk.Frame(self.sidebar, bg=PANEL).pack(fill=tk.BOTH, expand=True)
        tk.Label(self.sidebar, text="Thermal Arena · Ashoka Univ.",
                 bg=PANEL, fg=DIM, font=("Courier", 8)).pack(pady=6)

    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg=PANEL2, height=40)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        tools = [
            ("📂 Load [L]",    self.load_video,  ACCENT2),
            ("⬤ Arena [A]",   self.mode_circle,  ACCENT),
            ("↺ Rotate [R]",  self.rotate_quads, ACCENT),
            ("⊞ Grid [G]",    self.mode_grid,    ACCENT),
            ("⇔ Scale [S]",   self.mode_scale,   ACCENT),
            ("💾 Export [E]",  self.export,       SUCCESS),
        ]
        for txt, cmd, col in tools:
            styled_button(bar, txt, cmd, color=col).pack(
                side=tk.LEFT, padx=3, pady=4)

        # mode indicator
        self.mode_var = tk.StringVar(value="MODE: IDLE")
        tk.Label(bar, textvariable=self.mode_var, bg=PANEL2, fg=ACCENT,
                 font=("Courier", 10, "bold")).pack(side=tk.RIGHT, padx=15)

    def _build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=PANEL, height=26)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        self.coord_var  = tk.StringVar(value="x:—  y:—")
        self.msg_var    = tk.StringVar(value="Ready")
        self.grids_var  = tk.StringVar(value="Grids: 0/4")

        for v, side, fg in [
            (self.msg_var,   tk.LEFT,  TEXT),
            (self.grids_var, tk.RIGHT, SUCCESS),
            (self.coord_var, tk.RIGHT, MUTED),
        ]:
            tk.Label(bar, textvariable=v, bg=PANEL, fg=fg,
                     font=("Courier", 9), padx=10).pack(side=side)

    def _bind_keys(self):
        self.bind("l", lambda e: self.load_video())
        self.bind("a", lambda e: self.mode_circle())
        self.bind("r", lambda e: self.rotate_quads())
        self.bind("g", lambda e: self.mode_grid())
        self.bind("s", lambda e: self.mode_scale())
        self.bind("e", lambda e: self.export())
        self.bind("z", lambda e: self.undo_grid())
        self.bind("<Escape>", lambda e: self._cancel_mode())

    # ── GRID SLOTS ─────────────────────────────────────────────────────────────
    def _refresh_grid_slots(self):
        for w in self.grid_slots_frame.winfo_children():
            w.destroy()
        for i in range(4):
            col  = GRID_COLORS[i]
            name = GRID_NAMES[i]
            done = i < len(self.peltier_grids)
            row  = tk.Frame(self.grid_slots_frame, bg=PANEL2 if done else PANEL,
                            pady=4, padx=8, relief="flat")
            row.pack(fill=tk.X, pady=2)
            indicator = tk.Frame(row, bg=col if done else DIM, width=8)
            indicator.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8))
            status = "✓  " + name if done else "○  " + name
            tk.Label(row, text=status, bg=PANEL2 if done else PANEL,
                     fg=col if done else MUTED,
                     font=("Courier", 9, "bold" if done else "normal"),
                     anchor="w").pack(side=tk.LEFT)

    # ── STEP HIGHLIGHT ─────────────────────────────────────────────────────────
    def set_step(self, i):
        for idx, (badge, lbl, btn) in enumerate(self.step_frames):
            if idx < i:
                badge.config(bg=SUCCESS, fg=BG)
                lbl.config(fg=MUTED)
                btn.config(bg=SUCCESS)
            elif idx == i:
                badge.config(bg=ACCENT, fg=BG)
                lbl.config(fg=TEXT)
                btn.config(bg=ACCENT)
            else:
                badge.config(bg=DIM, fg=MUTED)
                lbl.config(fg=MUTED)
                btn.config(bg=DIM)

    def set_instr(self, text):
        self.instr_var.set(text)

    def set_mode_label(self, txt, color=ACCENT):
        self.mode_var.set(f"MODE: {txt}")

    def set_msg(self, txt):
        self.msg_var.set(txt)

    def _cancel_mode(self):
        self.mode = "none"
        self.current_grid = []
        self.set_mode_label("IDLE", MUTED)
        self.set_msg("Mode cancelled.")

    def _update_info(self):
        if self.arena_center:
            cx, cy = self.arena_center
            r = self.arena_radius or 0
            self.arena_info.set(f"Arena:  ({int(cx)}, {int(cy)})  r={int(r)}")
        else:
            self.arena_info.set("Arena:  —")

        if self.px_per_cm:
            self.scale_info.set(f"Scale:  {self.px_per_cm:.3f} px/cm")
        else:
            self.scale_info.set("Scale:  —")

        self.rot_info.set(f"Rotation:  {self.quadrant_rotation}°")
        self.grids_var.set(f"Grids: {len(self.peltier_grids)}/4")

    # ── VIDEO ──────────────────────────────────────────────────────────────────
    def load_video(self):
        path = filedialog.askopenfilename(
            title="Open Video File",
            filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv *.tiff *.tif"), ("All", "*.*")]
        )
        if not path: return
        self.cap = cv2.VideoCapture(path)
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Could not read frame from video.")
            return
        self.raw_frame = frame
        self._fit_canvas()
        self.set_step(0)
        self.set_instr("Drag from center → edge to define the arena circle.\n\nKeyboard shortcuts:\nA – Arena  G – Grid\nS – Scale  R – Rotate\nE – Export  Z – Undo Grid\nEsc – Cancel mode")
        self.set_msg("Video loaded.  Next: drag to define arena circle.")

    def _fit_canvas(self):
        """Scale raw_frame to fit canvas, store ratio."""
        if self.raw_frame is None:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 2 or ch < 2:
            return
        h, w = self.raw_frame.shape[:2]
        ratio = min(cw / w, ch / h)
        self.scale_ratio = ratio
        self.render()

    def _raw_to_disp(self, pt):
        """Convert raw-frame coords → display coords."""
        return (pt[0] * self.scale_ratio, pt[1] * self.scale_ratio)

    def _disp_to_raw(self, pt):
        """Convert display coords → raw-frame coords."""
        return (pt[0] / self.scale_ratio, pt[1] / self.scale_ratio)

    # ── MODES ──────────────────────────────────────────────────────────────────
    def mode_circle(self):
        self.mode = "circle"
        self.set_mode_label("ARENA  (drag center→edge)", ACCENT)
        self.set_step(1)
        self.set_instr("Drag from center → edge to define the circular arena boundary.")

    def rotate_quads(self):
        self.quadrant_rotation = (self.quadrant_rotation + 90) % 360
        self.set_step(2)
        self.set_msg(f"Quadrant rotation: {self.quadrant_rotation}°")
        self._update_info()
        self.render()

    def mode_grid(self):
        if len(self.peltier_grids) >= 4:
            messagebox.showinfo("Done", "All 4 Peltier grids have been defined.")
            return
        self.mode = "grid"
        self.current_grid = []
        idx = len(self.peltier_grids)
        name = GRID_NAMES[idx]
        self.set_mode_label(f"GRID  [{name}]", GRID_COLORS[idx])
        self.set_step(3)
        self.set_instr(f"Defining {name}.\n\nClick 4 corners in order:\n1. Top-left\n2. Top-right\n3. Bottom-right\n4. Bottom-left")

    def mode_scale(self):
        self.mode = "scale"
        self.scale_pt1 = None
        self.scale_pt2 = None
        self.set_mode_label("SCALE  (click 2 points)", ACCENT2)
        self.set_step(4)
        self.set_instr("Click two points of known distance.\n(Default reference: 8\" = 20.32 cm)")

    # ── EVENTS ─────────────────────────────────────────────────────────────────
    def mouse_move(self, e):
        raw = self._disp_to_raw((e.x, e.y))
        self.coord_var.set(f"x: {int(raw[0])}   y: {int(raw[1])}")
        self.hover_pos = (e.x, e.y)

    def click(self, e):
        raw = self._disp_to_raw((e.x, e.y))

        if self.mode == "circle":
            self.drag_start = raw

        elif self.mode == "grid":
            self.current_grid.append(raw)
            remaining = 4 - len(self.current_grid)
            if remaining > 0:
                nxt = CORNER_LABELS[len(self.current_grid)]
                self.set_instr(f"Defining {GRID_NAMES[len(self.peltier_grids)]}.\n\nNext corner:\n→ {nxt}\n\n({remaining} more to go)")
                self.set_msg(f"Point {len(self.current_grid)}/4 placed.")
            else:
                idx = len(self.peltier_grids)
                self.peltier_grids.append({
                    "name": GRID_NAMES[idx],
                    "peltier_id": chr(65 + idx),     # A/B/C/D
                    "corners_px": [list(p) for p in self.current_grid]
                })
                self.current_grid = []
                self.mode = "none"
                self.set_mode_label("IDLE", MUTED)
                self.set_msg(f"{GRID_NAMES[idx]} saved ✓   ({len(self.peltier_grids)}/4 grids)")
                self.set_step(3)
                self._refresh_grid_slots()
                if len(self.peltier_grids) == 4:
                    self.set_instr("All 4 grids defined ✓\n\nNext: set scale or export.")

        elif self.mode == "scale":
            if not self.scale_pt1:
                self.scale_pt1 = raw
                self.set_msg("Scale point 1 placed.  Click second point.")
            else:
                self.scale_pt2 = raw
                self._ask_scale()

        self.render()
        self._update_info()

    def drag(self, e):
        if self.mode == "circle" and self.drag_start:
            raw = self._disp_to_raw((e.x, e.y))
            self.arena_center = self.drag_start
            self.arena_radius = dist(self.drag_start, raw)
            self.render()

    def release(self, e):
        if self.mode == "circle":
            self.drag_start = None
            self.set_mode_label("IDLE", MUTED)
            self.mode = "none"
            self.set_msg("Arena defined ✓")
            self.set_step(1)
            self._update_info()

    # ── SCALE ──────────────────────────────────────────────────────────────────
    def _ask_scale(self):
        d_px = dist(self.scale_pt1, self.scale_pt2)
        win = tk.Toplevel(self)
        win.title("Set Scale")
        win.configure(bg=PANEL)
        win.geometry("320x180")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="SET REAL-WORLD DISTANCE", bg=PANEL, fg=ACCENT,
                 font=("Courier", 10, "bold")).pack(pady=(16,4))
        tk.Label(win, text=f"Measured span: {d_px:.1f} px", bg=PANEL, fg=TEXT,
                 font=("Courier", 9)).pack()
        tk.Label(win, text="Enter real distance (cm):", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(pady=(12,2))

        entry = tk.Entry(win, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=("Courier", 11), justify="center")
        entry.insert(0, "20.32")
        entry.pack(pady=4, ipadx=8, ipady=4)
        entry.focus()

        def ok(ev=None):
            try:
                cm = float(entry.get())
                if cm <= 0: raise ValueError
                self.px_per_cm = d_px / cm
                self.set_msg(f"Scale set: {self.px_per_cm:.3f} px/cm")
                self.set_step(4)
                self._update_info()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Enter a positive number.", parent=win)

        entry.bind("<Return>", ok)
        styled_button(win, "Confirm", ok, color=SUCCESS).pack(pady=8)

    # ── RESET ──────────────────────────────────────────────────────────────────
    def reset_arena(self):
        self.arena_center = None
        self.arena_radius = None
        self._update_info()
        self.set_msg("Arena cleared.")
        self.render()

    def undo_grid(self):
        if self.peltier_grids:
            removed = self.peltier_grids.pop()
            self._refresh_grid_slots()
            self._update_info()
            self.set_msg(f"{removed['name']} removed.")
            self.render()
        self.current_grid = []

    def clear_grids(self):
        if not self.peltier_grids: return
        if not messagebox.askyesno("Clear Grids", "Remove all grid definitions?"):
            return
        self.peltier_grids = []
        self.current_grid = []
        self._refresh_grid_slots()
        self._update_info()
        self.set_msg("All grids cleared.")
        self.render()

    def reset_scale(self):
        self.px_per_cm = None
        self.scale_pt1 = None
        self.scale_pt2 = None
        self._update_info()
        self.set_msg("Scale cleared.")
        self.render()

    def reset_rotation(self):
        self.quadrant_rotation = 0
        self._update_info()
        self.set_msg("Rotation reset to 0°.")
        self.render()

    # ── RENDER ─────────────────────────────────────────────────────────────────
    def render(self):
        if self.raw_frame is None:
            return

        frame = self.raw_frame.copy()
        h, w = frame.shape[:2]
        r = self.scale_ratio
        dw, dh = int(w * r), int(h * r)

        # ── arena circle + quadrant lines
        if self.arena_center and self.arena_radius:
            cx, cy = map(int, self.arena_center)
            ar = int(self.arena_radius)

            # subtle fill
            overlay = frame.copy()
            cv2.circle(overlay, (cx, cy), ar, (30, 60, 30), -1)
            cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

            cv2.circle(frame, (cx, cy), ar, (63, 255, 130), 2)
            cv2.circle(frame, (cx, cy), 5, (63, 255, 130), -1)

            for i in range(4):
                a    = np.deg2rad(self.quadrant_rotation + i * 90)
                xe   = int(cx + ar * np.cos(a))
                ye   = int(cy + ar * np.sin(a))
                cv2.line(frame, (cx, cy), (xe, ye), (255, 255, 255), 1, cv2.LINE_AA)

                # quadrant label
                mid  = a + np.pi / 4
                tx   = int(cx + ar * 0.55 * np.cos(mid))
                ty   = int(cy + ar * 0.55 * np.sin(mid))
                cv2.putText(frame, f"Q{i+1}", (tx-14, ty+6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (200, 200, 200), 1, cv2.LINE_AA)

        # ── saved grids
        for idx, g in enumerate(self.peltier_grids):
            pts = np.array(g["corners_px"], np.int32)
            col = GRID_COLORS[idx]
            # convert hex → BGR
            col_bgr = (int(col[5:7], 16), int(col[3:5], 16), int(col[1:3], 16))
            overlay = frame.copy()
            cv2.fillPoly(overlay, [pts], col_bgr)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
            cv2.polylines(frame, [pts], True, col_bgr, 2, cv2.LINE_AA)
            for p in pts:
                cv2.circle(frame, tuple(p), 5, col_bgr, -1)
            ctr = pts.mean(axis=0).astype(int)
            cv2.putText(frame, g["name"], (ctr[0]-30, ctr[1]+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, col_bgr, 2, cv2.LINE_AA)

        # ── in-progress grid
        if self.current_grid:
            col_bgr = (int(ACCENT[5:7], 16), int(ACCENT[3:5], 16), int(ACCENT[1:3], 16))
            for i, p in enumerate(self.current_grid):
                cv2.circle(frame, (int(p[0]), int(p[1])), 6, col_bgr, -1)
                cv2.putText(frame, CORNER_LABELS[i][:2],
                            (int(p[0])+8, int(p[1])-6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, col_bgr, 1, cv2.LINE_AA)
            if len(self.current_grid) > 1:
                for i in range(len(self.current_grid)-1):
                    p1 = tuple(map(int, self.current_grid[i]))
                    p2 = tuple(map(int, self.current_grid[i+1]))
                    cv2.line(frame, p1, p2, col_bgr, 1, cv2.LINE_AA)

        # ── scale line
        if self.scale_pt1:
            p1 = tuple(map(int, self.scale_pt1))
            cv2.circle(frame, p1, 5, (56, 139, 253), -1)
        if self.scale_pt1 and self.scale_pt2:
            p1 = tuple(map(int, self.scale_pt1))
            p2 = tuple(map(int, self.scale_pt2))
            cv2.line(frame, p1, p2, (56, 139, 253), 2, cv2.LINE_AA)
            cv2.circle(frame, p2, 5, (56, 139, 253), -1)
            d = dist(self.scale_pt1, self.scale_pt2)
            mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2 - 12)
            if self.px_per_cm:
                label = f"{d/self.px_per_cm:.2f} cm"
            else:
                label = f"{d:.0f} px"
            cv2.putText(frame, label, mid, cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (56, 139, 253), 1, cv2.LINE_AA)

        # ── resize to canvas and display
        disp = cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_AREA)
        img  = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
        img  = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(img)

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        ox = max(0, (cw - dw) // 2)
        oy = max(0, (ch - dh) // 2)

        # update offset so click events map correctly
        self._canvas_offset = (ox, oy)

        self.canvas.delete("all")
        self.canvas.create_image(ox, oy, anchor="nw", image=self.photo)

    def _disp_to_raw(self, pt):
        ox, oy = getattr(self, "_canvas_offset", (0, 0))
        return ((pt[0] - ox) / self.scale_ratio,
                (pt[1] - oy) / self.scale_ratio)

    def _raw_to_disp(self, pt):
        ox, oy = getattr(self, "_canvas_offset", (0, 0))
        return (pt[0] * self.scale_ratio + ox,
                pt[1] * self.scale_ratio + oy)

    # ── EXPORT ─────────────────────────────────────────────────────────────────
    def export(self):
        issues = validate_grids(self.peltier_grids)
        if issues:
            messagebox.showwarning("Grid Validation Issues", "\n".join(issues))
            return
        if len(self.peltier_grids) != 4:
            messagebox.showerror("Export Error",
                f"Need 4 grids — only {len(self.peltier_grids)} defined.")
            return

        config = {
            "arena": {
                "center_px":             list(self.arena_center) if self.arena_center else None,
                "radius_px":             self.arena_radius,
                "quadrant_rotation_deg": self.quadrant_rotation
            },
            "peltier_grids": self.peltier_grids,
            "calibration": {
                "px_per_cm":  self.px_per_cm,
                "cm_per_px":  (1 / self.px_per_cm) if self.px_per_cm else None
            }
        }

        path = filedialog.asksaveasfilename(
            title="Save Calibration JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path: return

        with open(path, "w") as f:
            json.dump(config, f, indent=2)

        self.set_step(5)
        self.set_msg(f"Saved → {path}")
        messagebox.showinfo("Exported", f"Calibration saved to:\n{path}")


if __name__ == "__main__":
    app = ArenaCalibrator()
    app.mainloop()
