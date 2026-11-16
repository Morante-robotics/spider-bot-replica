#!/usr/bin/env python3
"""Plan figure for chassis Part B (the looks parts): images/plan-b.png (and plan-b-es.png with --lang es).

A planning sketch from real geometry, drawn with tools/figures.py: the carcass body at 120 % (../robot.py), the drive
module as built in Part A (out/drive-module.stl), base v1's shell and front block (../base/out) standing in for the
looks shell and front block v2, and boxes for what Part B adds (hooks, rear tab, rear screw, bump, switch, slack pocket,
cradle, ballast box). Box sizes are the plan's (design-plan-b.md), not final parameters.

Left: the final robot, exploded along each part's way in (body with holder and eyes board lifted off; it goes on
down, 4 mm forward, one screw from below). Right: v0, the same shell with the ballast frame in place of the body.

    ../../.venv/bin/python plan_b_figure.py            # English
    ../../.venv/bin/python plan_b_figure.py --lang es  # Spanish copy for the workshop kit
Needs ../base/out (../base/build.py) and out/drive-module.stl (build.py).
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from cad import robot as R  # noqa: E402
from figures import PALETTE, PLACED, HARDWARE, draw, side_labels  # noqa: E402

CX = R.CX
BASE_OUT = os.path.join(HERE, "..", "base", "out")
LIFT_OFF = 45.0           # exploded: the body (or ballast frame) this far above its seat
SLIDE = 4.0               # the body is lowered 4 mm behind its place, then slid forward (-Y)
FB_OFF = 18.0             # exploded: front block above the deck

TEXT = {
    "en": {"shell": "looks shell (ground)\nbase v1 shown", "module": "drive module (Part A)",
           "fb": "front block v2\n2 × M3×10 from above", "hook": "hook tongues ±X\n(front block)",
           "body": "body v2: L-slots, rear lug,\ncradle bosses, eyes pocket", "holder": "holder in cradle\n(cover down)",
           "eyes": "eyes board pocket", "lug": "rear tab + nut (skirt\nextension, tip ≤ z 81.2)", "tunnel": "M3×8 from below into the tab,\nhead under the floor shelf (CX−9)",
           "bump": "2 mm bump\nover module rear", "switch": "switch, recessed (+X)", "slack": "battery JST and slack pocket\n(−X, inside the band)", "i7": "4 × M3 from below (I7)",
           "frame": "ballast frame (v0)\nsame hooks and screw", "steel": "steel box ≈ 110 g\n(lid, 2 screws)",
           "t1": "Final robot (exploded)", "t2": "v0 walk test: ballast frame instead of the body"},
    "es": {"shell": "carcasa base (fija)\nse muestra la base v1", "module": "módulo de transmisión (parte A)",
           "fb": "bloque frontal v2\n2 × M3×10 desde arriba", "hook": "lengüetas de enganche ±X\n(bloque frontal)",
           "body": "cuerpo v2: ranuras en L, oreja trasera,\nresaltes de la cuna, hueco de los ojos",
           "holder": "portapilas en su cuna\n(tapa abajo)", "eyes": "hueco de la placa de los ojos",
           "lug": "lengüeta trasera + tuerca\n(prolonga la falda, punta ≤ z 81,2)", "tunnel": "M3×8 desde abajo a la lengüeta,\ncabeza bajo el estante (CX−9)",
           "bump": "abultamiento de 2 mm\nsobre el final del módulo", "switch": "interruptor, hundido (+X)", "slack": "conector de la batería y hueco\npara el cable sobrante (−X)",
           "i7": "4 × M3 desde abajo (I7)", "frame": "marco de lastre (v0)\nmismos enganches y tornillo",
           "steel": "caja de acero ≈ 110 g\n(tapa, 2 tornillos)",
           "t1": "Robot final (despiezado)", "t2": "Prueba v0: marco de lastre en lugar del cuerpo"},
}


def box(lo, hi):
    return trimesh.creation.box(bounds=[lo, hi])


def cylz(x, y, r, z0, z1):
    c = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=32)
    c.apply_translation([x, y, (z0 + z1) / 2])
    return c


def moved(m, v):
    m = m.copy()
    m.apply_translation(v)
    return m


def common_items():
    shell = trimesh.load(os.path.join(BASE_OUT, "base-v1.stl"))
    module = trimesh.load(os.path.join(HERE, "out", "drive-module.stl"))
    fb = moved(trimesh.load(os.path.join(BASE_OUT, "front-block.stl")), [0, 0, FB_OFF])
    hooks = [moved(box((10.8 - 3.0, -34.0, 100.0), (10.8, -28.0, 103.0)), [0, 0, FB_OFF]),
             moved(box((74.4, -34.0, 100.0), (74.4 + 3.0, -28.0, 103.0)), [0, 0, FB_OFF])]
    bump = box((CX - 4.25, 34.84, 57.0), (CX + 4.25, 37.2, 74.8))
    tunnel = cylz(CX - 9.0, 37.5, 1.5, 73.0, 81.0)          # the M3×8 itself, head under the tab's floor shelf
    shelf = box((CX - 16.0, 33.0, 73.0), (CX - 2.0, 41.6, 74.8))
    switch = box((54.7, 27.5, 74.8), (66.7, 36.0, 80.8))
    slack = box((17.0, 16.0, 74.8), (31.0, 24.8, 81.0))
    jst = box((17.0, 26.0, 74.8), (27.0, 31.8, 82.0))
    i7 = [cylz(R.CX + x, y, 1.5, 47.0, z) for x, y, z in ((-0.15, -48.52, 58.2), (20.0, 12.18, 59.2),
                                                          (32.5, 12.18, 62.2), (-10.0, 12.18, 64.5))]
    items = [{"mesh": shell, "color": PLACED}, {"mesh": module, "color": PALETTE[1]},
             {"mesh": fb, "color": PALETTE[2]}, {"mesh": bump, "color": PALETTE[5]},
             {"mesh": tunnel, "color": PALETTE[6], "alpha": 0.6}, {"mesh": switch, "color": HARDWARE},
             {"mesh": slack, "color": PALETTE[8], "alpha": 0.6},
             {"mesh": shelf, "color": PALETTE[5]}, {"mesh": jst, "color": HARDWARE}]
    items += [{"mesh": h, "color": PALETTE[0]} for h in hooks] + [{"mesh": s, "color": HARDWARE} for s in i7]
    pts = {"shell": (CX - 45.0, -10.0, 60.0), "module": (CX, -20.0, 74.8), "fb": (CX, -60.0, 100.0 + FB_OFF),
           "hook": (7.8, -31.0, 101.5 + FB_OFF), "bump": (CX, 37.2, 66.0), "tunnel": (CX - 9.0, 41.6, 73.5),
           "switch": (60.7, 36.0, 78.0), "slack": (24.0, 20.0, 81.0), "i7": (R.CX + 20.0, 12.18, 50.0)}
    return items, pts


def final_items():
    items, pts = common_items()
    up = [0, SLIDE, LIFT_OFF]
    body = moved(R.carcass("body", lifted=True), up)
    holder = moved(R.holder(), up)
    hc = np.array(R.HOLDER_CENTRE)
    hh = np.array(R.HOLDER) / 2 + 2.0
    cradle = moved(box((hc[0] - hh[0], hc[1] - hh[1], hc[2] - R.HOLDER[2] / 2 - 2.0),
                       (hc[0] + hh[0], hc[1] + hh[1], hc[2] - R.HOLDER[2] / 2)), up)
    eyes = moved(R.eyes_board(), up)
    lug = moved(box((CX - 15.0, 33.55, 74.8), (CX - 3.0, 41.55, 83.8)), up)
    items += [{"mesh": body, "color": PALETTE[4], "alpha": 0.25, "edges": False},
              {"mesh": holder, "color": PALETTE[3]}, {"mesh": cradle, "color": PALETTE[7]},
              {"mesh": eyes, "color": PALETTE[8]}, {"mesh": lug, "color": PALETTE[0]}]
    pts.update({"body": (CX - 50.0, 0.0 + SLIDE, 130.0 + LIFT_OFF), "holder": (CX + 24.5, 11.0 + SLIDE, 106.5 + LIFT_OFF),
                "eyes": (43.0, -55.0 + SLIDE, 128.0 + LIFT_OFF), "lug": (CX - 9.0, 41.55 + SLIDE, 79.0 + LIFT_OFF)})
    return items, pts


def v0_items():
    items, pts = common_items()
    up = [0, SLIDE, LIFT_OFF]
    plate = box((CX - 30.0, -30.0, R.BAND_TOP), (CX + 30.0, 36.0, R.BAND_TOP + 2.5))
    tower = box((CX - 4.0, -14.0, R.BAND_TOP + 2.5), (CX + 4.0, 0.0, 120.0))
    steel = box((CX - 20.0, -18.0, 120.0), (CX + 20.0, 12.0, 136.0))
    holder = R.holder()
    frame = [moved(m, up) for m in (plate, tower)]
    items += [{"mesh": m, "color": PALETTE[4]} for m in frame]
    items += [{"mesh": moved(steel, up), "color": HARDWARE}, {"mesh": moved(holder, up), "color": PALETTE[3]}]
    pts.update({"frame": (CX - 30.0, 0.0 + SLIDE, R.BAND_TOP + 1.0 + LIFT_OFF),
                "steel": (CX + 20.0, -3.0 + SLIDE, 128.0 + LIFT_OFF),
                "holder": (CX + 24.5, 11.0 + SLIDE, 106.5 + LIFT_OFF)})
    return items, pts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="en", choices=sorted(TEXT))
    lang = ap.parse_args().lang
    T = TEXT[lang]
    view = (18, 130)          # from behind and to the left: the rear lug, tunnel, bump and switch face the camera
    fig, axs = plt.subplots(1, 2, figsize=(22, 11))
    for ax, (items, pts), title in ((axs[0], final_items(), T["t1"]), (axs[1], v0_items(), T["t2"])):
        proj = draw(ax, items, view)
        side_labels(ax, [(proj(np.array(p))[0], T[k]) for k, p in pts.items()])
        ax.set_title(title, fontsize=15, pad=14)
    fig.tight_layout()
    os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
    out = os.path.join(HERE, "images", "plan-b.png" if lang == "en" else f"plan-b-{lang}.png")
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
