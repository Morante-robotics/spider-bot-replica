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
CRANK_DY = (-1.5, -0.5, 2.5, 0.0)  # per-crank Y offset from N0 (mm at S 0.60): set from pr_arms (c7)
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
        O, r = Lg["O"], p_at(0.6)["r"]
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
CRANK_DY_D2 = (0.0, 0.0, 2.0, 0.0)  # crank offsets used with Ø2 balls (coordinator's pr_inside run, S 0.60 mm)
_ARMF = {}


def arm_field(S, ball, dy):
    """Room (mm) from grid points to the swept arms (ends and bars, all legs, a full turn), LEG_PATH taken off;
    same grid as room_grid; cached on disk per S, ball, offsets."""
    key = (S, ball, tuple(dy))
    if key not in _ARMF:
        path = os.path.join(CACHE, f"arms_{S:.3f}_{ball}_{'_'.join(f'{d:g}' for d in dy)}_{ROOM_PITCH}.npz")
        if os.path.exists(path):
            _ARMF[key] = dict(np.load(path))
        else:
            k = S / 0.6
            L = legs_ax(p_at(S), poses=24, dy=tuple(d * k for d in dy))
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
    k = S / 0.6
    dyk = tuple(d * k for d in dy)
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
    for nm, lo, hi, ex in boxes:
        mk = (tuple(np.round(lo, 3)), tuple(np.round(hi, 3)), wall, exact)
        if mk not in memo:
            memo[mk] = (inside_gap(box_pts(lo, hi), S, wall, exact),
                        (n0.pt_box(c["X"], lo, hi) - c["R"]).min() - F.LEG_PATH.side)
        res[f"{nm}↔shell"], res[f"{nm}↔arms"] = memo[mk]
        res[f"{nm}↔cranks"] = min(box_sep((lo, hi), s) for s in c["sweeps"])
        if not ex:
            res[f"{nm}↔strip"] = box_sep((lo, hi), c["strip"])
    for i, (n1_, l1, h1, _) in enumerate(boxes):
        for n2_, l2, h2, _ in boxes[i + 1:]:
            if n1_.split()[0] != n2_.split()[0]:          # motor + its own crown / worm are one sub-assembly
                res[f"{n1_}↔{n2_}"] = box_sep((l1, h1), (l2, h2))
    k = min(res, key=res.get)
    return res[k], k, res


def search_layouts(S=0.65, ball=BALL_D2, dy=CRANK_DY_D2, walls=(3.0, 1.6), refine=6, only=None):
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


def pr_arms(margin=0.2):
    """Item 2: arm end ↔ arm (real ends, 24 poses) per side; per-crank Y offsets searched pair by pair (a chain),
    least total shift with every pair ≥ LEG_PATH 0.8 + margin; crank gears ≥ 8.45 apart (tips 7.45 + 2 × GEAR_TIP)."""
    import itertools
    print("== arm ↔ arm (pr6): least gap − LEG_PATH 0.8, mm; ≥ 0 passes ==")
    p = p_at(0.60)
    L0 = legs_ax(p, poses=24)
    ys = [L0[i]["O"][1] for i in range(4)]
    D = np.arange(-3, 3.01, 0.5)
    for ball in BALLS.values():
        def pair(i, a, b, xc=None):
            dy = [0.0] * 4
            dy[i], dy[i + 1] = a, b
            if ys[i + 1] + b - ys[i] - a < 8.45:
                return -9
            L = legs_ax(p, poses=24, dy=dy, xc=xc)
            return min(capsule_gap(c1, c2) - F.LEG_PATH.side for k in range(24)
                       for c1 in arm_parts(L[i], k, ball) for c2 in arm_parts(L[i + 1], k, ball))
        c0 = [pair(i, 0, 0) if ys[i + 1] - ys[i] >= 8.45 else pair_raw(p, i, ball) for i in range(3)]
        print(f"c0 as N1, Ø{ball:.0f} ball (end Ø{2 * end_r(ball):.1f}): pairs 1-2/2-3/3-4 "
              f"{c0[0]:+.2f} / {c0[1]:+.2f} / {c0[2]:+.2f}; cranks 2-3 {ys[2] - ys[1]:.1f} apart (< 8.45: gears clash)")
        T = [{(a, b): pair(i, a, b) for a in D for b in D} for i in range(3)]
        ok = [(sum(abs(c) for c in cb), cb) for cb in itertools.product(D, repeat=4)
              if min(T[i][(cb[i], cb[i + 1])] for i in range(3)) >= margin]
        if ok:
            cost, cb = min(ok)
            gp = [T[i][(cb[i], cb[i + 1])] for i in range(3)]
            Lc = legs_ax(p, poses=24, dy=cb)
            yaw = [math.degrees(math.atan2(Lc[i]["u"][6][1], Lc[i]["u"][6][0]) -
                                math.atan2(L0[i]["u"][6][1], L0[i]["u"][6][0])) for i in range(4)]
            sw = [np.ptp(np.degrees(np.arctan2(Lc[i]["u"][:, 1], Lc[i]["u"][:, 0]))) for i in range(4)]
            print(f"c7 crank Y offsets {tuple(float(c) for c in cb)}, Ø{ball:.0f}: pairs {gp[0]:+.2f} / {gp[1]:+.2f} / "
                  f"{gp[2]:+.2f}; spacing {[round(ys[i + 1] + cb[i + 1] - ys[i] - cb[i], 1) for i in range(3)]}; "
                  f"arm yaw change {[round(y, 1) for y in yaw]}° (absorbed by the arm-leg key, D3a); "
                  f"swing p-p {[round(s, 1) for s in sw]}°")
        else:
            print(f"Ø{ball:.0f}: no Y offsets within ±3 give ≥ {margin}")
    for name, xc in (("c1 crank 3 XC 11", (6, 6, 11, 6)), ("c8 cranks 2, 4 XC 9 (alternate)", (6, 9, 6, 9))):
        g = [pair_raw(p, i, 3.0, xc=xc) for i in range(3)]
        print(f"{name}, Ø3: pairs {g[0]:+.2f} / {g[1]:+.2f} / {g[2]:+.2f}")


def pair_raw(p, i, ball, xc=None, dy=(0, 0, 0, 0)):
    L = legs_ax(p, poses=24, dy=dy, xc=xc)
    return min(capsule_gap(c1, c2) - F.LEG_PATH.side for k in range(24)
               for c1 in arm_parts(L[i], k, ball) for c2 in arm_parts(L[i + 1], k, ball))


def pr_pivot():
    """Items 3-4: root block swept in plan at the rim, rim left between notches 2-3, per pin; flare and crown."""
    print("== pivot (pr2/pr4 rev 2): swept root block at the rim and what is left between notches ==")
    p = p_at(0.60)
    L = legs_ax(p, poses=72)
    for name, pin in (("D2a Ø3 steel pin", 3.0), ("D2b M2 screw", 2.0), ("D2e Ø2 steel pin", 2.0)):
        w = F.bore(pin, F.STEEL) + 2 * W_LOAD                       # block across the leg
        lb = w + 1.0                                                 # along the leg, round the bore
        gaps = {}
        for a, b in ((0, 1), (1, 2), (2, 3)):
            poly = []
            for i in (a, b):
                P = L[i]["P"][:2]
                pts = []
                for k in range(72):
                    u = L[i]["u"][k]
                    yaw = math.atan2(u[1], u[0])
                    e = np.array([math.cos(yaw), math.sin(yaw)])
                    n = np.array([-e[1], e[0]])
                    for sa in (-1, 1):
                        for sb in (-1, 1):
                            pts.append(P + e * sa * lb / 2 + n * sb * w / 2)
                poly.append(np.array(pts))
            # gap between the swept blocks measured across the line joining the pivots
            d = cKDTree(poly[0]).query(poly[1])[0].min()
            c = np.linalg.norm(L[a]["P"][:2] - L[b]["P"][:2])
            # convex sweeps: least distance between the hulls (sample hull edges)
            h0 = poly[0][ConvexHull(poly[0]).vertices]
            h1 = poly[1][ConvexHull(poly[1]).vertices]
            e0 = np.vstack([seg_pts(h0[j], h0[(j + 1) % len(h0)], 0.05) for j in range(len(h0))])
            e1 = np.vstack([seg_pts(h1[j], h1[(j + 1) % len(h1)], 0.05) for j in range(len(h1))])
            d = cKDTree(e0).query(e1)[0].min()
            gaps[f"{a + 1}-{b + 1}"] = (c, d, d - 2 * F.LEG_PATH.side)
        swept = np.ptp(poly[0], 0)
        print(f"{name}: block {w:.1f} × {lb:.1f}; " + "; ".join(
            f"notches {k}: pivots {c:.1f} apart, blocks {d:.2f}, rim left {r:+.2f}" for k, (c, d, r) in gaps.items()))
    # pitch: one flare across the stack, crowned faces
    pitch = []
    for i in range(4):
        u = L[i]["u"]
        el = np.degrees(np.arcsin(u[:, 2]))
        pitch.append(np.ptp(el) / 2)
    pm = max(pitch)
    print(f"pitch amplitude per leg ±{', ±'.join(f'{x:.1f}' for x in pitch)}°: flare ±{pm + 2:.0f}° (+2° margin)")
    for pin in (3.0, 2.0):
        w = F.bore(pin, F.STEEL) + 2 * W_LOAD
        hstack = 2 * 2.4                                             # arm eye 2.4 + leg eye 2.4, one flare
        edge = (w / 2) * math.tan(math.radians(pm))
        rc = (w / 2) ** 2 / (2 * edge) if edge else 0
        print(f"Ø{pin:.0f}: stack {hstack:.1f} high, block {w:.1f} wide: flat face edge travel {edge:.2f} a side at "
              f"±{pm:.1f}°; crown R ≈ {rc:.0f} mm keeps the contact at the centre; play floor+keeper = "
              f"WINDOW {F.WINDOW.side:.1f} ≥ {edge:.2f}; key along the block 2 × {w + 1.0:.1f} long")


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
    R = n1.run()
    st = R["st"]
    p = R["p"]
    L = legs_ax(p, poses=24)
    w, lb = F.bore(3.0, F.STEEL) + 2 * W_LOAD, F.bore(3.0, F.STEEL) + 2 * W_LOAD + 1.0
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
    for ax, (title, kp) in zip(axs, (("N1 (approved look): hull of the 9 mm collar", R["keep"]),
                                     ("N2 rev 2: notch per leg at LEG_PATH 0.8, skirt slots open at the bottom", keep))):
        items = []
        for kk, col in (("base", "#7f8c8d"), ("body", "#c0392b")):
            items.append(dict(mesh=trimesh.Trimesh(st[kk + "_v"], st[kk + "_f"][kp[kk]]), color=col))
        items.append(dict(mesh=trimesh.Trimesh(st["eyes_v"], st["eyes_f"]), color="#2e86c1"))
        Fg.draw(ax, items, view=(8, 0), edge_angle=75.0)
        ax.set_title(title, fontsize=Fg.FONT + 1)
    fig.suptitle("Right side, legs off: windows and rim between notches (S 0.60, Ø3 pin, D2a)", fontsize=Fg.FONT + 2)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    print("wrote", path)



def pr_layouts(S=0.65, only=None):
    """Rev 3 (S fixed at 0.65, Ø2 balls): every drive × cell-holder layout × body wall; least room and binding pair.
    Writes out/.cache/layouts_<S>.json for the plan figure."""
    import time
    t = time.time()
    print(f"== inside layouts (S {S}, Ø{BALL_D2:g} balls, offsets {CRANK_DY_D2}): least room, mm (≥ 0 fits) ==")
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

if __name__ == "__main__":
    a = sys.argv[1:] or ["gear", "cell", "pins", "pivot", "arms", "asm", "inside", "layouts"]
    if a[0] == "layouts3":     # best rows only, at the S given: probes.py layouts3 0.70
        O = [(3.0, "D1b al", "H3e"), (1.6, "D1b al", "H3e"), (1.6, "D1b al", "H3 ")]
        pr_layouts(float(a[1]), only=O)
        sys.exit()
    if a[0] == "figure":
        pr_figure(a[1])
        sys.exit()
    for name in a:
        {"inside": pr_inside, "arms": pr_arms, "pivot": pr_pivot, "gear": pr_gear, "cell": pr_cell,
         "pins": pr_pins, "asm": pr_asm, "slice": pr_slice, "layouts": pr_layouts,
         "inside65": lambda: pr_inside((0.65,), dy=CRANK_DY_D2, ball=BALL_D2, walls=(3.0, 1.6))}[name]()
