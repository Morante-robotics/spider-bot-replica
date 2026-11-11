#!/usr/bin/env python3
"""Figure: each idler between its two crankshafts, with the cranks at their designed phases (crank angle 0°).
Top row: v1 (no gear offsets, 11/10/20 teeth, no backlash), each idler at its best angle; red is where the teeth would
have to pass through each other. Bottom row: v2 (gear offsets per crankshaft, 12/12/20 teeth, +CD_EXTRA centre
distance), each idler at its designed phase, with the measured gaps. Writes images/gear-phase.png.

    python3 gear_phase_figure.py
"""
import os

import matplotlib
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import build as B  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def outline(teeth, ang, y, z):
    return affinity.translate(affinity.rotate(Polygon(B.gear_profile(teeth)), ang, origin=(0, 0), use_radians=True),
                              y, z)


def fill(ax, p, color, z=1):
    for g in getattr(p, "geoms", [p]):
        if g.is_empty or g.geom_type != "Polygon":
            continue
        ax.fill(*g.exterior.xy, color=color, zorder=z, lw=0)
        for h in g.interiors:
            ax.fill(*h.xy, color="white", zorder=z, lw=0)


def v1_layout():
    """v1: idlers from 10 teeth up, at the exact centre distance; gears not offset."""
    sh, rs, out = B.shaft_yz(), B.MOD * B.SHAFT_TEETH / 2, []
    for (y1, z), (y2, _) in zip(sh, sh[1:]):
        half, n = (y2 - y1) / 2, 10
        while rs + B.MOD * n / 2 < half + 1.5:
            n += 1
        cd = rs + B.MOD * n / 2
        out.append(((y1 + y2) / 2, z - np.sqrt(cd ** 2 - half ** 2), n))
    return out, [0.0] * 4


def draw(ax, k, idl, off, phase, v2):
    sh = B.shaft_yz()
    y, z, n = idl[k]
    shafts = [outline(B.SHAFT_TEETH, off[j], *sh[j]) for j in (k, k + 1)]
    if phase is None:
        cand = np.linspace(0, 2 * np.pi / n, 240, endpoint=False)
        phase = min(cand, key=lambda p: sum(outline(n, p, y, z).intersection(s).area for s in shafts))
    idler = outline(n, phase, y, z)
    for s in shafts:
        fill(ax, s, "#9db4d6")
    fill(ax, idler, "#f2c14e")
    area = 0.0
    for s in shafts:
        x = idler.intersection(s)
        area += x.area
        fill(ax, x, "#d62728", 3)
    for j in (k, k + 1):                               # crank direction at crank angle 0 (right side)
        ph = np.pi * B.sim.GROUP["R"][j]
        ax.plot([sh[j][0], sh[j][0] - 3.91 * np.cos(ph)], [sh[j][1], sh[j][1] + 3.91 * np.sin(ph)], color="k", lw=2,
                zorder=4)
    ax.set_aspect("equal")
    ax.set_xlim(sh[k][0] - 8, sh[k + 1][0] + 8), ax.set_ylim(z - n / 2 - 2, sh[k][1] + 8)
    ax.set_xticks([]), ax.set_yticks([])
    if v2:
        gaps = [idler.distance(s) for s in shafts]
        verdict = f"meshes both: gaps {gaps[0]:.2f} and {gaps[1]:.2f} mm"
        offs = f"gear offsets {np.degrees(off[k]):.1f}° and {np.degrees(off[k + 1]):.1f}°"
    else:
        verdict = "meshes both" if area < 0.01 else f"best angle: {area:.1f} mm² of tooth in tooth"
        offs = "no gear offsets"
    ax.set_title(f"{'v2' if v2 else 'v1'} · idler {k + 1} ({n} teeth), crankshafts {k + 1}–{k + 2}\n{offs}\n{verdict}",
                 fontsize=9)


fig, axes = plt.subplots(2, 3, figsize=(13, 9))
idl1, off1 = v1_layout()
for k in range(3):
    draw(axes[0, k], k, idl1, off1, None, False)
    draw(axes[1, k], k, B.idlers(), B.gear_offsets(), B.idler_phase(k), True)
fig.suptitle("Crank angle 0°, cut through the gears (robot Y across, Z up). Black: right crank of each shaft.",
             fontsize=10)
fig.tight_layout()
out = os.path.join(HERE, "images", "gear-phase.png")
fig.savefig(out, dpi=110, bbox_inches="tight")
print("wrote", out)
