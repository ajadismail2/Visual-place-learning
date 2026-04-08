# Drosophila Visual Place Learning — Analysis Pipeline

**A step-by-step guide for neuroscience researchers**

This pipeline lets you go from a raw experiment video to publication-ready behavioral metrics — Time to Target, Path Length, Direction Index, Speed, Quadrant Occupancy, and Probe Learning Index — with no prior programming experience required.

---

## What does this pipeline actually do?

When flies explore the arena, a camera records their movement. This pipeline takes those recordings and answers questions like:

- **Did the flies learn?** (Do they find the cool tile faster over trials?)
- **Are they navigating more directly over time?** (Shorter, straighter paths?)
- **Where do they search during the probe trial?** (Do they go to where the cool tile *was*, even when it's absent?)

The pipeline has three stages, each handled by a separate tool:

```
Your experiment video
        │
        ▼
  ① arena_calibrator.py   ──►  arena_config.json
        │
        ▼
  ② SLEAP (sleap.ai)      ──►  tracking.slp  (fly positions, every frame)
        │
        ▼
  ③ place_learning_analysis.py  ──►  CSVs + figures
```

---

## Table of Contents

1. [Before You Start — Installation](#1-before-you-start--installation)
2. [Stage 1 — Calibrate the Arena](#2-stage-1--calibrate-the-arena)
3. [Stage 2 — Track Flies with SLEAP](#3-stage-2--track-flies-with-sleap)
4. [Stage 3 — Run the Analysis](#4-stage-3--run-the-analysis)
5. [Understanding Your Results](#5-understanding-your-results)
6. [Common Mistakes and Fixes](#6-common-mistakes-and-fixes)
7. [Glossary](#7-glossary)

---

## 1. Before You Start — Installation

You only need to do this once.

### What you need

- A computer running **Windows**, **macOS**, or **Linux**
- **Python 3.10 or newer** — download from [python.org](https://www.python.org/downloads/)
- The two scripts: `arena_calibrator.py` and `place_learning_analysis.py`

### Install the required Python libraries

Open a **Terminal** (macOS/Linux) or **Command Prompt** (Windows) and paste this command:

```
pip install opencv-python pillow numpy pandas matplotlib h5py
```

Press Enter and wait for it to finish. You will see a lot of text scrolling — that is normal.

> **What are these libraries?**
> Think of them as toolboxes Python needs to open videos, do math on coordinates, and draw figures. You install them once and never think about them again.

### Check that it worked

```
python --version
```

You should see something like `Python 3.11.2`. If you see an error, try `python3 --version` instead. On some systems Python is called `python3` — if so, replace `python` with `python3` everywhere in this guide.

---

## 2. Stage 1 — Calibrate the Arena

**Script:** `arena_calibrator.py`  
**What it produces:** `arena_config.json` — a small file that records exactly where the arena boundary, the four Peltier plates, and the scale reference are in your video frame.

**You only need to do this once per camera setup.** If your camera position, zoom, or arena placement does not change between experiments, you can reuse the same `arena_config.json` for all your recordings.

### Opening the calibrator

```
python arena_calibrator.py
```

A window will open that looks like this:

```
┌────────────────────────────────────────────────────────────────┐
│  Arena Tool    │                                               │
│  ─────────     │         (your video frame will appear here)  │
│  1. Load Video │                                               │
│  2. Define     │                                               │
│     Arena      │                                               │
│  3. Rotate     │                                               │
│     Quadrants  │                                               │
│  4. Add 4      │                                               │
│     Grids      │                                               │
│  5. Set Scale  │                                               │
│  6. Export     │                                               │
│                │                                               │
│  [Load] [Arena] [Rotate] [Grid] [Scale] [Export]              │
│  [Reset Arena] [Undo Grid] [Clear Grids] [Reset Scale]        │
└────────────────────────────────────────────────────────────────┘
```

The **left panel** shows your current progress through the six steps. Steps turn green as you complete them. The **status text** below the steps tells you exactly what to click next at each stage.

---

### Step 1 — Load Video

Click the **`Load`** button. A file browser opens. Navigate to any video from your experiment (`.mp4`, `.avi`, `.mov`). You only need **one representative frame** from any trial — the calibration tool reads just the first frame.

The video frame will appear in the main canvas area.

> **Tip:** Use a video where the arena and all four Peltier plates are clearly visible and the flies are not in the way. The very first frame of a recording before flies are introduced works well.

---

### Step 2 — Define the Arena Boundary

This step tells the software where the circular boundary of your arena is.

1. Click **`Arena`** in the button bar.
2. The status text will say: *"Drag from center → edge"*
3. **Click and hold** on the exact center of the circular arena, then **drag outward** until the green circle aligns with the edge of the arena wall. **Release** the mouse.

A green circle will appear on the frame. Four white lines divide it into quadrants, and the labels Q1–Q4 appear.

**If the circle is wrong:** Click **`Reset Arena`** and try again.

> **Why does this matter?**  
> The circle boundary defines what "inside the arena" means. The quadrant lines drawn from the center are used to measure which zone a fly is in at any given moment.

---

### Step 3 — Rotate the Quadrant Lines

The four white dividing lines might not align with your Peltier plate boundaries. This step rotates them until they match.

1. Click **`Rotate`** once — the lines rotate 90°.
2. Keep clicking **`Rotate`** until the quadrant boundaries match the physical boundaries between your Peltier plates.
3. If you overshoot, click **`Reset Rot`** to go back to 0° and try again.

> **Note:** You need exactly one click (90°) for most setups where the Peltier array is axis-aligned. If your array is tilted in the camera frame, rotate to the closest match.

---

### Step 4 — Mark All Four Peltier Grids

This is the most important step. You will draw a rectangle around each of the four Peltier plates (the individual temperature zones on the arena floor).

**Repeat this process four times — once per plate:**

1. Click **`Grid`**. The status text says: *"Click Top-left"*
2. Click the **top-left corner** of one Peltier plate.
3. Status text changes to *"Click Top-right"* — click the top-right corner.
4. Click **Bottom-right**, then **Bottom-left**.
5. The status text says *"Grid saved ✓"* and a blue rectangle appears over the plate.
6. Click **`Grid`** again for the next plate.

Do this for all four plates, in any order.

**If you mis-click a corner:** Click **`Undo Grid`** to remove the last completed grid and redo it.  
**If the whole set is wrong:** Click **`Clear Grids`** to start over.

> **Corner clicking order matters.** Always go: Top-left → Top-right → Bottom-right → Bottom-left (clockwise). If you go in the wrong order, the tool will detect this and warn you during Export.

> **What counts as a "corner"?**  
> Look at the visible edge of each Peltier tile in the video frame. Click as close to each physical corner as you can. The rectangle doesn't need to be perfect — a few pixels off is fine. What matters is that the rectangles don't overlap each other.

---

### Step 5 — Set the Scale

This converts pixel distances in the video to real-world centimetres, so that speed and path length are reported in cm/s and cm rather than pixels.

1. Click **`Scale`**. The status text says: *"Click 2 points"*
2. Click any two points in the image whose **real-world distance you know precisely.** The most reliable reference is the diameter of the arena (e.g., you know your arena is 20.32 cm across).
3. A small dialog box pops up showing the pixel distance between your two points (e.g., `348.2 px`).
4. Type the **real distance in centimetres** in the text box (e.g., `20.32`) and click **OK**.

**If you mis-click:** Click **`Reset Scale`** and try again.

> **Good scale references:**
> - The inner diameter of the arena ring (measure with calipers)
> - The width of a single Peltier tile (if you know it — standard 1-inch tiles = 2.54 cm each; 8×8 array = 20.32 cm total)

---

### Step 6 — Export the Config File

Click **`Export`**.

The tool checks that:
- All four grids are properly defined
- No grid corners are in the wrong order
- The scale has been set

If any check fails, a warning message explains what to fix.

If everything is correct, a **Save dialog** opens. Name the file something clear like `arena_config_2024_rig1.json` and save it somewhere you will remember.

The resulting file is a small text file that looks like this (abbreviated):

```json
{
  "arena": {
    "center_px": [650, 512],
    "radius_px": 480.3,
    "quadrant_rotation_deg": 0
  },
  "peltier_grids": [
    {
      "name": "grid_1",
      "corners_px": [[230, 290], [648, 290], [648, 510], [230, 510]]
    },
    ...
  ],
  "calibration": {
    "px_per_cm": 23.6
  }
}
```

> Keep this file alongside your data. If you ever change your camera setup, redo this calibration and save a new config file with a new name.

---

## 3. Stage 2 — Track Flies with SLEAP

SLEAP is a separate, dedicated fly-tracking program developed by the Murthy lab at Princeton. You use it to extract fly positions from your videos — this pipeline then reads those positions for analysis.

**SLEAP website:** [sleap.ai](https://sleap.ai)  
**SLEAP documentation:** [sleap.ai/docs](https://sleap.ai/docs)

### Installing SLEAP

Follow the official SLEAP installation guide at [sleap.ai](https://sleap.ai). The recommended method is via conda (Anaconda):

```
conda create -y -n sleap -c conda-forge -c nvidia -c sleap sleap
conda activate sleap
```

> SLEAP has its own environment — keep it separate from the Python environment you use for the calibrator and analysis scripts.

### What SLEAP needs from you

1. **Your experiment videos** — one file per trial.
2. **A trained model** — SLEAP needs to have learned what a fly looks like. If your lab already has a trained model for your rig, you can skip the labelling steps and jump straight to inference.

### The SLEAP workflow at a glance

If you are doing this for the first time:

```
New SLEAP Project
      │
      ▼
Label ~100–200 frames manually
(draw dots on fly body parts: thorax, head, abdomen)
      │
      ▼
Train a model
(can take 30 min – several hours, GPU recommended)
      │
      ▼
Run inference on all trial videos
(SLEAP finds the fly positions automatically)
      │
      ▼
Review and correct tracks
      │
      ▼
Export as analysis HDF5 (.h5)
```

For detailed labeling and training instructions, follow the [SLEAP Colab tutorial](https://colab.research.google.com/github/murthylab/sleap/blob/main/notebooks/Training_and_inference_on_an_example_dataset.ipynb).

### Running inference (the step you repeat for every video)

Once you have a trained model, inference is what you run for every new video. In the SLEAP GUI:

1. Open your `.slp` project file (or start a new one with **File → New Project**)
2. Go to **Predict → Run Inference**
3. Select your trained model
4. Select the video(s) you want to process
5. Click **Run**

SLEAP will output a `.slp` file containing predicted fly positions for every frame.

### Reviewing tracks

After inference, open the resulting `.slp` file and scroll through the video. Common issues to check:

- **Ghost tracks:** SLEAP sometimes creates spurious short tracks for shadows or reflections. Delete any track shorter than ~50 frames.
- **Identity swaps:** If two flies cross and SLEAP swaps their identities, the track will show an abrupt large jump. Correct these in the GUI by selecting the affected frames and using **Track → Fix Track**.
- **Missing detections:** Frames where SLEAP lost a fly will appear as gaps (dotted lines) in the track timeline. For short gaps (< 10 frames) this is acceptable — the analysis script handles missing data.

### Exporting for analysis

After reviewing, export the tracking data as an **Analysis HDF5 file**:

**GUI method:**  
Go to **File → Export Analysis HDF5** and save as `trial_01.h5`, `trial_02.h5`, etc.

**Command-line method:**
```
conda activate sleap
sleap-convert --format analysis trial_01.slp -o trial_01.h5
```

Repeat this for every trial, including the probe trial. You should end up with files like:

```
experiment_2024_01_15/
    trial_01.h5
    trial_02.h5
    trial_03.h5
    ...
    trial_10.h5
    probe.h5
    arena_config.json
```

---

## 4. Stage 3 — Run the Analysis

**Script:** `place_learning_analysis.py`

This script reads all your `.h5` tracking files plus the `arena_config.json` and produces CSV tables and figures.

### Opening a Terminal in your data folder

**Windows:** Hold Shift and right-click in the folder containing your files → "Open PowerShell window here"  
**macOS:** Right-click the folder → "New Terminal at Folder" (or use Terminal and type `cd` followed by dragging the folder in)  
**Linux:** Right-click → "Open Terminal Here"

### Basic command — full experiment

Replace the parts in angle brackets `< >` with your actual values:

```
python place_learning_analysis.py \
    --files trial_01.h5 trial_02.h5 trial_03.h5 trial_04.h5 trial_05.h5 \
            trial_06.h5 trial_07.h5 trial_08.h5 trial_09.h5 trial_10.h5 \
    --probe probe.h5 \
    --config arena_config.json \
    --target-grid 1 \
    --start-grid 0 \
    --fps 25 \
    --output results/
```

On Windows, replace each `\` at the end of a line with a backtick `` ` `` (PowerShell) or remove the line breaks entirely and type it all on one line.

### Explaining each option

| Option | What it means | Example |
|--------|--------------|---------|
| `--files` | Your tracking files, in trial order | `trial_01.h5 trial_02.h5 ...` |
| `--probe` | Your probe trial file (no cool tile) | `probe.h5` |
| `--config` | The arena calibration JSON from Stage 1 | `arena_config.json` |
| `--target-grid` | Which of the 4 Peltier plates is the cool tile, **counting from 0** | `1` means the 2nd plate you drew |
| `--start-grid` | Which plate the flies start on, **counting from 0** | `0` means the 1st plate you drew |
| `--fps` | Camera frame rate in frames per second | `25` |
| `--output` | Folder where results will be saved | `results/` |

> **Which grid number is the cool tile?**  
> The grids are numbered in the order you drew them in the calibrator. `grid_1` is index `0`, `grid_2` is index `1`, and so on. If you drew the cool tile's plate **second**, use `--target-grid 1`.

### Single-trial mode (for testing)

If you want to check that everything works before processing all trials:

```
python place_learning_analysis.py \
    --files trial_01.h5 \
    --config arena_config.json \
    --target-grid 1 \
    --fps 25 \
    --output test_results/
```

### What the script prints while running

As it runs, the script prints progress to the terminal:

```
[CONFIG] Arena center=[650, 512], radius=480.3px, scale=23.60px/cm
[CONFIG] 4 Peltier grids loaded
[CONFIG] Grid → Quadrant mapping: {0: 0, 1: 1, 2: 2, 3: 3}
[CONFIG] Target grid 1 → Q1

[TRIAL 1] trial_01.h5
  15 tracks × 7500 frames @ 25.0fps
  reached target: 14/15 flies
  time to target: 87.3 ± 9.2 s
  path length:    112.4 ± 15.1 cm
  mean speed:     1.21 ± 0.04 cm/s
  direction correct: 46.67%

[TRIAL 2] trial_02.h5
  ...

[DONE] All outputs in → results/
```

---

## 5. Understanding Your Results

All outputs appear in your `--output` folder.

### Output files

```
results/
    per_fly_metrics.csv          ← every metric for every fly, every trial
    trial_summaries.csv          ← mean ± SEM per trial (use this for stats)
    probe_metrics.csv            ← probe trial results per fly
    trajectories_trial01.png     ← fly path plots
    ...
    learning_curve.png           ← the key learning figure
    quadrant_occupancy.png       ← where flies spend time each trial
    probe_learning_index.png     ← probe trial learning score
    speed.png                    ← walking speed across trials
```

---

### The metrics explained

#### Time to Target
*The most direct measure of learning.*

How long each fly took to reach the cool tile, in seconds. As flies learn where the cool tile is relative to the visual panorama, this number should **decrease across trials** (the learning curve).

A fly that never reaches the target within the trial is recorded as `NaN` (not a number) — it is excluded from the mean for that trial.

#### Path Length (cm)
How far each fly walked before reaching the target, in centimetres. A learning fly not only arrives faster, but also walks a **shorter total distance** because it takes a more direct route.

#### Direction Index
A measure of how directly flies head toward the correct quadrant after leaving their starting zone.

- `1.0` = the fly went straight to the target quadrant first
- `0.0` = the fly went to the wrong quadrant first
- The group mean should **increase across trials** as flies learn.

#### Mean Speed (cm/s)
Average walking speed during navigation. This should **stay roughly constant** across trials — it serves as a negative control confirming that learning effects are due to navigation strategy, not changes in locomotion.

If speed drops dramatically, flies may be unhealthy or the arena may be too hot. If speed increases, flies might be more motivated to escape heat by Trial 10 — worth checking.

#### Quadrant Occupancy
The percentage of time each fly spends in each of the four zones during a trial. As learning proceeds, flies should spend **more time in the target quadrant** and less time in the others.

Chance performance = 25% per quadrant. In the target quadrant you should see a progressive rise above 25% over trials.

#### Probe Learning Index *(most important for the probe trial)*

This is the key metric from the Ofstad et al. (2011) paper. It measures **where flies search when the cool tile is absent**.

**Formula:**

```
                time in target quadrant – time in opposite quadrant
PLI = ─────────────────────────────────────────────────────────────
              time in target quadrant + time in opposite quadrant
```

- **PLI > 0** → flies preferentially search where the cool tile was (evidence of place memory)
- **PLI = 0** → flies search randomly (no place memory)
- **PLI < 0** → flies avoid the target quadrant (would be unusual)

The score is computed during the first **60 seconds** after each fly leaves its starting quadrant, matching the original paper's method.

A PLI significantly greater than zero (one-sample t-test against 0) is your main evidence for visual place learning.

---

### Reading the figures

**`learning_curve.png`** — Two panels showing how Time to Target and Path Length change across trials. You want to see both lines going down across trials 1–10.

**`quadrant_occupancy.png`** — A stacked bar chart. Each bar is one trial. As learning progresses, the target quadrant's color should grow taller.

**`probe_learning_index.png`** — A scatter plot with individual fly scores and a mean ± SEM bar. The dashed line at 0 is chance. A mean bar clearly above 0 is your learning result.

**`speed.png`** — Should look flat (constant speed across trials). Any dramatic change is a red flag worth investigating.

**`trajectories_trialXX.png`** — Individual fly paths overlaid on the arena for each trial. In early trials you will see meandering paths. In late trials, paths should be shorter and more direct. Colored zones show the Peltier grid boundaries.

---

### Doing statistics on the CSV files

Open `trial_summaries.csv` in Excel or any statistics software. Each row is one trial, with columns for mean and SEM of each metric.

Typical analyses:
- **Learning curve:** Repeated-measures ANOVA across trials (paired by experiment/day)
- **Probe PLI:** One-sample t-test of `probe_learning_index` against 0
- **Comparison across genotypes:** Between-group ANOVA on PLI or time-to-target at trial 10

`per_fly_metrics.csv` gives you individual fly data, useful for mixed-effects models treating individual flies as the unit of analysis.

---


