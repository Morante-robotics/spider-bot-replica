#!/usr/bin/env python3
"""Mass and centre of mass of the final robot and of the v0 walk test (chassis + ballast), for the plan.

CAD-derived where a mesh exists (sim/motor_sizing.py's shell model: 0.84 mm skin + 15 % infill, or the print
report), plan estimates for parts not modelled yet (marked «plan»). Positions in the robot frame; the centre of
mass is compared with the simulator's COM_BOX (±5 mm in x and y of the body axis sim.CENTER).
The ceiling is the design mass at which HP 380:1 keeps margin 3.0 at 4.0 V: 463 g × 3.1 / 3 (motor sizing).

    ../../.venv/bin/python mass_estimate.py              # table to stdout, images/plan-mass.png in English
    ../../.venv/bin/python mass_estimate.py --lang es    # the same figure in Spanish, images/plan-mass-es.png (kit)
"""
import argparse
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "sim"))
from cad import common as K, design  # noqa: E402
import motor_sizing as MS  # noqa: E402

C = design("crankshafts")
L = design("legs")
AXIS = np.array([*K.sim.CENTER, 0.0])
CX = K.CX
Y3, Z3, N3 = C.idlers()[2]
ZP = Z3 + C.MOD * (C.SHAFT_TEETH + N3) / 2 + C.CD_EXTRA
CEILING = 463 * 3.1 / 3
SIZING_MARGIN = MS.MARGIN


def mesh(path):
    return trimesh.load(os.path.join(ROOT, path))


def printed(path, lift=0.0):
    m = mesh(path)
    c = m.center_mass + [0, 0, lift]
    return MS.printed_g(m.volume / 1000, m.area / 100), c


def legs_centroid():
    """Mean position (over a turn) of the legs and forks, weighted by volume."""
    vols, acc = 0.0, np.zeros(3)
    cache = {}
    for a in range(0, 360, 30):
        for n, f, M in L.poses(np.radians(a)):
            if not (n.startswith("leg") or n.startswith("pivot")):
                continue
            if f not in cache:
                m = trimesh.load(L.stl(f))
                cache[f] = (m.volume, m.center_mass)
            v, c = cache[f]
            acc += v * (M[:3, :3] @ c + M[:3, 3])
            vols += v
    return acc / vols


def rows():
    base_g, base_c = 82.3, printed("cad/base/out/base-v1.stl")[1]
    body_g, body_c = printed("cad/carcass-120/spideybot_body.stl", lift=18.7)
    fb_c = mesh("cad/base/out/front-block.stl").center_mass
    shafts = np.array([[CX, y, z] for y, z in C.shaft_yz()]).mean(0)
    legs_c = legs_centroid()
    holder_c = np.array([CX, 11.0, 106.5])
    head = np.array([CX, -50.0, 128.0])
    pivots = np.array([P for _, _, P, _ in K.sim.pivots()]).mean(0)
    hw = MS.mass_table()                      # the sizing's own rows, for the numbers it measured
    screws_sizing = [r[1] for r in hw if r[0].startswith("Screws")][0]
    m3_10, m3_12, m3_8 = 0.9 + 0.25, 1.0 + 0.25, 0.8 + 0.25   # as motor_sizing.py (screw + nut)
    # (name, grams, centre, source, in final, in v0)
    R = [
        ("Chassis looks shell (band on the body's outline, lips, screws hidden, rear closed; also v0, L2)", base_g - 4.0 - 6.0 + 14.0, base_c, "plan: base v1 82.3 − spine/keel 4 − pegs and stems 6 + looks 14", 1, 1),
        ("Drive module (spine, keel, motor arm, flange)", 14.0, np.array([CX, -6.0, 62.0]), "plan", 1, 1),
        ("Cap", 5.8, np.array([CX, -8.0, 74.0]), "base v1 cap, print report", 1, 1),
        ("Motor strap, pin keeper, pinion, idler 3 v2 extra", 3.0 + 1.0 + 0.5 + 0.6, np.array([CX + 10, Y3, 74.0]), "plan", 1, 1),
        ("Front block v2 (hollow)", 15.0, fb_c, "plan (v1 solid: 23.4 measured)", 1, 1),
        ("4 crankshafts + 3 idlers", [r[1] for r in hw if r[0].startswith("4 crankshafts")][0], shafts, "STL volume, solid", 1, 1),
        ("8 legs + 8 forks", 46.9, legs_c, "legs-forks-v1 plate, measured", 1, 1),
        ("Body v2 (carcass 120 %, cuts ≈ −3, bosses and hooks slots ≈ +2)", body_g - 1.0, body_c, "shell model of the mesh", 1, 0),
        ("Holder cradle (in the body)", 6.0, holder_c + [0, 0, 9.5], "plan", 1, 1),
        ("Eyes and sensor, printed", [r[1] for r in hw if r[0].startswith("Eyes and")][0], head + [0, -12, 0], "shell model", 1, 0),
        ("Paint and finish allowance", 10.0, body_c, "plan: primer + paint ≈ 0.6 g / 100 cm² over 1570 cm²", 1, 0),
        ("4×AAA holder, empty", 20.0, holder_c, "catalogue (sizing)", 1, 1),
        ("4 × AAA NiMH", 48.0, holder_c, "catalogue (sizing)", 1, 1),
        ("N20 HP 380:1", 10.0, np.array([CX + 3.3 + 13, Y3, ZP]), "catalogue (datasheet)", 1, 1),
        ("Eyes board (perfboard, 2 LEDs, 2 resistors)", 5.0, head, "catalogue guess (sizing)", 1, 0),
        ("Wiring, 2 connector pairs, panel switch", 5.0 + 2 * 0.8 + 1.0, np.array([CX, 20.0, 85.0]), "plan (sizing 5 + connectors, switch)", 1, 1),
        ("Screws: 16 fork M3×10, 8 pivot M3×16, 3 pins (sizing set)", screws_sizing - 3 * (0.9 + 0.25), pivots, "catalogue screw masses (sizing set; its 19 M3×10 incl. 3 cap)", 1, 1),
        ("Screws added: 4 module, 2 strap, 2 front block, 2 cradle M3×10; 3 cap + 1 body M3×12; keeper M3×8", 10 * m3_10 + 4 * m3_12 + m3_8, np.array([CX, -5.0, 85.0]), "catalogue screw masses × counts from the plan", 1, 1),
    ]
    return R


CONTINGENCY = {"measured": 0.0, "shell": 0.05, "catalogue": 0.10, "plan": 0.15}


def category(src):
    """Where a mass comes from, for its contingency (design-reviewer, 2026-11-14)."""
    if "catalogue" in src:
        return "catalogue"
    if "plan" in src:
        return "plan"
    if "shell model" in src:
        return "shell"
    if any(k in src for k in ("measured", "print report", "STL")):
        return "measured"
    return "catalogue"


def com(items):
    g = sum(r[1] for r in items)
    c = sum(r[1] * np.asarray(r[2], float) for r in items) / g
    return g, c


def main():
    R = rows()
    final = [r for r in R if r[4]]
    v0 = [r for r in R if r[5]]
    gf, cf = com(final)
    g0, c0 = com(v0)
    print(f"{'Part':92s} {'g':>6s}  {'x−axis':>7s} {'y−axis':>7s} {'z':>6s}  F v0  source")
    for name, g, c, src, f, v in R:
        d = np.asarray(c) - AXIS
        print(f"{name:92s} {g:6.1f}  {d[0]:7.1f} {d[1]:7.1f} {c[2]:6.1f}  {'x' if f else ' '} {'x' if v else ' '}  {src}")
    ballast = gf - g0
    # ballast centre so that v0 + ballast has the final centre of mass
    cb = (gf * cf - g0 * c0) / ballast
    print()
    for lab, g, c in [("Final robot", gf, cf), ("v0 without ballast", g0, c0)]:
        d = c - AXIS
        ok = "inside" if max(abs(d[0]), abs(d[1])) <= MS.COM_BOX else "OUTSIDE"
        print(f"{lab:22s} {g:6.1f} g   CoM x{d[0]:+5.1f} y{d[1]:+5.1f} z {c[2]:5.1f}   ({ok} ±{MS.COM_BOX} mm)")
    d = cb - AXIS
    print(f"{'Ballast for v0':22s} {ballast:6.1f} g   at x{d[0]:+5.1f} y{d[1]:+5.1f} z {cb[2]:5.1f}  (v0 + ballast = final mass and CoM)")
    cont = {k: 0.0 for k in CONTINGENCY}
    for name, g, c, src, f, v in final:
        cont[category(src)] += g * CONTINGENCY[category(src)]
    gd = gf + sum(cont.values())
    print(f"\nContingency by source: " + ", ".join(f"{k} +{CONTINGENCY[k]:.0%}: {cont[k]:.1f} g" for k in CONTINGENCY))
    print(f"DESIGN MASS (decides the motor): {gf:.1f} + {sum(cont.values()):.1f} = {gd:.0f} g;  ceiling {CEILING:.0f} g "
          f"(HP 380:1, margin 3.0 at 4.0 V);  margin {3.1 * 463 / gd:.2f}  → {'UNDER' if gd <= CEILING else 'OVER'}")
    print(f"  (as summed, no contingency: {gf:.0f} g, margin {3.1 * 463 / gf:.2f}; margin scales as 1/mass, "
          f"a first approximation of motor_sizing.py)")
    print(f"Centre of mass, absolute y: final {cf[1]:.1f} (axis {AXIS[1]:.1f}); ballast {cb[1]:.1f}")


NAMES = {
    "en": {"Chassis looks": "Chassis, looks shell (also v0)", "Drive module": "Drive module", "Cap": "Cap",
           "Motor strap": "Clamp, pin keeper, pinion, idler 3 extra", "Front block": "Front block v2",
           "4 crankshafts": "4 crankshafts + 3 idlers", "8 legs": "8 legs + 8 forks", "Body v2": "Body v2 (carcass)",
           "Holder cradle": "Holder cradle", "Eyes and": "Eyes and sensor, printed",
           "Paint": "Paint and finish (allowance)", "4×AAA holder": "Battery holder, empty",
           "4 × AAA": "4 AAA NiMH batteries", "N20": "N20 motor HP 380:1", "Eyes board": "Eyes board",
           "Wiring": "Wiring, 2 connectors, switch", "Screws: 16": "Screws: legs and forks",
           "Screws added": "Screws added (module, cap, etc.)"},
    "es": {"Chassis looks": "Chasis definitivo (estético)", "Drive module": "Módulo de transmisión", "Cap": "Tapa",
           "Motor strap": "Abrazadera, retén, piñón, rueda 3", "Front block": "Bloque frontal v2",
           "4 crankshafts": "4 cigüeñales + 3 ruedas", "8 legs": "8 patas + 8 horquillas",
           "Body v2": "Cuerpo v2 (carcasa)", "Holder cradle": "Soporte del portapilas", "Eyes and": "Ojos y sensor",
           "Paint": "Pintura y acabado (margen)", "4×AAA holder": "Portapilas vacío", "4 × AAA": "4 pilas AAA NiMH",
           "N20": "Motor N20 380:1", "Eyes board": "Placa de los ojos", "Wiring": "Cables, 2 conectores, interruptor",
           "Screws: 16": "Tornillos de patas y horquillas", "Screws added": "Tornillos nuevos (módulo, tapa, etc.)"},
}
TXT = {
    "en": dict(origin={"plan": "plan (estimate)", "shell": "CAD, shell model", "measured": "measured or solid CAD",
                       "catalogue": "catalogue (nothing bought yet)"},
               ballast="v0 test ballast", at="at x{:+.1f} y{:+.1f} mm from the axis, z {:.0f}",
               com="CoM x{:+.1f} y{:+.1f} mm off the axis (limit ±5)",
               design="With contingency by source", margin="margin {:.2f} ({} the ceiling)", under="under",
               over="over", ceiling="Ceiling (HP 380:1, margin 3.0 at 4.0 V)", decides="decides the motor purchase",
               cols=["Part", "Final robot (g)", "v0 test (g)", "Source (contingency)"],
               title="Mass of the final robot and of the v0 test (ballast at the final robot's centre of mass)"),
    "es": dict(origin={"plan": "plan (estimado)", "shell": "CAD, modelo de cáscara", "measured": "medido o CAD macizo",
                       "catalogue": "catálogo (nada comprado aún)"},
               ballast="Lastre de la prueba v0", at="en x{:+.1f} y{:+.1f} mm del eje, z {:.0f}",
               com="c. de masas x{:+.1f} y{:+.1f} mm del eje (±5)",
               design="Con reserva según el origen", margin="margen {:.2f} ({} del techo)", under="por debajo",
               over="por encima", ceiling="Techo (HP 380:1, margen 3,0 a 4,0 V)", decides="decide la compra del motor",
               cols=["Pieza", "Robot final (g)", "Prueba v0 (g)", "Origen"],
               title="Masa del robot final y de la prueba v0 (con lastre en el centro de masas del final)"),
}


def figure(path, lang="en"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    w = TXT[lang]
    R = rows()
    gf, cf = com([r for r in R if r[4]])
    g0, c0 = com([r for r in R if r[5]])
    cb = (gf * cf - g0 * c0) / (gf - g0)
    cell = []
    for name, g, c, src, f, v in R:
        nm = next(v_ for k, v_ in NAMES[lang].items() if name.startswith(k))
        cell.append([nm, f"{g:.1f}" if f else "", f"{g:.1f}" if v else "",
                     f"{w['origin'][category(src)]} (+{CONTINGENCY[category(src)]:.0%})"])
    d = cb - AXIS
    cell.append([w["ballast"], "", f"{gf - g0:.1f}", w["at"].format(d[0], d[1], cb[2])])
    df = cf - AXIS
    cell.append(["TOTAL", f"{gf:.0f}", f"{gf:.0f}", w["com"].format(df[0], df[1])])
    gd = gf + sum(g * CONTINGENCY[category(src)] for name, g, c, src, f, v in R if f)
    cell.append([w["design"], f"{gd:.0f}", "",
                 w["margin"].format(3.1 * 463 / gd, w["under"] if gd <= CEILING else w["over"])])
    cell.append([w["ceiling"], f"{CEILING:.0f}", "", w["decides"]])
    fig, ax = plt.subplots(figsize=(11, 7.6))
    ax.axis("off")
    t = ax.table(cellText=cell, colLabels=w["cols"], loc="center", colWidths=[0.37, 0.13, 0.13, 0.37], cellLoc="left")
    t.auto_set_font_size(False)
    t.set_fontsize(10)
    t.scale(1, 1.3)
    for r in range(len(cell) - 2, len(cell) + 1):
        for c in range(4):
            t[r, c].set_text_props(fontweight="bold")
    ax.set_title(w["title"], fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor="white")
    print(os.path.relpath(path, HERE))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="en", choices=sorted(TXT))
    args = ap.parse_args()
    main()
    figure(os.path.join(HERE, "images", "plan-mass.png" if args.lang == "en" else f"plan-mass-{args.lang}.png"),
           args.lang)
