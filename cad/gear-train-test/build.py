#!/usr/bin/env python3
"""Gear train test (v2, cap v2.1): the four crankshafts and three idlers of ../crankshafts in a stand-alone spine,
held down by a cap as base v1's cap holds them, turned by hand.

Parts (all PLA):
  spine     two walls on a foot, holding the crankshafts (slots open at the top) and the idler axles; the robot's
            spine is built into base v1.
  test-cap  closes the spine's slots as base v1's cap does (tongues), 2 × M3×12.

Coordinates as in ../README.md (mm, Z up, forward = -Y, +X = right). Both parts are exported to out/ in robot
coordinates (print the cap upside down).

Usage:
    python3 build.py                   # both parts
    python3 build.py --part test-cap
    python3 ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
"""
import os
import sys

import numpy as np
from build123d import Box, Cylinder, Pos, Rot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design  # noqa: E402
from cad.common import (CLR, CLR_STEEL, CX, HEAD_D, HEAD_H, NUT_AF, NUT_T, PIN, SCREW, cyl,  # noqa: E402,F401
                        hexagon, marks)

C = design("crankshafts")
OUT = os.path.join(HERE, "out")

# --- parameters (mm) -----------------------------------------------------------------------------------------
JOURNAL, MOD, WALL_IN, WALL_OUT = C.JOURNAL, C.MOD, C.WALL_IN, C.WALL_OUT
TEST_TOP = 72.8      # test spine's top = base v1 deck underside (../base/build.py SEAM - WALL): tongues as long as there
TEST_CAP_T = 5.0     # test cap plate: thick and wide (2 screws only, at the ends) so it does not bow up between them
TEST_CAP_W = 20.0
TEST_SKIRT_CLR = 0.2 # test cap locator: skirts down both walls' outer faces at the end blocks, this much a side
TEST_SKIRT_T, TEST_SKIRT_H = 1.6, 4.0    # skirt thickness and how far down the walls it reaches
TEST_SKIRT_GAP = 9.0 # skirts start this far (y) from the end shafts: the cranks sweep a radius of 6.0
END_IN, END_OUT = C.KEEP_GAP, 17.0  # test spine end blocks, |y| from the end shafts (clear of the gear tips, radius 7)
END_SCREW = END_IN + 4.25          # cap screw in each end block (the nut's inner corner stays 0.9 mm off the gear side)
CAP_SCREW_L = 12.0   # M3×12 cap screws (as v1's axles and the test frame keeper)
FOOT_T, FOOT_W = 3.0, 30.0         # test spine foot plate: stands on the desk, and the thin walls print on it


def spine_box():
    sh = C.shaft_yz()
    z_bot = min(z - MOD * (n / 2 + 1) for _, z, n in C.idlers()) - 1.5
    return sh[0][0] - END_OUT, sh[-1][0] + END_OUT, z_bot, TEST_TOP


def cap_screws():
    """(y, outward ±1) of the test cap's two screws, in the end blocks."""
    sh = C.shaft_yz()
    return [(sh[0][0] - END_SCREW, -1), (sh[-1][0] + END_SCREW, 1)]


def cap_nut_z():
    """Bottom of the cap screws' nut pockets: the M3×12's tip comes 0.5 mm out under the nut."""
    return TEST_TOP + TEST_CAP_T - CAP_SCREW_L + 0.5


def spine():
    """Gear train test spine (v2): two walls along Y at |x| = WALL_IN..WALL_OUT on a foot plate, joined by end blocks;
    journal slots open at the top up to TEST_TOP (as in base v1), closed by test_cap(). Each end block takes a captive
    M3 nut for a cap screw, slid in from the end. Index dots for each crankshaft on the +X wall, under its slot."""
    sh, idl = C.shaft_yz(), C.idlers()
    y0, y1, z_bot, z_top = spine_box()
    t = WALL_OUT - WALL_IN
    part = Pos(0, (y0 + y1) / 2, z_bot - FOOT_T / 2) * Box(FOOT_W, y1 - y0, FOOT_T)
    for sx in (1, -1):
        part += Pos(sx * (WALL_IN + WALL_OUT) / 2, (y0 + y1) / 2, (z_top + z_bot) / 2) * Box(t, y1 - y0, z_top - z_bot)
    for ya, yb in ((y0, sh[0][0] - END_IN), (sh[-1][0] + END_IN, y1)):
        part += Pos(0, (ya + yb) / 2, (z_top + z_bot) / 2) * Box(2 * WALL_IN + 0.02, yb - ya, z_top - z_bot)
    for y, z in sh:
        part -= cyl([0, y, z], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
        part -= Pos(0, y, (z + z_top) / 2 + 1) * Box(20, JOURNAL + CLR, z_top - z + 2)
    for y, z, n in idl:
        part -= cyl([0, y, z], [1, 0, 0], (PIN + CLR_STEEL) / 2, 20)
    zn = cap_nut_z()
    for y, out in cap_screws():
        part -= Pos(0, y, (zn - 1 + z_top + 1) / 2) * Cylinder((SCREW + CLR_STEEL) / 2, z_top - zn + 2)
        part -= Pos(0, y, zn) * hexagon(NUT_AF + 0.3, NUT_T + 0.3, (0, 1))
        part -= Pos(0, (y + y + out * 20) / 2, zn + (NUT_T + 0.3) / 2) * Box(NUT_AF + 0.3, 20, NUT_T + 0.3)
    for i, (y, z) in enumerate(sh):                      # below the cranks' sweep (radius 6) and the axle heads
        part -= marks(i + 1, WALL_OUT, y, z_bot + 7)
    return Pos(CX, 0, 0) * part, (y0, y1, z_bot, z_top)


def test_cap():
    """Cap of the gear train test (v2.1), in robot coordinates (print it upside down): a plate on the spine's top with
    two tongues down every journal slot to the top of the journal hole, as base v1's cap has. The tongues stand over
    the outer part of each wall only (|x| TONGUE_IN..TONGUE_OUT), clear of the gear. Four skirts down the walls' outer
    faces at the end blocks locate the cap in X (TEST_SKIRT_CLR a side); the tongues in the slots locate it in Y. Two
    M3×12 down through it into the nuts in the end blocks."""
    sh = C.shaft_yz()
    y0, y1, _, z_top = spine_box()
    part = Pos(0, (y0 + y1) / 2, z_top + TEST_CAP_T / 2) * Box(TEST_CAP_W, y1 - y0, TEST_CAP_T)
    tw = JOURNAL + CLR - C.CAP_CLR
    for y, z in sh:
        # the tongue ends flat at the top of the journal hole: a round end (as on base v1's cap) is wider than the
        # tongue and leaves knife edges at its tips. The journal can rise 0.25 mm either way
        zb = z + (JOURNAL + CLR) / 2
        for sx in (1, -1):
            part += Pos(sx * (C.TONGUE_IN + C.TONGUE_OUT) / 2, y, (zb + z_top) / 2 + 0.01) * \
                Box(C.TONGUE_OUT - C.TONGUE_IN, tw, z_top - zb + 0.02)
    # X locator: skirts over the end blocks, where nothing turns (the cranks sweep 6.0 from the end shafts), with a
    # 0.4 mm lead-in on the inner edge of the tip
    xs = WALL_OUT + TEST_SKIRT_CLR
    for ya, yb in ((y0, sh[0][0] - TEST_SKIRT_GAP), (sh[-1][0] + TEST_SKIRT_GAP, y1)):
        for sx in (1, -1):
            sk = Pos(sx * (xs + TEST_SKIRT_T / 2), (ya + yb) / 2, z_top - TEST_SKIRT_H / 2 + 0.01) * \
                Box(TEST_SKIRT_T, yb - ya, TEST_SKIRT_H + 0.02)
            c = 0.4 * np.sqrt(2)
            sk -= Pos(sx * xs, (ya + yb) / 2, z_top - TEST_SKIRT_H) * Rot(0, 45, 0) * Box(c, yb - ya + 1, c)
            part += sk
    for y, _ in cap_screws():
        part -= Pos(0, y, z_top + TEST_CAP_T / 2) * Cylinder((SCREW + CLR_STEEL) / 2, TEST_CAP_T + 1)
    # +X edge marked with a dot over every shaft, so the cap's right side is plain to see (it only fits one way)
    for y, _ in sh:
        part -= marks(1, TEST_CAP_W / 2, y, z_top + TEST_CAP_T / 2)
    return Pos(CX, 0, 0) * part


PARTS = {"spine": lambda: spine()[0], "test-cap": test_cap}


def main():
    args = K.part_args(__doc__, PARTS)
    K.build_parts(PARTS, args.part or PARTS, OUT)


if __name__ == "__main__":
    main()
