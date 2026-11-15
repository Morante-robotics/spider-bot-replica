#!/usr/bin/env python3
"""Chassis (base v2), Part A: the drive module that carries the whole drive and the N20, and its small parts.

Parts (all PLA), in robot coordinates (../README.md: mm, Z up, forward = -Y, +X = right):
  drive-module  spine walls with the journal slots, idler pin holes (blind at -X), the idler 3 pocket (5.9 for a
                5 mm idler), the gearbox pad on the +X wall, a V saddle and an end wall for the N20 inside its own Y
                band, the -X boss for the cap's and clamp's shared screw, the keeper recess, 4 nut traps for the
                chassis (I7). Its top is flat at the deck top: printed upside down, top on the bed.
  cap           keeper over the journal slots as test cap v2.1 (tongues, front skirts), windows round the pinion,
                shaft tip and motor; 2 × M3×12 (one shared with the clamp)
  motor-clamp   bar along X over the N20, from the cap's -X bridge (over the pinion at the keep-out height) to the
                end wall behind the motor; presses the gearbox and can through two pads; 2 × M3×12
  pinion        12 teeth, module 1, 5 mm face, D-bore pressed on the N20 shaft (F3)
  idler-3-v2    idler 3 with a 5 mm face: same 20 teeth, same phase, a phase dot
  pin-keeper    strip over the three idler pins' +X ends, in a recess, 1 × M3×8
  gauge-fork    bench tool: the 0.8 mm gauge, a U-fork slid into the press jig over the pinion; the press ends with
                the pinion bearing on it and it on the gearbox face
  press-jig     bench tool: U-channel open at +Z, stood on the table (-X face down): the pinion sits in its pocket
                (squared), the fork in a slot over it, the gearbox in a socket above (squares the motor); the motor
                is pushed down into it. A through hole for the shaft tip (and to push the pinion out). Also presses
                coupon K1's discs. After the press the fork lifts out and the motor slides out along +Z. Printed on
                its -Z face (open side up: no support)
  press-cup     bench tool, only if the thumb is not enough: cup over the can's rear rim, clear of the terminals (a
                slot open at +Z lets the wires out); jig and cup go between the jaws of a vise

Shared numbers come from ../robot.py (master model), ../crankshafts (shafts, idlers, gears) and ../fits.py
(clearances): none is typed here. Each part is exported to out/ in robot coordinates (verify.py places them as they
are); print orientations are in verify.py PRINT_ORIENT and README.md.

Usage:
    ../../.venv/bin/python build.py                  # every part
    ../../.venv/bin/python build.py --part cap       # one part
"""
import os
import sys

import numpy as np
from build123d import Box, Cone, Cylinder, Plane, Polygon, Pos, Rot, extrude

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402

C = design("crankshafts")
OUT = os.path.join(HERE, "out")

# ---- datums and drive geometry (imported) -------------------------------------------------------------------------
CX = R.CX
SH = R.SHAFTS                              # crank axes (y, z)
IDL = R.IDLERS                             # idler axes (y, z, teeth)
TOP = R.DECK_TOP                           # module top = deck top (74.8): flat, on the bed when printed
YM, ZM = R.MOTOR_AXIS[1], R.MOTOR_AXIS[2]  # motor and pinion axis (y, z), along +X
MR = R.N20_H / 2                           # motor can radius (6)
GB_X0 = R.GEARBOX_X - CX                   # gearbox face, x from CX (3.3)
GB_X1 = GB_X0 + R.N20_GEARBOX_L            # gearbox / can joint (12.3)
CAN_X1 = GB_X1 + R.N20_CAN_L               # rear face of the can (29.3)
TERM_X1 = CAN_X1 + R.N20_TERM_L            # end of the terminals (35.0)
PAD_Z = ZM - MR                            # gearbox bottom = pad top (66.05)
MOTOR_TOP = ZM + MR                        # 78.05

# ---- clearances (fits.py only) ------------------------------------------------------------------------------------
J_HOLE = fits.bore(C.JOURNAL, fits.TURN)   # journal hole and slot, 4.5
PIN_D = K.PIN                              # Ø3 steel idler pins
PIN_HOLE = fits.bore(PIN_D, fits.STEEL)    # 3.3
SCREW_HOLE = fits.bore(K.SCREW, fits.STEEL)
NUT_AF, NUT_T = K.NUT_AF + 2 * fits.STEEL.side, K.NUT_T + 2 * fits.STEEL.side   # captive nut pockets
GAX = fits.GEAR_AXIAL.side                 # 0.8: spinning face to a still face
SEAT = fits.MOTOR_SEAT.side                # 0.2: N20 to its seat faces and clamp pads
WIN = fits.WINDOW.side                     # 0.5: windows something passes through
LOC = fits.LOCATOR.side                    # 0.2: skirts, keeper recess
LEAD = 0.5                                 # lead-in chamfer on slot and hole mouths (agent rule 0.5-1)

# ---- spine walls ----------------------------------------------------------------------------------------------------
W_IN = C.GEAR_T / 2 + fits.GEAR_THRUST_CRANK.side      # 1.75: crank gears' room (= C.WALL_IN)
W_OUT = C.WALL_OUT         # 4.25: the webs ride on these faces (float C.SHAFT_FLOAT = GEAR_THRUST_CRANK)
IDLER12_FACE = C.GEAR_T - 0.4                          # printed idlers 1-2 (crankshafts idler_part)
I3_IN = R.IDLER3_FACE / 2 + fits.GEAR_THRUST_IDLER.side  # 2.95: idler 3 v2 pocket half width
I3_WALL = 2.55             # idler 3 pocket walls (plan: K2 «2.55 mm walls»), so the +X wall is 5.5 there
W_THICK = I3_IN + I3_WALL  # 5.5: walls round idler 3 and below the crank sweep
W_LOW_Z = 57.0             # below this the walls are thickened (pins, keeper): crank sweep bottom 57.89 (r 6.01)
PIN_L = 10.0               # Ø3 × 10 steel pins (stock length; the plan's 8.5 did not reach the -X wall at idler 3)
KEEP_RECESS = 0.6          # keeper recess depth in the +X wall face
PIN_X1 = W_THICK - KEEP_RECESS          # pin +X end, flush with the recess floor (4.9)
PIN_X0 = PIN_X1 - PIN_L                 # pin -X end, blind (-5.1)
PIN_END = 0.8              # blind end of the -X pin holes, with a push-out hole for a 1.5 hex key
PUSH_HOLE = 2.0
W_THICK_MX = -PIN_X0 + PIN_END          # -X wall below W_LOW_Z (5.9)
GEAR_ROOM = fits.GEAR_TIP.side   # radial room round every gear tip in its pocket
SELF_SUPPORT = 50.0        # degrees from horizontal: faces that print facing down (module upside down) are this steep
                           # at least (pocket bottoms as teardrops, the V saddle), so they need no support
KEEL = 2.0                 # side walls round the gear pockets
KEEL_FLOOR = 1.5           # floor under the flat-bottomed pockets (Morante 2026-11-14, keel option b): idler 3's
                           # floor at 55.77 - 11 - 0.5 - 1.5 = 42.77, base v1's keel 42.7; nothing pushes on it
KEEL_Z = IDL[2][1] - C.MOD * (IDL[2][2] / 2 + 1) - GEAR_ROOM - KEEL_FLOOR   # module's lowest z (42.77)
WEB_SWEEP = K.P_["r"] + C.STUB / 2 + 1.0   # crank webs and pins sweep this radius (6.01)
WEB_CUT = WEB_SWEEP + WIN               # walls stay at W_OUT inside this radius round each crank (6.51)
CRANK_X = K.P_["XC"] + C.BALL / 2      # crankshaft half width (13.8)
Y0 = SH[0][0] - 15.0       # module front: end block with the cap's front nut (as base v1, -14 + 1)
Y1 = SH[3][0] + C.MOD * (C.SHAFT_TEETH / 2 + 1) + GEAR_ROOM + 0.95   # module rear (34.73): crank 4's gear
                           # room + 0.95, inside the carcass's rear face (34.84 at CX); nothing pushes on this wall
TIP_SH = C.MOD * (C.SHAFT_TEETH / 2 + 1)

# ---- pinion zone, gearbox pad, saddle ---------------------------------------------------------------------------------
PIN_R = R.PINION_TIP_R + GAX            # 7.8: nothing still inside this radius next to the pinion's faces
TESS = 0.05                # cuts that must clear a keep-out exactly: + the STL's chord error (export tolerance 0.02)
PZ_X = R.PINION_FACE / 2 + GAX          # 3.3: walls inside |x| < 3.3 stop below the pinion (at ZM - 7.8)
SHAFT_X0 = GB_X0 - R.N20_SHAFT_L        # shaft tip, x from CX (-5.7)
SHAFT_SLOT = R.N20_SHAFT_D / 2 + GAX    # U-slot in the -X wall round the spinning shaft tip (2.3)
SAD_Y = (R.MOTOR_ENVELOPE[0][1] + LOC, R.MOTOR_ENVELOPE[1][1] - LOC)  # saddle inside the motor's own Y band
SAD_Z0 = 58.0              # saddle underside
_TAN = np.tan(np.radians(SELF_SUPPORT))
V_CAN = ZM - MR / np.cos(np.radians(SELF_SUPPORT))   # V (flanks at 50°) under the can: touches it on two lines
V_GB = PAD_Z - SEAT - (SAD_Y[1] - SAD_Y[0]) / 2 * _TAN   # V under the gearbox, clear of its corners (no contact)
STOP_X = CAN_X1 + SEAT     # can's rear face stop (+X), below the terminals
STOP_Z = ZM + R.N20_TERM_Z[0] - 1.0     # stop block top: 1 mm under the terminals
END_X0 = TERM_X1 + WIN     # end wall behind the terminals
END_X1 = END_X0 + 8.2      # long enough for a nut pocket with 1.2 walls
SCREW_CLAMP_X = (END_X0 + END_X1) / 2

# ---- cap ---------------------------------------------------------------------------------------------------------
CAP_W = 10.0               # half width of the plate (test cap v2.1 TEST_CAP_W 20)
CLAMP_Z0 = ZM + PIN_R      # clamp bar underside: the pinion's keep-out height (79.85)
CAP_T = CLAMP_Z0 - TOP     # cap plate 5.05 (test cap v2.1: 5.0): its top carries the clamp's -X foot
CAP_Y0, CAP_Y1 = Y0, SH[3][0] + 4.0     # over every slot; ends behind crank 4's tongues
TONGUE_W = J_HOLE - 2 * fits.TONGUE.side   # 3.9
CAP_PLAY = LOC             # the cap's X play: its front skirts, LOCATOR a side
CAP_HOLE = SCREW_HOLE + 2 * CAP_PLAY      # cap screw holes: the skirts locate the cap, not the screws (3.7)
SKIRT_T, SKIRT_H = 1.6, 4.0             # test cap v2.1 skirts (gear-train-test TEST_SKIRT_T, _H)
SKIRT_Y1 = SH[0][0] - 9.0               # front skirts stop 9 mm before crank 1 (cranks sweep 6.01)
BOSS_X = (-13.5, -W_THICK)              # -X boss: behind the shaft tip, 0.8 + clear of it, nut 1 mm off it
BOSS_Y = (YM - 4.18, YM + 4.22)         # inside the motor's band (legs 3L/4L pass 1.2-2.0 mm outside it)
BOSS_Z0 = 63.0
SCREW_SHARED = (-10.0, YM)              # cap + clamp screw in the -X boss (x from CX, y)
SCREW_FRONT = (0.0, SH[0][0] - 11.5)    # cap front screw (x from CX, y)
CAP_SCREW_L = 12.0                      # M3×12
CLAMP_T = 3.0
CLAMP_W = 8.0
CHEEK_T, CHEEK_H = 2.5, 1.5  # clamp cheeks down the gearbox flats: 2.5 thick, 1.5 down the flat (torque ≈ 190 N·mm
                           # / 5.25 lever ≈ 36 N on one cheek, root moment ≈ 36 × 1.2 → 5 MPa across the layers)
PINION_RELIEF = (4.5, 1.0) # clamp bar underside relieved ±4.5 mm round the pinion, 1 mm deep (bar 2.0 there)
KEEPER_T = 2.0
KEEPER_Y = (IDL[0][0] - 3.5, IDL[2][0] + 3.5)
KEEPER_Z = (52.0, W_LOW_Z)
KEEPER_SCREW = (-0.5, 46.2)             # (y, z): between idler 2 and idler 3 pockets; the nut's lower corner
                                        # (46.2 - 3.35) is at the keel floor, its slot open below
KEEPER_TAB = (KEEPER_SCREW[1] - 3.0, KEEPER_Z[0])
KEEPER_BLOCK = (-5.0, 4.0, None)        # spine block round the keeper nut (y0, y1, z bottom = KEEL_Z)
KEEPER_SCREW_L = 8.0
# ---- bench tools: gauge fork, press jig and cup (in robot coordinates at the press position, the motor at its place) ----
FORK_X = (R.PINION_FACE / 2, GB_X0)     # 2.5..3.3: the 0.8 gauge is the gap the pinion keeps from the gearbox face
FORK_HW = R.N20_W / 2 + 1.0             # 6.0: fork half width (Y): covers the gearbox face (10 across Y) with 1 to spare
FORK_Z = (ZM - R.N20_H / 2, ZM + 18.0)  # from the gearbox's -Z face (6 below the axis) to a handle 8 above the jig
FORK_SLOT = R.N20_SHAFT_D / 2 + WIN     # 2.0: U-slot round the shaft, open at -Z (the fork drops over it)
JIG_POCKET = R.PINION_TIP_R + LOC       # 7.2: pinion pocket (tip + 0.2 a side: squares the pinion), a U open at +Z
JIG_BACK = 6.0             # block behind the pinion: the shaft tip (3.2 past the pinion) stays in its hole
JIG_HW = 10.0              # block half section (Y and Z): ≥ 2.8 walls round the pinion pocket
JIG_HOLE = R.N20_SHAFT_D / 2 + WIN      # 2.0: shaft tip relief, a U through the back (a 2.5 hex key pushes the pinion out)
JIG_SLOT = (FORK_X[0] - WIN, FORK_X[1] + WIN, FORK_HW + WIN)   # fork slot: x 2.0..3.8, ±6.5 in Y, open at +Z
JIG_SLOT_Z0 = FORK_Z[0] - LOC           # slot end: the fork's U stops 0.2 under the shaft's axis (the shaft clears it)
JIG_SOCKET = (R.N20_W / 2 + fits.MOTOR_SEAT.side, R.N20_H / 2 + fits.MOTOR_SEAT.side)   # 5.2, 6.2: gearbox socket
JIG_TOP = GB_X0 + 6.0      # socket along 6 of the gearbox's 9 mm (x 9.3): squares the motor while it is pushed down
CUP_SKIRT = 3.0            # cup skirt over the can's rear end (locates the cup on the can)
CUP_WALL = 1.6             # skirt wall (nothing pushes on it)
CUP_T = 2.0                # cup top plate, the vise jaw's face (loaded: ≥ 1.2)
# I7: (x from CX, y, nut pocket bottom z, slide-in direction): all inside the carcass shell's inner surface
# (carcass inset WALL, verify.py KEEP_IN). The front nut is 0.15 off CX so its corner keeps 1.05 to the +X face; the
# two saddle nuts are under the can's V (x 20) and behind the can's stop (x 32.5), above the inner surface (≈ 53.3 and
# 57.6 there); the rear foot of rev 4 (y 27.8-35.8, outside the shell) is gone.
I7_NUTS = [(-0.15, SH[0][0] - 11.5, 58.2, (-1, 0)), (20.0, YM, 59.2, (0, 1)),
           (32.5, YM, 62.2, (0, 1)), (SCREW_SHARED[0], YM, 64.5, (-1, 0))]   # ≥ 1.2 under each nut
I7_TIP = 0.8               # each I7 hole stops this far above its nut: the screw is cut to length (README, I7 table)
I7_TIP_V = 0.0             # ... none under the can's V (x 20): the hole stops at the nut's top, 0.81 under the V's
                           # bottom (62.71); that screw is cut flush with the nut's top (README, I7 table)
WALL = 2.0                 # the chassis shell (Part B): carcass inset by this, the module stays inside it
END_SLOPE = (30.0, 0.5)    # saddle and end wall underside rises 0.5 mm per mm from x 30: the shell's inner surface
                           # rises from 57.3 (x 30) to 63.3 (x 44) at the saddle's +Y edge
FRONT_CHAMFER = 2.0        # front block's lower front edge, 45°: the shell's front curves in (y -51.5 at z 57)


# ---- helpers ----------------------------------------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    """Box between the given bounds; x from CX."""
    return Pos(CX + (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cylx(y, z, r, x0, x1):
    return Pos(CX + (x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def cylz(x, y, r, z0, z1):
    return Pos(CX + x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def prism_yz(pts, x0, x1):
    """Prism of a (y, z) outline from x0 to x1 (from CX)."""
    return Pos(CX + x0, 0, 0) * extrude(Plane.YZ * Polygon(*pts, align=None), amount=x1 - x0, dir=(1, 0, 0))


def nut_pocket(x, y, z0, out, length=20.0):
    """Captive M3 nut pocket lying flat (axis Z) from z0 up, with a slot out along `out` (2D unit vector) to slide it
    in: flats parallel to the slot."""
    out = np.asarray(out, float)
    h = Pos(CX + x, y, z0) * K.hexagon(NUT_AF, NUT_T, (out[0], out[1]))
    c = np.array([CX + x, y, z0 + NUT_T / 2]) + np.array([out[0], out[1], 0]) * length / 2
    sl = Pos(*c) * Rot(0, 0, np.degrees(np.arctan2(out[1], out[0]))) * Box(length, NUT_AF, NUT_T)
    return h + sl


def lead_in(x, y, r, z):
    """0.5 mm × 45° lead-in at the mouth (top, z) of a vertical hole of radius r."""
    return Pos(CX + x, y, z - LEAD) * Cone(r, r + LEAD + 0.01, LEAD + 0.01, align=None)


def prisms(poly, x0, x1):
    """prism_yz of a shapely polygon or multipolygon."""
    out = None
    for g in getattr(poly, "geoms", [poly]):
        if g.geom_type != "Polygon" or g.area < 0.01:
            continue
        p = prism_yz(list(g.exterior.coords)[:-1], x0, x1)
        out = p if out is None else out + p
    return out


def teardrop(y, z, r, n=48):
    """(y, z) outline of a circle of radius r with a point below it: flanks at SELF_SUPPORT from horizontal."""
    a = np.radians(SELF_SUPPORT)
    t0, t1 = -np.pi / 2 + a, 3 * np.pi / 2 - a            # arc over the top, from one tangent point to the other
    arc = [(y + r * np.cos(t), z + r * np.sin(t)) for t in np.linspace(t0, t1, n)]
    return arc + [(y, z - r / np.cos(a))]


def gears():
    """(y, z, tip radius, half width of its room) of every gear between the walls."""
    g = [(y, z, TIP_SH, W_IN) for y, z in SH]
    g += [(y, z, C.MOD * (n / 2 + 1), W_IN if k < 2 else I3_IN) for k, (y, z, n) in enumerate(IDL)]
    return g


def profile():
    """Side outline (y, z) of the spine: the top band, a keel round every gear pocket, the keeper and rear blocks."""
    from shapely.geometry import Polygon as SPoly, box as sbox
    from shapely.ops import unary_union
    shapes = [sbox(Y0, W_LOW_Z, Y1, TOP)]
    shapes += [pocket(y, z, r + GEAR_ROOM).buffer(KEEL, 16).intersection(
        sbox(Y0, z - r - GEAR_ROOM - KEEL_FLOOR, Y1, TOP)) for y, z, r, _ in gears()]
    shapes += [sbox(KEEPER_BLOCK[0], KEEL_Z, KEEPER_BLOCK[1], W_LOW_Z)]
    p = unary_union(shapes)
    p = p.intersection(sbox(Y0, 0, Y1, TOP))
    f = FRONT_CHAMFER                     # front block's lower front edge, 45°
    p = p.difference(SPoly([(Y0 - 1, W_LOW_Z - 1), (Y0 + f, W_LOW_Z - 1), (Y0 + f, W_LOW_Z), (Y0, W_LOW_Z + f),
                            (Y0 - 1, W_LOW_Z + f)]))
    return list(p.exterior.coords)[:-1]


def pocket(y, z, r, n=48):
    """(y, z) outline of a gear pocket: the teardrop cut flat at the circle's bottom (≈ 0.93 r bridge when printed
    upside down; Morante 2026-11-14, keel option b)."""
    from shapely.geometry import Polygon as SPoly, box as sbox
    return SPoly(teardrop(y, z, r, n)).intersection(sbox(y - 2 * r, z - r, y + 2 * r, z + 2 * r))


# ---- drive module ------------------------------------------------------------------------------------------------------
def drive_module():
    pts = profile()
    part = prism_yz(pts, -W_OUT, W_OUT)
    # thickening: below the crank sweep (pins, keeper) and round idler 3 (2.55 mm pocket walls, gearbox pad)
    from shapely.geometry import Polygon as SP, box as sbox
    lowp = SP(pts).intersection(sbox(Y0, 0, Y1, W_LOW_Z))
    part += prisms(lowp, W_OUT - 0.01, W_THICK) + prisms(lowp, -W_THICK_MX, -W_OUT + 0.01)
    y3, z3, n3 = IDL[2]
    r3 = C.MOD * (n3 / 2 + 1) + GEAR_ROOM
    i3 = SP(pts).intersection(sbox(y3 - r3 - 1.5, 0, y3 + r3 + 1.5, TOP))
    part += prisms(i3, W_OUT - 0.01, W_THICK) + prisms(i3, -W_THICK, -W_OUT + 0.01)
    # -X boss: the cap's and clamp's shared screw, and an I7 nut, behind the shaft tip
    part += box(BOSS_X[0], BOSS_X[1] + 0.01, BOSS_Y[0], BOSS_Y[1], BOSS_Z0, TOP)
    # saddle (inside the motor's Y band) from the +X wall to the end wall behind the terminals
    part += box(W_THICK - 0.01, END_X1, SAD_Y[0], SAD_Y[1], SAD_Z0, STOP_Z)
    part += box(END_X0, END_X1, SAD_Y[0], SAD_Y[1], SAD_Z0, TOP)
    xs, k = END_SLOPE                   # underside rises from x xs: inside the shell's inner surface
    zx = SAD_Z0 + k * (END_X1 + 1 - xs)
    part -= Pos(0, 0, 0) * extrude(Plane.XZ * Polygon(*[(CX + xs, SAD_Z0 - 1), (CX + END_X1 + 1, SAD_Z0 - 1),
                                                       (CX + END_X1 + 1, zx), (CX + xs, SAD_Z0)], align=None),
                                   amount=40, both=True)
    cut = []
    # crank web sweep: the walls are W_OUT (the webs' thrust faces) within WEB_CUT of each crank
    for y, z in SH:                     # ... and above it, so the webs pass the thickened walls when it drops in
        cut += [cylx(y, z, WEB_CUT, W_OUT, CRANK_X + 1), cylx(y, z, WEB_CUT, -CRANK_X - 1, -W_OUT),
                box(W_OUT, CRANK_X + 1, y - WEB_CUT, y + WEB_CUT, z, TOP + 1),
                box(-CRANK_X - 1, -W_OUT, y - WEB_CUT, y + WEB_CUT, z, TOP + 1)]
    # gear rooms: a disc round each gear and a channel above it, open at the top (gears drop in from above)
    for y, z, r, hw in gears():
        n = 192 if (y, z) == tuple(IDL[2][:2]) else 48   # idler 3: chords within 0.001 of GEAR_TIP (48: 0.013)
        cut += [prisms(pocket(y, z, r + GEAR_ROOM, n), -hw, hw),
                box(-hw, hw, y - r - GEAR_ROOM, y + r + GEAR_ROOM, z, TOP + 1)]
    # journal holes and slots through both walls, with a lead-in at the top
    for y, z in SH:
        cut += [cylx(y, z, J_HOLE / 2, -CRANK_X, CRANK_X), box(-CRANK_X, CRANK_X, y - J_HOLE / 2, y + J_HOLE / 2,
                                                                z, TOP + 1)]
        cut += [Pos(CX, y, TOP) * Rot(45, 0, 0) * Box(2 * CRANK_X, (J_HOLE / 2 + LEAD) * np.sqrt(2) - 0.0,
                                                       (J_HOLE / 2 + LEAD) * np.sqrt(2))]
    # idler pins: Ø3.3 from the +X recess to the blind -X end, push-out hole through
    for y, z, _ in IDL:
        cut += [cylx(y, z, PIN_HOLE / 2, PIN_X0, W_THICK + 1), cylx(y, z, PUSH_HOLE / 2, -W_THICK_MX - 1, PIN_X0 + 0.1)]
    # pinion zone: nothing still within PIN_R of the pinion's axis inside |x| < PZ_X, and open above (it drops in)
    pr, px = PIN_R + TESS, PZ_X + TESS
    cut += [cylx(YM, ZM, pr, -px, px), box(-px, px, YM - pr, YM + pr, ZM, TOP + 1)]
    # -X wall: U-slot for the spinning shaft tip, open at the top
    cut += [cylx(YM, ZM, SHAFT_SLOT, -W_THICK - 1, -PZ_X + 0.01),
            box(-W_THICK - 1, -PZ_X + 0.01, YM - SHAFT_SLOT, YM + SHAFT_SLOT, ZM, TOP + 1)]
    # +X wall: the gearbox drops onto the pad (wall top at PAD_Z) between two steps that locate it in Y (MOTOR_SEAT)
    cut += [box(PZ_X - 0.01, W_THICK + 1, YM - R.N20_W / 2 - WIN, YM + R.N20_W / 2 + WIN, PAD_Z, TOP + 1)]
    # saddle: a 90° V under the gearbox (clear) and under the can (it rests on the V's flanks), then the can's stop
    for x0, x1, zv in ((W_THICK - 0.02, GB_X1, V_GB), (GB_X1, STOP_X, V_CAN)):
        h = 20.0
        cut += [prism_yz([(YM, zv), (YM + h, zv + h * _TAN), (YM - h, zv + h * _TAN)], x0, x1)]
    # keeper recess in the +X wall face (LOCATOR round the keeper)
    cut += [box(PIN_X1, W_THICK + 1, KEEPER_Y[0] - LOC, KEEPER_Y[1] + LOC, KEEPER_Z[0] - LOC, KEEPER_Z[1] + 1),
            box(PIN_X1, W_THICK + 1, KEEPER_SCREW[0] - 3.5 - LOC, KEEPER_SCREW[0] + 3.5 + LOC, KEEPER_TAB[0] - LOC,
                KEEPER_Z[0])]
    # keeper screw: hole from the recess, nut between the walls slid in from below
    ky, kz = KEEPER_SCREW
    cut += [cylx(ky, kz, SCREW_HOLE / 2, PIN_X1 - KEEPER_SCREW_L - 1, W_THICK + 1)]
    kx0 = PIN_X1 + KEEPER_T - KEEPER_SCREW_L + 0.5        # nut's -X face: the screw tip 0.5 past it
    cut += [Pos(CX + kx0, ky, kz) * Rot(0, 90, 0) * K.hexagon(NUT_AF, NUT_T, (1, 0)),   # corners along Z
            box(kx0, kx0 + NUT_T, ky - NUT_AF / 2, ky + NUT_AF / 2, KEEL_Z - 1, kz)]
    # cap screws: front (end block) and shared (-X boss); nuts slid in from -X
    for (sx, sy), zt in ((SCREW_FRONT, TOP + CAP_T), (SCREW_SHARED, TOP + CAP_T + CLAMP_T)):
        tip = zt - CAP_SCREW_L
        cut += [cylz(sx, sy, SCREW_HOLE / 2, tip - 0.5, TOP + 1), nut_pocket(sx, sy, tip + 0.5, (-1, 0)),
                lead_in(sx, sy, SCREW_HOLE / 2, TOP)]
    # clamp's rear screw in the end wall, nut slid in from +X
    tip = TOP + CAP_T + CLAMP_T - CAP_SCREW_L
    cut += [cylz(SCREW_CLAMP_X, YM, SCREW_HOLE / 2, tip - 0.5, TOP + 1),
            nut_pocket(SCREW_CLAMP_X, YM, tip + 0.5, (1, 0)), lead_in(SCREW_CLAMP_X, YM, SCREW_HOLE / 2, TOP)]
    # I7: 4 nut traps for M3×10 from below through the chassis (nuts slid in from the side)
    for nx, ny, nz, out in I7_NUTS:
        tip = I7_TIP_V if nx == I7_NUTS[1][0] else I7_TIP
        cut += [cylz(nx, ny, SCREW_HOLE / 2, nz - 20, nz + NUT_T + tip), nut_pocket(nx, ny, nz, out)]
    for c in cut:
        part -= c
    # marks: crank numbers (dice dots) beside each slot on the +X wall's face, and a FRONT arrow on the front block
    for i, (y, z) in enumerate(SH):
        part -= K.marks(i + 1, CX + W_OUT, y - J_HOLE / 2 - 2.2, TOP - 3.0)      # in the webs' channel: x W_OUT
    part -= arrow(W_OUT, (Y0 + SH[0][0] - C.KEEP_GAP) / 2, 66.0)
    # motor polarity on the end wall's +X face: «+» on the +Y side (red wire), «-» on the -Y side; wires leave on +Y
    zc, d = 68.0, K.MARK_DEPTH            # below the clamp nut's slot (z 71.35-74.05) on the same face
    for sy in (1, -1):
        yc = YM + sy * 2.5
        part -= box(END_X1 - d, END_X1 + 1, yc - 1.5, yc + 1.5, zc - 0.3, zc + 0.3)
        if sy > 0:
            part -= box(END_X1 - d, END_X1 + 1, yc - 0.3, yc + 0.3, zc - 1.5, zc + 1.5)
    return part


def arrow(xf, yc, zc, depth=0.5):
    """FRONT arrow (pointing -Y) sunk into the face at x = xf (from CX), outward normal +X."""
    tri = Polygon(*[(yc - 3.0, zc), (yc, zc + 2.2), (yc, zc - 2.2)], align=None)
    head = Pos(CX + xf - depth, 0, 0) * extrude(Plane.YZ * tri, amount=depth + 1, dir=(1, 0, 0))
    stem = box(xf - depth, xf + 1, yc - 0.01, yc + 3.0, zc - 0.7, zc + 0.7)
    return head + stem


# ---- cap ----------------------------------------------------------------------------------------------------------
def cap():
    z0, z1 = TOP, TOP + CAP_T
    part = box(-CAP_W, CAP_W, CAP_Y0, CAP_Y1, z0, z1)
    part += box(BOSS_X[0], -CAP_W + 0.01, BOSS_Y[0], BOSS_Y[1], z0, z1)           # -X bridge over the boss
    for y, z in SH:                                                                # tongues, flat ends
        zb = z + J_HOLE / 2
        for sx in (1, -1):
            x0, x1 = sorted((sx * C.TONGUE_IN, sx * C.TONGUE_OUT))
            part += box(x0, x1, y - TONGUE_W / 2, y + TONGUE_W / 2, zb, z0 + 0.01)
    xs = W_OUT + LOC                                                               # front skirts (X locator)
    for sx in (1, -1):
        x0, x1 = sorted((sx * xs, sx * (xs + SKIRT_T)))
        sk = box(x0, x1, CAP_Y0, SKIRT_Y1, z0 - SKIRT_H, z0 + 0.01)
        c = 0.4 * np.sqrt(2)
        sk -= Pos(CX + sx * xs, (CAP_Y0 + SKIRT_Y1) / 2, z0 - SKIRT_H) * Rot(0, 45, 0) * Box(c, 40, c)
        part += sk
    # windows: pinion zone, shaft tip, motor (all drop in from above after the cap)
    part -= box(-PZ_X - CAP_PLAY, PZ_X + CAP_PLAY, YM - PIN_R, YM + PIN_R, z0 - 1, z1 + 1)
    part -= box(SHAFT_X0 - GAX, -PZ_X + 0.01, YM - R.N20_SHAFT_D / 2 - WIN, YM + R.N20_SHAFT_D / 2 + WIN, z0 - 1,
                z1 + 1)
    cw = R.N20_W / 2 + SEAT + CHEEK_T + WIN            # round the clamp's cheeks
    part -= box(PZ_X - 0.01, CAP_W + 1, YM - cw, YM + cw, z0 - 1, z1 + 1)
    for sx, sy in (SCREW_FRONT, SCREW_SHARED):
        part -= cylz(sx, sy, CAP_HOLE / 2, z0 - 1, z1 + 1)
    for y, _ in SH:                                         # +X edge dots: the cap's right side (test cap v2.1)
        part -= K.marks(1, CX + CAP_W, y, z0 + CAP_T / 2)
    return part


# ---- motor clamp ---------------------------------------------------------------------------------------------------
def motor_clamp():
    y0, y1 = YM - CLAMP_W / 2, YM + CLAMP_W / 2
    x0 = SCREW_SHARED[0] - CLAMP_W / 2
    part = box(x0, END_X1, y0, y1, CLAMP_Z0, CLAMP_Z0 + CLAMP_T)
    part += box(END_X0, END_X1, y0, y1, TOP, CLAMP_Z0 + 0.01)                       # rear foot on the end wall
    zp = MOTOR_TOP + fits.MOTOR_PRELOAD.side          # pad 0.3 into the gearbox: the bar is the spring (≈ 9 N)
    part += box(GB_X0 + GAX, GB_X1, y0, y1, zp, CLAMP_Z0 + 0.01)                     # pad on the gearbox
    yc = R.N20_W / 2 + SEAT                            # cheeks down the gearbox flats: they take the motor torque
    for sy in (1, -1):
        a, b = sorted((YM + sy * yc, YM + sy * (yc + CHEEK_T)))
        part += box(GB_X0 + GAX, GB_X1, a, b, MOTOR_TOP - CHEEK_H, CLAMP_Z0 + 0.01)
    part += box(GB_X0 + GAX, GB_X1, YM - yc - CHEEK_T, YM + yc + CHEEK_T, CLAMP_Z0, CLAMP_Z0 + CLAMP_T)
    can = box(GB_X1 + 0.5, CAN_X1 - 0.5, y0, y1, ZM, CLAMP_Z0 + 0.01) - cylx(YM, ZM, MR + SEAT, GB_X1, CAN_X1)
    part += can                                                                     # arc pad on the can
    for x in (SCREW_SHARED[0], SCREW_CLAMP_X):
        part -= cylz(x, YM, SCREW_HOLE / 2, TOP - 1, CLAMP_Z0 + CLAMP_T + 1)
    part -= box(-PINION_RELIEF[0], PINION_RELIEF[0], y0 - 1, y1 + 1, CLAMP_Z0 - 1, CLAMP_Z0 + PINION_RELIEF[1])
    return part


# ---- pinion and idler 3 v2 --------------------------------------------------------------------------------------------
def flat_gear(teeth, face, bore):
    """Gear printed flat (z 0..face) with the first 0.2 mm layer 0.2 smaller (elephant's foot), minus the bore."""
    import shapely.geometry as sg
    fl = fits.FIRST_LAYER
    small = sg.polygon.orient(sg.Polygon(C.gear_profile(teeth)).buffer(-fl, join_style=2), 1.0)
    g = extrude(Polygon(*list(small.exterior.coords)[:-1], align=None), amount=0.2)          # one 0.2 layer
    g += Pos(0, 0, 0.2) * extrude(Polygon(*C.gear_profile(teeth), align=None), amount=face - 0.2)
    return g - bore


def dot(x, y, z):
    from build123d import Sphere
    return Pos(x, y, z + K.MARK_D / 2 + 0.1 - K.MARK_DEPTH) * Sphere(K.MARK_D / 2 + 0.1)


def pinion():
    """12 T, module 1, 5 mm, D-bore at the shaft's size + DSHAFT (pressed on), in its own frame: axis Z, the face
    at z 0 goes to -X (the shaft enters there: 0.5 mm lead-in). The flat of the D faces +Y here (= +Z in place at
    angle 0, R.n20_shaft()); a dot on the top face over the flat."""
    d = R.d_profile(R.N20_SHAFT_D + 2 * fits.DSHAFT.side, R.N20_SHAFT_FLAT)
    bore = Pos(0, 0, -1) * extrude(Polygon(*[tuple(p) for p in d], align=None), amount=R.PINION_FACE + 2)
    for z, (r0, r1) in ((-0.01, (R.N20_SHAFT_D / 2 + LEAD, R.N20_SHAFT_D / 2)),          # both mouths: the shaft
                        (R.PINION_FACE - LEAD, (R.N20_SHAFT_D / 2, R.N20_SHAFT_D / 2 + LEAD))):  # enters at +X
        bore += Pos(0, 0, z) * Cone(r0, r1, LEAD + 0.01, align=None)
    g = flat_gear(R.PINION_TEETH, R.PINION_FACE, bore)
    return g - dot(0, 3.4, R.PINION_FACE)


def idler_3_v2():
    """Idler 3 with a 5 mm face (same 20 teeth; same phase in place); a dot on the top face on tooth 0's line."""
    n = IDL[2][2]
    bore = Cylinder(PIN_HOLE / 2, 30) + Pos(0, 0, -0.01) * Cone(PIN_HOLE / 2 + 0.4, PIN_HOLE / 2, 0.41, align=None)
    g = flat_gear(n, R.IDLER3_FACE, bore)
    rr = C.MOD * (n / 2 - 1.25) - 1.2
    return g - dot(rr, 0, R.IDLER3_FACE)


# ---- pin keeper ------------------------------------------------------------------------------------------------------
def pin_keeper():
    part = box(PIN_X1, PIN_X1 + KEEPER_T, KEEPER_Y[0], KEEPER_Y[1], KEEPER_Z[0], KEEPER_Z[1])
    part += box(PIN_X1, PIN_X1 + KEEPER_T, KEEPER_SCREW[0] - 3.5, KEEPER_SCREW[0] + 3.5, KEEPER_TAB[0],
                KEEPER_Z[0] + 0.01)
    part -= cylx(KEEPER_SCREW[0], KEEPER_SCREW[1], SCREW_HOLE / 2, PIN_X1 - 1, PIN_X1 + KEEPER_T + 1)
    return part


# ---- bench tools ----------------------------------------------------------------------------------------------------
def gauge_fork():
    """0.8 mm plate (printed flat: 4 layers) with a U-slot over the shaft, open at -Z, 0.5 lead-ins at the mouth;
    a hole in the handle above."""
    x0, x1 = FORK_X
    part = box(x0, x1, YM - FORK_HW, YM + FORK_HW, FORK_Z[0], FORK_Z[1])
    part -= cylx(YM, ZM, FORK_SLOT, x0 - 1, x1 + 1) + box(x0 - 1, x1 + 1, YM - FORK_SLOT, YM + FORK_SLOT,
                                                            FORK_Z[0] - 1, ZM)
    m = LEAD
    part -= prism_yz([(YM - FORK_SLOT - m, FORK_Z[0] - 0.01), (YM + FORK_SLOT + m, FORK_Z[0] - 0.01),
                      (YM + FORK_SLOT, FORK_Z[0] + m), (YM - FORK_SLOT, FORK_Z[0] + m)], x0 - 1, x1 + 1)
    part -= cylx(YM, FORK_Z[1] - 4.0, 2.0, x0 - 1, x1 + 1)          # hole in the handle: hang it with the kit
    return part


def prism_xy(pts, z0, z1):
    """Prism of an (x from CX, y) outline from z0 to z1."""
    return Pos(CX, 0, z0) * extrude(Polygon(*pts, align=None), amount=z1 - z0)


def press_jig():
    """U-channel open at +Z, used with its -X face on the table: pinion pocket (its floor at the pinion's -X face,
    x -2.5), the fork's slot over it, the gearbox socket above. Printed on its -Z face, the open side up: every
    pocket, slot and hole is open upwards (no overhang). 0.5 lead-ins on the socket's and the channel's mouths."""
    x0 = -R.PINION_FACE / 2 - JIG_BACK
    zt = ZM + JIG_HW
    part = box(x0, JIG_TOP, YM - JIG_HW, YM + JIG_HW, ZM - JIG_HW, zt)
    sy, sz = JIG_SOCKET
    px1 = FORK_X[0] + LOC                          # pocket up to 0.2 over the pinion's +X face
    part -= cylx(YM, ZM, JIG_POCKET, -R.PINION_FACE / 2, px1) + \
        box(-R.PINION_FACE / 2, px1, YM - JIG_POCKET, YM + JIG_POCKET, ZM, zt + 1)
    a, b, w = JIG_SLOT
    part -= box(a, b, YM - w, YM + w, JIG_SLOT_Z0, zt + 1)
    part -= box(b - 0.01, JIG_TOP + 1, YM - sy, YM + sy, ZM - sz, zt + 1)
    m = LEAD
    for s in (-1, 1):                              # socket mouth: lead-ins on its Y faces and its -Z face
        part -= prism_xy([(JIG_TOP - m, YM + s * sy), (JIG_TOP + 0.01, YM + s * (sy + m + 0.01)),
                          (JIG_TOP + 0.01, YM + s * sy)], ZM - sz - m, zt + 1)
    part -= Pos(CX, YM, 0) * extrude(Plane.XZ * Polygon((JIG_TOP - m, ZM - sz), (JIG_TOP + 0.01, ZM - sz - m - 0.01),
                                                        (JIG_TOP + 0.01, ZM - sz), align=None), amount=sy + m,
                                     both=True)
    for s in (-1, 1):                              # channel's +Z mouth: lead-ins on the pocket's, slot's, socket's sides
        for y, xa, xb in ((JIG_POCKET, -R.PINION_FACE / 2, px1), (w, a, b), (sy, b, JIG_TOP)):
            part -= prism_yz([(YM + s * y, zt - m), (YM + s * (y + m + 0.01), zt + 0.01), (YM + s * y, zt + 0.01)],
                             xa, xb)
    part -= cylx(YM, ZM, JIG_HOLE, x0 - 1, -R.PINION_FACE / 2 + 0.01) + \
        box(x0 - 1, -R.PINION_FACE / 2 + 0.01, YM - JIG_HOLE, YM + JIG_HOLE, ZM, zt + 1)   # a U, open upwards
    return part


def press_cup():
    """Cup over the can's rear end: skirt (can section + MOTOR_SEAT a side), the terminals' relief open at +Z (the
    wires leave there), a 2 mm top plate the vise jaw presses. Bears on the can's rear face beside and below the
    terminal block. Printed top plate down (no support)."""
    sy, sz = JIG_SOCKET                            # the can's section is the gearbox's: 10 × Ø12
    x0, x1 = CAN_X1 - CUP_SKIRT, TERM_X1 + WIN
    part = box(x0, x1 + CUP_T, YM - sy - CUP_WALL, YM + sy + CUP_WALL, ZM - sz - CUP_WALL, ZM + sz + CUP_WALL)
    part -= box(x0 - 1, CAN_X1, YM - sy, YM + sy, ZM - sz - 1, ZM + sz + 1) & cylx(YM, ZM, sz, x0 - 1, CAN_X1)
    tw = R.N20_TERM_W / 2 + WIN
    part -= box(x0 - 1, x1, YM - tw, YM + tw, ZM + R.N20_TERM_Z[0] - WIN, ZM + sz + CUP_WALL + 1)
    part -= (Pos(CX + x0 + LEAD, YM, ZM) * Rot(0, -90, 0) * Cone(sz, sz + LEAD + 0.01, LEAD + 0.01, align=None)) & \
        box(x0 - 1, x0 + LEAD + 0.01, YM - sy - LEAD, YM + sy + LEAD, ZM - sz - LEAD, ZM + sz + LEAD)
    return part


PARTS = {"drive-module": drive_module, "cap": cap, "motor-clamp": motor_clamp, "pinion": pinion,
         "idler-3-v2": idler_3_v2, "pin-keeper": pin_keeper, "gauge-fork": gauge_fork, "press-jig": press_jig,
         "press-cup": press_cup}


def main():
    args = K.part_args(__doc__, PARTS)
    K.build_parts(PARTS, args.part or PARTS, OUT)


if __name__ == "__main__":
    main()
