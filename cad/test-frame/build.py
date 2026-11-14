#!/usr/bin/env python3
"""Test frame: a desk stand for one middle leg (right), its pivot fork and crankshaft 2, turned by hand.

Parts (all PLA):
  test-frame         plate, a slice of the spine with crankshaft 2's journal slots, and a bracket whose two arms hold
                     the fork's swivel screws.
  test-frame-keeper  cap over the journal slots, 2 × M3×12 into nuts in the end blocks (print it upside down).

The leg, fork and crankshaft are those of ../legs and ../crankshafts. Coordinates as in ../README.md (mm, Z up,
forward = -Y, +X = right); both parts are exported to out/ in robot coordinates.

Usage:
    python3 build.py
    python3 build.py --part test-frame-keeper
    python3 ../legs/check.py --gaps    # the whole drive and this frame over a full turn
"""
import functools
import os
import sys

import numpy as np
from build123d import Box, Cylinder, Pos

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design  # noqa: E402
from cad.common import CLR, CLR_STEEL, CX, NUT_AF, NUT_T, SCREW, cyl, sim  # noqa: E402

C = design("crankshafts")
L = design("legs")
OUT = os.path.join(HERE, "out")

# --- parameters (mm) -----------------------------------------------------------------------------------------
JOURNAL, MOD, SHAFT_TEETH, WALL_IN, WALL_OUT = C.JOURNAL, C.MOD, C.SHAFT_TEETH, C.WALL_IN, C.WALL_OUT
KEEP_Y = 14.0        # test frame: the shaft's walls reach this far either side of the shaft (end blocks beyond KEEP_GAP)
KEEP_GAP = C.KEEP_GAP  # end blocks start here, clear of the gear's tips (radius 7)
KEEP_SCREW_Y = 11.25 # keeper screws, either side of the shaft


@functools.lru_cache(maxsize=None)
def test_frame():
    """Stand for the right middle leg (i = 1) and crankshaft 2, in robot coordinates; returns the frame part and the
    height of its plate's top."""
    l = [x for x in sim.pivots() if x[0] == "R" and x[1] == 1][0]
    P = l[2]
    y_sh, z_sh = C.shaft_yz()[1]
    th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    feet = np.array([L.legs_at(t)[1]["F"] for t in th])
    z_floor = feet[:, 2].min() - 3                         # plate top just under the lowest foot
    plate_t = 4
    x0, x1 = CX - WALL_OUT - 6, P[0] + 12
    ya, yb = y_sh - 14, y_sh + 14
    frame = Pos((x0 + x1) / 2, (ya + yb) / 2, z_floor - plate_t / 2) * Box(x1 - x0, yb - ya, plate_t)
    # spine slice: two walls with the journal slot, from the plate up to the shaft + 6
    zt = z_sh + 6
    for sx in (1, -1):
        frame += Pos(CX + sx * (WALL_IN + WALL_OUT) / 2, y_sh, (zt + z_floor) / 2) * \
            Box(WALL_OUT - WALL_IN, 2 * KEEP_Y, zt - z_floor)
    # end blocks between the walls, clear of the gear (tip radius 7), each with a nut pocket for a keeper screw
    for sy in (1, -1):
        yc = y_sh + sy * (KEEP_GAP + KEEP_Y) / 2
        frame += Pos(CX, yc, (zt + z_floor) / 2) * Box(2 * WALL_IN + 0.01, KEEP_Y - KEEP_GAP, zt - z_floor)
        ys = y_sh + sy * KEEP_SCREW_Y
        frame -= Pos(CX, ys, zt - 4.5) * Cylinder((SCREW + CLR_STEEL) / 2, 9.2)
        frame -= Pos(CX, (ys + y_sh + sy * (KEEP_Y + 1)) / 2, zt - 5.5) * \
            Box(NUT_AF + 0.3, abs(y_sh + sy * (KEEP_Y + 1) - ys) + (NUT_AF + 0.3) / 2, NUT_T + 0.3)
    frame -= cyl([CX, y_sh, z_sh], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
    frame -= Pos(CX, y_sh, (z_sh + zt) / 2 + 1) * Box(20, JOURNAL + CLR, zt - z_sh + 2)
    # the gear must clear the plate: cut a pocket under it
    frame -= Pos(CX, y_sh, z_floor - plate_t / 2) * Box(2 * WALL_IN - 0.5, 2 * (SHAFT_TEETH / 2 + 1.5), plate_t + 1)
    # pivot bracket: two arms above and below the fork, reaching past it from a post beside the leg (+Y, behind it).
    # An M3×10 through each arm, locked to the arm by a nut on its inner face; the screw's tip goes 3 mm into the
    # fork and is the vertical axis it swings on
    _, win_y, _, h = L.yoke_size()
    arm_t, gap = 3.0, NUT_T + 0.4
    post_y = P[1] + (win_y + 2 * L.YOKE_WALL) / 2 + 7
    z_up, z_dn = P[2] + h / 2 + gap + arm_t / 2, P[2] - h / 2 - gap - arm_t / 2
    for zc in (z_up, z_dn):
        ya, yb_ = P[1] - 5, post_y + 3                                              # the hole is 5 mm from the arm's end
        frame += Pos(P[0], (ya + yb_) / 2, zc) * Box(8, yb_ - ya, arm_t)
        frame -= Pos(P[0], P[1], zc) * Cylinder((SCREW + CLR_STEEL) / 2, arm_t + 1)
    frame += Pos(P[0], post_y + 1.5, (z_up + arm_t / 2 + z_floor) / 2) * Box(8, 6, z_up + arm_t / 2 - z_floor)
    # plate reaches the post
    frame += Pos(P[0], (yb + post_y + 4.5) / 2, z_floor - plate_t / 2) * Box(12, post_y + 4.5 - yb + 1, plate_t)
    return frame, z_floor


def keeper():
    """Cap over the test frame's journal slots, in robot coordinates (print it upside down): a bridge on top of the
    walls and end blocks, a pocket for the gear's tips, and a tongue down each slot whose round end completes the
    journal hole. Two M3×12 down through it into nuts in the end blocks."""
    y_sh, z_sh = C.shaft_yz()[1]
    zt = z_sh + 6
    t = 4.0
    part = Pos(CX, y_sh, zt + t / 2) * Box(2 * WALL_OUT, 2 * KEEP_Y, t)
    part -= Pos(CX, y_sh, zt) * Box(2 * WALL_IN, 2 * (MOD * (SHAFT_TEETH / 2 + 1) + 0.6), 2 * 1.6 + 0.6)
    tw = JOURNAL + CLR - CLR                                  # tongue: the slot's width less a sliding clearance
    for sx in (1, -1):
        xc = CX + sx * (WALL_IN + WALL_OUT) / 2
        tongue = Pos(xc, y_sh, (z_sh + zt) / 2 + 0.01) * Box(WALL_OUT - WALL_IN, tw, zt - z_sh + 0.02)
        part += tongue
    part -= cyl([CX, y_sh, z_sh], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
    for sy in (1, -1):
        part -= Pos(CX, y_sh + sy * KEEP_SCREW_Y, zt + t / 2) * Cylinder((SCREW + CLR_STEEL) / 2, t + 1)
    return part


PARTS = {"test-frame": lambda: test_frame()[0], "test-frame-keeper": keeper}


def main():
    args = K.part_args(__doc__, PARTS)
    K.build_parts(PARTS, args.part or PARTS, OUT)
    if not args.part or "test-frame" in args.part:
        print(f"test frame plate top at z {test_frame()[1]:.1f}")


if __name__ == "__main__":
    main()
