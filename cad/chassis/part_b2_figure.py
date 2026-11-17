#!/usr/bin/env python3
"""Figure for chassis Part B2: images/part-b2-body.png. Body v2 (translucent) on the chassis, the seat where it bears
on the band top (z BAND_TOP) and the three kinds of tool relief cut inside it, all positions read from body_v2.py.

    ../../.venv/bin/python part_b2_figure.py
Needs out/body-v2.stl and out/chassis.stl (build.py).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
for p in (ROOT, os.path.join(ROOT, "cad"), os.path.join(ROOT, "tools"), HERE):
    sys.path.insert(0, p)
import body_v2 as B  # noqa: E402
from figures import PALETTE, PLACED, draw, side_labels, simplify  # noqa: E402

K = B.K


def rod_x(r, x0, x1, y, z):
    return B.xcyl(r, x0, x1, y, z)


def rod_z(r, x, y, z0, z1):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=48)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def main():
    chassis = simplify(trimesh.load(os.path.join(HERE, "out", "chassis.stl")))
    body = simplify(trimesh.load(os.path.join(HERE, "out", "body-v2.stl")))
    r = B.PLIERS_R + B.RELIEF
    lug_z = B.ROOT_NUT_Z0 + K.NUT_T / 2
    lugs = [rod_x(r, B.LUG_X[k], B.LUG_X[k] + (-1, 1)[k] * 29.0, B.LUG_SCREW_Y, lug_z) for k in (0, 1)]
    ey, nz = B.EB_SCREW[1], B.EB_SCREW_Z + B.EB_SCREW_L - K.NUT_T - 0.5
    eyes = rod_x(r, B.EB_BOSS[0] - 8.0, B.EB_BOSS[0] - B.MOUTH - 8.0, ey, nz + K.NUT_T / 2)
    places = B.screw_places()["cradle"]
    cr = [rod_z(K.HEAD_D / 2 + 0.3, x, y, B.BLK_Z0 - 4.0, B.BLK_Z0) for x, y, _ in places]
    items = [{"mesh": chassis, "color": PLACED}, {"mesh": body, "color": PALETTE[4], "alpha": 0.22, "edges": False}]
    items += [{"mesh": m, "color": PALETTE[0]} for m in lugs]
    items += [{"mesh": eyes, "color": PALETTE[5]}] + [{"mesh": m, "color": PALETTE[3]} for m in cr]
    cx = B.R.CX
    pts = {
        "seat": ((cx - 30.0, -42.0, B.R.BAND_TOP), "Seat: the body bears on the band top\n(z %.1f), 4 mm slide forward" % B.R.BAND_TOP),
        "lug": ((B.LUG_X[1] + 20.0, B.LUG_SCREW_Y, lug_z), "Relief 1: pliers rod r %.1f along the\nbody lug's nut slots" % r),
        "eyes": ((B.EB_BOSS[0] - 14.0, ey, nz + K.NUT_T / 2), "Relief 2: same rod along\nthe eyes nut slot"),
        "cradle": ((places[0][0], places[0][1], B.BLK_Z0 - 2.0), "Relief 3: r %.2f under the holder\ncradle block, for the hex key" % (K.HEAD_D / 2 + 0.3)),
    }
    fig, ax = plt.subplots(figsize=(11, 8))
    proj = draw(ax, items, (22, 130))
    side_labels(ax, [(proj(np.array(p))[0], t) for p, t in pts.values()])
    ax.set_title("Body v2 on the chassis: the seat and the three tool reliefs", fontsize=14, pad=12)
    fig.tight_layout()
    out = os.path.join(HERE, "images", "part-b2-body.png")
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
