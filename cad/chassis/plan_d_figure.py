#!/usr/bin/env python3
"""Part D (lightening) plan figure: where the grams come off, and the design mass and motor margin of each lever set.

Left: the chassis shell, crank cover, front block v2, drive module and cap from out/ (the built STLs), each region
coloured by the first lever set that thins it. Right: design mass per set against the 478 g ceiling, with the margin
of the HP 380:1 at 4.0 V from sim/motor_sizing.py's crank torque (probe numbers in design-plan-d.md, «Probes»).

    ../../.venv/bin/python plan_d_figure.py            # images/plan-d.png
    ../../.venv/bin/python plan_d_figure.py --lang es  # images/plan-d-es.png
"""
import argparse
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import figures as F  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

DECK_BOT, SEAM = 72.8, 74.8          # robot.DECK_BOT, robot.DECK_TOP
# design-plan-d.md «Lever sets» (probe_variants, probe_margin): design mass g, margin (motor_sizing), saved g
SETS = [("now", 466.0, 3.10), ("safe", 459.3, 3.15), ("moderate", 455.7, 3.17), ("aggressive", 426.9, 3.39)]
COL = {"safe": "#27ae60", "moderate": "#e2b007", "aggressive": "#c0392b", "keep": "#d5d5d5"}
WORDS = {
    "en": dict(title="Part D · where the grams come off", now="now", safe="safe", moderate="moderate",
               aggressive="aggressive", ceiling="ceiling 478 g (margin 3.0)", mass="design mass (g)",
               margin="margin {:.2f}", keep="kept as is (fits, gears)",
               bowl="bowl skin and crank cover 1.6 → 1.2", cover="crank cover 1.6 → 1.2", seat="seat plate 2.0 → 1.6, deck ring 10 → 6",
               band="band 1.2 → 0.85, lips off", screws="fork and pivot screws: aluminium"),
    "es": dict(title="Parte D · de dónde salen los gramos", now="ahora", safe="segura", moderate="moderada",
               aggressive="agresiva", ceiling="techo 478 g (margen 3,0)", mass="masa de diseño (g)",
               margin="margen {:.2f}", keep="se queda igual (ajustes, engranajes)",
               bowl="piel del cuenco y tapa de cigüeñales 1,6 → 1,2", cover="tapa de cigüeñales 1,6 → 1,2",
               seat="asiento 2,0 → 1,6, anillo de cubierta 10 → 6", band="banda 1,2 → 0,85, sin labios",
               screws="tornillos de horquillas y pivotes: aluminio"),
}


def load(n):
    return trimesh.load(os.path.join(HERE, "out", f"{n}.stl"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    lang = ap.parse_args().lang
    w = WORDS[lang]
    sh = load("chassis")
    z = sh.triangles_center[:, 2]
    items = [{"mesh": sh.submesh([np.where(z < DECK_BOT)[0]], append=True), "color": COL["safe"]},
             {"mesh": sh.submesh([np.where((z >= DECK_BOT) & (z < SEAM + 2.0))[0]], append=True), "color": COL["moderate"]},
             {"mesh": sh.submesh([np.where(z >= SEAM + 2.0)[0]], append=True), "color": COL["aggressive"]},
             {"mesh": load("crank-cover"), "color": COL["safe"]}]
    items += [{"mesh": load(n), "color": COL["keep"]} for n in ("front-block-v2", "drive-module", "cap")]
    fig = plt.figure(figsize=(15, 7))
    ax = fig.add_axes([0.0, 0.05, 0.58, 0.85])
    proj = F.draw(ax, items, view=(-28, -55))
    F.callout(ax, proj, [20.0, 10.0, 55.0], w["bowl"], dx=-60, dy=-60, color=COL["safe"])
    F.callout(ax, proj, [95.0, 0.0, 74.0], w["seat"], dx=-260, dy=-95, color="#9a7a00")
    F.callout(ax, proj, [100.0, -20.0, 90.0], w["band"], dx=20, dy=40, color=COL["aggressive"])
    F.callout(ax, proj, [43.0, -40.0, 95.0], w["keep"], dx=-120, dy=60, color="#555555")
    ax.set_title(w["title"], fontsize=F.FONT + 2)
    bx = fig.add_axes([0.66, 0.14, 0.32, 0.72])
    names = [w[k] for k, _, _ in SETS]
    g = [m for _, m, _ in SETS]
    cols = ["#7f8c8d", COL["safe"], COL["moderate"], COL["aggressive"]]
    bx.bar(names, g, color=cols, edgecolor="#1a1a1a")
    bx.axhline(478, color="#c0392b", ls="--", lw=1.2)
    bx.text(-0.4, 480, w["ceiling"], color="#c0392b", fontsize=F.FONT - 1)
    for i, (_, m, mg) in enumerate(SETS):
        bx.text(i, m + 2, f"{m:.0f} g\n" + w["margin"].format(mg).replace(".", "," if lang == "es" else "."), ha="center", va="bottom", fontsize=F.FONT - 1)
    bx.set_ylim(380, 500)
    bx.set_ylabel(w["mass"])
    bx.spines[["top", "right"]].set_visible(False)
    out = os.path.join(HERE, "images", "plan-d" + ("-es" if lang == "es" else "") + ".png")
    fig.savefig(out, dpi=110)
    print(out)


if __name__ == "__main__":
    main()
