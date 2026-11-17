#!/usr/bin/env python3
"""Chassis Part B2: `body-v2`, `holder-cradle`, `body-lug` (design-plan-b.md: Part list, I9-I11, «B2 addendum»).

Decision (Morante, 2026-11-17): the slicer lightens the body. body-v2 is the scanned skin
(../carcass-120/spideybot_body.stl, lifted by robot.LIFT) **as it is** (outer look untouched, no thinning) with plan B's
designed features added and cut; its grams come from the slicer (1 wall loop + gyroid 10 %, 85.5 g bare, S1), with a
«more loops» modifier on the features (FEATURE_BOXES, for the plater).

Features (every number below derived and commented; clearances from ../fits.py):
  - I9 hook posts: 2 L-slot posts on the scan's hook ribs, round front-block-v2's tongues (front_block.TONGUE_*): the
    vertical entry open at the bottom at +SLIDE in Y (the body is lowered 4 mm behind its place), the horizontal leg
    to the -Y end (the slide forward). WINDOW in Y and Z, 1.2 a side in X (plan «Body X stack-up»)
  - I9 lug root block under the rear skirt (H2): the separate `body-lug` (tab in the shell's notch, the M3×8's nut,
    its Ø7 ring on the floor shelf) is screwed to it by 2 × M3×10 from below on the bench, nuts in the root block
    (slid in from ±X; the notch walls, 1.0 off, keep them in)
  - I10 cradle groove blocks at the peg tubes: an L-groove each (entry notch at -CRADLE_SLIDE in Y, open at the
    bottom; the groove to a +Y end stop); 1 × M3×10 up through the floor, the ear and the roof into a nut slid in from
    the block's inboard face (the cradle's wall then closes the slot)
  - I11 eyes pocket opened downwards, 1.2 walls, 2 LED holes into the eye sockets, 1 × M3×10 whose head holds the
    board's bottom edge (the «screw tab»), its nut in a boss beside the pocket; a clip for the eyes lead
`holder-cradle`: a tray round the 4×AAA holder (snap lips 1.0 on the long bottom edges, ε 0.56 %), -Y crossbar above
the cover's plane, +Y end wall, top frame, 2 ears. `body-lug`: plan B's tab section.

    ../../.venv/bin/python body_v2.py                     # all three parts: out/*.stl, .step, grams
    ../../.venv/bin/python body_v2.py --part holder-cradle
"""
import os
import sys
import time

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from cad import common as K, fits, robot as R  # noqa: E402
import shell as SH  # noqa: E402  (shell interface numbers: notch, shelf, screw place, slide)
import front_block as FB  # noqa: E402  (tongue numbers)

BV = SH.BV
U, S, I, cyl, boxb = BV.U, BV.S, BV.I, BV.cyl, BV.boxb
OUT = os.path.join(HERE, "out")
RHO = SH.RHO
CX = R.CX
WIN, STL_ = fits.WINDOW.side, fits.STEEL.side
HOLE = fits.bore(K.SCREW, fits.STEEL)                       # 3.3
NUT_AF = K.NUT_AF + 2 * STL_                                 # 5.8 across the flats (nut pocket, plan «walls» probe)
NUT_H = K.NUT_T + 2 * STL_                                   # 2.7
CBORE = SH.CBORE                                             # 6.5
PLIERS_R = 5.0                    # the pliers' rod (tools/cad_verify.py TOOLS: Ø10)
RELIEF = 0.2                      # clear round a tool's rod where a relief is cut (plan «fourth pass»)
MOUTH = 25.0                      # a nut slot's mouth cut open this far past its pocket (the pliers' room, the nut's way out)
SEAT_DEPTH = 3.0                  # the flat seat cut reaches this far under the band top (z BAND_TOP) ...
SEAT_ABOVE = 3.0                  # ... and this far over it (the slide lip), in SEAT_LAYERS layers
SEAT_LAYERS = 12
SEAT_TRIM = 0.2                   # depth of the swept flat trim under the band top
SLIDE = SH.SLIDE                                             # 4: lowered 4 mm behind its place, slid forward

# ---- I9 hook posts (front_block tongues, read on the built block as verify.py does) -------------------------------
_fb = trimesh.load(os.path.join(OUT, f"{FB.NAME}.stl"))
TIP_L, TIP_R = float(_fb.bounds[0][0]), float(_fb.bounds[1][0])        # tongue tips (9.09, 75.96)
SIDE_L, SIDE_R = TIP_L + FB.TONGUE_OUT, TIP_R - FB.TONGUE_OUT          # block side faces at the tongues
HOOK_X = 1.2                       # a side in X (plan stack-up: slide lip 0.5 + pads 0.2 + 0.5)
HOOK_WALL = 2.0                    # behind the slot (a tab under load: >= 2)
T_Y0, T_Y1 = FB.TONGUE_Y           # -34, -28
T_Z1 = FB.TONGUE_TOP               # 103
T_Z0 = T_Z1 - FB.TONGUE_TIP - FB.TONGUE_OUT   # 98: the tongue's 45° underside meets the side face here
SLOT_Z = (T_Z0 - WIN, T_Z1 + WIN)  # 97.5-103.5: the horizontal leg
ENTRY_Y = (T_Y0 - WIN, T_Y1 + WIN)                   # the tongue + WINDOW in Y (its length: the entry's width)
LEG_Y = (T_Y0 - SLIDE - WIN, T_Y1 + WIN)             # body at +4 Y: the tongue is at y-4 in the body's frame
POST_Y = (LEG_Y[0] - 2.0, LEG_Y[1] + 2.0)            # 2 mm end walls
POST_Z = (SLOT_Z[0], 112.0)        # no floor: the shell's slide lip (top 96.5) is under it (-Z is the band top's);
                                   # up to 112 on the scan's rib (it hangs from the head at z 133)
RIB_CLEAR = 14.0                   # the scan's rib inboard of the post's face is cut to here (x from the side face)

# ---- I10 cradle (robot.HOLDER at HOLDER_CENTRE) ----------------------------------------------------------------------
HX, HY, HZ = R.HOLDER
HC = R.HOLDER_CENTRE
H0 = np.array(HC) - np.array([HX, HY, HZ]) / 2       # holder box min (x 18.2, y -21, z 98.5)
H1 = np.array(HC) + np.array([HX, HY, HZ]) / 2
CR_T = 1.2                         # walls, frame (nothing but the holder's 74 g hangs on them)
CR_IN = WIN                        # holder in the tray: WINDOW
CR_X0, CR_X1 = H0[0] - CR_IN - CR_T, H1[0] + CR_IN + CR_T     # tray outer faces in X
CR_Y0, CR_Y1 = H0[1] - CR_IN - CR_T, H1[1] + CR_IN + CR_T
CR_Z0 = H0[2] - CR_IN - CR_T       # lips' underside
CR_Z1 = H1[2] + CR_IN + CR_T       # top frame's top
SNAP = 1.0                         # lip reach under the case's long edges: wall deflection 1.0 over 18 mm:
                                   # ε = 1.5·t·y/L² = 1.5·1.2·1.0/18² = 0.56 % (≤ 2 %, rule §3.2)
CROSS_Z = 101.0                    # -Y crossbar from here up (the cover's plane is 98.5-100.5: it slides under)
FRAME_IN = 5.0                     # top frame width
EAR_Z = (105.0, 107.4)             # ear: 2.4 thick (tab >= 2)
EAR_OUT = 7.0                      # ear reach out of the wall (the screw hole 1.6 / 2.1 from its edges)
EAR_Y = (HC[1] - 4.0, HC[1] + 4.0) # 7-15 at its place
CRADLE_SLIDE = 11.5                # plan I10: the ears enter 11.5 mm forward of their place
GROOVE_Z = (EAR_Z[0] - WIN, EAR_Z[1] + WIN)
BLK_GAP = WIN                      # block inboard face to the tray wall
BLK_W = 10.0                       # block width in X (x 6-16 on the left: inside the peg tube, 3 mm behind the groove)
BLK_FLOOR, BLK_ROOF = 2.0, 1.2
BLK_Z0 = GROOVE_Z[0] - BLK_FLOOR   # 102.5: the screw head bears here
NUTP_Z0 = GROOVE_Z[1] + BLK_ROOF   # nut pocket bottom
BLK_Z1 = NUTP_Z0 + NUT_H + 1.2     # roof over the nut
BLK_Y = (EAR_Y[0] - CRADLE_SLIDE - WIN - 2.0, EAR_Y[1] + WIN + 2.0)   # 2 mm end walls; +Y end = the stop
CR_SCREW_L = 10.0

# ---- I11 eyes pocket (robot.EYES_BOX = the board's box) --------------------------------------------------------------
E0, E1 = np.array(R.EYES_BOX[0]), np.array(R.EYES_BOX[1])
P0, P1 = E0 - WIN, E1 + WIN        # pocket
EW = 1.2                           # walls
EYE_WALL_Z0 = 112.0                # walls start here (front block top 106.5 + 5)
LED_D = fits.bore(5.0, fits.WINDOW)   # 6.0: 5 mm LED (hardware.md: 3 or 5 mm; a 3 mm one passes too)
LED_X = (25.0, 2 * CX - 25.0)      # eye socket centres (probe on the scan: open x 20-30 / 56-66 at z 120-136)
LED_Z = (E0[2] + E1[2]) / 2        # 128
EB_OUT = 3.0                       # the screw sits this much further outboard than «shank 0.5 off the board» (x 16.0):
                                   # its nut (to x +3.35) then clears the board's edge by > WINDOW
EB_SCREW = (E0[0] - K.SCREW / 2 - WIN - EB_OUT, (E0[1] + E1[1]) / 2)   # x 13.0
EB_HEAD_TOP = P0[2]                # 116.5: the tab's top, 0.5 under the board (and the boss's underside)
TAB_T = 2.0                        # printed washer tab (tab >= 2)
TAB_LAP = 2.5                      # the tab reaches this far under the board's left edge
TAB_W = 8.0                        # across Y
TAB_X = (EB_SCREW[0] - 3.5, E0[0] + TAB_LAP)          # 9.5 - 20.5
EB_SCREW_Z = EB_HEAD_TOP - TAB_T   # 114.5: the head's top, under the tab
EB_SCREW_L = 10.0
EB_BOSS = (EB_SCREW[0] - 4.6, P0[0] - 0.2)           # boss x range round the screw, merged into the pocket wall
CLIP = (CX - 4.0, CX + 4.0, P1[1] + EW, P1[1] + EW + 4.0, 109.0, 112.5)   # x0 x1 y0 y1 z0 z1 behind the pocket
CLIP_SLOT = SH.LEAD_D + 2 * WIN    # 3.5 wide, open at the bottom

# ---- I9 lug (plan «Rear block layout», the tab's section) ------------------------------------------------------------
SX, SY = SH.SCREW_XY               # M3×8 from below (33.7, 37.5)
LUG_X = (SH.NOTCH[0] + 1.0, SH.NOTCH[2] - 1.0)       # 1.0 a side in the notch
LUG_Y0 = SH.NOTCH[1] + 0.55        # 33.55: the notch front + WINDOW (+0.05)
LUG_TOP = R.DATUMS["body_lug_top_max"]               # 81.2
RING_D, RING_H = 7.0, 0.5          # the ring that bears on the shelf
LUG_Z0 = R.DECK_TOP + RING_H       # 75.3: the tab's bottom over the ring
NUT_Z = (76.9, 76.9 + NUT_H - 0.0)  # plan: z 76.9-79.6
LUG_SCREW_Y = 44.8                 # the 2 lug screws: heads (r 2.75) 0.45 behind the shelf (y 41.6)
LUG_SCREW_X = (SX - 3.3, SX + 3.3)
LUG_REAR_Z0 = 76.0                 # the lug's rear part: heads under it at 73-76
LUG_Y1 = LUG_SCREW_Y + 3.7
LUG_SCREW_L = 10.0
ROOT_Y = (36.0, LUG_Y1 + 0.5)      # root block behind the skirt's inner face (35.65)
ROOT_Z1 = 92.0                     # merges into the skirt (underside 82-88.5 over this y range)
ROOT_NUT_Z0 = LUG_TOP + 1.3        # nut pocket in the root block

# ---- print: «more loops» modifier regions (slicer), named for the plater -------------------------------------------
FEATURE_BOXES = {
    "hook-post-L": ((SIDE_L - HOOK_X - FB.TONGUE_OUT - HOOK_WALL - 0.5, POST_Y[0] - 0.5, POST_Z[0] - 0.5),
                    (SIDE_L - HOOK_X + 0.5, POST_Y[1] + 0.5, POST_Z[1] + 0.5)),
    "hook-post-R": ((SIDE_R + HOOK_X - 0.5, POST_Y[0] - 0.5, POST_Z[0] - 0.5),
                    (SIDE_R + HOOK_X + FB.TONGUE_OUT + HOOK_WALL + 0.5, POST_Y[1] + 0.5, POST_Z[1] + 0.5)),
    "groove-block-L": ((CR_X0 - BLK_GAP - BLK_W - 0.5, BLK_Y[0] - 0.5, BLK_Z0 - 0.5),
                       (CR_X0 - BLK_GAP + 0.5, BLK_Y[1] + 0.5, BLK_Z1 + 0.5)),
    "groove-block-R": ((CR_X1 + BLK_GAP - 0.5, BLK_Y[0] - 0.5, BLK_Z0 - 0.5),
                       (CR_X1 + BLK_GAP + BLK_W + 0.5, BLK_Y[1] + 0.5, BLK_Z1 + 0.5)),
    "root-block": ((LUG_X[0] - 0.5, ROOT_Y[0] - 0.5, LUG_TOP - 0.5), (LUG_X[1] + 0.5, ROOT_Y[1] + 0.5, ROOT_Z1)),
    "eyes-boss": ((EB_BOSS[0] - 0.5, E0[1] - 3.5, EB_HEAD_TOP - 0.5), (EB_BOSS[1] + 0.5, E1[1] + 3.5, 130.0)),
}


def hexprism(xy, z0, z1, af=NUT_AF):
    m = trimesh.creation.cylinder(radius=af / 2 / np.cos(np.pi / 6), height=z1 - z0, sections=6)
    m.apply_translation([xy[0], xy[1], (z0 + z1) / 2])
    return m


def xcyl(r, x0, x1, y, z):
    """Cylinder along X from x0 to x1 at (y, z): the pliers' relief."""
    m = trimesh.creation.cylinder(radius=r, height=abs(x1 - x0), sections=48)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    m.apply_translation([(x0 + x1) / 2, y, z])
    return m


def bx(x0, x1, y0, y1, z0, z1):
    return boxb((min(x0, x1), min(y0, y1), min(z0, z1)), (max(x0, x1), max(y0, y1), max(z0, z1)))


def hook_post(sgn):
    """sgn -1: left (x < CX), +1: right. Post outboard of the tongue, slot cut in its inboard face."""
    side = SIDE_L if sgn < 0 else SIDE_R
    face = side + sgn * HOOK_X                       # post's inboard face
    bottom = face + sgn * FB.TONGUE_OUT              # slot bottom (1.2 beyond the tip)
    back = bottom + sgn * HOOK_WALL
    add = bx(face, back, POST_Y[0], POST_Y[1], POST_Z[0], POST_Z[1])
    e = 0.01
    cut = [bx(face - sgn * e, bottom, LEG_Y[0], LEG_Y[1], SLOT_Z[0], SLOT_Z[1]),            # the horizontal leg
           bx(face - sgn * e, bottom, LEG_Y[0], LEG_Y[0] + (ENTRY_Y[1] - ENTRY_Y[0]),        # the entry, open below
              R.BAND_TOP - 1.0, SLOT_Z[1]),   # the scan's rib under it too
           # the scan's rib between the post's face and the block, from the seat to the post's top
           bx(face - sgn * e, side + sgn * -RIB_CLEAR, POST_Y[0] - 1.0, POST_Y[1] + 1.0, R.BAND_TOP - 1.0, POST_Z[1])]
    # lead-in 45° at the entry's mouth: a wedge 1 mm
    return add, cut


def groove_block(sgn):
    face = (CR_X0 - BLK_GAP) if sgn < 0 else (CR_X1 + BLK_GAP)
    out = face + sgn * BLK_W
    gb = face + sgn * (EAR_OUT + WIN - BLK_GAP)      # groove bottom: the ear's tip + WINDOW
    add = bx(face, out, BLK_Y[0], BLK_Y[1], BLK_Z0, BLK_Z1)
    e = 0.01
    sx = (face + (face + sgn * (EAR_OUT - BLK_GAP))) / 2      # screw on the ear's middle (in the groove)
    sy = (EAR_Y[0] + EAR_Y[1]) / 2
    cut = [bx(face - sgn * e, gb, EAR_Y[0] - CRADLE_SLIDE - WIN, EAR_Y[1] + WIN, GROOVE_Z[0], GROOVE_Z[1]),
           bx(face - sgn * e, gb, EAR_Y[0] - CRADLE_SLIDE - WIN, EAR_Y[1] - CRADLE_SLIDE + WIN, BLK_Z0 - 1, GROOVE_Z[1]),
           cyl(HOLE / 2, BLK_Z0 - 1, BLK_Z1 - 1.2, (sx, sy)),
           cyl(K.HEAD_D / 2 + 0.3, BLK_Z0 - 4.0, BLK_Z0, (sx, sy)),   # head and 2.5 key room: a strip under the floor
           hexprism((sx, sy), NUTP_Z0, NUTP_Z0 + NUT_H),
           bx(sx, face - sgn * e, sy - NUT_AF / 2, sy + NUT_AF / 2, NUTP_Z0, NUTP_Z0 + NUT_H)]   # slot to the face
    return add, cut, (sx, sy)


def led_hole(x):
    """Through the pocket's front wall, along Y, at an eye socket's centre."""
    h = EW + 1.2
    m = trimesh.creation.cylinder(radius=LED_D / 2, height=h, sections=32)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, P0[1] - h / 2 + 0.1, LED_Z])
    return m


def eyes_features():
    add = [bx(P0[0] - EW, P1[0] + EW, P0[1] - EW, P1[1] + EW, EYE_WALL_Z0, P1[2] + EW),
           bx(EB_BOSS[0], EB_BOSS[1], E0[1] - 3.0, E1[1] + 3.0, EB_HEAD_TOP, EB_HEAD_TOP + 13.0),
           bx(*CLIP)]
    sx, sy = EB_SCREW
    nz = EB_SCREW_Z + EB_SCREW_L - NUT_H - 0.5
    cut = [bx(P0[0], P1[0], P0[1], P1[1], R.BAND_TOP - 8.0, P1[2]),                       # the pocket, open downwards
           *[led_hole(x) for x in LED_X],
           cyl(HOLE / 2, EB_HEAD_TOP - 0.01, EB_SCREW_Z + EB_SCREW_L + 1.0, (sx, sy)),
           # the tab's slot through the pocket wall (WINDOW round the tab, up to the boss's underside)
           bx(TAB_X[0] - WIN, P0[0] + 0.01, sy - TAB_W / 2 - WIN, sy + TAB_W / 2 + WIN, R.BAND_TOP - 8.0, EB_HEAD_TOP),
           hexprism((sx, sy), nz, nz + NUT_H),
           bx(sx, EB_BOSS[0] - MOUTH, sy - NUT_AF / 2, sy + NUT_AF / 2, nz, nz + NUT_H),   # nut slot from -X, mouth open
           # the pliers' rod (nose 8 mm off the boss) clipped the cheek's rounded edge 2 mm³: relief round its path
           xcyl(PLIERS_R + RELIEF, EB_BOSS[0] - 8.0, EB_BOSS[0] - MOUTH - 8.0, sy, nz + NUT_H / 2),
           bx((CLIP[0] + CLIP[1]) / 2 - CLIP_SLOT / 2, (CLIP[0] + CLIP[1]) / 2 + CLIP_SLOT / 2,
              CLIP[2] - 0.1, CLIP[3] + 0.1, CLIP[4] - 0.1, CLIP[5] - 1.2)]
    return add, cut


def eyes_tab():
    """Printed washer tab under the boss: the screw head clamps it up, its end lies 0.5 under the board's left edge."""
    sx, sy = EB_SCREW
    return S(bx(TAB_X[0], TAB_X[1], sy - TAB_W / 2, sy + TAB_W / 2, EB_SCREW_Z, EB_HEAD_TOP),
             cyl(HOLE / 2, EB_SCREW_Z - 1, EB_HEAD_TOP + 1, (sx, sy)))


def root_features():
    add = [bx(LUG_X[0], LUG_X[1], ROOT_Y[0], ROOT_Y[1], LUG_TOP, ROOT_Z1)]
    cut = []
    for k, x in enumerate(LUG_SCREW_X):
        cut.append(cyl(HOLE / 2, LUG_TOP - 0.01, LUG_TOP + LUG_SCREW_L - (LUG_TOP - LUG_REAR_Z0) + 1.0,
                       (x, LUG_SCREW_Y)))
        cut.append(hexprism((x, LUG_SCREW_Y), ROOT_NUT_Z0, ROOT_NUT_Z0 + NUT_H))
        edge = LUG_X[0] - MOUTH if k == 0 else LUG_X[1] + MOUTH
        cut.append(bx(x, edge, LUG_SCREW_Y - NUT_AF / 2, LUG_SCREW_Y + NUT_AF / 2, ROOT_NUT_Z0, ROOT_NUT_Z0 + NUT_H))
        # relief in the skirt's inside for the pliers' rod (Ø10 round the nut's mid-plane) pushing the nut along its slot
        side = -1 if k == 0 else 1
        x0 = LUG_X[k]
        cut.append(xcyl(PLIERS_R + RELIEF, x0, x0 + side * (8.0 + 20.0 + 1.0), LUG_SCREW_Y, ROOT_NUT_Z0 + K.NUT_T / 2))
    return add, cut


def body_lug():
    m = U(bx(LUG_X[0], LUG_X[1], LUG_Y0, SH.SHELF[3] - 0.05, LUG_Z0, LUG_TOP),
          bx(LUG_X[0], LUG_X[1], SH.SHELF[3] - 0.05, LUG_Y1, LUG_REAR_Z0, LUG_TOP),
          cyl(RING_D / 2, R.DECK_TOP, LUG_Z0 + 0.01, (SX, SY)))
    cuts = [cyl(HOLE / 2, R.DECK_TOP - 1, LUG_TOP + 1, (SX, SY)),
            hexprism((SX, SY), NUT_Z[0], NUT_Z[1]),
            bx(SX, LUG_X[0] - 0.1, SY - NUT_AF / 2, SY + NUT_AF / 2, NUT_Z[0], NUT_Z[1])]    # nut in from -X
    for x in LUG_SCREW_X:
        cuts.append(cyl(HOLE / 2, LUG_REAR_Z0 - 1, LUG_TOP + 1, (x, LUG_SCREW_Y)))
    # clear of the crank cover's rear lip (verify.py found 8.85 mm³ of overlap at x 38.5-39.7, y 33.6-34.8): WINDOW off
    # its +X-side end (the lip starts at rear_slot()[0] + WIN) and off its rear face
    cuts.append(bx(SH.rear_slot()[0], LUG_X[1] + 1.0, LUG_Y0 - 1.0, SH.REAR_FACE_Y + WIN, LUG_Z0 - 1.0, LUG_TOP + 1.0))
    return S(m, *cuts)


def holder_cradle():
    e = 0.01
    walls = [bx(CR_X0, CR_X0 + CR_T, CR_Y0, CR_Y1, CR_Z0, CR_Z1), bx(CR_X1 - CR_T, CR_X1, CR_Y0, CR_Y1, CR_Z0, CR_Z1)]
    frame = S(bx(CR_X0, CR_X1, CR_Y0, CR_Y1, CR_Z1 - CR_T, CR_Z1),
              bx(CR_X0 + FRAME_IN, CR_X1 - FRAME_IN, CR_Y0 + FRAME_IN, CR_Y1 - FRAME_IN, CR_Z1 - CR_T - 1, CR_Z1 + 1))
    lips = [bx(CR_X0, CR_X0 + CR_T + CR_IN + SNAP, H0[1], H1[1], CR_Z0, CR_Z0 + CR_T),
            bx(CR_X1 - CR_T - CR_IN - SNAP, CR_X1, H0[1], H1[1], CR_Z0, CR_Z0 + CR_T)]
    cross = bx(CR_X0, CR_X1, CR_Y0, CR_Y0 + CR_T, CROSS_Z, CR_Z1)
    end = bx(CR_X0, CR_X1, CR_Y1 - CR_T, CR_Y1, CROSS_Z, CR_Z1)
    ears = [bx(CR_X0 - EAR_OUT, CR_X0 + e, EAR_Y[0], EAR_Y[1], *EAR_Z),
            bx(CR_X1 - e, CR_X1 + EAR_OUT, EAR_Y[0], EAR_Y[1], *EAR_Z)]
    m = U(*walls, frame, *lips, cross, end, *ears)
    sy = (EAR_Y[0] + EAR_Y[1]) / 2
    cuts = [cyl(HOLE / 2, EAR_Z[0] - 1, EAR_Z[1] + 1, (CR_X0 - (EAR_OUT - BLK_GAP) / 2 - BLK_GAP, sy)),
            cyl(HOLE / 2, EAR_Z[0] - 1, EAR_Z[1] + 1, (CR_X1 + (EAR_OUT - BLK_GAP) / 2 + BLK_GAP, sy)),
            # wall windows (mass): ribs 6 mm round them
            bx(CR_X0 - 1, CR_X0 + CR_T + 1, CR_Y0 + 6, EAR_Y[0] - 3, CR_Z0 + CR_T + 3, CR_Z1 - CR_T - 3),
            bx(CR_X1 - CR_T - 1, CR_X1 + 1, CR_Y0 + 6, EAR_Y[0] - 3, CR_Z0 + CR_T + 3, CR_Z1 - CR_T - 3),
            bx(CR_X0 - 1, CR_X0 + CR_T + 1, EAR_Y[1] + 3, CR_Y1 - 6, CR_Z0 + CR_T + 3, CR_Z1 - CR_T - 3),
            bx(CR_X1 - CR_T - 1, CR_X1 + 1, EAR_Y[1] + 3, CR_Y1 - 6, CR_Z0 + CR_T + 3, CR_Z1 - CR_T - 3)]
    # the scan's rear inner wall comes within 0.025 mm of the side walls' lower rear corners (y 44.6, z 96.8-97.3;
    # verify.py found a 0.00 mm³ overlap): the walls end at the holder's rear end + WINDOW below the crossbar's height
    cuts.append(bx(CR_X0 - 1, CR_X1 + 1, H1[1] + CR_IN, CR_Y1 + 1, CR_Z0 - 1, CROSS_Z))
    return S(m, *cuts)


def body_v2():
    skin = R.carcass("body", lifted=True)
    adds, cuts = [], []
    for sgn in (-1, 1):
        a, c = hook_post(sgn)
        adds.append(a)
        cuts += c
        a, c, _ = groove_block(sgn)
        adds.append(a)
        cuts += c
    a, c = eyes_features()
    adds += a
    cuts += c
    a, c = root_features()
    adds += a
    cuts += c
    # the scan's seat sits 0.1 mm into the band top (8.2 mm³ at z 93.4-93.5). The body RESTS on the band top (plan:
    # «the seat bears at the sides and front»): a flat cut, no lift. In SEAT_LAYERS layers from SEAT_DEPTH under the band
    # top to SEAT_ABOVE over it, the shell's section there carried back along the slide (a 2D sweep, extruded: no 3D sweep) is cut out of the body,
    # WIN wider sideways: the seat is trimmed flat at z = BAND_TOP, and the skirt clears the band wall outside it.
    ch = trimesh.load(os.path.join(OUT, "chassis.stl"))
    from shapely.ops import unary_union
    from shapely.affinity import translate as _tr
    zs = np.linspace(R.BAND_TOP - SEAT_DEPTH, R.BAND_TOP + SEAT_ABOVE, SEAT_LAYERS + 1)
    layers = [(zs[i], zs[i + 1]) for i in range(SEAT_LAYERS)] + [(R.BAND_TOP - SEAT_TRIM, R.BAND_TOP)]
    pieces = []
    for z0, z1 in layers:
        sec = ch.section(plane_origin=[0, 0, (z0 + z1) / 2], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        pl, T = sec.to_2D()
        T = np.asarray(T)
        back = np.linalg.inv(T)[:3, :3] @ [0.0, -1.0, 0.0]      # world -Y in the section's own 2D frame
        base = unary_union(list(pl.polygons_full))
        # the layer's section carried back SLIDE in -Y (the body at every mm of the slide), WIN wider sideways
        swept = unary_union([_tr(base, back[0] * k, back[1] * k) for k in np.arange(0.0, SLIDE + 0.01, 0.5)]).buffer(WIN)
        for poly in (swept.geoms if hasattr(swept, "geoms") else [swept]):
            e = trimesh.creation.extrude_polygon(poly, z1 - z0)
            e.apply_transform(T)
            e.apply_translation([0, 0, z0 - (z0 + z1) / 2])
            pieces.append(e)
    cuts.append(U(*pieces))
    return S(U(skin, *adds), *cuts)


def screw_places():
    """Hardware places for verify.py (one source)."""
    g = {s: groove_block(s)[2] for s in (-1, 1)}
    return {"cradle": [(g[-1][0], g[-1][1], BLK_Z0), (g[1][0], g[1][1], BLK_Z0)],
            "eyes": (EB_SCREW[0], EB_SCREW[1], EB_SCREW_Z),
            "lug": [(x, LUG_SCREW_Y, LUG_REAR_Z0) for x in LUG_SCREW_X]}


def write_step(m, stl, path):
    import build123d as bd
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS, TopoDS_Shape
    sh = TopoDS_Shape()
    StlAPI_Reader().Read(sh, stl)
    sew = BRepBuilderAPI_Sewing(1e-4)
    sew.Add(sh)
    sew.Perform()
    ex, ms = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL), BRepBuilderAPI_MakeSolid()
    while ex.More():
        ms.Add(TopoDS.Shell(ex.Current()))
        ex.Next()
    sol = bd.Solid(ms.Solid())
    if abs(sol.volume - m.volume) > 0.01 * m.volume:
        raise RuntimeError(f"STEP solid {sol.volume:.0f} mm³ against the STL's {m.volume:.0f}")
    bd.export_step(sol, path)


PARTS = {"body-v2": body_v2, "holder-cradle": holder_cradle, "body-lug": body_lug, "eyes-tab": eyes_tab}


def build(n, step=True):
    """Build one part into out/ (STL, and STEP unless step is False); build.py --part <name> calls this."""
    t0 = time.time()
    m = PARTS[n]()
    p = os.path.join(OUT, f"{n}.stl")
    r = SH.export(m, p)
    if step:
        write_step(r, p, os.path.join(OUT, f"{n}.step"))
    print(f"{n}: {np.round(r.bounds, 1).tolist()} {r.volume / 1000:.2f} cm³ solid = {r.volume / 1000 * RHO:.1f} g "
          f"watertight {r.is_watertight}  {time.time() - t0:.0f} s")


def main():
    names = [sys.argv[sys.argv.index("--part") + 1]] if "--part" in sys.argv else list(PARTS)
    for n in names:
        build(n, "--no-step" not in sys.argv)


if __name__ == "__main__":
    main()
