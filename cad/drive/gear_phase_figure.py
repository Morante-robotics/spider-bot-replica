#!/usr/bin/env python3
"""Figure: each idler turned to its best angle between its two crankshafts, with the cranks at their designed phases.
Red is where the teeth would have to pass through each other. Writes images/gear-phase.png.

    python3 gear_phase_figure.py
"""
import os

import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import verify_gear_train as V  # noqa: E402
from cad_verify import overlap, to_manifold  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
X0 = V.B.CX - 0.5          # cut plane through the middle of the gears' face width
NRM = np.array([1.0, 0, 0])


def tri(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)


def draw(ax, man, color, z=1):
    if man.is_empty():
        return
    s = tri(man).section(plane_origin=[X0, 0, 0], plane_normal=NRM)
    if s is None:
        return
    for poly in s.to_2D(to_2D=TO2D)[0].polygons_full:
        ax.fill(*poly.exterior.xy, color=color, zorder=z, lw=0)
        for h in poly.interiors:
            ax.fill(*h.xy, color="white", zorder=z, lw=0)


# 2D axes: horizontal = robot Y, vertical = robot Z
TO2D = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -X0], [0, 0, 0, 1]], float)

fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
for k, ax in enumerate(axes):
    y, z, n = V.IDL[k]
    shafts = [to_manifold(trimesh.load(os.path.join(HERE, f"crankshaft-{j + 1}.stl"))).transform(V.shaft_pose(j, 0)[:3])
              for j in (k, k + 1)]
    idl0 = to_manifold(trimesh.load(os.path.join(HERE, f"idler-{k + 1}.stl")))
    best = min(np.linspace(0, 2 * np.pi / n, 120, endpoint=False),
               key=lambda p: sum(overlap(idl0.transform((V.rx(p, y, z) @ V.idler_base(k))[:3]), s) for s in shafts))
    idl = idl0.transform((V.rx(best, y, z) @ V.idler_base(k))[:3])
    vol = sum(overlap(idl, s) for s in shafts)
    for s in shafts:
        draw(ax, s, "#9db4d6")
    draw(ax, idl, "#f2c14e")
    for s in shafts:
        draw(ax, idl ^ s, "#d62728", 3)
    ax.set_aspect("equal")
    ax.set_xlim(V.SH[k][0] - 8, V.SH[k + 1][0] + 8), ax.set_ylim(z - n / 2 - 2, V.SH[k][1] + 8)
    ax.set_xticks([]), ax.set_yticks([])
    verdict = "meshes both" if vol < 0.1 else f"{vol:.1f} mm³ of teeth in each other"
    ax.set_title(f"Idler {k + 1} ({n} teeth) between crankshafts {k + 1} and {k + 2}\nbest angle: {verdict}", fontsize=10)
fig.tight_layout()
out = os.path.join(HERE, "images", "gear-phase.png")
fig.savefig(out, dpi=110, bbox_inches="tight")
print("wrote", out)
