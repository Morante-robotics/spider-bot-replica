"""Drive of cad/robot (plan.json): spine, 4 crankshafts (with the legs' Ø3 crank pins), 3 idlers + the transfer
compound on M3 shanks (plan B: no sleeves), the drive unit as 3 flat parts screwed with M3 (plan A): journal-cap
(tongues over journals 1-4, F), motor-u (web, U for the N10, ear 2) and transfer-cheek (pin pocket + strap), and the
pinion. The N10 and the M3 screws are hardware: their meshes are in drive_verify.py, their numbers here.

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
from build123d import Box, Cylinder, Pos, Rot, Plane, Polygon, extrude, Align, Compound, Sphere, Axis
from cad import common, fits as F
import shells as SH                        # CL (check.py layout), FE (S, P, patched pivots, A_ALL)
FE, CL, P, A_ALL = SH.FE, SH.CL, SH.P, SH.A_ALL
OUT = SH.OUT

# ---------------- gear train (check.py: m 0.6 from the scale; teeth)
M = F.MODULE_MIN; ZT, ZP, ZB, ZS = 10, 14, 17, 13   # crank gear, pinion, transfer big, transfer small: the S 0.70 pitch
                                                    # diameters x K at module 1.0, fewer teeth (datasheet «Phase 1 result»)
W, GW = CL.W, CL.GW                                 # wall fits.WALL_MIN, gear width 3.0 x K
rp = lambda z: M * z / 2
rt = lambda z: M * z / 2 + M
cc = lambda za, zb: rp(za) + rp(zb) + F.GEAR_BACKLASH / 2          # centre distance with backlash (check.py)
O = [FE.motion.pivot(i, P)[1] for i in range(4)]    # crank centres (motion.py)
Oy = [float(o[1]) for o in O]; Oz = float(O[0][2])
def _zfor(gap):                                     # smallest idler (>= ZT) bridging two crank gears, h >= 2
    for z in range(ZT, 60):
        c = cc(ZT, z)
        if c * c - (gap / 2) ** 2 >= 4.0: return z
ZI = [_zfor(Oy[i + 1] - Oy[i]) for i in range(3)]
def _idler(y1, y2, r):
    d = y2 - y1; h = math.sqrt(max(r * r - (d / 2) ** 2, 0)); return ((y1 + y2) / 2, Oz + h)   # above the crank line
I = [_idler(Oy[i], Oy[i + 1], cc(ZT, ZI[i])) for i in range(3)]
IDL_T = 0.2                                         # idlers GW - 0.4 wide (each face GEAR_THRUST_IDLER to its wall)
TH = F.GEAR_THRUST_CRANK.side; GX = GW / 2
WX0, WX1 = GX + TH, GX + TH + W                     # spine walls at |x| WX0..WX1
JR = 1.5 * FE.K                                     # crank journal Ø3 x K (Ø4.3, TURN)
PINR = CL.PINR                                      # crank pin Ø3 (legs' bore TURN over it)
WEB_T = CL.WEB_T; WB0 = WX1 + TH; WB1 = WB0 + WEB_T  # webs just outside the walls (THRUST)
WEBR = PINR + CL.WEBW                               # web stadium half-width (check.py WEBR)
WEB_SWEEP = [math.hypot(A_ALL[i + 4, 0][1] - Oy[i], A_ALL[i + 4, 0][2] - Oz) + WEBR for i in range(4)]   # -x webs' reach round each crank centre
PIN_TRIM = 0.5                                      # pin tip short of the leg's bore floor by this more (the inward-drifted leg's floor met the tip: crank 4 x legs 3/7, phase 3)
PIN_X1 = P["XC"] + CL.PINX - PIN_TRIM                 # pin tip (|x|)
# pin collar (leg-on-pin "+x crank web"): the leg's end tube starts at XC - TAIL; the collar stops it TURN short, less
# the tube face's tilt at the collar radius (the leg swings FLARE_DEG on its pin, shells.py), so the leg is held in x
COLLAR = False                                      # tried 2026-11-23: STL split into bodies, legs 3/4 overlap it at pose 0
COLLAR_R = PINR + F.TURN.side + 0.35
COLLAR_X1 = P["XC"] - CL.TAIL - F.TURN.side - COLLAR_R * math.sin(math.radians(max(SH.FLARE_DEG)))
IPR = 1.5                                           # M3 shank radius (idler and transfer axles, keel, holder)
M3_HEAD_R, M3_HEAD_H = 2.75, 3.0                    # ISO 4762 M3 head Ø5.5 x 3 (hardware.md socket cap)
M3_PILOT_R = 1.25                                   # self-tapping pilot Ø2.5 (plan m2-screws, assumed, coupon c2)
M3_HOLE_R = IPR + F.STEEL.side                      # clearance hole (STEEL)
YTOP = max(c[1] + IPR + F.STEEL.side + W for c in I)          # wall top over the idler axles
ZSP0 = Oz - JR - F.TURN.side - W - 0.3 * FE.K                         # wall bottom
SPF, SPB, KY = CL.SPF, CL.SPB, CL.KY
ZK1 = min(ZSP0, Oz - rt(ZT) - F.GEAR_TIP.side - F.TURN.side)   # keel top under the gear tips (KEELFIX)
KEEL_SCREW_Y = (-KY + 1.8 * FE.K, KY - 1.8 * FE.K)                # 2 M2 from below (check.py keel-screw)
# keel M2 from below: each head sits in a counterbore of a boss on the base floor (shells.py), flush with the base foot
# (z 0), bearing on the boss material above it, KEEL_BOSS_T thick; the spine's keel stands on the two boss tops.
BASE_FLOOR = FE.BASE_WALL_R                         # bowl floor 0.84 thick (base WALL x S; base.stl ray at the keel)
KEEL_BOSS_T = F.WALL_MIN                                   # boss material over the head (bearing slab)
KEEL_HEAD_Z = M3_HEAD_H                                   # head bearing face: head Ø3.8 x 2 flush with the foot (0 .. 2)
KEEL_LEN = 5.0                                      # M3 x 5 from the bearing face: 2 boss + 3 into the keel pilot (was 6: left 0.85 over the pilot, < WALL_MIN)
KEEL_PILOT_OVER = 0.2                               # pilot past the screw tip; keel top over it = ZK1 - (3 + 5 + 0.2) >= WALL_MIN
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
DZT = CL.DZT; DBH = CL.DBH                           # ear-2 top (holder tab seat) and half-depth: the holder tab's place (power.py), unchanged
LUGR = IPR + F.STEEL.side + W                       # lug round an idler axle: STEEL hole + wall
BLOCK_Y = (T[0] - CL.DSY1, T[0] + CL.DSY2)          # ear 2 (holder screw) at BLOCK_Y[1], as in phase 2
EAR_H = (2.4 * FE.K, CL.EARH2)
EAR_HW = 2.6 * FE.K                                 # ear 2 half-width in x (holder tab 2 x TABHW sits on it)
DU_W = 2.0                                          # plates of the 3 drive parts: fits.WALL_MIN (print 2026-11-24: 1.2 broke)
SLW = JR + F.TURN.side                              # journal slot half-width
TG = SLW - F.TURN.side                              # cap tongue half-width (TURN a side in the slot)
ZTG = Oz + JR + F.TURN.side                         # tongue foot over the journal (TURN)
# ---------------- journal-cap (plan A/F): flat plate over the idler tips, rails on the wall tops, tongues 1-4, lug on axle 3
CAP_Z0 = max(c[1] + rt(ZI[i]) for i, c in enumerate(I)) + F.GEAR_TIP.side   # plate underside over the highest idler tip
CAP_Z1 = CAP_Z0 + W                                 # cap top: the motor-u ledge and the holder post stand on it
LEG7_R, LEG7_DEPTH = 7.3, 0.25                       # round crank 4: the part of lug 3's -x face leg 7's hub sweeps within 0.2 of (probe at the poses 4-6)
CAP_Y0, CAP_Y1 = Oy[0] - SLW - W, Oy[3] + SLW + W   # over slot 1 .. slot 4 + wall
LUG_X0 = -WX1 - W                                   # lugs (cap lug 3, motor-u lugs 1, 2) on the -x wall's outer face
IDLER_BORE = IPR + F.STEEL.side                     # idlers and transfer turn on an M3 shank (plan B, STEEL)
HUB_R = IDLER_BORE + W                              # transfer hub through the +x wall band
MESH_TOL = 0.05                                     # coarse-STL chord on a designed gap (the checks read the coarse export)
NOTCH_R = rt(ZS) + F.GEAR_TIP.side + MESH_TOL       # cap notch round the transfer's small gear (PLAN probe: 0.24 -> tip + GEAR_TIP)
NOTCH_HY = math.sqrt(NOTCH_R ** 2 - (T[1] - CAP_Z1) ** 2)   # notch cut square through the plate: the tip circle's widest chord in it
HUBCUT = HUB_R + F.GEAR_TIP.side + MESH_TOL         # +x rail cut round the transfer hub, open to the top
BTN_R, BTN_H = 2.85, 1.65                           # ISO 7380 M3 button head Ø5.7 x 1.65, 2 mm hex key (Morante 2026-11-27): idler axles 1-3, transfer-pin
# ---------------- motor-u (plan A): -x web on the wall face, ledge + boss + ear 2 on the cap, U for the N10 (open +z)
UZ0 = MC[1] - N10_H / 2 - F.MOTOR_SEAT.side - DU_W  # U floor underside
UZ1 = MC[1] + N10_H / 2 + F.MOTOR_SEAT.side         # U wall tops = strap underside (motor top + MOTOR_SEAT)
UY0 = MC[0] - N10_W / 2 - F.MOTOR_SEAT.side - DU_W  # U outer faces in y
UY1 = MC[0] + N10_W / 2 + F.MOTOR_SEAT.side + DU_W
UX1 = MX1                                           # U ends at the gearbox face: the pinion is GEAR_AXIAL past it
BOSS_R = M3_HEAD_R + F.STEEL.side + 1.2             # transfer-pin boss half-size: head hole + 1.2 loaded wall
TP_X = LUG_X0                                       # transfer-pin head on the web's -x face (the bed face: no bridge over a counterbore)
TP_L = 16.0                                         # M3 x 16 (Morante 2026-11-26): thread 4.0 in web + boss, tip TP_X + 16 = 9.61, the cheek GEAR_AXIAL - 0.13 past it (+x stop)
STRAP_Y = UY0 + DU_W - W - M3_PILOT_R              # strap screw pilot: W to the U's inner face, W to the ear's outer face
EARM_Y0 = STRAP_Y - M3_PILOT_R - W                  # -y ear outer face (room probe: 1.81 to the body)
STRAP_X = 0.5 * (LUG_X0 + UX1)                      # one strap screw mid-ear (two heads do not fit in the ear's 10.8 mm)
STRAP_L = 10.0
ZS1 = UZ1 + DU_W                                    # strap top (screw head bearing face)
EARM_Z0 = ZS1 - STRAP_L - 0.5                       # -y ear bottom: the M3 x 10 tip 0.5 above it
HOLDER_SCREW = {"x": 0.0, "y": BLOCK_Y[1], "ear_top_z": DZT + EAR_H[1], "pilot_r": M3_PILOT_R, "pilot_bottom_z": CAP_Z1}
E2Y = (BLOCK_Y[1] - DBH, BLOCK_Y[1] + DBH)          # ear 2 in y
KEYHOLE_R = M3_HEAD_R + F.STEEL.side                # holder screw head + hex key through the U (slot open to +x)
# ---------------- transfer-cheek (plan A): +x cheek (transfer and pin stop) + strap over the N10 and the -y ear
CH_Y1 = T[0] + IDLER_BORE + W                       # cheek round the pin pocket
CH_Z0 = T[1] - IDLER_BORE - W - 1.0
PIN_R_CUT = rt(ZP) + F.GEAR_TIP.side + MESH_TOL     # pinion's room under the strap
STRAP_CUT_Y = MC[0] - math.sqrt(PIN_R_CUT ** 2 - (UZ1 - MC[1]) ** 2)   # strap's +y edge beside the pinion (square cut, no wedge)
SLOPE = 1.2                                         # self-supporting growth: 1 mm sideways per 1.2 mm of height (40 deg)
STRAP_TIP_W = F.WALL_MIN + 0.4                   # strap's square end is this wide where the 40 deg edge meets it
STRAP_LIP_Y = MC[0] - N10_W / 2 + W                 # strap's +y edge at the U's end: 2 mm over the motor's -y top edge


def _tip_over(y0, y1):
    yy = np.linspace(y0, y1, 61); t = [YTOP]
    for (c0, c1), R in [(c, rt(ZI[i]) + F.GEAR_TIP.side + 0.03) for i, c in enumerate(I)] + \
                       [((o, Oz), rt(ZT) + F.GEAR_TIP.side + 0.03) for o in Oy]:
        m = np.abs(yy - c0) < R
        if m.any(): t.append(float((c1 + np.sqrt(R * R - (yy[m] - c0) ** 2)).max()))
    return max(t)
PY, PZ = CL.PY, CL.PZ
POST_Y = (PY + CL.HSY - 3, PY + CL.HSY + 3)
SLOT4 = {"y": Oy[3], "half_width": SLW, "tongue_half_width": TG, "tongue_foot_z": ZTG, "wall_x": (WX0, WX1)}
_EAR2 = ((-EAR_HW, E2Y[0], CAP_Z1), (EAR_HW, E2Y[1], DZT + EAR_H[1]))
POWER_IFACE = dict(Oy=Oy, Oz=Oz, wx0=WX0, wx1=WX1, ytop=YTOP, tip_over=_tip_over, JR=JR, EAR2=_EAR2, BLOCK2=_EAR2, DZT=DZT,
                   POST_Y=POST_Y, SLOT4=SLOT4, HOLDER_SCREW=HOLDER_SCREW, CAP_TOP=CAP_Z1, CAP_Y1=CAP_Y1)

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
    walls.append(box((-WX1, -KY, ZKEEL0), (WX1, KY, ZK1 + 0.01)))          # keel block
    sp = fuse(walls)
    for o in Oy:                                                            # open-top U slots (TURN)
        sp = sp - cylx(o, Oz, SLW, -WX1 - 1, WX1 + 1) - box((-WX1 - 1, o - SLW, Oz), (WX1 + 1, o + SLW, YTOP + 1))
    for c in I:                                                             # idler axles (plan B): -x wall M3 pilot (the thread), +x wall STEEL
        sp = sp - cylx(c[0], c[1], M3_PILOT_R, -WX1 - 1, -WX0 + 0.01) - cylx(c[0], c[1], M3_HOLE_R, WX0 - 0.01, WX1 + 1)
    for y in KEEL_SCREW_Y:                                                  # keel pilots from below
        sp = sp - cylz(0, y, M3_PILOT_R, ZKEEL0 - 1, KEEL_HEAD_Z + KEEL_LEN + KEEL_PILOT_OVER)   # M3x5 from the boss, 0.2 past its tip
    return sp


MARK_H, MARK_DEPTH = 3.0, 0.5                      # engraved number: ≈ 3 mm high (datasheet Phase 1, mark), 0.5 deep into the hub face
MARK_FS = 4.2                                       # build123d Text font size whose digits stand 3.07 mm tall (bold)


def mark_cutter(i):
    """Cutter of crank i's number (i+1) on the +x web hub face (x = WB1), read from +x with z up; centred on the hub."""
    from build123d import Text, FontStyle
    o = (Oy[i], Oz)
    t = Text(str(i + 1), MARK_FS, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    t = extrude(t.faces().sort_by(Axis.Z)[0], MARK_DEPTH + 0.5)               # z 0..depth+0.5 (the part past the face is air)
    return Pos(WB1 - MARK_DEPTH, o[0], o[1]) * Rot(0, 90, 0) * Rot(0, 0, 90) * t


def crank(i):
    """crankshaft i at crank pose 0: journal through both walls, gear (phased), webs and Ø3 pins at A_ALL[i], A_ALL[i+4]."""
    o = (Oy[i], Oz)
    parts = [cylx(o[0], o[1], JR, -WB0 - 0.01, WB0 + 0.01), gear(ZT, -GX, GX, o[0], o[1], PH[f"crank-{i+1}"])]
    for L, sx in ((i, 1), (i + 4, -1)):
        A = A_ALL[L, 0]; x0, x1 = (WB0, WB1) if sx > 0 else (-WB1, -WB0)
        d = math.hypot(A[1] - o[0], A[2] - o[1]); ang = math.degrees(math.atan2(A[2] - o[1], A[1] - o[0]))
        parts.append(cylx(o[0], o[1], WEBR, x0, x1)); parts.append(cylx(A[1], A[2], WEBR, x0, x1))
        parts.append(Pos((x0 + x1) / 2, (o[0] + A[1]) / 2, (o[1] + A[2]) / 2) * Rot(ang, 0, 0) * Box(x1 - x0, d, 2 * WEBR))
        pa, pb = (WB1 - 0.01, PIN_X1) if sx > 0 else (-PIN_X1, -WB1 + 0.01)
        pin = cylx(A[1], A[2], PINR, pa, pb)
        gx0, gx1 = SH.snap_groove(i)                                                          # snap groove: the bead's travel over the 24 poses
        gx0, gx1 = (gx0, gx1) if sx > 0 else (-gx1, -gx0)
        pin = pin - (cylx(A[1], A[2], PINR + 0.5, gx0, gx1) - cylx(A[1], A[2], SH.SNAP_NECK_R, gx0 - 0.01, gx1 + 0.01))
        parts.append(pin)
        ca, cb = (WB1 - 0.01, COLLAR_X1) if sx > 0 else (-COLLAR_X1, -WB1 + 0.01)
        if COLLAR: parts.append(cylx(A[1], A[2], COLLAR_R, ca, cb))          # collar: the leg's inner stop along x (off: see report)
    c = fuse(parts)
    c = c - mark_cutter(i)                                                  # engraved number i+1 on the +x web hub: which crank, which end
    return c


def tear_hole(axis, c, r, a0, a1, up):
    """hole of radius r along axis 'x' or 'z' at c (the two other coordinates), a0..a1, with a 40-deg roof toward 'up' (a unit
    vector in the other two axes, the print's up): no support inside a hole that prints sideways."""
    t = math.radians(50)                               # tangent points 50 deg off the up axis: roof faces 50 deg from horizontal
    h = r / math.cos(t)                                # apex
    if axis == "x":
        u = np.array([0, up[0], up[1]], float); v = np.array([0, -up[1], up[0]], float); o = np.array([0, c[0], c[1]], float)
        pl = Plane(origin=(a0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)); uv = lambda p: (p[1], p[2])
        cyl = cylx(c[0], c[1], r, a0, a1)
    else:
        u = np.array([up[0], up[1], 0], float); v = np.array([-up[1], up[0], 0], float); o = np.array([c[0], c[1], 0], float)
        pl = Plane(origin=(0, 0, a0), x_dir=(1, 0, 0), z_dir=(0, 0, 1)); uv = lambda p: (p[0], p[1])
        cyl = cylz(c[0], c[1], r, a0, a1)
    pts = [o + u * h, o + r * (math.cos(t) * u + math.sin(t) * v), o - r * v * 0.0 + r * (math.cos(t) * u - math.sin(t) * v)]
    tri = extrude(pl * Polygon(*[uv(p) for p in pts], align=None), amount=a1 - a0)
    return cyl + tri


def idler(i):
    g = gear(ZI[i], -GX + IDL_T, GX - IDL_T, I[i][0], I[i][1], PH[f"idler-{i+1}"])
    return g - cylx(I[i][0], I[i][1], IDLER_BORE, -5, 5)


def transfer():
    g = gear(ZS, -GX + IDL_T, GX - IDL_T, T[0], T[1], PH["transfer-small"]) + cylx(T[0], T[1], HUB_R, GX - IDL_T - 0.01, XB0 + 0.01) \
        + gear(ZB, XB0, XB0 + GW, T[0], T[1], PH["transfer-big"])
    return g - cylx(T[0], T[1], IDLER_BORE, -10, 12)


def pinion():
    g = gear(ZP, XB0, XB0 + GW, MC[0], MC[1], PH["pinion"])
    r = SHAFT_R + F.DSHAFT.side
    bore = cylx(MC[0], MC[1], r, XB0 - 1, XB0 + GW + 1)
    flat = box((XB0 - 1, MC[0] - r - 1, MC[1] + r - SHAFT_FLAT), (XB0 + GW + 1, MC[0] + r + 1, MC[1] + r + 1))
    return g - (bore - flat)


def journal_cap():
    """plan A/F: plate over the idler tips, rails on both wall tops, tongues over journals 1-4, lug 3 on the -x wall
    (idler axle 3 clamps it). Prints top face on the bed: every feature hangs from the plate, so it rises in the print."""
    q = [box((-WX1, CAP_Y0, CAP_Z0), (WX1, CAP_Y1, CAP_Z1)),
         cylx(I[2][0], I[2][1], LUGR, LUG_X0, -WX1 + 0.01), box((LUG_X0, I[2][0] - LUGR, I[2][1]), (-WX1 + 0.01, I[2][0] + LUGR, CAP_Z1))]
    for sx in (1, -1):
        xa, xb = (WX0, WX1) if sx > 0 else (-WX1, -WX0)
        q.append(box((xa, CAP_Y0, YTOP), (xb, CAP_Y1, CAP_Z0 + 0.01)))                        # rail on the wall top
        for o in Oy: q.append(box((xa, o - TG, ZTG), (xb, o + TG, YTOP + 0.01)))               # tongue in slot i
    c = fuse(q)
    for i in (2, 3):                                                            # lug 3 stays TURN off the webs of cranks 3, 4 (their sweep R = d + WEBR; was 0.19)
        c = c - cylx(Oy[i], Oz, WEB_SWEEP[i] + F.TURN.side, LUG_X0 - 1, -WX1 + 0.01)
    c = c - cylx(Oy[3], Oz, LEG7_R, LUG_X0 - 1, LUG_X0 + LEG7_DEPTH)            # leg 7's hub passes the lug's +y edge at crank pose 5: face recessed (was 0.02..0.06 off)
    c = c - box((-WX0, T[0] - NOTCH_HY, CAP_Z0 - 1), (WX0, T[0] + NOTCH_HY, CAP_Z1 + 1)) \
          - box((WX0 - 0.01, T[0] - HUBCUT, YTOP - 0.01), (WX1 + 1, T[0] + HUBCUT, CAP_Z1 + 1)) \
          - tear_hole("x", I[2], M3_HOLE_R, LUG_X0 - 1, -WX1 + 0.01, (0, -1)) \
          - cylz(HOLDER_SCREW["x"], HOLDER_SCREW["y"], M3_HOLE_R, CAP_Z0 - 1, CAP_Z1 + 1)   # holder M3 x 10 tip passes
    return c


def motor_u():
    """plan A: -x web (lugs on idler axles 1, 2), ledge and transfer-pin boss on the cap top, ear 2 (holder screw), the U
    for the N10 open to +z, the -y ear for the strap screw. Every feature runs along +x from the web's -x face (the bed)."""
    xb = -WX0                                                                    # ledge / boss +x face: the -x rail's inner face (transfer THRUST_IDLER 0.45)
    yw0 = I[0][0] - LUGR
    q = [box((LUG_X0, yw0, YTOP), (-WX1, E2Y[1], UZ0 + DU_W)),                   # web
         box((-WX1 - 0.01, yw0, CAP_Z1), (xb, E2Y[1], CAP_Z1 + W)),              # ledge on the cap top (-x rail band)
         box((-WX1 - 0.01, T[0] - BOSS_R, CAP_Z1), (xb, T[0] + BOSS_R, T[1] + BOSS_R)),   # transfer-pin boss
         box((LUG_X0, E2Y[0], CAP_Z1), (EAR_HW, E2Y[1], HOLDER_SCREW["ear_top_z"])),       # ear 2: the holder tab's seat
         box((LUG_X0, UY0, UZ0), (UX1, UY1, UZ0 + DU_W)),                         # U floor
         box((LUG_X0, UY0, UZ0), (UX1, UY0 + DU_W, UZ1)), box((LUG_X0, UY1 - DU_W, UZ0), (UX1, UY1, UZ1)),   # U walls
         box((LUG_X0, EARM_Y0, EARM_Z0), (UX1, UY0 + 0.01, UZ1))]                # -y ear (strap screw)
    for k in (0, 1):
        c = I[k]; q += [cylx(c[0], c[1], LUGR, LUG_X0, -WX1), box((LUG_X0, c[0] - LUGR, c[1]), (-WX1, c[0] + LUGR, YTOP + 0.01))]
    m = fuse(q)
    for k in (0, 1):
        m = m - cylx(I[k][0], I[k][1], M3_HOLE_R, LUG_X0 - 1, -WX1 + 0.01)
    for i in (0, 1):                                                             # the lugs stay MIN_GAP off the webs' sweep (R = d + WEBR round crank i; was 0.19)
        m = m - cylx(Oy[i], Oz, WEB_SWEEP[i] + 0.2, LUG_X0 - 1, -WX1 + 0.01)
    m = m - cylx(T[0], T[1], M3_PILOT_R, TP_X - 1, xb + 1)                    # transfer-pin thread through web and boss
    m = m - tear_hole("z", (HOLDER_SCREW["x"], HOLDER_SCREW["y"]), M3_PILOT_R, CAP_Z1 - 0.01, HOLDER_SCREW["ear_top_z"] + 0.01, (1, 0))
    m = m - tear_hole("z", (STRAP_X, STRAP_Y), M3_PILOT_R, EARM_Z0 - 0.01, UZ1 + 0.01, (1, 0))
    hy = HOLDER_SCREW["y"]                                                       # head + hex key through the U: round end, open to +x
    m = m - box((-KEYHOLE_R, hy - KEYHOLE_R, UZ0 - 1), (UX1 + 1, hy + KEYHOLE_R, UZ1 + 1))   # square end: no sliver on the U wall
    return m


def transfer_cheek():
    """plan A: +x cheek (the big gear's and the pin's +x stop) + strap over the N10 onto the U and the -y ear,
    one M3 x 10. Prints +x face on the bed: the strap runs along -x, its pinion relief and its +y edge grow at 40 deg."""
    x0, x1 = XO, XO + DU_W
    q = [box((x0, EARM_Y0, CH_Z0), (x1, CH_Y1, ZS1))]
    sp = Plane(origin=(0, 0, UZ1), x_dir=(1, 0, 0), z_dir=(0, 0, 1))
    y_end = min(UY1 - DU_W, STRAP_CUT_Y + (UX1 - LUG_X0) / SLOPE); xe = UX1 - (y_end - STRAP_CUT_Y) * SLOPE
    y_sq = y_end - STRAP_TIP_W / SLOPE; xq = UX1 - (y_sq - STRAP_CUT_Y) * SLOPE      # square the tip: no wedge thinner than STRAP_TIP_W (was a 50 deg point)
    poly = [(x0 + 0.01, EARM_Y0), (x0 + 0.01, STRAP_CUT_Y), (UX1, STRAP_CUT_Y), (xq, y_sq), (LUG_X0, y_sq), (LUG_X0, EARM_Y0)]
    q.append(extrude(sp * Polygon(*poly, align=None), amount=DU_W))
    ch = fuse(q)                                                                 # beside the pinion the strap stops at STRAP_CUT_Y; over the U its +y edge grows at 40 deg
    ch = ch - tear_hole("z", (STRAP_X, STRAP_Y), M3_HOLE_R, UZ1 - 1, ZS1 + 1, (-1, 0))
    return ch


PARTS = {"spine": spine, **{f"crank-{i+1}": (lambda i=i: crank(i)) for i in range(4)},
         **{f"idler-{i+1}": (lambda i=i: idler(i)) for i in range(3)},
         "transfer": transfer, "pinion": pinion, "journal-cap": journal_cap, "motor-u": motor_u, "transfer-cheek": transfer_cheek}


def layout():
    print(f"O y {np.round(Oy, 2)} z {Oz:.2f}; ZI {ZI}; idlers {np.round(I, 2).tolist()}; T {np.round(T, 2)}; MC {np.round(MC, 2)}")
    print(f"walls x {WX0}..{WX1}, z {ZSP0:.2f}..{YTOP:.2f}, keel {ZKEEL0}..{ZK1:.2f}; cap z {CAP_Z0:.2f}..{CAP_Z1:.2f} y {CAP_Y0:.2f}..{CAP_Y1:.2f}; "
          f"U z {UZ0:.2f}..{UZ1:.2f} y {UY0:.2f}..{UY1:.2f}; strap screw ({STRAP_X:.2f}, {STRAP_Y:.2f}), ear z {EARM_Z0:.2f}; pin tip x {TP_X + TP_L:.2f}; motor x {MX0:.2f}..{MX1:.2f}")


def write_all(names=None, fine=None):
    for n in names or PARTS:
        sh = PARTS[n](); common.export(n, sh, OUT, fine=fine)
        print(f"    {n}: {len(sh.solids())} solid(s), valid {sh.is_valid}", flush=True)


if __name__ == "__main__":
    a = common.part_args(__doc__, PARTS, extra=lambda ap: ap.add_argument("--layout", action="store_true"))
    layout()
    if not a.layout: write_all(a.part, a.fine)
