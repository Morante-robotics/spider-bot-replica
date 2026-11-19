"""N1 mock-up of the looks Spider-Bot: jenscolt's real parts at 60 %, simplified, on N0's motion and inner boxes.

Parts  body (+ 2 eyes, 2 small eyes, front dome) and base: jenscolt's STLs, vertex-clustered to <= 25k triangles each,
       scaled about the base's bottom centre (as N0), one window per leg root cut in body and base.
       Legs: his L_leg2 (inner arm + upper leg) and L_leg1 (blade), the same pair for all 8 legs (left = mirror),
       bent and stretched along N0's leg path (a spine-to-spine warp, see warp()), then carried rigidly with the
       crank like N0's legs. His coordinates are 100 %; N0's P0 (scale, path, boxes, crank) is imported unchanged.
Windows each leg's root section (within COLLAR of the pivot) swept over the 24 crank poses, convex hull, +1 mm;
       the body and base triangles touching that hull are removed. Window = size of the hull.
Checks 24 poses; surfaces are sampled to <= 0.6 mm (body, base) and 1.0 mm (legs); every gap = nearest sample
       distance - SLACK (0.4 mm) so it is conservative. Pass: every gap >= 0.
Not N1: no build123d, no cad_verify, no STEP. The sources are not manifold (65 loose pieces), so no manifold3d
       booleans: windows are triangle removal, the "inside" test is N0's convex hull with a wall.

Usage (repo root):
    uv run python cad/mockup/n1.py [--png out.png] [--lang en] [--photo toy.jpg] [--set key=val ...]
Meshes by Jens Colt, CC BY-NC-SA (cad/carcass-jenscolt/).
"""
import argparse, os, sys, time

T0 = time.time()
import numpy as np
from scipy.spatial import ConvexHull, cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import n0  # noqa: E402  (P0, legs geometry, boxes, one source for scale, crank and path)

TL, J = n0.TL, n0.J
CACHE = os.path.join(HERE, ".cache")
P1 = dict(
    TRI_MAX=25000,      # triangles per simplified body / base mesh
    LEG_CELL=1.6,       # leg vertex-cluster cell at 100 % (mm)
    H_BODY=0.6, H_LEG=1.0,   # sampling spacing for the distance checks (mm, robot scale)
    SLACK=0.4,          # subtracted from every sampled gap
    COLLAR=9.0,          # leg root section that makes the window: distance to the pivot (mm; 2026-11-19, 12 → 9: windows ≈ 20 % smaller)
    BOWL_C=(35.6, -7.6, 80.0), TAB_DEPTH=1.0,   # empty bowl: centre for the outward rays, tab depth (jenscolt mm)
    WIN=1.0,            # window margin around the swept leg (mm)
    WALL_BASE=1.2,      # base wall (assumed)
    WALL_DOME=3.0,      # body wall: jenscolt's dome section is ~5 mm at 100 %
    DECK=(62 - 38) * 0.6,  # the base's top face, above its bottom (jenscolt z 62)
    kb_in=0.20,         # inner arm / hub: thickness across the leg (side) vs jenscolt x S (middle notches 7.7 mm apart)
    kn_in=0.15,         # inner arm: in-plane scale
    k_up=0.6,           # upper leg and blade cross-section scale (= S)
    kt=0.25,            # end caps of the legs (the hub's tip, the foot): along-the-spine scale
    root_len=14.0,      # mm past the pivot over which the thin root section (kb_in, kn_in) grows into the upper leg's (k_up)
    eye_y=-52.0, small_eye_y=-49.6,   # eye centres (jenscolt mm), front face of the sockets at y -60..-44
)
# N0 parameters changed at N1 (Morante, 2026-11-19): the motor 1 mm higher, clear of the crank hubs
P0_N1 = dict(motor=(0, 4, 22, 10, 24, 12), shaft=(0, -13, 22, 3, 10, 3))
EYES = [("eye", (21.7, 91.4)), ("eye", (49.5, 91.4)), ("small_eye", (7.5, 100.0)), ("small_eye", (63.7, 100.0))]


# ---------------------------------------------------------------- meshes
def load(name):
    import trimesh
    m = trimesh.load(J + name + ".stl", process=False)
    return np.asarray(m.vertices, float), np.asarray(m.faces)


def cluster(V, F, cell):
    q = np.round(V / cell).astype(np.int64)
    u, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.ravel()
    cnt = np.bincount(inv)
    W = np.stack([np.bincount(inv, V[:, k]) / cnt for k in range(3)], 1)
    G = inv[F]
    G = G[(G[:, 0] != G[:, 1]) & (G[:, 1] != G[:, 2]) & (G[:, 0] != G[:, 2])]
    G = np.unique(np.sort(G, 1), axis=0)
    used = np.unique(G)
    remap = -np.ones(len(W), int)
    remap[used] = np.arange(len(used))
    return W[used], remap[G]


def simplify(V, F, tri_max, cell0=0.4):
    cell = cell0
    while True:
        W, G = cluster(V, F, cell)
        if len(G) <= tri_max:
            return W, G
        cell *= 1.12


def dense(V, F, L):
    """Surface points with spacing ~ L/2: split triangles at their longest edge's midpoint until every edge is <= L
    (slivers cost only their length), keep the (deduplicated) vertices. Returns points and the face of each."""
    T, fid = V[F], np.arange(len(F))
    pts, ids = [], []
    while len(T):
        E = np.stack([np.linalg.norm(T[:, (k + 1) % 3] - T[:, k], axis=1) for k in range(3)], 1)
        big = E.max(1) > L
        pts.append(T[~big].reshape(-1, 3))
        ids.append(np.repeat(fid[~big], 3))
        T, fid, E = T[big], fid[big], E[big]
        if not len(T):
            break
        k = E.argmax(1)
        r = np.arange(len(T))
        a, b, c = T[r, k], T[r, (k + 1) % 3], T[r, (k + 2) % 3]
        m = (a + b) / 2
        T = np.concatenate([np.stack([a, m, c], 1), np.stack([m, b, c], 1)])
        fid = np.concatenate([fid, fid])
    P, I = np.vstack(pts), np.concatenate(ids)
    _, ix = np.unique(np.round(P / (L / 8)).astype(np.int64), axis=0, return_index=True)
    return P[ix], I[ix]


def to_robot(V, S):
    c = np.array([TL.CENTER[0] * n0.K120, TL.CENTER[1] * n0.K120, TL.BASE_BOTTOM * n0.K120])
    return (V - c) * S


def empty_bowl(V, F, q):
    """Keep only jenscolt's bowl skin + rim: the largest connected piece (drops the posts and block slivers), then drop the
    faces of the inner tabs (his static-leg plugs): faces with another surface straight outward from the bowl centre
    and deeper than TAB_DEPTH (his mm) inside the piece's convex hull. Outer skin and the rim notches stay."""
    import trimesh
    from trimesh.proximity import signed_distance
    M = trimesh.Trimesh(V, F, process=True)
    M = max(M.split(only_watertight=False), key=lambda c: len(c.faces))
    C = M.triangles_center
    d = C - np.array(q["BOWL_C"])
    d /= np.linalg.norm(d, axis=1)[:, None]
    _, ri, _ = M.ray.intersects_location(C + d * 0.05, d)
    inner = np.bincount(ri, minlength=len(C)) >= 1
    tab = inner & (signed_distance(M.convex_hull, C) > q["TAB_DEPTH"])
    return np.asarray(M.vertices), np.asarray(M.faces)[~tab]


def static(p, q):
    """Simplified body (with eyes and front dome) and base in the robot's frame, cached."""
    path = os.path.join(CACHE, f"n1_static6_{p['S']:.3f}_{q['TRI_MAX']}.npz")
    if os.path.exists(path):
        return dict(np.load(path))
    out = {}
    for n in ("body", "base"):
        V, F = load(n)
        if n == "base":                                    # jenscolt's base is solid: open its top face (our base is hollow)
            T = V[F]
            nz = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            nz = nz[:, 2] / (np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1) + 1e-9)
            z = T[:, :, 2].mean(1)
            xc = T[:, :, 0].mean(1)
            deck = (abs(nz) > 0.9) & (z > 61.9) & (z < 62.5)
            block = (z > 60.0) & (xc > 11) & (xc < 60)       # jenscolt's inner posts and mounts (for his lights), hidden by the dome
            F = F[~(deck | block)]
            V, F = empty_bowl(V, F, q)
        V, F = simplify(V, F, q["TRI_MAX"])
        out[n + "_v"], out[n + "_f"] = to_robot(V, p["S"]), F
    parts = []
    for n, (x, z) in EYES:
        V, F = load(n)
        ctr = (V.min(0) + V.max(0)) / 2
        V = V - ctr + [x, q["eye_y"] if n == "eye" else q["small_eye_y"], z]
        parts.append(cluster(V, F, 0.7))
    V, F = load("sensor")                              # jenscolt's file name for the small front dome
    parts.append(cluster(V, F, 0.7))
    off = np.cumsum([0] + [len(v) for v, _ in parts])
    out["eyes_v"] = to_robot(np.vstack([v for v, _ in parts]), p["S"])
    out["eyes_f"] = np.vstack([f + o for (_, f), o in zip(parts, off)])
    out["ball_v"] = np.vstack([out["body_v"], out["eyes_v"]])
    out["ball_f"] = np.vstack([out["body_f"], out["eyes_f"] + len(out["body_v"])])
    out["cpb"], out["cfb"] = dense(out["ball_v"], out["ball_f"], 3.0)
    out["cpa"], out["cfa"] = dense(out["base_v"], out["base_f"], 3.0)
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(path, **out)
    return out


# ---------------------------------------------------------------- leg warp
def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def resample(P, n=160):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1), t


def tangents(S):
    return unit(np.gradient(S, axis=0))


def frames(t, side):
    b = unit(side - (t @ side)[:, None] * t)
    return b, np.cross(t, b)


def spine_mesh(V, kind):
    """Old spine of a leg mesh (jenscolt mm): bin centroids from the foot/hub end to the top."""
    if kind == "blade":
        c = V.mean(0)
        ax = np.linalg.svd(V - c, full_matrices=False)[2][0]
        ax = ax if ax[2] > 0 else -ax                        # from the foot up
        s = (V - c) @ ax
        edges = np.linspace(s.min(), s.max(), 13)
        pts = [V[(s >= a) & (s <= b)].mean(0) for a, b in zip(edges[:-1], edges[1:])]
        P = np.array(pts)[::-1]                              # top first
        return P
    hub = V[V[:, 2] < 55].mean(0)
    zs = np.arange(58, 80, 3.5)
    pts = [hub] + [V[(V[:, 2] >= z - 2) & (V[:, 2] < z + 2)].mean(0) for z in zs]
    return np.array(pts)


def warp(V, S_old, S_new, brk_old, brk_new, kn, kb, side_old, side_new, kt=0.25):
    """Warp the vertices V along S_old onto S_new: arc length remapped piecewise-linearly between the breakpoints
    (arc lengths), the offset from the spine kept in the spine's frame (along: kt, in plane: kn(s), across: kb(s))."""
    So, to = resample(S_old)
    Sn, tn = resample(S_new)
    d, i = cKDTree(So).query(V)
    sl = to[i]
    s_new = np.interp(sl, brk_old, brk_new)
    sl_c = np.clip(s_new, 0, tn[-1])
    A = np.stack([np.interp(sl_c, tn, Sn[:, k]) for k in range(3)], 1)
    to_, no = tangents(So), None
    bo, no = frames(to_, side_old)
    tn_, = (tangents(Sn),)
    bn, nn = frames(tn_, side_new)
    off = V - So[i]
    dt, db, dn = (off * to_[i]).sum(1), (off * bo[i]).sum(1), (off * no[i]).sum(1)
    it = np.stack([np.interp(sl_c, tn, tn_[:, k]) for k in range(3)], 1)
    ib = np.stack([np.interp(sl_c, tn, bn[:, k]) for k in range(3)], 1)
    inn = np.stack([np.interp(sl_c, tn, nn[:, k]) for k in range(3)], 1)
    return A + kt * dt[:, None] * it + (kb(s_new) * db)[:, None] * ib + (kn(s_new) * dn)[:, None] * inn, (to, tn)


def leg_meshes(p, q, geom0=None):
    """jenscolt's two leg meshes clustered (cached) and their spines: (V2, F2, V1, F1, spine2, spine1)."""
    path = os.path.join(CACHE, f"n1_legsrc_{q['LEG_CELL']}.npz")
    if os.path.exists(path):
        d = np.load(path)
        return tuple(d[k] for k in ("V2", "F2", "V1", "F1", "sp2", "sp1"))
    V2o, F2o = cluster(*load("L_leg2"), q["LEG_CELL"])
    V1o, F1o = cluster(*load("L_leg1"), q["LEG_CELL"])
    out = (V2o, F2o, V1o, F1o, spine_mesh(V2o, "upper"), spine_mesh(V1o, "blade"))
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(path, **dict(zip(("V2", "F2", "V1", "F1", "sp2", "sp1"), out)))
    return out


def build_leg(p, q, src, P, A0, ang):
    V2o, F2o, V1o, F1o, sp2, sp1 = src
    pts, rad, ni = n0.leg_shape(P, A0, ang, p)
    inner = np.linspace(A0, P, 5)
    new2 = np.vstack([inner[:-1], pts[ni:ni + 10]])           # A0 ... P ... K
    new1 = pts[ni + 10:]                                      # blade top ... foot
    rd = np.array([np.cos(ang), np.sin(ang), 0])
    z = np.array([0, 0, 1.0])
    side_new = np.cross(z, rd)
    # old plane: horizontal direction of each old spine from its first to last point
    def rd_old(sp):
        d = sp[-1] - sp[0]
        return unit(np.array([d[0], d[1], 0]))
    S = p["S"]
    # leg2 (inner arm + upper): breakpoints at the spine point nearest z = 61 (the rim) / the new P
    so, _ = resample(sp2)
    to_old = np.r_[0, np.cumsum(np.linalg.norm(np.diff(so, axis=0), axis=1))]
    iP = np.argmin(abs(so[:, 2] - 61))
    sn, tn2 = resample(new2)
    s_old_P = to_old[iP]
    s_new_P = np.r_[0, np.cumsum(np.linalg.norm(np.diff(inner, axis=0), axis=1))][-1]
    # new arc length of P along new2 = length of the inner arm
    brk_old, brk_new = [0, s_old_P, to_old[-1]], [0, s_new_P, tn2[-1]]
    rl = q["root_len"]
    kb = lambda s: np.interp(s, [s_new_P, s_new_P + rl], [q["kb_in"], q["k_up"]])
    kn = lambda s: np.interp(s, [s_new_P, s_new_P + rl], [q["kn_in"], q["k_up"]])
    V2, info2 = warp(V2o, sp2, new2, brk_old, brk_new, kn, kb, np.cross(z, rd_old(sp2)), side_new, q["kt"])
    so1, _ = resample(sp1)
    L1o = np.linalg.norm(np.diff(sp1, axis=0), axis=1).sum()
    sn1, tn1 = resample(new1)
    k1 = lambda s: np.full_like(s, q["k_up"])
    V1, info1 = warp(V1o, sp1, new1, [0, L1o], [0, tn1[-1]], k1, k1, np.cross(z, rd_old(sp1)), side_new, q["kt"])
    stretch = dict(inner=s_new_P / (S * s_old_P), upper=(tn2[-1] - s_new_P) / (S * (to_old[-1] - s_old_P)),
                   blade=tn1[-1] / (S * L1o))
    return V2, F2o, V1, F1o, stretch, new2[-1]


# ---------------------------------------------------------------- poses
def pose_frames(p, poses=n0.POSES):
    """Per leg (8): P, R0 (neutral), R (poses, 3, 3), A0, sx, angle — N0's crank, copied from n0.legs."""
    c = np.array([TL.CENTER[0] * n0.K120, TL.CENTER[1] * n0.K120, TL.BASE_BOTTOM * n0.K120])
    B = dict(c=c)
    th = np.linspace(0, 2 * np.pi, poses, endpoint=False)
    out = []
    for side, sx in (("R", 1), ("L", -1)):
        for i, (x, y) in enumerate(TL.NOTCHES_RIGHT):
            P = n0.to_frame((x * n0.K120, y * n0.K120, TL.NOTCH_Z * n0.K120), B, p)
            O = np.array([p["XC"], P[1] + p["DY"], P[2] + p["H"]])
            ph = np.pi * TL.GROUP[side][i]
            A = O + p["r"] * (np.cos(th + ph)[:, None] * [0, -1, 0] + np.sin(th + ph)[:, None] * [0, 0, 1])
            A0 = O + p["r"] * np.array([0, -1, 0])
            R0 = n0.frame(n0.unit(P - A0)[None])[0]
            R = n0.frame(n0.unit(P - A))
            out.append(dict(P=P, A0=A0, R0=R0, R=R, sx=sx, ang=np.radians(p["angles"][i]), A=A))
    return out


def carry(loc, g):
    """Leg points in the neutral leg frame (M, 3) -> world over the crank poses (poses, M, 3), mirrored if left."""
    W = g["P"] + np.einsum("mk,nkj->nmj", loc, g["R"])
    return W * [g["sx"], 1, 1]


# ---------------------------------------------------------------- the model
def build(p, q):
    st = static(p, q)
    G = pose_frames(p)
    src = leg_meshes(p, q, None)
    legs = []
    for g in G:
        V2, F2, V1, F1, stretch, K = build_leg(p, q, src, g["P"], g["A0"], g["ang"])
        loc2, loc1 = (V2 - g["P"]) @ g["R0"].T, (V1 - g["P"]) @ g["R0"].T
        locK = (K - g["P"]) @ g["R0"].T
        pts = np.vstack([loc2, loc1])
        Fall = np.vstack([F2, F1 + len(V2)])
        sp, _ = dense(pts, Fall, q["H_LEG"] * 2.2)
        spc, _ = dense(pts, Fall, q["H_LEG"] * 4.5)
        legs.append(dict(g=g, loc=pts, F=Fall, samp=sp, coarse=spc, K=locK, stretch=stretch, n2=len(V2)))
    return st, G, legs


def windows(p, q, legs, st):
    """Remove body and base triangles inside each leg root's swept hull (+ WIN). Returns the kept masks and sizes."""
    dirs = [d for d in np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]) if d.any()]
    dirs = np.array([unit(d) for d in dirs]) * q["WIN"] * 1.08
    keep = {k: np.ones(len(st[k + "_f"]), bool) for k in ("body", "base")}
    sizes = []
    for lg in legs:
        g = lg["g"]
        col = lg["coarse"][np.linalg.norm(lg["coarse"], axis=1) <= q["COLLAR"]]
        W = carry(col, g).reshape(-1, 3)
        H = W[ConvexHull(W).vertices]
        H = (H[:, None] + dirs[None]).reshape(-1, 3)
        hull = ConvexHull(H)
        for k in keep:
            V, F = st[k + "_v"], st[k + "_f"]
            lo, hi = H.min(0), H.max(0)
            cand = np.nonzero(((V >= lo) & (V <= hi)).all(1))[0]
            inside = np.zeros(len(V), bool)
            inside[cand] = ((V[cand] @ hull.equations[:, :3].T + hull.equations[:, 3]) <= 0).all(1)
            keep[k] &= ~inside[F].any(1)
        hv = H[hull.vertices]
        sizes.append(np.ptp(hv, 0))
    return keep, np.array(sizes)


def pdist(X, tree):
    return tree.query(X, distance_upper_bound=4.0)[0]


def cellpts(lo, hi, n=24):
    """6 AG13 as three stacks of two lying along y: three cylinders (r = half the box height) side by side."""
    r, cz, w = (hi[2] - lo[2]) / 2, (hi[2] + lo[2]) / 2, (hi[0] - lo[0]) / 3
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    out = []
    for k in range(3):
        cx = lo[0] + w * (k + 0.5)
        for y in (lo[1], hi[1]):
            out.append(np.c_[cx + r * np.cos(a), np.full(n, y), cz + r * np.sin(a)])
    return np.vstack(out)


def boxpts(lo, hi, n=5):
    g = [np.linspace(lo[k], hi[k], n) for k in range(3)]
    P = np.array(np.meshgrid(*g, indexing="ij")).reshape(3, -1).T
    on = ((P == lo) | (P == hi)).any(1)
    return P[on]


def check(p, q, st, G, legs, keep, bx):
    res = {}
    sl = q["SLACK"]
    # legs over the poses: coarse points (spacing ~1.5 mm) for the leg-leg check, fine (~0.75) near the body
    allw = [carry(lg["samp"], lg["g"]) for lg in legs]               # (poses, M, 3) per leg
    allc = [carry(lg["coarse"], lg["g"]) for lg in legs]
    cloud = np.vstack([W.reshape(-1, 3) for W in allc])
    ctree = cKDTree(cloud)
    out = {}
    for k, nm, V, F, cp, cf, kp in (
            ("body", "patas ↔ cuerpo", st["ball_v"], st["ball_f"], st["cpb"], st["cfb"],
             np.r_[keep["body"], np.ones(len(st["eyes_f"]), bool)]),
            ("base", "patas ↔ base", st["base_v"], st["base_f"], st["cpa"], st["cfa"], keep["base"])):
        ok = kp[cf]
        cp, cf = cp[ok], cf[ok]
        near = np.unique(cf[np.isfinite(ctree.query(cp, distance_upper_bound=6.0)[0])])
        fp, _ = dense(V, F[near], q["H_BODY"] * 1.5)
        ft = cKDTree(fp)
        g = np.inf
        for lg, W in zip(legs, allw):
            d = pdist(W.reshape(-1, 3), ft).reshape(W.shape[:2])
            if k == "base":                       # parts inside the pivot sit in the hollow base: keep its wall
                d = d - np.where(lg["samp"][:, 0] < -1.0, q["WALL_BASE"], 0.0)
            g = min(g, d.min())
        out[nm] = g - sl
    res.update(out)
    pairs = [(a, a + 1) for a in (0, 1, 2, 4, 5, 6)] + [(0, 4), (3, 7)]
    gl = np.inf
    for a, b in pairs:
        for k in range(allc[a].shape[0]):
            d = cKDTree(allc[b][k]).query(allc[a][k], distance_upper_bound=4.0)[0].min() - 1.0
            if d < 2.5:                                              # close: again with the fine points
                Wa, Wb = carry(legs[a]["samp"], legs[a]["g"]), carry(legs[b]["samp"], legs[b]["g"])
                d = cKDTree(Wb[k]).query(Wa[k], distance_upper_bound=4.0)[0].min() - sl
            gl = min(gl, d)
    res["pata ↔ pata"] = gl
    # inner arms (inside the pivot) against the boxes, not the crankshaft they ride on nor the gears
    gi = np.inf
    for lg, W in zip(legs, allw):
        inner = W[:, lg["samp"][:, 0] < -1.0]
        for kx, (lo, hi) in bx.items():
            if kx.startswith("cigüeñal") or kx == "engranajes":
                continue
            gi = min(gi, n0.pt_box(inner, lo, hi).min() - 0.5 * q["H_LEG"] * 0.5)
    res["brazos ↔ piezas"] = gi
    # boxes inside: N0's hull of body + base, minus the wall (dome above the deck, base wall below)
    allv = np.vstack([st["body_v"], st["base_v"]])
    h = ConvexHull(allv)
    hb = ConvexHull(st["base_v"])
    gin = np.inf
    for kx, (lo, hi) in bx.items():
        X = cellpts(lo, hi) if kx == "pilas" else boxpts(lo, hi)
        d_all = -(X @ h.equations[:, :3].T + h.equations[:, 3]).max(1)
        d_base = -(X @ hb.equations[:, :3].T + hb.equations[:, 3]).max(1)
        low = X[:, 2] < q["DECK"]
        m = np.where(low, np.minimum(d_all, d_base) - q["WALL_BASE"], d_all - q["WALL_DOME"])
        gin = min(gin, m.min())
    res["piezas dentro"] = gin
    names = [k for k in bx if not k.startswith("cigüeñal")]
    ga = np.inf
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {"motor", "eje"}:
                continue
            (l1, h1), (l2, h2) = bx[a], bx[b]
            ga = min(ga, np.max(np.maximum(l1 - h2, l2 - h1)))
    res["piezas ↔ piezas"] = ga
    # walking: ground = lowest point of each pose
    low = np.array([W[:, :, 2].min(1) for W in allw])                # (8, poses)
    ground = low.min(0)
    res["altura bajo la base"] = -ground.mean()
    res["cabeceo"] = np.ptp(ground)
    res["paso (alto)"] = np.ptp(low, 1).mean()
    kz = np.mean([carry(lg["K"][None], lg["g"])[:, 0, 2].mean() for lg in legs])
    res["rodilla − cúpula"] = kz - st["body_v"][:, 2].max()
    ext = np.vstack([W.reshape(-1, 3) for W in allw] + [st["body_v"], st["base_v"]])
    res["ancho × largo"] = np.ptp(ext[:, :2], 0)
    res["ancho × largo × alto"] = np.ptp(ext, 0)
    return res


def run(p=None, q=None):
    p, q = {**n0.P0, **P0_N1, **(p or {})}, dict(P1, **(q or {}))
    st, G, legs = build(p, q)
    keep, sizes = windows(p, q, legs, st)
    bx = n0.boxes(p, np.array([g["P"] * [g["sx"], 1, 1] for g in G]))
    lo, hi = bx["engranajes"]                                        # the strip ends 1 mm short each end (bowl)
    bx["engranajes"] = (lo + [0, 1.0, 0], hi - [0, 1.0, 0])
    res = check(p, q, st, G, legs, keep, bx)
    return dict(p=p, q=q, st=st, G=G, legs=legs, keep=keep, win=sizes, bx=bx, res=res)


def report(R):
    res, ok = R["res"], lambda v: "ok" if v >= 0 else "roza (dentro de 1 mm)" if v >= -1.0 else "CHOCA"
    out = []
    for k, v in res.items():
        if k.startswith("ancho"):
            out.append(f"  {k:22s} " + " × ".join(f"{x:.0f}" for x in v) + " mm")
        else:
            out.append(f"  {k:22s} {v:6.1f} mm" + ("  " + ok(v) if k in ("patas ↔ cuerpo", "patas ↔ base", "pata ↔ pata", "brazos ↔ piezas", "piezas dentro", "piezas ↔ piezas") else ""))
    w = R["win"]
    out.append("  ventana por pata (x,y,z, mm): " + "; ".join(f"{a:.0f}×{b:.0f}×{c:.0f}" for a, b, c in w[:4]))
    s = R["legs"][0]["stretch"]
    out.append("  estiramiento de la pata sobre su 60 %: " + ", ".join(f"{k} ×{v:.2f}" for k, v in s.items()))
    out.append("  triángulos: cuerpo %d, base %d, ojos %d, patas %d" % (len(R["st"]["body_f"]), len(R["st"]["base_f"]), len(R["st"]["eyes_f"]), sum(len(l["F"]) for l in R["legs"])))
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png"), ap.add_argument("--photo"), ap.add_argument("--pose", type=int, default=0)
    ap.add_argument("--lang", default="es", choices=("es", "en"))
    ap.add_argument("--set", nargs="*")
    a = ap.parse_args()
    ov = n0.parse_set(a.set)
    pp = {k: v for k, v in ov.items() if k in n0.P0}
    qq = {k: v for k, v in ov.items() if k in P1}
    t1 = time.time()
    R = run(pp, qq)
    t2 = time.time()
    print(report(R))
    print(f"  tiempos: carga {t1 - T0:.1f} s, maqueta + comprobación {t2 - t1:.1f} s", end="")
    if a.png:
        import n1_render
        n1_render.render(a.png, R, a.pose, a.photo, a.lang)
        print(f", dibujo {time.time() - t2:.1f} s", end="")
    print(f", total {time.time() - T0:.1f} s")
