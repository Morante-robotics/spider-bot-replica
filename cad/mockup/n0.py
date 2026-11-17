"""N0 mock-up of the looks Spider-Bot: the whole robot in simple shapes, checked and drawn in seconds.

Body   jenscolt's body and base, scaled about the base's bottom centre: their convex hulls (4 mm grid) for the
       picture and the inside test, the distance to their real surface (2 mm voxels, cached) for the legs.
Legs   8 rigid legs, each a chain of spheres with radii (a swept tube): inner arm from the crank pin through the
       pivot P in the base rim, upper leg P → knee K (arched up), blade from just above K down to the foot F
       (bowed outward). Lengths and thickness from jenscolt's spideybot_L_leg1/2.stl at the same scale.
Motion the toy leg of sim/toy_leg_3d.py, "rows" axle, slide at the crank: four lateral crankshafts, one per pair
       of notches; the leg turns about P (gimbal, sideways axis kept level) as its inner end follows the crank pin.
       Unlike the simulator, the leg may bend up at P: the leg's shape is given in the neutral pose (crank level)
       and carried rigidly in the leg's frame (u = P − A, side, up).
Inside boxes: gear strip (module ≈ 0.6) and crankshafts, N10 motor + shaft, 6 × AG13 as 2S3P (three stacks of
       two Ø11.6 cells), slide switch.
Checks (numpy only; conservative at N0, 5 mm tolerance): body ↔ outer legs, neighbouring legs, inner arms ↔
       boxes, boxes inside the body wall and apart, over 24 crank poses; ground = lowest foot of each pose.

Frame: mm, z up, forward = −Y, +X = robot's right (cad/README.md); origin on the body axis, z = 0 at the base's
bottom. Usage (repo root):
    uv run python cad/mockup/n0.py                          # checks + timing
    uv run python cad/mockup/n0.py --png out.png [--lang en] [--photo toy.jpg] [--set knee_z=44 foot_r=60 ...]
Measured on a 2-core Mac: checks 0.5 s, 4-view render 1.3 s, whole run ≈ 2 s (first run ≈ 10 s more, building the
body cache). The photo of the toy is private: a picture with --photo never goes into the repo.
"""
import argparse, os, sys, time

T0 = time.time()
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "sim"))
import toy_leg_3d as TL  # noqa: E402  (notches, centre, gait groups: one source)

J = os.path.join(ROOT, "cad", "carcass-jenscolt", "spideybot_")
K120 = 1 / 1.2                                         # sim coordinates are jenscolt at 120 %
POSES = 24

# Every number in mm at the robot's scale; the leg sizes are jenscolt's × S unless noted.
P0 = dict(
    S=0.60,          # robot scale vs jenscolt (cad/mockup/sizing.py: smallest that holds N10 + 6 × AG13)
    WALL=1.6,        # body wall
    # crank (toy_leg_3d_rows_cad.json[0] × 0.5 = 60 % of jenscolt, rounded)
    r=2.0,           # crank throw
    XC=6.0,          # crank pins this far either side of the body axis
    H=-3.0,          # crankshafts this far below the notches (the base's bowl is narrow below)
    DY=-2.4,         # crankshafts shifted along Y from their notch pair
    # leg shape in the neutral pose (crank level), measured from the body axis in the notch's direction
    angles=(-45, -15, 15, 45),   # right legs front to rear: direction from the body axis, degrees from +X
    knee_r=44.0,     # knee: horizontal distance from the body axis (jenscolt ≈ 63 × S = 38)
    knee_z=46.0,     # knee: height above the base's bottom (dome top ≈ 49)
    foot_r=68.0,     # foot: horizontal distance from the body axis (jenscolt ≈ 83 × S = 50)
    foot_z=-8.0,     # foot: height above the base's bottom (< 0: the body stands clear of the ground)
    elbow=1.0,       # upper leg: 0 = straight from the pivot to the knee, 1 = out level first, then up
    up_arch=0.0,     # upper leg's bend raised by this much
    blade_top=6.0,   # blade goes on past the knee by this much (jenscolt ≈ 10 × S)
    blade_bow=4.0,   # blade bows outward by this much at its middle
    r_upper=4.0,     # upper leg radius at the knee (jenscolt leg2 ≈ Ø14 shaft × S)
    r_root=3.0,      # upper leg radius at the pivot (the middle notches are only ≈ 8 mm apart at 60 %)
    r_blade=6.0,     # blade radius at its thickest (jenscolt leg1 ≈ 23 × 10, a capsule of the same bulk)
    r_inner=1.5,     # inner arm radius
    # inside: (x, y, z) of each box's centre and its size, with the source of the size
    gear=(0, 0, 0, 7, 0, 9),           # gear strip along Y over the 4 crankshafts; y-length set from the notches
    motor=(0, 4, 21, 10, 24, 12),      # N10 ≈ 12 × 10 × 24 mm body, lying along Y (hardware.md)
    shaft=(0, -13, 21, 3, 10, 3),      # its 3 mm D-shaft, 10 mm
    cells=(0, 2, 35, 36, 12.6, 13),    # 6 × AG13 as three stacks of two (Ø11.6 × 5.4 each) side by side
    switch=(0, 24, 24, 12, 6, 6),      # SS12D00, at the rear under the dome; ≈ 12 × 6 × 6 (hardware.md)
)
COLLAR = 8.0                           # leg root inside the shell's window, not checked against the body
GAP_MIN = 1.0                          # N0 pass: everything at least this far apart (5 mm tolerance level)


# ---------------------------------------------------------------- body
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "n0_body.npz")
PITCH = 2.0                            # voxel size of the body's distance field, at jenscolt's scale


def body_cache():
    """jenscolt's body and base at 100 %, once (≈ 10 s, then read from .cache/): hull points of each on a 4 mm
    grid (for the picture and the inside test) and the distance to their surface on a 2 mm voxel grid (for the
    legs: the dome overhangs the base, so a convex hull would wrongly fill the room the legs come out under)."""
    if os.path.exists(CACHE):
        return dict(np.load(CACHE))
    import trimesh
    from scipy import ndimage
    from scipy.spatial import ConvexHull
    out = {}
    ms = {n: trimesh.load(J + n + ".stl") for n in ("body", "base")}
    for n, m in ms.items():
        q = np.unique(np.round(m.vertices / 4) * 4, axis=0)
        out[n] = q[ConvexHull(q).vertices]
    v = trimesh.util.concatenate(list(ms.values())).voxelized(PITCH)
    out["dist"] = (ndimage.distance_transform_edt(~v.matrix) * PITCH).astype(np.float32)
    out["origin"] = v.transform[:3, 3]
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez_compressed(CACHE, **out)
    return out


def body(p):
    from scipy.spatial import ConvexHull
    C = body_cache()
    c = np.array([TL.CENTER[0] * K120, TL.CENTER[1] * K120, TL.BASE_BOTTOM * K120])
    B = dict(c=c, dist=C["dist"], origin=C["origin"])
    for n in ("body", "base"):
        V = (C[n] - c) * p["S"]
        B[n] = (V, ConvexHull(V).simplices)
    pts = np.vstack([B["body"][0], B["base"][0]])
    h = ConvexHull(pts)
    B.update(V=pts, n=h.equations[:, :3], d=h.equations[:, 3])
    return B


def surface_gap(X, B, p):
    """Distance (mm, at the robot's scale) from points X (..., 3) to the body's surface; conservative by half a
    voxel's diagonal. Points off the grid get their distance to the grid added."""
    q = (X / p["S"] + B["c"] - B["origin"]) / PITCH
    sh = np.array(B["dist"].shape)
    i = np.clip(np.rint(q), 0, sh - 1).astype(int)
    off = np.linalg.norm(q - i, axis=-1) * PITCH * (np.abs(q - i).max(-1) > 0.5)
    return (B["dist"][i[..., 0], i[..., 1], i[..., 2]] + off - 0.87 * PITCH) * p["S"]


_BODY = {}


def body_cached(p):
    if p["S"] not in _BODY:
        _BODY[p["S"]] = body(p)
    return _BODY[p["S"]]


def to_frame(xyz, B, p):
    return (np.asarray(xyz, float) - B["c"]) * p["S"]


# ---------------------------------------------------------------- legs
def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def frame(u):
    """Leg frame for inner-arm directions u (N, 3): u, side (level), up."""
    side = unit(np.cross(np.array([0, 0, 1.0]), u))
    up = np.cross(side, u)
    return np.stack([u, side, up], -2)                 # (N, 3, 3), rows = axes


def bezier(a, c, b, n):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b


def leg_shape(P, A0, ang, p, n=10):
    """Points (M, 3) and radii (M,) of one right leg in the neutral pose; A0 = crank pin at the level crank.
    Returns also the slice of the outer leg (beyond the body) and of the inner arm."""
    rd = np.array([np.cos(ang), np.sin(ang), 0])
    K = np.array([p["knee_r"] * rd[0], p["knee_r"] * rd[1], p["knee_z"]])
    F = np.array([p["foot_r"] * rd[0], p["foot_r"] * rd[1], p["foot_z"]])
    inner = np.linspace(A0 - 2 * unit(P - A0), P, 6)[:-1]             # inner arm, a little past the pin
    e = p["elbow"]                                                    # 0: straight up to the knee, 1: out, then up
    C = np.r_[P[:2] + e * (K[:2] - P[:2]), P[2] + (1 - e) * (K[2] - P[2]) + p["up_arch"]]
    upper = bezier(P, C, K, n)
    kd = unit(K - F)
    top = K + p["blade_top"] * kd
    bmid = (top + F) / 2 + p["blade_bow"] * rd
    blade = bezier(top, 2 * bmid - (top + F) / 2, F, n + 4)
    t = np.linspace(0, 1, n + 4)
    rb = 2.0 + (p["r_blade"] - 2.0) * np.sin(np.pi * np.clip(t * 1.25, 0, 1)) ** 0.7
    rb[0] = max(rb[0], 2.5)
    pts = np.vstack([inner, upper, blade])
    rad = np.concatenate([np.full(len(inner), p["r_inner"]),
                          np.linspace(p["r_root"], p["r_upper"], n), rb])
    return pts, rad, len(inner)


def legs(p, B, poses=POSES):
    """Leg tubes over the crank turn: pts (8, poses, M, 3), radii (8, M), n_inner, pivots, crank pins."""
    th = np.linspace(0, 2 * np.pi, poses, endpoint=False)
    allp, A_all, piv = [], [], []
    for side, sx in (("R", 1), ("L", -1)):
        for i, (x, y) in enumerate(TL.NOTCHES_RIGHT):
            P = to_frame((x * K120, y * K120, TL.NOTCH_Z * K120), B, p)
            O = np.array([p["XC"], P[1] + p["DY"], P[2] + p["H"]])
            ph = np.pi * TL.GROUP[side][i]
            A = O + p["r"] * (np.cos(th + ph)[:, None] * [0, -1, 0] + np.sin(th + ph)[:, None] * [0, 0, 1])
            A0 = O + p["r"] * np.array([0, -1, 0])                     # crank level: the neutral pose
            ang = np.radians(p["angles"][i])
            pts, rad, ni = leg_shape(P, A0, ang, p)
            R0 = frame(unit(P - A0)[None])[0]
            loc = (pts - P) @ R0.T                                     # shape in the neutral leg frame
            R = frame(unit(P - A))                                     # (poses, 3, 3)
            W = P + np.einsum("mk,nkj->nmj", loc, R)
            Aw = A
            if sx < 0:
                W = W * [-1, 1, 1]
                Aw = A * [-1, 1, 1]
                P = P * [-1, 1, 1]
            allp.append(W)
            A_all.append(Aw)
            piv.append(P)
    return np.array(allp), rad, ni, np.array(piv), np.array(A_all)


# ---------------------------------------------------------------- boxes
def boxes(p, piv):
    ys = piv[:4, 1]
    g = list(p["gear"])
    zc = piv[0, 2] + p["H"]
    g[1], g[4], g[2] = (ys.min() + ys.max()) / 2 + p["DY"], ys.max() - ys.min() + 9, zc  # gear Ø ≈ 7 + walls
    out = {"engranajes": g}
    for k, y in enumerate(ys):                                        # crankshafts with their throws
        out[f"cigüeñal {k + 1}"] = (0, y + p["DY"], zc, 2 * (p["XC"] + 2), 2 * (p["r"] + 1.5), 2 * (p["r"] + 1.5))
    out.update(motor=p["motor"], eje=p["shaft"], pilas=p["cells"], interruptor=p["switch"])
    return {k: (np.array(v[:3], float) - np.array(v[3:]) / 2, np.array(v[:3], float) + np.array(v[3:]) / 2)
            for k, v in out.items()}


def corners(lo, hi):
    return np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])


def pt_box(X, lo, hi):
    return np.linalg.norm(np.maximum(np.maximum(lo - X, X - hi), 0), axis=-1)


# ---------------------------------------------------------------- checks
def check(p, B, L, rad, ni, piv, bx):
    res = {}
    # outer legs ↔ body: distance to the real body + base surface (voxel field, conservative)
    # (not within COLLAR of the pivot: the window the shell leaves for the leg, sized by its swing)
    outer = L[:, :, ni:]
    far = np.linalg.norm(outer - piv[:, None, None], axis=-1) > COLLAR
    sd = surface_gap(outer, B, p) - rad[ni:]
    res["patas ↔ cuerpo"] = sd[far].min()
    k = np.argmax(far[0, 0])                                          # the first point past the collar
    res["ventana (oscilación)"] = max(np.linalg.norm(np.ptp(outer[j, :, k], 0)) for j in range(8)) + 2 * rad[ni + k]
    # neighbouring legs on one side, and the two front / rear legs across
    pairs = [(a, a + 1) for a in (0, 1, 2, 4, 5, 6)] + [(0, 4), (3, 7)]
    g = np.inf
    for a, b in pairs:
        Xa, Xb = L[a][:, ni:], L[b][:, ni:]
        d = np.linalg.norm(Xa[:, :, None] - Xb[:, None], axis=-1) - rad[ni:][:, None] - rad[ni:][None]
        g = min(g, d.min())
    res["pata ↔ pata"] = g
    # inner arms ↔ boxes (not the crankshaft each arm rides on)
    inner = L[:, :, :ni]
    gi = np.inf
    for k, (lo, hi) in bx.items():
        if k.startswith("cigüeñal") or k == "engranajes":
            continue
        gi = min(gi, (pt_box(inner, lo, hi) - p["r_inner"]).min())
    res["brazos ↔ piezas"] = gi
    # boxes inside the wall and apart
    inside = min((-(corners(lo, hi) @ B["n"].T + B["d"]).max() - p["WALL"]) for lo, hi in bx.values())
    res["piezas dentro"] = inside
    names = [k for k in bx if not k.startswith("cigüeñal")]
    ga = np.inf
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {"motor", "eje"}:
                continue
            (l1, h1), (l2, h2) = bx[a], bx[b]
            ga = min(ga, np.max(np.maximum(l1 - h2, l2 - h1)))
    res["piezas ↔ piezas"] = ga
    # walking: the ground is the lowest foot of each pose
    feet = L[:, :, -1, 2] - rad[-1]
    ground = feet.min(0)
    res["altura bajo la base"] = -ground.mean()
    res["cabeceo"] = np.ptp(ground)
    res["paso (alto)"] = np.ptp(feet, 1).mean()
    kz = L[:, :, ni + 9, 2].mean()
    res["rodilla − cúpula"] = kz - B["body"][0][:, 2].max()
    span = np.ptp(L[:, 0, :, :2].reshape(-1, 2), 0) + 2 * rad.max()
    res["ancho × largo"] = span
    return res


def run(p):
    B = body_cached(p)
    L, rad, ni, piv, A = legs(p, B)
    bx = boxes(p, piv)
    return B, L, rad, ni, piv, bx, check(p, B, L, rad, ni, piv, bx)


def report(res):
    lines = []
    for k, v in res.items():
        if k == "ancho × largo":
            lines.append(f"  {k:22s} {v[0]:5.0f} × {v[1]:3.0f} mm")
        else:
            flag = ""
            if k in ("patas ↔ cuerpo", "pata ↔ pata", "brazos ↔ piezas", "piezas dentro", "piezas ↔ piezas"):
                flag = "  ok" if v >= GAP_MIN else "  roza (dentro de los 5 mm de N0)" if v >= -2 else "  CHOCA"
            lines.append(f"  {k:22s} {v:6.1f} mm{flag}")
    return "\n".join(lines)


def parse_set(items):
    out = {}
    for it in items or []:
        k, v = it.split("=")
        out[k] = tuple(float(x) for x in v.split(",")) if "," in v else float(v)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png")
    ap.add_argument("--photo")
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--pose", type=int, default=0)
    ap.add_argument("--lang", default="es", choices=("es", "en"))
    a = ap.parse_args()
    p = dict(P0, **parse_set(a.set))
    t1 = time.time()
    B, L, rad, ni, piv, bx, res = run(p)
    t2 = time.time()
    print(report(res))
    print(f"  tiempos: carga {t1 - T0:.1f} s, maqueta + comprobación {t2 - t1:.2f} s", end="")
    if a.png:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import n0_render
        n0_render.render(a.png, p, B, L, rad, ni, bx, a.pose, a.photo, a.lang)
        print(f", dibujo {time.time() - t2:.1f} s", end="")
    print(f", total {time.time() - T0:.1f} s")
