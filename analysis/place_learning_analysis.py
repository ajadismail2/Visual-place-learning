#!/usr/bin/env python3
"""
place_learning_analysis.py
============================
Drosophila Visual Place Learning — SLEAP Analysis Pipeline
Based on: Ofstad, Zuker & Reiser, Nature 2011

Computes all behavioral metrics from SLEAP tracking + arena_calibrator.py JSON:
  • Time to Target          — training trials only
  • Path Length to Target   — cm, training trials only
  • Direction Index         — first quadrant entered after leaving start
  • Mean Speed              — cm/s, up to target or full trial
  • Quadrant Occupancy      — % time in each of the 4 Peltier-grid zones
  • Probe Learning Index    — (t_Q_target - t_Q_opposite) / sum, probe trial only

───────────────────────────────────────────────────────────────────────────────
QUICK START
───────────────────────────────────────────────────────────────────────────────

1) Export SLEAP analysis HDF5 from your .slp:
       sleap-convert --format analysis tracking.slp -o trial_01.h5
   Or GUI: File → Export Analysis HDF5

2) Run — single training trial:
       python place_learning_analysis.py \\
           --files trial_01.h5 \\
           --config arena_config.json \\
           --target-grid 1 \\
           --start-grid 0 \\
           --fps 25

3) Run — full experiment (10 training + probe):
       python place_learning_analysis.py \\
           --files trial_01.h5 trial_02.h5 ... trial_10.h5 \\
           --probe probe.h5 \\
           --config arena_config.json \\
           --target-grid 1 --start-grid 0 --fps 25 --output results/

4) .slp files directly (requires `pip install sleap`):
       python place_learning_analysis.py \\
           --files trial_01.slp \\
           --config arena_config.json \\
           --target-grid 1 --fps 25

───────────────────────────────────────────────────────────────────────────────
GRID / QUADRANT NUMBERING
───────────────────────────────────────────────────────────────────────────────

Grid indices match the order they were drawn in arena_calibrator.py:
  grid_1 → index 0,  grid_2 → index 1, etc.

--target-grid : which peltier grid is the cool tile (default 1 = grid_2)
--start-grid  : where flies begin each trial (default 0 = grid_1)
Opposite quadrant for Probe Learning Index is computed automatically.
"""

import json
import sys
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# Optional imports — graceful fallback messages
try:
    import h5py
except ImportError:
    sys.exit("[ERROR] h5py not installed: pip install h5py")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    warnings.warn("[WARN] matplotlib not installed — plots will be skipped")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    warnings.warn("[WARN] opencv-python not installed — using slower polygon test")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  SLEAP LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_sleap_h5(path: Path, fps_override: float | None = None) -> dict:
    """
    Load SLEAP analysis export (.h5).

    SLEAP analysis HDF5 shape conventions handled:
        (n_tracks, n_frames, n_nodes, 2)  ← standard sleap-convert output
        (n_frames, n_nodes, 2, n_tracks)  ← older SLEAP versions

    Returns dict:
        centroids   : (n_tracks, n_frames, 2)  NaN where untracked
        fps         : float
        track_names : list[str]
        node_names  : list[str]
        n_tracks    : int
        n_frames    : int
    """
    with h5py.File(path, "r") as f:
        available = list(f.keys())

        if "tracks" not in f:
            raise KeyError(
                f"No 'tracks' dataset in {path}.\n"
                f"Available keys: {available}\n"
                "Export via:  sleap-convert --format analysis tracking.slp -o out.h5"
            )

        raw = f["tracks"][:]  # load fully

        # ── Detect shape convention ──────────────────────────────────────────
        if raw.ndim == 4:
            if raw.shape[-1] == 2:
                # (n_tracks, n_frames, n_nodes, 2)  ← standard
                t4 = raw
            elif raw.shape[2] == 2:
                # (n_frames, n_nodes, 2, n_tracks)  ← old
                t4 = np.transpose(raw, (3, 0, 1, 2))
            else:
                raise ValueError(f"Unrecognized 4-D tracks shape: {raw.shape}")
        elif raw.ndim == 3:
            # (n_tracks, n_frames, 2) — single-node skeleton
            t4 = raw[:, :, np.newaxis, :]
        else:
            raise ValueError(f"Unexpected tracks ndim={raw.ndim}, shape={raw.shape}")

        n_tracks, n_frames, n_nodes, _ = t4.shape

        # Centroid = nanmean across body nodes
        centroids = np.nanmean(t4, axis=2)  # (n_tracks, n_frames, 2)

        # ── FPS ─────────────────────────────────────────────────────────────
        fps = fps_override
        if fps is None:
            for key in ("fps", "video_fps"):
                if key in f:
                    fps = float(np.array(f[key]).ravel()[0])
                    break
            if fps is None and "fps" in f.attrs:
                fps = float(f.attrs["fps"])

        # ── Names ────────────────────────────────────────────────────────────
        def _decode(arr):
            return [x.decode() if isinstance(x, bytes) else str(x) for x in arr]

        track_names = _decode(f["track_names"][:]) if "track_names" in f else \
                      [f"fly_{i}" for i in range(n_tracks)]
        node_names  = _decode(f["node_names"][:])  if "node_names"  in f else \
                      [f"node_{i}" for i in range(n_nodes)]

    return dict(centroids=centroids, fps=fps, track_names=track_names,
                node_names=node_names, n_tracks=n_tracks, n_frames=n_frames)


def load_sleap_slp(path: Path, fps_override: float | None = None) -> dict:
    """Load SLEAP native .slp file. Requires `pip install sleap`."""
    try:
        import sleap
    except ImportError:
        raise ImportError(
            "sleap package required for .slp files.\n"
            "Install:  pip install sleap\n"
            "OR export to .h5:  sleap-convert --format analysis tracking.slp -o out.h5"
        )

    labels = sleap.load_file(str(path))
    n_frames = len(labels)
    n_tracks = len(labels.tracks)
    n_nodes  = len(labels.skeletons[0].nodes) if labels.skeletons else 1

    centroids   = np.full((n_tracks, n_frames, 2), np.nan)
    track_index = {t: i for i, t in enumerate(labels.tracks)}

    for fi, lf in enumerate(labels):
        for inst in lf.instances:
            if inst.track is None:
                continue
            ti  = track_index[inst.track]
            pts = inst.numpy()                          # (n_nodes, 2)
            ok  = pts[~np.any(np.isnan(pts), axis=1)]
            if len(ok):
                centroids[ti, fi] = ok.mean(axis=0)

    fps = fps_override
    if fps is None and labels.videos:
        v = labels.videos[0]
        fps = getattr(v, "fps", None)

    track_names = [t.name for t in labels.tracks]
    node_names  = [n.name for n in labels.skeletons[0].nodes] if labels.skeletons else []

    return dict(centroids=centroids, fps=fps, track_names=track_names,
                node_names=node_names, n_tracks=n_tracks, n_frames=n_frames)


def load_sleap(path: Path, fps_override: float | None = None) -> dict:
    path = Path(path)
    if path.suffix == ".slp":
        return load_sleap_slp(path, fps_override)
    return load_sleap_h5(path, fps_override)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ARENA / GEOMETRY UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def poly_corners(grid: dict) -> np.ndarray:
    """Return (4, 2) int32 corner array from a peltier_grid entry."""
    return np.array(grid["corners_px"], dtype=np.float32)


def point_in_poly(pt: np.ndarray, corners: np.ndarray) -> bool:
    """
    Test whether point pt=(x,y) lies inside the quadrilateral defined by corners.
    Uses cv2 if available, otherwise a winding-number fallback.
    """
    if np.any(np.isnan(pt)):
        return False
    if HAS_CV2:
        corners_i = corners.reshape((-1, 1, 2)).astype(np.float32)
        result = cv2.pointPolygonTest(corners_i, (float(pt[0]), float(pt[1])), False)
        return result >= 0
    # Winding-number fallback
    x, y = float(pt[0]), float(pt[1])
    n = len(corners)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = corners[i]
        xj, yj = corners[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def assign_quadrant(pt: np.ndarray, center: tuple, rotation_deg: float) -> int | None:
    """
    Return quadrant 0-3 based on angle from arena center.
    Q0 starts at rotation_deg and sweeps 90° CW (image coords, y-down).
    Returns None if point is NaN.
    """
    if np.any(np.isnan(pt)):
        return None
    dx = pt[0] - center[0]
    dy = pt[1] - center[1]
    angle = np.degrees(np.arctan2(dy, dx)) % 360
    offset = (angle - rotation_deg) % 360
    return int(offset // 90)    # 0, 1, 2, 3


def grid_centroid(grid: dict) -> np.ndarray:
    return np.mean(poly_corners(grid), axis=0)


def map_grids_to_quadrants(config: dict) -> dict[int, int]:
    """
    Returns {grid_index: quadrant_index} by matching each grid's centroid
    to the angle-based quadrant it falls in.
    """
    center = tuple(config["arena"]["center_px"])
    rot    = config["arena"]["quadrant_rotation_deg"]
    mapping = {}
    for gi, grid in enumerate(config["peltier_grids"]):
        c   = grid_centroid(grid)
        q   = assign_quadrant(c, center, rot)
        mapping[gi] = q
    return mapping


def opposite_quadrant(q: int) -> int:
    """Quadrant directly across from q (180° away)."""
    return (q + 2) % 4


# ─────────────────────────────────────────────────────────────────────────────
# 3.  PER-FLY METRIC COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_fly_metrics(
    positions:   np.ndarray,   # (n_frames, 2)  NaN where missing
    config:      dict,
    fps:         float,
    px_per_cm:   float,
    target_grid: int,          # grid index (0-based)
    start_grid:  int,          # grid index (0-based)
    is_probe:    bool = False,
    probe_window_s: float = 60.0,
) -> dict:
    """
    Compute all place-learning metrics for a single fly track.

    Returns a dict of scalar metrics (NaN where not applicable).
    """
    n_frames = len(positions)

    # ── Grid polygons ────────────────────────────────────────────────────────
    grids    = config["peltier_grids"]
    center   = tuple(config["arena"]["center_px"])
    rot      = config["arena"]["quadrant_rotation_deg"]
    g2q      = map_grids_to_quadrants(config)  # grid_idx → quadrant_idx

    target_q  = g2q[target_grid]
    start_q   = g2q[start_grid]
    opposite_q = opposite_quadrant(target_q)

    target_corners = poly_corners(grids[target_grid])
    start_corners  = poly_corners(grids[start_grid])

    # ── Per-frame quadrant + grid membership ─────────────────────────────────
    quadrants = np.array([assign_quadrant(positions[f], center, rot)
                          for f in range(n_frames)])           # int or None

    in_target = np.array([point_in_poly(positions[f], target_corners)
                          for f in range(n_frames)])           # bool

    # ── Frame-to-frame displacements (px) ────────────────────────────────────
    valid_mask = ~np.any(np.isnan(positions), axis=1)
    dx = np.diff(positions[:, 0])
    dy = np.diff(positions[:, 1])
    step_px = np.hypot(dx, dy)
    step_valid = valid_mask[:-1] & valid_mask[1:]
    step_px[~step_valid] = np.nan

    step_cm = step_px / px_per_cm

    # ────────────────────────────────────────────────────────────────────────
    # TRAINING-TRIAL METRICS
    # ────────────────────────────────────────────────────────────────────────
    if not is_probe:

        # ── Find first frame inside target ───────────────────────────────────
        target_frames = np.where(in_target)[0]
        if len(target_frames) == 0:
            # Fly never reached target
            arrival_frame = n_frames   # sentinel
            reached = False
        else:
            arrival_frame = target_frames[0]
            reached = True

        # Time to Target (s)
        time_to_target = arrival_frame / fps if reached else np.nan

        # Path Length to Target (cm)
        path_length_cm = float(np.nansum(step_cm[:arrival_frame])) if reached else np.nan

        # Mean Speed (cm/s) — up to arrival (or full trial)
        end_f = arrival_frame if reached else n_frames
        mean_speed_cms = float(np.nanmean(step_cm[:end_f]) * fps) if end_f > 0 else np.nan

        # ── Direction Index (first non-start quadrant entered) ────────────────
        # Find when fly first leaves start quadrant
        left_start = False
        first_quad_entered = None
        for f in range(n_frames):
            q = quadrants[f]
            if q is None:
                continue
            if not left_start:
                if q != start_q:
                    left_start = True
                    first_quad_entered = q
                    break

        if first_quad_entered is None:
            direction_correct = np.nan   # never left start
        else:
            direction_correct = 1.0 if first_quad_entered == target_q else 0.0

        # ── Quadrant Occupancy ────────────────────────────────────────────────
        occ = np.full(4, np.nan)
        valid_q = [(quadrants[f] is not None and valid_mask[f]) for f in range(n_frames)]
        n_valid = sum(valid_q)
        if n_valid > 0:
            for qi in range(4):
                occ[qi] = sum(1 for f in range(n_frames)
                              if valid_mask[f] and quadrants[f] == qi) / n_valid

        return dict(
            reached_target=reached,
            time_to_target_s=time_to_target,
            path_length_cm=path_length_cm,
            mean_speed_cms=mean_speed_cms,
            direction_correct=direction_correct,
            occ_Q0=occ[0], occ_Q1=occ[1], occ_Q2=occ[2], occ_Q3=occ[3],
            probe_learning_index=np.nan,
        )

    # ────────────────────────────────────────────────────────────────────────
    # PROBE-TRIAL METRICS
    # ────────────────────────────────────────────────────────────────────────
    else:
        # Find first frame fly leaves start quadrant
        probe_start_frame = None
        for f in range(n_frames):
            q = quadrants[f]
            if q is not None and q != start_q:
                probe_start_frame = f
                break

        window_frames = int(probe_window_s * fps)

        if probe_start_frame is None:
            # Fly never left start during probe
            pli = np.nan
            occ = np.full(4, np.nan)
        else:
            end_f = min(probe_start_frame + window_frames, n_frames)
            slice_q = [quadrants[f] for f in range(probe_start_frame, end_f)]
            slice_v = [valid_mask[f] for f in range(probe_start_frame, end_f)]

            t_target   = sum(1 for i, q in enumerate(slice_q)
                             if slice_v[i] and q == target_q)
            t_opposite = sum(1 for i, q in enumerate(slice_q)
                             if slice_v[i] and q == opposite_q)
            denom = t_target + t_opposite
            pli = (t_target - t_opposite) / denom if denom > 0 else np.nan

            # Full-trial occupancy
            n_valid = sum(valid_mask)
            occ = np.full(4, np.nan)
            if n_valid > 0:
                for qi in range(4):
                    occ[qi] = sum(1 for f in range(n_frames)
                                  if valid_mask[f] and quadrants[f] == qi) / n_valid

        return dict(
            reached_target=np.nan,
            time_to_target_s=np.nan,
            path_length_cm=np.nan,
            mean_speed_cms=float(np.nanmean(step_cm) * fps),
            direction_correct=np.nan,
            occ_Q0=occ[0], occ_Q1=occ[1], occ_Q2=occ[2], occ_Q3=occ[3],
            probe_learning_index=pli,
        )


def analyse_trial(
    sleap_data: dict,
    config:     dict,
    target_grid: int,
    start_grid:  int,
    fps:         float,
    is_probe:    bool = False,
    probe_window_s: float = 60.0,
) -> pd.DataFrame:
    """
    Run per-fly metrics for every track in a SLEAP file.
    Returns a DataFrame with one row per fly.
    """
    px_per_cm  = config["calibration"]["px_per_cm"]
    centroids  = sleap_data["centroids"]   # (n_tracks, n_frames, 2)
    track_names = sleap_data["track_names"]
    rows = []
    for ti in range(sleap_data["n_tracks"]):
        m = compute_fly_metrics(
            positions=centroids[ti],
            config=config,
            fps=fps,
            px_per_cm=px_per_cm,
            target_grid=target_grid,
            start_grid=start_grid,
            is_probe=is_probe,
            probe_window_s=probe_window_s,
        )
        m["fly"] = track_names[ti]
        rows.append(m)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  GROUP SUMMARY STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def summarise(df: pd.DataFrame) -> pd.Series:
    numeric = df.select_dtypes(include="number")
    return pd.concat([numeric.mean().rename(lambda c: c + "_mean"),
                      numeric.sem().rename(lambda c: c + "_sem")])


# ─────────────────────────────────────────────────────────────────────────────
# 5.  PLOTTING
# ─────────────────────────────────────────────────────────────────────────────

QUAD_COLORS = ["#4c72b0", "#dd8452", "#55a868", "#c44e52"]
GRID_ALPHA  = 0.25


def _draw_arena(ax, config, target_grid, start_grid):
    """Draw arena circle, grid polygons, and labels on an axes."""
    cx, cy = config["arena"]["center_px"]
    r      = config["arena"]["radius_px"]

    circle = plt.Circle((cx, cy), r, fill=False, edgecolor="white", lw=1.5, ls="--")
    ax.add_patch(circle)

    g2q = map_grids_to_quadrants(config)
    for gi, grid in enumerate(config["peltier_grids"]):
        corners = poly_corners(grid)
        color   = QUAD_COLORS[g2q[gi]]
        poly    = MplPolygon(corners, closed=True,
                             facecolor=color, edgecolor=color,
                             alpha=GRID_ALPHA, lw=2)
        ax.add_patch(poly)
        gc = grid_centroid(grid)
        label = "TARGET" if gi == target_grid else \
                ("START"  if gi == start_grid  else f"G{gi}")
        ax.text(gc[0], gc[1], label, ha="center", va="center",
                fontsize=7, color="white", fontweight="bold")


def plot_trajectories(sleap_data, config, target_grid, start_grid, out_path):
    if not HAS_MPL:
        return
    n_tracks = sleap_data["n_tracks"]
    centroids = sleap_data["centroids"]
    px_per_cm = config["calibration"]["px_per_cm"]

    fig, axes = plt.subplots(1, min(n_tracks, 8), figsize=(min(n_tracks, 8) * 2.5, 3),
                             facecolor="#1a1a1a")
    if n_tracks == 1:
        axes = [axes]
    elif n_tracks > 8:
        axes = axes[:8]

    for ti, ax in enumerate(axes):
        ax.set_facecolor("#1a1a1a")
        _draw_arena(ax, config, target_grid, start_grid)

        pos = centroids[ti]
        valid = ~np.any(np.isnan(pos), axis=1)
        xs, ys = pos[valid, 0], pos[valid, 1]
        ax.plot(xs, ys, lw=0.6, color="#00d4ff", alpha=0.7)
        if len(xs):
            ax.scatter(xs[0], ys[0], c="lime",   s=20, zorder=5, label="start")
            ax.scatter(xs[-1], ys[-1], c="red",   s=20, zorder=5, label="end")

        ax.set_aspect("equal")
        ax.set_title(sleap_data["track_names"][ti], color="white", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])

    fig.suptitle("Fly Trajectories", color="white", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Trajectories → {out_path}")


def plot_learning_curve(all_summaries: list[pd.Series], out_path):
    """Plot time-to-target and path-length across trials."""
    if not HAS_MPL:
        return
    n_trials = len(all_summaries)
    trials   = np.arange(1, n_trials + 1)

    t_mean = np.array([s.get("time_to_target_s_mean", np.nan) for s in all_summaries])
    t_sem  = np.array([s.get("time_to_target_s_sem",  np.nan) for s in all_summaries])
    p_mean = np.array([s.get("path_length_cm_mean",   np.nan) for s in all_summaries])
    p_sem  = np.array([s.get("path_length_cm_sem",    np.nan) for s in all_summaries])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), facecolor="#1a1a1a")
    for ax in (ax1, ax2):
        ax.set_facecolor("#111111")
        ax.spines[:].set_color("#555")
        ax.tick_params(colors="#aaa"); ax.xaxis.label.set_color("#aaa")
        ax.yaxis.label.set_color("#aaa"); ax.title.set_color("white")

    ax1.errorbar(trials, t_mean, yerr=t_sem, fmt="o-", color="#e94560",
                 capsize=4, lw=2, ms=5)
    ax1.set_xlabel("Trial"); ax1.set_ylabel("Time to target (s)")
    ax1.set_title("Learning Curve — Time to Target")

    ax2.errorbar(trials, p_mean, yerr=p_sem, fmt="s-", color="#4c9be8",
                 capsize=4, lw=2, ms=5)
    ax2.set_xlabel("Trial"); ax2.set_ylabel("Path length (cm)")
    ax2.set_title("Learning Curve — Path Length")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Learning curve → {out_path}")


def plot_quadrant_occupancy(all_summaries: list[pd.Series], out_path):
    if not HAS_MPL:
        return
    n_trials = len(all_summaries)
    trials   = list(range(1, n_trials + 1))
    occ = np.array([[s.get(f"occ_Q{q}_mean", 0) for q in range(4)]
                    for s in all_summaries])

    fig, ax = plt.subplots(figsize=(max(6, n_trials * 0.6 + 1), 4), facecolor="#1a1a1a")
    ax.set_facecolor("#111111")
    ax.spines[:].set_color("#555")
    ax.tick_params(colors="#aaa")
    ax.xaxis.label.set_color("#aaa"); ax.yaxis.label.set_color("#aaa")
    ax.title.set_color("white")

    bottom = np.zeros(n_trials)
    labels = ["Q0", "Q1 (target)", "Q2", "Q3"]
    for qi in range(4):
        ax.bar(trials, occ[:, qi], bottom=bottom,
               color=QUAD_COLORS[qi], label=labels[qi], alpha=0.85)
        bottom += occ[:, qi]

    ax.axhline(0.25, ls="--", color="white", lw=0.8, alpha=0.5, label="chance (25%)")
    ax.set_ylim(0, 1); ax.set_xlabel("Trial"); ax.set_ylabel("Fraction of time")
    ax.set_title("Quadrant Occupancy per Trial")
    ax.legend(fontsize=7, labelcolor="white", facecolor="#222", edgecolor="#555")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Quadrant occupancy → {out_path}")


def plot_probe_learning_index(probe_df: pd.DataFrame, out_path):
    if not HAS_MPL:
        return
    pli = probe_df["probe_learning_index"].dropna().values

    fig, ax = plt.subplots(figsize=(4, 4), facecolor="#1a1a1a")
    ax.set_facecolor("#111111")
    ax.spines[:].set_color("#555"); ax.tick_params(colors="#aaa")
    ax.yaxis.label.set_color("#aaa"); ax.title.set_color("white")

    jitter = np.random.default_rng(42).uniform(-0.05, 0.05, len(pli))
    ax.scatter(jitter, pli, color="#e94560", alpha=0.6, s=40, zorder=3)
    ax.bar([0], [np.nanmean(pli)], width=0.15, color="#e94560", alpha=0.4, zorder=2)
    ax.errorbar([0], [np.nanmean(pli)], yerr=[np.nanstd(pli) / np.sqrt(len(pli))],
                fmt="none", color="#e94560", capsize=6, lw=2)
    ax.axhline(0, ls="--", color="white", lw=0.8, alpha=0.5)
    ax.set_xlim(-0.3, 0.3); ax.set_xticks([0]); ax.set_xticklabels(["Probe"])
    ax.set_ylabel("Probe Learning Index")
    ax.set_title(f"Probe Learning Index\nn={len(pli)}, mean={np.nanmean(pli):.3f}")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Probe learning index → {out_path}")


def plot_speed(all_summaries: list[pd.Series], out_path):
    if not HAS_MPL:
        return
    trials  = list(range(1, len(all_summaries) + 1))
    s_mean  = [s.get("mean_speed_cms_mean", np.nan) for s in all_summaries]
    s_sem   = [s.get("mean_speed_cms_sem",  np.nan) for s in all_summaries]

    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor="#1a1a1a")
    ax.set_facecolor("#111111"); ax.spines[:].set_color("#555"); ax.tick_params(colors="#aaa")
    ax.xaxis.label.set_color("#aaa"); ax.yaxis.label.set_color("#aaa"); ax.title.set_color("white")
    ax.errorbar(trials, s_mean, yerr=s_sem, fmt="D-", color="#55a868",
                capsize=4, lw=2, ms=5)
    ax.set_xlabel("Trial"); ax.set_ylabel("Speed (cm/s)")
    ax.set_title("Mean Walking Speed (should stay flat)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Speed → {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  CLI / MAIN
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Drosophila Place Learning Analysis from SLEAP + arena_calibrator.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--files",   nargs="+", required=True, metavar="FILE",
                   help="SLEAP .h5 or .slp files, one per training trial (ordered trial1 … trialN)")
    p.add_argument("--probe",   default=None, metavar="FILE",
                   help="SLEAP file for the probe trial (no cool tile)")
    p.add_argument("--config",  required=True, metavar="JSON",
                   help="Arena config JSON from arena_calibrator.py")
    p.add_argument("--target-grid", type=int, default=1,
                   help="0-based index of cool-tile Peltier grid (default: 1)")
    p.add_argument("--start-grid",  type=int, default=0,
                   help="0-based index of fly-start Peltier grid (default: 0)")
    p.add_argument("--fps",     type=float, default=None,
                   help="Camera frame rate (Hz). Read from file if omitted.")
    p.add_argument("--probe-window", type=float, default=60.0,
                   help="Seconds after leaving start to score probe trial (default: 60)")
    p.add_argument("--output",  default="results", metavar="DIR",
                   help="Output directory for CSVs and plots (default: results/)")
    p.add_argument("--no-plots", action="store_true",
                   help="Skip generating figures")
    return p.parse_args()


def main():
    args = parse_args()
    out  = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config)
    print(f"[CONFIG] Arena center={config['arena']['center_px']}, "
          f"radius={config['arena']['radius_px']:.1f}px, "
          f"scale={config['calibration']['px_per_cm']:.2f}px/cm")
    print(f"[CONFIG] {len(config['peltier_grids'])} Peltier grids loaded")

    g2q = map_grids_to_quadrants(config)
    print("[CONFIG] Grid → Quadrant mapping:", g2q)
    print(f"[CONFIG] Target grid {args.target_grid} → Q{g2q[args.target_grid]}")
    print(f"[CONFIG] Start  grid {args.start_grid}  → Q{g2q[args.start_grid]}")

    # ── Training trials ──────────────────────────────────────────────────────
    all_dfs       = []
    all_summaries = []

    for ti, fpath in enumerate(args.files, start=1):
        print(f"\n[TRIAL {ti}] {fpath}")
        data = load_sleap(fpath, args.fps)
        fps  = data["fps"] or args.fps
        if fps is None:
            sys.exit("[ERROR] FPS unknown. Pass --fps <value>.")
        print(f"  {data['n_tracks']} tracks × {data['n_frames']} frames @ {fps:.1f}fps")

        df = analyse_trial(data, config,
                           target_grid=args.target_grid,
                           start_grid=args.start_grid,
                           fps=fps,
                           is_probe=False)
        df.insert(0, "trial", ti)
        df.insert(1, "file",  Path(fpath).name)
        all_dfs.append(df)

        s = summarise(df)
        all_summaries.append(s)

        print(f"  reached target: {df['reached_target'].sum()}/{len(df)} flies")
        print(f"  time to target: {s['time_to_target_s_mean']:.1f} ± {s['time_to_target_s_sem']:.1f} s")
        print(f"  path length:    {s['path_length_cm_mean']:.1f} ± {s['path_length_cm_sem']:.1f} cm")
        print(f"  mean speed:     {s['mean_speed_cms_mean']:.2f} ± {s['mean_speed_cms_sem']:.2f} cm/s")
        print(f"  direction correct: {df['direction_correct'].mean():.2%}")

        if not args.no_plots:
            plot_trajectories(data, config, args.target_grid, args.start_grid,
                              out / f"trajectories_trial{ti:02d}.png")

    # ── Merge and save training CSVs ─────────────────────────────────────────
    if all_dfs:
        full = pd.concat(all_dfs, ignore_index=True)
        full.to_csv(out / "per_fly_metrics.csv", index=False)
        print(f"\n[SAVED] Per-fly metrics → {out/'per_fly_metrics.csv'}")

        sum_df = pd.DataFrame(all_summaries)
        sum_df.insert(0, "trial", range(1, len(all_summaries) + 1))
        sum_df.to_csv(out / "trial_summaries.csv", index=False)
        print(f"[SAVED] Trial summaries → {out/'trial_summaries.csv'}")

        if not args.no_plots and len(all_summaries) > 1:
            plot_learning_curve(all_summaries, out / "learning_curve.png")
            plot_quadrant_occupancy(all_summaries, out / "quadrant_occupancy.png")
            plot_speed(all_summaries, out / "speed.png")

    # ── Probe trial ──────────────────────────────────────────────────────────
    if args.probe:
        print(f"\n[PROBE] {args.probe}")
        data  = load_sleap(args.probe, args.fps)
        fps   = data["fps"] or args.fps
        print(f"  {data['n_tracks']} tracks × {data['n_frames']} frames @ {fps:.1f}fps")

        probe_df = analyse_trial(data, config,
                                 target_grid=args.target_grid,
                                 start_grid=args.start_grid,
                                 fps=fps,
                                 is_probe=True,
                                 probe_window_s=args.probe_window)
        probe_df.insert(0, "trial", "probe")
        probe_df.insert(1, "file",  Path(args.probe).name)
        probe_df.to_csv(out / "probe_metrics.csv", index=False)

        pli_vals = probe_df["probe_learning_index"].dropna()
        print(f"  Probe Learning Index: {pli_vals.mean():.3f} ± {pli_vals.sem():.3f}  (n={len(pli_vals)})")
        print(f"[SAVED] Probe metrics → {out/'probe_metrics.csv'}")

        if not args.no_plots:
            plot_probe_learning_index(probe_df, out / "probe_learning_index.png")
            plot_trajectories(data, config, args.target_grid, args.start_grid,
                              out / "trajectories_probe.png")

    print(f"\n[DONE] All outputs in → {out}/")


if __name__ == "__main__":
    main()
