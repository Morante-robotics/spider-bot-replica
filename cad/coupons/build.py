#!/usr/bin/env python3
"""Coupons for the S 1.0 robot (phase 3, local): every fit that is `assumed` in fits.py or never printed, cut from the
real constants of cad/robot (drive.py, shells.py) and cad/fits.py. One fit per coupon, 2-3 steps, step numbers
engraved (or edge notches where a face is too thin), flat, no support. Print table: README.md here / the report.

  c1-leg-snap     leg snap: crank pin groove + end-tube bead and slit (fits.PRESS), 3 bead radii
  c2-motor-seat   N10 in its U (fits.MOTOR_SEAT), 3 seats + a printed 12x10 stand-in
  c3-gear-tip     module-1.0 10T pair at the real centre distance in a pocket (fits.GEAR_TIP), 3 pockets
  c4-pilots       M3 self-tapping pilots at the real depths, 3 diameters (drive.M3_PILOT_R)
  c5-seats        ISO 7380 button-head seat hole and socket-head counterbore on the bed (STEEL, FIRST_LAYER)
  c6-marks        engraved numbers 1-4 at the real size, 3 depths (drive.MARK_DEPTH)
  c7-leg-turn     leg end tube turning on the crank pin (fits.TURN), 3 bores
  c8-neighbour    two parts side by side, 3 gaps (fits.NEIGHBOUR)
  c9-leg-window   leg neck in an open-top window, 3 widths (fits.LEG_OPEN / LEG_PATH)
  c10-dshaft      pinion D-bore on the motor's D-shaft (fits.DSHAFT), 3 bores
  c11-snap        body <-> base front snap: finger + hook on the base's rib (fits.PRESS), 3 rib depths
  c12-cell-lid    cell lid lip bump in the holder's groove (power.py, fits.PRESS), 3 bump heights

Frame: each part in its print position, z = 0 is the bed.
    ../../.venv/bin/python build.py [--part c1-leg-snap] [--fine]
"""
import os
import sys
import math

from build123d import Box, Cylinder, Pos, Rot, Plane, Polygon, extrude, Align, Compound, Axis, Text, FontStyle

HERE = os.path.dirname(os.path.abspath(__file__))
ROBOT = os.path.join(HERE, "..", "robot")
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, ROBOT)
import timebudget  # noqa: E402
from cad import common, fits as F  # noqa: E402
import shells as SH  # noqa: E402   (the robot's numbers: read, never copied)
import drive as D  # noqa: E402

OUT = os.path.join(HERE, "out")

# ---- numbers: every one imported or derived from the robot's code
W = F.WALL_MIN                         # walls
M3_HOLE_R, M3_PILOT_R, IPR = D.M3_HOLE_R, D.M3_PILOT_R, D.IPR
LABEL_FS, LABEL_DEPTH = D.MARK_FS, D.MARK_DEPTH       # engraved number: the robot's 3 mm digit, 0.5 deep
STEP_TXT = "123"

# c1 / c7: the crank pin and the leg's end tube (shells.py: groove, bead, slit; drive.crank: the pin)
PINR, WB1 = D.PINR, D.WB1
PIN_LEN = SH.PIN_X1 - WB1                              # pin from the web face to its tip
GX0, GX1 = SH.snap_groove(0)                           # groove span in robot |x| (leg 0 / crank 1)
FLOOR_X = SH.PIN_X1 + SH.PIN_TRIM                      # tube bore floor (the pin tip stands PIN_TRIM short of it)
MOUTH_ABOVE_WEB = 1.0                                  # tube mouth this far over the web face when pushed home
BORE_DEPTH = FLOOR_X - (WB1 + MOUTH_ABOVE_WEB)
BEAD_Z = BORE_DEPTH - (FLOOR_X - 0.5 * (GX0 + GX1))    # bead centre: on the groove centre when the pin tip is PIN_TRIM from the floor
BORE_R = SH.BORE_R[0]                                  # leg 0's designed bore (tilted-pin ellipse)
BEAD_STEPS = [SH.SNAP_NECK_R + F.TURN.side,            # 1: neck + TURN, pin not tilted
              SH.snap_bead_r(0), SH.snap_bead_r(3)]    # 2: leg 0/4's tilted ring (the robot's value), 3: leg 3/7's (widest tilt)
TURN_STEPS = [F.TURN.side - 0.10, F.TURN.side, F.TURN.side + 0.10]

PLATE_T = 2.0


def box(x0, y0, z0, x1, y1, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cylz(x, y, r, z0, z1):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def cylx(y, z, r, x0, x1):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def digits(txt, x, y, ztop, depth=LABEL_DEPTH, fs=LABEL_FS):
    """cutter of an engraved number on a face with normal +z at height ztop (read from above), centred at x, y."""
    t = Text(txt, fs, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    t = extrude(t.faces(), depth + 0.5)
    return Pos(x, y, ztop - depth) * t


def bottom_digits(txt, x, y, depth=LABEL_DEPTH, fs=LABEL_FS):
    """cutter of an engraved number on the bed face (read from below, mirrored as the face is seen from below)."""
    t = Text(txt, fs, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    t = extrude(t.faces(), depth + 0.5)
    return Pos(x, y, depth) * Rot(180, 0, 0) * t


def compound(*solids):
    return Compound(children=list(solids))


# ---------------------------------------------------------------- c1 / c7: crank pin and end tube
# Printed as the plater prints the robot's legs and cranks: the pin and the tube axis HORIZONTAL (print +x), the tube on a flat
# foot (a block under the tube, as wide as the tube, so the wall stays WALL_MIN round the bore), slit up, no support in the bore.
# Built standing along z (as before), then turned: standing (x, y, z) -> print (y, z, x).
def _lay(shape, y, z):
    """standing solid -> lying along print x; its standing origin goes to print (0, y, z)."""
    return Pos(0, y, z) * (Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * shape)


WEB_HW = 6.0                                           # pin web half-width (print y)
TUBE_R_OUT = PINR + max(TURN_STEPS) + W                # widest tube's outer r (pitch of the row)
TUBE_Y0 = WEB_HW + 1.5 + TUBE_R_OUT                    # first tube's axis (print y)
TUBE_PITCH = 2 * TUBE_R_OUT + 1.5


def _pin():
    """the real crank pin (drive.crank): Ø(2 PINR) with the snap groove (neck SNAP_NECK_R), lying along print x from a web."""
    pin = cylz(0, 0, PINR, PLATE_T - 0.01, PLATE_T + PIN_LEN)
    g0, g1 = PLATE_T + GX0 - WB1, PLATE_T + GX1 - WB1
    pin = pin - (cylz(0, 0, PINR + 0.5, g0, g1) - cylz(0, 0, SH.SNAP_NECK_R, g0 - 0.01, g1 + 0.01))
    web = box(-WEB_HW, -PINR, 0, WEB_HW, PINR + 3.0, PLATE_T)          # standing on its edge; the pin's axis PINR over the bed
    return _lay(web + pin, 0, PINR)


def _tube(bore_r, rb, slit, label):
    """end tube, standing open end down (then lain by _lay): bore, closed end SNAP_WALL thick, wall WALL_MIN; with rb: the bead,
    the slit (+y = up when printed) and its 45 deg chamfers (SLIT_CHAMFER, as the leg). The foot (y < 0) is the flat it lies on."""
    r_out = bore_r + W
    length = BORE_DEPTH + SH.SNAP_WALL
    tube = cylz(0, 0, r_out, 0, length) + box(-r_out, -r_out, 0, r_out, 0, length)
    bore = cylz(0, 0, bore_r, -0.01, BORE_DEPTH)
    if rb is not None:
        ring = cylz(0, 0, bore_r + 0.4, BEAD_Z - SH.SNAP_BW / 2, BEAD_Z + SH.SNAP_BW / 2) - \
            cylz(0, 0, rb, BEAD_Z - SH.SNAP_BW / 2 - 0.01, BEAD_Z + SH.SNAP_BW / 2 + 0.01)
        bore = bore - ring
    tube = tube - bore
    if slit:
        zs1 = BORE_DEPTH + SH.SLIT_END
        tube = tube - box(-SH.SNAP_SLIT / 2, 0, -0.01, SH.SNAP_SLIT / 2, r_out + 1, zs1)
        h, c = SH.SNAP_SLIT / 2, SH.SLIT_CHAMFER
        ye = math.sqrt(r_out ** 2 - h ** 2)
        vee = Plane(origin=(0, 0, -0.01), x_dir=(1, 0, 0), z_dir=(0, 0, 1)) * Polygon(
            (-h - c, ye + 1.0), (-h - c, ye - 0.0 + 0.0), (-h, ye - c), (h, ye - c), (h + c, ye), (h + c, ye + 1.0), align=None)
        tube = tube - extrude(vee, amount=zs1 + 0.01)
    return tube - digits(label, 0, 0, length)


def _tube_row(specs):
    return [_lay(_tube(*sp, str(i + 1)), TUBE_Y0 + i * TUBE_PITCH, sp[0] + W) for i, sp in enumerate(specs)]


def c1_leg_snap():
    return compound(_pin(), *_tube_row([(BORE_R, rb, True) for rb in BEAD_STEPS]))


def c7_leg_turn():
    return compound(_pin(), *_tube_row([(PINR + s, None, False) for s in TURN_STEPS]))


# ---------------------------------------------------------------- c2: N10 in its U
MOTOR_STEPS = [F.MOTOR_SEAT.side - 0.10, F.MOTOR_SEAT.side, F.MOTOR_SEAT.side + 0.10]
U_LEN = 8.0                                            # channel length (printed standing: the robot's U rises along +x)


def _u(s, label):
    w, h = D.N10_W + 2 * s, D.N10_H + 2 * s
    ow, oh = w + 2 * D.DU_W, h + D.DU_W
    u = box(-ow / 2, 0, 0, ow / 2, oh, U_LEN) - box(-w / 2, D.DU_W, -0.01, w / 2, oh + 0.01, U_LEN + 0.01)
    t = Text(label, LABEL_FS, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    t = extrude(t.faces(), LABEL_DEPTH + 0.5)               # engraved on the floor's outer face (normal -y)
    return u - Pos(0, LABEL_DEPTH, U_LEN / 2) * Rot(90, 0, 0) * t


def c2_motor_seat():
    parts, x = [], 0.0
    for i, s in enumerate(MOTOR_STEPS):
        ow = D.N10_W + 2 * s + 2 * D.DU_W
        parts.append(Pos(x + ow / 2, 0, 0) * _u(s, str(i + 1)))
        x += ow + 4
    parts.append(box(x, 0, 0, x + D.N10_W, D.N10_H, U_LEN))       # stand-in at the motor's catalogue section (the real one is to be measured)
    return compound(*parts)


# ---------------------------------------------------------------- c3: gear pair in its pocket
GEAR_N = D.ZT
GEAR_CC = D.cc(D.ZT, D.ZI[0])                          # crank gear <-> idler 1 centre distance with backlash
TIP_STEPS = [0.25, F.GEAR_TIP.side, 0.50]              # 0.25 = the bare minimum the fit derives (datasheet), 0.5 = chassis rev 4 (before)
TIP_PITCH = 2 * (D.rt(GEAR_N) + max(TIP_STEPS) + W) + 1.5
PLATE3_T = 3.0


def _gear_solid(teeth, phase, cx, cy, z0, h, bore_r):
    c, s = math.cos(phase), math.sin(phase)
    pts = [(cx + u * c - v * s, cy + u * s + v * c) for u, v in D.gear_profile(teeth)]
    g = extrude(Plane(origin=(0, 0, z0)) * Polygon(*pts, align=None), amount=h)
    return g - cylz(cx, cy, bore_r, z0 - 0.01, z0 + h + 0.01)


def c3_gear_tip():
    ph_b = D._mate(GEAR_N, (0, 0), 0.0, GEAR_N, (GEAR_CC, 0))
    r_in = lambda s: D.rt(GEAR_N) + s
    x0, x1 = -(r_in(max(TIP_STEPS)) + W + 3.5), GEAR_CC + r_in(max(TIP_STEPS)) + W
    y1 = (len(TIP_STEPS) - 1) * TIP_PITCH + r_in(max(TIP_STEPS)) + W
    plate = box(x0, -(r_in(max(TIP_STEPS)) + W), 0, x1, y1, PLATE3_T)
    walls, cavs = [], []
    for k, s in enumerate(TIP_STEPS):
        y = k * TIP_PITCH
        for cx in (0.0, GEAR_CC):
            walls.append(cylz(cx, y, r_in(s) + W, PLATE3_T - 0.01, PLATE3_T + D.GW))
            cavs.append(cylz(cx, y, r_in(s), PLATE3_T, PLATE3_T + D.GW + 0.1))
            plate = plate - cylz(cx, y, M3_PILOT_R, PLATE3_T - 2.5, PLATE3_T + 0.01)
        plate = plate - digits(str(k + 1), x0 + 1.75, y, PLATE3_T)
    body = plate
    for wl in walls:
        body = body + wl
    for cv in cavs:
        body = body - cv
    for k in range(len(TIP_STEPS)):                                       # (pilots again: the walls closed the cavities' floors above them)
        for cx in (0.0, GEAR_CC):
            body = body - cylz(cx, k * TIP_PITCH, M3_PILOT_R, PLATE3_T - 2.5, PLATE3_T + 0.01)
    gx = x1 + 3 + D.rt(GEAR_N)
    ga = _gear_solid(GEAR_N, 0.0, gx, 0, 0, D.GW, IPR + F.STEEL.side)
    gb = _gear_solid(GEAR_N, ph_b, gx + 2 * D.rt(GEAR_N) + 2, 0, 0, D.GW, IPR + F.STEEL.side)
    return compound(body, ga, gb)


# ---------------------------------------------------------------- c4: M3 pilots
PILOT_R_STEPS = [M3_PILOT_R - 0.05, M3_PILOT_R, M3_PILOT_R + 0.05]
DEPTH_KEEL = D.KEEL_LEN - D.KEEL_BOSS_T + D.KEEL_PILOT_OVER      # keel M3 x 5: 3 in the pilot + 0.2 over the tip
DEPTH_TP = 4.0                                                    # transfer-pin M3 x 16: 4.0 of thread in the web + boss (drive.TP_L comment)
PITCH4 = 7.0


def c4_pilots():
    floor = W
    h = max(DEPTH_KEEL, DEPTH_TP) + floor
    blk = box(-PITCH4 * 1.5, -PITCH4 * 1.5, 0, PITCH4 * 1.5, PITCH4 * 1.5, h)
    for j, r in enumerate(PILOT_R_STEPS):
        x = (j - 1) * PITCH4
        blk = blk - cylz(x, PITCH4, r, h - DEPTH_KEEL, h + 0.01) - cylz(x, 0, r, h - DEPTH_TP, h + 0.01)
        blk = blk - digits(str(j + 1), x, -PITCH4, h)
    # axle pilots: through the spine wall (WALL_MIN thick), printed on edge so the hole is horizontal like the spine's
    wall = box(PITCH4 * 2.4, -PITCH4 * 1.5, 0, PITCH4 * 2.4 + W, PITCH4 * 1.5, 11.0)
    for j, r in enumerate(PILOT_R_STEPS):
        wall = wall - Pos(PITCH4 * 2.4 + W / 2, (j - 1) * PITCH4, 6.0) * Rot(0, 90, 0) * Cylinder(r, W + 0.2)
    return compound(blk, wall)


# ---------------------------------------------------------------- c5: screw-head seats
SEAT_STEPS = [F.STEEL.side - 0.10, F.STEEL.side, F.STEEL.side + 0.10]        # added to the shank / head radius


def c5_seats():
    plate = box(0, -5, 0, 32, 5, W)                                    # button head: M3 hole through a WALL_MIN plate, head Ø5.7 bears on the face
    for j, s in enumerate(SEAT_STEPS):
        plate = plate - cylz(6 + 10 * j, 0, IPR + s, -0.01, W + 0.01)
    blk = box(0, 12, 0, 32, 24, D.M3_HEAD_H + D.KEEL_BOSS_T)           # socket head: counterbore opens on the bed, floor KEEL_BOSS_T
    for j, s in enumerate(SEAT_STEPS):
        x = 6 + 10 * j
        blk = blk - cylz(x, 18, D.M3_HEAD_R + s, -0.01, D.M3_HEAD_H) - cylz(x, 18, M3_HOLE_R, 0, D.M3_HEAD_H + D.KEEL_BOSS_T + 0.01)
    for j in range(3):
        plate = plate - digits(str(j + 1), 6 + 10 * j, 3.0, W, depth=0.4, fs=LABEL_FS * 0.5)
    return compound(plate, blk)


# ---------------------------------------------------------------- c6: engraved numbers
MARK_STEPS = [D.MARK_DEPTH - 0.2, D.MARK_DEPTH, D.MARK_DEPTH + 0.2]
TILE_T = max(MARK_STEPS) + W


def c6_marks():
    tiles = []
    for j, d in enumerate(MARK_STEPS):
        y = j * 11.0
        t = box(0, y, 0, 24, y + 9, TILE_T)
        for k in range(j + 1):                                          # step number: j+1 notches on the left edge
            t = t - box(-0.01, y + 1.5 + 2.2 * k, TILE_T - 1.0, 1.0, y + 2.7 + 2.2 * k, TILE_T + 0.01)
        t = t - digits("1234", 12.5, y + 4.5, TILE_T, depth=d)
        tiles.append(t)
    return compound(*tiles)


# ---------------------------------------------------------------- c8: neighbours
NEIGH_STEPS = [0.05, F.NEIGHBOUR.side, 0.15]


def c8_neighbour():
    out = []
    for j, g in enumerate(NEIGH_STEPS):
        y = j * 12.0
        a, b = box(0, y, 0, 10, y + 8, 4), box(10 + g, y, 0, 20 + g, y + 8, 4)
        out += [a - digits(str(j + 1), 5, y + 4, 4, depth=0.4), b]
    return compound(*out)


# ---------------------------------------------------------------- c9: open-top window
WIN_STEPS = [F.LEG_PATH.side - 0.10, F.LEG_PATH.side, F.LEG_PATH.side + 0.10]   # the robot's value (0.5) in the middle: a «0.5 rubs» result has a step above it
BAR_W = 2 * W                                                          # stand-in for the leg's neck: a 4 mm strip


def c9_leg_window():
    ws = [BAR_W + 2 * s for s in WIN_STEPS]
    x0, blk = 0.0, None
    x1 = sum(ws) + 4 * W
    blk = box(0, 0, 0, x1, 10 + 4.5, 5)
    x = W
    for j, w in enumerate(ws):
        blk = blk - box(x, -0.01, -0.01, x + w, 10, 5.01) - digits(str(j + 1), x + w / 2, 12.2, 5, depth=0.4, fs=LABEL_FS * 0.9)
        x += w + W
    bar = box(x1 + 4, 0, 0, x1 + 4 + BAR_W, 10 - 0.5, 5 - 0.5)
    return compound(blk, bar)


# ---------------------------------------------------------------- c10: pinion D-bore on the D-shaft
DSHAFT_STEPS = [-0.10, F.DSHAFT.side, 0.10]


def c10_dshaft():
    out = []
    for j, ds in enumerate(DSHAFT_STEPS):
        cx = j * (2 * D.rt(D.ZP) + 3)
        g = _gear_solid(D.ZP, 0.0, cx, 0, 0, D.GW, 0.1)
        r = D.SHAFT_R + F.DSHAFT.side + ds
        bore = cylz(cx, 0, r, -0.01, D.GW + 0.01) - box(cx - r - 1, r - D.SHAFT_FLAT, -0.02, cx + r + 1, r + 1, D.GW + 0.02)
        g = g - bore - digits(str(j + 1), cx, -D.rp(D.ZP) * 0.45, D.GW, depth=0.4, fs=LABEL_FS * 0.8)
        out.append(g)
    return compound(*out)


# ---------------------------------------------------------------- c11: body <-> base front snap (finger + hook on the base's rib)
# Section of shells.snap_geometry (u = robot y from the base wall's inner face yw = 0, v = robot z), extruded along x. Three ribs
# on a wall piece (rib depth RIBD -0.2 / 0 / +0.2) and ONE finger piece (finger + hook + root block, shells.finger_root), each
# printed on its broad face (finger: its back face on the bed, hook up; wall: outer face on the bed, rib up).
RIB_STEPS = [SH.RIBD - 0.2, SH.RIBD, SH.RIBD + 0.2]
RIB_W = SH.SNW + 1.0                                   # the rib's x span (snap_geometry: SNW + 2 x 0.5)
YF11 = SH.RIBD + SH.SNG                                # finger's wall-side face (robot RIBD, not the step's)
WALL_BELOW, WALL_ABOVE = 3.0, 5.0                      # wall piece: below the hook's foot SNZ / above it


def c11_snap():
    vh = WALL_BELOW + WALL_ABOVE
    pitch = RIB_W + 3.0
    wx = 3 * pitch + 2.0
    wall = box(-wx / 2, 0, 0, wx / 2, vh, SH.BASE_WALL)
    for j, d in enumerate(RIB_STEPS):
        cx = (j - 1) * pitch
        v0 = WALL_BELOW + 0.9                           # rib z SNZ + 0.9 .. + 1.9, rooted 0.6 in the wall
        wall = wall + box(cx - RIB_W / 2, v0, SH.BASE_WALL - 0.6, cx + RIB_W / 2, v0 + 1.0, SH.BASE_WALL + d)
        wall = wall - digits(str(j + 1), cx, 1.6, SH.BASE_WALL, depth=0.4, fs=LABEL_FS)
    fl = SH.FING_Z1 - SH.SNZ                            # finger piece length (print y): hook foot to the root block's end
    fw = SH.SNW
    t, fin_in = SH.SNT, SH.FING_IN
    fing = box(-fw / 2, 0, 0, fw / 2, SH.FING_Z0 + 0.3 - SH.SNZ, t)
    hook = box(-fw / 2, 0, t - 0.01, fw / 2, 0.8, t + YF11 - F.WINDOW.side)       # y = SNZ .. SNZ + 0.8, hangs toward the wall (print up)
    block = box(-fw / 2, SH.FING_Z0 - SH.SNZ, 0, fw / 2, fl, t + fin_in)           # the root block, embedded in the body's wall
    grip = box(-fw / 2 - 3.0, fl - 0.01, 0, fw / 2 + 3.0, fl + 8.0, t + fin_in)     # handle for the hand (not a robot feature)
    finger = fing + hook + block + grip
    return compound(wall, Pos(0, -fl - 6.0, 0) * finger)


# ---------------------------------------------------------------- c12: cell lid <-> cell-holder front wall (power.py lips)
import power as PW  # noqa: E402

LIP_STEPS = [PW.BUMP - 0.1, PW.BUMP, PW.BUMP + 0.1]    # bump proud of the lip: engagement 0.1 / 0.2 / 0.3 past the LOCATOR gap
WALL_V = PW.LIP_L + 4.0


def _prism_x(pts, x0, x1):
    """polygon in (print y, print z) extruded along x from x0 to x1."""
    # dir given: a clockwise polygon flips the face normal and the prism went to x0 - (x1 - x0) .. x0 (c12's bump stood
    # beside the lip, 2026-11-28)
    return extrude(Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * Polygon(*pts, align=None), amount=x1 - x0, dir=(1, 0, 0))


def _lid_piece(bump, label):
    lw = PW.LIP_W
    y0 = PW.W + F.LOCATOR.side                          # lip's wall-side face: over the wall + LOCATOR (the lid's plate overlies the wall)
    lt = PW.LIDT
    plate = box(-lw / 2 - 2.0, 0, 0, lw / 2 + 2.0, y0 + PW.LIP_T + 7.0, lt)
    lip = box(-lw / 2, y0, lt - 0.01, lw / 2, y0 + PW.LIP_T, lt + PW.LIP_L)
    zc = lt + PW.LIP_L - 0.4 - PW.BUMP_H / 2           # the bump's centre: 0.4 + half under the lip's tip (power.zc)
    hh, yo = PW.BUMP_H / 2, y0 + 0.1
    ridge = _prism_x([(yo, zc - hh), (y0, zc - hh), (y0 - bump, zc - hh + bump), (y0 - bump, zc + hh - bump), (y0, zc + hh), (yo, zc + hh)],
                     -lw / 2, lw / 2)
    return plate + lip + ridge - digits(label, 0, y0 + PW.LIP_T + 4.0, lt, depth=0.4)


def c12_cell_lid():
    lw = PW.LIP_W + 2 * F.LOCATOR.side
    wall = box(-lw / 2 - 4.0, 0, 0, lw / 2 + 4.0, WALL_V, PW.W)                      # the holder's front wall, inner face up
    zc = WALL_V - PW.LIP_L + 0.4 + PW.BUMP_H / 2
    g0, g1 = zc - PW.BUMP_H / 2 - F.LOCATOR.side, zc + PW.BUMP_H / 2 + F.LOCATOR.side
    wall = wall - box(-lw / 2, g0, PW.W - PW.GROOVE, lw / 2, g1, PW.W + 0.01)
    pw = PW.LIP_W + 4.0 + 3.0
    pieces = [wall] + [Pos(0, WALL_V + 4.0 + 0.0, 0) * Pos(0, 0, 0) * Pos((i - 1) * pw, 0, 0) * _lid_piece(b, str(i + 1)) for i, b in enumerate(LIP_STEPS)]
    return compound(*pieces)


PARTS = {"c1-leg-snap": c1_leg_snap, "c2-motor-seat": c2_motor_seat, "c3-gear-tip": c3_gear_tip, "c4-pilots": c4_pilots,
         "c5-seats": c5_seats, "c6-marks": c6_marks, "c7-leg-turn": c7_leg_turn, "c8-neighbour": c8_neighbour,
         "c9-leg-window": c9_leg_window, "c10-dshaft": c10_dshaft,
         "c11-snap": c11_snap, "c12-cell-lid": c12_cell_lid}


def main():
    args = common.part_args(__doc__, PARTS)
    for name in args.part or PARTS:
        timebudget.reset(name)
        with timebudget.stage(name):
            common.export(name, PARTS[name](), OUT, fine=args.fine)


if __name__ == "__main__":
    main()
