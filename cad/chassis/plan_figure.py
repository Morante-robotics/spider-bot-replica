#!/usr/bin/env python3
"""Plan figure for the chassis (base v2) and the robot master model: three cuts through the robot with the drive,
the proposed N20 place, the battery bay and the eyes board envelope: images/plan-layout.png (the three side by side)
and images/plan-side.png, plan-front.png, plan-top.png (one view each, readable at the build log's width).

A planning sketch from real geometry: the carcass at 120 % lifted by base v1's band (../base/out), the legs and
crankshafts placed by ../legs poses() over a full turn (grey: everything they sweep), and boxes for what is not
modelled yet. Numbers of the boxes are the plan's (design-plan.md), not final parameters.

    ../../.venv/bin/python plan_figure.py              # English labels (repo, build log)
    ../../.venv/bin/python plan_figure.py --lang es    # Spanish labels, files end in -es (workshop kit)
Needs ../base/out (../base/build.py) and the legs' and crankshafts' STLs.
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from scipy.spatial import ConvexHull  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design  # noqa: E402

C = design("crankshafts")
L = design("legs")
BASE = os.path.join(HERE, "..", "base", "out")
CX = K.CX
GROUND = 15.6                     # sim/motor-sizing-result.txt «ground z 15.6»
DECK_BOT, SEAM, TOP = 72.8, 74.8, 93.5    # ../base/build.py DECK_BOT, SEAM, TOP (body seat)
Y3, Z3, N3 = C.idlers()[2]
ZP = Z3 + C.MOD * (C.SHAFT_TEETH + N3) / 2 + C.CD_EXTRA      # pinion axis over idler 3
MOTOR = dict(x=(CX + 3.3, CX + 3.3 + 26 + 6), y=(Y3 - 5, Y3 + 5), z=(ZP - 6, ZP + 6))   # body + terminals (datasheet)
HOLDER = dict(x=(CX - 24.5, CX + 24.5), y=(-21.0, 43.0), z=(98.5, 114.5))              # 64 × 49 × 16, long axis on Y
EYES = dict(x=(18.0, 68.0), y=(-55.0, -45.0), z=(117.0, 139.0))                      # proposed envelope


def section_paths(m, origin, normal, to2d):
    s = m.section(plane_origin=origin, plane_normal=normal)
    if s is None:
        return []
    out = []
    for e in s.discrete:
        out.append(np.asarray(e) @ to2d.T)
    return out


def sweep_hulls(view, step=30):
    """2D hulls of every leg, crankshaft and idler over a full turn, projected on the view (columns of xyz)."""
    hulls = []
    cache = {}
    for a in range(0, 360, step):
        for n, f, M in L.poses(np.radians(a)):
            if f == "spine":
                continue
            if f not in cache:
                cache[f] = trimesh.load(L.stl(f)).vertices
            v = cache[f] @ M[:3, :3].T + M[:3, 3]
            yield n, v


def draw_box(ax, b, i, j, **kw):
    keys = "xyz"
    lo = (b[keys[i]][0], b[keys[j]][0])
    ax.add_patch(Rectangle(lo, b[keys[i]][1] - lo[0], b[keys[j]][1] - lo[1], **kw))


TXT = {
    "en": dict(
        views=["Side cut through the body axis (x = CX), seen from the right",
               "Front cut through idler 3 and the motor (y = 12.2), seen from the front",
               "From above: cut through the deck (z 74) and what sits on it"],
        axes=[("y (mm, ← front)", "z (mm)"), ("x (mm, robot's right →)", "z (mm)"), ("x (mm)", "y (mm, front ↑)")],
        base="base v1 (reference)", front="front block v1", body="body (carcass, raised 18.7)",
        pinion="12-tooth pinion, 5 mm wide", clamp="motor clamp",
        clamp_note="clamp (screws above\nthe deck, no walls\nnext to the legs)",
        body_on="1 lower the body (with the holder)\n2 slide 4 mm forward: hooks\n3 one M3 screw from below, rear",
        rear_screw="rear screw\n(from below,\nno hole in the skirt)",
        switch="switch (to buy)", cradle="holder cradle (in the body)",
        motor="N20 motor + terminals (catalogue)", holder="4×AAA holder (rides in the body)",
        eyes="eyes board (pocket in the head)", ground="ground", deck="deck", top="band: body seat",
        title="Chassis (base v2), plan: the N20 over idler 3, half through the deck; the battery holder rides in the "
              "body and lifts off with it.\nOrange / blue fill: legs / crankshafts and idlers over a full turn"),
    "es": dict(
        views=["Corte lateral por el eje del cuerpo (x = CX), visto desde la derecha",
               "Corte frontal por la rueda intermedia 3 y el motor (y = 12,2), visto de frente",
               "Planta: corte de la cubierta (z 74) y lo que va encima"],
        axes=[("y (mm, ← delante)", "z (mm)"), ("x (mm, derecha del robot →)", "z (mm)"), ("x (mm)", "y (mm, delante ↑)")],
        base="base v1 (referencia)", front="bloque frontal v1", body="cuerpo (carcasa, subido 18,7)",
        pinion="piñón de 12 dientes, 5 mm de ancho", clamp="abrazadera del motor",
        clamp_note="abrazadera (tornillos encima\nde la cubierta, sin paredes\njunto a las patas)",
        body_on="1 bajar el cuerpo (con el portapilas)\n2 deslizar 4 mm hacia delante: ganchos\n"
                "3 un tornillo M3 desde abajo, atrás",
        rear_screw="tornillo trasero\n(desde abajo,\nsin agujero en la falda)",
        switch="interruptor (a comprar)", cradle="soporte del portapilas (en el cuerpo)",
        motor="motor N20 + terminales (catálogo)", holder="portapilas 4×AAA (va en el cuerpo)",
        eyes="placa de los ojos (hueco en la cabeza)", ground="suelo", deck="cubierta", top="aro: apoyo del cuerpo",
        title="Chasis (base v2), plan: el N20 sobre la rueda intermedia 3, medio por la cubierta; el portapilas va "
              "en el cuerpo y sale con él.\nRelleno naranja / azul: patas / cigüeñales y ruedas en una vuelta entera"),
}
VIEWS = [((CX, 0, 0), (1, 0, 0), (1, 2)), ((0, Y3, 0), (0, 1, 0), (0, 2)), ((0, 0, 74.0), (0, 0, 1), (0, 1))]
LIMITS = [((-72, 70), (10, 165)), ((-22, 108), (10, 165)), ((-22, 108), (70, -72))]
NAMES = ["side", "front", "top"]


def load():
    meshes = dict(base=trimesh.load(os.path.join(BASE, "base-v1.stl")),
                  body=trimesh.load(os.path.join(BASE, "body-lifted.stl")),
                  front=trimesh.load(os.path.join(BASE, "front-block.stl")))
    sweeps = {}
    for n, v in sweep_hulls(None):
        sweeps.setdefault(n, []).append(v)
    return meshes, sweeps


def draw_view(ax, k, meshes, sweeps, w, fs):
    """One cut (k: 0 side, 1 front, 2 top) with labels in w (a TXT entry) at base font size fs."""
    o, nrm, (i, j) = VIEWS[k]
    T = np.zeros((2, 3))
    T[0, i], T[1, j] = 1, 1
    # moving parts: grey hull per part over the turn (only those near the cut for the side and front views)
    for n, vs in sweeps.items():
        v = np.vstack(vs)
        kk = [a for a in range(3) if a not in (i, j)][0]
        if kk != 2:
            near = np.abs(v[:, kk] - o[kk]) < (14 if kk == 0 else 6)
            v = v[near]
        if len(v) < 4:
            continue
        p = v[:, [i, j]]
        try:
            h = ConvexHull(p)
        except Exception:
            continue
        col = "#f4a261" if n.startswith("leg") else "#9db4c0"
        ax.fill(*p[h.vertices].T, color=col, alpha=0.35, lw=0)
    for m, col, lab in [(meshes["base"], "#555555", w["base"]), (meshes["front"], "#2a9d8f", w["front"]),
                        (meshes["body"], "#bc4749", w["body"])]:
        first = True
        for path in section_paths(m, o, nrm, T):
            ax.plot(path[:, 0], path[:, 1], color=col, lw=1.0, label=lab if first else None)
            first = False
    if (i, j) == (1, 2):
        for y, z in C.shaft_yz():
            ax.add_patch(Circle((y, z), 7, fill=False, color="#1d3557", lw=1))
        for kk, (y, z, n) in enumerate(C.idlers()):
            ax.add_patch(Circle((y, z), C.MOD * (n / 2 + 1), fill=False, color="#1d3557", lw=1,
                                ls="-" if kk < 2 else "--"))
        ax.add_patch(Circle((Y3, ZP), 7, fill=False, color="#e63946", lw=2, label=w["pinion"]))
    if (i, j) == (0, 2):
        ax.add_patch(Rectangle((CX - 2.5, ZP - 7), 5, 14, fill=False, color="#e63946", lw=2))
        ax.add_patch(Rectangle((CX - 2.5, Z3 - 11), 5, 22, fill=False, color="#1d3557", lw=1.5, ls="--"))
        # motor clamp: a bridge over the motor, its two screws in bosses on the flange, all above the deck
        ax.add_patch(Rectangle((CX + 6, ZP + 6.8), 26, 2.0, color="#457b9d", label=w["clamp"]))
        for xs in (CX + 9, CX + 29):
            ax.add_patch(Rectangle((xs - 1.5, SEAM), 3, ZP + 6.8 - SEAM, fill=False, ec="#457b9d", lw=1))
        ax.text(CX + 34, ZP + 9.5, w["clamp_note"], fontsize=fs, color="#457b9d")
    if (i, j) == (1, 2):
        ax.annotate("", xy=(30, 150), xytext=(30, 112), arrowprops=dict(arrowstyle="<-", color="#6a4c93", lw=2))
        ax.annotate("", xy=(-4, 104), xytext=(0, 104), arrowprops=dict(arrowstyle="->", color="#6a4c93", lw=2))
        ax.text(-8, 152, w["body_on"], fontsize=fs, color="#6a4c93")
        ax.plot([40, 40], [52, 92], color="#6a4c93", lw=1.5, ls="--")
        ax.text(41, 54, w["rear_screw"], fontsize=fs - 0.5, color="#6a4c93")
        ax.add_patch(Rectangle((36.5, 75.5), 6, 6, color="#2b9348", label=w["switch"]))
        ax.add_patch(Rectangle((-18, 115.5), 66, 2, color="#6a4c93", alpha=0.5, label=w["cradle"]))
    if (i, j) == (0, 1):
        for y, z in C.shaft_yz():
            ax.plot([CX - 13.8, CX + 13.8], [y, y], color="#1d3557", lw=1)
        for side, kk, P, r in K.sim.pivots():
            ax.plot(P[0], P[1], "k^", ms=5)
    draw_box(ax, MOTOR, i, j, fill=True, color="#e63946", alpha=0.45, label=w["motor"])
    draw_box(ax, HOLDER, i, j, fill=False, ec="#6a4c93", lw=2, ls="-", label=w["holder"])
    draw_box(ax, EYES, i, j, fill=False, ec="#ff9f1c", lw=2, ls="--", label=w["eyes"])
    if j == 2:
        for z, lab in [(GROUND, w["ground"]), (DECK_BOT, ""), (SEAM, w["deck"]), (TOP, w["top"])]:
            ax.axhline(z, color="#999999", lw=0.6, ls=":")
            if lab:
                ax.text(-70 if i == 1 else -20, z + 0.8, lab, fontsize=fs, color="#666666")
    ax.set_title(w["views"][k], fontsize=fs + 3)
    ax.set_xlabel(w["axes"][k][0], fontsize=fs + 1)
    ax.set_ylabel(w["axes"][k][1], fontsize=fs + 1)
    ax.tick_params(labelsize=fs)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_xlim(*LIMITS[k][0])
    ax.set_ylim(*LIMITS[k][1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="en", choices=sorted(TXT))
    args = ap.parse_args()
    w = TXT[args.lang]
    sfx = "" if args.lang == "en" else f"-{args.lang}"
    meshes, sweeps = load()
    # the three views side by side (the plan, the kit)
    fig, axs = plt.subplots(1, 3, figsize=(21, 8), gridspec_kw=dict(width_ratios=[1.25, 1.0, 1.05]))
    for k, ax in enumerate(axs):
        draw_view(ax, k, meshes, sweeps, w, 7)
    h, lab = axs[0].get_legend_handles_labels()
    seen = dict(zip(lab, h))
    fig.legend(seen.values(), seen.keys(), loc="lower center", ncol=7, fontsize=8)
    fig.suptitle(w["title"], fontsize=11)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    out = os.path.join(HERE, "images", f"plan-layout{sfx}.png")
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(os.path.relpath(out, HERE))
    # one view per figure, larger labels (the build log)
    for k, name in enumerate(NAMES):
        fig, ax = plt.subplots(figsize=(9, 8))
        draw_view(ax, k, meshes, sweeps, w, 11)
        h, lab = ax.get_legend_handles_labels()
        seen = dict(zip(lab, h))
        ax.legend(seen.values(), seen.keys(), loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=11)
        out = os.path.join(HERE, "images", f"plan-{name}{sfx}.png")
        fig.savefig(out, dpi=100, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(os.path.relpath(out, HERE))


if __name__ == "__main__":
    main()
