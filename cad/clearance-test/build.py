#!/usr/bin/env python3
"""Clearance test: which hole clearance this printer needs for the drive's turning and sliding fits.

Parts (PLA, printed as laid out here):
  clearance-block  an upright wall on a foot. Horizontal holes through the wall (printed with their axis horizontal,
                   like the leg's bore and the journal holes), in 3 rows × 4 columns, clearance +0.1 / +0.2 / +0.3 /
                   +0.4 mm on the diameter from left to right (engraved on top):
                     top row     Ø4.0 + c  journal holes (crankshaft in the spine / test frame)
                     middle row  Ø3.6 + c  leg bore (ball on the crank pin)
                     bottom row  Ø3.0 + c  M3 screw turning in a hole (leg on its pivot screw)
                   In the foot, 3 blind holes Ø2.3 / 2.5 / 2.7 mm, 3.6 mm deep (left to right): an M3 screw cutting its
                   own thread, as in the fork (build.py uses 2.5).
  clearance-pin    a Ø4.0 journal and a Ø3.6 ball on a Ø2.2 stub, printed lying down like the crankshafts.

Use: push the journal through each top hole and the ball into each middle hole, and an M3 screw through each bottom
hole. The right clearance is the smallest one that turns freely without wobbling. Set CLR in ../drive/build.py to it.

Usage:
    python3 build.py        # STEP + STL into this folder
"""
import os

from build123d import Axis, Box, Cylinder, Plane, Pos, Rot, Sphere, Text, export_step, export_stl, extrude

HERE = os.path.dirname(os.path.abspath(__file__))
CLEARANCES = [0.1, 0.2, 0.3, 0.4]
ROWS = [(24.0, 4.0), (15.0, 3.6), (7.0, 3.0)]   # (z of the hole axis, nominal diameter)
TAPS = [2.3, 2.5, 2.7]
COL_X = [-15.0, -5.0, 5.0, 15.0]
W, T, H = 42.0, 6.0, 30.0                       # wall width, thickness (= hole length), height
FOOT_D, FOOT_H = 16.0, 5.0                      # foot depth (in front of the wall) and thickness


def block():
    part = Pos(0, 0, H / 2) * Box(W, T, H)
    part += Pos(0, -(FOOT_D - T) / 2, FOOT_H / 2) * Box(W, FOOT_D, FOOT_H)
    for z, d in ROWS:
        for x, c in zip(COL_X, CLEARANCES):
            part -= Pos(x, 0, z) * Rot(90, 0, 0) * Cylinder((d + c) / 2, T + 2)
    for x, d in zip([-10.0, 0.0, 10.0], TAPS):
        part -= Pos(x, -(FOOT_D - T / 2) + 3, FOOT_H - 1.8) * Cylinder(d / 2, 3.6 + 0.01)
    for x, c in zip(COL_X, CLEARANCES):
        txt = Plane.XY.offset(H - 0.6).location * Pos(x, 0, 0) * extrude(Text(f".{int(c * 10)}", 3.6), amount=1)
        part -= txt
    return part


def pin():
    """Along X, lying: ball Ø3.6, stub Ø2.2, a square grip, journal Ø4.0. Axis at z = 4 (grip on the bed)."""
    g = 7.0
    part = Pos(0, 0, g / 2) * Box(g, g, g)
    part += Pos(g / 2 + 9, 0, g / 2) * Rot(0, 90, 0) * Cylinder(2.0, 18)            # journal Ø4, 18 long
    part += Pos(-g / 2 - 3, 0, g / 2) * Rot(0, 90, 0) * Cylinder(1.1, 6)            # stub Ø2.2
    part += Pos(-g / 2 - 6, 0, g / 2) * Sphere(1.8)                                  # ball Ø3.6
    return part


def main():
    for name, p in (("clearance-block", block()), ("clearance-pin", pin())):
        export_step(p, os.path.join(HERE, f"{name}.step"))
        export_stl(p, os.path.join(HERE, f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
        bb = p.bounding_box()
        print(f"{name:16s} {bb.size.X:5.1f} × {bb.size.Y:5.1f} × {bb.size.Z:5.1f} mm")


if __name__ == "__main__":
    main()
