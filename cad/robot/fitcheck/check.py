"""The whole robot's fit check (N2): every part, screw, contact and resistor as sampled solids on the parametric body
and base sections (fit_env.py, no mesh), the real cad/legs parts over 24 crank poses (fit_legs.py), the body's lift-off
path, each part's assembly path and each screw's driver line. Every gap signed against its cad/fits.py clearance, least
margin first; a gap within 0.1 mm under its need is «at tolerance» (sampling noise), not a FAIL.

Which clearance a pair needs (need()): a moving leg LEG_PATH; a gear GEAR_TIP; the crankshafts TURN; the shell (a large
part) LOCATOR; a bought part against a printed one STEEL; bendable leads, wires and springs among bought parts only no
overlap; two fixed printed parts NEIGHBOUR. Assembly paths need NEIGHBOUR (the running fit is checked in place).
Wires take no volume (spec.json must-haves). The layout knobs (LAYOUT below) can be overridden from the environment.

    uv run python cad/robot/fitcheck/check.py > cad/robot/fitcheck/out/report.txt    # ≈ 8 min (2 cores), ≈ 10 min cold
Progress goes to stderr; out/rows.json holds every row, out/window_old_vs_new.png the leg-window comparison.
"""
import sys, os, math, itertools, json, time
_t0 = time.time()
def tick(m): print(f"[{time.time() - _t0:5.1f}s] {m}", file=sys.stderr)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# the layout chosen at the S 0.70 probe of 2026-11-21 (env values, overridable)
LAYOUT = dict(MANG=78, PY=14.4, PZ=31, TANG=107.5, DSY1=8.3, DSY2=8.075, DBH=2.45, SWZ=22, JZ=43.5, WEBW=0.55, KEELFIX=1,
              HSZ=1, RYO=1.3, CLX1=-2.1, CTX0=-7.0, NSX=18.5, BSA=44, PR=2.35, SNT=0.8, RIBD=0.9, SNZ=9, N=70)
for _k, _v in LAYOUT.items(): os.environ.setdefault(_k, str(_v))
from fit_env import *
import fit_legs as LR
from fit_samplers import cyl_ax, swept_x
E = lambda k, d: float(os.environ.get(k, d))
# ---------------- gear train: module from the scale, m 1 proven at 120 % -> 0.583 at 70 % -> m 0.6
M = 0.6; ZT = 12; ZP = 16; ZB = 20; ZS = 15; W = 1.2; GW = 3.0
rp = lambda z: M * z / 2; rt = lambda z: M * z / 2 + M
O = [motion.pivot(i, P)[1] for i in range(4)]; Oy = [o[1] for o in O]; Oz = O[0][2]
def zfor(gap):                                       # smallest idler (>= 12 T) that bridges two crank gears with h >= 2
    for z in range(12, 40):
        c = rp(ZT) + rp(z) + F.GEAR_BACKLASH / 2
        if c * c - (gap / 2) ** 2 >= 4.0: return z
ZI = [zfor(Oy[i + 1] - Oy[i]) for i in range(3)]
def idler(c1, c2, r1, r2, up=True):
    (y1, z1), (y2, z2) = c1, c2; d = math.hypot(y2 - y1, z2 - z1); a = (r1**2 - r2**2 + d*d) / (2*d); h = math.sqrt(max(r1*r1 - a*a, 0))
    ym, zm = y1 + a*(y2 - y1)/d, z1 + a*(z2 - z1)/d; s = 1 if up else -1
    return (ym - s*h*(z2 - z1)/d, zm + s*h*(y2 - y1)/d)
cc = lambda za, zb: rp(za) + rp(zb) + F.GEAR_BACKLASH / 2
I = [idler((Oy[i], Oz), (Oy[i + 1], Oz), cc(ZT, ZI[i]), cc(ZT, ZI[i])) for i in range(3)]
IDL_T = 0.2                                          # idlers and transfer-small are GW - 0.4 wide, centred: each face GEAR_THRUST_IDLER (0.45) to the spine walls
TH = F.GEAR_THRUST_CRANK.side; gx = GW / 2; wx0, wx1 = gx + TH, gx + TH + W
ST, MV, BD, HW = {}, {}, {}, set()
JR = 1.5                                             # printed crank journal r (Ø3) in the spine walls, TURN
PINR = 1.5                                           # printed crank pin Ø3 (no steel pin)
WEB_T = 1.2; wb0 = wx1 + TH; wb1 = wb0 + WEB_T       # webs just outside the walls
for i in range(4): MV[f"crank-gear-{i+1}"] = cyl_x(Oy[i], Oz, rt(ZT), -gx, gx)
for i, c in enumerate(I): MV[f"idler-{i+1}"] = cyl_x(c[0], c[1], rt(ZI[i]), -gx + IDL_T, gx - IDL_T)
IPR = 1.0                                            # idler axle: M2 screw (steel) through both walls
ytop = max(c[1] + IPR + F.STEEL.side + W for c in I)
zsp0 = Oz - JR - F.TURN.side - W - 0.3
SPF, SPB = E("SPF", 3.2), E("SPB", 3.2)
KY = E("KY", 5.0)                                    # keel under the spine to the bowl floor, 2 M2 from below
KEELFIX = E("KEELFIX", 1)                            # 1: keel top under the gear tips (Oz - tip - GEAR_TIP), walls down to it
KSLOT = E("KSLOT", F.TURN.side)                      # each crank journal rests on its slot bottom: gear TURN lower than centred
zk1 = min(zsp0, Oz - rt(ZT) - F.GEAR_TIP.side - KSLOT) if KEELFIX else zsp0
ST["spine"] = np.vstack([box((wx0 if sx > 0 else -wx1, min(Oy) - SPF, zsp0), (wx1 if sx > 0 else -wx0, max(Oy) + SPB, ytop)) for sx in (1, -1)]
                        + ([box((wx0 if sx > 0 else -wx1, -KY, zk1), (wx1 if sx > 0 else -wx0, KY, zsp0)) for sx in (1, -1)] if KEELFIX else []))
ST["spine-keel"] = box((-wx1, -KY, 2.0), (wx1, KY, zk1 - 0.01))
for i, c in enumerate(I): ST[f"idler-axle-{i+1}"] = cyl_x(c[0], c[1], IPR, -wx1 - 1.2, wx1 + 0.3); HW.add(f"idler-axle-{i+1}")
for k, y in enumerate((-KY + 1.8, KY - 1.8)):
    ST[f"keel-screw-{k+1}"] = np.vstack([cyl_z(0, y, 1.0, -0.5, 6.0), cyl_z(0, y, 1.9, -1.8, -0.5)]); HW.add(f"keel-screw-{k+1}")
# transfer compound above idler TI; pinion on the N10 along -x; drive unit screwed to the spine top
ti = int(E("TI", 1)); a = math.radians(E("TANG", 90)); T = (I[ti][0] + cc(ZS, ZI[ti]) * math.cos(a), I[ti][1] + cc(ZS, ZI[ti]) * math.sin(a))
XB0 = E("XB0", wx1 + F.GEAR_AXIAL.side)
MV["transfer-small"] = cyl_x(T[0], T[1], rt(ZS), -gx + IDL_T, gx - IDL_T); MV["transfer-big"] = cyl_x(T[0], T[1], rt(ZB), XB0, XB0 + GW)
ST["transfer-axle"] = cyl_x(T[0], T[1], 1.0, -wx1, XB0 + GW + F.GEAR_AXIAL.side + W); HW.add("transfer-axle")
ma = math.radians(E("MANG", 60)); Mc = (T[0] + cc(ZB, ZP) * math.cos(ma), T[1] + cc(ZB, ZP) * math.sin(ma))
MV["pinion"] = cyl_x(Mc[0], Mc[1], rt(ZP), XB0, XB0 + GW)
mx1 = XB0 - F.GEAR_AXIAL.side; mx0 = mx1 - 21.0
ST["n10-motor"] = box((mx0, Mc[0] - 6, Mc[1] - 5), (mx1, Mc[0] + 6, Mc[1] + 5)); HW.add("n10-motor")
ST["n10-shaft"] = cyl_x(Mc[0], Mc[1], 1.5, mx1, XB0 + GW); HW.add("n10-shaft")
ST["motor-leads"] = box((mx0 - 2.5, Mc[0] - 3, Mc[1] - 2), (mx0, Mc[0] + 3, Mc[1] + 2)); HW.add("motor-leads")
DSY_ = E("DSY", 8.0); DZT = E("DZT", 26.0)
g = F.MOTOR_SEAT.side + W; xo = XB0 + GW + F.GEAR_AXIAL.side
CLX1 = min(mx1, E("CLX1", mx1))                     # lower clamp stops here in x
ST["drive-unit"] = np.vstack([box((mx0 + 3, Mc[0] - 6 - g, Mc[1] - 5 - g), (CLX1, Mc[0] + 6 + g, Mc[1] - 5 - F.MOTOR_SEAT.side)),
    box((max(mx0 + 3, E("CTX0", mx0 + 3)), Mc[0] - 6 - g, Mc[1] + 5 + F.MOTOR_SEAT.side), (mx1, Mc[0] + 6 + g, Mc[1] + 5 + g)),
    box((xo, min(T[0], Mc[0]) - 3, min(T[1], Mc[1]) - 3), (xo + W, max(T[0], Mc[0]) + 3, max(T[1], Mc[1]) + 3)),
    box((-wx1 - W, min(T[0], Mc[0]) - E("DSY1", DSY_) - 2.6, DZT), (-wx1, max(T[0], Mc[0]) + 3, T[1] + 3)),               # web to the ears
    box((-wx1 - W, T[0] - 3, T[1] - 3), (-wx1, T[0] + 3, T[1] + 3))])                                       # inner cheek
DSY = E("DSY", 8.0); DZT = E("DZT", 26.0)          # drive unit screws: 2 M2 down into solid blocks between the walls
def _top_below(y):                                   # highest gear tip under y (between the walls)
    t = [c[1] + rt(ZI[i]) for i, c in enumerate(I) if abs(c[0] - y) < rt(ZI[i]) + 2.6] + [Oz + rt(ZT) for o in Oy if abs(o - y) < rt(ZT) + 2.6]
    return max(t + [ytop])
DBH = E("DBH", 2.6); ZB, YB = [], []                                  # block / ear half-length in y
for k, y in enumerate((T[0] - E("DSY1", DSY), T[0] + E("DSY2", DSY))):
    zb = _top_below(y) + F.GEAR_TIP.side
    y0b = y - DBH; ZB.append(zb); YB.append((y0b, y + DBH))
    ST[f"drive-block-{k+1}"] = box((-wx1, y0b, zb), (wx1, y + DBH, DZT - 0.01))
    hs_ = E("HSINK2", 0.3) if k == 1 else 0.0            # screw 2's head counterbored into its ear (local reshape: N10 clearance)
    ST[f"drive-screw-{k+1}"] = np.vstack([cyl_z(0, y, 1.0, max(DZT - 5.0, zb + 0.01), DZT + 2.4 - hs_), cyl_z(0, y, 1.9, DZT + 2.4 - hs_, DZT + 3.8 - hs_)]); HW.add(f"drive-screw-{k+1}")
    ST[f"drive-ear-{k+1}"] = box((-2.6, y - DBH, DZT), (2.6, y + DBH, DZT + 2.4 - 0.01))
# cells: 3 stacks of 2 AG13 lying along y, side by side along x; conical spring + nickel strip; lid on top
cy, cz = E("PY", 12.0), E("PZ", 30.0); pd = 11.6 + 2 * F.STEEL.side; pitch = pd + 0.8
SPR = E("SPR", 2.0)                                  # conical spring compressed
L = 2 * 5.4 + SPR + 0.3 + 2 * F.STEEL.side
hx = 1.5 * pitch - 0.4 + W; hy = L / 2 + W
ST["cell-holder"] = np.vstack([box((-hx, cy - hy, cz - pd/2 - W), (hx, cy + hy, cz)),
    box((-hx, cy - hy, cz), (-hx + W, cy + hy, cz + pd/2)), box((hx - W, cy - hy, cz), (hx, cy + hy, cz + pd/2)),
    box((-hx, cy - hy, cz), (hx, cy - hy + W, cz + pd/2)), box((-hx, cy + hy - W, cz), (hx, cy + hy, cz + pd/2))])
LIDT = E("LIDT", 1.2)
ST["cell-lid"] = box((-hx, cy - hy, cz + pd/2 + 0.01), (hx, cy + hy, cz + pd/2 + LIDT))
_cq = cyl_x(0.0, cz, 5.8, -5.4, 5.4)
ST["ag13-cells"] = np.vstack([np.c_[_cq[:, 1] + xs, _cq[:, 0] + cy + sy * 2.85, _cq[:, 2]] for xs in (-pitch, 0, pitch) for sy in (-1, 1)]) if False else \
    np.vstack([np.c_[_cq[:, 1] + xs, _cq[:, 0] * (10.8 / 10.8) + cy, _cq[:, 2]] for xs in (-pitch, 0, pitch)])
HW.add("ag13-cells")
ST["cell-springs"] = np.vstack([cyl_ax((xs, cy - L/2 + F.STEEL.side, cz), (xs, cy - L/2 + F.STEEL.side + SPR, cz), 3.5) for xs in (-pitch, 0, pitch)]); HW.add("cell-springs")
NSX = E("NSX", 1.5 * pitch + 4)                     # strip half-width (inside the holder's back wall: hx - W - STEEL)
ST["nickel-strip"] = box((-NSX, cy + L/2 - F.STEEL.side - 0.3, cz - 4), (NSX, cy + L/2 - F.STEEL.side, cz + 4)); HW.add("nickel-strip")
HNOTCH = E("HNOTCH", 1)                              # local notch in the cell holder's front-bottom edge round drive block/ear/screw 2
HNOTCH_D = 0.0
if HNOTCH:
    HB = [((-hx, cy - hy, cz - pd/2 - W), (hx, cy + hy, cz)), ((-hx, cy - hy, cz), (-hx + W, cy + hy, cz + pd/2)), ((hx - W, cy - hy, cz), (hx, cy + hy, cz + pd/2)),
          ((-hx, cy - hy, cz), (hx, cy - hy + W, cz + pd/2)), ((-hx, cy + hy - W, cz), (hx, cy + hy, cz + pd/2))]
    inb = lambda q, lo, hi, e=0: np.all((q > np.asarray(lo) + e) & (q < np.asarray(hi) - e), axis=1)
    in_h = lambda q: np.any([inb(q, a, b) for a, b in HB], axis=0)
    _hq = ST["cell-holder"]; NOTCHES = []
    for _n, _g in (("drive-block-2", 0.55), ("drive-ear-2", 0.55), ("drive-screw-2", 0.2), ("drive-unit", 0.55)):
        _d = cKDTree(_hq).query(ST[_n])[0]; s_ = ST[_n][_d < _g + E("HNS", 1.2)]
        if not len(s_): continue
        lo_, hi_ = s_.min(0) - _g, s_.max(0) + _g; lo_ = np.maximum(lo_, HB[0][0]); hi_ = np.minimum(hi_, (hx, cy + hy, cz + pd/2))
        if E("HOPEN", 1): lo_[2] = HB[0][0][2]               # notch open to the holder's underside: it lifts off +z
        NOTCHES.append((_n, np.round(lo_, 2), np.round(hi_, 2)))
        f_ = box(lo_, hi_, 0.25); _hq = np.vstack([_hq[~inb(_hq, lo_ - 0.02, hi_)], f_[in_h(f_)]])
        HNOTCH_D = max(HNOTCH_D, float(hi_[1] - (cy - hy)))
    ST["cell-holder"] = _hq
    SPRING_Y0 = cy - L/2 + F.STEEL.side
HSY = E("HSY", 0.0)
HSZ = E("HSZ", 0)                                    # 1: post down to the gear tips + GEAR_TIP, screw ends in it
def _tip_over(y0, y1):                               # highest gear tip anywhere over the span y0..y1 (between the walls)
    yy = np.linspace(y0, y1, 61); t = [ytop]
    for (c0, c1), R in [(c, rt(ZI[i]) + F.GEAR_TIP.side + 0.03) for i, c in enumerate(I)] + [((o, Oz), rt(ZT) + F.GEAR_TIP.side + 0.03) for o in Oy]:
        m = np.abs(yy - c0) < R
        if m.any(): t.append(float((c1 + np.sqrt(R * R - (yy[m] - c0) ** 2)).max()))
    return max(t)
zhp = _tip_over(cy + HSY - 3, cy + HSY + 3) if HSZ else ytop   # post foot over the whole footprint
SPRISE = max(0.0, zhp - ytop)                        # local reshape: spine walls raised under the post where idler 3's tip is above ytop
if SPRISE > 0:
    ST["spine"] = np.vstack([ST["spine"]] + [box((wx0 if sx > 0 else -wx1, cy + HSY - 3, ytop), (wx1 if sx > 0 else -wx0, cy + HSY + 3, zhp)) for sx in (1, -1)])
YB_END = YB[1][1]; ZCAP = min(ZB) + 0.0
ST["holder-post"] = box((-wx1, cy + HSY - 3, zhp), (wx1, cy + HSY + 3, cz - pd/2 - W - 0.01))     # the holder's foot on the spine top
SLW = JR + F.TURN.side                                # slot half-width (journal + TURN)
PY0 = cy + HSY - 3; PY1 = max(cy + HSY + 3, Oy[3] + SLW + W)
wtop = lambda y: np.where(np.abs(y - (cy + HSY)) <= 3, max(zhp, ytop), ytop)
def _slots(q):
    m = np.zeros(len(q), bool)
    for o in Oy: m |= ((np.abs(q[:, 1] - o) < SLW - 1e-6) & (q[:, 2] > Oz - 1e-6) | (np.hypot(q[:, 1] - o, q[:, 2] - Oz) < SLW - 1e-6)) & (np.abs(q[:, 0]) > wx0 - 1e-6) & (np.abs(q[:, 0]) < wx1 + 1e-6)   # U slot: straight sides and its round floor
    return m
_sq = ST["spine"]; _sf = []
for o in Oy:
    for sx in (1, -1):
        for x_ in np.linspace(wx0, wx1, 4) * sx:
            zt_ = float(wtop(o)); zz_ = np.arange(Oz, zt_, 0.25); _sf += [np.c_[np.full(len(zz_), x_), np.full(len(zz_), o + e_ * SLW), zz_] for e_ in (1, -1)]
            t_ = np.linspace(np.pi, 2 * np.pi, 25); _sf.append(np.c_[np.full(25, x_), o + SLW * np.cos(t_), Oz + SLW * np.sin(t_)])
ST["spine"] = np.vstack([_sq[~_slots(_sq)]] + _sf)
TG = SLW - F.TURN.side                                # cap tongue half-width in the slot (TURN a side)
ztg = Oz + JR + F.TURN.side                           # tongue foot over the journal (TURN)
cap = []
for sx in (1, -1):
    xa, xb = (wx0, wx1) if sx > 0 else (-wx1, -wx0)
    cap.append(box((xa, Oy[0] - SLW - W, ytop), (xb, YB_END, ZCAP)))            # cheek on the wall top, up to the blocks
    for i in range(3): cap.append(box((xa, Oy[i] - TG, ztg), (xb, Oy[i] + TG, ytop)))
ST["journal-caps"] = np.vstack(cap)
pc = []
for sx in (1, -1):
    xa, xb = (wx0, wx1) if sx > 0 else (-wx1, -wx0); pc.append(box((xa, Oy[3] - TG, ztg), (xb, Oy[3] + TG, zhp)))
pc.append(box((-wx1, cy + HSY + 3, zhp), (wx1, PY1, cz - pd/2 - W - 0.01)))
ST["post-cap"] = np.vstack(pc)
ST["holder-screw"] = np.vstack([cyl_z(0, cy + HSY, 1.0, (zhp + 0.01) if HSZ else ytop - 4, cz - pd/2), cyl_z(0, cy + HSY, 1.9, cz - pd/2, cz - pd/2 + 1.4)]); HW.add("holder-screw")
# leg pivots: the toy's notch: a ball on the leg root in the base wall window, held down by the body's rim
PB = P["r_root"]
# body screws: a pair M2 from below, through posts on the base wall into bosses under the body rim, at angle BSA
RIMR = (BO.Z_RIM - motion.ORIGIN[2]) * S
BSA = math.radians(E("BSA", 50.0))                  # from straight ahead (-y) towards +-x
def rim_inner(th):                                   # base band inner face at the rim, robot frame, direction th
    d = BASE_WALL_R / S; c, s_ = math.cos(th), math.sin(th); n = BA.N_TOP
    a_, b_ = A_L - 0.5 * d, B_L - 0.5 * d; rr = (abs(c / a_) ** n + abs(s_ / b_) ** n) ** (-1 / n)
    return j2r((BA.CX + rr * c, BA.CY + rr * s_, BA.Z_LEDGE))[:2]
HEADZ = []
# front: two snap fingers on the body (cantilever down from the rim, hook outward) under a rib on the base's front wall
# (spec must_have: snaps at the front; the screws there are boxed in). Rib top 45 deg lead, hook return 45 deg: pulls off.
SNX, SNW, SNT, SNZ, RIBD, SNG = E("SNX", 6.0), E("SNW", 5.0), E("SNT", 1.0), E("SNZ", 10.0), E("RIBD", 1.0), E("SNG", 0.3)
SNAPS = []
for k, sx in enumerate((1, -1)):
    xc = sx * SNX; zz_ = np.arange(SNZ, RIMR - 0.3, 0.2); yy_ = np.arange(-40, -20, 0.05)
    yw = max(yy_[inside(np.c_[np.full(len(yy_), xc), yy_, np.full(len(yy_), z_)])].min() for z_ in zz_)   # innermost wall face
    yf = yw + RIBD + SNG                                # finger outer face
    x0, x1 = xc - SNW / 2, xc + SNW / 2
    BD[f"snap-finger-{k+1}"] = np.vstack([box((x0, yf, SNZ), (x1, yf + SNT, RIMR)), box((x0, yw + F.WINDOW.side, SNZ), (x1, yf, SNZ + 0.8))])
    ST[f"snap-rib-{k+1}"] = box((x0 - 0.5, yw - 0.6, SNZ + 0.9), (x1 + 0.5, yw + RIBD, SNZ + 1.9))
    dl = (RIBD - F.WINDOW.side) + 0.1; Lf = RIMR - SNZ
    SNAPS.append((k, xc, yw, dl, Lf, 1.5 * SNT * dl / Lf ** 2))
# rear: the body's own tab behind the base's back sheet carries a snap rib (PRESS, coupon)
tw, ty0, ty1, tz = BO.TAB

def jbox(x0, x1, y0, y1, z0, z1):
    a_, b_ = j2r((x0, y0, z0)), j2r((x1, y1, z1)); return box(np.minimum(a_, b_), np.maximum(a_, b_))
_tab = jbox(BO.CX - tw, BO.CX + tw, ty0, ty0 + 3.0, tz, BO.Z_RIM)
_win = (np.abs(_tab[:, 0]) <= PKT[1] + 0.5) & (_tab[:, 2] >= PKT[2] - 0.5) & (_tab[:, 2] <= PKT[3] + 0.5)
BD["rear-tab"] = np.vstack([_tab[~_win], _tab[_win] + [0, PKT[0], 0],                 # notch: the tab's face 1.6 back in the window
                            box((-PKT[1] - 0.5, _tab[:, 1].min(), PKT[2] - 0.5), (PKT[1] + 0.5, _tab[:, 1].min() + PKT[0], PKT[2] - 0.5))])
# body side: eye block, LEDs, resistors, switch in the rear wall, JST
cx_, hw_ = BO.CX, BO.BLOCK_HW
BD["eye-block"] = np.vstack([jbox(cx_ - hw_, cx_ + hw_, -60, BO.BLOCK_Y, BO.EYE_Z, BO.BLOCK_Z1), jbox(cx_ - hw_, cx_ + hw_, -60, BO.BLOCK_OPEN_Y, BO.BLOCK_Z0, BO.EYE_Z),
    jbox(cx_ - hw_, cx_ - hw_ + BO.FRAME_T, BO.BLOCK_OPEN_Y, BO.BLOCK_Y, BO.FRAME_Z0, BO.EYE_Z), jbox(cx_ + hw_ - BO.FRAME_T, cx_ + hw_, BO.BLOCK_OPEN_Y, BO.BLOCK_Y, BO.FRAME_Z0, BO.EYE_Z),
    jbox(cx_ - BO.BRIDGE[0], cx_ + BO.BRIDGE[0], -60, BO.BRIDGE[1], BO.BRIDGE[2], BO.BLOCK_Z0)])
ex, ez, ey = BO.EYE_DX * S, (BO.EYE_Z - motion.ORIGIN[2]) * S, (BO.EYE_BORE_BACK - motion.ORIGIN[1]) * S
# 5 mm LED through the bore floor: dome in the bore, flange Ø5.8 x 1 + body behind the floor, leads bent up
LEDB = E("LEDB", 1.5); RYO = E("RYO", 1.0)          # resistor axis behind the LED base                                # LED base proud of the block's back face
for sx, nm in ((1, "r"), (-1, "l")):
    BD[f"led-{nm}"] = cyl_ax((sx * ex, ey - 0.01, ez), (sx * ex, ey + LEDB, ez), 2.9); HW.add(f"led-{nm}")
    BD[f"led-leads-{nm}"] = box((sx * ex - 1.6, ey + LEDB, ez - 0.4), (sx * ex + 1.6, ey + LEDB + 2.0, ez + 0.4)); HW.add(f"led-leads-{nm}")
    BD[f"resistor-{nm}"] = cyl_ax((sx * ex, ey + LEDB + RYO, ez + 1.4), (sx * ex, ey + LEDB + RYO, ez + 1.4 + 6.5), 1.15); HW.add(f"resistor-{nm}")  # up along the block's back face
SWY, SWZ = E("SWY", 0.0), E("SWZ", 21.0)            # switch: in the body's back wall, lever out to +y (SWY = 0: on the inner wall)
zsw = (SWZ / S + motion.ORIGIN[2]); _zs, _R = BODY_ROWS; bbk = np.interp(zsw, _zs, _R[:, 2]) * S
swy1 = bbk - 0.01 if SWY == 0 else SWY
BD["ss12d00-switch"] = box((-6, swy1 - 6, SWZ - 3), (6, swy1, SWZ + 3)); HW.add("ss12d00-switch")
BD["switch-keeper"] = box((-7.2, swy1 - 6 - F.STEEL.side - W, SWZ - 4.2), (7.2, swy1 - 6 - F.STEEL.side, SWZ + 4.2))
JX, JY, JZ = E("JX", 0.0), E("JY", 12.0), E("JZ", 41.0)
ST["jst-xh"] = box((JX - 6, JY - 2.9, JZ - 4.95), (JX + 6, JY + 2.9, JZ + 4.95)); HW.add("jst-xh")   # 3-pin mated pair, along x
# moving: crank journals, webs (stadium hub..pin) and printed pins, per pose and swept
pin_x1 = P["XC"] + E("PINX", 3.0); WEBR = PINR + E("WEBW", 1.0)
TH24 = np.linspace(0, 2 * np.pi, 24, endpoint=False)
def crank_pose(i, k, sides=(1, -1), pins=True):
    q = []
    for sx in sides:
        A = A_ALL[i if sx > 0 else i + 4, k]
        o = np.array([0, Oy[i], Oz]); a_ = np.array([0, A[1], A[2]])
        x0, x1 = (wb0, wb1) if sx > 0 else (-wb1, -wb0)
        for t in np.linspace(0, 1, 6):
            c = o + t * (a_ - o); q.append(cyl_x(c[1], c[2], WEBR, x0, x1))
        if pins: q.append(cyl_x(A[1], A[2], PINR, *((wb1, pin_x1) if sx > 0 else (-pin_x1, -wb1))))
    return np.vstack(q)
def vox(q, h=0.25):
    _, j = np.unique(np.round(q / h).astype(np.int64), axis=0, return_index=True); return q[j]
MV["crankshafts"] = vox(np.vstack([np.vstack([cyl_x(Oy[i], Oz, JR, -wb0, wb0)] + [crank_pose(i, k) for k in range(24)]) for i in range(4)]), 0.35)
CR = [[crank_pose(i, k) for i in range(4)] for k in range(24)]
# legs: the inner end is a bore Ø3.5 (TURN) over the printed pin, wall 1.2, the arm slides on the pin; root ball at P
END_R = PINR + F.TURN.side + W
TAIL = E("TAIL", 0.7)                               # end tube tail past the pin (spec: ~0.7)
SL = float(np.max([np.ptp(np.linalg.norm(PIV[k] - A_ALL[k], axis=1)) for k in range(8)]))
HUBCUT = 11.5                                        # real arm kept from 11.5 mm past the pin (the jenscolt hub is replaced by the end tube)
RLEG = LR.load(motion, PIV, A_ALL, HUBCUT)
def leg_end(Lg, k):
    A = A_ALL[Lg, k]; u = (PIV[Lg] - A) / np.linalg.norm(PIV[Lg] - A); return cyl_ax(A - TAIL * u, A + (1.0 + SL + 0.8) * u, END_R)
_LPC = {}
def leg_pose(Lg, k, full=False):
    if (Lg, k, full) not in _LPC: _LPC[(Lg, k, full)] = _leg_pose(Lg, k, full)
    return _LPC[(Lg, k, full)]
def _leg_pose(Lg, k, full=False):
    A = A_ALL[Lg, k]; u = (PIV[Lg] - A) / np.linalg.norm(PIV[Lg] - A); e1 = 1.0 + SL + 0.8
    q = [cyl_ax(A - TAIL * u, A + e1 * u, END_R), cyl_ax(A + e1 * u, A + HUBCUT * u, P["r_inner"])]   # end tube (capsule) + joint to the real neck
    q.append(cyl_ax(PIV[Lg] - PB * u, PIV[Lg] + 0.01 * u, PB))                                         # root ball in its window
    q.append(RLEG(Lg, k, full))                       # the real cad/legs arm from its neck on (hub cut), + blade if full
    return np.vstack(q)
ARMS = [np.vstack([leg_pose(Lg, k) for Lg in range(8)]) for k in range(24)]; AT = [cKDTree(a_) for a_ in ARMS]
ARM_LO = np.min([a_.min(0) for a_ in ARMS], 0); ARM_HI = np.max([a_.max(0) for a_ in ARMS], 0)
# ---------------- clearances (fits.py) per pair
FLEX = {"led-leads-r", "led-leads-l", "resistor-r", "resistor-l", "motor-leads", "jst-xh", "nickel-strip", "cell-springs"}
def need(a_, b_):
    s = {a_, b_}
    if s <= HW and s & FLEX: return 0.0                    # bendable leads, wires, springs among bought parts: no overlap only
    if any(n.startswith("leg") for n in s): return F.LEG_PATH.side
    if any(n.startswith(("crank-gear", "idler-", "transfer-small", "transfer-big", "pinion")) for n in s): return F.GEAR_TIP.side
    if "crankshafts" in s: return F.TURN.side
    if "shell" in s: return F.LOCATOR.side                 # a part inside the cavity, not located on the wall
    if s & HW: return F.STEEL.side
    return F.NEIGHBOUR.side                                # two static printed parts side by side (window/slot parts are designed pairs)
D = set()
def des(*pairs):
    for p_ in pairs: D.add(frozenset(p_))
des(("n10-motor", "drive-unit"), ("motor-leads", "n10-motor"), ("n10-shaft", "n10-motor"), ("n10-shaft", "pinion"), ("transfer-axle", "drive-unit"),
    ("transfer-axle", "spine"), ("transfer-axle", "transfer-small"), ("transfer-axle", "transfer-big"), ("drive-unit", "spine"), ("transfer-small", "transfer-big"),
    ("ag13-cells", "cell-holder"), ("ag13-cells", "cell-springs"), ("ag13-cells", "nickel-strip"), ("cell-springs", "cell-holder"), ("nickel-strip", "cell-holder"),
    ("cell-lid", "cell-holder"), ("ss12d00-switch", "switch-keeper"), ("led-r", "eye-block"), ("led-l", "eye-block"), ("led-leads-r", "led-r"), ("led-leads-l", "led-l"),
    ("resistor-r", "led-leads-r"), ("resistor-l", "led-leads-l"), ("resistor-r", "eye-block"), ("resistor-l", "eye-block"), ("led-leads-r", "eye-block"), ("led-leads-l", "eye-block"),
    ("holder-post", "cell-holder"), ("holder-post", "spine"), ("holder-screw", "holder-post"), ("holder-screw", "cell-holder"), ("holder-screw", "spine"),
    ("spine-keel", "spine"), ("crankshafts", "spine"))
for k in (1, 2):
    des((f"snap-finger-{k}", f"snap-rib-{k}"),
        (f"keel-screw-{k}", "spine-keel"), (f"drive-screw-{k}", "drive-unit"), (f"drive-screw-{k}", "spine"), (f"drive-ear-{k}", "drive-unit"),
        (f"drive-ear-{k}", "spine"), (f"drive-ear-{k}", f"drive-screw-{k}"), (f"drive-block-{k}", "spine"), (f"drive-block-{k}", f"drive-ear-{k}"),
        (f"drive-block-{k}", f"drive-screw-{k}"), (f"drive-block-{k}", "drive-unit"))
for i in range(3): des((f"idler-axle-{i+1}", "spine"), (f"idler-axle-{i+1}", f"idler-{i+1}"))
for i in range(4): des((f"crank-gear-{i+1}", "crankshafts"))
MESH = [(f"crank-gear-{i+1}", f"idler-{i+1}") for i in range(3)] + [(f"crank-gear-{i+2}", f"idler-{i+1}") for i in range(3)] + \
       [("transfer-small", f"idler-{ti+1}"), ("transfer-big", "pinion")]
des(*MESH)
# a spinning gear between the walls is held axially by GEAR_THRUST (designed); its radial gap to the walls is not a gap
for n in [f"crank-gear-{i+1}" for i in range(4)] + [f"idler-{i+1}" for i in range(3)] + ["transfer-small"]: des((n, "spine"))
des(("transfer-big", "drive-unit"), ("pinion", "drive-unit"))                   # axial, GEAR_AXIAL built into xo / mx1
for k in (1, 2): des((f"idler-axle-{k}", "drive-unit"))
# journal caps fill the open-top slots: axial faces to the gears as the walls (GEAR_THRUST), fused to the drive unit / post
for n in ["spine", "drive-unit", "drive-block-1", "drive-block-2", "transfer-small"] + [f"crank-gear-{i+1}" for i in range(4)] + [f"idler-{i+1}" for i in range(3)]:
    des(("journal-caps", n))
for n in ["spine", "holder-post", "cell-holder", "holder-screw", "crank-gear-4", "idler-3"]: des(("post-cap", n))
SEATED_SHELL = {"spine-keel", "snap-finger-1", "snap-finger-2", "snap-rib-1", "snap-rib-2", "eye-block", "led-r", "led-l", "rear-tab",
                "ss12d00-switch", "switch-keeper", "keel-screw-1", "keel-screw-2", "body-screw-1", "body-screw-2",
                "resistor-r", "resistor-l", "led-leads-r", "led-leads-l"}
ALL = {**ST, **MV, **BD}
_dead = sorted(tuple(sorted(p)) for p in D if any(n not in ALL for n in p)); D = {p for p in D if all(n in ALL for n in p)}
print("DEAD designed pairs (a name that is not a part here), removed:", len(_dead), _dead)
tick("parts"); rows = []; seats = []; tick(f"crankshafts pts {len(MV['crankshafts'])}")
BB = {n: (q.min(0), q.max(0)) for n, q in ALL.items()}
def bbd(a_, b_):
    (l1, h1), (l2, h2) = BB[a_], BB[b_]; return float(np.linalg.norm(np.maximum(0, np.maximum(l1 - h2, l2 - h1))))
FAR = 3.0; KD = {n: cKDTree(q) for n, q in ALL.items()}
def shell_gap(q):                                    # gaps over 3 mm are reported as 3 (either sign): rows only need the least
    d, _ = WALL_T.query(q, distance_upper_bound=3.0, workers=-1); d = np.minimum(d, 3.0); ins = inside(q); gg = np.where(ins, d, -d); k = int(np.argmin(gg)); return gg[k], q[k]
for n, q in ALL.items():
    if n in SEATED_SHELL: seats.append((n, "shell", "seated on / fused to its shell")); continue
    gq, at = shell_gap(q); rows.append((gq, need(n, "shell"), n, "shell", np.round(at, 1)))
for a_, b_ in itertools.combinations(ALL, 2):
    if frozenset((a_, b_)) in D:
        if bbd(a_, b_) < FAR: seats.append((a_, b_, f"designed, gap {KD[a_].query(ALL[b_])[0].min():.2f}"))
        continue
    if bbd(a_, b_) > FAR: continue
    gq = KD[a_].query(ALL[b_])[0]; k = int(np.argmin(gq)); rows.append((gq[k], need(a_, b_), a_, b_, np.round(ALL[b_][k], 1)))
for n_ in [f"idler-{i+1}" for i in range(3)] + ["transfer-small"]:   # axial faces to the spine walls: GEAR_THRUST_IDLER
    _x = ALL[n_][:, 0]
    rows.append((float(min(wx0 - _x.max(), wx0 + _x.min())), F.GEAR_THRUST_IDLER.side, n_, "spine wall faces (axial THRUST)", ""))
# keel vs crank gears with each crank journal resting on its slot bottom (TURN lower than centred)
for i in range(4):
    gq = KD["spine-keel"].query(ALL[f"crank-gear-{i+1}"] - [0, 0, KSLOT])[0]; k = int(np.argmin(gq))
    rows.append((gq[k], F.GEAR_TIP.side, "spine-keel", f"crank-gear-{i+1} at slot bottom (-{KSLOT:.2f})", np.round(ALL[f"crank-gear-{i+1}"][k], 1)))
tick("pairs")
# local pockets in the two parts that meet a leg arm's sweep (spec: reshape the colliding part locally): their surface within PKR of the arms' sweep is pushed back to PKR
PKR = E("PKR", 0.85); _AT0 = cKDTree(vox(np.vstack(ARMS), 0.25)); POCKETS, POCKET_DROPPED = {}, {}
for n_ in ("eye-block", "cell-holder"):
    q0 = ALL[n_]; q = q0.copy(); d0 = _AT0.query(q0, distance_upper_bound=PKR)[0]
    for _it in range(40):
        d_, j_ = _AT0.query(q, distance_upper_bound=PKR); m_ = np.isfinite(d_) & (d_ < PKR - 1e-3) & (d_ > 1e-6)
        if not m_.any(): break
        v_ = q[m_] - _AT0.data[j_[m_]]; q[m_] = _AT0.data[j_[m_]] + PKR * v_ / np.linalg.norm(v_, axis=1)[:, None]
    # points still inside the sweep (between two arms' samples the push does not converge) are material the pocket
    # removes: drop them; the pocket wall is the pushed points around them, all at >= PKR from the sweep
    _in = _AT0.query(q)[0] < PKR - 0.05; POCKET_DROPPED[n_] = int(_in.sum()); q, q0, d0 = q[~_in], q0[~_in], d0[~_in]
    ch_ = np.linalg.norm(q - q0, axis=1) > 1e-6
    if ch_.any():
        POCKETS[n_] = (np.round(q0[ch_].min(0), 1).tolist(), np.round(q0[ch_].max(0), 1).tolist(), round(float(PKR - d0[np.isfinite(d0)].min()), 2))
        for D_ in (ALL, ST, BD, MV):
            if n_ in D_: D_[n_] = q
        KD[n_] = cKDTree(q); BB[n_] = (q.min(0), q.max(0))
print("leg-arm pockets in parts (bbox, depth)", POCKETS, "points removed inside the sweep", POCKET_DROPPED)
# legs (inner end, arm, root ball) over the 24 poses vs every part; the pin is their designed bearing
for n, q in ALL.items():
    if n == "crankshafts": continue      # per pose above
    if np.linalg.norm(np.maximum(0, np.maximum(ARM_LO - q.max(0), q.min(0) - ARM_HI))) > FAR: continue
    q = q[np.all((q > ARM_LO - FAR) & (q < ARM_HI + FAR), axis=1)]
    gl = [t.query(q, distance_upper_bound=FAR)[0] for t in AT]; k = int(np.argmin([x.min() for x in gl])); j = int(np.argmin(gl[k]))
    rows.append((min(gl[k][j], FAR), need(n, "leg"), n, f"leg-arms@pose{k}", np.round(q[j], 1)))
# per pose: crank vs crank (webs), each leg vs every crank but its own pin (its own web counts: the end's axial gap)
gcc = min(cKDTree(CR[k][i]).query(CR[k][i + 1])[0].min() for k in range(24) for i in range(3))
rows.append((gcc, F.TURN.side, "crankshaft i", "crankshaft i+1 (24 poses)", ""))
gl_, gw_ = (9e9, None), (9e9, None)
WAIVE = {1: 2, 2: 1}                                 # crank index -> the neighbour whose pin/webs the leg END may touch (gap >= 0)
CRT = [[cKDTree(CR[k][j]) for j in range(4)] for k in range(24)]
for k in range(24):
    for Lg in range(8):
        i, sx = Lg % 4, (1 if Lg < 4 else -1)
        lq = leg_pose(Lg, k); le = leg_end(Lg, k); rest = lq[np.linalg.norm(lq - A_ALL[Lg, k], axis=1) > 0]
        own = [cKDTree(crank_pose(i, k, (sx,), pins=False)), cKDTree(crank_pose(i, k, (-sx,)))]
        for j in range(4):
            if j == i: continue
            if WAIVE.get(i) == j:                    # end tube: waived to 0; the rest of the leg (arm, ball) keeps 0.8
                ge = CRT[k][j].query(le, distance_upper_bound=4)[0].min()
                if ge < gw_[0]: gw_ = (ge, (Lg, k, j))
                arm = lq[np.min(cKDTree(le).query(lq)[0][:, None], axis=1) > 0.3]
                g_ = CRT[k][j].query(arm, distance_upper_bound=4)[0].min()
            else:
                g_ = CRT[k][j].query(lq, distance_upper_bound=4)[0].min()
            if g_ < gl_[0]: gl_ = (g_, (Lg, k, f"crank {j+1}"))
        for t_ in own:
            g_ = t_.query(lq, distance_upper_bound=4)[0].min()
            if g_ < gl_[0]: gl_ = (g_, (Lg, k, "own"))
rows.append((gl_[0], F.LEG_PATH.side, "leg-arms", f"cranks (own web, other cranks; waived end excluded) leg {gl_[1][0]} pose {gl_[1][1]} {gl_[1][2]}", ""))
rows.append((gw_[0], 0.0, "leg-end cranks 2/3", f"neighbour crank pin+webs (LEG_PATH waived to 0) leg {gw_[1][0]} pose {gw_[1][1]} crank {gw_[1][2]+1}", ""))
# signed (capsule) check of the leg ends: point clouds cannot see two solids that pass into each other
def _segd(p0, p1, q0, q1, n=60):
    t = np.linspace(0, 1, n); p = p0 + t[:, None] * (p1 - p0); q = q0 + t[:, None] * (q1 - q0)
    return np.linalg.norm(p[:, None] - q[None], axis=2).min()
def _end(Lg, k):
    A = A_ALL[Lg, k]; u = (PIV[Lg] - A) / np.linalg.norm(PIV[Lg] - A); return A - TAIL * u, A + (1.0 + SL + 0.8) * u
for La, Lb in ((0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7)):
    g_ = min((_segd(*_end(La, k), *_end(Lb, k)) - 2 * END_R, k) for k in range(24))
    rows.append((g_[0], F.LEG_PATH.side, f"leg-end {La}", f"leg-end {Lb} SIGNED capsule @pose{g_[1]}", ""))
for La, Lb in ((1, 2), (2, 1), (5, 6), (6, 5)):
    sx = 1 if La < 4 else -1
    g_ = min((_segd(*_end(La, k), np.r_[sx * wb1, A_ALL[Lb, k][1:]], np.r_[sx * pin_x1, A_ALL[Lb, k][1:]]) - END_R - PINR, k) for k in range(24))
    rows.append((g_[0], 0.0, f"leg-end {La}", f"pin of crank {Lb % 4 + 1} SIGNED capsule, waived to 0 @pose{g_[1]}", ""))
tick("legs vs cranks")
# leg vs leg, whole legs (motion tubes) over 24 poses
for La, Lb in ([(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (3, 7), (1, 5), (2, 6)] if E("LEGLEG", 1) else []):
    best_ = (9e9,)
    for k in range(24):
        qa, qb = leg_pose(La, k, True), leg_pose(Lb, k, True); d_, j_ = cKDTree(qa).query(qb, distance_upper_bound=3.0, workers=-1); d_ = np.minimum(d_, 3.0)
        m_ = int(np.argmin(d_))
        if d_[m_] < best_[0]: best_ = (d_[m_], k, qb[m_])
    rows.append((best_[0], F.LEG_PATH.side, f"leg-{La}", f"leg-{Lb} (24 poses) @pose{best_[1]}", np.round(best_[2], 1)))
# leg arms vs the shell, away from the pivot window (the window is the leg's seat: WINDOW round the ball's swing)
# ---- leg windows (spec must_have: size the window from the real arm neck): the neck = the real leg's samples within RN of the pivot over
# the 24 poses (ball + neck of the real cad/legs arm), plus its slide off the pin (LSL along u); the window = the open-top slot
# (that sweep pushed up past the rim) dilated by WR = LEG_PATH 0.8 + 0.1 sampling slack; wall points inside it are removed
WR = E("WR", 0.9); RN = E("RN", 8.0); LSL = (pin_x1 - wb1) + 1.0; ZTOP = RIMR + 1.0
WEXT = {}
for Lg in range(8):
    nk = np.vstack([leg_pose(Lg, k, True) for k in range(24)]); nk = nk[np.linalg.norm(nk - PIV[Lg], axis=1) <= RN]
    u_ = PIV[Lg] - A_ALL[Lg, 0]; u_ /= np.linalg.norm(u_); nk = vox(np.vstack([nk + t_ * u_ for t_ in np.arange(0, LSL + 0.01, 0.4)]), 0.35)
    WEXT[Lg] = cKDTree(np.vstack([nk + [0, 0, dz] for dz in np.arange(0, ZTOP - nk[:, 2].min(), 0.5)]))
def in_win(Lg, q):
    return WEXT[Lg].query(q, distance_upper_bound=WR, workers=-1)[0] < WR
def in_win_any(q):
    m = np.zeros(len(q), bool)
    for Lg in range(8):
        c = np.linalg.norm(q[:, :2] - PIV[Lg][:2], axis=1) < 30
        if c.any(): m[c] |= in_win(Lg, q[c])
    return m
def arm_only(Lg, k, cav=False):                       # arm samples outside its own window (the windowed whole-leg rows cover the window's rim band)
    q = leg_pose(Lg, k); q = q[~in_win(Lg, q)]; return q[inside(q)] if cav else q
BRELD = E("BRELD", 0.85)                             # body rim notch: the body inner face within BRELD of the legs' sweep is pocketed
_wk = ~(in_win_any(WALL_PTS) & (WALL_PTS[:, 2] <= RIMR)); WIN_CUT = WALL_PTS[~_wk]; WALL_PTS = WALL_PTS[_wk]; WALL_T = cKDTree(WALL_PTS)     # the window itself: wall points inside it removed
print('window cut: wall points removed', len(WIN_CUT), 'bbox', np.round(WIN_CUT.min(0), 1).tolist(), np.round(WIN_CUT.max(0), 1).tolist(), 'LSL', round(LSL, 2))
AQ = np.vstack([arm_only(Lg, k) for Lg in range(8) for k in range(24)])
RELD = E("RELD", 0.85)                               # front leg window relief: the wall within RELD of the arms' sweep is pocketed
if RELD > 0:
    _ta = cKDTree(AQ); dw, jw = _ta.query(WALL_PTS, distance_upper_bound=RELD); cut = np.isfinite(dw)
    if cut.any():
        _n = WALL_PTS[cut] - AQ[jw[cut]]; _n /= np.maximum(np.linalg.norm(_n, axis=1), 1e-9)[:, None]
        floor = AQ[jw[cut]] + RELD * _n             # pocket floor: the cut wall points pushed out to RELD from the arm
        for _it in range(12):                       # push until RELD from every arm sample, not only the nearest one
            _d2, _j2 = _ta.query(floor); _m = _d2 < RELD - 1e-3
            if not _m.any(): break
            _v = floor[_m] - AQ[_j2[_m]]; floor[_m] = AQ[_j2[_m]] + RELD * _v / np.maximum(np.linalg.norm(_v, axis=1), 1e-9)[:, None]
        BULGE = (floor + 0 * floor, _n.copy()); floor = floor[~inside(floor)]
        from scipy.sparse.csgraph import connected_components
        _cp = WALL_PTS[cut]; _nc, _lb = connected_components(cKDTree(_cp).sparse_distance_matrix(cKDTree(_cp), 1.2), directed=False)
        PATCHES = [(np.round(_cp[_lb == c].min(0), 1).tolist(), np.round(_cp[_lb == c].max(0), 1).tolist(), round(float(RELD - dw[cut][_lb == c].min()), 2)) for c in range(_nc)]                # a floor pushed into the cavity is the window itself (arm passes out through it)
        RELIEF = (WALL_PTS[cut].min(0), WALL_PTS[cut].max(0), float(RELD - np.min(dw[cut])), int(cut.sum()))
        WALL_PTS = np.vstack([WALL_PTS[~cut], floor]); WALL_T = cKDTree(WALL_PTS)
        print("relief bbox", np.round(RELIEF[0], 1), np.round(RELIEF[1], 1), "max depth", round(RELIEF[2], 2), "pts", RELIEF[3])
gs = []
for k in range(0, 24):
    q = np.vstack([arm_only(Lg, k, True) for Lg in range(8)]); gs.append(shell_gap(q) + (k,))
g_ = min(gs, key=lambda r: r[0]); rows.append((g_[0], F.LEG_PATH.side, "leg-arms (off the pivot)", f"shell @pose{g_[2]} (relief {RELD})", np.round(g_[1], 1)))
# pivot windows: the root ball's swing vs the base window (angular room as the leg yaws/pitches): reported
sw = []
for Lg in range(4):
    u = np.array([(PIV[Lg] - A_ALL[Lg, k]) / np.linalg.norm(PIV[Lg] - A_ALL[Lg, k]) for k in range(24)])
    yaw = np.degrees(np.ptp(np.arctan2(u[:, 1], u[:, 0]))); pit = np.degrees(np.ptp(np.arcsin(u[:, 2]))); sw.append((Lg, round(yaw, 1), round(pit, 1)))
# screws in walls: the shank >= 1.2 inside the outer skin where it runs in a post/boss on the wall
OUTER = j2r(np.vstack([np.c_[BA.CX + BA.meridian(BA.X_W, BA.X_ZE, BA.X_H, BA.X_P, z) * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** (2 / BA.plan_n(z)),
                             BA.CY + BA.meridian(BA.Y_W, BA.Y_ZE, BA.Y_H, BA.Y_P, z) * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** (2 / BA.plan_n(z)), np.full(len(t), z)]
                       for z in np.arange(BA.Z_FOOT, BA.Z_LEDGE, 0.3) for t in [np.linspace(0, 2 * np.pi, 240, endpoint=False)]]))
OT_ = cKDTree(np.vstack([OUTER, BAND_OUT]))
tick("leg-leg, shell")
for k, xc, yw, dl, Lf, eps in SNAPS:                # finger + hook swept inward (+y) by the hook's travel: vs every part and the legs
    q = BD[f"snap-finger-{k+1}"]; g_ = (9e9, "")
    for t in np.linspace(0, dl, 5):
        qq = q + [0, t, 0]
        for o in ALL:
            if o.startswith("snap-") or o in BD or bbd(o, f"snap-finger-{k+1}") > FAR + dl: continue
            gg = KD[o].query(qq, distance_upper_bound=3)[0].min()
            if gg < g_[0]: g_ = (gg, o)
        gg = min(a_.query(qq, distance_upper_bound=3)[0].min() for a_ in AT)
        if gg < g_[0] - (F.LEG_PATH.side - F.WINDOW.side): g_ = (gg + F.WINDOW.side - F.LEG_PATH.side, "legs (shown vs 0.5: leg need 0.8)")
    rows.append((min(g_[0], 3.0), F.WINDOW.side, f"snap-finger-{k+1} deflected {dl:.2f}", f"{g_[1]} (strain {100*eps:.1f} %, L {Lf:.1f})", ""))
if not E("LEGSONLY", 0):
    # body lift-off: body inner wall + its parts raised 0..40 past every base-side part (wires, JST flexible: unplugged first)
    _BI = j2r(BODY_PTS); _HL = np.vstack([ST["cell-holder"], ST["cell-lid"]]); _sw = np.vstack([_HL - [0, 0, t] for t in np.arange(0, 40.1, 0.5)]); _st = cKDTree(vox(_sw, 0.2))
    _LF = np.vstack([leg_pose(Lg, k, True) for Lg in range(8) for k in range(24)]); _LF = _LF[cKDTree(PIV).query(_LF)[0] > PB + 2.5]
    _AQ2 = np.vstack([AQ, _LF]); _ta2 = cKDTree(_AQ2)
    def _relieve(B):                                     # body rim notch: body points within BRELD of the legs' sweep pushed out to BRELD
        B = B.copy(); _dr, _ = _ta2.query(B, distance_upper_bound=BRELD); cr = np.isfinite(_dr); B0 = B[cr].copy(); dmin = _dr[cr].min() if cr.any() else BRELD
        for _it in range(12):
            d_, j_ = _ta2.query(B, distance_upper_bound=BRELD); m_ = np.isfinite(d_) & (d_ < BRELD - 1e-3)
            if not m_.any(): break
            v_ = B[m_] - _AQ2[j_[m_]]; B[m_] = _AQ2[j_[m_]] + BRELD * v_ / np.maximum(np.linalg.norm(v_, axis=1), 1e-9)[:, None]
        return B, cr, dmin
    LIFTC = E("LIFTC", 0.05)                               # body pocket for the holder/lid lift-off: only where it would touch
    _BI0 = _BI.copy(); _BI, _cr, _dm = _relieve(_BI); _dr = np.full(len(_BI), BRELD); _dr[_cr] = _dm
    print('body rim notch over the leg arms (bbox, depth)', np.round(_BI0[_cr].min(0), 1).tolist() if _cr.any() else None, np.round(_BI0[_cr].max(0), 1).tolist() if _cr.any() else None, round(float(BRELD - _dr[_cr].min()), 2) if _cr.any() else 0)
    _d0, _j0 = _st.query(_BI, distance_upper_bound=LIFTC); _c0 = np.isfinite(_d0); BPOCK = None
    if _c0.any():
        _v = _BI[_c0] - _st.data[_j0[_c0]]; _BI[_c0] = _st.data[_j0[_c0]] + (LIFTC) * _v / np.maximum(np.linalg.norm(_v, axis=1), 1e-9)[:, None]
        BPOCK = (np.round(j2r(BODY_PTS)[_c0].min(0), 1).tolist(), np.round(j2r(BODY_PTS)[_c0].max(0), 1).tolist(), round(float(LIFTC - _d0[_c0].min()), 2))
    print("body inner pocket for holder/lid lift-off (bbox, depth)", BPOCK)
    _BW, _crw, _dmw = _relieve(j2r(body_inner_pts(w=0.3)[0])); print('body rim notch (w=0.3 rows) depth', round(float(BRELD - _dmw), 2) if _crw.any() else 0)
    BODY_SET = np.vstack([_BI, _BW] + [BD[n] for n in BD])
    _bxy = cKDTree(_LF[:, :2]); LIFTD = E("LIFTD", 8.0); LIFTR = E("LIFTR", F.NEIGHBOUR.side + 0.1); NOTCH2 = {}   # assembly path need (README) + sampling (a cloud overestimates a gap ~0.1)
    BS = BODY_SET[_bxy.query(BODY_SET[:, :2], distance_upper_bound=3.0)[0] < 3.0]; _best = None
    for k in range(24):                                  # the body goes on last, at ONE crank pose chosen as the best of the 24
        Lk = np.vstack([leg_pose(Lg, k, True) for Lg in range(8)]); Lk = Lk[cKDTree(PIV).query(Lk)[0] > PB + 2.5]; tk = cKDTree(vox(Lk, 0.3))
        BSk = BS.copy(); tv = cKDTree(np.vstack([tk.data - [0, 0, t] for t in np.arange(0, LIFTD + 0.01, 0.5)]))     # deeper rim notch: the body keeps LEG_PATH from the leg parts above it along the lift
        for _it in range(40):
            d_, j_ = tv.query(BSk, distance_upper_bound=LIFTR); m_ = np.isfinite(d_) & (d_ < LIFTR - 1e-3)
            if not m_.any(): break
            v_ = BSk[m_] - tv.data[j_[m_]]; BSk[m_] = tv.data[j_[m_]] + LIFTR * v_ / np.maximum(np.linalg.norm(v_, axis=1), 1e-9)[:, None]
        _in = tv.query(BSk)[0] < LIFTR - 0.05; _dropped = int(_in.sum()); BSk = BSk[~_in]; BS_ = BS[~_in]      # still inside between two columns: material the notch removes
        _mv = np.linalg.norm(BSk - BS_, axis=1) > 1e-6; NOTCH2[k] = (np.round(BS_[_mv].min(0), 1).tolist(), np.round(BS_[_mv].max(0), 1).tolist(), round(float(np.linalg.norm(BSk - BS_, axis=1).max()), 2), 'dropped', _dropped) if _mv.any() else None
        gk = min((tk.query(BSk + [0, 0, t], distance_upper_bound=3.0)[0].min(), t) for t in np.r_[0.0, 0.5, np.arange(1.0, 40.1, 1.0)])
        if _best is None or gk[0] > _best[0]: _best = gk + (k,)
    print("body lift-off vs legs: best of 24 poses = pose", _best[2], "gap", round(float(_best[0]), 2), "at +", _best[1])
    print("body rim notch deepened for the lift-off at the best pose (bbox, depth)", NOTCH2[_best[2]])
    rows.append((min(_best[0], 3.0), F.NEIGHBOUR.side, "legs (whole, ball seat excluded)", f"body lift-off at the best of 24 crank poses (pose {_best[2]}), @+{_best[1]:.1f}", ""))
    BST = {n: q for n, q in {**ST, **MV}.items() if not n.startswith(("body-screw", "jst", "snap-rib"))}
    names = list(BST); SQ = np.vstack([BST[n] for n in names]); lab = np.concatenate([np.full(len(BST[n]), i) for i, n in enumerate(names)])
    SK = cKDTree(SQ); best = {n: (9e9, 0) for n in names}
    for t in np.r_[0.5, np.arange(1.0, 40.1, 1.0)]:
        d, j = SK.query(BODY_SET + [0, 0, t], distance_upper_bound=3.0); ok = np.isfinite(d)
        mn = np.full(len(names), 9e9); np.minimum.at(mn, lab[j[ok]], d[ok])
        for i in np.nonzero(mn < 9e9)[0]:
            if mn[i] < best[names[i]][0]: best[names[i]] = (mn[i], t)
    for n in names:
        m = best[n]
        if m[0] < 3.0: rows.append((m[0], 0.0, n, f"body lift-off @+{m[1]:.0f}", ""))
tick("lift-off")
# ---------------- assembly paths: each part along its way in (reversed: out), against what is already placed;
# the legs over 24 poses in every stage after them; driver lines as filled cylinders
PATHQ = {}
LEGS_IN = cKDTree(vox(np.vstack(ARMS), 0.3))
def path(q, d, dist, against, shell=True, legs=False, extra=None):
    worst = (3.0, 0, "")
    for t in np.arange(0.5, dist, 0.5):
        qq = q + t * np.asarray(d, float)
        for o in against:
            g_ = KD[o].query(qq, distance_upper_bound=3.0)[0].min()
            if g_ < worst[0]: worst = (g_, t, o)
        if legs:
            g_ = LEGS_IN.query(qq, distance_upper_bound=3.0)[0].min()
            if g_ < worst[0]: worst = (g_, t, "legs (24 poses)")
        if extra is not None:
            g_ = extra.query(qq, distance_upper_bound=3.0)[0].min()
            if g_ < worst[0]: worst = (g_, t, "placed set")
        if shell and qq[:, 2].min() < RIMR and t < dist - 0.5 and abs(t - round(t)) < 1e-6:
            g_ = shell_gap(vox(qq, 0.5))[0]
            if g_ < worst[0]: worst = (g_, t, "shell")
    return worst
def prow(n, need_, g_, d, why=""):
    rows.append((g_[0], need_, n, f"assembly path {d} @{g_[1]:.1f} vs {g_[2]} {why}", ""))
up = (0, 0, 1); GEARS = [f"crank-gear-{i+1}" for i in range(4)] + [f"idler-{i+1}" for i in range(3)]
JOUR = lambda: np.vstack([cyl_x(Oy[i], Oz, JR, -wb0, wb0) for i in range(4)])
# 1 cranks drop into the open-top slots of the spine (bench): vs the slot faces and walls, TURN; best of 8 crank angles
best_ = (-9e9,)
for k in range(0, 24, 3):
    q = np.vstack([JOUR()] + [CR[k][i] for i in range(4)] + [MV[f"crank-gear-{i+1}"] for i in range(4)])
    g_ = path(q, up, 9.5, ["spine"], shell=False)
    _ss = np.vstack([ST["spine"], q] + [MV[f"idler-{j+1}"] for j in range(3)]); g2 = path(_ss, up, 28, ["snap-rib-1", "snap-rib-2"])
    if min(g_[0] - F.GEAR_THRUST_CRANK.side, g2[0]) > best_[0]: best_ = (min(g_[0] - F.GEAR_THRUST_CRANK.side, g2[0]), g_, k)
best_ = best_[1] + (best_[2],)
KC = best_[3]; prow("crankshafts", F.NEIGHBOUR.side, best_[:3], f"+z into the slots at crank pose {KC}", "(slot TURN 0.25)")
CRK = np.vstack([JOUR()] + [CR[KC][i] for i in range(4)]); KD["crank@KC"] = cKDTree(CRK)
tick('stage 1 cranks')
# 2 idlers drop between the walls onto the cranks (mesh radial, designed): vs walls (THRUST) and the cranks' webs/journals
for i in range(3):
    g_ = path(MV[f"idler-{i+1}"], up, 9.0, ["spine", "crank@KC"], shell=False); prow(f"idler-{i+1}", F.NEIGHBOUR.side, g_, "+z between the walls", "(axial THRUST)")
# 3 idler axles M2 along +x (head -x): driver line out along -x vs the spine set
def driver(n, c, d, against, legs=False, extra=None, r=2.25, Ld=40.0):
    d = np.asarray(d, float); a_ = np.cross(d, [0.3, 0.5, 0.8]); a_ /= np.linalg.norm(a_); b_ = np.cross(d, a_)
    q = []
    for rr in np.linspace(0, r, 8):
        nn = max(1, int(2 * np.pi * rr / 0.25)); t = np.linspace(0, 2 * np.pi, nn, endpoint=False)
        ring = rr * (np.cos(t)[:, None] * a_ + np.sin(t)[:, None] * b_)
        for z_ in np.arange(0, Ld, 0.25): q.append(c + z_ * d + ring)
    q = np.vstack(q); g_ = (9.0, "")
    for o in against:
        gg = KD[o].query(q, distance_upper_bound=4.0)[0].min()
        if gg < g_[0]: g_ = (gg, o)
    if legs:
        gg = LEGS_IN.query(q, distance_upper_bound=4.0)[0].min()
        if gg < g_[0]: g_ = (gg, "legs (24 poses)")
    rows.append((min(g_[0], 4.0), 0.0, n, f"driver line {tuple(np.round(d, 2))} vs {g_[1]} (filled Ø{2*r:.1f})", ""))
for i, c in enumerate(I):
    driver(f"idler-axle-{i+1}", np.array([-wx1 - 1.2, c[0], c[1]]), (-1, 0, 0), ["spine", "crank@KC"] + GEARS)
tick('stage 3 axles')
# 4 the spine set (spine, cranks at KC, idlers, axles) down onto the keel: vs shell, snap ribs
# local pockets in the base's inner face where the spine set's gear tips pass the rim (front, back): inner face moved out by
# dy, the outer skin bulged out by the same (wall stays BASE_WALL_R); spec must_have: local reshape, bulge outward on the shell
SPK = [[float(v) for v in b.split(",")] for b in os.environ.get("SPK", "-2.5,2.5,-30,-21,14.5,18.5,-0.35;;-3,3,19,30,15,18.5,0.3").split(";;") if b]
for x0_, x1_, y0_, y1_, z0_, z1_, dy_ in SPK:
    _m = (WALL_PTS[:, 0] > x0_) & (WALL_PTS[:, 0] < x1_) & (WALL_PTS[:, 1] > y0_) & (WALL_PTS[:, 1] < y1_) & (WALL_PTS[:, 2] > z0_) & (WALL_PTS[:, 2] < z1_)
    WALL_PTS = WALL_PTS.copy(); WALL_PTS[_m] += [0, dy_, 0]
if SPK: WALL_T = cKDTree(WALL_PTS); print("spine-set rim pockets (x0,x1,y0,y1,z0,z1,dy)", SPK)
SPSET = np.vstack([ST["spine"], CRK] + [MV[g] for g in GEARS] + [ST[f"idler-axle-{i+1}"] for i in range(3)])
prow("spine set", 0.0, path(SPSET, up, 28, ["snap-rib-1", "snap-rib-2"]), "+z onto the keel")
for k_ in (1, 2): driver(f"keel-screw-{k_}", np.array([0, (-KY + 1.8, KY - 1.8)[k_ - 1], -1.8]), (0, 0, -1), [], legs=True)
tick('stage 4 spine set')
# 5 legs: each slides off its pin along its axis (x) by the end tube's length, then lifts out (+z) through its open-top window
NR = PB + F.WINDOW.side                              # old window radius (Ø8), kept for the comparison picture
NRW = E("NRW", 5.4)                                   # new window radius from the real neck (+ LEG_PATH)
NRL = {Lg: float(os.environ.get(f"NRW{Lg}", NRW)) for Lg in range(8)}
SURF = np.vstack([WALL_PTS, OUTER, BAND_OUT])
def in_outer(q):
    J = r2j(q); x, y, z = J.T; zc = np.clip(z, BA.Z_FOOT, BA.Z_LEDGE)
    A = np.interp(zc, _ZG[0], [BA.meridian(BA.X_W, BA.X_ZE, BA.X_H, BA.X_P, zz) for zz in _ZG[0]]); B = np.interp(zc, _ZG[0], [BA.meridian(BA.Y_W, BA.Y_ZE, BA.Y_H, BA.Y_P, zz) for zz in _ZG[0]])
    N = np.interp(zc, _ZG[0], [BA.plan_n(zz) for zz in _ZG[0]])
    lo = (z >= BA.Z_FOOT) & (z <= BA.Z_LEDGE) & ((np.abs(x - BA.CX) / A) ** N + (np.abs(y - BA.CY) / B) ** N < 1)
    n = BA.N_TOP; hi = (z > BA.Z_LEDGE) & (z <= band_top(x, y)) & ((np.abs(x - BA.CX) / (A_L + BA.LEDGE)) ** n + (np.abs(y - BA.CY) / (B_L + BA.LEDGE)) ** n < 1)
    scoop = np.hypot(x - BA.CX, y - BACK_Y_J) < BA.BACK_R - pocket_dr(J)
    return (lo | hi) & ~scoop
inside(np.zeros((1, 3))); import fit_env as _E; _ZG = _E._ZG
if os.environ.get('PROBE'): exec(open(os.environ['PROBE']).read()); sys.exit()
RNEAR = E("RNEAR", 16.0)                              # a window's responsibility: leg samples within RNEAR of its pivot (farther arms: the 'leg-arms off the window' row)
LWR = E("LWR", 0.85); RELW = {}
def leg_shell(Lg, own=None, rest=None):
    NR = NRL[Lg]; c = PIV[Lg]; near = SURF[np.linalg.norm(SURF - c, axis=1) < 25]; u_ = (PIV[Lg] - A_ALL[Lg, KC]); u_ /= np.linalg.norm(u_)
    WINM = os.environ.get("WINM", "notch")
    def col(q): return in_win(Lg, q)
    cw = np.zeros((0, 3))
    WIN[Lg] = (np.round(u_, 2).tolist(), 'neck sweep RN %.1f + %.2f' % (RN, WR))
    if own is None:
        pts = np.vstack([near[~col(near)], cw]); T_ = cKDTree(pts)
        def g(q):
            q = q[np.linalg.norm(q - c, axis=1) < RNEAR]
            if not len(q): g.at = c; return 3.0
            d, _ = T_.query(q, distance_upper_bound=3.0); d = np.minimum(d, 3.0); mat = ~inside(q) & in_outer(q) & ~col(q); v_ = np.where(mat, -d, d); k_ = int(np.argmin(v_)); g.at = q[k_]; return v_[k_]
        return g
    # window relief (look cost, recorded): the shell within LWR of the leg's own sweep (24 poses, whole leg) and of its
    # assembly path near the window is pocketed; the pocket's faces are LWR from that sweep
    g0 = leg_shell(Lg); own = own[np.linalg.norm(own - c, axis=1) < 16]; OT = cKDTree(own); rest = rest[np.linalg.norm(rest - c, axis=1) < 16]
    def mat0(q): return ~inside(q) & in_outer(q) & ~col(q)
    pen = -g0(rest); pnp = -g0(own); base = np.vstack([near[~col(near)], cw])
    dn = OT.query(base, distance_upper_bound=LWR)[0] if LWR > 0 else np.full(len(base), np.inf); keep = ~np.isfinite(dn)
    cand = own[cKDTree(base).query(own, distance_upper_bound=LWR + 1.0)[0] < 9] if len(base) else own[:0]
    face = np.zeros((0, 3))
    if LWR > 0 and len(cand) and (~keep).any():
        dirs = np.random.default_rng(1).normal(size=(26, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
        fc = (cand[:, None, :] + LWR * dirs[None]).reshape(-1, 3); fc = fc[mat0(fc)]
        fc = fc[OT.query(fc)[0] >= LWR - 0.03]; face = fc
        cutp = base[~keep]; cutp = cutp[cKDTree(rest).query(cutp)[0] < LWR] if len(cutp) else cutp
        RELW[Lg] = (np.round(cutp.min(0), 1).tolist() if len(cutp) else None, np.round(cutp.max(0), 1).tolist() if len(cutp) else None, round(float(max(pen, 0) + LWR), 2) if pen > -LWR else 0.0, 'path depth', round(float(max(pnp, 0) + LWR), 2))
    pts = np.vstack([base[keep], face]); T_ = cKDTree(pts)
    def g(q):
        q = q[np.linalg.norm(q - c, axis=1) < RNEAR]
        if not len(q): g.at = c; return 3.0
        d, _ = T_.query(q, distance_upper_bound=3.0); d = np.minimum(d, 3.0); mat = mat0(q) & ~(OT.query(q, distance_upper_bound=LWR)[0] < LWR) if LWR > 0 else mat0(q); v_ = np.where(mat, -d, d); k_ = int(np.argmin(v_)); g.at = q[k_]; return v_[k_]
    return g
LUP = E("LUP", 14.0)                                  # then up out of the open-top window
def legpath(t, u_): return t * u_ if t <= LSL else LSL * u_ + np.array([0, 0, t - LSL])   # slide off the pin along u (LSL), then lift +z
LG = {}; WIN = {}; KL = {}
LPOSES = [int(v) for v in os.environ.get("LPOSES", ",".join(str((KC + d) % 24) for d in (0, 6, 12, 18))).split(",")]
ag = ["spine", "spine-keel", "keel-screw-1", "keel-screw-2", "snap-rib-1", "snap-rib-2"] + GEARS + [f"idler-axle-{j+1}" for j in range(3)]
AGT = cKDTree(np.vstack([ALL[o] for o in ag]))
def _leg_task(Lg):
    n0 = len(rows)
    i, sx = Lg % 4, (1 if Lg < 4 else -1); best = None
    for k in LPOSES:
        q = leg_pose(Lg, k, True); u_ = (PIV[Lg] - A_ALL[Lg, k]); Lout = LSL + LUP; u_ /= np.linalg.norm(u_)
        oth = np.vstack([crank_pose(j, k) for j in range(4) if j != i] + [crank_pose(i, k, (sx,), pins=False), crank_pose(i, k, (-sx,)), JOUR()]
                        + [leg_pose(L2, k, True) for L2 in range(8) if L2 != Lg]); OK_ = cKDTree(vox(oth, 0.3)); worst = (3.0, 0, ""); qv = vox(q, 0.35)
        for t in np.arange(0.25, Lout, 0.5):
            qq = qv + legpath(t, u_)
            m_ = min([(AGT.query(qq, distance_upper_bound=3.0, workers=-1)[0].min(), "spine set, keel"), (OK_.query(qq, distance_upper_bound=3.0, workers=-1)[0].min(), "cranks, other legs")])
            if m_[0] < worst[0]: worst = (m_[0], f"u{t:.2f}", m_[1])
        if best is None or worst[0] > best[0][0] + 0.02 or (abs(worst[0] - best[0][0]) <= 0.02 and k == KC): best = (worst, k, q, u_, Lout)
    worst, k, q, u_, Lout = best; KL[Lg] = k; tick(f"leg {Lg} insertion path")
    _sw = [leg_pose(Lg, kk, True) for kk in range(24)]; PTH = [q + legpath(t, u_) for t in np.arange(0.0, Lout, 0.5)]
    gsh = leg_shell(Lg, vox(np.vstack(_sw + PTH), 0.12), vox(np.vstack(_sw), 0.12))
    _gr, _ga = min((gsh(a_), tuple(np.round(gsh.at, 1))) for a_ in _sw); rows.append((min(_gr, 3.0), F.LEG_PATH.side, f"leg-{Lg} whole (24 poses) NR {NRL[Lg]:.2f} at {_ga}", f"shell at its window (relief {RELW.get(Lg)})", ""))
    tick(f"leg {Lg} whole sweep"); gp = min((gsh(qq), t) for t, qq in zip(np.arange(0.0, Lout, 0.5), PTH))
    if gp[0] < worst[0]: worst = (gp[0], f"u{gp[1]:.2f}", "shell (window + relief)")
    rows.append((min(worst[0], 3.0), 0.0, f"leg-{Lg}", f"assembly path: off its pin along u ({LSL:.1f}) then up {LUP:.0f} through its open-top window @{worst[1]} vs {worst[2]} (crank pose {k})", ""))
    return rows[n0:], KL[Lg], WIN[Lg], RELW.get(Lg)
import multiprocessing as _mp
with _mp.get_context('fork').Pool(int(E('NPROC', 4))) as _pool: _res = _pool.map(_leg_task, range(8), chunksize=1)
for Lg, (_r, _k, _w, _rw) in enumerate(_res):
    rows.extend(_r); KL[Lg] = _k; WIN[Lg] = _w
    if _rw is not None: RELW[Lg] = _rw

print("leg insertion crank poses", KL); tick("leg windows")
tick('legs done')
# 6 drive unit down (+z): tongues into slots 1-3 (TURN), blocks over the gears; legs in (24 poses)
DUQ = np.vstack([ST["drive-unit"], ST["journal-caps"], ST["drive-block-1"], ST["drive-block-2"], ST["drive-ear-1"], ST["drive-ear-2"]])
prow("drive-unit", F.NEIGHBOUR.side, path(DUQ, up, 30, ["spine", "crankshafts", "transfer-small"] + GEARS + [f"idler-axle-{j+1}" for j in range(3)], legs=True), "+z", "(tongues in slots TURN)")
PLACED = ["spine", "crankshafts", "transfer-small", "transfer-big", "drive-unit", "journal-caps", "drive-block-1", "drive-block-2", "drive-ear-1", "drive-ear-2"] + GEARS + [f"idler-axle-{j+1}" for j in range(3)]
for k_ in (1, 2):
    c = ST[f"drive-screw-{k_}"].mean(0); c[2] = ST[f"drive-screw-{k_}"][:, 2].max(); driver(f"drive-screw-{k_}", c, up, [o for o in PLACED if o != "drive-unit"] + [f"drive-block-{3-k_}"], legs=True)
# 7 motor slides into its clamp along +x (out: -x)
prow("n10-motor", 0.0, path(np.vstack([ST["n10-motor"], ST["n10-shaft"]]), (-1, 0, 0), 24, ["spine", "transfer-big", "transfer-small", "journal-caps", "drive-block-1", "drive-block-2", "drive-ear-1", "drive-ear-2"] + GEARS, legs=True), "-x (out of the clamp)")
PLACED += ["n10-motor", "n10-shaft", "pinion", "motor-leads"]
# 8 holder with its post down (+z): post cap tongues into crank 4's slots (TURN); then its screw
HQ = np.vstack([ST["cell-holder"], ST["holder-post"], ST["cell-springs"], ST["nickel-strip"]])
prow("cell-holder", 0.0, path(HQ, up, 30, [o for o in PLACED if o != "spine"], legs=True), "+z")
prow("post-cap", F.NEIGHBOUR.side, path(ST["post-cap"], up, 30, ["spine", "crankshafts"] + GEARS, legs=True), "+z into crank 4's slots", "(TURN)")
c = ST["holder-screw"].mean(0); c[2] = ST["holder-screw"][:, 2].max(); driver("holder-screw", c, up, PLACED + ["cell-springs", "nickel-strip"], legs=True)
PLACED += ["cell-holder", "holder-post", "post-cap", "cell-springs", "nickel-strip"]
for n, ag_ in (("ag13-cells", PLACED), ("cell-lid", PLACED + ["ag13-cells"]), ("jst-xh", PLACED + ["ag13-cells", "cell-lid"])):
    prow(n, 0.0, path(ALL[n], up, 25, [o for o in ag_ if o not in ("cell-holder",) or n == "jst-xh"], legs=True), "+z")
tick('stage 6-8')
# ---------------- base wall pads (1.2 where loaded) and the front-window bulge's outer skin vs the whole legs
LFULL = cKDTree(vox(np.vstack([leg_pose(Lg, k, True) for Lg in range(8) for k in range(24)]), 0.3))
def lf_gap(q, excl=True):
    d, j = LFULL.query(q, distance_upper_bound=4.0); return float(np.minimum(d, 4.0).min())
PADT = 1.2 - BASE_WALL_R; PADS = {}; PADCOV = {}
for k, xc, yw, dl, Lf, eps in SNAPS:                  # snap rib: front wall thickened outward (-y) behind the rib
    PADS[f"pad-snap-{k+1}"] = box((xc - SNW / 2 - 1.5, yw - BASE_WALL_R - PADT, SNZ - 0.5), (xc + SNW / 2 + 1.5, yw - BASE_WALL_R, SNZ + 2.9))
for Lg in range(8):                                   # leg window: a 2 mm ring round the notch, outer skin pushed out
    c = PIV[Lg]; zl_ = (BA.Z_LEDGE - motion.ORIGIN[2]) * S; cen = j2r((BA.CX, BA.CY, 0))[:2]
    o2 = np.vstack([OUTER]); dE_ = WEXT[Lg].query(o2, distance_upper_bound=WR + 2.0, workers=-1)[0]; rg = o2[(dE_ >= WR) & (dE_ < WR + 2.0) & (o2[:, 2] < zl_)]
    d2 = rg[:, :2] - cen; d2 /= np.linalg.norm(d2, axis=1)[:, None]; pw = rg + np.c_[d2 * PADT, np.zeros(len(rg))]
    own = np.vstack([leg_pose(Lg, k, True) for k in range(24)]); own = own[np.linalg.norm(own - PIV[Lg], axis=1) > RN]
    gk = cKDTree(own).query(pw, distance_upper_bound=4.0)[0]; ok_ = gk >= F.LEG_PATH.side + 0.36
    PADCOV[Lg] = round(100 * ok_.mean(), 0); PADS[f"pad-window-{Lg}"] = np.vstack([rg[ok_] + np.c_[d2[ok_] * s_, np.zeros(ok_.sum())] for s_ in np.linspace(0, PADT, 3)]) if ok_.any() else rg[:0]
_tb = BD["rear-tab"]; TABX = float(np.abs(_tb[:, 0]).max()); TABZ = float(_tb[:, 2].min())
_wb = WALL_PTS[(WALL_PTS[:, 1] > 15) & (np.abs(WALL_PTS[:, 0]) <= TABX) & (WALL_PTS[:, 2] >= TABZ) & (WALL_PTS[:, 2] <= RIMR) & ~((np.abs(WALL_PTS[:, 0]) <= PKT[1]) & (WALL_PTS[:, 2] <= PKT[3]))]
if len(_wb): PADS["pad-rear-tab"] = np.vstack([_wb - [0, s_, 0] for s_ in np.linspace(0, PADT, 3)])   # back sheet thickened inward behind the tab's rib
for n, q in PADS.items():
    if not len(q): continue
    g_ = lf_gap(q) if not n.startswith("pad-window") else None
    if n.startswith("pad-window"):
        Lg = int(n.split("-")[-1]); d_ = LFULL.query(q, distance_upper_bound=4.0)[0]
        own = np.vstack([leg_pose(Lg, k, True) for k in range(24)]); own = own[np.linalg.norm(own - PIV[Lg], axis=1) > RN]
        g_ = float(cKDTree(own).query(q, distance_upper_bound=4.0)[0].min())
    oth = min([KD[o].query(q, distance_upper_bound=3.0)[0].min() for o in ALL if o not in SEATED_SHELL and not o.startswith("snap-") and bbd(o, o) >= 0 and np.linalg.norm(np.maximum(0, np.maximum(BB[o][0] - q.max(0), q.min(0) - BB[o][1]))) < 3] + [3.0])
    rows.append((min(g_, 4.0), F.LEG_PATH.side, n, f"(+{PADT:.2f} to 1.2) vs whole legs 24 poses (window: own leg off its ball)", np.round(q.mean(0), 1)))
    rows.append((oth, F.NEIGHBOUR.side, n, "vs every other part", ""))
if RELD > 0 and cut.any():                            # outer skin of the front-window bulge (floor + wall) and its 45 deg chamfer below
    fl, nn_ = BULGE; skin = fl + nn_ * BASE_WALL_R; zb_ = skin[:, 2].min()
    bot = skin[skin[:, 2] < zb_ + 0.3]; dep = RELIEF[2]; ch = np.vstack([bot - np.c_[nn_[skin[:, 2] < zb_ + 0.3][:, :2] * s_, np.full(len(bot), s_)] for s_ in np.linspace(0, dep, 5)])
    gsk = np.minimum(LFULL.query(skin, distance_upper_bound=4.0)[0], 4.0); BUL = []; keep_ = np.zeros(len(skin), bool)
    for c_ in range(_nc):
        m_ = _lb == c_; BUL.append((PATCHES[c_][:2], PATCHES[c_][2], "bulge" if gsk[m_].min() >= F.LEG_PATH.side else "through", round(float(gsk[m_].min()), 2))); keep_ |= m_ & (gsk[m_].min() >= F.LEG_PATH.side)
    sk = skin[keep_]; mb = (skin[:, 2] < zb_ + 0.3) & keep_
    ch = np.vstack([skin[mb] - np.c_[nn_[mb][:, :2] * s_, np.full(mb.sum(), s_)] for s_ in np.linspace(0, dep, 5)]) if mb.any() else sk[:0]
    sk = np.vstack([sk, ch]); own = LFULL.query(sk, distance_upper_bound=4.0)[0] if len(sk) else np.array([4.0])
    rows.append((float(np.minimum(own, 4.0).min()), F.LEG_PATH.side, "front-window bulges (outer skin + 45° chamfer)", f"whole legs (24 poses), depth {dep:.2f}", ""))
    print("BULGE/THROUGH per patch (bbox, depth, kind, skin gap to legs)", BUL)
tick("paths, drivers"); rows.sort(key=lambda r: r[0] - r[1])
print(f"S {S} m {M} ZI {ZI} cranks y {np.round(Oy, 2).tolist()} z {Oz:.2f} idlers {np.round(I, 2).tolist()} T {np.round(T, 2)} "
      f"pinion {np.round(Mc, 2)} motor x {mx0:.1f}..{mx1:.1f} pack c ({cy},{cz}) hx {hx:.2f} hy {hy:.2f} ytop {ytop:.2f} SL {SL:.2f} END_R {END_R:.2f}")
print("snaps (k, x, wall y, travel, L, strain)", [tuple(round(float(v), 3) for v in s_) for s_ in SNAPS], "D23", D23, "D23C", D23C, "TAIL", TAIL, "holder notch depth", round(HNOTCH_D, 2), "post foot z", round(zhp, 2), "spine rise", round(SPRISE, 2), "REL", REL, "body wall robot", BO.WALL * S, "base wall robot", BASE_WALL_R, "pivot swing (leg, yaw, pitch deg)", sw)
print(f"{'gap':>7} {'need':>5} {'margin':>7}  pair")
for r in rows[:int(E("N", 45))]: print(f"{r[0]:7.2f} {r[1]:5.2f} {r[0]-r[1]:7.2f}  {r[2]} <> {r[3]} {r[4]}")
TOLN2 = 0.1                                          # N2 tolerance: a gap within 0.1 of its need is reported "at tolerance", not FAIL
_fail = [r for r in rows if r[0] - r[1] < -TOLN2 - 1e-6]
_tol = [r for r in rows if -TOLN2 - 1e-6 <= r[0] - r[1] < -1e-6 or (r[1] == 0.0 and -TOLN2 - 1e-6 <= r[0] <= 1e-6)]
print("FAILING:", len(_fail), "AT TOLERANCE (within 0.1 under need):", len(_tol), "of", len(rows), "checks;", len(seats), "designed contacts")
for r in _fail: print("  FAIL", round(r[0], 2), r[1], r[2], "<>", r[3])
for r in _tol: print("  at tolerance", round(r[0], 2), r[1], r[2], "<>", r[3])
print("leg window reliefs (bbox, depth)", RELW); print("PADCOV % of each window ring padded", PADCOV, "WIN", WIN, "KC", KC, "holder notches", NOTCHES if HNOTCH else None, "notch depth y", round(HNOTCH_D, 2), "spring seat y0", round(SPRING_Y0, 2) if HNOTCH else None,
      "holder front y", round(cy - hy, 2), "relief patches", PATCHES if RELD > 0 else None, "band thickness robot", round((BA.LEDGE + 0.5 * BASE_WALL_R / S) * S, 2),
      "tab |x|", round(TABX, 2), "tab z0", round(TABZ, 2), "pads", {n: len(q) for n, q in PADS.items()}, "slot half-width", SLW, "tongue", TG, ztg, "cap z", round(ytop, 2), round(ZCAP, 2), "post y", round(PY0, 2), round(PY1, 2))
if E("SEATS", 0):
    for s_ in seats: print("   seat:", *s_)
json.dump([[float(r[0]), float(r[1]), r[2], r[3]] for r in rows], open(os.environ.get("JOUT", os.path.join(OUT, "rows.json")), "w"))
if E("FIG", 0):                                       # Morante's picture: base outer skin at one leg window, old Ø8 window vs the new neck-sized one, S 0.70
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    LGF = int(E("FIGLEG", 1)); c = PIV[LGF]; sx_ = 1 if c[0] > 0 else -1
    sk = np.vstack([OUTER, SURF]); sk = sk[(np.linalg.norm(sk - c, axis=1) < 20) & (sk[:, 2] < (BA.Z_LEDGE - motion.ORIGIN[2]) * S + 4)]
    r_ = np.linalg.norm(sk[:, :2] - c[:2], axis=1); old = (r_ < NR) & (sk[:, 2] > c[2] - np.sqrt(np.maximum(NR**2 - r_**2, 0))); new = in_win(LGF, sk) | old
    nk = np.vstack([leg_pose(LGF, k, True) for k in range(24)]); nk = nk[np.linalg.norm(nk - c, axis=1) <= RN]
    fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    for a_, m_, tt in ((ax[0], old, f"old window: Ø{2*NR:.0f} round notch (+ 0.85 relief patches)"), (ax[1], new, "new window: neck sweep over 24 poses + 0.9 (open top)")):
        a_.scatter(sk[~m_][:, 1], sk[~m_][:, 2], s=3, c="#bbbbbb", lw=0); a_.scatter(sk[m_][:, 1], sk[m_][:, 2], s=3, c="#d62728", lw=0)
        a_.scatter(nk[:, 1], nk[:, 2], s=1, c="#1f77b4", lw=0, alpha=0.5); a_.set_aspect("equal"); a_.set_title(tt, fontsize=9); a_.set_xlabel("y (mm, robot S 0.70)"); a_.grid(alpha=.3)
        a_.set_xlim(c[1] - 17, c[1] + 17); a_.set_ylim(c[2] - 12, c[2] + 14)
    ax[0].set_ylabel("z (mm)"); fig.suptitle(f"Base shell seen from outside at leg {LGF} window (pivot y {c[1]:.1f}, z {c[2]:.1f}); red = wall removed, blue = real leg neck (24 poses)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "window_old_vs_new.png"), dpi=130)
    print("window removal on the outer skin (old, new) points", int(old.sum()), int(new.sum()), "new bbox", np.round(sk[new].min(0), 1).tolist(), np.round(sk[new].max(0), 1).tolist())
