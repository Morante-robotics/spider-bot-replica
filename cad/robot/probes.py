"""N2 plan probes: every number design-plan.md rests on, run on the N1 meshes (cad/mockup/n1.py) and N0's motion.

Each probe prints its result; the plan names the probe next to each number. Envelopes are real: bare part + walls
(1.2 loaded, 0.8 elsewhere) + fits from cad/fits.py + contacts; idlers at the positions the gear geometry gives; arm
ends Ø3.5 bore + 0.8 walls (Ø3 ball) or Ø2.5 + 0.8 (Ø2 ball). Not a check of a model: N2 is not modelled yet.

Usage (repo root):
    uv run python cad/robot/probes.py [inside arms pivot gear cell pins asm]   # geometry, ≈ 20 s with the N1 cache
    uv run python cad/robot/probes.py slice     # slicer support grams for body/base candidates (≈ 3-5 min, parallel)
    uv run python cad/robot/probes.py figure cad/robot/images/plan-windows.png   # N1 vs N2 windows and rim
"""
import os, sys, subprocess, json, math, tempfile
import numpy as np
from scipy.spatial import cKDTree, ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "cad", "mockup"), os.path.join(ROOT, "tools"), ROOT]
import n0, n1  # noqa: E402
from cad import fits as F  # noqa: E402

# ---------------------------------------------------------------- bought parts (datasheet, measure on arrival)
MOTOR = (24.0, 10.0, 12.0)       # N10 gearmotor body: length × width × height (hardware.md, plan rev 1)
SHAFT = (10.0, 3.0)              # D-shaft length, Ø
CELL_D, CELL_T = 11.6, 5.4       # AG13 / LR44 (hardware.md)
CELL_NEG_CAP = 8.0               # LR44 negative cap Ø (datasheet ≈ 7.6-8.9): the negative contact must stay inside it
SPRING = (1.5, 5.0)              # negative contact: compressed coil spring height, coil Ø (to buy; < CELL_NEG_CAP)
PLATE = 0.5                      # positive contact: nickel / brass plate thickness
SWITCH = (12.0, 6.0, 6.0)        # SS12D00 (hardware.md)
# ---------------------------------------------------------------- walls and design numbers
W_LOAD, W_MIN = 1.2, 0.8         # cad-rules §3.2
CLAMP_W = 1.2                    # motor seat walls, floor and clamp bar
BODY_WALL = {"D4a 3.0": 3.0, "D4b 1.6": 1.6}   # jenscolt's 3 mm (N1 WALL_DOME) vs 1.6 mm (same outside)
BASE_WALL = 1.2                  # N1 WALL_BASE
GEAR_W = 3.0                     # spur face width (gear train v2)
ARM_R = 1.4                      # arm bar half-thickness (2.8 mm: ≥ 2 mm tongue rule, loaded)
BALLS = {"Ø3 ball": 3.0, "Ø2 ball": 2.0}
CRANK_DY = (-1.5, -0.5, 2.5, 0.0)  # rev 2 only (Ø3 balls, mm at S 0.60, rescaled by S/0.6 in pr_inside)
SLIDE = 1.0                      # ball travel in its bore over a turn (pr1 arm length 17.5-18.3 → ≤ 1.0)


def end_r(ball):                 # arm end radius: bore (TURN) + 0.8 wall
    return F.bore(ball, F.TURN) / 2 + W_MIN


def p_at(S, **kw):
    """N0/N1 parameters at scale S: the crank scales with the look (r, XC, H, DY are 60 %-of-jenscolt numbers)."""
    p = {**n0.P0, **n1.P0_N1}
    k = S / 0.60
    p.update(S=S, r=p["r"] * k, XC=p["XC"] * k, H=p["H"] * k, DY=p["DY"] * k)
    p.update(kw)
    return p


# ---------------------------------------------------------------- geometry helpers
def legs_ax(p, dy=(0, 0, 0, 0), dh=(0, 0, 0, 0), xc=None, poses=36):
    """Per leg (8): pivot P, crank centre O, ball centres A (poses, 3), unit u = P − A, for per-crank tweaks."""
    c = np.array([n0.TL.CENTER[0] * n0.K120, n0.TL.CENTER[1] * n0.K120, n0.TL.BASE_BOTTOM * n0.K120])
    B = dict(c=c)
    th = np.linspace(0, 2 * np.pi, poses, endpoint=False)
    out = []
    for side, sx in (("R", 1), ("L", -1)):
        for i, (x, y) in enumerate(n0.TL.NOTCHES_RIGHT):
            P = n0.to_frame((x * n0.K120, y * n0.K120, n0.TL.NOTCH_Z * n0.K120), B, p)
            XC = p["XC"] if xc is None else xc[i]
            O = np.array([XC, P[1] + p["DY"] + dy[i], P[2] + p["H"] + dh[i]])
            ph = np.pi * n0.TL.GROUP[side][i]
            A = O + p["r"] * (np.cos(th + ph)[:, None] * [0, -1, 0] + np.sin(th + ph)[:, None] * [0, 0, 1])
            s = np.array([sx, 1, 1])
            out.append(dict(P=P * s, O=O * s, A=A * s, u=n0.unit(P * s - A * s), side=side, i=i))
    return out


def seg_pts(a, b, step=0.25):
    n = max(2, int(np.linalg.norm(b - a) / step) + 1)
    return a + np.linspace(0, 1, n)[:, None] * (b - a)


def arm_parts(L, k, ball):
    """Arm capsules at pose k: (points, radius) for the end tube and the bar to the pivot."""
    A, u, P = L["A"][k], L["u"][k], L["P"]
    e = ball / 2 + SLIDE / 2 + W_MIN                      # tube reaches past the ball both ways
    return [(seg_pts(A - u * e, A + u * (e + SLIDE)), end_r(ball)), (seg_pts(A + u * e, P - u * 3.0), ARM_R)]


def capsule_gap(c1, c2):
    (p1, r1), (p2, r2) = c1, c2
    return cKDTree(p1).query(p2)[0].min() - r1 - r2


def box_pts(lo, hi, h=1.5):          # 1.5 mm face samples: gaps good to ≈ ±0.3
    return n1.boxpts(np.asarray(lo, float), np.asarray(hi, float), n=max(3, int(np.max(np.subtract(hi, lo)) / h)))


CACHE = os.path.join(HERE, "out", ".cache")    # probe cache (not in git): shell samples and room grids per S
ROOM_PITCH, ROOM_UB = 0.5, 4.5                  # room grid spacing; distances past ROOM_UB are capped (room ≥ ≈ 3)
_SHELL = {}


def _outer_mask(V, Fc, P, wall):
    """Body samples on the OUTER skin: the body voxelised, its cavity filled column-wise from the footprint (as the
    D4b slice, foot = 2-D hull of the body's plan), depth of each sample in that solid ≤ wall / 3 (inner faces
    lie ≈ one wall deep)."""
    import trimesh
    from scipy import ndimage
    pitch = 0.3
    vg = trimesh.Trimesh(V, Fc, process=False).voxelized(pitch)
    G, org = vg.matrix.copy(), vg.translation
    z0 = np.argwhere(G.any((0, 1)))[0][0]
    ring = np.argwhere(G.any(2))            # footprint: 2-D hull of the body's plan (the skirt bottom is not flat)
    h2 = ConvexHull(ring)
    ij = np.argwhere(np.ones(G.shape[:2], bool))
    foot = ((ij @ h2.equations[:, :2].T + h2.equations[:, 2]) <= 0.5).all(1).reshape(G.shape[:2])
    top = np.where(G.any(2), G.shape[2] - 1 - np.argmax(G[:, :, ::-1], 2), 0)
    zz = np.arange(G.shape[2])[None, None]
    full = np.pad(G | (foot[:, :, None] & (zz <= top[:, :, None]) & (zz >= z0)), 1)
    d = ndimage.distance_transform_edt(full) * pitch
    ijk = np.clip(np.round((P - org) / pitch).astype(int) + 1, 0, np.array(full.shape) - 1)
    return d[ijk[:, 0], ijk[:, 1], ijk[:, 2]] <= wall / 3


def shell(S):
    """Inner faces of the N1 body (+ eyes) and the N1 base skin at scale S: KD-trees of dense samples (0.3 mm) + hull,
    and the body's outer-skin samples (for a thinner wall, D4b). Samples cached on disk per S."""
    if S not in _SHELL:
        st = n1.static(p_at(S), n1.P1)
        path = os.path.join(CACHE, f"shell_{S:.3f}.npz")
        if os.path.exists(path):
            c = dict(np.load(path))
            pb, pa, ob = c["pb"], c["pa"], c["ob"]
        else:
            pb, _ = n1.dense(st["ball_v"], st["ball_f"], 0.6)
            pa, _ = n1.dense(st["base_v"], st["base_f"], 0.6)
            ob = _outer_mask(st["ball_v"], st["ball_f"], pb, 3.0 * S / 0.6)
            os.makedirs(CACHE, exist_ok=True)
            np.savez_compressed(path, pb=pb, pa=pa, ob=ob)
        h = ConvexHull(np.vstack([st["ball_v"], st["base_v"]]))
        _SHELL[S] = dict(tb=cKDTree(pb), ta=cKDTree(pa), to=cKDTree(pb[ob]), n=h.equations[:, :3], d=h.equations[:, 3],
                         st=st, nout=int(ob.sum()), nall=len(pb))
    return _SHELL[S]


def _out_hull(X, sh, tol=0.0):
    return np.concatenate([(X[i:i + 8000] @ sh["n"].T + sh["d"]).max(1) > tol for i in range(0, len(X), 8000)]) \
        if len(X) else np.zeros(0, bool)


def _gap_exact(X, S, body_wall):
    """Room (mm) from each point to the body's inner face and the base skin. Every wall (D4a 3.0, D4b 1.6): the outer
    skin offset inward by that wall (jenscolt's inner posts / housings are dropped, rev 3). Points
    outside the hull: −9. Room past ROOM_UB − 1.5 is capped."""
    sh = shell(S)
    out = _out_hull(X, sh)
    gb = sh["to"].query(X, distance_upper_bound=ROOM_UB + body_wall, workers=-1)[0] - 0.3 - body_wall
    ga = sh["ta"].query(X, distance_upper_bound=ROOM_UB + BASE_WALL, workers=-1)[0] - 0.3 - BASE_WALL
    g = np.minimum(np.minimum(gb, ga), ROOM_UB - 0.3)
    g[out] = -9
    return g


_ROOM = {}


def room_grid(S, body_wall):
    """_gap_exact on a ROOM_PITCH grid over the hull's box (cached on disk): trilinear lookups for the coarse search."""
    key = (S, body_wall)
    if key not in _ROOM:
        path = os.path.join(CACHE, f"room3_{S:.3f}_{body_wall:.1f}_{ROOM_PITCH}.npz")
        if os.path.exists(path):
            _ROOM[key] = dict(np.load(path))
        else:
            sh = shell(S)
            V = np.vstack([sh["st"]["ball_v"], sh["st"]["base_v"]])
            lo, hi = V.min(0) - 1, V.max(0) + 1
            ax = [np.arange(lo[k], hi[k] + ROOM_PITCH, ROOM_PITCH) for k in range(3)]
            Q = np.array(np.meshgrid(*ax, indexing="ij")).reshape(3, -1).T
            g = np.full(len(Q), -9.0)
            ins = ~_out_hull(Q, sh, ROOM_PITCH)
            g[ins] = _gap_exact(Q[ins], S, body_wall)
            _ROOM[key] = dict(lo=lo, g=g.reshape([len(a) for a in ax]))
            os.makedirs(CACHE, exist_ok=True)
            np.savez_compressed(path, **_ROOM[key])
    return _ROOM[key]


def inside_gap(X, S, body_wall, exact=False):
    """Least room (mm) from points X to the inner face of body and base (see _gap_exact). exact=False: trilinear
    lookup in room_grid (≈ 1 ms; good to ≈ 0.1 off the hull edge), used for the coarse search only."""
    if exact:
        return _gap_exact(X, S, body_wall).min()
    from scipy.ndimage import map_coordinates
    R = room_grid(S, body_wall)
    return map_coordinates(R["g"], ((X - R["lo"]) / ROOM_PITCH).T, order=1, mode="nearest").min()


# ---------------------------------------------------------------- gears
INV = lambda a: math.tan(a) - a  # noqa: E731
ALPHA = math.radians(20)


def tip_thickness(z, m, x, ha=1.0):
    d, da = m * z, m * (z + 2 * ha + 2 * x)
    s = m * (math.pi / 2 + 2 * x * math.tan(ALPHA))
    aa = math.acos(d * math.cos(ALPHA) / da)
    return da * (s / d + INV(ALPHA) - INV(aa)), da


def idler_pos(c1, c2, r1, r2, ri, up=True):
    """Idler centre (y, z) meshing two gears at c1, c2 (y, z) with pitch radii r1, r2."""
    a, b = r1 + ri, r2 + ri
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    D = np.linalg.norm(c2 - c1)
    if D > a + b:
        return None
    t = (a * a - b * b + D * D) / (2 * D)
    h = math.sqrt(max(a * a - t * t, 0))
    e = (c2 - c1) / D
    n = np.array([-e[1], e[0]]) * (1 if up else -1)
    if n[1] < 0 and up or n[1] > 0 and not up:
        n = -n
    return c1 + e * t + n * h


def train(p, m=0.6, zc=10, x_c=0.42, dy=(0, 0, 0, 0)):
    """Crank gears and idlers along the strip: list of (name, y, z, tip radius), each idler above or below,
    whichever leaves the most room (below: floor at z = BASE_WALL + GEAR_TIP)."""
    L = legs_ax(p, dy=dy)
    ys = [L[i]["O"][1] for i in range(4)]
    z0 = L[0]["O"][2]
    rc = m * zc / 2
    tipc = m * (zc + 2 + 2 * x_c) / 2
    g = [(f"crank {i + 1} {zc}T", y, z0, tipc) for i, y in enumerate(ys)]
    for i in range(3):
        D = ys[i + 1] - ys[i]
        best = None
        for zi in range(10, 17):
            ri = m * zi / 2
            for up in (False, True):
                c = idler_pos((ys[i], z0), (ys[i + 1], z0), rc, rc, ri, up)
                if c is None:
                    continue
                tip = m * (zi + 2 - 2 * x_c) / 2           # idler takes −x (zero-sum shift)
                low = c[1] - tip - F.GEAR_TIP.side - BASE_WALL
                top = c[1] + tip + F.GEAR_TIP.side
                score = (low >= 0, -top if low >= 0 else low)
                if best is None or score > best[0]:
                    best = (score, (f"idler {i + 1}-{i + 2} {zi}T {'up' if up else 'down'}", c[0], c[1], tip), D)
        g.append(best[1])
    return g, z0


# ---------------------------------------------------------------- probes
def arm_cloud(L, ball, step=2):
    """All arm points of all legs over the turn, with their radii (for one vectorised gap to a box)."""
    X, R = [], []
    for Lg in L:
        for k in range(0, len(Lg["A"]), step):
            for pts, r in arm_parts(Lg, k, ball):
                X.append(pts)
                R.append(np.full(len(pts), r))
    return np.vstack(X), np.concatenate(R)


def crank_sweeps(L):
    """Stationary keep-outs round each crank's moving web + ball (r + 1.5 radius, x from wall to ball end)."""
    out = []
    for Lg in L:
        O = Lg["O"]
        r = float(np.linalg.norm(Lg["A"][0] - O))         # the crank radius at this S (rev 3 used S 0.60's)
        x0, x1 = sorted((np.sign(O[0]) * 3.4, O[0] + np.sign(O[0]) * 1.5))
        R = r + 1.5 + F.LEG_PATH.side
        out.append((np.array([x0, O[1] - R, O[2] - R]), np.array([x1, O[1] + R, O[2] + R])))
    return out


_HB = {}


def holder_best(S, zf, hold, wall=3.0, exact=False):
    """Best Y for the holder with its floor at zf (cached): (least room to the shell, y)."""
    if (S, zf, wall, exact) not in _HB:
        _HB[S, zf, wall, exact] = max((inside_gap(box_pts(np.array([-hold[0] / 2, yc - hold[1] / 2, zf]),
                                                          np.array([-hold[0] / 2, yc - hold[1] / 2, zf]) + hold),
                                                  S, wall, exact), yc) for yc in np.arange(-12, 12.1, 2.0))
    return _HB[S, zf, wall, exact]


def pr_inside(scales=(0.60, 0.62, 0.65), dy=CRANK_DY, ball=3.0, walls=(3.0,), top=6):
    """Item 1: D1a/b/c with real envelopes; true crank/motor ratio of each. Body wall D4a 3.0 (jenscolt's inner
    faces) or D4b (outer skin − wall). Motor + seat walls + clamp; pinion / crown / worm in the gear plane; holder
    D9a above the motor; arms with real ends, LEG_PATH 0.8; crank sweeps; strip top from the idler layout.
    Rev 3 speed: shell samples and room grids cached on disk per S (out/.cache); every position is scored on the
    grid (trilinear), the best `top` per option re-scored exactly (KD on the samples), as rev 2 did everywhere."""
    print("== inside fit (pr5 rev 3): least room, mm (≥ 0 fits); ball", ball, "crank offsets", dy, "==")
    hold = cell_holder()["D9a printed, axis Y"]
    mw = np.array(MOTOR) + 2 * (F.MOTOR_SEAT.side + CLAMP_W)
    for S in scales:
        p = p_at(S)
        k = S / 0.6
        L = legs_ax(p, poses=24, dy=tuple(d * k for d in dy))
        X, Rr = arm_cloud(L, ball)
        g, z0 = train(p, dy=tuple(d * k for d in dy))
        gtop = max(z + t + F.GEAR_TIP.side for _, y, z, t in g)
        gy = [y for _, y, _, _ in g[:4]]
        sweeps = crank_sweeps(L)
        xw = GEAR_W / 2 + F.GEAR_THRUST_CRANK.side + W_LOAD
        for wall in walls:
            for opt, ratio in (("D1a", 12 / 10), ("D1b", 10 / 20), ("D1c", 1 / 10)):
                cands = []
                for zm in np.arange(8, 32.1, 1.0):
                    for ym in np.arange(-16, 16.1, 2.0):
                        if opt == "D1a":   # along X, left of the spine, gearbox face on the wall, pinion in the plane
                            lo = np.array([-xw - mw[0], ym - mw[1] / 2, zm - mw[2] / 2])
                            d = min(math.hypot(ym - y, zm - z0) for y in gy)
                            if d < 6.6 - 1e-6 or d > 13.8:          # direct mesh 6.6, or one 12T idler ≤ 13.8
                                continue
                            clash = [n for n, y, z, t in g if math.hypot(ym - y, zm - z) < 4.2 + t + F.GEAR_TIP.side
                                     and abs(math.hypot(ym - y, zm - z) - (3.6 + t - 0.6)) > 0.7]
                            if clash:
                                continue
                            extra = []
                            mot = [(lo, lo + mw)]
                        elif opt == "D1b":  # along Y at x 0 above the strip, crown pair at the shaft end
                            lo = np.array([-mw[1] / 2, ym - mw[0] / 2, zm - mw[2] / 2])
                            mot = [(lo, lo + [mw[1], mw[0], mw[2]])]
                            extra = [(np.array([-7.1, lo[1] - 10.5, zm - 7.1]), np.array([7.1, lo[1] - 0.5, zm + 2.0]))]
                        else:               # worm along Y over the crank wheels, motor in line behind the strip
                            zm = z0 + 3.0 + 3.0 + F.GEAR_TIP.side
                            lo = np.array([-mw[1] / 2, max(gy) + 4.5, zm - mw[2] / 2])
                            mot = [(lo, lo + [mw[1], mw[0], mw[2]])]
                            extra = [(np.array([-4.0, min(gy) - 4.5, zm - 4.0]), np.array([4.0, lo[1], zm + 4.0]))]
                        boxes = mot + extra

                        def score(exact, boxes=boxes, lo=lo, ym=ym, zm=zm):
                            gm = min(inside_gap(box_pts(a, b), S, wall, exact) for a, b in boxes)
                            ga = min((n0.pt_box(X, a, b) - Rr).min() - F.LEG_PATH.side for a, b in boxes)
                            gs = min(np.max(np.maximum(l1 - h2, l2 - h1)) for l1, h1 in sweeps for l2, h2 in boxes)
                            gg = (lo[2] - gtop) if opt == "D1b" else 9.0
                            top_ = max(b[2] for a, b in boxes)
                            cb = holder_best(S, round(top_ + 0.5, 1), hold, wall, exact)
                            return min(gm, ga, gs, gg, cb[0]), dict(ym=ym, zm=zm, gm=gm, ga=ga, gs=gs, gg=gg, gc=cb[0],
                                                                    ct=top_ + 0.5)
                        cands.append((score(False)[0], score))
                        if opt == "D1c":
                            break
                    if opt == "D1c" and cands:
                        break
                cands.sort(key=lambda t: -t[0])
                sc, d = max((f(True) for _, f in cands[:top]), key=lambda t: t[0])
                print(f"S {S:.2f} D4 {wall:.1f} {opt} crank/motor {ratio:.2f}: least {sc:+.2f}  motor↔shell "
                      f"{d['gm']:+.2f} arms↔motor {d['ga']:+.2f} cranks↔motor {d['gs']:+.2f} strip {d['gg']:+.2f} "
                      f"holder↔shell {d['gc']:+.2f} (motor axis y {d['ym']:.0f} z {d['zm']:.0f}, holder floor z "
                      f"{d['ct']:.1f})", flush=True)
        print(f"S {S:.2f}: strip top z {gtop:.1f}; " + ", ".join(f"{n} z {z:.1f}" for n, y, z, t in g[4:]))


# ---------------------------------------------------------------- inside layouts (rev 3: S fixed, Ø2 balls)
BALL_D2 = 2.0                       # Morante, 2026-11-19: Ø2 balls at S 0.65
CRANK_DY_D2 = (0.0, 0.0, 2.0, 0.0)  # rev 3 only: mm at S 0.60 (rescaled to 0, 0, 2.17, 0 at S 0.65)
S_FIX = 0.65                        # Morante, 2026-11-19
STALL = 40.0                        # N10 stall torque at 3 V, N·mm (assumed ≈ 0.4 kg·cm, typical N10 listing; measure)
CROWN = dict(z_pinion=10, z_crown=20, z_spur=10, m=0.6, x=0.42, r_in=5.4, r_out=6.9, disc=1.6)  # B1, see pr_crown
LEDS = {5.0: (5.8, 8.6), 3.0: (3.8, 5.3)}   # LED Ø: (flange Ø, dome tip to flange back), datasheet
JST_XH = (17.0, 8.0, 6.0)           # mated 2-pin JST-XH wire pair (hardware.md; datasheet, measure on arrival)
M3_HEAD, M3_NUT = (5.5, 3.0), (5.5, 2.4)   # socket head Ø × h, nut AF × t (hardware.md)
CRANK_DY_65 = (0.0, 0.0, 2.0, 0.0)  # rev 4, frozen: per-crank Y offsets in mm AT S 0.65 (no rescale), pr_arms(0.65)
_ARMF = {}


def arm_field(S, ball, dy):
    """Room (mm) from grid points to the swept arms (ends and bars, all legs, a full turn), LEG_PATH taken off;
    same grid as room_grid; cached on disk per S, ball, offsets."""
    key = (S, ball, tuple(dy))          # dy in mm at S (rev 4; rev 3 files without «mmS» were rescaled)
    if key not in _ARMF:
        path = os.path.join(CACHE, f"arms_{S:.3f}_{ball}_{'_'.join(f'{d:g}' for d in dy)}_{ROOM_PITCH}_mmS.npz")
        if os.path.exists(path):
            _ARMF[key] = dict(np.load(path))
        else:
            L = legs_ax(p_at(S), poses=24, dy=tuple(dy))
            X, R = arm_cloud(L, ball, step=1)
            G = room_grid(S, 3.0)
            ax = [G["lo"][i] + ROOM_PITCH * np.arange(G["g"].shape[i]) for i in range(3)]
            Q = np.array(np.meshgrid(*ax, indexing="ij")).reshape(3, -1).T
            f = np.full(len(Q), ROOM_UB)
            near = np.all((Q > X.min(0) - ROOM_UB - 3) & (Q < X.max(0) + ROOM_UB + 3), 1)
            for r in np.unique(R):
                d = cKDTree(X[R == r]).query(Q[near], distance_upper_bound=ROOM_UB + r + 1, workers=-1)[0]
                f[near] = np.minimum(f[near], d - r - F.LEG_PATH.side)
            _ARMF[key] = dict(lo=G["lo"], g=np.minimum(f, ROOM_UB).reshape(G["g"].shape), X=X, R=R)
            os.makedirs(CACHE, exist_ok=True)
            np.savez_compressed(path, **_ARMF[key])
    return _ARMF[key]


def _look(fld, X):
    from scipy.ndimage import map_coordinates
    return map_coordinates(fld["g"], ((X - fld["lo"]) / ROOM_PITCH).T, order=1, mode="nearest")


def box_sep(a, b):
    """Separation of two axis boxes (lo, hi): > 0 apart, < 0 overlap depth along the least axis."""
    return np.max(np.maximum(a[0] - b[1], b[0] - a[1]))


def holders():
    """Cell holder shapes (x, y, z) per layout; each a list of boxes (two packs = two boxes). Bays: cell Ø + WINDOW,
    walls 0.8 between bays, 1.2 outside; stack: cells + spring + plate + floor + lid + WINDOW."""
    bay = CELL_D + 2 * F.WINDOW.side
    row = lambda n: n * bay + (n - 1) * W_MIN + 2 * W_LOAD                       # n bays in a row
    flat = CELL_T + SPRING[0] + PLATE + 2 * W_LOAD + F.WINDOW.side              # one cell lying flat, lid strap
    edge = 2 * CELL_T + SPRING[0] + PLATE + 2 * W_LOAD + F.WINDOW.side          # two cells stacked (series), on edge
    up1 = CELL_T + SPRING[0] + PLATE + 2 * W_LOAD + F.WINDOW.side               # one cell on edge
    h = bay + 2 * W_LOAD
    return {
        "H1 2S stacks on edge, 3 across X (rev 2)": [(row(3), edge, h)],
        "H1r same, 3 along Y": [(edge, row(3), h)],
        "H1z 2S stacks upright (axis Z)": [(row(3), h, edge)],
        "H2 flat 3×2, one layer (lid strap = series)": [(row(3), row(2), flat)],
        "H2r flat 2×3": [(row(2), row(3), flat)],
        "H3 two 3P packs flat, rows along Y": [(h, row(3), flat)] * 2,
        "H3e two 3P packs on edge, rows along Y": [(up1, row(3), h)] * 2,
        "H3x two 3P packs flat, rows along X": [(row(3), h, flat)] * 2,
    }


def drives(p, g, z0):
    """Motor options (name, ratio, list of (box lo, hi), meshing box index exempt from the strip) as functions of
    the motor axis (y, z) [and x for along-X]. Same envelopes as pr_inside rev 2."""
    mw = np.array(MOTOR) + 2 * (F.MOTOR_SEAT.side + CLAMP_W)
    xw = GEAR_W / 2 + F.GEAR_THRUST_CRANK.side + W_LOAD
    gy = [y for _, y, _, _ in g[:4]]
    out = []

    def d1a(ym, zm, side=-1):
        d = min(math.hypot(ym - y, zm - z0) for y in gy)
        if d < 6.6 - 1e-6 or d > 13.8:
            return None
        if [n for n, y, z, t in g if math.hypot(ym - y, zm - z) < 4.2 + t + F.GEAR_TIP.side
                and abs(math.hypot(ym - y, zm - z) - (3.6 + t - 0.6)) > 0.7]:
            return None
        lo = np.array([-xw - mw[0], ym - mw[1] / 2, zm - mw[2] / 2]) if side < 0 else \
            np.array([xw, ym - mw[1] / 2, zm - mw[2] / 2])
        return [(lo, lo + mw)], 99

    def d1b(ym, zm, crown=-1):     # along Y at x 0, crown pair at the shaft end (front −1 / rear +1)
        lo = np.array([-mw[1] / 2, ym - mw[0] / 2, zm - mw[2] / 2])
        m = (lo, lo + [mw[1], mw[0], mw[2]])
        if crown < 0:
            c = (np.array([-7.1, lo[1] - 10.5, zm - 7.1]), np.array([7.1, lo[1] - 0.5, zm + 2.0]))
        else:
            c = (np.array([-7.1, m[1][1] + 0.5, zm - 7.1]), np.array([7.1, m[1][1] + 10.5, zm + 2.0]))
        return [m, c], 1

    def d1c(ym, zm, rear=1):       # worm along Y over the crank wheels, motor in line behind (rear) / in front
        zm = z0 + 3.0 + 3.0 + F.GEAR_TIP.side
        if rear > 0:
            lo = np.array([-mw[1] / 2, max(gy) + 4.5, zm - mw[2] / 2])
            w = (np.array([-4.0, min(gy) - 4.5, zm - 4.0]), np.array([4.0, lo[1], zm + 4.0]))
        else:
            lo = np.array([-mw[1] / 2, min(gy) - 4.5 - mw[0], zm - mw[2] / 2])
            w = (np.array([-4.0, lo[1] + mw[0], zm - 4.0]), np.array([4.0, max(gy) + 4.5, zm + 4.0]))
        return [(lo, lo + [mw[1], mw[0], mw[2]]), w], 1

    out = [("D1a along X, pinion → idler → crank, ratio 1.20", d1a),
           ("D1b along Y, crown at the front, ratio 0.50", lambda y, z: d1b(y, z, -1)),
           ("D1b' along Y, crown at the rear, ratio 0.50", lambda y, z: d1b(y, z, 1)),
           ("D1c worm, motor behind, ratio 0.10", lambda y, z: d1c(y, z, 1)),
           ("D1c' worm, motor in front, ratio 0.10", lambda y, z: d1c(y, z, -1))]
    return out


def _ctx(S, ball, dy):
    p = p_at(S)
    dyk = tuple(dy)                       # mm at S (rev 4)
    L = legs_ax(p, poses=24, dy=dyk)
    g, z0 = train(p, dy=dyk)
    X, R = arm_cloud(L, ball)
    gtop = max(z + t + F.GEAR_TIP.side for _, y, z, t in g)
    xw = GEAR_W / 2 + F.GEAR_THRUST_CRANK.side + W_LOAD
    ys = [y for _, y, _, _ in g]
    tip = max(t for *_, t in g) + F.GEAR_TIP.side
    strip = (np.array([-xw, min(ys) - tip, 0.0]), np.array([xw, max(ys) + tip, gtop]))
    return dict(S=S, ball=ball, dy=dy, p=p, L=L, g=g, z0=z0, X=X, R=R, gtop=gtop, strip=strip,
                sweeps=crank_sweeps(L))


def _mech_field(c, G, exempt_strip):
    ax = [G["lo"][i] + ROOM_PITCH * np.arange(G["g"].shape[i]) for i in range(3)]
    Q = np.array(np.meshgrid(*ax, indexing="ij")).reshape(3, -1).T
    f = np.full(len(Q), ROOM_UB)
    for lo, hi in c["sweeps"] + ([] if exempt_strip else [c["strip"]]):
        f = np.minimum(f, n0.pt_box(Q, lo, hi) - (np.all((Q >= lo) & (Q <= hi), 1) * 0.5))
    return f.reshape(G["g"].shape)


def _boxmin(field, size):
    """Min of field over a box of `size` centred at every grid point (box rounded up to the grid: conservative)."""
    from scipy.ndimage import minimum_filter
    n = [int(math.ceil(s / ROOM_PITCH)) + 1 for s in size]
    n = [m + (m % 2 == 0) for m in n]
    return minimum_filter(field, size=n, mode="constant", cval=-9.0)


def eval_layout(c, boxes, wall, exact=True):
    """Least room of a layout: boxes = [(name, lo, hi, exempt_strip)]. Every box against the shell (body wall
    `wall`), the swept arms (LEG_PATH taken off), the crank sweeps, the strip (unless it meshes it), every other box.
    Returns (least, binding pair, all pairs)."""
    S = c["S"]
    res = {}
    memo = c.setdefault("_memo", {})
    for b in boxes:                      # (name, lo, hi, exempt from strip[, shell check])
        nm, lo, hi, ex = b[:4]
        shl = b[4] if len(b) > 4 else True   # False: passes through the shell by design (LED in its eye bore)
        mk = (tuple(np.round(lo, 3)), tuple(np.round(hi, 3)), wall, exact, shl)
        if mk not in memo:
            memo[mk] = (inside_gap(box_pts(lo, hi), S, wall, exact) if shl else 9.0,
                        (n0.pt_box(c["X"], lo, hi) - c["R"]).min() - F.LEG_PATH.side)
        res[f"{nm}↔shell"], res[f"{nm}↔arms"] = memo[mk]
        res[f"{nm}↔cranks"] = min(box_sep((lo, hi), s) for s in c["sweeps"])
        if not ex:
            res[f"{nm}↔strip"] = box_sep((lo, hi), c["strip"])
    for i, (n1_, l1, h1, *_) in enumerate(boxes):
        for n2_, l2, h2, *_ in boxes[i + 1:]:
            if n1_.split()[0] != n2_.split()[0]:          # motor + its own crown / worm are one sub-assembly
                res[f"{n1_}↔{n2_}"] = box_sep((l1, h1), (l2, h2))
    k = min(res, key=res.get)
    return res[k], k, res


def search_layouts(S=0.65, ball=BALL_D2, dy=CRANK_DY_65, walls=(3.0, 1.6), refine=6, only=None):
    """(only = [(wall, drive[:6], holder[:3])] limits the rows.) Every drive × holder × body wall: coarse search on the room grids (box min filters, 0.5 mm steps), the best
    `refine` combinations re-checked exactly and hill-climbed (0.5 mm moves). Returns rows for the table."""
    c = _ctx(S, ball, dy)
    rows = []
    for wall in walls:
        G = room_grid(S, wall)
        A = arm_field(S, ball, dy)
        base = np.minimum(G["g"], A["g"])
        F_all = np.minimum(base, _mech_field(c, G, False))
        F_ex = np.minimum(base, _mech_field(c, G, True))
        ax = [G["lo"][i] + ROOM_PITCH * np.arange(G["g"].shape[i]) for i in range(3)]
        idx = lambda v: [int(round((v[i] - G["lo"][i]) / ROOM_PITCH)) for i in range(3)]
        hmin = {}
        for hn, shapes in holders().items():
            for sz in set(shapes):
                if sz not in hmin:
                    hmin[sz] = _boxmin(F_all, sz)
        for dn, fn in drives(c["p"], c["g"], c["z0"]):
            if only and not any(o[0] == wall and o[1] == dn[:6] and o[2] in [h[:3] for h in holders()] for o in only):
                continue
            # motor candidates: (ym, zm) on a 1 mm grid, coarse score from the min filters
            cand = []
            cache = {}
            for ym in np.arange(-24, 24.1, 1.0):
                for zm in np.arange(8, 40.1, 1.0):
                    r = fn(ym, zm)
                    if r is None:
                        continue
                    bx, mesh = r
                    s = 9.0
                    for j, (lo, hi) in enumerate(bx):
                        sz = tuple(np.round(hi - lo, 2))
                        key = (sz, j == mesh)
                        if key not in cache:
                            cache[key] = _boxmin(F_ex if j == mesh else F_all, sz)
                        ii = idx((lo + hi) / 2)
                        if not all(0 <= ii[q] < cache[key].shape[q] for q in range(3)):
                            s = -9
                            break
                        s = min(s, cache[key][tuple(ii)])
                    cand.append((s, ym, zm, bx))
                    if dn.startswith("D1c"):
                        break
            cand.sort(key=lambda t: -t[0])
            for hn, shapes in holders().items():
                if only and (wall, dn[:6], hn[:3]) not in only:
                    continue
                best = []
                for s_m, ym, zm, bx in cand[:12]:
                    H = hmin[shapes[0]]
                    hs = np.array(shapes[0])
                    C = np.stack(np.meshgrid(*ax, indexing="ij"), -1)
                    sc = np.minimum(H, s_m)
                    for lo, hi in bx:
                        sep = np.max(np.maximum(C - hs / 2 - hi, lo - C - hs / 2), -1)
                        sc = np.minimum(sc, sep)
                    if len(shapes) == 1:
                        j = np.unravel_index(np.argmax(sc), sc.shape)
                        best.append((sc[j], ym, zm, bx, [C[j]]))
                    else:
                        flat = sc.ravel()
                        top = np.argpartition(-flat, 400)[:400]
                        P = C.reshape(-1, 3)[top]
                        sp = np.max(np.abs(P[:, None] - P[None]) - hs, -1)
                        tot = np.minimum(np.minimum(flat[top][:, None], flat[top][None]), sp)
                        np.fill_diagonal(tot, -99)
                        a, b = np.unravel_index(np.argmax(tot), tot.shape)
                        best.append((tot[a, b], ym, zm, bx, [P[a], P[b]]))
                best.sort(key=lambda t: -t[0])
                top = None
                for s0, ym, zm, bx, hc in best[:refine]:
                    boxes = [(f"motor{'' if j == 0 else ' crown/worm'}", lo, hi, j == 1 and dn[:3] != "D1a")
                             for j, (lo, hi) in enumerate(bx)]
                    boxes += [(f"holder{'' if len(hc) == 1 else ' ' + 'AB'[q]}", h - np.array(shapes[q]) / 2,
                               h + np.array(shapes[q]) / 2, False) for q, h in enumerate(hc)]
                    sc, kk, res, boxes = _climb(c, boxes, wall, dn)
                    if top is None or sc > top[0]:
                        top = (sc, kk, res, boxes, s0)
                rows.append(dict(wall=wall, drive=dn, holder=hn, least=top[0], bind=top[1], res=top[2],
                                 boxes=top[3], coarse=top[4]))
                print(f"  {'D4a' if wall >= 3 else 'D4b'} | {dn[:6]:6s} | {hn[:44]:44s} | least {top[0]:+.2f} "
                      f"({top[1]}) coarse {top[4]:+.2f}", flush=True)
    return rows, c


def _climb(c, boxes, wall, dn, steps=4):
    """Hill-climb a layout with exact checks: move one box (motor moves with its crown / worm) 0.5 mm along an axis
    (motor along Y/Z only: its X is set by the strip), keep the move if the least room grows."""
    sc, kk, res = eval_layout(c, boxes, wall)
    for _ in range(steps):
        better = False
        groups = [[0, 1] if len(boxes) > 1 and boxes[1][0].startswith("motor") else [0]]
        groups += [[i] for i, b in enumerate(boxes) if b[0].startswith("holder")]
        for gi in groups:
            if 0 in gi and dn[:3] != "D1b":
                continue      # D1a / D1c: the gears set the motor's place; only D1b's motor slides along Y / Z
            for a in ((1, 2) if 0 in gi else (0, 1, 2)):
                for d in (-0.5, 0.5):
                    nb = [(n, lo + (np.eye(3)[a] * d if i in gi else 0), hi + (np.eye(3)[a] * d if i in gi else 0), e)
                          for i, (n, lo, hi, e) in enumerate(boxes)]
                    s2, k2, r2 = eval_layout(c, nb, wall)
                    if s2 > sc + 1e-3:
                        boxes, sc, kk, res, better = nb, s2, k2, r2, True
        if not better:
            break
    return sc, kk, res, boxes


def pr_arms(S=S_FIX, ball=BALL_D2, margin=0.2):
    """Item 2 / B4 (rev 4): arm end ↔ arm at scale S (real ends, 24 poses) per side; per-crank Y offsets (mm at S)
    searched pair by pair, least total shift with every pair ≥ LEG_PATH 0.8 + margin (ties: largest least pair);
    crank gears ≥ 8.45 apart (tips 7.45 + 2 × GEAR_TIP: the module does not scale). Also the ball's swivel."""
    import itertools
    print(f"== arm ↔ arm (pr6, S {S}, Ø{ball:g} ball, end Ø{2 * end_r(ball):.1f}): least gap − LEG_PATH 0.8, mm ==")
    p = p_at(S)
    L0 = legs_ax(p, poses=24)
    ys = [L0[i]["O"][1] for i in range(4)]
    D = np.arange(-3, 3.01, 0.5)

    def pair(i, a, b):
        dy = [0.0] * 4
        dy[i], dy[i + 1] = a, b
        if ys[i + 1] + b - ys[i] - a < 8.45:
            return -9
        L = legs_ax(p, poses=24, dy=dy)
        return min(capsule_gap(c1, c2) - F.LEG_PATH.side for k in range(24)
                   for c1 in arm_parts(L[i], k, ball) for c2 in arm_parts(L[i + 1], k, ball))
    for nm, cb in (("as N1", (0, 0, 0, 0)), ("rev 3 (0, 0, 2, 0) at S 0.60, rescaled",
                                             tuple(d * S / 0.6 for d in CRANK_DY_D2))):
        gp = [pair(i, cb[i], cb[i + 1]) for i in range(3)]
        print(f"  {nm} {tuple(round(c, 2) for c in cb)}: pairs 1-2/2-3/3-4 {gp[0]:+.2f} / {gp[1]:+.2f} / {gp[2]:+.2f}")
    T = [{(a, b): pair(i, a, b) for a in D for b in D} for i in range(3)]
    ok = [(sum(abs(c) for c in cb), -min(T[i][(cb[i], cb[i + 1])] for i in range(3)), cb)
          for cb in itertools.product(D, repeat=4) if min(T[i][(cb[i], cb[i + 1])] for i in range(3)) >= margin]
    if not ok:
        print(f"  no offsets within ±3 give ≥ {margin}")
        return None
    # rev 4 rule: total shift ≤ 2 mm, then the largest least pair (rev 3's «least shift» left 2-3 at +0.38)
    cost, _, cb = min(ok, key=lambda t: (t[0] > 2.0 + 1e-9, t[1], t[0]))
    cb = tuple(float(c) for c in cb)
    gp = [T[i][(cb[i], cb[i + 1])] for i in range(3)]
    Lc = legs_ax(p, poses=24, dy=cb)
    yaw = [math.degrees(math.atan2(Lc[i]["u"][6][1], Lc[i]["u"][6][0]) -
                        math.atan2(L0[i]["u"][6][1], L0[i]["u"][6][0])) for i in range(4)]
    sw = [np.ptp(np.degrees(np.arctan2(Lc[i]["u"][:, 1], Lc[i]["u"][:, 0]))) for i in range(4)]
    tilt = [np.degrees(np.arccos(np.clip(np.abs(Lc[i]["u"][:, 0]), 0, 1))).max() for i in range(4)]
    print(f"  FROZEN offsets (mm at S {S}) {tuple(float(c) for c in cb)}: pairs {gp[0]:+.2f} / {gp[1]:+.2f} / "
          f"{gp[2]:+.2f} (margin ≥ {margin}); crank spacing "
          f"{[round(float(ys[i + 1] + cb[i + 1] - ys[i] - cb[i]), 2) for i in range(3)]}; arm yaw change "
          f"{[round(float(y), 1) for y in yaw]}° (D3a key); swing p-p {[round(float(s), 1) for s in sw]}°; ball "
          f"swivel off the crank axis ≤ {[round(float(t), 1) for t in tilt]}°")
    return cb, max(tilt)


def pr_neck(S=S_FIX, ball=BALL_D2, neck=1.6, sigma=40.0):
    """B4: printed Ø2 ball on its neck. The neck runs along the crank axis X (crank printed lying down, so the neck
    lies in the bed plane: perimeters run along it and a bending load pulls along the lines, not across layers).
    Lever = ball centre to the web face (the arm end tube needs ball/2 + slide/2 + 0.8 wall + LEG_PATH)."""
    print(f"== crank ball neck (B4, S {S}) ==")
    p = p_at(S)
    lever = ball / 2 + SLIDE / 2 + W_MIN + F.LEG_PATH.side
    Z = math.pi * neck ** 3 / 32                      # section modulus, round neck
    flat = 0.3                                        # the bed-side flat (item 5) takes 0.3 off one side
    Zf = Z * (1 - 1.7 * flat / neck)                  # ≈ loss of a 0.3 chord on a Ø1.6 section (conservative)
    Fmax = sigma * Zf / lever
    Fstall = STALL / (CROWN["z_spur"] / CROWN["z_crown"] * CROWN["z_pinion"] / CROWN["z_spur"]) / p["r"]
    walk = 1.2 * 9.81 * 0.100 / 4 * (30 / 18)         # 100 g robot, 4 legs in stance, foot/ball lever 30/18, ×1.2
    tilt_ok = (F.bore(ball, F.TURN) / 2 + 0.5 - neck / 2) / (ball / 2)   # tan of the swivel the 0.5 × 45° mouth allows
    print(f"neck Ø{neck} (4 lines of 0.4), lever {lever:.1f} mm, Z {Zf:.3f} mm³ after the 0.3 flat; PLA along the "
          f"lines {sigma:.0f} MPa → breaks at ≈ {Fmax:.1f} N at the ball. Walking ≈ {walk:.2f} N (×{Fmax / walk:.0f}); "
          f"motor stall {STALL:.0f} N·mm (assumed) × 2 (crank:motor 1:2) / r {p['r']:.2f} = {Fstall:.0f} N: a jammed "
          f"leg can break a neck before the motor stalls → the neck is the weak link on purpose (a crankshaft "
          f"reprints in 0.4 g). Swivel the bore mouth (0.5 × 45°) passes: {math.degrees(math.atan(tilt_ok)):.0f}°")


def pr_pivot(S=S_FIX, dy=CRANK_DY_65, pin=2.0):
    """Items 3-4 / B2 (rev 4): root block swept in plan at the rim; rim left between notches (Ø2 steel pin, D2e),
    the lands an M3 needs, the rim past legs 1 and 4 (keeper end screws), the pin's retention and length."""
    print(f"== pivot (pr2/pr4 rev 4, S {S}, offsets {dy}): swept root block at the rim ==")
    p = p_at(S)
    L = legs_ax(p, poses=72, dy=dy)
    w = F.bore(pin, F.STEEL) + 2 * W_LOAD
    lb = w + 1.0
    hulls = []
    for i in range(4):
        P = L[i]["P"][:2]
        pts = []
        for k in range(72):
            u = L[i]["u"][k]
            e = n0.unit(np.array([u[0], u[1]]))
            n = np.array([-e[1], e[0]])
            for sa in (-1, 1):
                for sb in (-1, 1):
                    pts.append(P + e * sa * lb / 2 + n * sb * w / 2)
        pts = np.array(pts)
        h = pts[ConvexHull(pts).vertices]
        hulls.append(np.vstack([seg_pts(h[j], h[(j + 1) % len(h)], 0.05) for j in range(len(h))]))
    land_s = F.bore(3.0, F.STEEL) + 2 * W_LOAD                    # M3 shank hole + walls (screw into a nut below)
    land_n = F.bore(5.5, F.STEEL) + 2 * W_LOAD                    # M3 nut pocket (5.5 AF) + walls
    out = {}
    for a in range(3):
        d = cKDTree(hulls[a]).query(hulls[a + 1])[0].min()
        rim = d - 2 * F.LEG_PATH.side
        out[f"{a + 1}-{a + 2}"] = rim
        print(f"  notches {a + 1}-{a + 2}: pivots {np.linalg.norm(L[a]['P'][:2] - L[a + 1]['P'][:2]):.1f} apart, rim "
              f"left {rim:+.2f} → M3 screw land {land_s:.1f} {'fits' if rim >= land_s else 'no'}, nut land "
              f"{land_n:.1f} {'fits' if rim >= land_n else 'no'}")
    R = n1.run(p)
    V = R["st"]["base_v"]
    z = L[0]["P"][2]
    rimv = V[(np.abs(V[:, 2] - z) < 1.5) & (V[:, 0] > 5)]
    front = hulls[0][:, 1].min() - F.LEG_PATH.side - rimv[:, 1].min()
    rear = rimv[:, 1].max() - hulls[3][:, 1].max() - F.LEG_PATH.side
    print(f"  rim past the swept blocks (base mesh at z {z:.1f} ± 1.5, along Y): front of leg 1 {front:.1f}, rear of "
          f"leg 4 {rear:.1f} (the rim curves in there: the keeper end lands sit on the curve)")
    floor, seat, eyes, play, kt, pocket = 2.0, 1.2, 2 * 2.4, F.WINDOW.side, 2.4, 1.5
    ln = seat + eyes + play + pocket
    print(f"  Ø{pin:g} pin: blind seat {seat} in the {floor} notch floor (Ø{F.bore(pin, F.STEEL):.2f}, STEEL) on a "
          f"step with a Ø1.5 push-out hole; stack {eyes}; play {play}; keeper {kt} with a {pocket} pocket → "
          f"{ln:.1f} → stock Ø2 × 8; {8 - seat - eyes:.1f} proud above the stack with the keeper off (pull with "
          f"pliers, or push from below through the Ø1.5 hole with the 1.5 hex key)")
    pitch = [np.ptp(np.degrees(np.arcsin(L[i]["u"][:, 2]))) / 2 for i in range(4)]
    pm = max(pitch)
    edge = (w / 2) * math.tan(math.radians(pm))
    print(f"  pitch ±{', ±'.join(f'{x:.1f}' for x in pitch)}°: flare ±{pm + 2:.0f}°; block {w:.1f} × {lb:.1f}; flat-face "
          f"edge travel {edge:.2f} ≤ WINDOW {F.WINDOW.side}; crown R ≈ {(w / 2) ** 2 / (2 * edge):.0f} mm")
    return out, front, rear


def pair_raw(p, i, ball, xc=None, dy=(0, 0, 0, 0)):
    L = legs_ax(p, poses=24, dy=dy, xc=xc)
    return min(capsule_gap(c1, c2) - F.LEG_PATH.side for k in range(24)
               for c1 in arm_parts(L[i], k, ball) for c2 in arm_parts(L[i + 1], k, ball))


def pr_gear():
    """Item 5: 10T tooth plan (undercut, profile shift, tip land) per module and nozzle."""
    print("== gear teeth (pr7): tip land, mm; one line = nozzle width ==")
    for m, noz in ((0.6, 0.4), (0.6, 0.2), (0.8, 0.4)):
        for z in (10, 12):
            for x in (0.0, 0.25, 0.41):
                for ha in (1.0, 0.8):
                    s, da = tip_thickness(z, m, x, ha)
                    zmin = 2 / math.sin(ALPHA) ** 2 * (1 - x)
                    print(f"m{m} {z}T x {x:+.2f} tip h {ha:.1f}: tip Ø{da:.2f}, land {s:.2f} "
                          f"({s / noz:.1f} lines of {noz}), undercut {'no' if z >= zmin - 1e-6 else 'yes'}")


def cell_holder():
    """Item 8: 2S3P holder envelopes (x, y, z) for each D9 candidate."""
    out = {}
    stack = 2 * CELL_T + SPRING[0] + PLATE + 2 * W_LOAD + F.WINDOW.side      # along the stack axis
    across = 3 * (CELL_D + 2 * F.WINDOW.side) + 2 * W_MIN + 2 * W_LOAD     # three bays side by side
    high = CELL_D + 2 * F.WINDOW.side + 2 * W_LOAD                         # floor + lid
    out["D9a printed, axis Y"] = (across, stack, high)
    out["D9a printed, axis Z"] = (across, CELL_D + 2 * F.WINDOW.side + 2 * W_LOAD, stack)
    out["D9c brass strip, axis Y"] = (across, 2 * CELL_T + 2 * 0.3 + 2 * 1.0 + 2 * W_LOAD + F.WINDOW.side, high)
    return out


def pr_cell():
    print("== cell holder (pr8): envelope x × y × z, mm (rev 1 box 36 × 12.6 × 13) ==")
    for k, v in cell_holder().items():
        print(f"{k}: {v[0]:.1f} × {v[1]:.1f} × {v[2]:.1f}")
    print(f"negative contact: spring coil Ø{SPRING[1]:.1f} < cap Ø{CELL_NEG_CAP:.1f} (datasheet), centred by a "
          f"Ø{SPRING[1] + 2 * F.WINDOW.side:.1f} pocket with a {(CELL_D - CELL_NEG_CAP) / 2:.1f} mm wide ring "
          f"standing 0.6 proud: the can rim cannot reach the spring")
    print("D9b bought 2 × LR44 holders: 3 (one per parallel branch); size from the listing, to measure on arrival")


def pr_pins():
    print("== pin lengths (pr9) ==")
    for pin in (3.0, 2.0):
        stack = W_LOAD + 2 * 2.4 + F.WINDOW.side + W_LOAD           # notch floor + 2 eyes + play + keeper
        print(f"Ø{pin:.0f} pivot pin: floor {W_LOAD} + eyes 2 × 2.4 + play {F.WINDOW.side} + keeper {W_LOAD} = "
              f"{stack:.1f} → pin {math.ceil(stack + 1.0):.0f} (1 mm proud below to push out)")
    idl = GEAR_W + 2 * F.GEAR_THRUST_IDLER.side + 2 * W_LOAD
    print(f"idler pin: wall + idler {GEAR_W} + 2 × {F.GEAR_THRUST_IDLER.side} + wall = {idl:.1f} → Ø3 × 6 "
          f"(through both walls, head under the cap; v2 used × 10 over a wider frame)")


def pr_asm():
    """Item 6: leg in along its arm onto the ball: drop at +e outboard, then in along −u; gap to the neighbours."""
    print("== leg path (pr10): drop into the open notch 3 mm outboard, slide in along the arm onto the ball ==")
    p = p_at(0.60)
    for name, kw in (("c0", {}), ("c3", dict(dy=(0, -2.5, 2.5, 0)))):
        L = legs_ax(p, poses=36, **kw)
        k = 9                                                    # crank level, ball at its outermost: the mark
        worst = 9.0
        for i in range(8):
            for t in np.linspace(0, 3.0, 7):
                me = [(pts + L[i]["u"][k] * t, r) for pts, r in arm_parts(L[i], k, 3.0)]
                for j in range(8):
                    if j == i or L[j]["side"] != L[i]["side"]:
                        continue
                    for c2 in arm_parts(L[j], k, 3.0):
                        for c1 in me:
                            worst = min(worst, capsule_gap(c1, c2))
        print(f"{name}: least gap moving leg ↔ placed arms over the 3 mm slide {worst:+.2f} (≥ 0: path clear)")


# ---------------------------------------------------------------- slicer (item 7)
def _vox_mesh(G, pitch, origin):
    import trimesh
    V, Fc = [], []
    G = np.pad(G, 1)
    for ax in range(3):
        for sgn in (1, -1):
            sh = np.roll(G, -sgn, axis=ax)
            face = G & ~sh
            idx = np.argwhere(face)
            if not len(idx):
                continue
            base = idx.astype(float)
            if sgn > 0:
                base[:, ax] += 1
            o = [a for a in range(3) if a != ax]
            c = np.zeros((len(idx), 4, 3))
            for j, (da, db) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
                c[:, j] = base
                c[:, j, o[0]] += da
                c[:, j, o[1]] += db
            if (sgn > 0) == (ax == 1):
                c = c[:, ::-1]
            n0_ = len(V) and sum(len(v) for v in V)
            V.append(c.reshape(-1, 3))
            k = np.arange(len(idx))[:, None] * 4 + n0_
            Fc.append(np.vstack([np.hstack([k, k + 1, k + 2]), np.hstack([k, k + 2, k + 3])]))
    V = (np.vstack(V) - 1) * pitch + origin
    m = trimesh.Trimesh(V, np.vstack(Fc), process=True)
    trimesh.repair.fix_normals(m)
    return m


def slice_parts(out):
    """Body D4a (jenscolt's 3 mm, as is), body D4b (1.6 mm, voxel-thinned), base bowl 1.2 (voxel-hollowed)."""
    import trimesh
    from scipy import ndimage
    pitch = 0.35
    paths = {}
    for nm in ("body", "base"):
        m = trimesh.load(n0.J + nm + ".stl")
        m.vertices = n1.to_robot(np.asarray(m.vertices), 0.60)
        if nm == "body":
            m.export(os.path.join(out, "body_D4a.stl"))
            paths["body_D4a"] = os.path.join(out, "body_D4a.stl")
        vg = m.voxelized(pitch).fill()
        G = vg.matrix.copy()
        org = vg.translation
        if nm == "body":
            z0 = np.argwhere(G.any((0, 1)))[0][0]
            foot = ndimage.binary_fill_holes(G[:, :, z0:z0 + 3].any(2))
            top = np.where(G.any(2), G.shape[2] - 1 - np.argmax(G[:, :, ::-1], 2), 0)
            zz = np.arange(G.shape[2])[None, None]
            full = G | (foot[:, :, None] & (zz <= top[:, :, None]) & (zz >= z0))
            d = ndimage.distance_transform_edt(full) * pitch
            sh = full & (d <= 1.6 + 1e-6)
            sh &= ~((zz < z0 + int(1.6 / pitch) + 1) & ~G)
            sh |= G & ~foot[:, :, None]
            paths["body_D4b"] = os.path.join(out, "body_D4b.stl")
            _vox_mesh(sh, pitch, org).export(paths["body_D4b"])
        else:
            d = ndimage.distance_transform_edt(G) * pitch
            zz = np.arange(G.shape[2])[None, None]
            ztop = np.argwhere(G.any((0, 1)))[-1][0]
            inner = ndimage.binary_erosion(G.any(2), iterations=int(BASE_WALL / pitch) + 1)
            sh = G & (d <= BASE_WALL + 1e-6)
            sh &= ~((zz > ztop - int(BASE_WALL / pitch) - 1) & inner[:, :, None])
            paths["base"] = os.path.join(out, "base_bowl.stl")
            _vox_mesh(sh, pitch, org).export(paths["base"])
    return paths


def pr_slice():
    out = os.path.join(HERE, "out", ".cache", "probe-slice")
    os.makedirs(out, exist_ok=True)
    P = slice_parts(out)
    jobs = {"body D4a open side down": (P["body_D4a"], ""), "body D4b open side down": (P["body_D4b"], ""),
            "body D4b open side up": (P["body_D4b"], "@180,0,0"), "base rim up (bottom on bed)": (P["base"], ""),
            "base rim down": (P["base"], "@180,0,0")}
    procs = {}
    for k, (stl, rot) in jobs.items():
        f = os.path.join(out, k.replace(" ", "_").replace("(", "").replace(")", "") + ".3mf")
        procs[k] = (f, subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "bambu_plate.py"), f, stl + rot,
                                         "--standard"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True))
    print("== support from the slicer (pr4 rev 2), 0.20 Standard, tree(auto), build plate only ==")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import print_report as PR
    for k, (f, pr) in procs.items():
        txt = pr.communicate()[0]
        try:
            r = PR.report(f)
            print(f"{k}: {json.dumps(r) if not isinstance(r, str) else r}")
        except Exception as e:  # noqa: BLE001
            print(f"{k}: slice failed ({e}); {txt[-300:]}")


# ---------------------------------------------------------------- figure (item 9)
def pr_figure(path):
    import trimesh, matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import figures as Fg
    R = n1.run(p_at(S_FIX))
    st = R["st"]
    p = R["p"]
    L = legs_ax(p, poses=24, dy=CRANK_DY_65)
    w, lb = F.bore(2.0, F.STEEL) + 2 * W_LOAD, F.bore(2.0, F.STEEL) + 2 * W_LOAD + 1.0      # D2e Ø2 pin
    keep = {k: np.ones(len(st[k + "_f"]), bool) for k in ("body", "base")}
    for Lg in L:
        pts = []
        for k in range(24):
            u = Lg["u"][k]
            n = n0.unit(np.cross([0, 0, 1], u))
            up = np.cross(u, n)
            for a in (-1, 1):
                for b in (-1, 1):
                    for c in (-1, 1):
                        e = (lb / 2 + 5.0 * (a > 0)) * a          # block + 5 mm of leg past it, outward
                        pts.append(Lg["P"] + u * e + n * b * (w / 2 + F.LEG_PATH.side) + up * c * (2.4 + F.LEG_PATH.side))
        pts = np.array(pts)
        lo = pts.min(0)
        pts = np.vstack([pts, pts * [1, 1, 0] + [0, 0, lo[2] - 30]])   # open downward: notch / slot to the bottom...
        H = ConvexHull(pts)
        for kk in keep:
            V, Fc = st[kk + "_v"], st[kk + "_f"]
            ins = ((V @ H.equations[:, :3].T + H.equations[:, 3]) <= 0).all(1)
            if kk == "base":                                       # ...in the body skirt; the base notch opens up
                ins &= V[:, 2] >= Lg["P"][2] - 2.4 - F.LEG_PATH.side - W_LOAD
            keep[kk] &= ~ins[Fc].any(1)
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    for ax, (title, kp) in zip(axs, (("N1 (aspecto aprobado): ventanas del collar de 9 mm", R["keep"]),
                                     ("N2 rev 4: una muesca por pata (holgura 0,8), ranuras del faldón\n"
                                      "abiertas por abajo; borde libre entre muescas 1-2 3,2 / 2-3 1,4 / 3-4 9,0 mm",
                                      keep))):
        items = []
        for kk, col in (("base", "#7f8c8d"), ("body", "#c0392b")):
            items.append(dict(mesh=trimesh.Trimesh(st[kk + "_v"], st[kk + "_f"][kp[kk]]), color=col))
        items.append(dict(mesh=trimesh.Trimesh(st["eyes_v"], st["eyes_f"]), color="#2e86c1"))
        Fg.draw(ax, items, view=(8, 0), edge_angle=75.0)
        ax.set_title(title, fontsize=Fg.FONT + 1)
    fig.suptitle("Lado derecho, sin patas: ventanas y borde entre muescas (escala 0,65, pasador de acero Ø2)",
                 fontsize=Fg.FONT + 2)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    print("wrote", path)



def pr_layouts(S=0.65, only=None):
    """Rev 3 (S fixed at 0.65, Ø2 balls): every drive × cell-holder layout × body wall; least room and binding pair.
    Writes out/.cache/layouts_<S>.json for the plan figure."""
    import time
    t = time.time()
    print(f"== inside layouts (S {S}, Ø{BALL_D2:g} balls, offsets {CRANK_DY_65} mm at S): least room, mm (≥ 0 fits) ==")
    rows, c = search_layouts(S, only=only)
    keep = [dict(wall=r["wall"], drive=r["drive"], holder=r["holder"], least=float(r["least"]), bind=r["bind"],
                 boxes=[(n, list(map(float, lo)), list(map(float, hi))) for n, lo, hi, _ in r["boxes"]]) for r in rows]
    with open(os.path.join(CACHE, f"layouts_{S:.3f}.json"), "w") as f:
        json.dump(keep, f, indent=1)
    fit = [r for r in keep if r["least"] >= 0]
    print(f"fits (≥ 0 everywhere): {len(fit)}; best per wall:")
    for w in sorted({r["wall"] for r in keep}):
        b = max((r for r in keep if r["wall"] == w), key=lambda r: r["least"])
        print(f"  D4 {w:.1f}: {b['drive'][:6]} + {b['holder']}: {b['least']:+.2f} ({b['bind']}); boxes "
              + "; ".join(f"{n} {np.round(lo, 1).tolist()}..{np.round(hi, 1).tolist()}" for n, lo, hi in b["boxes"]))
    print(f"({time.time() - t:.0f} s)")

# ---------------------------------------------------------------- rev 4: crown pair (B1) and the full inside (B3)
def _teeth(name):
    return int([t for t in name.split() if t.endswith("T")][0][:-1])


def crown_drive(c, ym, zm):
    """B1: D1b motor along Y (axis x 0, y ym, z zm), 10T pinion (x +0.42) on its D-shaft at the front, meshing a
    20T face (crown) gear whose axis is X at the motor's height; the crown part carries a 10T spur (x +0.42) in the
    strip plane x 0, nested inside the crown's tooth ring, which drives one strip gear through one transfer idler
    (−0.42, zero-sum). Returns (boxes, info) or None. Envelopes: real gears + GEAR_TIP, walls W_LOAD, fits."""
    m, Cw = CROWN["m"], CROWN
    mw = np.array(MOTOR) + 2 * (F.MOTOR_SEAT.side + CLAMP_W)
    lo = np.array([-mw[1] / 2, ym - mw[0] / 2, zm - mw[2] / 2])
    hi = lo + [mw[1], mw[0], mw[2]]
    tip_p = m * (Cw["z_pinion"] + 2 + 2 * Cw["x"]) / 2               # 3.85
    yp = lo[1] - 3.1                     # pinion centre: seat wall, 1.6 of free shaft, half the 3 mm face
    R0 = m * Cw["z_crown"] / 2           # 6.0: the pinion meshes the crown face at R0 from its axis
    yC = yp - R0
    xf = -(m * Cw["z_pinion"] / 2 + m * Cw["x"])                      # crown pitch plane (pinion pitch line)
    xback = xf - 1.25 * m - Cw["disc"]                                # tooth root, then the disc
    xl = xback - F.GEAR_THRUST_IDLER.side - W_LOAD                    # left spine wall outer face
    xr = GEAR_W / 2 + F.GEAR_THRUST_IDLER.side + W_LOAD               # right wall (spur 3 wide at x 0)
    rc = Cw["r_out"] + F.GEAR_TIP.side
    rs, tip_s = m * Cw["z_spur"] / 2, tip_p
    boxes = [("motor", lo, hi, False),
             ("motor pinion", np.array([-tip_p - .5, yp - 2.0, zm - tip_p - .5]),
              np.array([tip_p + .5, lo[1], zm + tip_p + .5]), False),
             ("motor crown", np.array([xl, yC - rc, zm - rc]), np.array([xr, yC + rc, zm + rc]), False),
             ("motor terminals", np.array([-4.0, hi[1], zm - 4.0]), np.array([4.0, hi[1] + 3.0, zm + 4.0]), False),
             ("motor wires", np.array([-lo[0] * -1, hi[1] + 3.0, zm - 6.0]) * [1, 1, 1] + [0, 0, 0],
              np.array([-lo[0], hi[1] + 6.0, zm + 6.0]), False)]
    boxes[-1] = ("motor wires", np.array([lo[0], hi[1] + 3.0, zm - 6.0]), np.array([hi[0], hi[1] + 6.0, zm + 6.0]),
                 False)                  # solder joints, series link A → B, leads down to the switch (4 × 4 bundle)
    ear = F.bore(M3_HEAD[0], F.STEEL)                                  # 5.8 head pocket = ear width
    for nm, sx, y0 in (("motor clamp ear L", -1, lo[1] + 1.0), ("motor clamp ear R", 1, hi[1] - 1.0 - ear)):
        x0 = hi[0] if sx > 0 else lo[0] - ear
        boxes.append((nm, np.array([x0, y0, zm - M3_NUT[1] - W_LOAD - 0.4]),
                      np.array([x0 + ear, y0 + ear, hi[2] + M3_HEAD[1]]), False))
    # transfer idler: crown spur (yC, zm) → idler → one strip gear
    strip = [(n, y, z, t, m * _teeth(n) / 2) for n, y, z, t in c["g"]]
    pin_rect = (yp - 1.5, yp + 1.5, zm - tip_p, zm + tip_p)
    mot_rect = (lo[1], hi[1], lo[2], hi[2])
    rect_d = lambda q, r: math.hypot(max(r[0] - q[0], 0, q[0] - r[1]), max(r[2] - q[1], 0, q[1] - r[3]))
    best = None
    for n_t, y_t, z_t, t_t, r_t in strip:
        for zi in range(10, 25):
            ri, tip_i = m * zi / 2, m * (zi + 2 - 2 * Cw["x"]) / 2
            for up in (False, True):
                q = idler_pos((yC, zm), (y_t, z_t), rs, r_t, ri, up)
                if q is None:
                    continue
                cl = [q[1] - tip_i - F.GEAR_TIP.side - BASE_WALL,
                      rect_d(q, pin_rect) - tip_i - F.GEAR_TIP.side, rect_d(q, mot_rect) - tip_i - F.GEAR_TIP.side]
                cl += [math.hypot(q[0] - y, q[1] - z) - tip_i - t - F.GEAR_TIP.side
                       for n, y, z, t, _ in strip if n != n_t]
                cl += [math.hypot(yC - y, zm - z) - tip_s - t - F.GEAR_TIP.side for n, y, z, t, _ in strip]
                sc = min(cl)
                # smallest idler with ≥ 0.3 in-plane clearance (rev 4 first run preferred clearance: 23T idlers)
                if sc >= 0.3 and (best is None or zi < best[2] or (zi == best[2] and sc > best[0])):
                    best = (sc, n_t, zi, q, tip_i)
    if best is None:
        return None
    sc, n_t, zi, q, tip_i = best
    e = tip_i + F.GEAR_TIP.side
    boxes.append(("motor idler", np.array([-xr, q[0] - e, q[1] - e]), np.array([xr, q[0] + e, q[1] + e]), True))
    return boxes, dict(target=n_t, idler=zi, idler_c=q, crown_c=(yC, zm), pinion_y=yp, clear=sc, xf=xf, xl=xl,
                       xr=xr, rc=rc)


def fixed_boxes(c, led=5.0, eyes_mode="vertical"):
    """B3 boxes that the shell places (not the motor or cells): eyes board + LEDs + ledge + its M3 head, the front
    and rear body bosses (body → base, M3 from below, nut in the body boss, column in the base), the switch +
    retainer at the rear. Positions: LEDs on the N1 eye axes; bosses and switch at the extreme with room ≥ 0.3 on
    the shell + arms + strip + crank-sweep field (placed one after the other)."""
    S = c["S"]
    R = n1.run(c["p"])
    import trimesh
    eyes = sorted(trimesh.Trimesh(R["st"]["eyes_v"], R["st"]["eyes_f"]).split(only_watertight=False),
                  key=lambda q: -q.area)[:2]
    ec = [q.bounds.mean(0) for q in eyes]
    ytip = min(q.bounds[0][1] for q in eyes)                       # pupil = LED dome at the eye's front
    xe, ze = abs(ec[0][0]), float(np.mean([q[2] for q in ec]))
    fl, ln = LEDS[led]
    yb = ytip + ln + 2.0                                            # 2 mm of leads before the board
    out = []
    for sx in (-1, 1):
        out.append((f"LED{'LR'[sx > 0]}", np.array([sx * xe - fl / 2, ytip, ze - fl / 2]),
                    np.array([sx * xe + fl / 2, yb, ze + fl / 2]), False, False))
    if eyes_mode == "flat":     # R1 (c): board lying flat above the LEDs (leads bend up 0.4), 11 deep, M3 head on top
        zb = ze + fl / 2 + 0.4
        y0 = ytip + ln
        out.append(("eyes board", np.array([-xe - 3.5, y0, zb]), np.array([xe + 3.5, y0 + 11.0, zb + 4.1]), False))
        out.append(("eyes screw", np.array([-3.1, y0 + 2.4, zb + 4.1]),
                    np.array([3.1, y0 + 8.6, zb + 4.1 + M3_HEAD[1] + .2]), False))
    else:
        out.append(("eyes board", np.array([-xe - 3.5, yb, ze - 5.5 - W_LOAD]), np.array([xe + 3.5, yb + 4.1, ze + 5.5]),
                    False))                                         # 1.6 board + 2.5 resistors / solder; ledge 1.2
        out.append(("eyes screw", np.array([-3.1, yb + 4.1, ze - 3.1]),
                    np.array([3.1, yb + 4.1 + M3_HEAD[1] + .2, ze + 3.1]), False))
    G = room_grid(S, c["wall"])
    A = arm_field(S, c["ball"], c["dy"])
    fld = np.minimum(np.minimum(G["g"], A["g"]), _mech_field(c, G, False))
    ax = [G["lo"][i] + ROOM_PITCH * np.arange(G["g"].shape[i]) for i in range(3)]
    Cg = np.stack(np.meshgrid(*ax, indexing="ij"), -1)

    def add_field(f, lo, hi):
        Q = Cg.reshape(-1, 3)
        return np.minimum(f, (n0.pt_box(Q, lo, hi) - np.all((Q >= lo) & (Q <= hi), 1) * 0.5).reshape(f.shape))
    for b in out:
        fld = add_field(fld, b[1], b[2])

    placed = []

    def place(nm, size, key, x0=None, zmin=None, zmax=None):
        nonlocal fld
        mf = _boxmin(fld, size)
        cons = np.ones(mf.shape, bool)
        for plo, phi in placed:          # a box placed earlier is not free room: never on top of it
            cons &= np.max(np.maximum(Cg - np.array(size) / 2 - phi, plo - Cg - np.array(size) / 2), -1) >= 0.3
        if x0 is not None:
            cons &= np.abs(Cg[..., 0] - x0) < 0.26
        if zmin is not None:
            cons &= Cg[..., 2] - size[2] / 2 >= zmin
        if zmax is not None:
            cons &= Cg[..., 2] - size[2] / 2 <= zmax
        ok = cons & (mf >= 0.3)
        if not ok.any():                 # no room: keep it where it must be, at its best (the eval reports it)
            top_ = np.where(cons, mf, -99)
            near = cons & (mf >= top_.max() - 0.3)       # best room, within 0.3: then the key (front / rear)
            j = np.unravel_index(np.argmax(np.where(near, key(Cg), -1e9)), mf.shape)
        else:
            sc = np.where(ok, key(Cg), -1e9)
            j = np.unravel_index(np.argmax(sc), sc.shape)
        ctr = Cg[j]
        lo, hi = ctr - np.array(size) / 2, ctr + np.array(size) / 2
        fld = add_field(fld, lo, hi)
        placed.append((lo, hi))
        return (nm, lo, hi, False)
    boss = (F.bore(M3_NUT[0], F.STEEL) + 2 * W_LOAD,) * 2 + (8.0,)  # body boss: nut pocket + walls, 8 tall
    # body bosses sit on the skirt band (bottom z 9-13), the M3 comes up through a lug of the base wall there
    out.append(place("bossR body", boss, lambda C: C[..., 1], x0=0.0, zmin=9.0, zmax=13.0))
    out.append(place("bossF body", boss, lambda C: -C[..., 1], zmin=9.0, zmax=13.0))   # front: off the axis (option e)
    sw = (SWITCH[0] + 2 * W_LOAD + 6.5, SWITCH[1] + W_LOAD + 5.0, SWITCH[2] + 2 * W_LOAD)   # + retainer M3 boss, tabs
    out.append(place("switch", sw, lambda C: C[..., 1] - 0.2 * np.abs(C[..., 2] - 12)))
    return out, fld, Cg


def h3e_boxes(cA, cB, hook=False):
    """H3e pack (two 3P packs on edge) + the inner tongue on the motor seat (2 + 2 × TONGUE) + the rear end boss of
    the lid screw (1 × M3 through lid and pack into a nut in the seat's lug): head on the lid, nut lug under."""
    boss_y = 0.0 if hook else 6.2        # R2 (d): lid screw in the hook, inside the 41.8 pack length: no end boss
    hs = np.array(holders()["H3e two 3P packs on edge, rows along Y"][0]) + [2 + 2 * F.TONGUE.side, boss_y, 0]
    out = []
    for q, cc in (("A", cA), ("B", cB)):
        lo, hi = cc - hs / 2, cc + hs / 2
        hx = (cc[0] - 3.1, cc[0] + 3.1)
        out += [(f"holder{q}", lo, hi, False),
                (f"holder{q} lid screw", np.array([hx[0], hi[1] - 6.2, hi[2]]), np.array([hx[1], hi[1], hi[2] + 3.2]),
                 False),
                (f"holder{q} nut lug", np.array([lo[0], hi[1] - 6.2, lo[2] - M3_NUT[1] - W_LOAD]),
                 np.array([hi[0], hi[1], lo[2]]), False)]
    return out, hs


def search_b3(S=S_FIX, wall=3.0, led=5.0, ball=BALL_D2, dy=CRANK_DY_65, steps=10, eyes="vertical", hook=False):
    """B3: D1b + crown (crown_drive) + H3e with every B3 box; coarse search on min-filtered room grids, then an exact
    hill-climb of (motor y, z) and both pack centres (0.5 mm). JSTs placed last in the room left."""
    c = _ctx(S, ball, dy)
    c["wall"] = wall
    fixed, fld, Cg = fixed_boxes(c, led, eyes)
    G = room_grid(S, wall)
    fex = np.minimum(np.minimum(G["g"], arm_field(S, ball, dy)["g"]), _mech_field(c, G, True))
    Qg = Cg.reshape(-1, 3)
    for b in fixed:
        fex = np.minimum(fex, (n0.pt_box(Qg, b[1], b[2]) - np.all((Qg >= b[1]) & (Qg <= b[2]), 1) * .5).reshape(fex.shape))
    cand = []
    for ym in np.arange(-24, 24.1, 1.0):
        for zm in np.arange(18, 40.1, 1.0):
            r = crown_drive(c, ym, zm)
            if r is None:
                continue
            s = 9.0
            for nm, lo, hi, ex in r[0]:
                ctr = (lo + hi) / 2
                ii = tuple(int(round((ctr[k] - Cg[0, 0, 0][k]) / ROOM_PITCH)) for k in range(3))
                if not all(0 <= ii[k] < fld.shape[k] for k in range(3)):
                    s = -9
                    break
                s = min(s, float(_boxmin_cached(fex if ex else fld, tuple(np.round(hi - lo, 1)))[ii]))
            cand.append((s, ym, zm))
    cand.sort(key=lambda t: -t[0])
    print(f"  crown drive valid at {len(cand)} motor places; coarse best {cand[0][0]:+.2f}", flush=True)
    _, hs = h3e_boxes(np.zeros(3), np.zeros(3), hook)
    H = _boxmin_cached(fld, tuple(np.round(hs, 1)))
    best = None
    for s_m, ym, zm in cand[:8]:
        mb = crown_drive(c, ym, zm)[0]
        sc = np.minimum(H, s_m)
        for nm, lo, hi, ex in mb:
            sc = np.minimum(sc, np.max(np.maximum(Cg - hs / 2 - hi, lo - Cg - hs / 2), -1))
        # packs as a mirrored pair (A at x < 0, B = A mirrored in x = 0): no overlap by construction, not two clusters
        ixm = np.clip(np.round((-Cg[:, 0, 0, 0] - Cg[0, 0, 0, 0]) / ROOM_PITCH).astype(int), 0, fld.shape[0] - 1)
        tot = np.minimum(sc, sc[ixm])
        tot = np.where(Cg[..., 0] <= -hs[0] / 2 + 0.01, tot, -99)
        flat = tot.ravel()
        top = np.argpartition(-flat, 60)[:60]
        P = Cg.reshape(-1, 3)[top[np.argsort(-flat[top])]]
        picks = []
        for q in P:
            if all(np.abs(q - r).max() > 2.0 for r in picks):
                picks.append(q)
            if len(picks) == 3:
                break
        for q in picks:
            st = dict(ym=ym, zm=zm, A=q.copy())
            sc2, kk, res = _eval_b3(c, st, fixed, wall, hook)
            if best is None or sc2 > best[0]:
                best = (sc2, kk, res, st)
    sc, kk, res, st = best
    for _ in range(steps):
        better = False
        moves = [("ym", None, d) for d in (-.5, .5)] + [("zm", None, d) for d in (-.5, .5)]
        moves += [("A", a, d) for a in range(3) for d in (-.5, .5)]
        for q, a, d in moves:
            n = dict(st, A=st["A"].copy())
            if a is None:
                n[q] += d
            else:
                n[q][a] += d
            s2, k2, r2 = _eval_b3(c, n, fixed, wall, hook)
            if s2 > sc + 1e-3:
                sc, kk, res, st, better = s2, k2, r2, n, True
        if not better:
            break
    boxes = crown_drive(c, st["ym"], st["zm"])[0] + h3e_boxes(st["A"], _mir(st["A"]), hook)[0] + fixed
    # JSTs: two mated pairs on their leads, placed in the room that is left (best of 3 orientations each)
    Q = Cg.reshape(-1, 3)
    for nm, lo, hi, *_ in boxes[:len(boxes) - len(fixed)]:
        fld = np.minimum(fld, (n0.pt_box(Q, lo, hi) - np.all((Q >= lo) & (Q <= hi), 1) * 0.5).reshape(fld.shape))
    for j in range(2):
        cbest = None
        for perm in ((0, 1, 2), (1, 0, 2), (2, 1, 0)):
            sz = tuple(np.array(JST_XH)[list(perm)])
            mf = _boxmin(fld, sz)
            ii = np.unravel_index(np.argmax(mf), mf.shape)
            if cbest is None or mf[ii] > cbest[0]:
                cbest = (mf[ii], Cg[ii], np.array(sz))
        lo, hi = cbest[1] - cbest[2] / 2, cbest[1] + cbest[2] / 2
        boxes.append((f"jst{j + 1}", lo, hi, False))
        fld = np.minimum(fld, (n0.pt_box(Q, lo, hi) - np.all((Q >= lo) & (Q <= hi), 1) * 0.5).reshape(fld.shape))
    sc, kk, res = eval_layout(c, boxes, wall)
    return dict(least=sc, bind=kk, res=res, st=st, boxes=boxes, c=c, fixed=fixed,
                info=crown_drive(c, st["ym"], st["zm"])[1])


_BMC = {}


def _boxmin_cached(fld, size):
    k = (id(fld), size)
    if k not in _BMC:
        _BMC[k] = _boxmin(fld, size)
    return _BMC[k]


def _mir(a):
    return a * np.array([-1.0, 1.0, 1.0])


def _eval_b3(c, st, fixed, wall, hook=False):
    r = crown_drive(c, st["ym"], st["zm"])
    if r is None:
        return -9.0, "crown drive invalid", {}
    return eval_layout(c, r[0] + h3e_boxes(st["A"], _mir(st["A"]), hook)[0] + fixed, wall)


def pr_crown(info=None):
    """B1 numbers that do not need the layout: tooth counts, ratio, crown tooth print."""
    m = CROWN["m"]
    s_tip = math.pi * m / 2 - 2 * m * math.tan(ALPHA)              # crown tooth top land at R0 (rack-like)
    print(f"== crown pair (B1) ==\npinion {CROWN['z_pinion']}T x +{CROWN['x']} on the N10 shaft (axis Y) → crown "
          f"{CROWN['z_crown']}T (axis X, R0 {m * CROWN['z_crown'] / 2:.1f}, teeth R {CROWN['r_in']}–{CROWN['r_out']}, "
          f"face {CROWN['r_out'] - CROWN['r_in']:.1f} = {(CROWN['r_out'] - CROWN['r_in']) / m:.1f} m) + spur "
          f"{CROWN['z_spur']}T x +{CROWN['x']} on the same part → idler (−{CROWN['x']}) → strip. crank:motor = "
          f"{CROWN['z_pinion']}/{CROWN['z_crown']} × {CROWN['z_spur']}/10 = 1:{CROWN['z_crown'] // CROWN['z_pinion']} "
          f"(0.50); crown tooth at R0: thickness {math.pi * m / 2:.2f}, top land {s_tip:.2f} "
          f"({s_tip / 0.4:.1f} lines of 0.4), height {2.25 * m:.2f} = {2.25 * m / 0.2:.0f} layers of 0.2 "
          f"({2.25 * m / 0.12:.0f} at 0.12, variable layer height on the crown part)")
    if info:
        print(f"layout: crown centre y {info['crown_c'][0]:.1f} z {info['crown_c'][1]:.1f}, pinion y "
              f"{info['pinion_y']:.1f}; spur → {info['idler']}T idler at y {info['idler_c'][0]:.1f} z "
              f"{info['idler_c'][1]:.1f} → {info['target']}; in-plane clearance {info['clear']:+.2f}; crown pitch "
              f"plane x {info['xf']:.2f}, spine walls x {info['xl']:.2f} / +{info['xr']:.2f}")


def pr_motor_only(walls=(3.0, 1.6), led=5.0, S=S_FIX, ball=BALL_D2, dy=CRANK_DY_65, eyes="vertical"):
    """B3 bound: the motor group (motor, seat, clamp ears, terminals, wires, pinion, crown, idler) with the fixed B3
    boxes and NO cells, exact at the 12 best coarse places: if this is < 0 no cell layout can be ≥ 0."""
    for wall in walls:
        c = _ctx(S, ball, dy)
        c["wall"] = wall
        fixed, fld, Cg = fixed_boxes(c, led, eyes)
        best = None
        cand = []
        for ym in np.arange(-24, 24.1, 1.0):
            for zm in np.arange(18, 40.1, 1.0):
                r = crown_drive(c, ym, zm)
                if r is not None:
                    cand.append((ym, zm, r[0]))
        sco = []
        for ym, zm, bx in cand:
            s_, k_, _ = eval_layout(c, bx + fixed, wall, exact=False)
            sco.append((s_, ym, zm))
        sco.sort(key=lambda t: -t[0])
        for _, ym, zm in sco[:12]:           # exact on the 12 best coarse places (coarse and exact can disagree)
            s_, k_, _ = eval_layout(c, crown_drive(c, ym, zm)[0] + fixed, wall)
            if best is None or s_ > best[0]:
                best = (s_, k_, ym, zm)
        s_, k_, res = eval_layout(c, crown_drive(c, best[2], best[3])[0] + fixed, wall)
        nxt = sorted(res.items(), key=lambda kv: kv[1])[:5]
        print(f"D4 {wall}: motor group + B3 boxes, no cells: least {s_:+.2f} ({k_}) at motor y {best[2]} z {best[3]}; "
              + ", ".join(f"{k} {v:+.2f}" for k, v in nxt[1:]))
        for b in fixed:
            print(f"    {b[0]:12s} {np.round(b[1], 1).tolist()} .. {np.round(b[2], 1).tolist()}")


def pr_layouts4(walls=(3.0,), led=5.0, also_led=3.0, eyes="vertical", hook=False):
    """B3: one search per body wall for D1b + crown + H3e with every B3 box; the 3 mm LED re-checked exactly on the
    5 mm layout (eyes board moved, no new search). Writes out/.cache/layouts4_0.650.json for the plan figure."""
    import time
    t = time.time()
    keep = []
    for wall in walls:
        r = search_b3(wall=wall, led=led, eyes=eyes, hook=hook)
        pairs = sorted(r["res"].items(), key=lambda kv: kv[1])[:6]
        print(f"D4 {wall}: least {r['least']:+.2f} ({r['bind']}); next " + ", ".join(f"{k} {v:+.2f}" for k, v in pairs[1:]))
        pr_crown(r["info"])
        fx3, _, _ = fixed_boxes(r["c"], also_led, eyes)
        b3 = [b for b in r["boxes"] if not b[0].startswith(("LED", "eyes"))] + [b for b in fx3 if b[0].startswith(("LED", "eyes"))]
        s3, k3, _ = eval_layout(r["c"], b3, wall)
        print(f"  same layout with {also_led:g} mm LEDs: least {s3:+.2f} ({k3})")
        for nm, lo, hi, *_ in r["boxes"]:
            print(f"    {nm:22s} {np.round(lo, 1).tolist()} .. {np.round(hi, 1).tolist()}")
        keep.append(dict(wall=wall, least=float(r["least"]), bind=r["bind"], led3=float(s3),
                         boxes=[(b[0], list(map(float, b[1])), list(map(float, b[2]))) for b in r["boxes"]],
                         info={k: (list(map(float, v)) if hasattr(v, "__len__") and not isinstance(v, str) else
                                   (v if isinstance(v, str) else float(v))) for k, v in r["info"].items()}))
    if eyes == "vertical" and not hook:      # R0 only: the plan figure reads this file
        with open(os.path.join(CACHE, f"layouts4_{S_FIX:.3f}.json"), "w") as f:
            json.dump(keep, f, indent=1)
    print(f"({time.time() - t:.0f} s)")


if __name__ == "__main__":
    a = sys.argv[1:] or ["gear", "cell", "pins", "pivot", "arms", "neck", "crown", "asm"]
    if a[0] == "layouts3":     # best rows only, at the S given: probes.py layouts3 0.70
        O = [(3.0, "D1b al", "H3e"), (1.6, "D1b al", "H3e"), (1.6, "D1b al", "H3 ")]
        pr_layouts(float(a[1]), only=O)
        sys.exit()
    if a[0] == "figure":
        pr_figure(a[1])
        sys.exit()
    if a[0] == "motoronly":
        pr_motor_only(eyes="flat" if "flat" in a[1:] else "vertical")
        sys.exit()
    if a[0] == "layouts4":     # B3: probes.py layouts4 [3.0 [1.6]]
        pr_layouts4(tuple(float(w) for w in a[1:] if w[0].isdigit()) or (3.0,),
                    eyes="flat" if "flat" in a[1:] else "vertical", hook="hook" in a[1:])
        sys.exit()
    for name in a:
        {"crown": pr_crown, "neck": pr_neck, "inside": pr_inside, "arms": pr_arms, "pivot": pr_pivot, "gear": pr_gear, "cell": pr_cell,
         "pins": pr_pins, "asm": pr_asm, "slice": pr_slice, "layouts": pr_layouts,
         "inside65": lambda: pr_inside((0.65,), dy=CRANK_DY_D2, ball=BALL_D2, walls=(3.0, 1.6))}[name]()
