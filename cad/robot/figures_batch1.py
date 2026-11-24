"""Figures of the batch-1 entry (build-log/4-looks-first.md, «Batch 1 result»).

  .venv/bin/python cad/robot/figures_batch1.py

batch1-limits.png: the sizes the design asks for against what a 0.4 mm nozzle at 0.20 mm layers prints.
Sizes are read from the CAD code (module M, wall W, M2 radii, fits), not typed here.
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import fits as F
import drive as D

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "build-log", "images")
LINE, LAYER = 0.4, 0.2

rows = [  # (label, size mm, what it is, ok?)
    ("Index dot, diameter", 2 * 0.35, "dots on the cranks that say which is which"),
    ("Index dot, depth", 0.35, "sunk into the crank hub"),
    ("Gear tooth, thickness at the pitch circle", math.pi * D.M / 2, f"module {D.M}"),
    ("Gear tip room (radial)", F.GEAR_TIP.side, "assumed, never printed"),
    ("M2 self-tapping pilot, diameter", 2 * D.M2_PILOT_R, "assumed, never printed"),
    ("Drive-unit ear 2, height", 1.0, "snapped (now 2.0 mm plates)"),
    ("Wall (3 lines)", D.W, "snapped when touched"),
    ("M2 screw hole, diameter", 2 * D.M2_HOLE_R, "M2 screw + 0.15 a side"),
]
fig, ax = plt.subplots(figsize=(10, 4.6))
for i, (lab, v, note) in enumerate(rows[::-1]):
    c = "#d9534f" if v < 2 * LINE else "#f0ad4e" if v < 3 * LINE else "#5cb85c"
    ax.barh(i, v, color=c, height=0.6)
    ax.text(max(v, 0.85) + 0.05, i, f"{v:.2f} mm  ·  {note}", va="center", fontsize=10)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=10)
ax.axvline(LINE, color="k", ls="--"); ax.text(LINE + 0.03, len(rows) + 0.15, "one line 0.4", ha="left", fontsize=10)
ax.axvline(2 * LINE, color="k", ls=":"); ax.text(2 * LINE + 0.03, len(rows) - 0.3, "two lines", ha="left", fontsize=10)
ax.axvline(LAYER, color="grey", ls="-", lw=0.8); ax.text(LAYER + 0.03, -0.9, "one layer 0.2", ha="left", fontsize=9, color="grey")
ax.set_xlim(0, 4.6); ax.set_ylim(-1.1, len(rows) + 0.4); ax.set_xlabel("designed size, mm (S 0.70, 0.4 mm nozzle)")
ax.set_title("Batch 1: sizes asked of the printer; red = under two lines, orange = under three", fontsize=11)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "batch1-limits.png"), dpi=130)

