"""Coupons of the friction clutch (design-plan-clutch.md §4), cut from the same geometry as the robot's parts.

  coupon-cl1-stand  slice of the drive module round idler 3 and the gearbox pad (x -5.9..+12.3, y -5..+25.2):
                    the real pin hole, notch, pinion zone and pad. Holds idler 3 v2 on its Ø3 × 10 pin (pin keeper
                    and its M3×8 + nut) at the robot's centre distance (motor axis +0.1): the test rig of CL1
  coupon-cl1-arm    30 mm lever that slides over the pinion's teeth (LOCATOR a side): hang the weight at the hole
  coupon-cl2        option B, printed in place: 4 detent hubs in 4 tooth rings (arms 0.8 / 1.0 × bumps 0.25 / 0.4;
                    1-4 dots on each ring)
  coupon-cl3        option C: 3 pinions with two O-ring grooves (15 / 20 / 25 % squeeze on a 5 × 1 ring; 1-3 dots)
                    and one hub (the clutch sleeve)
  coupon-k1         3 sleeves with a 50 mm lever and 3 collars, D-bores DSHAFT -0.05 / 0 / +0.05 a side (1-3 dots)

CL1 itself is the real clutch (clutch-sleeve, pinion, wave washer, shims, clutch-collar) pressed on the motor in
the press jig. Each coupon is built in its own frame, flat side down on the bed.
"""
import numpy as np
from build123d import Box, Cylinder, Polygon, Pos, Rot, extrude

import build as B
from build import C, K, R, ZMIN, fits

DSHAFT_STEPS = (-0.05, 0.0, 0.05)       # K1: bores round DSHAFT (fits.py, assumed)
ARM_L = 30.0                            # CL1 lever: 30 mm (plan §4)
K1_ARM = 50.0                           # K1 lever: 440 g on 50 mm = 215 N·mm (plan §4)
CL2_VARIANTS = [(0.8, 0.25), (0.8, 0.4), (1.0, 0.25), (1.0, 0.4)]   # arm thickness, bump height (plan §3 B)
CL3_SQUEEZE = (0.15, 0.20, 0.25)        # O-ring 5 × 1 NBR squeeze (plan §4)
ORING_CS = 1.0
GROOVE_W = 1.3                          # 1.3 × the cross-section
TURN = fits.TURN.side


def dots(n, r, z):
    out = None
    for k in range(n):
        d = B.dot(r * np.cos(np.radians(90 + 25 * (k - (n - 1) / 2))), r * np.sin(np.radians(90 + 25 * (k - (n - 1) / 2))), z)
        out = d if out is None else out + d
    return out


def cl1_stand():
    """Module slice: everything the clutch and idler 3 touch, as in the robot (cut from drive_module())."""
    y0, y1 = B.KEEPER_BLOCK[0], B.YM + 13.0
    keep = B.box(-B.W_THICK_MX - 1, B.GB_X1, y0, y1, B.KEEL_Z - 1, B.TOP + 1)
    return B.drive_module() & keep


def cl1_arm():
    """Lever over the pinion's teeth (LOCATOR a side), 3 mm, hole Ø3 at 30 mm for the string."""
    import shapely.geometry as sg
    hole = sg.Polygon(C.gear_profile(R.PINION_TEETH)).buffer(fits.LOCATOR.side, join_style=2)
    t = 3.0
    part = Cylinder(10.0, t, align=ZMIN) + Pos(0, ARM_L / 2, t / 2) * Box(6.0, ARM_L + 6.0, t)
    part -= Pos(0, 0, -1) * extrude(Polygon(*list(hole.exterior.coords)[:-1], align=None), amount=t + 2)
    return part - Pos(0, ARM_L, -1) * Cylinder(1.6, t + 2, align=ZMIN)


def detent(arm_t, bump):
    """Option B: tooth ring (pinion, 4 mm, bore r 3.9, 6 notches) round a D-bore hub with 3 arms, printed in place
    with TURN all round (the bumps rest in their notches)."""
    face = R.PINION_FACE
    r_bore = 3.9
    r_out = r_bore - TURN
    r_in = r_out - arm_t
    bw = 0.6
    ring = B.flat_gear(R.PINION_TEETH, face, Pos(0, 0, -1) * Cylinder(r_bore, face + 2, align=ZMIN))
    hub = Cylinder(2.3, face, align=ZMIN) - B.d_bore(face)
    for k in range(3):
        a0 = np.radians(120 * k)
        span = np.radians(70)
        th = np.linspace(a0, a0 + span, 16)
        pts = [(r_out * np.cos(t), r_out * np.sin(t)) for t in th] + \
              [(r_in * np.cos(t), r_in * np.sin(t)) for t in th[::-1]]
        hub += extrude(Polygon(*pts, align=None), amount=face)
        hub += Pos(0, 0, face / 2) * Rot(0, 0, np.degrees(a0) + 4) * Pos((2.2 + r_in + 0.1) / 2, 0, 0) * \
            Box(r_in + 0.1 - 2.2, 0.9, face)
        rb = r_out + bump - bw
        bx, by = rb * np.cos(a0 + span), rb * np.sin(a0 + span)
        hub += Pos(bx, by, 0) * Cylinder(bw, face, align=ZMIN)
    for k in range(6):
        a = np.radians(70 + 60 * k)
        rb = r_out + bump - bw
        ring -= Pos(rb * np.cos(a), rb * np.sin(a), -1) * Cylinder(bw + TURN, face + 2, align=ZMIN)
    return ring + hub


def cl2():
    out = None
    for i, (t, b) in enumerate(CL2_VARIANTS):
        p = Pos(18.0 * i, 0, 0) * (detent(t, b) - dots(i + 1, 5.2, R.PINION_FACE))
        out = p if out is None else out + p
    return out


def oring_pinion(squeeze):
    """Option C: pinion bore = hub Ø5 + TURN, two grooves; groove floor = hub r + cs × (1 - squeeze)."""
    face = R.PINION_FACE
    r_hub = B.SLEEVE_OD / 2
    g = B.pinion(B.SLEEVE_OD + 2 * TURN, face)
    rg = r_hub + ORING_CS * (1 - squeeze)
    for zc in (face * 0.27, face * 0.73):
        g -= Pos(0, 0, zc - GROOVE_W / 2) * Cylinder(rg, GROOVE_W, align=ZMIN)
    return g


def cl3():
    out = Pos(-18.0, 0, 0) * Rot(180, 0, 0) * Pos(0, 0, -(B.SHOULDER_X[1] - B.SLEEVE_X0)) * B.clutch_sleeve()
    for i, s in enumerate(CL3_SQUEEZE):
        out += Pos(18.0 * i, 0, 0) * oring_pinion(s)
    for i in range(3):
        out -= dots(i + 1, 5.6, R.PINION_FACE).translate((18.0 * i, 0, 0))
    return out


def k1_sleeve(side):
    """1 mm-wall sleeve (the real one's length) whose shoulder is a 50 mm lever, printed lever down."""
    d = R.d_profile(R.N20_SHAFT_D + 2 * (fits.DSHAFT.side + side), R.N20_SHAFT_FLAT)
    L = B.SHOULDER_X[1] - B.SLEEVE_X0
    t = B.SHOULDER_X[1] - B.SHOULDER_X[0]
    part = Cylinder(B.SHOULDER_D / 2, t, align=ZMIN) + Pos(0, K1_ARM / 2, t / 2) * Box(6.0, K1_ARM + 6, t)
    part += Cylinder(B.SLEEVE_OD / 2, L, align=ZMIN)
    part -= Pos(0, 0, -1) * extrude(Polygon(*[tuple(p) for p in d], align=None), amount=L + 2)
    return part - Pos(0, K1_ARM, -1) * Cylinder(1.6, t + 2, align=ZMIN)


def k1_collar(side):
    d = R.d_profile(R.N20_SHAFT_D + 2 * (fits.DSHAFT.side + side), R.N20_SHAFT_FLAT)
    part = Cylinder(B.COLLAR_D / 2, B.COLLAR_L, align=ZMIN)
    return part - Pos(0, 0, -1) * extrude(Polygon(*[tuple(p) for p in d], align=None), amount=B.COLLAR_L + 2)


def k1():
    out = None
    t = B.SHOULDER_X[1] - B.SHOULDER_X[0]
    for i, s in enumerate(DSHAFT_STEPS):
        p = Pos(12.0 * i, 0, 0) * (k1_sleeve(s) - dots(i + 1, 0.0, t).translate((0, 12.0, 0)))
        p += Pos(12.0 * i, -12.0, 0) * k1_collar(s)
        out = p if out is None else out + p
    return out


PARTS = {"coupon-cl1-stand": cl1_stand, "coupon-cl1-arm": cl1_arm, "coupon-cl2": cl2, "coupon-cl3": cl3,
         "coupon-k1": k1}
