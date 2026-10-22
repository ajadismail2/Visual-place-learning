"""AMADEUS Fly Target Analysis, version 1.3.0.

Windows setup (PowerShell):
    py -m pip install numpy opencv-python pillow
    py fly_target_time_gui_amadeus.py

Requires Python 3.10 or later with Tkinter.

Use the SAME video geometry as the AMADEUS input. Temporal offset cannot fix
spatial cropping, resizing, rotation, or an altered frame rate. CSV frame
numbers are zero-based. Video frame = CSV frame - video offset.

Analysis uses OBB centres, not SLEAP keypoints. Headings are optional and do
not affect target or movement calculations. Original identities and positions
are never reassigned, interpolated, smoothed, or automatically corrected.
Missing-frame tolerance is an explicit assumption used only for target dwell.
Movement uses consecutive valid frames within each trial, and percentages of
time moving use valid step durations as their denominator. Jump flags are
review aids; flagged displacements remain in the numerical results.

Target success requires continuous time inside the target, with movement
allowed. Each plotted trajectory ends at that fly's first completed dwell,
including the completion frame. Main GUI playback keeps following the fly
after success. Exported MP4 trails freeze at success within each trial. Separate
JPEGs are available for every fly. Movement metrics describe the full trial.

The Flies included in analysis checkboxes select the analysis population.
Excluded IDs are omitted from calculations, plots and exports; original fly
numbers and colors remain unchanged. Recalculate after changing selection.

All data CSVs retain floating-point precision. Exports record definitions,
settings, identity mapping, tracking coverage, and input-file SHA-256.
Run --self-test to check the numerical engine or --check-csv PATH to validate
a CSV without opening the graphical interface.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import queue
import re
import shutil
import tempfile
import threading
import time
import traceback
import tkinter as tk
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install with:\n"
        "  py -m pip install numpy opencv-python pillow\n"
        f"Details: {exc}"
    ) from exc

APP_VERSION = "1.3.0"
FORMAT_DOCUMENTATION = "https://amadeus.jpmyrmecol.com/Manual_EN.html#outputs"
FULL_TRIAL_COUNT = 10
FULL_TRIAL_SECONDS = 300
FULL_TARGET_SEQUENCE = [1, 2, 3, 2, 1, 0, 3, 2, 1, 0]
FULL_TARGET_TEXT = "B - C - D - C - B - A - D - C - B - A"
BOX_LETTERS = ["A", "B", "C", "D"]
BOX_NAMES = [f"Cool Box {letter}" for letter in BOX_LETTERS]


class CancelledError(Exception):
    """A user-cancelled operation; never reported as a successful export."""


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise CancelledError("Operation cancelled. No completed output was saved.")


def positive_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a positive number.") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive finite number.")
    return number


def nonnegative_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be zero or a positive number.") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be zero or a positive finite number.")
    return number


def integer_number(value, label, allow_negative=False):
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?\d+", text):
        raise ValueError(f"{label} must be an integer.")
    number = int(text)
    if not allow_negative and number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def format_target_sequence(sequence):
    return " - ".join(BOX_LETTERS[int(i)] for i in sequence)


def parse_target_sequence(text):
    raw = str(text).strip().upper()
    tokens = list(raw) if re.fullmatch(r"[A-D]{10}", raw) else [
        x for x in re.split(r"[\s,;>\-–—]+", raw) if x
    ]
    mapping = {"A": 0, "B": 1, "C": 2, "D": 3,
               "1": 0, "2": 1, "3": 2, "4": 3}
    if len(tokens) != FULL_TRIAL_COUNT or any(x not in mapping for x in tokens):
        raise ValueError("Target order must contain exactly 10 targets, using A-D or 1-4.")
    return tuple(mapping[x] for x in tokens)


@dataclass(frozen=True)
class Zone:
    name: str
    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self):
        a, b, c, d = map(float, (self.x1, self.y1, self.x2, self.y2))
        if not all(math.isfinite(v) for v in (a, b, c, d)):
            raise ValueError("Box coordinates must be finite numbers.")
        a, c = sorted((a, c))
        b, d = sorted((b, d))
        if a == c or b == d:
            raise ValueError("Each box needs positive width and height.")
        for attr, value in zip(("x1", "y1", "x2", "y2"), (a, b, c, d)):
            object.__setattr__(self, attr, value)

    def contains(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def as_dict(self):
        return asdict(self)


def validate_zones(zones, video_size=None):
    if len(zones) != 4:
        raise ValueError("Define all four named boxes: A, B, C and D.")
    for i, z in enumerate(zones):
        if min(z.x1, z.y1) < 0:
            raise ValueError(f"Box {BOX_LETTERS[i]} has negative coordinates.")
        if video_size:
            w, h = video_size
            if z.x2 > w or z.y2 > h:
                raise ValueError(f"Box {BOX_LETTERS[i]} extends beyond the loaded video.")
        for j in range(i):
            other = zones[j]
            if (min(z.x2, other.x2) > max(z.x1, other.x1)
                    and min(z.y2, other.y2) > max(z.y1, other.y1)):
                raise ValueError(
                    f"Boxes {BOX_LETTERS[j]} and {BOX_LETTERS[i]} overlap in area. "
                    "Redraw the boxes so a fly has an unambiguous region."
                )


def load_zones_json(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    entries = obj.get("boxes", obj.get("zones", [])) if isinstance(obj, dict) else obj
    if isinstance(entries, dict):
        # Choose one complete naming convention. Never mix 0-based and 1-based keys.
        conventions = [
            [str(i) for i in range(4)], [str(i + 1) for i in range(4)],
            BOX_LETTERS, BOX_NAMES, [f"Cool Box {i + 1}" for i in range(4)],
            [f"zone_{i + 1}" for i in range(4)],
        ]
        keys = next((keys for keys in conventions if all(k in entries for k in keys)), None)
        if keys is None:
            raise ValueError("Box JSON does not contain a complete A-D set.")
        entries = [entries[k] for k in keys]
    if not isinstance(entries, list) or len(entries) != 4:
        raise ValueError("Box JSON must contain exactly four rectangles.")
    zones = tuple(Zone(BOX_NAMES[i], *(a[k] for k in ("x1", "y1", "x2", "y2")))
                  for i, a in enumerate(entries))
    validate_zones(zones)
    return zones, obj if isinstance(obj, dict) else {}


@dataclass
class TrackingDataset:
    source_path: str
    ids: tuple
    first_frame: int
    values: np.ndarray  # shape [frame span, ID column, cx/cy/w/h/heading]
    row_present: np.ndarray
    csv_rows: int
    source_sha256: str
    source_size_bytes: int
    heading_ids: tuple
    warnings: list = field(default_factory=list)
    original_ids: tuple = ()

    @property
    def imported_ids(self):
        return self.original_ids or self.ids

    def fly_number(self, index):
        return self.imported_ids.index(self.ids[index]) + 1

    def color(self, index):
        return FLY_COLORS[(self.fly_number(index) - 1) % len(FLY_COLORS)]

    def select_ids(self, included_ids):
        """Project columns without changing source data, identities or frame numbers."""
        chosen = set(included_ids)
        unknown = chosen.difference(self.ids)
        if unknown:
            raise ValueError(f"Unknown AMADEUS IDs: {sorted(unknown)}")
        if chosen == set(self.ids):
            return self
        indices = [i for i, ident in enumerate(self.ids) if ident in chosen]
        values = self.values[:, indices, :]
        values.setflags(write=False)
        return TrackingDataset(self.source_path, tuple(self.ids[i] for i in indices),
                               self.first_frame, values, self.row_present, self.csv_rows,
                               self.source_sha256, self.source_size_bytes,
                               tuple(i for i in self.heading_ids if i in chosen),
                               list(self.warnings), self.imported_ids)

    @property
    def frame_count(self):
        return int(self.values.shape[0])

    @property
    def end_frame(self):
        return self.first_frame + self.frame_count  # exclusive

    @property
    def valid(self):
        return np.isfinite(self.values[:, :, 0]) & np.isfinite(self.values[:, :, 1])

    @property
    def names(self):
        return [f"ID {ident}" for ident in self.ids]

    def row_index(self, frame):
        index = int(frame) - self.first_frame
        return index if 0 <= index < self.frame_count else None

    def position(self, frame, tid):
        index = self.row_index(frame)
        if index is None or not 0 <= tid < len(self.ids):
            return None
        xy = self.values[index, tid, :2]
        return (float(xy[0]), float(xy[1])) if np.isfinite(xy).all() else None

    def legacy_view(self):
        return {"dataset": self, "positions": PositionsView(self), "track_names": self.names,
                "num_frames": self.frame_count, "fps": None, "width": None, "height": None}


class PositionsView:
    """Compatibility view; avoids a large nested dictionary for hour-long videos."""
    def __init__(self, dataset):
        self.dataset = dataset

    def get(self, frame, default=None):
        index = self.dataset.row_index(frame)
        if index is None:
            return {} if default is None else default
        xy = self.dataset.values[index, :, :2]
        return {int(tid): (float(xy[tid, 0]), float(xy[tid, 1]))
                for tid in np.flatnonzero(np.isfinite(xy).all(axis=1))}


def load_amadeus_csv(path, progress=None, cancel=None):
    """Strict wide-CSV loader. Invalid rows are errors, never silently discarded."""
    path = Path(path).expanduser().resolve()
    before = path.stat()
    frame_numbers, chunks = [], []
    count, block_used, block = 0, 0, None
    partial_xy, bad_geometry, bad_heading = 0, 0, 0
    warnings = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            header = [x.strip() for x in next(reader)]
        except StopIteration:
            raise ValueError("The CSV is empty.") from None
        if not header or len(header) != len(set(header)):
            raise ValueError("CSV column names must be nonempty and unique.")
        if any(not x for x in header) or "frame" not in header:
            raise ValueError("CSV needs a 'frame' column and named columns.")
        column = {name: i for i, name in enumerate(header)}
        identified = {int(m.group(1)) for name in header
                      if (m := re.fullmatch(r"(?:cx|cy|w|h|heading)(\d+)", name))}
        ids = tuple(sorted(identified))
        if not ids:
            raise ValueError("No AMADEUS IDs found. Expected cx0, cy0, cx1, cy1, ...")
        if len(ids) > 500:
            raise ValueError("More than 500 identity columns were found. Check the CSV header.")
        for ident in ids:
            if f"cx{ident}" not in column or f"cy{ident}" not in column:
                raise ValueError(f"ID {ident} requires both cx{ident} and cy{ident}.")
        fields = ("cx", "cy", "w", "h", "heading")
        selected = [(column[f"{key}{ident}"], tid, axis, f"{key}{ident}")
                    for tid, ident in enumerate(ids) for axis, key in enumerate(fields)
                    if f"{key}{ident}" in column]
        ignored = [name for name in header if name != "frame"
                   and not re.fullmatch(r"(?:cx|cy|w|h|heading)\d+", name)]
        if ignored:
            warnings.append("Unused columns: " + ", ".join(ignored))
        heading_ids = tuple(ident for ident in ids if f"heading{ident}" in column)
        previous = -1
        for row in reader:
            check_cancel(cancel)
            if not row or all(not x.strip() for x in row):
                continue
            if len(row) != len(header):
                raise ValueError(f"CSV line {reader.line_num}: expected {len(header)} fields, got {len(row)}.")
            frame_text = row[column["frame"]].strip()
            if not re.fullmatch(r"\d+", frame_text):
                raise ValueError(f"CSV line {reader.line_num}: frame must be a nonnegative integer.")
            frame = int(frame_text)
            if frame > np.iinfo(np.int64).max - 1:
                raise ValueError(f"CSV line {reader.line_num}: frame number is too large.")
            if frame <= previous:
                raise ValueError(f"CSV line {reader.line_num}: duplicate or out-of-order frame {frame}.")
            if block is None or block_used == len(block):
                if block is not None:
                    chunks.append(block)
                block = np.full((4096, len(ids), 5), np.nan, dtype=np.float64)
                block_used = 0
            out = block[block_used]
            for col, tid, axis, name in selected:
                text = row[col].strip()
                if not text or text.casefold() in {"nan", "na", "n/a", "null", "none"}:
                    continue
                try:
                    value = float(text)
                except ValueError:
                    raise ValueError(f"CSV line {reader.line_num}, {name}: invalid number {text!r}.") from None
                if not math.isfinite(value):
                    raise ValueError(f"CSV line {reader.line_num}, {name}: infinite values are invalid.")
                if axis < 2 and abs(value) > 500_000_000:
                    raise ValueError(f"CSV line {reader.line_num}, {name}: coordinate magnitude is not compatible with video pixels.")
                out[tid, axis] = value
            finite_xy = np.isfinite(out[:, :2])
            partial = finite_xy.any(axis=1) & ~finite_xy.all(axis=1)
            partial_xy += int(partial.sum())
            # Keep source values untouched. Every consumer uses BOTH cx/cy validity.
            bad_geometry += int((np.isfinite(out[:, 2:4]) & (out[:, 2:4] <= 0)).sum())
            bad_heading += int((np.isfinite(out[:, 4])
                                & ((out[:, 4] < 0) | (out[:, 4] >= 360))).sum())
            frame_numbers.append(frame)
            previous, count, block_used = frame, count + 1, block_used + 1
            if progress and count % 2000 == 0:
                progress(f"Reading tracking CSV: {count:,} rows")
    if not count:
        raise ValueError("The CSV header is present but there are no data rows.")
    chunks.append(block[:block_used])
    origin, span = frame_numbers[0], frame_numbers[-1] - frame_numbers[0] + 1
    estimated = span * len(ids) * 5 * 8
    if estimated > 768 * 1024 * 1024:
        raise ValueError(
            f"Frame span {span:,} would require {estimated / 1024**2:.0f} MB for positions alone. "
            "Check frame numbering or export a shorter analysis interval."
        )
    check_cancel(cancel)
    frames = np.asarray(frame_numbers, dtype=np.int64) - origin
    values = np.full((span, len(ids), 5), np.nan, dtype=np.float64)
    row_present = np.zeros(span, dtype=bool)
    row_present[frames] = True
    start = 0
    for block in chunks:
        check_cancel(cancel)
        values[frames[start:start + len(block)]] = block
        start += len(block)
    if span != count:
        warnings.append(f"{span - count:,} frame rows absent from CSV; retained as missing frames.")
    if partial_xy:
        warnings.append(f"{partial_xy:,} centre pairs have only one coordinate; treated as missing positions.")
    if bad_geometry:
        warnings.append(f"{bad_geometry:,} nonpositive box dimensions; positions retained, invalid boxes not drawn.")
    if bad_heading:
        warnings.append(f"{bad_heading:,} headings outside [0,360); raw values retained, arrows wrapped for display.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            check_cancel(cancel)
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("The input CSV changed while it was loading. Load a stable saved file.")
    values.setflags(write=False)
    row_present.setflags(write=False)
    check_cancel(cancel)
    return TrackingDataset(str(path), ids, origin, values, row_present, count,
                           digest.hexdigest(), int(after.st_size), heading_ids, warnings)


@dataclass(frozen=True)
class AnalysisSettings:
    fps: float
    pixels_per_cm: float | None = None
    dwell_seconds: float = 3.0
    missing_gap_seconds: float = 0.0
    moving_threshold_cm_s: float = 0.2
    jump_threshold_cm: float = 0.5
    trial_start_frame: int = 0
    single_trial: bool = True
    single_target: int = 0
    target_sequence: tuple = tuple(FULL_TARGET_SEQUENCE)
    video_frame_offset: int = 0
    fps_source: str = "manual"

    def __post_init__(self):
        positive_number(self.fps, "Analysis FPS")
        if self.pixels_per_cm is not None:
            positive_number(self.pixels_per_cm, "Pixels per centimetre")
        positive_number(self.dwell_seconds, "Dwell threshold")
        nonnegative_number(self.missing_gap_seconds, "Missing-data tolerance")
        nonnegative_number(self.moving_threshold_cm_s, "Movement threshold")
        positive_number(self.jump_threshold_cm, "Jump threshold")
        if self.missing_gap_seconds >= self.dwell_seconds:
            raise ValueError("Missing-data tolerance must be shorter than the dwell threshold.")
        if not isinstance(self.trial_start_frame, int) or self.trial_start_frame < 0:
            raise ValueError("Trial start must be a nonnegative integer CSV frame.")
        if not isinstance(self.video_frame_offset, int):
            raise ValueError("Video frame offset must be an integer.")
        if self.single_target not in range(4):
            raise ValueError("Choose a target A-D.")
        if len(self.target_sequence) != 10 or any(t not in range(4) for t in self.target_sequence):
            raise ValueError("The full experiment requires ten targets, each A-D.")

    @property
    def dwell_frames(self):
        count = self.dwell_seconds * self.fps
        if not math.isfinite(count):
            raise ValueError("Dwell and FPS produce an invalid frame threshold.")
        return max(1, int(math.ceil(count - 1e-10)))

    @property
    def gap_frames(self):
        # Floor: never tolerate a gap longer than the selected duration.
        count = self.missing_gap_seconds * self.fps
        if not math.isfinite(count):
            raise ValueError("Gap tolerance and FPS produce an invalid frame threshold.")
        return max(0, int(math.floor(count + 1e-10)))


@dataclass
class TrialResult:
    number: int
    target: int
    start: int
    planned_end: int
    available_start: int
    available_end: int
    coverage_status: str
    reach_frames: list
    reach_times: list
    reach_dwell_start_frames: list
    reach_bridged_missing_frames: list
    metrics: list = field(default_factory=list)

    @property
    def available_frames(self):
        return max(0, self.available_end - self.available_start)

    @property
    def team_time(self):
        return max(self.reach_times) if self.reach_times and all(t is not None for t in self.reach_times) else None

    @property
    def mean_time(self):
        return float(np.mean(self.reach_times)) if self.team_time is not None else None


@dataclass
class AnalysisResult:
    dataset: TrackingDataset
    settings: AnalysisSettings
    zones: tuple
    valid: np.ndarray
    assignment: np.ndarray
    cumulative: np.ndarray
    step_px: np.ndarray
    dwell_seconds: np.ndarray
    jump_mask: np.ndarray
    trials: tuple

    def trial_for_frame(self, frame):
        return next((t for t in self.trials if t.start <= frame < t.planned_end), None)

    def occupancy(self, tid, frame, current_trial=True):
        start = self.dataset.first_frame
        if current_trial:
            trial = self.trial_for_frame(frame)
            if trial is None:
                return np.zeros(4)
            start = max(start, trial.start)
        end = min(int(frame) + 1, self.dataset.end_frame)
        if end <= start:
            return np.zeros(4)
        a, b = start - self.dataset.first_frame, end - self.dataset.first_frame
        return (self.cumulative[b, tid] - self.cumulative[a, tid]) / self.settings.fps


def trajectory_frame_bounds(trial, fly_index, at_frame=None):
    """Original CSV frame interval [start, end); include the first success frame.

    A fly that never completes the dwell uses the available trial interval.
    Missing positions remain missing; this helper only selects a frame span.
    The optional preview limit prevents showing future positions during playback.
    """
    if not 0 <= fly_index < len(trial.reach_frames):
        raise ValueError("Fly index is outside this trial's identity list.")
    start, end = trial.available_start, trial.available_end
    reached = trial.reach_frames[fly_index]
    if reached is not None:
        end = min(end, reached + 1)
    if at_frame is not None:
        end = min(end, int(at_frame) + 1)
    return start, max(start, end)


def trajectory_window_row(result, trial, fly_index):
    start, end = trajectory_frame_bounds(trial, fly_index)
    reached = trial.reach_frames[fly_index]
    reason = ("first_target_success" if reached is not None else
              "no_data" if trial.available_frames == 0 else
              "available_partial_trial_end" if trial.coverage_status == "partial" else
              "trial_end_without_observed_success")
    return {"trial": trial.number, "target_letter": BOX_LETTERS[trial.target],
            "fly_number": result.dataset.fly_number(fly_index), "amadeus_id": result.dataset.ids[fly_index],
            "trajectory_start_frame": start, "trajectory_end_frame_exclusive": end,
            "trajectory_stop_reason": reason,
            "target_reach_frame": reached, "target_reach_time_s": trial.reach_times[fly_index]}


def trial_definitions(dataset, settings):
    if settings.single_trial:
        return [(1, settings.single_target, settings.trial_start_frame, dataset.end_frame)]
    return [(i + 1, int(target),
             settings.trial_start_frame + int(math.floor(i * 300 * settings.fps + 0.5)),
             settings.trial_start_frame + int(math.floor((i + 1) * 300 * settings.fps + 0.5)))
            for i, target in enumerate(settings.target_sequence)]


def analyze_tracking(dataset, zones, settings, progress=None, cancel=None):
    """One numerical engine shared by the interface and every export."""
    if not dataset.ids:
        raise ValueError("Select at least one fly for analysis.")
    zones = tuple(zones)
    validate_zones(zones)
    if settings.trial_start_frame >= dataset.end_frame:
        raise ValueError("Trial 1 starts after the end of the tracking CSV.")
    check_cancel(cancel)
    valid = dataset.valid
    nframes, nflies = valid.shape
    assignment = np.full(valid.shape, -1, dtype=np.int8)
    x, y = dataset.values[:, :, 0], dataset.values[:, :, 1]
    # Inclusive rectangle edges. Shared boundaries belong to A, then B, C, D.
    for zi, zone in enumerate(zones):
        belongs = (valid & (assignment == -1) & (x >= zone.x1) & (x <= zone.x2)
                   & (y >= zone.y1) & (y <= zone.y2))
        assignment[belongs] = zi
    cumulative = np.zeros((nframes + 1, nflies, 4), dtype=np.int32)
    for zi in range(4):
        np.cumsum(assignment == zi, axis=0, dtype=np.int32, out=cumulative[1:, :, zi])
    step_px = np.full(valid.shape, np.nan, dtype=np.float64)
    if nframes > 1:
        with np.errstate(invalid="ignore", over="ignore"):
            lengths = np.hypot(np.diff(x, axis=0), np.diff(y, axis=0))
        steps_valid = valid[1:] & valid[:-1]
        if not np.isfinite(lengths[steps_valid]).all():
            raise ValueError("Coordinates produce infinite displacement. Check coordinate magnitudes.")
        step_px[1:] = np.where(steps_valid, lengths, np.nan)
    jump_mask = np.zeros(valid.shape, dtype=bool)
    if settings.pixels_per_cm is not None:
        jump_mask = step_px / settings.pixels_per_cm > settings.jump_threshold_cm
    dwell_values = np.full(valid.shape, np.nan, dtype=np.float64)
    trials = []
    required, gap_limit = settings.dwell_frames, settings.gap_frames
    definitions = trial_definitions(dataset, settings)
    for number, target, start, planned_end in definitions:
        check_cancel(cancel)
        a = max(start, dataset.first_frame)
        b = min(planned_end, dataset.end_frame)
        if b <= a:
            a = min(max(start, dataset.first_frame), dataset.end_frame)
            b = a
            coverage = "no_data"
        else:
            coverage = "complete" if a == start and b == planned_end else "partial"
        trial = TrialResult(number, target, start, planned_end, a, b, coverage,
                            [None] * nflies, [None] * nflies, [None] * nflies, [None] * nflies)
        ia, ib = a - dataset.first_frame, b - dataset.first_frame
        for tid in range(nflies):
            run, pending, bridged, dwell_start = 0, 0, 0, None
            for idx in range(ia, ib):
                if idx % 4096 == 0:
                    check_cancel(cancel)
                frame = dataset.first_frame + idx
                if assignment[idx, tid] == target:
                    if run == 0:
                        dwell_start = frame
                    run += pending + 1
                    bridged += pending
                    pending = 0
                    dwell_values[idx, tid] = run / settings.fps
                    if trial.reach_frames[tid] is None and run >= required:
                        trial.reach_frames[tid] = frame
                        trial.reach_times[tid] = (frame - start + 1) / settings.fps
                        trial.reach_dwell_start_frames[tid] = dwell_start
                        trial.reach_bridged_missing_frames[tid] = bridged
                elif not valid[idx, tid] and run > 0 and pending < gap_limit:
                    pending += 1
                    # Unobserved positions never appear as confirmed current dwell.
                else:
                    run, pending, bridged, dwell_start = 0, 0, 0, None
                    if valid[idx, tid]:
                        dwell_values[idx, tid] = 0.0
            v = valid[ia:ib, tid]
            tracked = int(v.sum())
            steps = step_px[ia:ib, tid].copy()
            if steps.size:
                steps[0] = np.nan  # No step crosses the trial's available start.
            distances = steps[np.isfinite(steps)]
            count = int(distances.size)
            path_px = float(distances.sum()) if count else (0.0 if tracked else None)
            scale = settings.pixels_per_cm
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                speeds = distances / scale * settings.fps if scale is not None else np.array([])
            if speeds.size and not np.isfinite(speeds).all():
                raise ValueError("FPS or physical scale produces nonfinite speed. Check the numerical settings.")
            if tracked:
                local = np.flatnonzero(v)
                first, last = int(local[0] + ia), int(local[-1] + ia)
                displacement_px = float(np.hypot(x[last, tid] - x[first, tid], y[last, tid] - y[first, tid]))
                first_frame, last_frame = first + dataset.first_frame, last + dataset.first_frame
            else:
                displacement_px = first_frame = last_frame = None
            reached = trial.reach_frames[tid] is not None
            outcome = ("reached" if reached else "not_reached" if coverage == "complete"
                       else "no_data" if coverage == "no_data" else "not_observed_in_available_data")
            occupancy = ((cumulative[ib, tid] - cumulative[ia, tid]) / settings.fps).tolist()
            trial.metrics.append({
                "trial": number, "target_letter": BOX_LETTERS[target], "fly_number": dataset.fly_number(tid),
                "amadeus_id": dataset.ids[tid], "coverage_status": coverage, "reach_status": outcome,
                "trial_start_frame": start, "planned_end_frame_exclusive": planned_end,
                "available_start_frame": a, "available_end_frame_exclusive": b,
                "actual_trial_duration_s": (b - a) / settings.fps,
                "valid_frames": tracked, "missing_frames": (b - a) - tracked,
                "tracking_coverage_pct": tracked / (b - a) * 100 if b > a else None,
                "valid_step_count": count, "valid_step_duration_s": count / settings.fps,
                "path_length_px": path_px,
                "path_length_cm": path_px / scale if path_px is not None and scale is not None else None,
                "displacement_cm": displacement_px / scale if displacement_px is not None and scale is not None else None,
                "mean_speed_cm_s_tracked": float(speeds.mean()) if speeds.size else None,
                "median_speed_cm_s": float(np.median(speeds)) if speeds.size else None,
                "max_speed_cm_s": float(speeds.max()) if speeds.size else None,
                "trial_averaged_speed_cm_s": path_px / scale / ((b - a) / settings.fps)
                    if path_px is not None and scale is not None and b > a else None,
                "time_moving_s_tracked": int((speeds > settings.moving_threshold_cm_s).sum()) / settings.fps
                    if speeds.size else None,
                "time_moving_pct_tracked": float((speeds > settings.moving_threshold_cm_s).mean() * 100)
                    if speeds.size else None,
                "moving_threshold_cm_s": settings.moving_threshold_cm_s,
                "first_tracked_frame": first_frame, "last_tracked_frame": last_frame,
                **{f"occupancy_{letter}_s": occupancy[i] for i, letter in enumerate(BOX_LETTERS)},
                "target_occupancy_s": occupancy[target], "target_reach_frame": trial.reach_frames[tid],
                "target_reach_time_s": trial.reach_times[tid],
                "target_dwell_start_frame": trial.reach_dwell_start_frames[tid],
                "reach_bridged_missing_frames": trial.reach_bridged_missing_frames[tid],
                "flagged_jump_steps": int((distances / scale > settings.jump_threshold_cm).sum())
                    if scale is not None else None,
            })
        trials.append(trial)
        if progress:
            progress(f"Analyzing trial {number}/{len(definitions)}")
    if not any(t.available_frames for t in trials):
        raise ValueError("None of the scheduled trials overlaps the CSV frame span. Check Trial 1 start.")
    check_cancel(cancel)
    for array in (valid, assignment, cumulative, step_px, dwell_values, jump_mask):
        array.setflags(write=False)
    return AnalysisResult(dataset, settings, zones, valid, assignment, cumulative,
                          step_px, dwell_values, jump_mask, tuple(trials))


def mean_present(values):
    values = [v for v in values if v is not None and math.isfinite(float(v))]
    return float(np.mean(values)) if values else None


def trial_summary(result, trial):
    settings = result.settings
    return {
        "trial": trial.number, "target_letter": BOX_LETTERS[trial.target],
        "coverage_status": trial.coverage_status, "start_frame": trial.start,
        "planned_end_frame_exclusive": trial.planned_end,
        "available_start_frame": trial.available_start, "available_end_frame_exclusive": trial.available_end,
        "actual_duration_s": trial.available_frames / settings.fps,
        "planned_duration_s": 300 if not settings.single_trial else (trial.planned_end - trial.start) / settings.fps,
        "quantized_frame_span_duration_s": (trial.planned_end - trial.start) / settings.fps,
        "team_size": len(result.dataset.ids), "team_found": trial.team_time is not None,
        "team_time_to_target_s": trial.team_time, "mean_time_to_target_s_all_flies": trial.mean_time,
        "flies_reached": sum(v is not None for v in trial.reach_times),
        "mean_path_length_cm": mean_present(m["path_length_cm"] for m in trial.metrics),
        "mean_tracked_speed_cm_s": mean_present(m["mean_speed_cm_s_tracked"] for m in trial.metrics),
        "mean_time_moving_pct_tracked": mean_present(m["time_moving_pct_tracked"] for m in trial.metrics),
        "mean_tracking_coverage_pct": mean_present(m["tracking_coverage_pct"] for m in trial.metrics),
        "total_flagged_jump_steps": sum(m["flagged_jump_steps"] or 0 for m in trial.metrics),
        "analysis_fps": settings.fps, "pixels_per_cm": settings.pixels_per_cm,
        "dwell_threshold_s": settings.dwell_seconds, "dwell_threshold_frames": settings.dwell_frames,
        "missing_gap_tolerance_s": settings.missing_gap_seconds,
        "missing_gap_tolerance_frames": settings.gap_frames,
    }


def iter_jump_events(result):
    for index, tid in zip(*np.nonzero(result.jump_mask)):
        frame = int(index) + result.dataset.first_frame
        trial = result.trial_for_frame(frame)
        # Cross-trial steps are excluded from per-trial movement metrics.
        included = trial is not None and frame > trial.available_start
        yield {"csv_frame": frame, "previous_csv_frame": frame - 1,
               "video_frame": frame - result.settings.video_frame_offset,
               "fly_number": result.dataset.fly_number(int(tid)), "amadeus_id": result.dataset.ids[int(tid)],
               "trial": trial.number if trial else None,
               "included_in_trial_movement": included,
               "step_distance_cm": float(result.step_px[index, tid] / result.settings.pixels_per_cm),
               "speed_cm_s": float(result.step_px[index, tid] / result.settings.pixels_per_cm * result.settings.fps),
               "jump_threshold_cm": result.settings.jump_threshold_cm}


def json_clean(obj):
    """JSON null, never nonstandard NaN or Infinity."""
    if isinstance(obj, dict):
        return {str(k): json_clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_clean(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if math.isfinite(float(obj)) else None
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def metadata_for(result, video_info=None):
    return json_clean({
        "app_version": APP_VERSION, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_csv": result.dataset.source_path, "input_csv_sha256": result.dataset.source_sha256,
        "input_csv_size_bytes": result.dataset.source_size_bytes,
        "csv_rows": result.dataset.csv_rows, "first_csv_frame": result.dataset.first_frame,
        "last_csv_frame": result.dataset.end_frame - 1, "frame_span": result.dataset.frame_count,
        "absent_csv_frame_rows": result.dataset.frame_count - result.dataset.csv_rows,
        "import_warnings": result.dataset.warnings, "settings": asdict(result.settings),
        "effective_dwell_frames": result.settings.dwell_frames,
        "effective_gap_tolerance_frames": result.settings.gap_frames,
        "fly_selection": {"imported_ids": result.dataset.imported_ids,
                          "included_ids": result.dataset.ids,
                          "excluded_ids": [i for i in result.dataset.imported_ids if i not in result.dataset.ids],
                          "included_count": len(result.dataset.ids)},
        "identity_mapping": [{"fly_number": result.dataset.fly_number(i), "amadeus_id": ident}
                             for i, ident in enumerate(result.dataset.ids)],
        "trajectory_windows": [trajectory_window_row(result, trial, tid)
                               for trial in result.trials for tid in range(len(result.dataset.ids))],
        "zones": [z.as_dict() for z in result.zones], "video": video_info or {},
        "definitions": {
            "frame_numbering": "Original zero-based CSV frame numbers are preserved.",
            "video_alignment": "video_frame = csv_frame - video_frame_offset; temporal offset only.",
            "sample_timing": "Each frame represents one 1/FPS occupancy interval. Success is recorded at interval completion.",
            "target_reach_time_s": "(qualifying_csv_frame - trial_start_frame + 1) / FPS.",
            "target_success": "First completed dwell; movement inside the target is allowed. Outside observations reset dwell.",
            "success_requires_stationarity": False,
            "plotted_trajectories": "Each fly's path starts at the available trial start and includes its first completed-dwell frame, then stops. Flies without observed success use the available trial end. Missing positions break the path; paths never cross trial boundaries.",
            "live_playback": "The main GUI follows current fly positions after success. REACHED and recorded success times remain set. Exported trajectory paths still stop at first success.",
            "video_trajectories": "In exported MP4s with analysis active, each fly's trail and endpoint marker freeze at that fly's first success within the current trial. The trail-length setting selects the last N frames of that stopped path. The next trial starts a new path.",
            "movement_metric_scope": "Full available trial, including frames after first success; the trajectory cutoff affects plotted paths only.",
            "missing_data": "No interpolation. Short gaps count toward dwell only after the same ID reappears inside the target. Pending gaps never trigger success.",
            "gap_limit": "floor(tolerance_seconds * FPS), allowing only floating-point rounding tolerance.",
            "team_time": "Maximum first qualifying reach time, available only when every included ID succeeds.",
            "all_fly_mean": "Arithmetic mean of first qualifying reach times, available only when all included IDs succeed.",
            "regions": "OBB centre in inclusive rectangle; shared boundaries assigned A then B then C then D. Area overlap prohibited.",
            "occupancy": "Count of observed valid positions inside each region divided by FPS; missing positions contribute zero observed occupancy.",
            "path_length": "Sum of Euclidean distances between consecutive valid frames inside the same available trial. No cross-trial or gap-spanning steps.",
            "mean_speed_cm_s_tracked": "Mean of valid consecutive-frame speeds; equivalent to path length / valid step duration.",
            "trial_averaged_speed_cm_s": "Path length divided by the available trial frame span / FPS. Missing steps make this a lower observed-motion estimate.",
            "time_moving_pct_tracked": "100 * count(valid step speed > moving threshold) / valid step count. Missing intervals excluded.",
            "tracking_coverage_pct": "100 * valid position frames / available trial frame span.",
            "jump_flags": "Consecutive-frame distance > selected cm threshold. Review only; flagged positions remain in all results.",
            "coordinate_cm": "Input-video top-left origin; x right and y down. Coordinates divided by px/cm.",
            "heading_deg": "AMADEUS heading: 0 up, increasing clockwise. Optional; unused by numerical analysis.",
            "trial_boundaries": "Full experiment: start0 + floor(i * 300 * FPS + 0.5); avoids cumulative rounding drift.",
            "partial_trials": "Only the CSV's available frame span is analyzed. Missing scheduled portions are not classified as observed failure.",
            "empty_values": "Blank CSV fields / JSON null mean unavailable, never zero completion time.",
            "precision": "float64 calculation and unrounded CSV values. Labels and JPEG plots are rounded for display only.",
        },
        "trials": [trial_summary(result, t) for t in result.trials],
    })


def write_dict_csv(path, rows, fieldnames=None, cancel=None):
    iterator = iter(rows)
    first = next(iterator, None)
    if fieldnames is None:
        if first is None:
            raise ValueError("Cannot infer columns for an empty table.")
        fieldnames = list(first)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        if first is not None:
            writer.writerow(json_clean(first))
        for count, row in enumerate(iterator):
            if count % 1000 == 0:
                check_cancel(cancel)
            writer.writerow(json_clean(row))


def iter_framewise_rows(result, cancel=None):
    data, settings = result.dataset, result.settings
    scale = settings.pixels_per_cm
    for trial in result.trials:
        for frame in range(trial.available_start, trial.available_end):
            if frame % 512 == 0:
                check_cancel(cancel)
            idx = frame - data.first_frame
            for tid, ident in enumerate(data.ids):
                vals = data.values[idx, tid]
                observed = bool(result.valid[idx, tid])
                step = result.step_px[idx, tid] if frame > trial.available_start else np.nan
                distance_cm = float(step / scale) if scale is not None and np.isfinite(step) else None
                zone = int(result.assignment[idx, tid])
                yield {
                    "trial": trial.number, "target_letter": BOX_LETTERS[trial.target],
                    "csv_frame": frame, "video_frame": frame - settings.video_frame_offset,
                    "trial_time_s": (frame - trial.start) / settings.fps,
                    "frame_interval_end_trial_time_s": (frame - trial.start + 1) / settings.fps,
                    "fly_number": data.fly_number(tid), "amadeus_id": ident,
                    "csv_row_present": bool(data.row_present[idx]), "tracking_valid": observed,
                    "cx_px": float(vals[0]) if np.isfinite(vals[0]) else None,
                    "cy_px": float(vals[1]) if np.isfinite(vals[1]) else None,
                    "x_cm": float(vals[0] / scale) if scale is not None and observed else None,
                    "y_cm": float(vals[1] / scale) if scale is not None and observed else None,
                    "width_px": float(vals[2]) if np.isfinite(vals[2]) else None,
                    "height_px": float(vals[3]) if np.isfinite(vals[3]) else None,
                    "heading_deg": float(vals[4]) if np.isfinite(vals[4]) else None,
                    "step_distance_cm": distance_cm,
                    "speed_cm_s": distance_cm * settings.fps if distance_cm is not None else None,
                    "moving": distance_cm * settings.fps > settings.moving_threshold_cm_s
                        if distance_cm is not None else None,
                    "zone_letter": BOX_LETTERS[zone] if zone >= 0 else None,
                    "in_target": zone == trial.target if observed else None,
                    "current_confirmed_dwell_s": float(result.dwell_seconds[idx, tid])
                        if np.isfinite(result.dwell_seconds[idx, tid]) else None,
                    "flagged_jump_step": bool(result.jump_mask[idx, tid]) if np.isfinite(step) else False,
                }


def atomic_json(path, obj):
    path = Path(path)
    temp = path.with_name(path.name + f".tmp-{time.time_ns()}")
    try:
        temp.write_text(json.dumps(json_clean(obj), indent=2, allow_nan=False), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def decode_video_frame(cap, index):
    if index < 0:
        raise ValueError("Mapped video frame is negative. Check the video frame offset.")
    current = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if not math.isfinite(current) or abs(current - index) > 0.25:
        if not cap.set(cv2.CAP_PROP_POS_FRAMES, int(index)):
            raise ValueError(f"Video decoder cannot seek to frame {index:,}.")
    ok, frame = cap.read()
    if not ok or frame is None:
        raise ValueError(f"Could not decode video frame {index:,}. Export stopped rather than skipping a frame.")
    reported = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if math.isfinite(reported) and reported > 0 and abs(reported - (index + 1)) > 0.5:
        raise ValueError(f"Decoder returned a different frame near {index:,}. Check the video encoding.")
    return frame



BG = "#171717"


PANEL = "#202020"


PANEL_2 = "#262626"


BORDER = "#343434"


TEXT = "#ededed"


MUTED = "#a0a0a0"


ACCENT = "#6aa5d7"


GOOD = "#72b58d"


WARN = "#d4a85a"


BAD = "#d97878"


FONT_UI = "Segoe UI"


FONT_MONO = "Cascadia Mono"


BOX_BGR = [
    (80, 110, 255),
    (255, 160, 70),
    (100, 220, 100),
    (220, 160, 60),
]


FLY_COLORS = [
    (80, 90, 255), (60, 180, 255), (80, 230, 255), (80, 220, 110),
    (230, 120, 255), (255, 180, 70), (200, 100, 255), (80, 220, 200),
    (255, 230, 80), (170, 200, 255), (120, 255, 130), (255, 130, 180),
]


PLOT_BG_BGR = (38, 38, 38)


PLOT_GRID_BGR = (61, 61, 61)


PLOT_TEXT_BGR = (205, 205, 205)


PLOT_MUTED_BGR = (145, 145, 145)


PLOT_ACCENT_BGR = (215, 165, 106)


PLOT_GOOD_BGR = (141, 181, 114)


PLOT_WARN_BGR = (90, 168, 212)


GOOD_BGR = (80, 210, 90)


class ZoneDrawWindow(tk.Toplevel):
    """Edit named regions on independently decoded reference video frames."""
    def __init__(self, parent, frame_bgr, existing=None, on_done=None,
                 video_path=None, initial_video_frame=0, video_frame_offset=0):
        super().__init__(parent)
        self.parent, self.on_done = parent, on_done
        self.title("Draw / edit cool boxes")
        self.configure(bg=BG)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.cap = None
        self.seek_after_id = None
        self._updating_scale = False
        self.video_frame_offset = video_frame_offset
        self.frame_bgr = frame_bgr
        self.h, self.w = frame_bgr.shape[:2]
        self.video_frame_count = 1
        self.video_fps = 0.0
        self.video_frame = 0
        self.zones = {i: z for i, z in enumerate((existing or [])[:4])}
        self.selected_box = tk.IntVar(value=0)
        self.start = self.rect_id = None
        if video_path:
            self.cap = cv2.VideoCapture(str(video_path))
            if not self.cap.isOpened():
                self.destroy()
                raise ValueError("Could not open the video for reference-frame browsing.")
            self.video_frame_count = max(1, int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.video_fps = float(self.cap.get(cv2.CAP_PROP_FPS))
            self.video_frame = min(max(int(initial_video_frame), 0), self.video_frame_count - 1)
        # Leave room for the side panel and the always-visible frame controls.
        sw = max(320, parent.winfo_screenwidth() - 340)
        sh = max(220, parent.winfo_screenheight() - 220)
        self.scale = min(sw / self.w, sh / self.h, 1.0)
        self.disp_w, self.disp_h = max(1, round(self.w * self.scale)), max(1, round(self.h * self.scale))
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(12, 5))
        self.canvas = tk.Canvas(body, width=self.disp_w, height=self.disp_h, bg="black",
                                highlightthickness=0)
        self.canvas.pack(side="left")
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        side = tk.Frame(body, bg=PANEL, width=270, height=max(self.disp_h, 410))
        side.pack(side="left", fill="y", padx=(12, 0))
        side.pack_propagate(False)
        tk.Label(side, text="Choose a box, then drag", font=(FONT_UI, 13, "bold"),
                 fg=TEXT, bg=PANEL).pack(anchor="w", padx=12, pady=(12, 6))
        tk.Label(side, text="Draw A-D in any order. Drawing again replaces the selected box. Boxes stay fixed while you browse frames.",
                 font=(FONT_UI, 9), fg=MUTED, bg=PANEL, wraplength=240,
                 justify="left").pack(anchor="w", padx=12, pady=(0, 10))
        self.labels = []
        for i, name in enumerate(BOX_NAMES):
            button = tk.Radiobutton(side, text=name, variable=self.selected_box, value=i,
                                    command=self._select_box, bg=PANEL, fg=TEXT,
                                    selectcolor=PANEL_2, activebackground=PANEL,
                                    activeforeground=TEXT, anchor="w", font=(FONT_UI, 10, "bold"))
            button.pack(fill="x", padx=12, pady=3)
            self.labels.append(button)
        tk.Button(side, text="Delete selected box", command=self._delete_selected,
                  bg=PANEL_2, fg=TEXT, relief="flat").pack(fill="x", padx=12, pady=(8, 0))
        self.status = tk.Label(side, font=(FONT_UI, 9), bg=PANEL, fg=ACCENT,
                               wraplength=240, justify="left")
        self.status.pack(anchor="w", padx=12, pady=10)
        btns = tk.Frame(side, bg=PANEL)
        btns.pack(side="bottom", fill="x", padx=12, pady=12)
        tk.Button(btns, text="Clear all", command=self._clear, bg=PANEL_2, fg=TEXT,
                  relief="flat").pack(side="left", padx=(0, 5))
        tk.Button(btns, text="Cancel", command=self.destroy, bg=PANEL_2, fg=TEXT,
                  relief="flat").pack(side="left", padx=5)
        self.save_btn = tk.Button(btns, text="Use Boxes", command=self._save, bg=ACCENT,
                                  fg=BG, relief="flat", font=(FONT_UI, 9, "bold"))
        self.save_btn.pack(side="right")
        nav = tk.Frame(self, bg=PANEL)
        nav.pack(fill="x", padx=12, pady=(0, 12))
        self.frame_scale = tk.Scale(nav, from_=0, to=self.video_frame_count - 1,
                                    orient="horizontal", showvalue=False, command=self._seek,
                                    bg=PANEL, fg=TEXT, troughcolor=BORDER, highlightthickness=0)
        self.frame_scale.pack(fill="x", padx=8)
        controls = tk.Frame(nav, bg=PANEL)
        controls.pack(fill="x", padx=8, pady=(0, 6))
        self.nav_buttons = []
        jump = max(1, round(self.video_fps)) if math.isfinite(self.video_fps) else 1
        for text, delta in (("-1 s", -jump), ("< Frame", -1), ("Frame >", 1), ("+1 s", jump)):
            button = tk.Button(controls, text=text, command=lambda d=delta: self.set_video_frame(self.video_frame + d),
                               bg=PANEL_2, fg=TEXT, relief="flat")
            button.pack(side="left", padx=2)
            self.nav_buttons.append(button)
        tk.Label(controls, text="Video frame", bg=PANEL, fg=MUTED).pack(side="left", padx=(10, 3))
        self.frame_var = tk.StringVar(value=str(self.video_frame))
        self.frame_entry = tk.Entry(controls, textvariable=self.frame_var, width=9,
                                    bg=PANEL_2, fg=TEXT, insertbackground=TEXT)
        self.frame_entry.pack(side="left")
        self.frame_entry.bind("<Return>", self._go_to_frame)
        go = tk.Button(controls, text="Go", command=self._go_to_frame, bg=PANEL_2, fg=TEXT, relief="flat")
        go.pack(side="left", padx=4)
        self.nav_buttons.append(go)
        self.frame_info = tk.Label(nav, bg=PANEL, fg=MUTED, anchor="w", font=(FONT_UI, 9))
        self.frame_info.pack(fill="x", padx=10, pady=(0, 6))
        self.bind("<Left>", lambda e: self._step_key(-1))
        self.bind("<Right>", lambda e: self._step_key(1))
        self.bind("<Escape>", lambda e: self.destroy())
        if self.cap is None:
            for widget in [self.frame_scale, self.frame_entry, *self.nav_buttons]:
                widget.configure(state="disabled")
        self._set_image(frame_bgr)
        self._sync_frame_controls()
        self._redraw()
        self.grab_set()

    def _set_image(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((self.disp_w, self.disp_h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(pil)
        self.frame_bgr = frame

    def _sync_frame_controls(self):
        self._updating_scale = True
        try:
            self.frame_scale.set(self.video_frame)
            self.frame_var.set(str(self.video_frame))
        finally:
            self._updating_scale = False
        if self.cap is None:
            text = "Still reference image; load a video to browse frames."
        else:
            seconds = f" | {self.video_frame / self.video_fps:.3f} s" if self.video_fps > 0 else ""
            text = (f"Video frame {self.video_frame:,} / {self.video_frame_count - 1:,}{seconds}"
                    f" | CSV frame {self.video_frame + self.video_frame_offset:,} | zero-based")
        self.frame_info.configure(text=text)

    def _cancel_seek(self):
        if self.seek_after_id is not None:
            self.after_cancel(self.seek_after_id)
            self.seek_after_id = None

    def _seek(self, value):
        frame = int(float(value))
        if self._updating_scale or self.cap is None or frame == self.video_frame:
            return
        self._cancel_seek()
        self.seek_after_id = self.after(70, lambda: self.set_video_frame(frame))

    def set_video_frame(self, frame):
        self._cancel_seek()
        if self.cap is None:
            return
        frame = min(max(int(frame), 0), self.video_frame_count - 1)
        if frame == self.video_frame:
            self._sync_frame_controls()
            return
        self.start = self.rect_id = None
        try:
            image = decode_video_frame(self.cap, frame)
            if image.shape[:2] != (self.h, self.w):
                raise ValueError("Reference frame dimensions differ from the box coordinate system.")
        except Exception as exc:
            self._sync_frame_controls()
            self._redraw()
            self.status.configure(text=f"Could not read frame {frame}: {exc}", fg=WARN)
            return
        self.video_frame = frame
        self._set_image(image)
        self._sync_frame_controls()
        self._redraw()

    def _go_to_frame(self, event=None):
        try:
            frame = integer_number(self.frame_var.get(), "Video frame")
            if not 0 <= frame < self.video_frame_count:
                raise ValueError(f"Choose a video frame from 0 to {self.video_frame_count - 1}.")
            self.set_video_frame(frame)
        except ValueError as exc:
            self.status.configure(text=str(exc), fg=WARN)
        return "break"

    def _step_key(self, delta):
        if isinstance(self.focus_get(), (tk.Entry, ttk.Entry)):
            return
        self.set_video_frame(self.video_frame + delta)
        return "break"

    def _select_box(self):
        self.start = self.rect_id = None
        self._redraw()

    def _press(self, e):
        self._cancel_seek()
        self._sync_frame_controls()
        self.start = (min(max(e.x, 0), self.disp_w), min(max(e.y, 0), self.disp_h))
        self._redraw()
        color = BOX_BGR[self.selected_box.get()]
        rgbhex = "#%02x%02x%02x" % (color[2], color[1], color[0])
        self.rect_id = self.canvas.create_rectangle(*self.start, *self.start, outline=rgbhex, width=3)

    def _drag(self, e):
        if self.start is not None and self.rect_id is not None:
            self.canvas.coords(self.rect_id, *self.start,
                               min(max(e.x, 0), self.disp_w), min(max(e.y, 0), self.disp_h))

    def _release(self, e):
        if self.start is None:
            return
        x0, y0 = self.start
        x1, y1 = min(max(e.x, 0), self.disp_w), min(max(e.y, 0), self.disp_h)
        self.start = self.rect_id = None
        if abs(x1 - x0) >= 6 and abs(y1 - y0) >= 6:
            index = self.selected_box.get()
            self.zones[index] = Zone(BOX_NAMES[index], x0 * self.w / self.disp_w, y0 * self.h / self.disp_h,
                                     x1 * self.w / self.disp_w, y1 * self.h / self.disp_h)
        self._redraw()

    def _delete_selected(self):
        self.zones.pop(self.selected_box.get(), None)
        self.start = self.rect_id = None
        self._redraw()

    def _clear(self):
        self.zones.clear()
        self.start = self.rect_id = None
        self._redraw()

    def _redraw(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        current = self.selected_box.get()
        for i, label in enumerate(self.labels):
            label.configure(text=f"{BOX_NAMES[i]}: {'set' if i in self.zones else 'not set'}")
        for i, z in sorted(self.zones.items()):
            color = BOX_BGR[i]
            rgbhex = "#%02x%02x%02x" % (color[2], color[1], color[0])
            x1, y1 = z.x1 * self.disp_w / self.w, z.y1 * self.disp_h / self.h
            self.canvas.create_rectangle(x1, y1, z.x2 * self.disp_w / self.w, z.y2 * self.disp_h / self.h,
                                         outline=rgbhex, width=4 if i == current else 2)
            self.canvas.create_text(x1 + 6, y1 + 6, anchor="nw", text=f"Box {BOX_LETTERS[i]}",
                                    fill="white", font=(FONT_UI, 12, "bold"))
        verb = "Redraw / replace" if current in self.zones else "Draw"
        self.status.configure(text=f"{verb} {BOX_NAMES[current]}. {len(self.zones)}/4 boxes set.", fg=ACCENT)
        self.save_btn.configure(state="normal" if len(self.zones) == 4 else "disabled")

    def _save(self):
        if len(self.zones) != 4:
            return
        zones = [self.zones[i] for i in range(4)]
        try:
            validate_zones(zones, (self.w, self.h))
        except ValueError as exc:
            self.status.configure(text=str(exc), fg=WARN)
            return
        callback = self.on_done
        self.destroy()
        if callback:
            callback(zones)

    def destroy(self):
        self._cancel_seek()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        super().destroy()


def _plot_canvas(width, height):
    return np.full((max(1, int(height)), max(1, int(width)), 3), PLOT_BG_BGR, dtype=np.uint8)


def _axis_box(img, left=34, right=8, top=7, bottom=24):
    h, w = img.shape[:2]
    x0, x1 = left, max(left + 10, w - right)
    y0, y1 = top, max(top + 10, h - bottom)
    for frac in (0.0, 0.5, 1.0):
        y = int(y1 - frac * (y1 - y0))
        cv2.line(img, (x0, y), (x1, y), PLOT_GRID_BGR, 1, cv2.LINE_AA)
    return x0, y0, x1, y1


def _small_text(img, text, x, y, color=PLOT_MUTED_BGR, scale=0.34, align='left'):
    text = str(text)
    if align == 'center':
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0]
        x -= tw // 2
    elif align == 'right':
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0]
        x -= tw
    cv2.putText(img, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def draw_compact_bars(width, height, values, labels, colors=None, missing=None, suffix='s', reference=None):
    img = _plot_canvas(width, height)
    x0, y0, x1, y1 = _axis_box(img)
    vals = [None if v is None else max(0.0, float(v)) for v in values]
    finite = [v for v in vals if v is not None]
    vmax = max(max(finite, default=0.0), float(reference or 0.0), 1.0)
    _small_text(img, f'{vmax:.1f}', x0 - 4, y0 + 4, align='right')
    _small_text(img, '0', x0 - 4, y1 + 4, align='right')
    if reference is not None and 0 <= float(reference) <= vmax:
        ry = int(y1 - (float(reference) / vmax) * (y1 - y0))
        cv2.line(img, (x0, ry), (x1, ry), PLOT_WARN_BGR, 1, cv2.LINE_AA)
        _small_text(img, f'{float(reference):.1f}', x1 - 2, max(y0 + 9, ry - 3), PLOT_WARN_BGR, 0.30, 'right')
    n = max(1, len(vals))
    slot = (x1 - x0) / n
    bw = max(4, min(28, int(slot * 0.58)))
    for i, v in enumerate(vals):
        cx = int(x0 + (i + 0.5) * slot)
        label = labels[i] if i < len(labels) else str(i + 1)
        _small_text(img, label, cx, y1 + 15, align='center', scale=0.31)
        is_missing = bool(missing[i]) if missing is not None and i < len(missing) else v is None
        if is_missing or v is None:
            cv2.rectangle(img, (cx - bw // 2, y1 - 5), (cx + bw // 2, y1), PLOT_GRID_BGR, 1)
            continue
        bh = max(1, int((v / vmax) * max(1, y1 - y0)))
        top = y1 - bh
        color = (colors[i % len(colors)] if colors else PLOT_ACCENT_BGR)
        cv2.rectangle(img, (cx - bw // 2, top), (cx + bw // 2, y1), color, -1)
        if len(vals) <= 6:
            _small_text(img, f'{v:.1f}', cx, max(y0 + 10, top - 3), PLOT_TEXT_BGR, 0.31, 'center')
    if suffix:
        _small_text(img, suffix, x1, 11, align='right', scale=0.30)
    return img


def draw_compact_line(width, height, xs, ys, x_max=None, y_max=None, current_x=None,
                      x_suffix='s', y_integer=False, color=PLOT_ACCENT_BGR):
    img = _plot_canvas(width, height)
    x0, y0, x1, y1 = _axis_box(img)
    pairs = [(float(x), float(y)) for x, y in zip(xs, ys) if x is not None and y is not None]
    if not pairs:
        _small_text(img, 'No data yet', (x0 + x1)//2, (y0 + y1)//2, PLOT_MUTED_BGR, 0.38, 'center')
        return img
    xmax = max(float(x_max or 0), max(x for x, _ in pairs), 1.0)
    ymax = max(float(y_max or 0), max(y for _, y in pairs), 1.0)
    _small_text(img, f'{int(ymax) if y_integer else ymax:.0f}' if y_integer else f'{ymax:.1f}', x0 - 4, y0 + 4, align='right')
    _small_text(img, '0', x0 - 4, y1 + 4, align='right')
    _small_text(img, '0', x0, y1 + 15, align='center', scale=0.30)
    _small_text(img, f'{xmax:.0f}{x_suffix}', x1, y1 + 15, align='right', scale=0.30)
    pts = []
    for x, y in pairs:
        px = int(x0 + (x / xmax) * (x1 - x0))
        py = int(y1 - (y / ymax) * (y1 - y0))
        pts.append((px, py))
    for a, b in zip(pts[:-1], pts[1:]):
        cv2.line(img, a, b, color, 2, cv2.LINE_AA)
    for pt in pts:
        cv2.circle(img, pt, 2, color, -1, cv2.LINE_AA)
    if current_x is not None:
        cx = int(x0 + min(max(float(current_x), 0.0), xmax) / xmax * (x1 - x0))
        cv2.line(img, (cx, y0), (cx, y1), PLOT_WARN_BGR, 1, cv2.LINE_AA)
    return img


def draw_step_progress(width, height, reach_times, current_time, nflies):
    valid = sorted(float(t) for t in reach_times if t is not None)
    xs, ys = [0.0], [0.0]
    count = 0
    for t in valid:
        xs.extend([t, t])
        ys.extend([count, count + 1])
        count += 1
    xmax = max(float(current_time or 0), max(valid, default=0.0), 1.0)
    return draw_compact_line(width, height, xs, ys, x_max=xmax, y_max=max(1, nflies),
                             current_x=current_time, x_suffix='s', y_integer=True, color=PLOT_GOOD_BGR)


HELP_TEXT = """1. Load the AMADEUS result CSV, preferably the reviewed/refined result.
2. Load the exact video used by AMADEUS. Keep its crop, resolution and frames.
3. Check FPS. A manual FPS override changes time calculations and MP4 timing.
4. Set scale in px/cm. For a 20 cm arena: measured pixel diameter / 20.
   Example only: 916 pixels / 20 cm = 45.8 px/cm; use your actual video scale.
5. Draw or load the four cool boxes. In the editor select A, B, C or D in any
   order, then drag to draw/replace it. Delete selected box removes only that
   region. Browse the full video using the slider, frame buttons or frame entry;
   boxes retain their original-video coordinates across reference frames.
   Use Boxes applies all four regions; Cancel discards edits.
6. Choose single trial or the full 10 x 5 min experiment and its target order.
7. Trial 1 start uses the original, zero-based CSV frame number.
8. Video frame = CSV frame - Video offset. Default 0 for the same input video.
9. Select/deselect IDs under Flies included in analysis. All/None changes all
   checkboxes. At least one fly must be selected. Recalculate after changing
   selection, a numerical setting or a box. The Fly dropdown only changes the view.
10. Review jump flags, missing data and coverage before exporting.

Success time is recorded when the required dwell finishes. Movement within
the target is allowed: the fly never has to stand still. Leaving the target
resets the continuous in-box timer. Team time is the last individual first-success time;
the included flies do not need to be inside together. The all-fly average is blank
until all included IDs succeed. Team size is the number of selected IDs.
Excluded flies are omitted from calculations, plots, jump review and exports.
Original fly numbers, AMADEUS IDs and colors are retained. Export metadata
records included/excluded IDs. Reloading a CSV selects all its flies again.

Every plotted path includes that fly's first qualifying success frame and
stops there, independently of the other flies. Main playback continues following
each fly after success, with REACHED shown at its current location. Exported
MP4 paths and endpoint markers freeze at success and restart at the next trial. A fly without observed
success is plotted through the available trial end; missing positions break
the path. Choose export -> Separate trajectory for every fly saves one JPEG
per fly per trial under fly_tracks. All-flies trajectory plots use the same
per-fly cutoffs. Movement metrics still cover the full available trial.

Gap 0 is the default: strict observed continuity. A positive tolerance bridges a missing
gap only if the same ID reappears in that target, within the selected limit.
Missing observations never establish a success by themselves. Occupancy
counts observed positions only. Movement calculations never bridge gaps or
trial boundaries. Time-moving % uses valid movement intervals only.

Jump flags do not repair or exclude data. Correct errors in AMADEUS, save
a revised CSV, then reload/recalculate. The movement threshold (default
0.2 cm/s) and jump threshold (default 0.5 cm/frame) are editable review
settings, not automatically calibrated biological limits.

The GUI can analyze a CSV with saved boxes and an explicit FPS without a
video. That mode cannot verify spatial/video alignment. Partial trials are
labelled, and unavailable results remain blank rather than zero.

Choose export creates a new timestamped subfolder; completed outputs are
published together. CSV numbers are unrounded; plots use rounded labels.
Export MP4 covers the loaded CSV frame span, at the analysis FPS.

PowerShell setup:
  py -m pip install numpy opencv-python pillow
  py fly_target_time_gui_amadeus.py
Numerical checks:
  py fly_target_time_gui_amadeus.py --self-test
"""


def audit_columns(result):
    s = result.settings
    return {"input_csv_sha256": result.dataset.source_sha256,
            "included_amadeus_ids": ";".join(map(str, result.dataset.ids)),
            "excluded_amadeus_ids": ";".join(str(i) for i in result.dataset.imported_ids if i not in result.dataset.ids),
            "included_fly_count": len(result.dataset.ids),
            "analysis_fps": s.fps, "pixels_per_cm": s.pixels_per_cm,
            "dwell_threshold_s": s.dwell_seconds, "missing_gap_tolerance_s": s.missing_gap_seconds,
            "moving_threshold_cm_s": s.moving_threshold_cm_s, "jump_threshold_cm": s.jump_threshold_cm,
            "video_frame_offset": s.video_frame_offset}


def audited_rows(result, rows):
    audit = audit_columns(result)
    for row in rows:
        yield {**row, **audit}


def draw_track_trail(image, positions, track_id, frame_idx, trail_frames, color, start_frame=None):
    dataset = positions.dataset
    first = max(dataset.first_frame, int(frame_idx) - max(1, int(trail_frames)) + 1)
    if start_frame is not None:
        first = max(first, int(start_frame))
    end = min(int(frame_idx) + 1, dataset.end_frame)
    if end <= first:
        return 0
    xy = dataset.values[first - dataset.first_frame:end - dataset.first_frame, track_id, :2]
    good = np.isfinite(xy).all(axis=1)
    previous = None
    for index in range(len(xy)):
        if not good[index]:
            previous = None
            continue
        point = tuple(int(round(v)) for v in xy[index])
        strength = 0.4 + 0.6 * index / max(1, len(xy) - 1)
        shade = tuple(int(channel * strength) for channel in color)
        if previous is not None:
            cv2.line(image, previous, point, (12, 12, 12), 5, cv2.LINE_AA)
            cv2.line(image, previous, point, shade, 3, cv2.LINE_AA)
        cv2.circle(image, point, 3, shade, -1, cv2.LINE_AA)
        previous = point
    return int(good.sum())


def render_annotation(frame, dataset, result, zones, csv_frame, show_all=True, show_boxes=True,
                      show_heading=False, trail_frames=30, selected_fly=0, stop_at_success=True):
    """Pure renderer: no Tk calls, safe for the export worker."""
    out = frame.copy()
    h, w = out.shape[:2]
    trial = result.trial_for_frame(csv_frame) if result else None
    target = trial.target if trial else None
    if show_boxes:
        for i, z in enumerate(zones):
            color = BOX_BGR[i]
            cv2.rectangle(out, (round(z.x1), round(z.y1)), (round(z.x2), round(z.y2)), color, 4 if i == target else 2)
            cv2.putText(out, f"BOX {BOX_LETTERS[i]}" + (" TARGET" if i == target else ""),
                        (round(z.x1) + 5, round(z.y1) + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    if dataset:
        tids = range(len(dataset.ids)) if show_all else [selected_fly]
        view = PositionsView(dataset)
        for tid in tids:
            if not 0 <= tid < len(dataset.ids):
                continue
            color = dataset.color(tid)
            display_frame = csv_frame
            if trial:
                if stop_at_success:
                    start, end = trajectory_frame_bounds(trial, tid, at_frame=csv_frame)
                else:
                    start, end = trial.available_start, min(csv_frame + 1, trial.available_end)
                if end <= start:
                    continue
                display_frame = end - 1
                draw_track_trail(out, view, tid, display_frame, trail_frames, color, start_frame=start)
            elif result is None:
                draw_track_trail(out, view, tid, csv_frame, trail_frames, color)
            # Keep the position and heading aligned with the displayed trail endpoint.
            point = dataset.position(display_frame, tid)
            if point is None:
                continue
            x, y = (int(round(v)) for v in point)
            cv2.circle(out, (x, y), 5, color, -1, cv2.LINE_AA)
            cv2.circle(out, (x, y), 9, (245, 245, 245), 1, cv2.LINE_AA)
            cv2.putText(out, f"ID {dataset.ids[tid]}", (x + 11, y - 7), cv2.FONT_HERSHEY_SIMPLEX,
                        0.44, color, 1, cv2.LINE_AA)
            display_index = dataset.row_index(display_frame)
            if show_heading and display_index is not None:
                width, height, heading = dataset.values[display_index, tid, 2:5]
                if np.isfinite(heading):
                    length = max(15.0, max(width, height) / 2 if np.isfinite(width) and np.isfinite(height) and min(width, height) > 0 else 15.0)
                    angle = math.radians(float(heading) % 360)
                    tip = (round(x + math.sin(angle) * length), round(y - math.cos(angle) * length))
                    cv2.arrowedLine(out, (x, y), tip, color, 2, cv2.LINE_AA, tipLength=0.3)
            if trial and trial.reach_frames[tid] is not None and trial.reach_frames[tid] <= csv_frame:
                cv2.putText(out, "REACHED", (x + 11, y + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GOOD_BGR, 1, cv2.LINE_AA)
            if result and display_index is not None and result.jump_mask[display_index, tid]:
                cv2.circle(out, (x, y), 15, (80, 80, 255), 2, cv2.LINE_AA)
                cv2.putText(out, "JUMP", (x + 11, y + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (80, 80, 255), 1, cv2.LINE_AA)
    if result:
        if trial:
            reached = sum(f is not None and f <= csv_frame for f in trial.reach_frames)
            found = trial.team_time is not None and all(f <= csv_frame for f in trial.reach_frames)
            elapsed = trial.team_time if found else (csv_frame - trial.start + 1) / result.settings.fps
            text = f"Trial {trial.number} | {'TEAM FOUND' if found else 'SEARCHING'} | {elapsed:.2f}s | {reached}/{len(dataset.ids)} | {trial.coverage_status.upper()}"
            color = GOOD_BGR if found else (70, 205, 255)
        else:
            text = "BEFORE TRIAL 1" if csv_frame < result.trials[0].start else "AFTER SCHEDULED TRIALS"
            color = (170, 170, 170)
    else:
        text, color = "AMADEUS positions | Recalculate to apply analysis settings", (170, 170, 170)
    scale = min(0.59, max(0.28, w / 2100))
    cv2.rectangle(out, (6, 6), (max(7, min(w - 6, 1050)), min(h - 1, 40)), (22, 22, 22), -1)
    cv2.putText(out, text, (12, 29), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
    return out


def save_jpeg(path, image):
    path = Path(path)
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not ok:
        raise OSError(f"Could not encode JPEG {path.name}.")
    encoded.tofile(str(path))  # Works with non-ASCII Windows paths.
    if not path.is_file() or not path.stat().st_size:
        raise OSError(f"JPEG was not written: {path.name}.")


def draw_trajectory_path(image, xy, color, y_offset=0, reached=False):
    """Draw consecutive observed runs only; missing positions break the path."""
    if not len(xy):
        return
    good = np.isfinite(xy).all(axis=1)
    boundaries = np.flatnonzero(np.diff(np.r_[False, good, False]))
    for start, end in zip(boundaries[::2], boundaries[1::2]):
        points = np.rint(xy[start:end]).astype(np.int32)
        points[:, 1] += y_offset
        if len(points) > 1:
            cv2.polylines(image, [points.reshape(-1, 1, 2)], False, (10, 10, 10), 4, cv2.LINE_AA)
            cv2.polylines(image, [points.reshape(-1, 1, 2)], False, color, 2, cv2.LINE_AA)
        else:
            cv2.circle(image, tuple(points[0]), 2, color, -1, cv2.LINE_AA)
    valid_indices = np.flatnonzero(good)
    if valid_indices.size:
        first = np.rint(xy[valid_indices[0]]).astype(int)
        last = np.rint(xy[valid_indices[-1]]).astype(int)
        cv2.circle(image, (int(first[0]), int(first[1]) + y_offset), 6, (240, 240, 240), 1, cv2.LINE_AA)
        cv2.circle(image, (int(last[0]), int(last[1]) + y_offset), 5, color, -1, cv2.LINE_AA)
        if reached:
            cv2.putText(image, "REACHED", (int(last[0]) + 8, int(last[1]) + y_offset - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, .4, GOOD_BGR, 1, cv2.LINE_AA)


def draw_trial_trajectory(result, trial, background, fly_index=None):
    """All flies, or one original identity, with a separate cutoff for each fly."""
    if fly_index is not None:
        trajectory_frame_bounds(trial, fly_index)  # Validate before indexing IDs.
    count = len(result.dataset.ids) if fly_index is None else 1
    cols = min(5, max(1, background.shape[1] // 150))
    header = max(144, 100 + math.ceil(count / cols) * 24)
    return draw_trial_trajectory_with_header(result, trial, background, header, fly_index)


def draw_trial_trajectory_with_header(result, trial, background, header, fly_index=None):
    h, w = background.shape[:2]
    out = np.full((h + header, w, 3), 28, np.uint8)
    out[header:] = np.clip(background.astype(np.float32) * 0.32, 0, 255).astype(np.uint8)
    trial_label = "Trial" if result.settings.single_trial else f"Trial {trial.number}"
    if fly_index is None:
        tids = list(range(len(result.dataset.ids)))
        title = f"{trial_label} | Target {BOX_LETTERS[trial.target]} | Each path stops at first success | {trial.coverage_status.upper()}"
        span_text = (f"CSV {trial.available_start}-{trial.available_end - 1}; each fly uses its own success cutoff"
                     if trial.available_frames else "NO AVAILABLE TRIAL DATA")
    else:
        tids = [fly_index]
        start, end = trajectory_frame_bounds(trial, fly_index)
        success = trial.reach_times[fly_index]
        status = (f"REACHED at {success:.3f}s" if success is not None else
                  "NO DATA" if not trial.available_frames else
                  "SUCCESS NOT OBSERVED (PARTIAL)" if trial.coverage_status == "partial" else
                  "NOT REACHED")
        title = f"{trial_label} | Fly {result.dataset.fly_number(fly_index)} / ID {result.dataset.ids[fly_index]} | Target {BOX_LETTERS[trial.target]} | {status}"
        span_text = (f"Plotted CSV {start}-{end - 1} (inclusive) | {trial.coverage_status.upper()} coverage"
                     if end > start else "NO AVAILABLE TRIAL DATA")
    cv2.putText(out, title, (14, 27), cv2.FONT_HERSHEY_SIMPLEX, max(0.32, min(0.65, w / 1500)), (235, 235, 235), 1, cv2.LINE_AA)
    small_font = max(.24, min(.44, w / 2400))
    cv2.putText(out, f"Continuous time inside target >= {result.settings.dwell_seconds:g}s; movement allowed. Start: hollow circle; end: filled circle.",
                (14, 51), cv2.FONT_HERSHEY_SIMPLEX, small_font, (195, 195, 195), 1, cv2.LINE_AA)
    cv2.putText(out, span_text, (14, 74), cv2.FONT_HERSHEY_SIMPLEX, small_font, (175, 175, 175), 1, cv2.LINE_AA)
    cols = min(5, max(1, w // 150))
    for slot, tid in enumerate(tids):
        ident = result.dataset.ids[tid]
        color = result.dataset.color(tid)
        lx, ly = 14 + (slot % cols) * (w // cols), 100 + (slot // cols) * 24
        cv2.circle(out, (lx + 4, ly - 5), 4, color, -1, cv2.LINE_AA)
        cv2.putText(out, f"F{result.dataset.fly_number(tid)} / ID {ident}", (lx + 14, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
    for i, zone in enumerate(result.zones):
        color = BOX_BGR[i]
        cv2.rectangle(out, (round(zone.x1), round(zone.y1) + header),
                      (round(zone.x2), round(zone.y2) + header), color, 3 if i == trial.target else 1)
        cv2.putText(out, BOX_LETTERS[i] + (" TARGET" if i == trial.target else ""),
                    (round(zone.x1) + 4, round(zone.y1) + header + 19), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1, cv2.LINE_AA)
    for tid in tids:
        start, end = trajectory_frame_bounds(trial, tid)
        a, b = start - result.dataset.first_frame, end - result.dataset.first_frame
        xy = result.dataset.values[a:b, tid, :2]
        color = result.dataset.color(tid)
        draw_trajectory_path(out, xy, color, y_offset=header, reached=trial.reach_frames[tid] is not None)
    return out


def draw_time_to_target(result, trial):
    w, h = 1100, 630
    out = np.full((h, w, 3), 32, dtype=np.uint8)
    x0, x1, y0, y1 = 82, w - 32, 112, h - 114
    ymax = 300.0
    times = [t for t in trial.reach_times if t is not None]
    if result.settings.single_trial and times and max(times) > ymax:
        ymax = math.ceil(max(times) / 60) * 60
    title = f"{'Trial' if result.settings.single_trial else f'Trial {trial.number}'} | Target {BOX_LETTERS[trial.target]} | Time to target"
    cv2.putText(out, title, (22, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.76, (235, 235, 235), 2, cv2.LINE_AA)
    subtitle = f"Dwell >= {result.settings.dwell_seconds:g} s | {trial.coverage_status.upper()} coverage | {trial.available_frames / result.settings.fps:.2f}s available"
    cv2.putText(out, subtitle, (22, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.47, (170, 170, 170), 1, cv2.LINE_AA)
    cv2.putText(out, "seconds", (15, 101), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)
    for i in range(6):
        yy = y1 - round((y1 - y0) * i / 5)
        cv2.line(out, (x0, yy), (x1, yy), (62, 62, 62), 1, cv2.LINE_AA)
        cv2.putText(out, f"{ymax * i / 5:g}", (17, yy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.line(out, (x0, y0), (x0, y1), (165, 165, 165), 1)
    cv2.line(out, (x0, y1), (x1, y1), (165, 165, 165), 1)
    slot = (x1 - x0) / len(result.dataset.ids)
    for tid, ident in enumerate(result.dataset.ids):
        cx = round(x0 + slot * (tid + 0.5))
        half = max(6, round(slot * 0.29))
        color = result.dataset.color(tid)
        value = trial.reach_times[tid]
        if value is None:
            code = "NR" if trial.coverage_status == "complete" else "ND" if trial.coverage_status == "no_data" else "UNK"
            top = y1 - 18
            cv2.rectangle(out, (cx - half, top), (cx + half, y1), color, 1)
            cv2.line(out, (cx - half, top), (cx + half, y1), color, 1)
            cv2.line(out, (cx + half, top), (cx - half, y1), color, 1)
            text = code
        else:
            top = y1 - round(min(value, ymax) / ymax * (y1 - y0))
            cv2.rectangle(out, (cx - half, top), (cx + half, y1), color, -1)
            text = f"{value:.2f}"
        _small_text(out, text, cx, max(y0 + 12, top - 9), color, 0.4, "center")
        _small_text(out, f"F{result.dataset.fly_number(tid)}", cx, y1 + 22, color, 0.45, "center")
        _small_text(out, f"ID {ident}", cx, y1 + 43, color, 0.37, "center")
    if trial.team_time is not None:
        text = f"Team {trial.team_time:.2f}s | All-fly average {trial.mean_time:.2f}s"
        cv2.putText(out, text, (x0 + 8, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 220, 255), 1, cv2.LINE_AA)
        for value, color in ((trial.team_time, (235, 235, 235)), (trial.mean_time, (100, 220, 255))):
            yy = y1 - round(min(value, ymax) / ymax * (y1 - y0))
            for xx in range(x0, x1, 20):
                cv2.line(out, (xx, yy), (min(xx + 11, x1), yy), color, 1, cv2.LINE_AA)
    else:
        cv2.putText(out, "Team completion unavailable", (x0 + 8, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 180, 255), 1, cv2.LINE_AA)
    footer = "NR = not reached in a complete trial; UNK = not observed in partial data; ND = no data"
    cv2.putText(out, footer, (x0, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.41, (170, 170, 170), 1, cv2.LINE_AA)
    return out


def draw_team_summary(result):
    w, h = 1180, 620
    out = np.full((h, w, 3), 32, np.uint8)
    x0, x1, y0, y1 = 82, w - 28, 105, h - 107
    ymax = 300.0
    if result.settings.single_trial and result.trials[0].team_time is not None:
        ymax = max(ymax, math.ceil(result.trials[0].team_time / 60) * 60)
    cv2.putText(out, "Team completion and all-fly average by trial", (22, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.putText(out, "Bar: last fly's first success. Yellow marker: mean first success of all included IDs.",
                (22, 63), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (100, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(out, "seconds", (15, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (170, 170, 170), 1, cv2.LINE_AA)
    for i in range(6):
        yy = y1 - round((y1 - y0) * i / 5)
        cv2.line(out, (x0, yy), (x1, yy), (65, 65, 65), 1)
        cv2.putText(out, f"{ymax * i / 5:g}", (17, yy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (175, 175, 175), 1, cv2.LINE_AA)
    slot = (x1 - x0) / len(result.trials)
    for i, t in enumerate(result.trials):
        cx = round(x0 + slot * (i + 0.5))
        half = max(7, round(slot * 0.28))
        color = BOX_BGR[t.target]
        if t.team_time is not None:
            top = y1 - round(min(t.team_time, ymax) / ymax * (y1 - y0))
            cv2.rectangle(out, (cx - half, top), (cx + half, y1), color, -1)
            yy = y1 - round(min(t.mean_time, ymax) / ymax * (y1 - y0))
            cv2.line(out, (cx - half - 4, yy), (cx + half + 4, yy), (100, 220, 255), 3, cv2.LINE_AA)
            text = f"{t.team_time:.1f}"
        else:
            top = y1 - 20
            cv2.rectangle(out, (cx - half, top), (cx + half, y1), color, 1)
            cv2.line(out, (cx - half, top), (cx + half, y1), color, 1)
            text = "NR" if t.coverage_status == "complete" else "ND" if t.coverage_status == "no_data" else "UNK"
        _small_text(out, text, cx, max(y0 + 12, top - 8), color, 0.42, "center")
        _small_text(out, "Trial" if result.settings.single_trial else str(t.number), cx, y1 + 24, color, 0.43, "center")
        _small_text(out, BOX_LETTERS[t.target] + (" *" if t.coverage_status == "partial" else ""), cx, y1 + 45, color, 0.38, "center")
    cv2.putText(out, "NR: incomplete team in complete data; UNK: partial data; ND: no data; *: partial coverage",
                (x0, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (175, 175, 175), 1, cv2.LINE_AA)
    return out


def tile_images(images, columns=2, tile_width=840):
    """One panel remains one panel. No empty right column for a single trial."""
    if not images:
        raise ValueError("No plot panels to combine.")
    columns = min(columns, len(images))
    heights = [round(img.shape[0] * tile_width / img.shape[1]) for img in images]
    tile_height = max(heights)
    output = np.full((math.ceil(len(images) / columns) * tile_height, columns * tile_width, 3), 25, np.uint8)
    for i, img in enumerate(images):
        resized = cv2.resize(img, (tile_width, heights[i]), interpolation=cv2.INTER_AREA)
        r, c = divmod(i, columns)
        output[r * tile_height:r * tile_height + heights[i], c * tile_width:(c + 1) * tile_width] = resized
    return output


@dataclass(frozen=True)
class ExportSnapshot:
    result: AnalysisResult
    video_info: dict
    options: dict
    canvas_size: tuple
    fallback_background: np.ndarray | None = None


def write_analysis_package(parent, snapshot, progress=None, cancel=None):
    """Stage selected outputs in a new folder; rename only after successful completion."""
    parent = Path(parent).expanduser().resolve()
    if not parent.is_dir():
        raise ValueError("Choose an existing output parent folder.")
    result, options = snapshot.result, snapshot.options
    stage = Path(tempfile.mkdtemp(prefix=".amadeus_partial_", dir=parent))
    created_rows = {}
    cap = None
    try:
        check_cancel(cancel)
        if options.get("per_fly_metrics_csv"):
            rows = [m for t in result.trials for m in t.metrics]
            write_dict_csv(stage / "per_fly_trial_metrics.csv", audited_rows(result, rows), cancel=cancel)
            created_rows["per_fly_trial_metrics.csv"] = len(rows)
        if options.get("trial_summary_csv"):
            rows = [trial_summary(result, t) for t in result.trials]
            write_dict_csv(stage / "trial_summary.csv", audited_rows(result, rows), cancel=cancel)
            created_rows["trial_summary.csv"] = len(rows)
        if options.get("framewise_csv"):
            if progress:
                progress("Writing unrounded framewise CSV; long experiments can produce a large file")
            write_dict_csv(stage / "framewise_tracks.csv", audited_rows(result, iter_framewise_rows(result, cancel)), cancel=cancel)
            created_rows["framewise_tracks.csv"] = sum(t.available_frames for t in result.trials) * len(result.dataset.ids)
        if options.get("fly_color_key_csv"):
            rows = []
            for i, ident in enumerate(result.dataset.ids):
                b, g, r = result.dataset.color(i)
                rows.append({"fly_number": result.dataset.fly_number(i), "amadeus_id": ident, "red": r, "green": g, "blue": b,
                             "hex_color": f"#{r:02X}{g:02X}{b:02X}"})
            write_dict_csv(stage / "fly_color_key.csv", audited_rows(result, rows), cancel=cancel)
            created_rows["fly_color_key.csv"] = len(rows)
        if options.get("jump_review_csv"):
            fields = ["csv_frame", "previous_csv_frame", "video_frame", "fly_number", "amadeus_id", "trial",
                      "included_in_trial_movement", "step_distance_cm", "speed_cm_s", "jump_threshold_cm"] + list(audit_columns(result))
            fields = list(dict.fromkeys(fields))
            write_dict_csv(stage / "jump_review.csv", audited_rows(result, iter_jump_events(result)), fields, cancel)
            created_rows["jump_review.csv"] = int(result.jump_mask.sum())
        need_all_tracks = options.get("individual_track_plots") or options.get("combined_track_plot")
        need_tracks = need_all_tracks or options.get("per_fly_track_plots")
        need_targets = options.get("individual_target_plots") or options.get("combined_target_plot")
        if options.get("individual_track_plots"):
            (stage / "trial_tracks").mkdir()
        if options.get("per_fly_track_plots"):
            (stage / "fly_tracks").mkdir()
        if options.get("individual_target_plots"):
            (stage / "time_to_target_plots").mkdir()
        if need_tracks and snapshot.video_info.get("path"):
            cap = cv2.VideoCapture(snapshot.video_info["path"])
            if not cap.isOpened():
                raise ValueError("Could not reopen the video to generate trajectory backgrounds.")
        tracks, targets = [], []
        for trial in result.trials:
            check_cancel(cancel)
            if progress:
                progress(f"Exporting selected plots: trial {trial.number}/{len(result.trials)}")
            if need_tracks:
                w, h = snapshot.canvas_size
                background = np.zeros((h, w, 3), dtype=np.uint8)
                if cap is not None and trial.available_frames:
                    background = decode_video_frame(cap, trial.available_start - result.settings.video_frame_offset)
                elif snapshot.fallback_background is not None:
                    background = snapshot.fallback_background
                if need_all_tracks:
                    image = draw_trial_trajectory(result, trial, background)
                    if options.get("individual_track_plots"):
                        save_jpeg(stage / "trial_tracks" / f"trial_{trial.number:02d}_target_{BOX_LETTERS[trial.target]}_tracks.jpg", image)
                    if options.get("combined_track_plot"):
                        # Keep preview-sized panels, not ten full-resolution frames.
                        height = round(image.shape[0] * 840 / image.shape[1])
                        tracks.append(cv2.resize(image, (840, height), interpolation=cv2.INTER_AREA))
                if options.get("per_fly_track_plots"):
                    folder = stage / "fly_tracks" / f"trial_{trial.number:02d}_target_{BOX_LETTERS[trial.target]}"
                    folder.mkdir()
                    for tid, ident in enumerate(result.dataset.ids):
                        check_cancel(cancel)
                        if progress:
                            progress(f"Trial {trial.number}: exporting fly {tid + 1}/{len(result.dataset.ids)} (ID {ident})")
                        image = draw_trial_trajectory(result, trial, background, fly_index=tid)
                        save_jpeg(folder / f"fly_{result.dataset.fly_number(tid):02d}_amadeus_id_{ident}.jpg", image)
            if need_targets:
                image = draw_time_to_target(result, trial)
                if options.get("individual_target_plots"):
                    save_jpeg(stage / "time_to_target_plots" / f"trial_{trial.number:02d}_target_{BOX_LETTERS[trial.target]}_time_to_target.jpg", image)
                if options.get("combined_target_plot"):
                    targets.append(image)
        if options.get("combined_track_plot"):
            save_jpeg(stage / "all_trials_tracks.jpg", tile_images(tracks))
        if options.get("combined_target_plot"):
            save_jpeg(stage / "all_trials_time_to_target.jpg", tile_images(targets))
        if options.get("trial_time_summary_plot"):
            save_jpeg(stage / "team_time_to_target_by_trial.jpg", draw_team_summary(result))
        if options.get("readme_txt"):
            (stage / "READ_ME.txt").write_text(HELP_TEXT + "\n\nINPUT CSV:\n" + result.dataset.source_path
                                              + "\nSHA-256: " + result.dataset.source_sha256 + "\n", encoding="utf-8")
        if options.get("analysis_metadata_json"):
            metadata = metadata_for(result, snapshot.video_info)
            metadata["selected_outputs"] = options
            metadata["exported_table_row_counts"] = created_rows
            metadata["output_files"] = []
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    check_cancel(cancel)
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        while chunk := stream.read(1024 * 1024):
                            check_cancel(cancel)
                            digest.update(chunk)
                    metadata["output_files"].append({"name": str(path.relative_to(stage)),
                                                     "size_bytes": path.stat().st_size,
                                                     "sha256": digest.hexdigest()})
            (stage / "analysis_metadata.json").write_text(json.dumps(json_clean(metadata), indent=2, allow_nan=False), encoding="utf-8")
        if not any(stage.iterdir()):
            raise ValueError("No export options were selected.")
        check_cancel(cancel)
        base = "amadeus_analysis_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        final = parent / base
        suffix = 1
        while final.exists():
            final = parent / f"{base}_{suffix}"
            suffix += 1
        stage.rename(final)
        return str(final)
    finally:
        if cap is not None:
            cap.release()
        if stage.exists():
            shutil.rmtree(stage)


def write_validation_video(path, input_video, result, params, progress=None, cancel=None):
    target = Path(path)
    if target.resolve() == Path(input_video).resolve():
        raise ValueError("Output cannot overwrite the input video.")
    if target.resolve() == Path(result.dataset.source_path).resolve():
        raise ValueError("Output cannot overwrite the input tracking CSV.")
    handle, temp_path = tempfile.mkstemp(prefix=".amadeus_video_", suffix=".mp4", dir=target.parent)
    os.close(handle)
    temp = Path(temp_path)
    cap = writer = None
    try:
        cap = cv2.VideoCapture(str(input_video))
        if not cap.isOpened():
            raise ValueError("Could not open input video for export.")
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = result.dataset.frame_count
        start = result.dataset.first_frame - result.settings.video_frame_offset
        input_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if start < 0 or start + total > input_count:
            raise ValueError("CSV frame span cannot be mapped entirely into this video. Check the frame offset.")
        if w % 2 or h % 2:
            raise ValueError("MP4 encoding needs even image dimensions. Use an AVI/input export with even dimensions; do not silently crop scientific video.")
        writer = cv2.VideoWriter(str(temp), cv2.VideoWriter_fourcc(*"mp4v"), result.settings.fps, (w, h))
        if not writer.isOpened():
            raise ValueError("Could not initialize MP4 encoder. Try a local writable folder.")
        for row in range(total):
            check_cancel(cancel)
            frame = decode_video_frame(cap, start + row)
            image = render_annotation(frame, result.dataset, result, result.zones,
                                      result.dataset.first_frame + row, *params)
            writer.write(image)
            if progress and (row % 100 == 0 or row + 1 == total):
                progress(f"Rendering MP4: {row + 1:,}/{total:,} frames")
        writer.release()
        writer = None
        cap.release()
        cap = None
        check_cancel(cancel)
        verification = cv2.VideoCapture(str(temp))
        try:
            if not verification.isOpened():
                raise ValueError("Encoded MP4 could not be reopened for verification.")
            actual = int(verification.get(cv2.CAP_PROP_FRAME_COUNT))
            out_fps = float(verification.get(cv2.CAP_PROP_FPS))
            out_w, out_h = int(verification.get(cv2.CAP_PROP_FRAME_WIDTH)), int(verification.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual != total or (out_w, out_h) != (w, h) or abs(out_fps - result.settings.fps) > 0.01:
                raise ValueError("MP4 frame count, dimensions or FPS failed verification. No completed video was saved.")
            decode_video_frame(verification, 0)
            decode_video_frame(verification, total - 1)
        finally:
            verification.release()
        check_cancel(cancel)
        os.replace(temp, target)
        return str(target)
    finally:
        if writer is not None:
            writer.release()
        if cap is not None:
            cap.release()
        temp.unlink(missing_ok=True)



class TargetTimeApp:
    def __init__(self, root):
        self.root = root
        root.title("AMADEUS Fly Target Analysis")
        root.configure(bg=BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{min(1600, max(1180, sw - 60))}x{min(1000, max(720, sh - 80))}")
        root.minsize(1120, 720)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.csv_path = self.video_path = self.zone_path = None
        self.data = self.dataset = self.result = self.source_dataset = None
        self.fly_inclusion_vars = {}
        self.zones = []
        self.cap = self.current_bgr = None
        self.current_frame = self.video_frame_count = 0
        self.video_width = self.video_height = 0
        self.video_fps = self.analysis_fps = None
        self.playing = False
        self.timer_id = self.seek_after_id = self.resize_after_id = None
        self._updating_scale = self._closed = self._closing = False
        self._suppress_settings = False
        self.last_display_image = self.video_image_id = None
        self.selected_fly = 0
        self.trail_frames = 30
        self.threshold_seconds, self.missing_gap_seconds = 3.0, 0.0
        self.target_box, self.single_trial = 0, True
        self.target_sequence = list(FULL_TARGET_SEQUENCE)
        self.trial_start_user = 0
        self.analysis_ready = False
        self.fly_target_reach_frame = {}
        self.fly_target_reach_time = {}
        self.team_time_to_target = {}
        self.mean_time_to_target = {}
        self.busy = False
        self.export_cancel = threading.Event()
        self.job_messages = queue.Queue()
        self._job_callback = None
        self._disabled_widgets = []
        self.build_ui()
        for var in (self.threshold_var, self.fps_override_var, self.trial_start_frame_var,
                    self.seq_var, self.px_per_cm_var, self.missing_gap_var,
                    self.offset_var, self.moving_var, self.jump_var):
            var.trace_add("write", self._settings_changed)
        self.root.after(60, self._poll_jobs)

    def build_ui(self):
        self._configure_ttk()

        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=16, pady=(8, 3))
        tk.Label(top, text="AMADEUS fly target analysis", font=(FONT_UI, 17, "bold"),
                 fg=TEXT, bg=BG).pack(side="left")
        self.status = tk.Label(top, text="Load AMADEUS CSV and the matching video", fg=MUTED,
                               bg=BG, font=(FONT_UI, 9), anchor="w")
        self.status.pack(side="left", padx=16, fill="x", expand=True)

        files = tk.LabelFrame(self.root, text=" Files ", bg=PANEL, fg=MUTED,
                              font=(FONT_UI, 9, "bold"), bd=1, relief="solid")
        files.pack(fill="x", padx=16, pady=3)
        self._file_row(files, "AMADEUS", "Choose CSV", self.pick_csv, "csv_var")
        self._file_row(files, "Video", "Choose video", self.pick_video, "video_var")
        self._file_row(files, "Cool boxes", "Draw / load", self.draw_or_load_boxes, "box_var_path")

        setup = tk.LabelFrame(self.root, text=" Analysis settings ", bg=PANEL, fg=MUTED,
                              font=(FONT_UI, 9, "bold"), bd=1, relief="solid")
        setup.pack(fill="x", padx=16, pady=3)

        row1 = tk.Frame(setup, bg=PANEL)
        row1.pack(fill="x", padx=10, pady=(4, 2))
        self._field_label(row1, "Mode")
        self.mode_var = tk.StringVar(value="Single clip / single trial")
        self.mode_combo = ttk.Combobox(row1, textvariable=self.mode_var, state="readonly", width=24,
                                       values=["Single clip / single trial", "Full 10-trial experiment"])
        self.mode_combo.pack(side="left", padx=(4, 12))
        self.mode_combo.bind("<<ComboboxSelected>>", self.mode_changed)

        self._field_label(row1, "Target")
        self.target_var = tk.StringVar(value=BOX_NAMES[0])
        self.target_combo = ttk.Combobox(row1, textvariable=self.target_var, state="readonly", width=12,
                                         values=BOX_NAMES)
        self.target_combo.current(0)
        self.target_combo.pack(side="left", padx=(4, 12))
        self.target_combo.bind("<<ComboboxSelected>>", self.target_changed)

        self._field_label(row1, "Inside target")
        self.threshold_var = tk.StringVar(value="3.0")
        self._entry(row1, self.threshold_var, width=6).pack(side="left", padx=(4, 3))
        tk.Label(row1, text="s (movement allowed)", bg=PANEL, fg=MUTED, font=(FONT_UI, 9)).pack(side="left", padx=(0, 12))

        self._field_label(row1, "FPS")
        self.fps_override_var = tk.StringVar(value="")
        self._entry(row1, self.fps_override_var, width=7).pack(side="left", padx=(4, 4))
        tk.Label(row1, text="auto if blank", bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left")

        row2 = tk.Frame(setup, bg=PANEL)
        row2.pack(fill="x", padx=10, pady=3)
        self._field_label(row2, "Trial 1 start (CSV)")
        self.trial_start_frame_var = tk.StringVar(value="0")
        self.trial_start_entry = self._entry(row2, self.trial_start_frame_var, width=9)
        self.trial_start_entry.pack(side="left", padx=(4, 4))
        self.use_current_btn = self._button(row2, "Use current", self.set_start_current)
        self.use_current_btn.pack(side="left", padx=(0, 12))

        self._field_label(row2, "Trail")
        self.trail_var = tk.StringVar(value="30")
        self.trail_entry = self._entry(row2, self.trail_var, width=6)
        self.trail_entry.pack(side="left", padx=(4, 3))
        self.trail_entry.bind("<Return>", lambda e: self.refresh_frame())
        self.trail_entry.bind("<FocusOut>", lambda e: self.refresh_frame())
        tk.Label(row2, text="frames", bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left", padx=(0, 12))

        self._field_label(row2, "Fly")
        self.fly_combo = ttk.Combobox(row2, state="readonly", values=[], width=20)
        self.fly_combo.pack(side="left", padx=(4, 10))
        self.fly_combo.bind("<<ComboboxSelected>>", self.fly_changed)

        self.all_var = tk.BooleanVar(value=True)
        self._check(row2, "all flies", self.all_var, self.refresh_frame).pack(side="left", padx=4)
        self.heading_var = tk.BooleanVar(value=False)
        self._check(row2, "heading arrows", self.heading_var, self.refresh_frame).pack(side="left", padx=4)
        self.show_boxes_var = tk.BooleanVar(value=True)
        self._check(row2, "boxes", self.show_boxes_var, self.refresh_frame).pack(side="left", padx=4)

        row3 = tk.Frame(setup, bg=PANEL)
        row3.pack(fill="x", padx=10, pady=(3, 7))
        self._field_label(row3, "Target order")
        self.seq_var = tk.StringVar(value=FULL_TARGET_TEXT)
        self.seq_entry = self._entry(row3, self.seq_var, width=42)
        self.seq_entry.pack(side="left", padx=(4, 8))
        tk.Label(row3, text="10 targets; A-D or 1-4", bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 8)).pack(side="left", padx=(0, 12))
        self.auto_starts_label = tk.Label(
            row3,
            text="10 × 5 min; later starts are automatic",
            bg=PANEL,
            fg=MUTED,
            font=(FONT_UI, 8),
        )
        self.auto_starts_label.pack(side="left")

        row4 = tk.Frame(setup, bg=PANEL)
        row4.pack(fill="x", padx=10, pady=(0, 3))
        self._field_label(row4, "Scale")
        self.px_per_cm_var = tk.StringVar(value="")
        self._entry(row4, self.px_per_cm_var, width=9).pack(side="left", padx=(4, 4))
        tk.Label(row4, text="px/cm", bg=PANEL, fg=TEXT, font=(FONT_UI, 9)).pack(side="left")
        tk.Label(
            row4,
            text="needed for movement metrics",
            bg=PANEL,
            fg=MUTED,
            font=(FONT_UI, 8),
        ).pack(side="left", padx=(8, 0))

        self._field_label(row4, "Missing-data gap")
        self.missing_gap_var = tk.StringVar(value="0")
        self._entry(row4, self.missing_gap_var, width=6).pack(side="left", padx=(4, 3))
        tk.Label(row4, text="s", bg=PANEL, fg=TEXT, font=(FONT_UI, 9)).pack(side="left")
        tk.Label(
            row4,
            text="dwell only; 0 = strict continuity",
            bg=PANEL,
            fg=MUTED,
            font=(FONT_UI, 8),
        ).pack(side="left", padx=(8, 0))

        row5 = tk.Frame(setup, bg=PANEL)
        row5.pack(fill="x", padx=10, pady=(0, 4))
        self._field_label(row5, "Video offset")
        self.offset_var = tk.StringVar(value="0")
        offset_entry = self._entry(row5, self.offset_var, width=9)
        offset_entry.pack(side="left", padx=(4, 4))
        offset_entry.bind("<Return>", lambda e: self.set_frame(self.current_frame, force=True))
        offset_entry.bind("<FocusOut>", lambda e: self.set_frame(self.current_frame, force=True))
        tk.Label(row5, text="Video = CSV - offset", bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left", padx=(0, 16))
        self._field_label(row5, "Moving speed >")
        self.moving_var = tk.StringVar(value="0.2")
        self._entry(row5, self.moving_var, width=7).pack(side="left", padx=(4, 4))
        tk.Label(row5, text="cm/s", bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left", padx=(0, 16))
        self._field_label(row5, "Flag jump >")
        self.jump_var = tk.StringVar(value="0.5")
        self._entry(row5, self.jump_var, width=7).pack(side="left", padx=(4, 4))
        tk.Label(row5, text="cm/frame (review only)", bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left")

        inclusion = tk.LabelFrame(self.root, text=" Flies included in analysis ",
                                  bg=PANEL, fg=MUTED, font=(FONT_UI, 9, "bold"))
        inclusion.pack(fill="x", padx=16, pady=3)
        controls = tk.Frame(inclusion, bg=PANEL)
        controls.pack(side="left", padx=7)
        self._button(controls, "All", lambda: self.set_all_flies(True)).pack(side="left")
        self._button(controls, "None", lambda: self.set_all_flies(False)).pack(side="left", padx=4)
        self.inclusion_count = tk.Label(controls, text="Load a CSV", bg=PANEL, fg=MUTED,
                                        font=(FONT_UI, 9))
        self.inclusion_count.pack(side="left", padx=5)
        scroll_area = tk.Frame(inclusion, bg=PANEL)
        scroll_area.pack(side="left", fill="x", expand=True, padx=5)
        self.inclusion_canvas = tk.Canvas(scroll_area, height=26, bg=PANEL, highlightthickness=0)
        self.inclusion_canvas.pack(fill="x")
        self.inclusion_scrollbar = ttk.Scrollbar(scroll_area, orient="horizontal", command=self.inclusion_canvas.xview)
        self.inclusion_canvas.configure(xscrollcommand=self.inclusion_scrollbar.set)
        self.inclusion_choices = tk.Frame(self.inclusion_canvas, bg=PANEL)
        self.inclusion_canvas.create_window((0, 0), window=self.inclusion_choices, anchor="nw")
        self.inclusion_choices.bind("<Configure>", self._resize_inclusion_section)
        self.inclusion_canvas.bind("<Configure>", self._resize_inclusion_section)

        action = tk.Frame(self.root, bg=BG)
        action.pack(fill="x", padx=16, pady=(5, 3))
        self._button(action, "Recalculate", self.prepare_analysis, primary=True).pack(side="left")
        self._button(action, "Export CSV", self.export_csv).pack(side="left", padx=(6, 0))
        self._button(action, "Choose export...", self.export_analysis_package).pack(side="left", padx=(6, 0))
        self._button(action, "Export MP4", self.export_video).pack(side="left", padx=(6, 0))
        self._button(action, "Review jumps", self.show_tracking_review).pack(side="left", padx=(6, 0))
        self._button(action, "Help", self.show_help).pack(side="left", padx=(6, 0))
        self.cancel_job_btn = self._button(action, "Cancel task", self.export_cancel.set)
        self.cancel_job_btn.pack(side="left", padx=(6, 0))
        self.cancel_job_btn.config(state="disabled")
        self.job_progress = ttk.Progressbar(action, mode="indeterminate", length=50)
        self.job_progress.pack(side="left", padx=6)
        tk.Label(action, text="Space: play   Arrows: frames   Wheel: 5 frames",
                 bg=BG, fg=MUTED, font=(FONT_UI, 8)).pack(side="right")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        right = tk.Frame(body, bg=PANEL, width=520, highlightthickness=1, highlightbackground=BORDER)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        header = tk.Frame(right, bg=PANEL)
        header.pack(fill="x", padx=12, pady=(5, 3))
        tk.Label(header, text="Analysis", font=(FONT_UI, 12, "bold"), fg=TEXT, bg=PANEL).pack(side="left")
        self.scope_var = tk.StringVar(value="Current trial")
        scope_combo = ttk.Combobox(header, textvariable=self.scope_var, state="readonly", width=13,
                                   values=["Current trial", "Full session"])
        scope_combo.pack(side="right")
        scope_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_frame())

        self.state_label = tk.Label(right, text="No analysis prepared", font=(FONT_UI, 10, "bold"),
                                    fg=MUTED, bg=PANEL, anchor="w")
        self.state_label.pack(fill="x", padx=12, pady=(1, 0))
        self.timer_label = tk.Label(right, text="Time to target  --", font=(FONT_UI, 19, "bold"),
                                    fg=ACCENT, bg=PANEL, anchor="w")
        self.timer_label.pack(fill="x", padx=12, pady=(1, 2))
        self.target_detail = tk.Label(right, text="", font=(FONT_UI, 8), fg=MUTED,
                                      bg=PANEL, justify="left", anchor="nw", height=4)
        self.target_detail.config(wraplength=490)
        self.target_detail.pack(fill="x", padx=12, pady=(0, 3))
        tk.Frame(right, height=1, bg=BORDER).pack(fill="x", padx=12, pady=(0, 3))

        plots = tk.Frame(right, bg=PANEL)
        plots.pack(fill="both", expand=True, padx=8, pady=(0, 5))
        plots.pack_propagate(False)
        plots.grid_propagate(False)
        plots.grid_columnconfigure(0, weight=1, uniform="p")
        plots.grid_columnconfigure(1, weight=1, uniform="p")
        plots.grid_rowconfigure(0, weight=1, uniform="p")
        plots.grid_rowconfigure(1, weight=1, uniform="p")
        self.plot_labels, self.plot_images, self.plot_title_labels = {}, {}, {}
        self._make_plot_card(plots, "occupancy", "Selected fly occupancy", 0, 0)
        self._make_plot_card(plots, "reach", "First reach time by fly", 0, 1)
        self._make_plot_card(plots, "progress", "Flies reaching target", 1, 0)
        self._make_plot_card(plots, "trial", "Current target dwell", 1, 1)

        self.summary = tk.Label(right, text="", bg=PANEL, fg=MUTED, justify="left", anchor="nw",
                                font=(FONT_UI, 8), wraplength=490, height=2)
        self.summary.pack(fill="x", padx=12, pady=(2, 8))

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)
        self.video_canvas = tk.Canvas(left, bg="#050505", highlightthickness=1, highlightbackground=BORDER, bd=0)
        self.video_canvas.pack(side="top", fill="both", expand=True)
        self.video_canvas.bind("<MouseWheel>", self.on_video_wheel)
        self.video_canvas.bind("<Button-4>", self.on_video_wheel)
        self.video_canvas.bind("<Button-5>", self.on_video_wheel)
        self.video_canvas.bind("<Configure>", self.on_video_resize)

        transport = tk.Frame(left, bg=PANEL, height=76, highlightthickness=1, highlightbackground=BORDER)
        transport.pack(side="bottom", fill="x", pady=(6, 0), before=self.video_canvas)
        transport.pack_propagate(False)
        transport.columnconfigure(4, weight=1)
        self._button(transport, "|<", self.prev_frame, width=4).grid(row=0, column=0, padx=(6, 2), pady=8)
        self.play_btn = self._button(transport, "Play", self.toggle_play, primary=True, width=7)
        self.play_btn.grid(row=0, column=1, padx=2, pady=8)
        self._button(transport, ">|", self.next_frame, width=4).grid(row=0, column=2, padx=2, pady=8)
        self._button(transport, "-1 s", lambda: self.jump_seconds(-1), width=5).grid(row=0, column=3, padx=(7, 2), pady=8)
        self.frame_scale = tk.Scale(transport, from_=0, to=1, orient="horizontal", command=self.seek,
                                    showvalue=False, bg=PANEL, fg=TEXT, troughcolor=BORDER,
                                    highlightthickness=0, sliderlength=18, bd=0, activebackground=ACCENT)
        self.frame_scale.grid(row=0, column=4, sticky="ew", padx=6, pady=2)
        self.frame_scale.bind("<MouseWheel>", self.on_video_wheel)
        self._button(transport, "+1 s", lambda: self.jump_seconds(1), width=5).grid(row=0, column=5, padx=(2, 7), pady=8)
        self.frame_entry_var = tk.StringVar(value="0")
        entry = self._entry(transport, self.frame_entry_var, width=8, justify="center")
        entry.grid(row=0, column=6, padx=2, pady=8)
        entry.bind("<Return>", lambda e: self.go_to_frame())
        self._button(transport, "Go", self.go_to_frame, width=4).grid(row=0, column=7, padx=2, pady=8)
        self.time_label = tk.Label(transport, text="Frame 0 | 0.00 s", bg=PANEL, fg=TEXT,
                                   font=(FONT_UI, 8), anchor="w")
        self.time_label.grid(row=1, column=0, columnspan=8, sticky="ew", padx=8, pady=(0, 4))

        self.root.bind("<space>", lambda e: self._shortcut(self.toggle_play))
        self.root.bind("<Left>", lambda e: self._shortcut(self.prev_frame))
        self.root.bind("<Right>", lambda e: self._shortcut(self.next_frame))
        self.root.bind("<Shift-Left>", lambda e: self._shortcut(lambda: self.jump_seconds(-1)))
        self.root.bind("<Shift-Right>", lambda e: self._shortcut(lambda: self.jump_seconds(1)))
        self.update_mode_widgets()
        self.update_plots(np.zeros(4))

    def _configure_ttk(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox", font=(FONT_UI, 9), padding=3,
                        fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT,
                        arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.map("TCombobox",
                  fieldbackground=[("disabled", PANEL_2), ("readonly", PANEL_2)],
                  foreground=[("disabled", "#686868"), ("readonly", TEXT)],
                  selectbackground=[("disabled", PANEL_2), ("readonly", PANEL_2)],
                  selectforeground=[("disabled", "#686868"), ("readonly", TEXT)])
        style.configure("TProgressbar", troughcolor=PANEL_2, background=ACCENT,
                        bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=PANEL, fg=MUTED, font=(FONT_UI, 8)).pack(side="left")

    def _entry(self, parent, variable, width=None, justify="left"):
        return tk.Entry(parent, textvariable=variable, width=width, bg=PANEL_2, fg=TEXT,
                        insertbackground=TEXT, relief="flat", bd=0, justify=justify, font=(FONT_UI, 9),
                        disabledbackground=PANEL_2, disabledforeground="#686868",
                        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)

    def _button(self, parent, text, command, primary=False, width=None):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else PANEL_2,
                         fg="#101010" if primary else TEXT, activebackground=ACCENT if primary else BORDER,
                         activeforeground="#101010" if primary else TEXT, relief="flat", bd=0, width=width,
                         padx=9, pady=4, font=(FONT_UI, 9, "bold" if primary else "normal"), cursor="hand2")

    def _check(self, parent, text, variable, command):
        return tk.Checkbutton(parent, text=text, variable=variable, command=command, bg=PANEL, fg=TEXT,
                              selectcolor=PANEL_2, activebackground=PANEL, activeforeground=TEXT,
                              font=(FONT_UI, 8), bd=0, highlightthickness=0)

    def _make_plot_card(self, parent, key, title, row, column):
        card = tk.Frame(parent, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=row, column=column, sticky="nsew", padx=4, pady=4)
        card.pack_propagate(False)
        title_lbl = tk.Label(card, text=title, bg=PANEL_2, fg=TEXT, font=(FONT_UI, 9, "bold"), anchor="w")
        title_lbl.pack(fill="x", padx=7, pady=(6, 1))
        plot_lbl = tk.Label(card, bg=PANEL_2, bd=0)
        plot_lbl.pack(fill="both", expand=True, padx=3, pady=(0, 3))
        self.plot_title_labels[key] = title_lbl
        self.plot_labels[key] = plot_lbl

    def _shortcut(self, func):
        widget = self.root.focus_get()
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Button, ttk.Button, tk.Checkbutton, ttk.Checkbutton, tk.Scale, ttk.Scale)):
            return
        func()
        return "break"

    def _file_row(self, parent, label, button_text, cmd, attr_name):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=10, pady=3)
        tk.Label(row, text=label, width=11, anchor="w", fg=MUTED, bg=PANEL,
                 font=(FONT_UI, 8)).pack(side="left")
        var = tk.StringVar(value="")
        entry = self._entry(row, var)
        entry.configure(state="readonly", readonlybackground=PANEL_2)
        entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        self._button(row, button_text, cmd).pack(side="left")
        setattr(self, attr_name, var)

    def current_trail_frames(self):
        try:
            value = int(self.trail_var.get().strip())
        except (ValueError, AttributeError):
            value = self.trail_frames
        return max(1, min(5000, value))

    def update_mode_widgets(self):
        combo_state = "readonly" if self.single_trial else "disabled"
        # Trial 1 start is the only timing input needed in either mode.
        self.trial_start_entry.config(state="normal")
        self.use_current_btn.config(state="normal")
        self.target_combo.config(state=combo_state)
        self.seq_entry.config(state="disabled" if self.single_trial else "normal")
        self.auto_starts_label.config(fg="#707070" if self.single_trial else MUTED)

    def _commit_seek(self, idx):
        self.seek_after_id = None
        self.set_frame(idx, update_scale=False)

    def go_to_frame(self):
        try:
            idx = int(self.frame_entry_var.get().strip())
        except Exception:
            self.frame_entry_var.set(str(self.current_frame))
            return
        self.set_frame(idx)

    def prev_frame(self):
        self.set_frame(self.current_frame - 1)

    def next_frame(self):
        self.set_frame(self.current_frame + 1)

    def pause_playback(self):
        self.playing = False
        if hasattr(self, "play_btn"):
            self.play_btn.config(text="Play")
        if self.timer_id is not None:
            try:
                self.root.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None

    def fly_changed(self, event=None):
        cur = self.fly_combo.current()
        self.selected_fly = max(0, cur)
        self.refresh_frame()

    def on_video_resize(self, event=None):
        if self.resize_after_id is not None:
            try:
                self.root.after_cancel(self.resize_after_id)
            except Exception:
                pass
        self.resize_after_id = self.root.after(80, self._redraw_after_resize)

    def _redraw_after_resize(self):
        self.resize_after_id = None
        self.refresh_frame()

    def show_frame(self, frame):
        max_w = max(1, self.video_canvas.winfo_width())
        max_h = max(1, self.video_canvas.winfo_height())
        h, w = frame.shape[:2]
        scale = min(max_w / w, max_h / h)
        dw, dh = max(1, int(w * scale)), max(1, int(h * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        resized = cv2.resize(frame, (dw, dh), interpolation=interp)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tk_im = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.last_display_image = tk_im
        cx, cy = max_w / 2, max_h / 2
        if self.video_image_id is None:
            self.video_image_id = self.video_canvas.create_image(cx, cy, image=tk_im, anchor="center")
        else:
            self.video_canvas.itemconfig(self.video_image_id, image=tk_im)
            self.video_canvas.coords(self.video_image_id, cx, cy)

    def _set_plot_image(self, key, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tk_im = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.plot_images[key] = tk_im
        self.plot_labels[key].config(image=tk_im)

    def _selected_fly_name(self):
        if self.data and 0 <= self.selected_fly < len(self.data["track_names"]):
            return self.data["track_names"][self.selected_fly]
        return "--"

    def choose_analysis_exports(self):
        """Ask which files should be included in the analysis folder."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose analysis exports")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Choose what to save",
            font=(FONT_UI, 14, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", padx=18, pady=(16, 3))
        tk.Label(
            dialog,
            text="Only the selected plots and data files will be created.",
            font=(FONT_UI, 9),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 10))

        groups = [
            ("DATA FILES", [
                ("framewise_csv", "Framewise tracks CSV"),
                ("per_fly_metrics_csv", "Per-fly trial metrics CSV"),
                ("trial_summary_csv", "Trial summary CSV"),
                ("fly_color_key_csv", "Fly color key CSV"),
                ("analysis_metadata_json", "Analysis metadata JSON with definitions and file hashes"),
                ("jump_review_csv", "Jump review CSV"),
                ("readme_txt", "Workflow and metric explanation text"),
            ]),
            ("PLOTS (JPEG)", [
                ("per_fly_track_plots", "Separate trajectory for every fly (stops at first success)"),
                ("individual_track_plots", "All flies per trial (each stops at first success)"),
                ("combined_track_plot", "Combined trial trajectories (each fly stops at first success)"),
                ("individual_target_plots", "Individual time-to-target plots"),
                ("combined_target_plot", "Combined time-to-target plot"),
                ("trial_time_summary_plot", "Trial time summary plot"),
            ]),
        ]
        variables = {}
        for heading, items in groups:
            section = tk.LabelFrame(
                dialog, text=f" {heading} ", bg=PANEL, fg=MUTED,
                font=(FONT_UI, 9, "bold"), bd=1, relief="solid",
            )
            section.pack(fill="x", padx=18, pady=5)
            for key, label in items:
                var = tk.BooleanVar(value=True)
                variables[key] = var
                self._check(section, label, var, lambda: None).pack(anchor="w", padx=10, pady=3)

        result = {"options": None}

        def set_all(value):
            for var in variables.values():
                var.set(value)

        def accept():
            selected = {key: bool(var.get()) for key, var in variables.items()}
            if not any(selected.values()):
                messagebox.showwarning("Nothing selected", "Select at least one plot or data file.", parent=dialog)
                return
            result["options"] = selected
            dialog.destroy()

        controls = tk.Frame(dialog, bg=BG)
        controls.pack(fill="x", padx=18, pady=(9, 16))
        self._button(controls, "Select all", lambda: set_all(True)).pack(side="left")
        self._button(controls, "Clear all", lambda: set_all(False)).pack(side="left", padx=(6, 0))
        self._button(controls, "Cancel", dialog.destroy).pack(side="right")
        self._button(controls, "Continue", accept, primary=True).pack(side="right", padx=(0, 6))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - dialog.winfo_width()) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - dialog.winfo_height()) // 2)
        dialog.geometry(f"+{x}+{y}")
        self.root.wait_window(dialog)
        return result["options"]

    def _settings_changed(self, variable_name, *_):
        if not self._suppress_settings:
            self.invalidate_analysis()
            if variable_name == str(self.offset_var):
                self._update_frame_range()
                self.set_frame(self.current_frame, force=True)
                return
            if self.current_bgr is not None or self.dataset:
                self.refresh_frame()

    def invalidate_analysis(self):
        self.pause_playback()
        self.analysis_ready = False
        self.result = None
        self.analysis_fps = None
        self.fly_target_reach_frame = {}
        self.fly_target_reach_time = {}
        self.team_time_to_target = {}
        self.mean_time_to_target = {}
        if hasattr(self, "state_label"):
            self.state_label.config(text="Settings changed: click Recalculate", fg=WARN)

    def effective_fps(self):
        if self.result is not None:
            return self.result.settings.fps
        text = self.fps_override_var.get().strip() if hasattr(self, "fps_override_var") else ""
        try:
            value = float(text)
            if math.isfinite(value) and value > 0:
                return value
        except ValueError:
            pass
        return self.video_fps if self.video_fps and self.video_fps > 0 else 24.0

    def pixels_per_cm(self):
        return positive_number(self.px_per_cm_var.get().strip(), "Pixels per centimetre (px/cm)")

    def video_offset(self):
        return integer_number(self.offset_var.get(), "Video frame offset", allow_negative=True)

    def parse_settings(self):
        fps_text = self.fps_override_var.get().strip()
        if fps_text:
            fps, fps_source = positive_number(fps_text, "Analysis FPS"), "manual"
        elif self.video_fps:
            fps, fps_source = self.video_fps, "video_metadata"
        else:
            raise ValueError("CSV contains no FPS. Load the matching video or enter Analysis FPS explicitly.")
        scale_text = self.px_per_cm_var.get().strip()
        scale = positive_number(scale_text, "Pixels per centimetre") if scale_text else None
        return AnalysisSettings(
            fps=fps, pixels_per_cm=scale,
            dwell_seconds=positive_number(self.threshold_var.get(), "Dwell threshold"),
            missing_gap_seconds=nonnegative_number(self.missing_gap_var.get(), "Missing-data tolerance"),
            moving_threshold_cm_s=nonnegative_number(self.moving_var.get(), "Movement threshold"),
            jump_threshold_cm=positive_number(self.jump_var.get(), "Jump threshold"),
            trial_start_frame=integer_number(self.trial_start_frame_var.get(), "Trial 1 start"),
            single_trial=self.mode_var.get().startswith("Single"), single_target=max(0, self.target_combo.current()),
            target_sequence=(parse_target_sequence(self.seq_var.get()) if not self.mode_var.get().startswith("Single")
                             else tuple(FULL_TARGET_SEQUENCE)), video_frame_offset=self.video_offset(),
            fps_source=fps_source,
        )

    def mode_changed(self, event=None):
        self.single_trial = self.mode_var.get().startswith("Single")
        self.update_mode_widgets()
        self.invalidate_analysis()
        self.refresh_frame()

    def target_changed(self, event=None):
        self.target_box = max(0, self.target_combo.current())
        self.invalidate_analysis()
        self.refresh_frame()

    def set_start_current(self):
        self.trial_start_frame_var.set(str(self.current_frame))

    def _set_busy(self, busy):
        self.busy = busy
        if busy:
            self.pause_playback()
            self._disabled_widgets = []
            def disable(widget):
                for child in widget.winfo_children():
                    if child is self.cancel_job_btn:
                        continue
                    if isinstance(child, (tk.Button, tk.Entry, tk.Checkbutton, tk.Scale,
                                          ttk.Combobox, ttk.Button, ttk.Entry, ttk.Checkbutton)):
                        try:
                            state = str(child.cget("state"))
                            self._disabled_widgets.append((child, state))
                            child.configure(state="disabled")
                        except tk.TclError:
                            pass
                    disable(child)
            disable(self.root)
        else:
            for widget, state in self._disabled_widgets:
                try:
                    if widget.winfo_exists():
                        widget.configure(state=state)
                except tk.TclError:
                    pass
            self._disabled_widgets = []
        self.cancel_job_btn.configure(state="normal" if busy else "disabled")
        if busy:
            self.job_progress.start(12)
        else:
            self.job_progress.stop()
            self.job_progress.configure(value=0)

    def _start_job(self, title, operation, callback):
        if self.busy:
            return
        self.export_cancel.clear()
        self._job_callback = callback
        self._set_busy(True)
        self.status.configure(text=title, fg=ACCENT)
        def worker():
            try:
                value = operation(lambda msg: self.job_messages.put(("progress", str(msg))), self.export_cancel)
                self.job_messages.put(("done", value))
            except CancelledError as exc:
                self.job_messages.put(("cancelled", str(exc)))
            except Exception as exc:
                self.job_messages.put(("error", (str(exc), traceback.format_exc())))
        threading.Thread(target=worker, daemon=True).start()

    def _poll_jobs(self):
        if self._closed:
            return
        try:
            while True:
                kind, payload = self.job_messages.get_nowait()
                if kind == "progress":
                    self.status.configure(text=payload, fg=ACCENT)
                    continue
                callback = self._job_callback
                self._job_callback = None
                self._set_busy(False)
                if self._closing:
                    self._close_now()
                    return
                if kind == "done":
                    try:
                        callback(payload)
                    except Exception as exc:
                        self.status.configure(text="Could not apply result", fg=BAD)
                        messagebox.showerror("Result error", str(exc))
                elif kind == "cancelled":
                    self.status.configure(text=payload, fg=WARN)
                else:
                    self.status.configure(text="Operation failed; no completed result was applied", fg=BAD)
                    if not self._closing:
                        messagebox.showerror("Operation failed", payload[0])
                if self._closing:
                    self._close_now()
                    return
        except queue.Empty:
            pass
        if not self._closed:
            self.root.after(60, self._poll_jobs)

    def pick_csv(self):
        path = filedialog.askopenfilename(title="Choose AMADEUS result CSV",
                                         filetypes=[("AMADEUS tracking", "*.csv"), ("All files", "*.*")])
        if path:
            self._start_job("Loading AMADEUS CSV...",
                            lambda progress, cancel: load_amadeus_csv(path, progress, cancel), self._csv_loaded)

    def _csv_loaded(self, data):
        self.pause_playback()
        self.invalidate_analysis()
        self.source_dataset = data
        self.dataset, self.data, self.csv_path = data, data.legacy_view(), data.source_path
        self.csv_var.set(data.source_path)
        for widget in self.inclusion_choices.winfo_children():
            widget.destroy()
        self.fly_inclusion_vars = {}
        for ident in data.ids:
            variable = tk.BooleanVar(value=True)
            self.fly_inclusion_vars[ident] = variable
            self._check(self.inclusion_choices, f"ID {ident}", variable,
                        self.fly_inclusion_changed).pack(side="left", padx=3)
        self.inclusion_canvas.xview_moveto(0)
        self._update_included_fly_combo()
        self.current_frame = data.first_frame
        self.current_bgr = None
        self._update_frame_range()
        self.set_frame(data.first_frame, force=True)
        self.check_alignment()
        if data.warnings:
            messagebox.showwarning("CSV import notes", "\n\n".join(data.warnings))

    def _resize_inclusion_section(self, event=None):
        self.inclusion_canvas.configure(scrollregion=self.inclusion_canvas.bbox("all"))
        if self.inclusion_choices.winfo_reqwidth() > self.inclusion_canvas.winfo_width():
            self.inclusion_scrollbar.pack(fill="x")
        else:
            self.inclusion_scrollbar.pack_forget()
            self.inclusion_canvas.xview_moveto(0)

    def _update_included_fly_combo(self, preferred_id=None):
        ids = self.dataset.ids
        self.fly_combo["values"] = [f"Fly {self.dataset.fly_number(i)}  |  ID {ident}"
                                     for i, ident in enumerate(ids)]
        self.selected_fly = ids.index(preferred_id) if preferred_id in ids else 0
        if ids:
            self.fly_combo.current(self.selected_fly)
        else:
            self.fly_combo.set("")
        self.inclusion_count.configure(text=f"{len(ids)}/{len(self.source_dataset.ids)} selected",
                                       fg=GOOD if ids else WARN)

    def set_all_flies(self, included):
        if self.busy or self.source_dataset is None:
            return
        for variable in self.fly_inclusion_vars.values():
            variable.set(included)
        self.fly_inclusion_changed()

    def fly_inclusion_changed(self):
        if self.busy or self.source_dataset is None:
            return
        preferred_id = (self.dataset.ids[self.selected_fly]
                        if self.dataset.ids else None)
        included = tuple(ident for ident, variable in self.fly_inclusion_vars.items() if variable.get())
        if included == self.dataset.ids:
            return
        self.invalidate_analysis()
        self.dataset = self.source_dataset.select_ids(included)
        self.data = self.dataset.legacy_view()
        self._update_included_fly_combo(preferred_id)
        self.refresh_frame()
        self.status.configure(text=(f"{len(included)}/{len(self.source_dataset.ids)} flies selected. "
                                    "Click Recalculate to apply selection." if included else
                                    "No flies selected. Select at least one fly for analysis."), fg=WARN)

    def pick_video(self):
        path = filedialog.askopenfilename(title="Choose the exact AMADEUS input video",
                                         filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")])
        if not path:
            return
        cap = cv2.VideoCapture(path)
        try:
            if not cap.isOpened():
                raise ValueError("Could not open the video.")
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if count <= 0 or w <= 0 or h <= 0:
                raise ValueError("The decoder did not report valid frame count and dimensions.")
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            first = decode_video_frame(cap, 0)
        except Exception as exc:
            cap.release()
            messagebox.showerror("Video error", str(exc))
            return
        self.pause_playback()
        if self.cap is not None:
            self.cap.release()
        self.cap, self.video_path = cap, str(Path(path).resolve())
        self.video_var.set(self.video_path)
        self.video_frame_count, self.video_width, self.video_height = count, w, h
        self.video_fps = fps if math.isfinite(fps) and fps > 0 else None
        self.invalidate_analysis()
        self.current_bgr = first
        self._update_frame_range()
        self.set_frame(self.current_frame, force=True)
        self.check_alignment()

    def _update_frame_range(self):
        low, high = self.frame_limits()
        self._updating_scale = True
        try:
            self.frame_scale.configure(from_=low, to=high)
            self.frame_scale.set(min(max(self.current_frame, low), high))
        finally:
            self._updating_scale = False

    def frame_limits(self):
        if self.dataset:
            return self.dataset.first_frame, self.dataset.end_frame - 1
        try:
            offset = self.video_offset()
        except ValueError:
            offset = 0
        return offset, max(offset, offset + self.video_frame_count - 1)

    def max_video_frame(self):
        return self.frame_limits()[1]

    def check_alignment(self):
        parts, warning = [], False
        if self.dataset:
            d = self.dataset
            parts.append(f"{len(d.ids)} IDs; CSV {d.first_frame:,}-{d.end_frame - 1:,}; {d.csv_rows:,} rows")
            if len(d.ids) != 10:
                parts.append("team size differs from 10")
                warning = True
        if self.video_path:
            parts.append(f"video {self.video_frame_count:,} frames, {self.video_width}x{self.video_height}")
        if self.dataset and self.video_path:
            try:
                offset = self.video_offset()
                a, b = self.dataset.first_frame - offset, self.dataset.end_frame - 1 - offset
                if a < 0 or b >= self.video_frame_count:
                    parts.append(f"offset mismatch: mapped video {a:,}-{b:,}")
                    warning = True
                elif self.dataset.frame_count < self.video_frame_count:
                    parts.append("CSV covers part of the video")
                if self._outside_video_count():
                    parts.append("some centres outside video geometry")
                    warning = True
            except ValueError:
                parts.append("invalid video frame offset")
                warning = True
        if parts:
            self.status.configure(text="  |  ".join(parts), fg=WARN if warning else GOOD)

    def _outside_video_count(self):
        if not self.dataset or not self.video_width:
            return 0
        xy = self.dataset.values[:, :, :2]
        outside = ((xy[:, :, 0] < 0) | (xy[:, :, 0] > self.video_width)
                   | (xy[:, :, 1] < 0) | (xy[:, :, 1] > self.video_height))
        return int((self.dataset.valid & outside).sum())

    def draw_or_load_boxes(self):
        choice = messagebox.askyesnocancel("Cool boxes", "Yes = load saved JSON\nNo = draw boxes on the video\nCancel = close")
        if choice is None:
            return
        if choice:
            path = filedialog.askopenfilename(filetypes=[("Box coordinates", "*.json"), ("All files", "*.*")])
            if not path:
                return
            try:
                zones, obj = load_zones_json(path)
                size = obj.get("video_size")
                if size and self.video_width and list(size) != [self.video_width, self.video_height]:
                    raise ValueError("Saved boxes were drawn on a different video size. Redraw them on the matching video.")
                validate_zones(zones, (self.video_width, self.video_height) if self.video_width else None)
            except Exception as exc:
                messagebox.showerror("Box error", str(exc))
                return
            self.zones, self.zone_path = list(zones), path
            self.box_var_path.set(path)
            self.invalidate_analysis()
            self.refresh_frame()
        else:
            if self.current_bgr is None or self.cap is None:
                messagebox.showwarning("Video required", "Load the matching video and choose a valid mapped frame before drawing.")
                return
            self.pause_playback()
            try:
                ZoneDrawWindow(self.root, self.current_bgr.copy(), existing=self.zones, on_done=self._boxes_drawn,
                               video_path=self.video_path,
                               initial_video_frame=self.current_frame - self.video_offset(),
                               video_frame_offset=self.video_offset())
            except Exception as exc:
                messagebox.showerror("Box editor error", str(exc))

    def _boxes_drawn(self, zones):
        try:
            validate_zones(zones, (self.video_width, self.video_height))
        except ValueError as exc:
            messagebox.showerror("Invalid boxes", str(exc))
            return
        self.zones, self.zone_path = list(zones), None
        self.box_var_path.set("Four boxes drawn; coordinates in input-video pixels")
        self.invalidate_analysis()
        self.refresh_frame()
        if messagebox.askyesno("Save boxes", "Save these box coordinates for reuse?"):
            path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="amadeus_cool_boxes.json",
                                               filetypes=[("JSON", "*.json")])
            if path:
                try:
                    if Path(path).suffix.lower() != ".json":
                        raise ValueError("Use a .json filename for box coordinates.")
                    self._protect_input_path(path)
                    atomic_json(path, {"boxes": [z.as_dict() for z in self.zones],
                                       "video_size": [self.video_width, self.video_height]})
                    self.zone_path = path
                    self.box_var_path.set(path)
                except Exception as exc:
                    messagebox.showerror("Save error", str(exc))

    def prepare_analysis(self):
        if not self.dataset:
            messagebox.showwarning("Tracking required", "Load an AMADEUS tracking CSV first.")
            return
        try:
            if not self.dataset.ids:
                raise ValueError("Select at least one fly for analysis.")
            settings = self.parse_settings()
            validate_zones(self.zones, (self.video_width, self.video_height) if self.video_width else None)
            if self.video_path:
                a = self.dataset.first_frame - settings.video_frame_offset
                b = self.dataset.end_frame - 1 - settings.video_frame_offset
                if a < 0 or b >= self.video_frame_count:
                    raise ValueError(
                        f"CSV maps to video frames {a:,}-{b:,}, but the video contains 0-{self.video_frame_count - 1:,}.\n"
                        "Set Video offset so video frame = CSV frame - offset. Use matching video geometry."
                    )
        except ValueError as exc:
            messagebox.showerror("Check analysis settings", str(exc))
            return
        dataset, zones = self.dataset, tuple(self.zones)
        self._start_job("Calculating target and movement metrics...",
                        lambda progress, cancel: analyze_tracking(dataset, zones, settings, progress, cancel),
                        self._analysis_loaded)

    def _analysis_loaded(self, result):
        self.result = result
        self.analysis_ready = True
        s = result.settings
        self.analysis_fps, self.single_trial = s.fps, s.single_trial
        self.threshold_seconds, self.missing_gap_seconds = s.dwell_seconds, s.missing_gap_seconds
        self.target_sequence = list(s.target_sequence)
        self.trial_start_user = s.trial_start_frame
        self.fly_target_reach_frame = {t.number: t.reach_frames for t in result.trials}
        self.fly_target_reach_time = {t.number: t.reach_times for t in result.trials}
        self.team_time_to_target = {t.number: t.team_time for t in result.trials}
        self.mean_time_to_target = {t.number: t.mean_time for t in result.trials}
        partial = sum(t.coverage_status != "complete" for t in result.trials)
        jumps = int(result.jump_mask.sum()) if s.pixels_per_cm is not None else None
        text = f"Ready: {s.fps:.6g} FPS; dwell {s.dwell_frames} frames; gap <= {s.gap_frames} frames"
        if partial:
            text += f"; {partial} partial/unavailable trial(s)"
        text += f"; {jumps} jump flags" if jumps is not None else "; enter scale to calculate motion and jump flags"
        self.status.configure(text=text, fg=WARN if partial or jumps else GOOD)
        self.auto_starts_label.configure(text=f"5 min = {300 * s.fps:,.3f} frames; boundaries rounded from elapsed time")
        self._update_frame_range()
        self.set_frame(self.current_frame, force=True)

    def current_trial_target(self, frame_idx):
        if self.result:
            trial = self.result.trial_for_frame(frame_idx)
            if trial:
                return trial.number, trial.start, trial.target
            if frame_idx < self.result.trials[0].start:
                return 0, self.result.trials[0].start, None
            return len(self.result.trials) + 1, self.result.trials[-1].planned_end, None
        return 0, 0, None

    def team_current_state(self, frame_idx):
        trial = self.result.trial_for_frame(frame_idx) if self.result else None
        if trial is None:
            return 0, 0, None, 0.0, False, 0, len(self.dataset.ids) if self.dataset else 0
        reached = sum(f is not None and f <= frame_idx for f in trial.reach_frames)
        found = trial.team_time is not None and all(f <= frame_idx for f in trial.reach_frames)
        elapsed = (frame_idx - trial.start + 1) / self.result.settings.fps
        return trial.number, trial.start, trial.target, trial.team_time if found else elapsed, found, reached, len(self.dataset.ids)

    def current_zone_seconds(self, tid, frame_idx, scope="Current trial"):
        return self.result.occupancy(tid, frame_idx, scope == "Current trial") if self.result else np.zeros(4)

    def continuous_target_seconds(self, tid, frame_idx, target):
        index = self.dataset.row_index(frame_idx) if self.dataset else None
        if self.result is None or index is None:
            return None
        value = self.result.dwell_seconds[index, tid]
        return float(value) if np.isfinite(value) else None

    def _trial_definitions(self):
        return [(t.number, t.available_start, t.available_end, t.target) for t in self.result.trials] if self.result else []

    def read_frame(self, idx):
        if self.cap is None:
            return None
        return decode_video_frame(self.cap, int(idx) - self.video_offset())

    def set_frame(self, idx, update_scale=True, force=False):
        if self.busy:
            return
        if self.seek_after_id is not None:
            self.root.after_cancel(self.seek_after_id)
            self.seek_after_id = None
        low, high = self.frame_limits()
        idx = min(max(int(idx), low), high)
        if force or idx != self.current_frame or self.current_bgr is None:
            if self.cap is not None:
                try:
                    self.current_bgr = self.read_frame(idx)
                except Exception as exc:
                    self.current_bgr = None
                    self.status.configure(text=str(exc), fg=BAD)
                    self.pause_playback()
            self.current_frame = idx
        if update_scale:
            self._updating_scale = True
            try:
                self.frame_scale.set(idx)
            finally:
                self._updating_scale = False
        self.frame_entry_var.set(str(idx))
        self.refresh_frame()

    def seek(self, value):
        if self._updating_scale or self.busy:
            return
        try:
            idx = int(round(float(value)))
        except ValueError:
            return
        # Tk may defer Scale's command until idle, after _updating_scale resets.
        # A programmatic timeline update already matches the displayed frame.
        if idx == self.current_frame:
            return
        self.pause_playback()
        if self.seek_after_id:
            self.root.after_cancel(self.seek_after_id)
        self.seek_after_id = self.root.after(25, lambda: self._commit_seek(idx))

    def jump_seconds(self, seconds):
        self.set_frame(self.current_frame + int(round(seconds * self.effective_fps())))

    def on_video_wheel(self, event):
        if self.busy:
            return "break"
        direction = 1 if getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4 else -1
        self.set_frame(self.current_frame + direction * 5)
        return "break"

    def toggle_play(self):
        if self.busy or not (self.dataset or self.cap):
            return
        if self.playing:
            self.pause_playback()
        else:
            self.playing = True
            self.play_btn.configure(text="Pause")
            self.timer_id = self.root.after(1, self.play_loop)

    def play_loop(self):
        self.timer_id = None
        if not self.playing or self.busy:
            return
        if self.current_frame >= self.max_video_frame():
            self.pause_playback()
            return
        began = time.perf_counter()
        self.set_frame(self.current_frame + 1)
        if self.playing:
            delay = max(1, int(round(1000 / self.effective_fps() - (time.perf_counter() - began) * 1000)))
            self.timer_id = self.root.after(delay, self.play_loop)

    def render_overlay(self, frame, frame_idx):
        return render_annotation(frame, self.dataset, self.result, self.zones, frame_idx,
                                 self.all_var.get(), self.show_boxes_var.get(), self.heading_var.get(),
                                 self.current_trail_frames(), self.selected_fly, stop_at_success=False)

    def refresh_frame(self):
        if not hasattr(self, "video_canvas") or self._closed:
            return
        if self.current_bgr is not None:
            background = self.current_bgr
        elif self.dataset:
            w, h = self._analysis_canvas_size()
            background = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(background, "CSV POSITIONS ONLY - NO MAPPED VIDEO FRAME", (18, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 170, 240), 1, cv2.LINE_AA)
        else:
            return
        self.show_frame(self.render_overlay(background, self.current_frame))
        try:
            video_frame = self.current_frame - self.video_offset()
            video_text = f"Video frame {video_frame:,}" if self.cap else "No video"
        except ValueError:
            video_text = "Invalid offset"
        self.time_label.configure(text=f"CSV frame {self.current_frame:,}  |  {video_text}  |  {self.effective_fps():.6g} FPS")
        self.frame_entry_var.set(str(self.current_frame))
        secs = self.current_zone_seconds(self.selected_fly, self.current_frame, self.scope_var.get())
        self.update_plots(secs)
        self.update_right_panel(secs)

    def _plot_size(self, key):
        label = self.plot_labels[key]
        # Images never increase a panel's requested width or height.
        return max(1, label.winfo_width() - 2), max(1, label.winfo_height() - 2)

    def update_plots(self, secs):
        if not hasattr(self, "plot_labels"):
            return
        self._set_plot_image("occupancy", draw_compact_bars(*self._plot_size("occupancy"), list(secs),
                                                           BOX_LETTERS, BOX_BGR, suffix="s"))
        self.plot_title_labels["occupancy"].configure(text=f"Occupancy | {self._selected_fly_name()}")
        trial = self.result.trial_for_frame(self.current_frame) if self.result else None
        if trial is None:
            for key in ("reach", "progress", "trial"):
                self._set_plot_image(key, draw_compact_line(*self._plot_size(key), [], []))
            return
        labels = [str(self.dataset.fly_number(i)) for i in range(len(self.dataset.ids))]
        values = trial.reach_times
        self._set_plot_image("reach", draw_compact_bars(*self._plot_size("reach"), values, labels,
                                                       [PLOT_ACCENT_BGR], missing=[v is None for v in values], suffix="s"))
        self.plot_title_labels["reach"].configure(text=f"First reach | trial {trial.number}")
        current = (self.current_frame - trial.start + 1) / self.result.settings.fps
        self._set_plot_image("progress", draw_step_progress(*self._plot_size("progress"), values, current, len(values)))
        self.plot_title_labels["progress"].configure(text=f"Flies reached | {sum(f is not None and f <= self.current_frame for f in trial.reach_frames)}/{len(values)}")
        if self.result.settings.single_trial:
            dwell = [self.continuous_target_seconds(i, self.current_frame, trial.target) for i in range(len(values))]
            self._set_plot_image("trial", draw_compact_bars(*self._plot_size("trial"), dwell, labels,
                                                           [PLOT_GOOD_BGR], missing=[v is None for v in dwell],
                                                           suffix="s", reference=self.result.settings.dwell_seconds))
            self.plot_title_labels["trial"].configure(text="Current confirmed target dwell")
        else:
            times = [t.team_time for t in self.result.trials]
            self._set_plot_image("trial", draw_compact_bars(*self._plot_size("trial"), times,
                                                           [str(t.number) for t in self.result.trials], [PLOT_GOOD_BGR],
                                                           missing=[v is None for v in times], suffix="s"))
            self.plot_title_labels["trial"].configure(text="Team time by trial")

    def update_right_panel(self, secs):
        trial = self.result.trial_for_frame(self.current_frame) if self.result else None
        if self.result is None:
            self.state_label.configure(text=("Select at least one fly" if self.dataset is not None and not self.dataset.ids
                                             else "Recalculate to apply analysis settings"), fg=MUTED)
            self.timer_label.configure(text="Time to target  --", fg=ACCENT)
            self.target_detail.configure(text="Load CSV and boxes; verify FPS, scale, start frame, and offset.")
        elif trial is None:
            before = self.current_frame < self.result.trials[0].start
            self.state_label.configure(text="Before trial 1" if before else "After scheduled trials", fg=MUTED)
            self.timer_label.configure(text="No active trial", fg=MUTED)
            self.target_detail.configure(text="Pre-trial and post-trial frames are excluded from trial metrics.")
        else:
            _, _, _, elapsed, found, reached, total = self.team_current_state(self.current_frame)
            self.state_label.configure(text=f"Trial {trial.number} | target {BOX_LETTERS[trial.target]} | {trial.coverage_status} coverage",
                                       fg=GOOD if found else ACCENT)
            self.timer_label.configure(text=f"{'Team time' if found else 'Search time'}  {elapsed:.2f} s",
                                       fg=GOOD if found else ACCENT)
            tid = self.selected_fly
            reach_frame, reach_time = trial.reach_frames[tid], trial.reach_times[tid]
            selected = f"{reach_time:.2f} s" if reach_frame is not None and reach_frame <= self.current_frame else "not reached yet"
            mean = f" | all-fly mean {trial.mean_time:.2f} s" if found else ""
            metric = trial.metrics[tid]
            motion = "Scale not set; movement metrics unavailable"
            if metric["path_length_cm"] is not None:
                speed = metric["mean_speed_cm_s_tracked"]
                moving = metric["time_moving_pct_tracked"]
                motion = f"Path {metric['path_length_cm']:.2f} cm | mean speed {speed:.3f} cm/s" if speed is not None else f"Path {metric['path_length_cm']:.2f} cm | no valid steps"
                if moving is not None:
                    motion += f" | moving {moving:.1f}%"
            coverage = metric["tracking_coverage_pct"]
            coverage_text = f"{coverage:.1f}%" if coverage is not None else "no data"
            self.target_detail.configure(text=(
                f"Reached {reached}/{total} | dwell >= {self.result.settings.dwell_seconds:.3g} s | {self._selected_fly_name()}: {selected}{mean}\n"
                f"{motion}\nTracking coverage {coverage_text}; movement metrics cover the whole trial."
            ))
        box_text = "  ".join(f"{BOX_LETTERS[i]} {v:.1f}s" for i, v in enumerate(secs))
        flags = int(self.result.jump_mask.sum()) if self.result else 0
        self.summary.configure(text=f"{box_text} | trail {self.current_trail_frames()} frames\n"
                                    f"{flags} jump flags. Raw positions retained; inspect in Review jumps.")

    def _analysis_canvas_size(self):
        if self.video_width and self.video_height:
            return self.video_width, self.video_height
        if self.dataset:
            x, y = self.dataset.values[:, :, 0], self.dataset.values[:, :, 1]
            finite_x, finite_y = x[np.isfinite(x)], y[np.isfinite(y)]
            max_x = float(finite_x.max()) if finite_x.size else 640
            max_y = float(finite_y.max()) if finite_y.size else 480
            return max(640, min(4096, int(math.ceil(max_x)) + 30)), max(480, min(4096, int(math.ceil(max_y)) + 30))
        return 640, 480

    def _video_info_snapshot(self):
        return {"path": self.video_path, "metadata_fps": self.video_fps,
                "frame_count": self.video_frame_count, "width": self.video_width, "height": self.video_height,
                "video_frame_offset": self.result.settings.video_frame_offset if self.result else self.video_offset(),
                "positions_outside_video_count": self._outside_video_count(),
                "geometry_verified_by_user": "Load the exact AMADEUS input video; dimensions alone cannot verify a crop or resize."}

    def export_csv(self):
        if not self.result:
            messagebox.showwarning("Recalculate first", "Prepare the analysis before exporting.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="amadeus_target_times.csv",
                                           filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            if Path(path).suffix.lower() != ".csv":
                raise ValueError("Use a .csv filename for the target-time table.")
            self._protect_input_path(path)
        except ValueError as exc:
            messagebox.showerror("Choose another output filename", str(exc))
            return
        result = self.result
        def operation(progress, cancel):
            rows = []
            for trial in result.trials:
                row = {**trial_summary(result, trial), **audit_columns(result)}
                for tid, ident in enumerate(result.dataset.ids):
                    row[f"id_{ident}_reach_frame"] = trial.reach_frames[tid]
                    row[f"id_{ident}_reach_time_s"] = trial.reach_times[tid]
                rows.append(row)
            temp = Path(path).with_name(Path(path).name + f".tmp-{time.time_ns()}")
            try:
                write_dict_csv(temp, rows, cancel=cancel)
                check_cancel(cancel)
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
            return path
        self._start_job("Exporting target times...", operation,
                        lambda p: messagebox.showinfo("CSV saved", f"Saved:\n{p}"))

    def export_analysis_package(self):
        if not self.result:
            messagebox.showwarning("Recalculate first", "Prepare the analysis before exporting.")
            return
        options = self.choose_analysis_exports()
        if options is None:
            return
        parent = filedialog.askdirectory(title="Choose parent folder; a new analysis subfolder will be created")
        if not parent:
            return
        snapshot = ExportSnapshot(self.result, self._video_info_snapshot(), options,
                                  self._analysis_canvas_size(), self.current_bgr.copy() if self.current_bgr is not None else None)
        self._start_job("Saving selected analysis outputs...",
                        lambda progress, cancel: write_analysis_package(parent, snapshot, progress, cancel),
                        lambda p: self._export_finished(p))

    def _export_finished(self, path):
        self.status.configure(text=f"Saved complete analysis: {Path(path).name}", fg=GOOD)
        messagebox.showinfo("Analysis saved", f"Saved selected outputs to:\n{path}")

    def _protect_input_path(self, path):
        output = Path(path).resolve()
        for source in (self.csv_path, self.video_path):
            if source and output == Path(source).resolve():
                raise ValueError("An analysis output cannot overwrite the input CSV or video.")

    def show_tracking_review(self):
        if not self.result:
            messagebox.showwarning("Recalculate first", "Prepare the analysis with a px/cm scale to review jumps.")
            return
        if self.result.settings.pixels_per_cm is None:
            messagebox.showwarning("Scale required", "Enter px/cm and recalculate to apply the jump distance threshold.")
            return
        win = tk.Toplevel(self.root)
        reviewed_result = self.result
        win.title("Tracking quality and jump review")
        win.configure(bg=BG)
        win.geometry("860x580")
        total = int(self.result.jump_mask.sum())
        tk.Label(win, text=f"{total:,} jump steps > {self.result.settings.jump_threshold_cm:g} cm/frame",
                 bg=BG, fg=TEXT, font=(FONT_UI, 13, "bold")).pack(anchor="w", padx=12, pady=(12, 3))
        tk.Label(win, text="Flags do not change identities or coordinates. Double-click to inspect the corresponding frame.\n"
                           "Correct confirmed errors in AMADEUS Refinement, save a revised CSV, and reload it here.",
                 bg=BG, fg=MUTED, justify="left").pack(anchor="w", padx=12, pady=(0, 8))
        missing = [(int(self.result.valid[:, i].size - self.result.valid[:, i].sum()), ident)
                   for i, ident in enumerate(self.dataset.ids)]
        tk.Label(win, text="Missing positions: " + "; ".join(f"ID {ident}: {n}" for n, ident in missing),
                 bg=BG, fg=MUTED, wraplength=830, justify="left").pack(anchor="w", padx=12, pady=(0, 8))
        frame = tk.Frame(win, bg=BG)
        frame.pack(fill="both", expand=True, padx=12, pady=6)
        names = ("CSV frame", "ID", "Step cm", "Speed cm/s", "Trial", "In metrics")
        tree = ttk.Treeview(frame, columns=names, show="headings", selectmode="browse")
        for name in names:
            tree.heading(name, text=name)
            tree.column(name, width=120, anchor="center")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for count, event in enumerate(iter_jump_events(self.result)):
            if count >= 5000:
                break
            tree.insert("", "end", values=(event["csv_frame"], event["amadeus_id"],
                                           f"{event['step_distance_cm']:.4f}", f"{event['speed_cm_s']:.3f}",
                                           event["trial"] or "--", "yes" if event["included_in_trial_movement"] else "no"))
        if total > 5000:
            tk.Label(win, text="First 5,000 shown. Export jump review CSV for all events.", bg=BG, fg=WARN).pack(pady=4)
        def select(event=None):
            if self.busy or self.result is not reviewed_result:
                return
            item = tree.selection()
            if item:
                vals = tree.item(item[0], "values")
                self.pause_playback()
                self.selected_fly = self.dataset.ids.index(int(vals[1]))
                self.fly_combo.current(self.selected_fly)
                self.set_frame(int(vals[0]))
        tree.bind("<Double-1>", select)
        self._button(win, "Inspect selected frame", select, primary=True).pack(pady=(3, 12))

    def show_help(self):
        messagebox.showinfo("AMADEUS analysis workflow", HELP_TEXT)

    def export_video(self):
        if not self.result or not self.video_path:
            messagebox.showwarning("Video and analysis required", "Load the matching video and recalculate first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".mp4", initialfile="amadeus_validation.mp4",
                                           filetypes=[("MP4", "*.mp4")])
        if not path:
            return
        try:
            if Path(path).suffix.lower() != ".mp4":
                raise ValueError("Use a .mp4 filename for the validation video.")
            self._protect_input_path(path)
        except ValueError as exc:
            messagebox.showerror("Choose another output filename", str(exc))
            return
        result, video = self.result, self.video_path
        params = (bool(self.all_var.get()), bool(self.show_boxes_var.get()), bool(self.heading_var.get()),
                  self.current_trail_frames(), int(self.selected_fly))
        self._start_job("Rendering validation video over the loaded CSV interval...",
                        lambda progress, cancel: write_validation_video(path, video, result, params, progress, cancel),
                        lambda p: messagebox.showinfo("Validation video saved", f"Saved verified MP4:\n{p}"))

    def on_close(self):
        if self.busy:
            self._closing = True
            self.export_cancel.set()
            self.status.configure(text="Cancelling operation and cleaning temporary output before closing...", fg=WARN)
            return
        self._close_now()

    def _close_now(self):
        self._closed = True
        self.pause_playback()
        for attr in ("seek_after_id", "resize_after_id"):
            callback = getattr(self, attr, None)
            if callback:
                try:
                    self.root.after_cancel(callback)
                except tk.TclError:
                    pass
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()


def run_self_tests():
    """Small reproducible checks, runnable on the user's computer with --self-test."""
    import unittest

    class NumericalTests(unittest.TestCase):
        def zones(self):
            return tuple(Zone(BOX_NAMES[i], *(coords)) for i, coords in enumerate(
                [(0, 0, 10, 10), (20, 0, 30, 10), (0, 20, 10, 30), (20, 20, 30, 30)]))

        def data(self, xy, first=0, ids=None):
            array = np.asarray(xy, dtype=float)
            if array.ndim == 2:
                array = array[:, None, :]
            values = np.full((*array.shape[:2], 5), np.nan)
            values[:, :, :2] = array
            return TrackingDataset("self_test.csv", tuple(range(array.shape[1])) if ids is None else tuple(ids),
                                   first, values, np.ones(len(array), bool), len(array), "self-test", 0, ())

        def analyze(self, xy, **kwargs):
            return analyze_tracking(self.data(xy), self.zones(), AnalysisSettings(fps=kwargs.pop("fps", 1),
                                                                                 pixels_per_cm=kwargs.pop("pixels_per_cm", 1), **kwargs))

        def test_exclusion_changes_team_and_mean_without_changing_source(self):
            xy = [[[1, 1], [25, 5], [25, 5]]] * 2 + [[[1, 1], [1, 1], [25, 5]]] * 3
            data = self.data(xy, first=100, ids=(2, 9, 27))
            original = data.values.copy()
            settings = AnalysisSettings(fps=1, trial_start_frame=100)
            full = analyze_tracking(data, self.zones(), settings)
            self.assertIsNone(full.trials[0].team_time)
            subset = data.select_ids((9, 2))
            result = analyze_tracking(subset, self.zones(), settings)
            self.assertEqual(subset.ids, (2, 9))
            self.assertEqual(result.trials[0].reach_times, [3.0, 5.0])
            self.assertEqual(result.trials[0].team_time, 5.0)
            self.assertEqual(result.trials[0].mean_time, 4.0)
            self.assertEqual(trial_summary(result, result.trials[0])["team_size"], 2)
            single = analyze_tracking(data.select_ids((2,)), self.zones(), settings)
            self.assertEqual(single.trials[0].team_time, 3.0)
            self.assertEqual(single.trials[0].mean_time, 3.0)
            np.testing.assert_array_equal(data.values, original)
            self.assertEqual(data.ids, (2, 9, 27))
            self.assertFalse(subset.values.flags.writeable)

        def test_exclusion_preserves_identity_color_and_export_audit(self):
            data = self.data([[[1, 1], [2, 2], [3, 3]]] * 3, ids=(2, 9, 27))
            subset = data.select_ids((9, 27))
            self.assertEqual([subset.fly_number(i) for i in range(2)], [2, 3])
            self.assertEqual(subset.color(0), data.color(1))
            self.assertEqual(subset.color(1), data.color(2))
            result = analyze_tracking(subset, self.zones(), AnalysisSettings(fps=1))
            self.assertEqual([m["fly_number"] for m in result.trials[0].metrics], [2, 3])
            self.assertEqual({r["amadeus_id"] for r in iter_framewise_rows(result)}, {9, 27})
            self.assertEqual({r["fly_number"] for r in iter_framewise_rows(result)}, {2, 3})
            meta = metadata_for(result)
            self.assertEqual(meta["fly_selection"]["excluded_ids"], [2])
            self.assertEqual(meta["fly_selection"]["included_ids"], [9, 27])
            self.assertEqual(meta["trajectory_windows"][0]["fly_number"], 2)
            self.assertEqual(audit_columns(result)["excluded_amadeus_ids"], "2")

        def test_empty_or_unknown_fly_selection(self):
            data = self.data([(1, 1)] * 3, ids=(9,))
            with self.assertRaisesRegex(ValueError, "at least one fly"):
                analyze_tracking(data.select_ids(()), self.zones(), AnalysisSettings(fps=1))
            with self.assertRaisesRegex(ValueError, "Unknown AMADEUS IDs"):
                data.select_ids((27,))

        def test_completion_at_interval_end(self):
            result = self.analyze([(1, 1)] * 72, fps=24, missing_gap_seconds=0)
            self.assertEqual(result.trials[0].reach_frames, [71])
            self.assertEqual(result.trials[0].reach_times, [3.0])

        def test_shorter_than_required_never_succeeds(self):
            result = self.analyze([(1, 1)] * 71, fps=24)
            self.assertEqual(result.trials[0].reach_times, [None])

        def test_motion_inside_target_is_allowed(self):
            result = self.analyze([(1, 1), (5, 1), (9, 9)], missing_gap_seconds=0)
            self.assertEqual(result.trials[0].reach_times, [3.0])

        def test_moving_for_three_seconds_ignores_movement_threshold(self):
            xy = [(1 + 8 * i / 71, 5) for i in range(72)]
            result = self.analyze(xy, fps=24, moving_threshold_cm_s=1e9)
            self.assertEqual(result.trials[0].reach_frames, [71])
            self.assertEqual(result.trials[0].reach_times, [3.0])
            self.assertEqual(trajectory_frame_bounds(result.trials[0], 0), (0, 72))

        def test_each_fly_trajectory_uses_its_own_first_success(self):
            xy = [[[1, 1], [25, 5]], [[4, 1], [25, 5]], [[8, 8], [1, 1]],
                  [[25, 5], [4, 1]], [[28, 9], [8, 8]], [[1, 1], [25, 5]]]
            result = self.analyze(xy)
            trial = result.trials[0]
            self.assertEqual(trial.reach_frames, [2, 4])
            self.assertEqual(trajectory_frame_bounds(trial, 0), (0, 3))
            self.assertEqual(trajectory_frame_bounds(trial, 1), (0, 5))
            self.assertEqual(trajectory_frame_bounds(trial, 1, at_frame=3), (0, 4))
            self.assertEqual(result.dataset.position(5, 0), (1.0, 1.0))

        def test_unreached_trajectory_uses_available_end(self):
            result = self.analyze([(1, 1), (5, 5), (25, 5), (25, 5)])
            self.assertIsNone(result.trials[0].reach_frames[0])
            self.assertEqual(trajectory_frame_bounds(result.trials[0], 0), (0, 4))

        def test_trajectory_resets_at_next_trial(self):
            result = self.analyze([(1, 1)] * 300 + [(25, 5)] * 5, single_trial=False,
                                  target_sequence=(0, 1) + tuple(FULL_TARGET_SEQUENCE[2:]))
            self.assertEqual(trajectory_frame_bounds(result.trials[0], 0), (0, 3))
            self.assertEqual(trajectory_frame_bounds(result.trials[1], 0), (300, 303))
            self.assertEqual(trajectory_frame_bounds(result.trials[1], 0, at_frame=299), (300, 300))
            self.assertEqual(trajectory_frame_bounds(result.trials[2], 0), (305, 305))

        def test_trajectory_bounds_keep_nonzero_original_frames(self):
            data = self.data([(1, 1), (4, 4), (8, 8), (25, 5)], first=100, ids=(9,))
            result = analyze_tracking(data, self.zones(), AnalysisSettings(fps=1, trial_start_frame=100))
            self.assertEqual(trajectory_frame_bounds(result.trials[0], 0), (100, 103))
            row = trajectory_window_row(result, result.trials[0], 0)
            self.assertEqual(row['amadeus_id'], 9)
            self.assertEqual(row['trajectory_stop_reason'], 'first_target_success')

        def test_exported_video_path_and_marker_freeze_after_success(self):
            zones = tuple(Zone(BOX_NAMES[i], *rect) for i, rect in enumerate(
                [(100, 100, 130, 130), (200, 100, 230, 130), (100, 200, 130, 230), (200, 200, 230, 230)]))
            data = self.data([(102, 102), (110, 110), (120, 120), (250, 250), (350, 350)])
            result = analyze_tracking(data, zones, AnalysisSettings(fps=1))
            background = np.zeros((400, 400, 3), dtype=np.uint8)
            at_success = render_annotation(background, data, result, zones, 2, show_boxes=False)
            after_success = render_annotation(background, data, result, zones, 4, show_boxes=False)
            self.assertTrue(np.array_equal(at_success, after_success))
            self.assertEqual(data.position(4, 0), (350.0, 350.0))

        def test_live_playback_follows_after_success_without_changing_reach(self):
            from unittest.mock import patch
            data = self.data([(1, 1), (4, 4), (8, 8), (25, 25), (28, 28)])
            result = analyze_tracking(data, self.zones(), AnalysisSettings(fps=1))
            background = np.zeros((100, 100, 3), dtype=np.uint8)
            with patch(__name__ + ".draw_track_trail", wraps=draw_track_trail) as trail:
                render_annotation(background, data, result, self.zones(), 4, stop_at_success=False)
                self.assertEqual(trail.call_args.args[3], 4)
                self.assertEqual(trail.call_args.kwargs["start_frame"], 0)
            self.assertEqual(result.trials[0].reach_frames, [2])
            self.assertEqual(result.trials[0].reach_times, [3.0])
            self.assertEqual(trajectory_frame_bounds(result.trials[0], 0), (0, 3))

        def test_trajectory_drawing_never_connects_missing_gap(self):
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            draw_trajectory_path(image, np.array([(10, 10), (np.nan, np.nan), (90, 90)]), (255, 100, 80))
            self.assertTrue((image[48:53, 48:53] == 0).all())
            self.assertTrue(image[90, 90].any())

        def test_live_trail_has_no_pretrial_points(self):
            data = self.data([(90, 90)] * 3 + [(20, 20), (30, 30)])
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            draw_track_trail(image, PositionsView(data), 0, 4, 30, (255, 100, 80), start_frame=3)
            self.assertTrue((image[85:95, 85:95] == 0).all())
            self.assertTrue(image[30, 30].any())

        def test_strict_missing_resets_dwell(self):
            result = self.analyze([(1, 1), (1, 1), (np.nan, np.nan), (1, 1), (1, 1), (1, 1)], missing_gap_seconds=0)
            self.assertEqual(result.trials[0].reach_frames, [5])
            self.assertEqual(result.trials[0].reach_times, [6.0])

        def test_short_gap_requires_inside_reappearance(self):
            result = self.analyze([(1, 1), (1, 1), (np.nan, np.nan), (1, 1)], missing_gap_seconds=1)
            self.assertEqual(result.trials[0].reach_frames, [3])
            self.assertEqual(result.trials[0].reach_times, [4.0])
            self.assertEqual(result.trials[0].reach_bridged_missing_frames, [1])
            self.assertTrue(np.isnan(result.dwell_seconds[2, 0]))

        def test_pending_trailing_gap_cannot_trigger_success(self):
            result = self.analyze([(1, 1), (1, 1), (np.nan, np.nan)], missing_gap_seconds=1)
            self.assertEqual(result.trials[0].reach_times, [None])

        def test_gap_over_limit_resets_dwell(self):
            result = self.analyze([(1, 1), (1, 1), (np.nan, np.nan), (np.nan, np.nan), (1, 1), (1, 1), (1, 1)], missing_gap_seconds=1)
            self.assertEqual(result.trials[0].reach_frames, [6])

        def test_tracked_outside_always_resets(self):
            result = self.analyze([(1, 1), (1, 1), (15, 15), (1, 1), (1, 1), (1, 1)], missing_gap_seconds=1)
            self.assertEqual(result.trials[0].reach_frames, [5])

        def test_team_does_not_require_simultaneous_occupancy(self):
            xy = [[[1, 1], [25, 5]], [[1, 1], [25, 5]], [[25, 5], [1, 1]], [[25, 5], [1, 1]]]
            result = self.analyze(xy, dwell_seconds=2, missing_gap_seconds=0)
            self.assertEqual(result.trials[0].reach_times, [2.0, 4.0])
            self.assertEqual(result.trials[0].team_time, 4.0)
            self.assertEqual(result.trials[0].mean_time, 3.0)

        def test_team_average_unavailable_if_one_missing(self):
            xy = [[[1, 1], [25, 5]]] * 4
            result = self.analyze(xy, dwell_seconds=2)
            self.assertIsNone(result.trials[0].team_time)
            self.assertIsNone(result.trials[0].mean_time)

        def test_known_path_speed_and_moving_percentage(self):
            result = self.analyze([(0, 0), (2, 0), (4, 0)], fps=2, pixels_per_cm=2,
                                  dwell_seconds=1.5, moving_threshold_cm_s=1.9)
            metric = result.trials[0].metrics[0]
            self.assertEqual(metric["path_length_cm"], 2.0)
            self.assertEqual(metric["mean_speed_cm_s_tracked"], 2.0)
            self.assertEqual(metric["valid_step_duration_s"], 1.0)
            self.assertEqual(metric["time_moving_pct_tracked"], 100.0)
            self.assertEqual(metric["time_moving_s_tracked"], 1.0)
            self.assertAlmostEqual(metric["trial_averaged_speed_cm_s"], 4 / 3)

        def test_stationary_and_missing_are_distinct(self):
            result = self.analyze([(0, 0)] * 4)
            metric = result.trials[0].metrics[0]
            self.assertEqual(metric["valid_frames"], 4)
            self.assertEqual(metric["mean_speed_cm_s_tracked"], 0)
            self.assertEqual(metric["time_moving_pct_tracked"], 0)
            absent = self.analyze([(np.nan, np.nan)] * 4).trials[0].metrics[0]
            self.assertIsNone(absent["path_length_cm"])
            self.assertIsNone(absent["mean_speed_cm_s_tracked"])

        def test_movement_never_bridges_missing_positions(self):
            result = self.analyze([(0, 0), (2, 0), (np.nan, np.nan), (8, 0), (10, 0)], fps=2, pixels_per_cm=2)
            metric = result.trials[0].metrics[0]
            self.assertEqual(metric["valid_step_count"], 2)
            self.assertEqual(metric["path_length_cm"], 2)
            self.assertEqual(metric["tracking_coverage_pct"], 80)

        def test_moving_threshold_is_strictly_greater(self):
            result = self.analyze([(0, 0), (1, 0), (2, 0)], moving_threshold_cm_s=1)
            self.assertEqual(result.trials[0].metrics[0]["time_moving_pct_tracked"], 0)

        def test_jump_flags_do_not_remove_or_reassign_positions(self):
            result = self.analyze([(1, 1), (9, 1), (9, 1)], jump_threshold_cm=2)
            self.assertEqual(int(result.jump_mask.sum()), 1)
            self.assertEqual(result.trials[0].metrics[0]["path_length_cm"], 8)
            self.assertEqual(result.dataset.position(1, 0), (9, 1))

        def test_observed_occupancy_excludes_bridged_missing_time(self):
            result = self.analyze([(1, 1), (1, 1), (np.nan, np.nan), (1, 1)], missing_gap_seconds=1)
            self.assertEqual(result.trials[0].metrics[0]["occupancy_A_s"], 3)
            self.assertEqual(result.occupancy(0, 3)[0], 3)

        def test_nonzero_frame_origin_and_offset_preserved(self):
            data = self.data([(1, 1)] * 4, first=100, ids=(9,))
            result = analyze_tracking(data, self.zones(), AnalysisSettings(fps=1, pixels_per_cm=1,
                                      trial_start_frame=100, video_frame_offset=100))
            self.assertEqual(result.trials[0].reach_frames, [102])
            rows = list(iter_framewise_rows(result))
            self.assertEqual(rows[0]["csv_frame"], 100)
            self.assertEqual(rows[0]["video_frame"], 0)
            self.assertEqual(rows[0]["amadeus_id"], 9)

        def test_partial_start_keeps_time_relative_to_actual_trial_start(self):
            data = self.data([(1, 1)] * 4, first=100)
            result = analyze_tracking(data, self.zones(), AnalysisSettings(fps=1, trial_start_frame=98))
            self.assertEqual(result.trials[0].coverage_status, "partial")
            self.assertEqual(result.trials[0].reach_times, [5.0])

        def test_full_trial_boundaries_and_no_cross_boundary_motion(self):
            xy = [(25, 5)] * 7200 + [(1, 1)]
            result = self.analyze(xy, fps=24, single_trial=False)
            self.assertEqual(result.trials[0].planned_end, 7200)
            self.assertEqual(result.trials[1].start, 7200)
            self.assertEqual(result.trials[0].coverage_status, "complete")
            self.assertEqual(result.trials[1].coverage_status, "partial")
            self.assertEqual(result.trials[2].coverage_status, "no_data")
            self.assertEqual(result.trials[1].metrics[0]["valid_step_count"], 0)
            self.assertEqual(result.trials[1].metrics[0]["path_length_cm"], 0)

        def test_fractional_fps_boundaries_do_not_accumulate_drift(self):
            data = self.data([(1, 1)] * 2)
            settings = AnalysisSettings(fps=23.976, single_trial=False, trial_start_frame=50)
            definitions = trial_definitions(data, settings)
            for i, (_, _, start, end) in enumerate(definitions):
                self.assertEqual(start, 50 + math.floor(i * 300 * 23.976 + .5))
                self.assertEqual(end, 50 + math.floor((i + 1) * 300 * 23.976 + .5))

        def test_gap_limit_never_rounds_up(self):
            self.assertEqual(AnalysisSettings(fps=24, missing_gap_seconds=.12).gap_frames, 2)
            self.assertEqual(AnalysisSettings(fps=24, missing_gap_seconds=.25).gap_frames, 6)

        def test_missing_scale_does_not_invent_movement(self):
            result = self.analyze([(1, 1)] * 4, pixels_per_cm=None)
            self.assertEqual(result.trials[0].reach_times, [3.0])
            self.assertIsNone(result.trials[0].metrics[0]["path_length_cm"])
            self.assertIsNone(result.trials[0].metrics[0]["time_moving_pct_tracked"])

        def test_invalid_settings_fail_explicitly(self):
            for kwargs in ({"fps": float("nan")}, {"fps": 0}, {"pixels_per_cm": 0},
                           {"missing_gap_seconds": 3}, {"moving_threshold_cm_s": -1}, {"jump_threshold_cm": 0}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    AnalysisSettings(**({"fps": 24} | kwargs))

        def test_overlapping_regions_rejected(self):
            zones = list(self.zones())
            zones[1] = Zone("B", 5, 5, 15, 15)
            with self.assertRaises(ValueError):
                validate_zones(zones)

        def test_shared_edge_is_assigned_once_by_declared_priority(self):
            zones = list(self.zones())
            zones[1] = Zone("B", 10, 0, 20, 10)
            result = analyze_tracking(self.data([(10, 5)] * 4), zones, AnalysisSettings(fps=1))
            self.assertEqual(result.assignment[:, 0].tolist(), [0, 0, 0, 0])
            self.assertEqual(result.trials[0].metrics[0]["occupancy_A_s"], 4)
            self.assertEqual(result.trials[0].metrics[0]["occupancy_B_s"], 0)

        def test_same_target_in_consecutive_trials_still_resets_dwell(self):
            result = self.analyze([(1, 1)] * 14400, fps=24, single_trial=False, target_sequence=(0,) * 10)
            self.assertEqual(result.trials[0].reach_frames, [71])
            self.assertEqual(result.trials[1].reach_frames, [7271])
            self.assertEqual(result.trials[1].reach_times, [3.0])
            self.assertEqual(result.dwell_seconds[7200, 0], 1 / 24)

        def test_schedule_with_no_overlap_fails_explicitly(self):
            with self.assertRaises(ValueError):
                analyze_tracking(self.data([(1, 1)] * 4, first=10000), self.zones(),
                                 AnalysisSettings(fps=1, single_trial=False))

        def test_heading_does_not_change_analysis(self):
            data = self.data([(1, 1)] * 4)
            data.values[:, :, 4] = 275
            result = analyze_tracking(data, self.zones(), AnalysisSettings(fps=1))
            self.assertEqual(result.trials[0].reach_times, [3.0])

        def test_json_has_no_nan_or_infinity(self):
            result = self.analyze([(np.nan, np.nan)] * 4)
            output = json.dumps(metadata_for(result), allow_nan=False)
            self.assertNotIn("NaN", output)

        def test_cancellation_does_not_produce_a_result(self):
            event = threading.Event()
            event.set()
            with self.assertRaises(CancelledError):
                analyze_tracking(self.data([(1, 1)] * 4), self.zones(), AnalysisSettings(fps=1), cancel=event)

        def test_loader_sparse_rows_and_original_ids(self):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "data.csv"
                path.write_text("frame,cx2,cy2,w2,h2,cx10,cy10,w10,h10\n100,0,0,5,2,8,8,5,2\n102,1,1,5,2,,,,\n", encoding="utf-8")
                data = load_amadeus_csv(path)
                self.assertEqual(data.ids, (2, 10))
                self.assertEqual(data.first_frame, 100)
                self.assertEqual(data.frame_count, 3)
                self.assertEqual(data.position(100, 0), (0, 0))
                self.assertIsNone(data.position(101, 0))
                self.assertEqual(data.heading_ids, ())
                self.assertTrue(data.warnings)

        def test_bad_csv_rows_and_duplicate_frames_rejected(self):
            header = "frame,cx0,cy0,w0,h0\n"
            bad = ["0,1,1,5,2\n0,2,2,5,2\n", "2,1,1,5,2\n1,2,2,5,2\n", "0,1,1,5\n",
                   "0,oops,1,5,2\n", "0,inf,1,5,2\n", "0.5,1,1,5,2\n"]
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "bad.csv"
                for text in bad:
                    path.write_text(header + text, encoding="utf-8")
                    with self.subTest(text=text), self.assertRaises(ValueError):
                        load_amadeus_csv(path)

        def test_duplicate_column_names_rejected(self):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "bad.csv"
                path.write_text("frame,cx0,cy0,cx0\n0,1,1,1\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_amadeus_csv(path)

        def test_partial_coordinate_is_missing_and_raw_value_preserved(self):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "partial.csv"
                path.write_text("frame,cx0,cy0,w0,h0\n0,0,,5,2\n", encoding="utf-8")
                data = load_amadeus_csv(path)
                self.assertFalse(data.valid[0, 0])
                self.assertEqual(data.values[0, 0, 0], 0)
                self.assertTrue(data.warnings)

        def test_old_one_based_box_json_maps_each_box_once(self):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "zones.json"
                boxes = {str(i + 1): z.as_dict() for i, z in enumerate(self.zones())}
                path.write_text(json.dumps({"boxes": boxes}), encoding="utf-8")
                zones, _ = load_zones_json(path)
                self.assertEqual([z.x1 for z in zones], [0, 20, 0, 20])
                self.assertEqual([z.y1 for z in zones], [0, 0, 20, 20])

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NumericalTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)



def main():
    parser = argparse.ArgumentParser(description="AMADEUS fly target analysis GUI")
    parser.add_argument("--self-test", action="store_true", help="Run reproducible numerical checks")
    parser.add_argument("--check-csv", metavar="PATH", help="Validate an AMADEUS CSV without opening a window")
    args = parser.parse_args()
    if args.self_test:
        run_self_tests()
        return
    if args.check_csv:
        data = load_amadeus_csv(args.check_csv)
        print(json.dumps({"ids": data.ids, "csv_rows": data.csv_rows, "first_frame": data.first_frame,
                          "last_frame": data.end_frame - 1, "missing_positions_by_id": {
                              str(ident): int((~data.valid[:, tid]).sum()) for tid, ident in enumerate(data.ids)},
                          "warnings": data.warnings, "input_sha256": data.source_sha256}, indent=2))
        return
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise SystemExit(f"A graphical desktop and Tkinter are required. Details: {exc}") from exc
    app = TargetTimeApp(root)
    def report_error(exc_type, value, tb):
        app.pause_playback()
        messagebox.showerror("Interface error", f"{exc_type.__name__}: {value}\nNo numerical data was modified.")
    root.report_callback_exception = report_error
    root.mainloop()


if __name__ == "__main__":
    main()

