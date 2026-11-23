"""Drive of cad/robot (plan.json): spine, 4 crankshafts (with the legs' Ø3 crank pins), 3 idlers + the transfer
compound on printed spacer sleeves, the drive unit (N10 clamp, transfer cheeks, blocks and ears, journal-cap cheeks
and tongues for cranks 1-3, lugs clamped by idler axles 1 and 2) and the pinion. The N10 and the M2 screws are
hardware: their meshes are in drive_verify.py, their numbers here.

Every layout number is the fit check's (fitcheck/check.py LAYOUT and its E() defaults, read by shells.CL; 0 failing
of 319 with the real legs), re-derived here with the same formulas, never typed. Clearances only from cad/fits.py.
Robot frame, mm: x across (right legs +x), y along (front -y), z up; crank axes along x.

    ../../.venv/bin/python drive.py [--part spine] [--fine]
"""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT, ROOT + "/cad", HERE, HERE + "/fitcheck"):
    if p not in sys.path: sys.path.insert(0, p)
from build123d import Box, Cylinder, Pos, Rot, Plane, Polygon, extrude, Align, Compound, Sphere
from cad import common, fits as F
import shells as SH                        # CL (check.py layout), FE (S, P, patched pivots, A_ALL)
FE, CL, P, A_ALL = SH.FE, SH.CL, SH.P, SH.A_ALL
OUT = SH.OUT

# ---------------- gear train (check.py: m 0.6 from the scale; teeth)
M = 0.6; ZT, ZP, ZB, ZS = 12, 16, 20, 15            # crank gear, pinion, transfer big, transfer small
W, GW = CL.W, CL.GW                                 # wall 1.2, gear width 3.0
rp = lambda z: M * z / 2
rt = lambda z: M * z / 2 + M
cc = lambda za, zb: rp(za) + rp(zb) + F.GEAR_BACKLASH / 2          # centre distance with backlash (check.py)
O = [FE.motion.pivot(i, P)[1] for i in range(4)]    # crank centres (cranks 2/3 D23 patch in fit_env)
Oy = [float(o[1]) for o in O]; Oz = float(O[0][2])
def _zfor(gap):                                     # smallest idler (>= 12 T) bridging two crank gears, h >= 2
    for z in range(12, 40):
        c = cc(ZT, z)
        if c * c - (gap / 2) ** 2 >= 4.0: return z
ZI = [_zfor(Oy[i + 1] - Oy[i]) for i in range(3)]
def _idler(y1, y2, r):
    d = y2 - y1; h = math.sqrt(max(r * r - (d / 2) ** 2, 0)); return ((y1 + y2) / 2, Oz + h)   # above the crank line
I = [_idler(Oy[i], Oy[i + 1], cc(ZT, ZI[i])) for i in range(3)]
IDL_T = 0.2                                         # idlers GW - 0.4 wide (each face GEAR_THRUST_IDLER to its wall)
TH = F.GEAR_THRUST_CRANK.side; GX = GW / 2
WX0, WX1 = GX + TH, GX + TH + W                     # spine walls at |x| WX0..WX1
JR = 1.5                                            # crank journal Ø3 (check.py JR)
PINR = CL.PINR                                      # crank pin Ø3 (legs' bore TURN over it)
WEB_T = CL.WEB_T; WB0 = WX1 + TH; WB1 = WB0 + WEB_T  # webs just outside the walls (THRUST)
WEBR = PINR + CL.WEBW                               # web stadium half-width (check.py WEBR)
PIN_X1 = P["XC"] + CL.PINX                          # pin tip (|x|)
PIN_TIP_TRIM = 0.5                                  # printed pin ends this much short of PIN_X1: the leg's arm sits on the pin axis just past the tip (2026-11-23: 0.25 left crank-4 x leg-3 at 0.06 at pose 21 in --quick); the snap bead, not the tip, holds the leg
# pin collar (leg-on-pin "+x crank web"): the leg's end tube starts at XC - TAIL; the collar stops it TURN short, less
# the tube face's tilt at the collar radius (the leg swings FLARE_DEG on its pin, shells.py), so the leg is held in x
COLLAR = False                                      # tried 2026-11-23: STL split into bodies, legs 3/4 overlap it at pose 0
COLLAR_R = PINR + F.TURN.side + 0.35
COLLAR_X1 = P["XC"] - CL.TAIL - F.TURN.side - COLLAR_R * math.sin(math.radians(max(SH.FLARE_DEG)))
IPR = 1.0                                           # M2 shank radius (idler and transfer axles, keel, holder)
M2_HEAD_R, M2_HEAD_H = 1.9, 2.0                     # ISO 4762 M2 head Ø3.8 x 2 (hardware.md socket cap)
M2_PILOT_R = 0.8                                    # self-tapping pilot Ø1.6 (plan m2-screws, assumed, coupon c2)
M2_HOLE_R = IPR + F.STEEL.side                      # clearance hole (STEEL)
YTOP = max(c[1] + IPR + F.STEEL.side + W for c in I)          # wall top over the idler axles
ZSP0 = Oz - JR - F.TURN.side - W - 0.3                         # wall bottom
SPF, SPB, KY = CL.SPF, CL.SPB, CL.KY
ZK1 = min(ZSP0, Oz - rt(ZT) - F.GEAR_TIP.side - F.TURN.side)   # keel top under the gear tips (KEELFIX)
KEEL_SCREW_Y = (-KY + 1.8, KY - 1.8)                # 2 M2 from below (check.py keel-screw)
# keel M2 from below: each head sits in a counterbore of a boss on the base floor (shells.py), flush with the base foot
# (z 0), bearing on the boss material above it, KEEL_BOSS_T thick; the spine's keel stands on the two boss tops.
BASE_FLOOR = FE.BASE_WALL_R                         # bowl floor 0.84 thick (base WALL x S; base.stl ray at the keel)
KEEL_BOSS_T = 1.5                                   # boss material over the head (bearing slab)
KEEL_HEAD_Z = 2.0                                   # head bearing face: head Ø3.8 x 2 flush with the foot (0 .. 2)
KEEL_LEN = 4.0                                      # M2 x 4: 1.5 boss + 2.5 into the keel pilot (was M2 x 6 from z 0)
KEEL_SCREWS = [(0.0, y, KEEL_HEAD_Z, KEEL_LEN) for y in KEEL_SCREW_Y]    # (x, y, z of the head's bearing face, length), shank up
ZKEEL0 = KEEL_HEAD_Z + KEEL_BOSS_T                  # keel foot on the boss tops (3.5); boss rises from the floor top to here
# transfer compound over idler TI, pinion on the N10 (check.py)
TI = int(CL.TI); _a = math.radians(CL.TANG)
T = (I[TI][0] + cc(ZS, ZI[TI]) * math.cos(_a), I[TI][1] + cc(ZS, ZI[TI]) * math.sin(_a))
XB0 = WX1 + F.GEAR_AXIAL.side                       # big gear and pinion face (+x of the +x wall)
_m = math.radians(CL.MANG); MC = (T[0] + cc(ZB, ZP) * math.cos(_m), T[1] + cc(ZB, ZP) * math.sin(_m))
# N10 (hardware.md: N10 3 V metal gearbox, Ø3 D-shaft; 12 x 10 section, 21 long with its gearbox: check.py, to be
# measured when bought, plan m5): its gearbox face at MX1, shaft to the pinion's far face
N10_W, N10_H, N10_L = 12.0, 10.0, 21.0
MX1 = XB0 - F.GEAR_AXIAL.side; MX0 = MX1 - N10_L
SHAFT_R, SHAFT_FLAT = 1.5, 0.5                      # Ø3 D-shaft, flat 0.5 deep (fits.DSHAFT)
SHAFT_X1 = XB0 + GW
XO = XB0 + GW + F.GEAR_AXIAL.side                   # transfer cheek inner face
# drive unit (check.py)
DZT = CL.DZT; DBH = CL.DBH; G_CL = F.MOTOR_SEAT.side + W
CLX1 = min(MX1, CL.CLX1); CTX0 = max(MX0 + 3, CL.CTX0)
LUGR = IPR + F.STEEL.side + W
def _top_below(y):                                  # highest gear tip under y (between the walls)
    t = [c[1] + rt(ZI[i]) for i, c in enumerate(I) if abs(c[0] - y) < rt(ZI[i]) + 2.6] + \
        [Oz + rt(ZT) for o in Oy if abs(o - y) < rt(ZT) + 2.6]
    return max(t + [YTOP])
BLOCK_Y = (T[0] - CL.DSY1, T[0] + CL.DSY2)
ZBLK = [_top_below(y) + F.GEAR_TIP.side for y in BLOCK_Y]
EAR_H = (2.4, CL.EARH2)                             # ear 2 lowered to 1.0 (plan drive-unit)
EAR_HW = 2.6
SLW = JR + F.TURN.side                              # journal slot half-width
TG = SLW - F.TURN.side                              # cap tongue half-width
ZTG = Oz + JR + F.TURN.side                         # tongue foot over the journal
ZCAP = min(ZBLK)
# cell holder interface (power.py imports these; check.py cell-holder / holder-post)
PY, PZ = CL.PY, CL.PZ                               # cells' centre y, z
def _tip_over(y0, y1):
    yy = np.linspace(y0, y1, 61); t = [YTOP]
    for (c0, c1), R in [(c, rt(ZI[i]) + F.GEAR_TIP.side + 0.03) for i, c in enumerate(I)] + \
                       [((o, Oz), rt(ZT) + F.GEAR_TIP.side + 0.03) for o in Oy]:
        m = np.abs(yy - c0) < R
        if m.any(): t.append(float((c1 + np.sqrt(R * R - (yy[m] - c0) ** 2)).max()))
    return max(t)
POST_Y = (PY + CL.HSY - 3, PY + CL.HSY + 3)         # holder-post zone in y (x +-WX1)
POST_X = (-WX1, WX1)
ZHP = _tip_over(*POST_Y) if CL.HSZ else YTOP        # post foot = spine wall top under it (spine seat)
SPRISE = max(0.0, ZHP - YTOP)                       # walls raised under the post (plan spine)
SPINE_SEAT = {"x": POST_X, "y": POST_Y, "z": ZHP}   # cell holder's post rests here, on both wall tops
SLOT4 = {"y": Oy[3], "half_width": SLW, "tongue_half_width": TG, "tongue_foot_z": ZTG, "wall_x": (WX0, WX1)}
HOLDER_SCREW = {"x": 0.0, "y": 0.5 * (BLOCK_Y[1] - DBH + BLOCK_Y[1] + DBH), "ear_top_z": DZT + EAR_H[1],
                "pilot_r": M2_PILOT_R, "pilot_bottom_z": None}       # M2 down through the holder tab into ear 2 / block 2
YB_END = BLOCK_Y[1] + DBH
POWER_IFACE = dict(Oy=Oy, Oz=Oz, wx0=WX0, wx1=WX1, ytop=YTOP, tip_over=_tip_over, JR=JR,
                   EAR2=((-EAR_HW, BLOCK_Y[1] - DBH, DZT), (EAR_HW, BLOCK_Y[1] + DBH, DZT + EAR_H[1])),
                   BLOCK2=((-WX1, BLOCK_Y[1] - DBH, ZBLK[1]), (WX1, BLOCK_Y[1] + DBH, DZT)), DZT=DZT,
                   SPINE_SEAT=SPINE_SEAT, POST_Y=POST_Y, SLOT4=SLOT4, HOLDER_SCREW=HOLDER_SCREW)


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return Pos(*((lo + hi) / 2)) * Box(*(hi - lo))


def cylx(y, z, r, x0, x1):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def cylz(x, y, r, z0, z1):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def fuse(shs):
    out = shs[0]
    for s in shs[1:]: out = out + s
    return out


# ---------------- gears: involute 20 deg, teeth thinned by GEAR_BACKLASH / 4 a flank at the pitch circle
def gear_profile(teeth, n=6):
    r_p = rp(teeth); rb = r_p * math.cos(math.radians(20)); ra, rf = r_p + M, r_p - 1.25 * M
    inv = lambda a: math.tan(a) - a
    half = math.pi / (2 * teeth) + inv(math.acos(rb / r_p)) - (F.GEAR_BACKLASH / 4) / r_p
    pts = []
    for k in range(teeth):
        c = 2 * math.pi * k / teeth
        rs = np.linspace(max(rb, rf), ra, n)
        flank = [(r, half - inv(math.acos(min(1.0, rb / r)))) for r in rs]
        if rf < rb: flank = [(rf, half)] + flank
        for r, a in flank: pts.append((r * math.cos(c - a), r * math.sin(c - a)))
        for r, a in reversed(flank): pts.append((r * math.cos(c + a), r * math.sin(c + a)))
    return pts


def gear(teeth, x0, x1, y, z, phase):
    """spur gear along x from x0 to x1, centred (y, z), tooth 0 at angle phase (rad, from +y towards +z)."""
    c, s = math.cos(phase), math.sin(phase)
    pts = [(y + u * c - v * s, z + u * s + v * c) for u, v in gear_profile(teeth)]
    pl = Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    return extrude(pl * Polygon(*pts, align=None), amount=x1 - x0)


def _dir(a, b): return math.atan2(b[1] - a[1], b[0] - a[0])
def _mate(na, ca, pa, nb, cb):
    """phase of gear b (nb teeth at cb) so that it meshes gear a (na at ca, phase pa) centred in its backlash."""
    ba = _dir(ca, cb); u = na * (ba - pa) / (2 * math.pi)
    return ba + math.pi - 2 * math.pi * (0.5 - u) / nb


def phases():
    """tooth-0 angle at crank pose 0 of every gear: crank 1 at 0, then along the train."""
    ph = {"crank-1": 0.0}; C = [(Oy[i], Oz) for i in range(4)]
    for i in range(3):
        ph[f"idler-{i+1}"] = _mate(ZT, C[i], ph[f"crank-{i+1}"], ZI[i], I[i])
        ph[f"crank-{i+2}"] = _mate(ZI[i], I[i], ph[f"idler-{i+1}"], ZT, C[i + 1])
    ph["transfer-small"] = _mate(ZI[TI], I[TI], ph[f"idler-{TI+1}"], ZS, T)
    ph["transfer-big"] = 0.0
    ph["pinion"] = _mate(ZB, T, 0.0, ZP, MC)
    return ph
PH = phases()
# turn per crank pose (rad about +x): cranks -15 deg a pose (motion: the pins' angle falls 15 deg a pose)
def crank_angle(k): return -2 * math.pi * k / 24
RATIO = {**{f"crank-{i+1}": 1.0 for i in range(4)}, **{f"idler-{i+1}": -ZT / ZI[i] for i in range(3)},
         "transfer": ZT / ZS, "pinion": -ZT / ZS * ZB / ZP}
CENTRE = {**{f"crank-{i+1}": (Oy[i], Oz) for i in range(4)}, **{f"idler-{i+1}": I[i] for i in range(3)},
          "transfer": T, "pinion": MC}


# ---------------- parts
def spine():
    walls = []
    for sx in (1, -1):
        xa, xb = (WX0, WX1) if sx > 0 else (-WX1, -WX0)
        walls.append(box((xa, Oy[0] - SPF, ZSP0), (xb, Oy[3] + SPB, YTOP)))
        walls.append(box((xa, -KY, ZK1), (xb, KY, ZSP0 + 0.01)))
        if SPRISE > 0: walls.append(box((xa, POST_Y[0], YTOP - 0.01), (xb, POST_Y[1], ZHP)))
    walls.append(box((-WX1, -KY, ZKEEL0), (WX1, KY, ZK1 + 0.01)))          # keel block
    sp = fuse(walls)
    for o in Oy:                                                            # open-top U slots (TURN)
        sp = sp - cylx(o, Oz, SLW, -WX1 - 1, WX1 + 1) - box((-WX1 - 1, o - SLW, Oz), (WX1 + 1, o + SLW, ZHP + 1))
    for c in I:                                                             # idler axles: -x STEEL, +x pilot
        sp = sp - cylx(c[0], c[1], M2_HOLE_R, -WX1 - 1, -WX0 + 0.01) - cylx(c[0], c[1], M2_PILOT_R, WX0 - 0.01, WX1 + 1)
    for y in KEEL_SCREW_Y:                                                  # keel pilots from below
        sp = sp - cylz(0, y, M2_PILOT_R, ZKEEL0 - 1, KEEL_HEAD_Z + KEEL_LEN + 0.5)   # M2x4 from the boss, 0.5 past its tip
    return sp


def crank(i):
    """crankshaft i at crank pose 0: journal through both walls, gear (phased), webs and Ø3 pins at A_ALL[i], A_ALL[i+4]."""
    o = (Oy[i], Oz)
    parts = [cylx(o[0], o[1], JR, -WB0 - 0.01, WB0 + 0.01), gear(ZT, -GX, GX, o[0], o[1], PH[f"crank-{i+1}"])]
    for L, sx in ((i, 1), (i + 4, -1)):
        A = A_ALL[L, 0]; x0, x1 = (WB0, WB1) if sx > 0 else (-WB1, -WB0)
        d = math.hypot(A[1] - o[0], A[2] - o[1]); ang = math.degrees(math.atan2(A[2] - o[1], A[1] - o[0]))
        parts.append(cylx(o[0], o[1], WEBR, x0, x1)); parts.append(cylx(A[1], A[2], WEBR, x0, x1))
        parts.append(Pos((x0 + x1) / 2, (o[0] + A[1]) / 2, (o[1] + A[2]) / 2) * Rot(ang, 0, 0) * Box(x1 - x0, d, 2 * WEBR))
        pa, pb = (WB1 - 0.01, PIN_X1 - PIN_TIP_TRIM) if sx > 0 else (-PIN_X1 + PIN_TIP_TRIM, -WB1 + 0.01)
        pin = cylx(A[1], A[2], PINR, pa, pb)
        gx0, gx1 = SH.snap_groove(i)                                                          # snap groove: the bead's travel over the 24 poses
        gx0, gx1 = (gx0, gx1) if sx > 0 else (-gx1, -gx0)
        pin = pin - (cylx(A[1], A[2], PINR + 0.5, gx0, gx1) - cylx(A[1], A[2], SH.SNAP_NECK_R, gx0 - 0.01, gx1 + 0.01))
        parts.append(pin)
        ca, cb = (WB1 - 0.01, COLLAR_X1) if sx > 0 else (-COLLAR_X1, -WB1 + 0.01)
        if COLLAR: parts.append(cylx(A[1], A[2], COLLAR_R, ca, cb))          # collar: the leg's inner stop along x (off: see report)
    c = fuse(parts)
    for u, v in common.dice(i + 1, 1.0):                                    # i+1 dots on the +x web hub: which crank, which end
        c = c - Pos(WB1, o[0] + u, o[1] + v) * Sphere(0.35)
    return c


IDLER_BORE = 3.2 / 2 + F.TURN.side                  # idler turns on its sleeve (TURN)
SLEEVE_R = 3.2 / 2                                  # printed sleeve Ø3.2 (plan idlers), M2 tapped bore Ø1.6


def idler(i):
    g = gear(ZI[i], -GX + IDL_T, GX - IDL_T, I[i][0], I[i][1], PH[f"idler-{i+1}"])
    return g - cylx(I[i][0], I[i][1], IDLER_BORE, -5, 5)


def sleeve(i):
    c = I[i]; return cylx(c[0], c[1], SLEEVE_R, -WX0, WX0) - cylx(c[0], c[1], M2_PILOT_R, -WX0 - 1, WX0 + 1)


HUB_R = IDLER_BORE + W                              # transfer hub over the wall band
def transfer():
    g = gear(ZS, -GX + IDL_T, GX - IDL_T, T[0], T[1], PH["transfer-small"]) + cylx(T[0], T[1], HUB_R, GX - IDL_T - 0.01, XB0 + 0.01) \
        + gear(ZB, XB0, XB0 + GW, T[0], T[1], PH["transfer-big"])
    return g - cylx(T[0], T[1], IDLER_BORE, -10, 12)


TS_X0, TS_X1 = -WX1, XO                              # transfer sleeve between the drive unit's cheeks
def transfer_sleeve():
    return cylx(T[0], T[1], SLEEVE_R, TS_X0, TS_X1) - cylx(T[0], T[1], M2_PILOT_R, TS_X0 - 1, TS_X1 + 1)


def pinion():
    g = gear(ZP, XB0, XB0 + GW, MC[0], MC[1], PH["pinion"])
    r = SHAFT_R + F.DSHAFT.side
    bore = cylx(MC[0], MC[1], r, XB0 - 1, XB0 + GW + 1)
    flat = box((XB0 - 1, MC[0] - r - 1, MC[1] + r - SHAFT_FLAT), (XB0 + GW + 1, MC[0] + r + 1, MC[1] + r + 1))
    return g - (bore - flat)


def drive_unit():
    my, mz = MC; g = G_CL; ty, tz = T
    q = [box((MX0 + 3, my - N10_W / 2 - g, mz - N10_H / 2 - g), (CLX1, my + N10_W / 2 + g, mz - N10_H / 2 - F.MOTOR_SEAT.side)),
         box((CTX0, my - N10_W / 2 - g, mz + N10_H / 2 + F.MOTOR_SEAT.side), (MX1, my + N10_W / 2 + g, mz + N10_H / 2 + g)),
         box((XO, min(ty, my) - 3, min(tz, mz) - 3), (XO + W, max(ty, my) + 3, mz + rt(ZP) + F.GEAR_TIP.side + W)),   # transfer cheek, up to the bridge
         box((-WX1 - W, min(ty, my) - CL.DSY1 - 2.6, DZT), (-WX1, max(ty, my) + 3, mz - N10_H / 2 - g + W)),   # -x web: ears to the lower clamp
         box((MX1 - 1.0, my - 3, mz + rt(ZP) + F.GEAR_TIP.side), (XO + W, my + 3, mz + rt(ZP) + F.GEAR_TIP.side + W)),  # bridge over the pinion: upper clamp to the transfer cheek
         box((-WX1 - W, ty - 3, tz - 3), (-WX1, ty + 3, tz + 3))]                                     # inner cheek
    for sy in (-1, 1):                                                       # clamp side rails (motor +-y, MOTOR_SEAT)
        ya, yb = my + sy * (N10_W / 2 + F.MOTOR_SEAT.side), my + sy * (N10_W / 2 + g)
        q.append(box((CTX0, min(ya, yb), mz - N10_H / 2 - g), (CTX0 + 3, max(ya, yb), mz + N10_H / 2 + g)))
    for k in (0, 1):                                                         # lugs on the -x plate, idler axles 1, 2
        c = I[k]; q.append(cylx(c[0], c[1], LUGR, -WX1 - W, -WX1)); q.append(box((-WX1 - W, c[0] - LUGR, c[1]), (-WX1, c[0] + LUGR, DZT + 0.5)))
    for k, y in enumerate(BLOCK_Y):                                          # blocks + ears
        q.append(box((-WX1, y - DBH, ZBLK[k]), (WX1, y + DBH, DZT + 0.01)))
        q.append(box((-EAR_HW, y - DBH, DZT), (EAR_HW, y + DBH, DZT + EAR_H[k])))
        for sx in (1, -1):                                                   # block legs down to the cheeks (wall band)
            xa, xb = (WX0, WX1) if sx > 0 else (-WX1, -WX0); q.append(box((xa, y - DBH, YTOP), (xb, y + DBH, ZBLK[k] + 0.01)))
    for sx in (1, -1):                                                       # cheeks on the wall tops + tongues 1-3
        xa, xb = (WX0, WX1) if sx > 0 else (-WX1, -WX0)
        q.append(box((xa, Oy[0] - SLW - W, YTOP), (xb, YB_END, ZCAP)))
        for i in range(3): q.append(box((xa, Oy[i] - TG, ZTG), (xb, Oy[i] + TG, YTOP + 0.01)))
    du = fuse(q)
    pr = rt(ZP) + F.NEIGHBOUR.side; gw = math.sqrt(pr ** 2 - (N10_H / 2 + F.MOTOR_SEAT.side) ** 2) + 0.1
    for sz in (-1, 1):                                                       # pinion path grooves in both clamp plates (it rides in along +x)
        z0, z1 = sorted((mz + sz * (N10_H / 2 + F.MOTOR_SEAT.side - 0.01), mz + sz * pr))
        du = du - box((MX0, my - gw, z0), (MX1 + 0.5, my + gw, z1))
    for k in (0, 1):                                                         # lug holes (STEEL)
        c = I[k]; du = du - cylx(c[0], c[1], M2_HOLE_R, -WX1 - W - 1, -WX1 + 0.01)
    du = du - cylx(ty, tz, M2_HOLE_R, -WX1 - W - 1, -WX1 + 0.01) - cylx(ty, tz, M2_PILOT_R, XO - 0.01, XO + W + 1)   # transfer axle
    du = du - cylx(ty, tz, rt(ZS) + F.GEAR_TIP.side, -GX, GX) - cylx(ty, tz, HUB_R + F.TURN.side, GX - IDL_T, XB0) \
            - cylx(ty, tz, rt(ZB) + F.GEAR_TIP.side, XB0 - F.GEAR_AXIAL.side + 0.01, XO - 0.01) \
            - cylx(my, mz, rt(ZP) + F.GEAR_TIP.side, MX1 + 0.01, XO - 0.01)                   # the transfer's and pinion's sweeps
    HOLDER_SCREW["pilot_bottom_z"] = max(ZBLK[1] + 0.8, HOLDER_SCREW["ear_top_z"] - 7.0)
    du = du - cylz(0, HOLDER_SCREW["y"], M2_PILOT_R, HOLDER_SCREW["pilot_bottom_z"], HOLDER_SCREW["ear_top_z"] + 1)
    return du


PARTS = {"spine": spine, **{f"crank-{i+1}": (lambda i=i: crank(i)) for i in range(4)},
         **{f"idler-{i+1}": (lambda i=i: idler(i)) for i in range(3)},
         **{f"sleeve-{i+1}": (lambda i=i: sleeve(i)) for i in range(3)},
         "transfer": transfer, "transfer-sleeve": transfer_sleeve, "drive-unit": drive_unit, "pinion": pinion}


def layout():
    print(f"O y {np.round(Oy, 2)} z {Oz:.2f}; ZI {ZI}; idlers {np.round(I, 2).tolist()}; T {np.round(T, 2)}; MC {np.round(MC, 2)}")
    print(f"walls x {WX0}..{WX1}, z {ZSP0:.2f}..{YTOP:.2f}, keel {ZKEEL0}..{ZK1:.2f}; blocks y {np.round(BLOCK_Y, 2)} z {np.round(ZBLK, 2)}; "
          f"ZHP {ZHP:.2f} SPRISE {SPRISE:.2f}; post y {np.round(POST_Y, 2)}; YB_END {YB_END:.2f}; motor x {MX0:.2f}..{MX1:.2f}")


def write_all(names=None, fine=None):
    for n in names or PARTS:
        sh = PARTS[n](); common.export(n, sh, OUT, fine=fine)
        print(f"    {n}: {len(sh.solids())} solid(s), valid {sh.is_valid}", flush=True)


if __name__ == "__main__":
    a = common.part_args(__doc__, PARTS, extra=lambda ap: ap.add_argument("--layout", action="store_true"))
    layout()
    if not a.layout: write_all(a.part, a.fine)
