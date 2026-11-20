#!/usr/bin/env python3
"""Fig. for the build log: each converted jenscolt part (reference mesh, grey) beside its parametric rebuild (colour),
same view and framing. The part files come from each design's `build.py` (out/); the reference meshes are jenscolt's.

    uv run python tools/conversions_figure.py OUT.png
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import trimesh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figures import draw, simplify  # noqa: E402

ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "cad", "carcass-jenscolt")
ROWS = [  # name, view, reference files, (design folder, part files), colour
    ("body", (28, 130), ["spideybot_body.stl"], ("body", ["body.stl"]), "#d9822b"),
    ("base", (-35, 130), ["spideybot_base_bowl.stl"], ("base", ["base.stl"]), "#4a7fb5"),
    ("legs (blade and arm)", (15, 150), ["spideybot_L_leg1.stl", "spideybot_L_leg2.stl"],
     ("legs", ["leg-blade.stl", "leg-arm.stl"]), "#c0392b"),
    ("eyes", (20, 150), ["spideybot_eye.stl", "spideybot_small_eye.stl", "spideybot_sensor.stl"],
     ("eyes", ["eye.stl", "small-eye.stl", "sensor.stl"]), "#2e8b57"),
]


def load(path, cell=0.4):
    return simplify(trimesh.load(path, force="mesh"), cell)


def row_up(meshes, gap=6.0):
    """Parts that sit far apart in jenscolt's frame (the three eyes): centred and set side by side."""
    x = 0.0
    for it in meshes:
        m = it["mesh"].copy()
        m.apply_translation(-m.bounds.mean(axis=0))
        w = m.extents[0]
        m.apply_translation([x + w / 2, 0, 0])
        x += w + gap
        it["mesh"] = m
    return meshes


def main(out):
    fig, axes = plt.subplots(len(ROWS), 2, figsize=(9, 3.6 * len(ROWS)))
    for r, (name, view, refs, (folder, parts), colour) in enumerate(ROWS):
        ref = [{"mesh": load(os.path.join(REF, f)), "color": "#9a9a9a"} for f in refs]
        des = [{"mesh": load(os.path.join(ROOT, "cad", folder, "out", f)), "color": colour} for f in parts]
        if name == "eyes":
            ref, des = row_up(ref), row_up(des)
        draw(axes[r, 0], ref, view)
        draw(axes[r, 1], des, view)
        axes[r, 0].set_title(f"{name}: jenscolt's mesh (reference)", fontsize=12)
        axes[r, 1].set_title(f"{name}: rebuilt from parameters", fontsize=12)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    fig.savefig(out, dpi=110)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "conversions.png")
