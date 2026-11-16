#!/usr/bin/env python3
"""Plan figure for chassis Part B: a cut through the rear tab and its screw (plane x = CX - 9, seen from the robot's
-X side): images/plan-b-rear-section.png (and -es with --lang es).

Real geometry: the carcass body lifted by LIFT (its rear skirt), the carcass base (the shell's outer face), and every
leg and fork swept over a full turn every 10° (grey dots within 1 mm of the plane). Planned features are drawn from
this plan's numbers (design-plan-b.md «Rear block»), not final parameters: the body's tab with its nut, the M3×8,
the rear block and its floor, the notch the tab slides in, and the ledge the tab leaves under the skirt's edge.

    ../../.venv/bin/python plan_b_rear_section.py [--lang es]
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon as MPoly, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402

X = R.CX - 9.0             # the screw's plane (plan: screw at (CX - 9, 37.5))
SCREW_Y = 37.5
FLOOR = (73.0, R.DECK_TOP)            # rear block floor under the tab
TAB = (33.55, 41.55)                  # tab section in Y: walls 1.05 (front, loaded) and 1.15 (rear) to the pocket
POCKET = K.NUT_AF + 2 * fits.STEEL.side   # nut pocket across the flats, 5.8 (Part A's rule)
NUT_Z = (77.0, 79.4)                  # nut, its pocket + 0.15 a side
SCREW = (FLOOR[0], FLOOR[0] + 8.0)    # M3×8: head under the floor, tip at 81.0
SLIDE = 4.0

TEXT = {"en": {"title": "Rear tab and its screw, cut at x = CX − 9 (seen from −X; rear to the right)",
               "skirt": "body skirt (carcass)", "bowl": "bowl (shell's outer face)", "legs": "legs and forks, full turn",
               "tab": "rear tab (body-lug), nut in its\n5.8 pocket, M3×8", "floor": "rear block floor\n(head bears here)",
               "ledge": "tab and floor stand ≈ 5.5 mm\nproud of the rear face", "lowered": "tab lowered 4 mm back,\nbefore the slide",
               "groove": "groove in the bowl\nfor the head (0.8 left)"},
        "es": {"title": "Lengüeta trasera y su tornillo, corte en x = CX − 9 (visto desde −X; detrás a la derecha)",
               "skirt": "falda del cuerpo (carcasa)", "bowl": "cuenco (cara exterior de la carcasa base)",
               "legs": "patas y horquillas, vuelta completa", "tab": "lengüeta trasera (pieza aparte), tuerca\nen su hueco de 5,8, M3×8",
               "floor": "suelo del bloque trasero\n(apoya la cabeza)", "ledge": "lengüeta y suelo sobresalen\n≈ 5,5 mm de la cara trasera",
               "lowered": "lengüeta bajada 4 mm atrás,\nantes de deslizar",
               "groove": "ranura en el cuenco\npara la cabeza (quedan 0,8)"}}


def cut(mesh):
    s = mesh.section(plane_origin=(X, 0, 0), plane_normal=(1, 0, 0))
    return [] if s is None else [s.vertices[e][:, 1:] for e in s.vertex_nodes]


def swept_legs():
    L = design("legs")
    import trimesh
    cache, out = {}, []
    for a in np.arange(0, 360, 10):
        for n, f, M in L.poses(np.radians(a)):
            if not (n.startswith("leg") or n.startswith("pivot")):
                continue
            if f not in cache:
                m = trimesh.load(L.stl(f))
                cache[f] = np.vstack([m.vertices, m.sample(6000)])
            p = cache[f] @ M[:3, :3].T + M[:3, 3]
            out.append(p[np.abs(p[:, 0] - X) < 1.0][:, 1:])
    return np.vstack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=sorted(TEXT))
    T = TEXT[ap.parse_args().lang]
    fig, ax = plt.subplots(figsize=(11, 8))
    legs = swept_legs()
    ax.plot(legs[:, 0], legs[:, 1], ".", ms=1, color="#bbbbbb", label=T["legs"])
    for k, (mesh, col, lab) in enumerate(((R.carcass("body", lifted=True), "#8e44ad", T["skirt"]),
                                          (R.carcass("base"), "#555555", T["bowl"]))):
        for i, seg in enumerate(cut(mesh)):
            ax.plot(seg[:, 0], seg[:, 1], "-", color=col, lw=1.5, label=lab if i == 0 else None)
    # rear block floor and the tab, nut, screw
    ax.add_patch(Rectangle((32.0, FLOOR[0]), 9.2, FLOOR[1] - FLOOR[0], fc="#cccccc", ec="k", lw=1, label=T["floor"]))
    tab = [(TAB[0], R.DECK_TOP), (TAB[1], R.DECK_TOP), (TAB[1], 83.8), (TAB[0], 83.8)]
    ax.add_patch(MPoly(tab, closed=True, fc="#e74c3c", ec="k", alpha=0.55, lw=1, label=T["tab"]))
    ax.add_patch(MPoly([(x + SLIDE, z) for x, z in tab], closed=True, fc="none", ec="#e74c3c", ls="--", lw=1.2,
                       label=T["lowered"]))
    ax.add_patch(Rectangle((SCREW_Y - POCKET / 2, NUT_Z[0] - 0.1), POCKET, NUT_Z[1] - NUT_Z[0] + 0.2, fc="white", ec="k", lw=0.6))
    ax.add_patch(Rectangle((SCREW_Y - K.NUT_AF / 2, NUT_Z[0]), K.NUT_AF, NUT_Z[1] - NUT_Z[0], fc="#4d4d4d"))
    ax.add_patch(Rectangle((SCREW_Y - 1.5, SCREW[0]), 3.0, SCREW[1] - SCREW[0], fc="#7f8c8d", ec="k", lw=0.6))
    ax.add_patch(Rectangle((SCREW_Y - K.HEAD_D / 2, SCREW[0] - K.HEAD_H), K.HEAD_D, K.HEAD_H, fc="#7f8c8d", ec="k"))
    ax.annotate(T["ledge"], xy=(TAB[1], 82.0), xytext=(46.5, 86.5), arrowprops=dict(arrowstyle="->"))
    ax.annotate(T["groove"], xy=(SCREW_Y - K.HEAD_D / 2 - 0.5, 64.0), xytext=(22.0, 58.0),
                arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(18, 52)
    ax.set_ylim(54, 92)
    ax.set_aspect("equal")
    ax.set_xlabel("y (mm)")
    ax.set_ylabel("z (mm)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title(T["title"], fontsize=12)
    lang = "" if ap.parse_args().lang == "en" else "-es"
    out = os.path.join(HERE, "images", f"plan-b-rear-section{lang}.png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
