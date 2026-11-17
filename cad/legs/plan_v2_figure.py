#!/usr/bin/env python3
"""Legs v2 plan figure: today's legs and the candidate legs (plan_v2_geom.py) on the robot, in the 4 standard views.

Rows (plan rev 3): today and the B family with the shin raised >= 1 mm off the bed: B'' (key B3), Bs (sweep +-5, shin
6.5) and Bb (sweep +2/-8, shin 7). A, C, D (and rev 2's unraised B, B', B'') were dropped by Morante (2026-11-17);
their meshes stay in plan_v2_geom.py for the record. Columns: 3/4 front, front, side, below-front. Left column: the reference photo when --photo
is given (the photo is private: the copies in images/ leave its panel empty) and the printed grams per leg + fork.

Mock-up, not the model: chassis, crank cover, front block v2 and forks from the built STLs (black), the body as
robot.carcass_proxy("body") (red), legs posed by the simulator at crank angle 0 (red outside, black tube, boss and knee).

    ../../.venv/bin/python plan_v2_figure.py                 # images/plan-v2.png
    ../../.venv/bin/python plan_v2_figure.py --lang es        # images/plan-v2-es.png
    ../../.venv/bin/python plan_v2_figure.py --lang es --photo P --out X.png   # private copy beside the photo
    ../../.venv/bin/python plan_v2_figure.py --lite           # one view per row
"""
import argparse
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import figures as F  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import plan_v2_geom as G  # noqa: E402
from cad import robot as R  # noqa: E402

COL = dict(black="#2b2b2b", red="#c0392b", grey="#9a9a9a", body="#b03a2e")
VIEWS = [(22, -125), (3, -90), (3, 0), (-25, -110)]
ROWS = ["today", "B3", "Bs", "Bb"]
LEG_G = {"today": 5.9, "B3": 8.62, "Bs": 8.21, "Bb": 8.33}   # leg + fork, g: today measured (15 %); others probe_v3 at 10 % infill
WORDS = {
    "en": dict(title="Legs v2 plan: candidate legs in the 4 standard views",
               views=["3/4 front", "front", "side", "below-front"],
               rows={"today": "today: 5 × 6 bars", "A": "A · arched, thin (5 across)",
                     "B": "B · arched, thick (8), feet spread", "B'": "B' · as B, 5 across near the fork",
                     "B2": "B'' · as B', knee 5 across too (8 on the shin)",
                     "B3": "B'' · sweep ±14/10, shin 8, raised 1 mm",
                     "Bs": "Bs · sweep ±5, shin 6.5, raised 1 mm",
                     "Bb": "Bb · sweep +2/−8, shin 7, raised 1 mm"},
               photo="reference photo\n(private: not in the repo)", mass="printed leg + fork (g)"),
    "es": dict(title="Plan de patas v2: patas candidatas en las 4 vistas",
               views=["3/4 frontal", "frente", "lado", "desde abajo y delante"],
               rows={"today": "hoy: barras de 5 × 6", "A": "A · arqueada, fina (5 de ancho)",
                     "B": "B · arqueada, gruesa (8), pies abiertos",
                     "B'": "B' · como B, 5 de ancho junto a la horquilla",
                     "B2": "B'' · como B', rodilla de 5 también (8 en la tibia)",
                     "B3": "B'' · barrido ±14/10, tibia 8, elevada 1 mm",
                     "Bs": "Bs · barrido ±5, tibia 6,5, elevada 1 mm",
                     "Bb": "Bb · barrido +2/−8, tibia 7, elevada 1 mm"},
               photo="foto de referencia\n(privada: no va al repositorio)", mass="pata + horquilla impresas (g)"),
}


def load(n):
    return trimesh.load(os.path.join(HERE, "..", "chassis", "out", f"{n}.stl"))


def legs(opt):
    o = G.OPTIONS.get(opt, {})
    out = []
    for i, Ml, My in G.poses(0.0, o.get("dpiv", [0, 0, 0, 0])):
        if opt == "today":
            pieces = [(G.today(i), COL["black"])]
        elif opt == "C":
            pieces = [(G.today(i), COL["black"]), (G.shell_c(i), COL["red"])]
        else:
            red, knee = G.arched(i, opt)[2]
            pieces = [(G.inner(i), COL["black"]), (red, COL["red"]), (knee, COL["black"])]
        pieces.append((trimesh.load(G.L.stl("pivot")), COL["black"], My))
        for p in pieces:
            M = p[2] if len(p) > 2 else Ml
            for T in (M, G.L.MIRROR @ M):
                out.append({"mesh": p[0].copy().apply_transform(T), "color": p[1]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--photo", default=None, help="private reference photo: only for a copy outside the repo")
    ap.add_argument("--out", default=None)
    ap.add_argument("--lite", action="store_true")
    a = ap.parse_args()
    w = WORDS[a.lang]
    views = VIEWS[:1] if a.lite else VIEWS
    static = [{"mesh": load(n), "color": COL["black"]} for n in ("chassis", "crank-cover", "front-block-v2")]
    static.append({"mesh": R.carcass_proxy("body", lifted=True), "color": COL["body"], "edges": False})
    nc, nr = len(views) + 1, len(ROWS)
    fig = plt.figure(figsize=(3.6 * nc, 3.3 * nr))
    for r, opt in enumerate(ROWS):
        items = static + legs(opt)
        for c, v in enumerate(views):
            ax = fig.add_axes([(c + 1) / nc, 1 - (r + 1.3) / (nr + 0.6), 1 / nc, 0.85 / (nr + 0.6)])
            F.draw(ax, items, view=v)
            ax.set_title((f"{w['rows'][opt]}\n" if c == 0 else "\n") + w["views"][c], fontsize=F.FONT - 2,
                         loc="left" if c == 0 else "center")
    px = fig.add_axes([0.0, 1 - 2.3 / (nr + 0.6), 1 / nc, 1.9 / (nr + 0.6)])
    if a.photo:
        px.imshow(plt.imread(a.photo))
    else:
        px.text(0.5, 0.5, w["photo"], ha="center", va="center", fontsize=F.FONT, color=COL["grey"])
    px.axis("off")
    cx = fig.add_axes([0.05, 0.08, 0.75 / nc, 0.35])
    fmt = (lambda g: f"{g:.1f}".replace(".", "," if a.lang == "es" else "."))
    for k, opt in enumerate(ROWS):
        cx.barh(k, LEG_G[opt], color=COL["black"] if opt == "today" else COL["red"])
        cx.text(LEG_G[opt] + 0.1, k, fmt(LEG_G[opt]), va="center", fontsize=F.FONT - 2)
    cx.set_yticks(range(len(ROWS)), [{"today": "hoy" if a.lang == "es" else "today", "B3": "B''"}.get(o, o) for o in ROWS],
                  fontsize=F.FONT - 2)
    cx.invert_yaxis()
    cx.set_xlabel(w["mass"], fontsize=F.FONT - 2)
    cx.spines[["top", "right"]].set_visible(False)
    fig.suptitle(w["title"], fontsize=F.FONT + 3, y=0.995)
    out = a.out or os.path.join(HERE, "images", "plan-v2" + ("-es" if a.lang == "es" else "") + ".png")
    fig.savefig(out, dpi=80)
    print(out)


if __name__ == "__main__":
    main()
