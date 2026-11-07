#!/usr/bin/env python3
"""Render binary STL files to a PNG grid and print a Markdown table with their sizes.

Usage:
    python3 stl_preview.py OUT.png part1.stl part2.stl ... [--elev 25] [--azim -60] [--cols 3]

Needs numpy and matplotlib (pip install numpy matplotlib).
"""
import argparse
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

RECORD = np.dtype([("normal", "<3f4"), ("v", "<9f4"), ("attr", "<u2")])


def load(path):
    data = np.fromfile(path, dtype=np.uint8)
    n = int(data[80:84].view("<u4")[0])
    if len(data) != 84 + 50 * n:
        raise ValueError(f"{path}: not a binary STL")
    return np.frombuffer(data[84:84 + 50 * n].tobytes(), dtype=RECORD)["v"].reshape(-1, 3, 3).astype(float)


def draw(ax, tris, elev, azim, color="#c0392b"):
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
    shade = 0.35 + 0.65 * np.abs(normals @ light)
    faces = np.array(matplotlib.colors.to_rgb(color))[None, :] * shade[:, None]
    ax.add_collection3d(Poly3DCollection(tris, facecolors=faces, edgecolors="none"))
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    mid, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(mid[0] - r, mid[0] + r)
    ax.set_ylim(mid[1] - r, mid[1] + r)
    ax.set_zlim(mid[2] - r, mid[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev, azim)
    ax.set_axis_off()
    return hi - lo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("stls", nargs="+")
    p.add_argument("--elev", type=float, default=25)
    p.add_argument("--azim", type=float, default=-60)
    p.add_argument("--cols", type=int, default=3)
    a = p.parse_args()

    cols = min(a.cols, len(a.stls))
    rows = -(-len(a.stls) // cols)
    fig = plt.figure(figsize=(4 * cols, 4 * rows), dpi=110)
    print("| File | X × Y × Z (mm) | Triangles |\n|---|---|---|")
    for i, path in enumerate(a.stls):
        tris = load(path)
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        size = draw(ax, tris, a.elev, a.azim)
        name = os.path.basename(path)
        ax.set_title(f"{name}\n{size[0]:.0f} × {size[1]:.0f} × {size[2]:.0f} mm", fontsize=11)
        print(f"| `{name}` | {size[0]:.1f} × {size[1]:.1f} × {size[2]:.1f} | {len(tris)} |")
    plt.tight_layout()
    plt.savefig(a.out)


if __name__ == "__main__":
    main()
