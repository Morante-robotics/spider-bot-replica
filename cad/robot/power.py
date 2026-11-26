"""Power parts of cad/robot (plan.json): the 2S3P AG13 cell holder (post + post-cap tongues that cap crank 4, front tab
screwed into drive block 2 / ear 2, front-bottom notch round block 2), its snap lid, and the bought parts as hardware
from their datasheets: 6 x AG13, 3 conical springs + nickel strip, SS12D00 switch, two 5 mm LEDs + resistors, JST-XH.

    ../../.venv/bin/python power.py [--part cell-holder] [--fine]

Every layout number is the plan's probe (fitcheck/check.py LAYOUT, read by shells.CL), every clearance cad/fits.py.
The drive interface (crank 4 slot, spine wall tops under the post, drive block / ear 2) is derived from the same probe
here until drive.py publishes it: `iface()` prefers drive.py's constants when they exist (never edited here).
Robot frame, mm: x right, y back, z up.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT, ROOT + "/cad", HERE, HERE + "/fitcheck"):
    if p not in sys.path: sys.path.insert(0, p)
from build123d import Box, Cylinder, Cone, Sphere, Pos, Rot, Align, Compound, Polygon, extrude, Plane
from cad import common, fits as F
import fit_env as FE
import shells as SH

CL, S, P, motion = SH.CL, FE.S, FE.P, FE.motion
OUT = SH.OUT
MIN = (Align.MIN, Align.MIN, Align.MIN)

# ---------------------------------------------------------------- drive interface (probe; drive.py when published)
def iface():
    """Crank centres, spine wall x faces and tops, crank-4 slot, drive block / ear 2: drive.py's numbers if it
    publishes them (POWER_IFACE dict), else the plan's probe (fitcheck/check.py gear layout, same sources)."""
    try:
        import drive
        if hasattr(drive, "POWER_IFACE"): return dict(drive.POWER_IFACE)
    except ImportError:
        pass
    M, ZT, ZS, W, GW = 0.6, 12, 15, CL.W, CL.GW         # check.py: m 0.6, 12 T cranks/idlers, 15 T transfer small
    rp = lambda z: M * z / 2; rt = lambda z: M * z / 2 + M
    cc = lambda a, b: rp(a) + rp(b) + F.GEAR_BACKLASH / 2
    O = [motion.pivot(i, P)[1] for i in range(4)]; Oy = [float(o[1]) for o in O]; Oz = float(O[0][2])
    def zfor(gap):
        for z in range(12, 40):
            if cc(ZT, z) ** 2 - (gap / 2) ** 2 >= 4.0: return z
    ZI = [zfor(Oy[i + 1] - Oy[i]) for i in range(3)]
    def idler(y1, y2, r):
        d = y2 - y1; h = math.sqrt(max(r * r - (d / 2) ** 2, 0)); return ((y1 + y2) / 2, Oz + h)
    I = [idler(Oy[i], Oy[i + 1], cc(ZT, ZI[i])) for i in range(3)]
    gx = GW / 2; wx0 = gx + F.GEAR_THRUST_CRANK.side; wx1 = wx0 + W
    ytop = max(c[1] + 1.0 + F.STEEL.side + W for c in I)              # spine wall top (idler M2 + STEEL + wall)
    a = math.radians(CL.TANG); T = (I[1][0] + cc(ZS, ZI[1]) * math.cos(a), I[1][1] + cc(ZS, ZI[1]) * math.sin(a))
    def top_below(y):
        t = [c[1] + rt(ZI[i]) for i, c in enumerate(I) if abs(c[0] - y) < rt(ZI[i]) + 2.6] + \
            [Oz + rt(ZT) for o in Oy if abs(o - y) < rt(ZT) + 2.6]
        return max(t + [ytop])
    y2 = T[0] + CL.DSY2; zb2 = top_below(y2) + F.GEAR_TIP.side
    def tip_over(y0, y1, n=61):                       # highest gear tip + GEAR_TIP over y0..y1 (check.py _tip_over)
        best = ytop
        for k in range(n):
            y = y0 + (y1 - y0) * k / (n - 1)
            for (c0, c1), R in [(c, rt(ZI[i]) + F.GEAR_TIP.side + 0.03) for i, c in enumerate(I)] + \
                               [((o, Oz), rt(ZT) + F.GEAR_TIP.side + 0.03) for o in Oy]:
                if abs(y - c0) < R: best = max(best, c1 + math.sqrt(R * R - (y - c0) ** 2))
        return best
    return dict(Oy=Oy, Oz=Oz, wx0=wx0, wx1=wx1, ytop=ytop, tip_over=tip_over, JR=1.5,
                EAR2=((-2.6, y2 - CL.DBH, CL.DZT), (2.6, y2 + CL.DBH, CL.DZT + CL.EARH2)),
                BLOCK2=((-wx1, y2 - CL.DBH, zb2), (wx1, y2 + CL.DBH, CL.DZT)), DZT=CL.DZT)

D = iface()
K = SH.FE.K                                           # printed sizes set at S 0.70 grow with S
W = CL.W                                              # wall fits.WALL_MIN (loaded, rules 3.2)
# ---------------------------------------------------------------- cells, contacts (datasheets) and holder box (probe)
CELL_D, CELL_H = 11.6, 5.4                            # AG13 / LR44: Ø11.6 x 5.4 (IEC LR44 datasheet)
CY, CZ = CL.PY, CL.PZ                                 # cells' centre (probe LAYOUT PY 14.4, PZ 31)
PD = CELL_D + 2 * F.STEEL.side                        # cradle Ø: cell + STEEL a side (bought part in printed seat)
PITCH = PD + 0.8 * K                                      # 3 stacks side by side, 0.8 rib (two lines) between cradles
SPR = CL.SPR                                          # conical spring compressed length 2.0
SPR_R0, SPR_R1 = 3.5, 2.0                             # conical spring Ø7 base on the wall -> Ø4 on the cell (to buy)
STRIP_T = 0.3                                         # nickel strip 0.3 thick (to buy, probe)
L_IN = 2 * CELL_H + SPR + STRIP_T + 2 * F.STEEL.side  # inner length along y
HX = 1.5 * PITCH - 0.4 * K + W; HY = L_IN / 2 + W         # outer half sizes (probe hx, hy)
Z0 = CZ - PD / 2 - W                                  # floor underside
ZT = CZ + PD / 2                                      # wall top = lid underside (cells' top + STEEL)
YF, YB = CY - HY, CY + HY                             # front / back outer faces
YFI, YBI = YF + W, YB - W                             # inner faces
XS = (-PITCH, 0.0, PITCH)
CYC = YBI - F.STEEL.side - STRIP_T - CELL_H           # cells' stack centre: pushed by the spring against the strip
NSX = CL.NSX                                          # strip half-width 18.5 (probe)
# ---------------------------------------------------------------- post, post cap, tab (probe, re-plan 2026-11-22)
OY4 = D["Oy"][3]
SLW = D["JR"] + F.TURN.side                           # slot 4 half-width (journal + TURN)
TG = SLW - F.TURN.side                                # cap tongue half-width in the slot (TURN a side)
ZTG = D["Oz"] + D["JR"] + F.TURN.side                 # tongue foot: journal top + TURN
ZHP = D["tip_over"](CY - 3, CY + 3)                   # post foot: over idler 3's tip + GEAR_TIP (spine walls raised to it)
PY1 = max(CY + 3, OY4 + SLW + W)                      # post cap's back end, over slot 4 + wall
(E2x0, E2y0, E2z0), (E2x1, E2y1, E2z1) = D["EAR2"]
(B2x0, B2y0, B2z0), (B2x1, B2y1, B2z1) = D["BLOCK2"]
HSYY = 0.5 * (E2y0 + E2y1)                            # holder M2 at ear 2's centre
TABHW = CL.TABHW                                      # tab half-width 2.6 (5.2 wide)
ZTB = E2z1; TABZ1 = ZTB + W                           # tab rests on ear 2's top (lowered, EARH2 1.0), 1.2 thick
M3_D, M3_HEAD_D, M3_HEAD_H = 3.0, 5.5, 3.0            # ISO 4762 M3: head Ø5.5 x 3.0
M3_L = 8.0                                            # M2 x 6 (was x 8): 0.4 tab + 5.6 into ear 2 / block 2, tip 0.5 above the block's floor
HOLE_R = M3_D / 2 + F.STEEL.side                      # tab hole: shank + STEEL
CB_R, CB_D = M3_HEAD_D / 2 + F.STEEL.side, 0.8 * K        # head counterbored 0.8 into the tab: the N10's underside (z 29.79) clears the head
BZ = TABZ1 - CB_D                                     # head bearing face (tab left 0.4 under it)
NOTCH = F.WINDOW.side                                 # front-bottom notch round block 2 / ear 2 (fixed printed part passed by)
SEAT_W, SEAT_H = 0.8 * K, 0.8 * K                             # spring seat ring: 0.8 wall (two lines), 0.8 high
WIRE_W, WIRE_D = 2.0, 1.5                             # wire slots in the wall tops (spring bus front, strip back), m3
# ---------------------------------------------------------------- lid: plate, 2 front snap lips inside, 2 back lips outside
LIDT = CL.LIDT                                        # 1.2
JZ = ZT + LIDT + 11.5 / 2                             # JST pair stands on the lid (probe CL.JZ 43.5 put it 0.4 into the lid)
LIP_T, LIP_L, LIP_W = 0.8 * K, 3.5 * K, 4.0 * K                   # snap lip: 0.8 thick (two lines), 3.5 long, 4 wide
LIP_X = PITCH / 2                                     # between the springs / cell columns
BUMP = 0.2 + F.LOCATOR.side                           # bump proud of the lip: 0.2 engagement past the LOCATOR gap
BUMP_H = 0.8 * K                                          # bump height (45 deg both faces: snaps on, pulls off)
EPS_SNAP = 1.5 * LIP_T * (BUMP - F.LOCATOR.side) / LIP_L ** 2   # y = eps L^2 / (1.5 t): 1.96 % (<= 2 %, rules 3.2)
GROOVE = BUMP                                         # groove depth: the bump reaches 0.2 past the face, + LOCATOR 0.2
PLUS, PLUS_T, PLUS_D = 3.0 * K, 0.8 * K, 0.4 * K                  # '+' engraved on the back wall's outer face (wall left 0.8)
KEY_END = 0.6 * K                                         # back wall left outside the key notch (a pocket, not through): the key's +y stop
KEY_X, KEY_W, KEY_H = 10.0 * K, 3.0 * K, 1.0 * K                  # x-locating key in a notch on the back wall top (LOCATOR a side)

def lip_bump(y_face, sgn, x0, x1, zc):
    """45 deg ridge on a lip face at y_face, pointing sgn (+1 / -1 in y), x0..x1, centred at zc: BUMP proud."""
    yo = y_face - sgn * 0.1                           # 0.1 rooted in the lip: a face-only touch left 4 loose solids (not watertight)
    pts = [(yo, zc - BUMP_H / 2), (y_face, zc - BUMP_H / 2), (y_face + sgn * BUMP, zc - BUMP_H / 2 + BUMP),
           (y_face + sgn * BUMP, zc + BUMP_H / 2 - BUMP), (y_face, zc + BUMP_H / 2), (yo, zc + BUMP_H / 2)]
    face = Plane.YZ * Polygon(*pts, align=None)
    return Pos(x1, 0, 0) * extrude(face, amount=x1 - x0)          # Plane.YZ's extrusion runs toward -x from x1

def holder():
    b = Pos(-HX, YF, Z0) * Box(2 * HX, 2 * HY, ZT - Z0, align=MIN)
    b -= Pos(-HX + W, YFI, CZ) * Box(2 * (HX - W), 2 * (HY - W), ZT - CZ + 1, align=MIN)            # open top
    for x in XS:                                                                                      # cradles
        b -= Pos(x, YFI, CZ) * Rot(-90, 0, 0) * Cylinder(PD / 2, YBI - YFI, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # post and post cap down to the spine wall tops, tongues into slot 4 (cap crank 4)
    b += Pos(-D["wx1"], CY - 3, ZHP) * Box(2 * D["wx1"], PY1 - (CY - 3), Z0 - ZHP + 0.01, align=MIN)
    for xa in (D["wx0"], -D["wx1"]):
        b += Pos(xa, OY4 - TG, ZTG) * Box(D["wx1"] - D["wx0"], 2 * TG, ZHP - ZTG + 0.01, align=MIN)
    # front tab on drive ear 2, M2 hole (STEEL), lead-in chamfer is the hole's countersink-free top (head seats flat)
    b += Pos(-TABHW, HSYY - TABHW, ZTB) * Box(2 * TABHW, YFI - (HSYY - TABHW), W, align=MIN)
    b -= Pos(0, HSYY, ZTB - 1) * Cylinder(HOLE_R, W + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b -= Pos(0, HSYY, BZ) * Cylinder(CB_R, CB_D + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # front-bottom notch round drive block 2 / ear 2 (WINDOW), open to the underside: lifts off +z
    nx = max(E2x1, B2x1) + NOTCH
    ny, nz = max(E2y1, B2y1) + NOTCH - (YF - 1), ZTB - (Z0 - 1)
    if min(nx, ny, nz) > 0:                       # at S 1.0 the block may not reach the holder: no notch
        b -= Pos(-nx, YF - 1, Z0 - 1) * Box(2 * nx, ny, nz, align=MIN)
    else:
        print(f"    holder: block-2 notch not cut (nx {nx:.2f}, ny {ny:.2f}, nz {nz:.2f})")
    # spring seats: a ring on the front wall's inner face holds each spring's Ø7 base (STEEL a side, 0.8 high)
    for x in XS:
        b += Pos(x, YFI - 0.01, CZ) * Rot(-90, 0, 0) * (Cylinder(SPR_R0 + F.STEEL.side + SEAT_W, SEAT_H + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                       - Cylinder(SPR_R0 + F.STEEL.side, SEAT_H + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    # wire slots in the wall tops at x 0: spring bus (front), strip lead (back)
    for y0 in (YF - 0.5, YBI - 0.5):
        b -= Pos(-WIRE_W / 2, y0, ZT - WIRE_D) * Box(WIRE_W, W + 1, WIRE_D + 1, align=MIN)
    # lid snap grooves: front wall inner face (x +-LIP_X), back wall outer face; x key notch on the back wall top
    zc = ZT - LIP_L + 0.4 + BUMP_H / 2
    for sx in (1, -1):
        x0, x1 = sx * LIP_X - LIP_W / 2 - F.LOCATOR.side, sx * LIP_X + LIP_W / 2 + F.LOCATOR.side
        g0, g1 = zc - BUMP_H / 2 - F.LOCATOR.side, zc + BUMP_H / 2 + F.LOCATOR.side
        b -= Pos(x0, YFI - GROOVE, g0) * Box(x1 - x0, GROOVE + 0.01, g1 - g0, align=MIN)
        b -= Pos(x0, YB - GROOVE, g0) * Box(x1 - x0, GROOVE + 0.01, g1 - g0, align=MIN)
    b -= Pos(KEY_X - KEY_W / 2, YBI - 0.5, ZT - KEY_H) * Box(KEY_W, W - KEY_END + 0.5, KEY_H + 1, align=MIN)
    for bx, bz in ((PLUS, PLUS_T), (PLUS_T, PLUS)):                                            # '+' mark: polarity
        b -= Pos(-PITCH - bx / 2, YB - PLUS_D, CZ - bz / 2) * Box(bx, PLUS_D + 0.5, bz, align=MIN)
    assert len(b.solids()) == 1 and b.is_valid, f"cell-holder: {len(b.solids())} solids"
    return b

def lid():
    l = Pos(-HX, YF, ZT) * Box(2 * HX, 2 * HY, LIDT, align=MIN)
    zc = ZT - LIP_L + 0.4 + BUMP_H / 2
    for sx in (1, -1):
        x0, x1 = sx * LIP_X - LIP_W / 2, sx * LIP_X + LIP_W / 2
        yf = YFI + F.LOCATOR.side                                       # front lip: inside the front wall
        l += Pos(x0, yf, ZT - LIP_L) * Box(LIP_W, LIP_T, LIP_L + 0.01, align=MIN)
        l += lip_bump(yf, -1, x0, x1, zc)
        yb = YB + F.LOCATOR.side                                        # back lip: outside the back wall, pull tab
        l += Pos(x0, YB, ZT) * Box(LIP_W, yb + LIP_T - YB, LIDT, align=MIN)
        l += Pos(x0, yb, ZT - LIP_L) * Box(LIP_W, LIP_T, LIP_L + 0.01, align=MIN)
        l += lip_bump(yb, -1, x0, x1, zc)
    k0 = KEY_X - KEY_W / 2 + F.LOCATOR.side
    l += Pos(k0, YBI, ZT - (KEY_H - F.LOCATOR.side)) * Box(KEY_W - 2 * F.LOCATOR.side, W - KEY_END - F.LOCATOR.side, KEY_H - F.LOCATOR.side + 0.01, align=MIN)
    return l

# ---------------------------------------------------------------- hardware (datasheets)
def cells():
    out = []
    for x in XS:                                      # each stack of 2 as one cylinder (two faces touching would not export watertight)
        out.append(Pos(x, CYC - CELL_H, CZ) * Rot(-90, 0, 0) * Cylinder(CELL_D / 2, 2 * CELL_H, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return Compound(out)

def springs():
    y0 = YFI + F.STEEL.side
    return Compound([Pos(x, y0, CZ) * Rot(-90, 0, 0) * Cone(SPR_R0, SPR_R1, SPR, align=(Align.CENTER, Align.CENTER, Align.MIN)) for x in XS])

def strip():
    return Pos(-NSX, YBI - F.STEEL.side - STRIP_T, CZ + 0.2) * Box(2 * NSX, STRIP_T, ZT - 0.25 - CZ - 0.2, align=MIN)   # above the cradle ribs (z >= CZ), under the lid

def holder_screw():
    return Compound([Pos(0, HSYY, BZ - M3_L) * Cylinder(M3_D / 2, M3_L, align=(Align.CENTER, Align.CENTER, Align.MIN)),
                     Pos(0, HSYY, BZ) * Cylinder(M3_HEAD_D / 2, M3_HEAD_H, align=(Align.CENTER, Align.CENTER, Align.MIN))])

# SS12D00G3 slide switch (datasheet): body 8.6 x 3.6 x 3.5, lever 1.5 x 1.5 x 3.0 proud; pins bendable (no volume)
SW_BODY, SW_LEVER = (8.6, 3.5, 3.6), (1.5, 3.0, 1.5)  # (x, y, z): y along the lever, out through the body's back wall
SWZ = CL.SWZ                                          # probe SWZ 22
SW_PROUD = 1.0                                        # lever tip stands out of the body's outer skin by this much (a thumb)
def _skin_y(z, ob):
    """body skin y at x 0 (robot frame), z: ob 'out' = outer skin (the control table's back meridian), 'in' = inner skin (probe rows)."""
    import numpy as np
    from scipy.interpolate import PchipInterpolator
    zj = z / S + motion.ORIGIN[2]
    if ob == "in": zs, R = FE.BODY_ROWS; yj = np.interp(zj, zs, R[:, 2])
    else: c = np.array(SH.BO.SKIN_CTRL, float); yj = PchipInterpolator(c[:, 0], c[:, 1:], axis=0)(zj)[2]
    return float((yj - motion.ORIGIN[1]) * S)
SWY_IN = _skin_y(SWZ, "in")                           # body inner back face at the switch (34.2)
# the lever's upper edge meets the sloped outer skin highest (skin leans back with z): tip = outer there + SW_PROUD, so the body
# of the switch sits SWY1 - SWY_IN deep in the wall (pocket in the wall, lever through the slot)
SWY1 = _skin_y(SWZ + SW_LEVER[2] / 2, "out") + SW_PROUD - SW_LEVER[1]
def switch():
    bx, by, bz = SW_BODY; lx, ly, lz = SW_LEVER
    return Compound([Pos(-bx / 2, SWY1 - by, SWZ - bz / 2) * Box(bx, by, bz, align=MIN),
                     Pos(-lx / 2, SWY1, SWZ - lz / 2) * Box(lx, ly, lz, align=MIN)])

# 5 mm LEDs (datasheet: Ø5 dome/body, flange Ø5.8 x 1, 8.6 overall) in the big eyes' bores (shells.led_pos, flange on the floor's
# back face LEDF behind the bore floor, dome forward in the bore); 1/4 W resistors Ø2.3 x 6.5 upright behind them (leads bendable, no volume)
LED_D, LED_FL_D, LED_FL_H, LED_H = 5.0, 5.8, 1.0, 8.6
RES_D, RES_L, RES_GAP = 2.3, 6.5, 2.0
RES_Z0 = LED_FL_D / 2 + 0.1                           # resistor's foot just above the LED flange (leads bent up, as the probe's RYO layout)
BO = SH.BO
def led_axis(sx):
    x, y, z = SH.led_pos(sx)
    return x, y + SH.LEDF + F.LOCATOR.side - (LED_H - LED_FL_H), z      # dome tip: the flange's front face LOCATOR off the floor's back face
def leds():
    out = []
    for sx in (1, -1):
        x, tip, z = led_axis(sx)
        body = (Pos(x, tip + LED_D / 2, z) * Sphere(LED_D / 2)                        # dome + barrel + flange fused (rooted 0.01:
                + Pos(x, tip + LED_D / 2, z) * Rot(-90, 0, 0) * Cylinder(LED_D / 2, LED_H - LED_D / 2 - LED_FL_H + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
                + Pos(x, tip + LED_H - LED_FL_H, z) * Rot(-90, 0, 0) * Cylinder(LED_FL_D / 2, LED_FL_H, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        out += [body, Pos(x, tip + LED_H + RES_GAP / 2 + RES_D / 2, z + RES_Z0) * Cylinder(RES_D / 2, RES_L, align=(Align.CENTER, Align.CENTER, Align.MIN))]   # upright up the block's back face, as the probe has it
    return Compound(out)

# JST-XH 3-pin mated pair (datasheet: housing 9.9 x 5.75, 2.5 pitch; mated height ~ 11.5 incl. plug), along x (probe JX/JY/JZ)
JST = (9.9, 5.8, 11.5)
def jst():
    jx, jy, jz = JST
    return Pos(CL.JX - jx / 2, CL.JY - jy / 2, JZ - jz / 2) * Box(jx, jy, jz, align=MIN)

PARTS = {"cell-holder": holder, "cell-lid": lid}
HARDWARE = {"ag13-cells": cells, "cell-springs": springs, "nickel-strip": strip, "holder-screw": holder_screw,
            "ss12d00-switch": switch, "leds": leds, "jst-xh": jst}

def write_all(names=None, fine=False):
    for n in names or list(PARTS) + list(HARDWARE):
        sh = (PARTS.get(n) or HARDWARE[n])()
        common.export(n, sh, OUT, fine=fine)
        print(f"    {n}: {len(sh.solids())} solid(s), valid {sh.is_valid}, {sh.volume:.0f} mm3"
              + (f", {sh.volume * 1.24e-3:.1f} g PLA" if n in PARTS else ""), flush=True)

if __name__ == "__main__":
    a = common.part_args(__doc__, {**PARTS, **HARDWARE})
    write_all(a.part, a.fine)
    print(f"snap lip strain {EPS_SNAP * 100:.2f} %, post foot z {ZHP:.2f}, tab z {ZTB:.2f}, M2 y {HSYY:.2f}, notch to y {max(E2y1, B2y1) + NOTCH:.2f}")
