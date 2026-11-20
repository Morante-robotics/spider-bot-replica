#!/usr/bin/env python3
"""jenscolt's eye domes as parameters: the large eye, the small eye and the front sensor.

    ../../.venv/bin/python build.py            # the three parts into out/ (coarse STL + STEP), reference frames
    ../../.venv/bin/python build.py --sweep    # also S 0.65, wall 0.8x / 1.2x, size 0.8x / 1.2x: each a valid solid
    ../../.venv/bin/python build.py --fine     # fine STL

One cup, revolved about its own axis (+Y, apex at the lowest Y, open end at the highest Y): a flat apex of radius
RF, an elliptic dome of depth H rising to the outer radius R, then a straight wall to the length L, a wall of
thickness W. Each part is that cup with its own numbers, placed where its reference mesh sits (C = apex centre).
Numbers measured on the reference meshes with radial/height probes (r of the outer and inner surface per Y band,
rim centre; scratch probes, never read here).
"""
import argparse
import math
import os
import sys
import time

from build123d import (Axis, Edge, Face, Plane, Pos, Vector, Wire, export_step, export_stl, revolve)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
STL_TOL = {True: (0.02, 0.15), False: (0.05, 0.3)}

S = 1.0                       # overall scale (1.0 = the reference's size)

# name: R outer radius, L length along the axis, H dome depth, RF flat apex radius, W wall, C apex centre (x, y, z)
CUPS = {
    "eye":       dict(R=8.83, L=8.46, H=6.5, RF=2.4, W=0.62, C=(283.24, 53.75, 91.37)),
    "small-eye": dict(R=3.68, L=4.78, H=2.9, RF=1.2, W=0.3, C=(310.60, 23.50, 99.95)),
    "sensor":    dict(R=3.80, L=4.78, H=2.9, RF=1.2, W=0.3, C=(35.50, -53.89, 66.18)),
}


def cup(R, L, H, RF, W, C, s=1.0, wall_k=1.0, size_k=1.0):
    k = s * size_k
    R, L, H, RF = R * k, L * k, H * k, RF * k
    W = W * s * wall_k
    a, b = R - RF, H                       # dome semi-axes (r, y), centre (RF, H)
    P = lambda x, y: Vector(x, y, 0)
    outer = Edge.make_ellipse(a, b, Plane(origin=(RF, H, 0)),
                              start_angle=270, end_angle=360)
    ai, bi = a - W, b - W
    inner = Edge.make_ellipse(ai, bi, Plane(origin=(RF, H, 0)),
                              start_angle=270, end_angle=360)
    segs = [
        Edge.make_line(P(0, 0), P(RF, 0)), outer,
        Edge.make_line(P(R, H), P(R, L)), Edge.make_line(P(R, L), P(R - W, L)),
        Edge.make_line(P(R - W, L), P(R - W, H)), inner,
        Edge.make_line(P(RF, W), P(0, W)), Edge.make_line(P(0, W), P(0, 0)),
    ]
    solid = revolve(Face(Wire(segs)), Axis.Y)
    return Pos(C[0] * s, C[1] * s, C[2] * s) * solid.solids()[0] if s != 1 else Pos(*C) * solid.solids()[0]


def build(name, **kw):
    return cup(**CUPS[name], **kw)


def valid(sh):
    return sh.is_valid and len(sh.solids()) == 1 and sh.volume > 0


def sweep():
    bad = 0
    variants = [("S0.65", dict(s=0.65))]
    for k in (0.8, 1.2):
        variants += [(f"wall{k}", dict(wall_k=k)), (f"size{k}", dict(size_k=k))]
    for n in CUPS:
        for label, kw in variants:
            try:
                sh = build(n, **kw)
                ok = valid(sh)
            except Exception as e:  # noqa: BLE001
                ok, sh = False, str(e)
            if not ok:
                bad += 1
                print(f"FAIL {n} {label}: not one valid closed solid ({sh if isinstance(sh, str) else ''})")
    print("sweep done, failures:", bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--fine", action="store_true")
    ap.add_argument("--part")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    tol = STL_TOL[a.fine]
    for n in CUPS:
        if a.part and a.part != n:
            continue
        t = time.time()
        sh = build(n)
        export_stl(sh, os.path.join(OUT, f"{n}.stl"), tolerance=tol[0], angular_tolerance=tol[1])
        export_step(sh, os.path.join(OUT, f"{n}.step"))
        print(f"{n}: valid={valid(sh)} vol={sh.volume:.1f} {time.time() - t:.1f}s")
    if a.sweep:
        sweep()


if __name__ == "__main__":
    sys.exit(main())
