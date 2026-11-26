"""The fit check's environment: the shell cavity from the body/base build modules' own section functions (no mesh),
the legs' inner arms from cad/motion.py over 24 poses, and helpers to sample boxes/cylinders/capsules. Robot frame, S
(the robot's scale, read from cad/robot/spec.json). Point clouds are cached in .cache/, keyed by their inputs and the
modification time of the build modules they come from."""
import sys, os, math, json, numpy as np
from scipy.spatial import cKDTree
import fit_samplers as _FS
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..")); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/cad")
CACHE = os.path.join(HERE, ".cache"); os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
def stamp(*rel):
    """Newest modification time of these repo files, for cache keys: a cache older than its sources is not used."""
    return int(max(os.path.getmtime(os.path.join(ROOT, r)) for r in rel))
import motion
from cad import design, fits as F
BO, BA = design("body"), design("base")
S = float(json.load(open(os.path.join(HERE, "..", "spec.json")))["dims"]["S_start"]["value"])   # Morante 2026-11-21: «Prueba 0.70»
_LEN = ("r", "XC", "H", "DY", "knee_r", "knee_z", "foot_r", "foot_z", "up_arch", "blade_top", "blade_bow",
        "r_upper", "r_root", "r_blade", "r_inner")
K = S / 0.70    # printed layout numbers (check.py LAYOUT, drive, power, shells) were set at S 0.70: they grow with S
P = dict(motion.P0, S=S, **{k: motion.P0[k] * S / motion.P0["S"] for k in _LEN})   # every P0 length x S/0.60
BASE_WALL_R = max(F.WALL_MIN, BA.WALL * S)    # robot mm: fits.WALL_MIN. No 1.2 pads round the leg windows any more (2026-11-23): the windows are
                             # open-top LEG_OPEN, the leg is held by its pin, so they carry no load; 1.2 everywhere put the wall
                             # 0.14 from the front arms (decision 2: smooth front, 0.40 at 0.84)
BODY_WALL_J = BO.WALL   # spec body_wall 1.6 robot mm (Morante 2026-11-21)
def j2r(q): return motion.to_frame(q, P)
def r2j(q): return np.asarray(q, float) / S + motion.ORIGIN
# --- inner surface point clouds (jenscolt frame), then to robot frame
SCOOP_J = 0.0                 # Morante 2026-11-21: back scoop 1.2 robot mm further back
BACK_Y_J = BA.BACK_Y + SCOOP_J
A_L = BA.meridian(BA.X_W, BA.X_ZE, BA.X_H, BA.X_P, BA.Z_LEDGE); B_L = BA.meridian(BA.Y_W, BA.Y_ZE, BA.Y_H, BA.Y_P, BA.Z_LEDGE)
EAR = np.array(BA.RIM_EAR, float)
def band_top(x, y):
    """upper edge of the base's band (jenscolt): the ear polyline on the side walls (|x-CX| > EAR_DX), RIM_Z elsewhere."""
    e = np.interp(y, EAR[:, 0], EAR[:, 1], left=BA.RIM_Z, right=BA.RIM_Z)
    return np.where(np.abs(np.asarray(x) - BA.CX) > BA.EAR_DX, e, BA.RIM_Z)
def band_pts(d, nt=360, h=0.3):
    """band (ledge .. ear top) wall points grown by -0.5 d (inner, as base/build.py skin) or +LEDGE (outer, d=None),
    plus its top edge: what a part above the ear sees (air, visible)."""
    g = BA.LEDGE if d is None else -0.5 * d; t = np.linspace(0, 2 * np.pi, nt, endpoint=False); c, s = np.cos(t), np.sin(t)
    n = BA.N_TOP; x = BA.CX + (A_L + g) * np.sign(c) * np.abs(c) ** (2 / n); y = BA.CY + (B_L + g) * np.sign(s) * np.abs(s) ** (2 / n)
    top = band_top(x, y); out = []
    for z in np.arange(BA.Z_LEDGE, EAR[:, 1].max() + 0.01, h):
        k = z <= top; out.append(np.c_[x[k], y[k], np.full(k.sum(), z)])
    out.append(np.c_[x, y, top])
    if d is not None:                               # top edge across the gap to the body's skirt (a horizontal fringe 4 mm wide)
        for f in np.linspace(0.85, 1.0, 6):
            out.append(np.c_[BA.CX + (x - BA.CX) * f, BA.CY + (y - BA.CY) * f, top])
    return np.vstack(out)
def body_inner_pts(nt=180, w=None):
    rows = np.array(BO.inner_rows(BODY_WALL_J if w is None else w)); zs = np.arange(rows[0, 0], rows[-1, 0], 0.4)
    R = np.array([np.interp(zs, rows[:, 0], rows[:, k]) for k in range(1, 6)]).T
    t = np.linspace(0, 2 * np.pi, nt, endpoint=False); c, s = np.cos(t), np.sin(t); out = []
    for z, (a, bf, bb, nf, nb) in zip(zs, R):
        b = np.where(s > 0, bb, bf); e = np.where(s > 0, nb, nf)
        out.append(np.c_[BO.CX + a * np.sign(c) * np.abs(c) ** (2 / e), b * np.sign(s) * np.abs(s) ** (2 / e), np.full(nt, z)])
    top = rows[-1]; # roof cap: fill the last section
    for f in np.linspace(0, 1, 15):
        a, bf, bb, nf, nb = top[1:] * np.array([f, f, f, 1, 1]); b = np.where(s > 0, bb, bf); e = np.where(s > 0, nb, nf)
        out.append(np.c_[BO.CX + a * np.sign(c) * np.abs(c) ** (2 / e), b * np.sign(s) * np.abs(s) ** (2 / e), np.full(nt, top[0])])
    return np.vstack(out), (zs, R)
def base_hw(z, d):
    return (BA.meridian(BA.X_W - d, BA.X_ZE, BA.X_H - d, BA.X_P, z), BA.meridian(BA.Y_W - d, BA.Y_ZE, BA.Y_H - d, BA.Y_P, z), BA.plan_n(z))
def base_inner_pts(nt=180):
    d = BASE_WALL_R / S; zs = np.arange(BA.Z_FOOT + d, BA.Z_LEDGE, 0.3); t = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    c, s = np.cos(t), np.sin(t); out = []
    for z in zs:
        a, b, n = base_hw(z, d)
        out.append(np.c_[BA.CX + a * np.sign(c) * np.abs(c) ** (2 / n), BA.CY + b * np.sign(s) * np.abs(s) ** (2 / n), np.full(nt, z)])
    for f in np.linspace(0, 1, 25):                # floor
        a, b, n = base_hw(zs[0] + 0.01, d); a, b = a * f, b * f
        out.append(np.c_[BA.CX + a * np.sign(c) * np.abs(c) ** (2 / n), BA.CY + b * np.sign(s) * np.abs(s) ** (2 / n), np.full(nt, zs[0])])
    t2 = np.linspace(np.pi / 2 - 0.6, np.pi / 2 + 0.6, 300)          # back sheet (inner face of the scoop's wall)
    Rb = BA.BACK_R + d
    for z in zs:
        out.append(np.c_[BA.CX + Rb * np.cos(t2), BACK_Y_J - Rb * np.sin(t2), np.full(len(t2), z)])
    out.append(band_pts(d))
    return np.vstack(out)
_CK = os.path.join(CACHE, f"env_{stamp('cad/body/build.py', 'cad/base/build.py', 'cad/motion.py', 'cad/fits.py', 'cad/robot/fitcheck/fit_env.py')}_{S}_{BASE_WALL_R}_{BODY_WALL_J}_{SCOOP_J:.4f}.npz")
if os.path.exists(_CK):
    _z = np.load(_CK); BODY_PTS, BODY_ROWS, BASE_PTS = _z["b"], (_z["zs"], _z["R"]), _z["a"]
else:
    BODY_PTS, BODY_ROWS = body_inner_pts(); BASE_PTS = base_inner_pts()
    _ob = body_inner_pts(w=0.3)[0]; BASE_PTS = np.vstack([BASE_PTS, _ob[_ob[:, 2] < EAR[:, 1].max() + 0.5]])  # body skirt outside
    np.savez(_CK, b=BODY_PTS, zs=BODY_ROWS[0], R=BODY_ROWS[1], a=BASE_PTS)
WALL_PTS = np.vstack([j2r(BODY_PTS), j2r(BASE_PTS)])
WALL_T = cKDTree(WALL_PTS)
_OR = np.array(BO.inner_rows(0.3))
def in_body_outer(J):
    x, y, z = J.T; a, bf, bb, nf, nb = [np.interp(z, _OR[:, 0], _OR[:, k]) for k in range(1, 6)]
    b, e = np.where(y > 0, bb, bf), np.where(y > 0, nb, nf)
    return (z >= BO.Z_RIM) & (z <= _OR[-1, 0]) & ((np.abs(x - BO.CX) / a) ** e + (np.abs(y) / b) ** e < 1)
_ZG = None
def inside(q):
    """robot points inside the cavity (base inner below the ledge minus the back scoop, body inner above the rim)."""
    J = r2j(q); x, y, z = J.T; zs, R = BODY_ROWS; d = BASE_WALL_R / S
    a, bf, bb, nf, nb = [np.interp(z, zs, R[:, k]) for k in range(5)]
    b, e = np.where(y > 0, bb, bf), np.where(y > 0, nb, nf)
    ok = (z >= zs[0]) & (z <= zs[-1]) & ((np.abs(x - BO.CX) / a) ** e + (np.abs(y) / b) ** e < 1)
    global _ZG
    if _ZG is None: _zg = np.linspace(BA.Z_FOOT + d, BA.Z_LEDGE, 400); _ZG = (_zg, np.array([base_hw(zz, d) for zz in _zg]))
    zg, HW = _ZG; Rb = BA.BACK_R + d
    zc = np.clip(z, BA.Z_FOOT + d, BA.Z_LEDGE); A, B, N = [np.interp(zc, zg, HW[:, k]) for k in range(3)]; A = np.maximum(A, 1e-6); B = np.maximum(B, 1e-6)
    okb = (z >= BA.Z_FOOT + d) & (z <= BA.Z_LEDGE) & ((np.abs(x - BA.CX) / A) ** N + (np.abs(y - BA.CY) / B) ** N < 1)
    okb &= np.hypot(x - BA.CX, y - BACK_Y_J) > Rb
    # upper band: inside the band's inner face, from the ledge up to the ear top (side walls) or RIM_Z, and outside the
    # body's outer skin (the gap between the body's skirt and the ears; the body's own inside is `ok`)
    n = BA.N_TOP; okc = (z >= BA.Z_LEDGE) & (z <= band_top(x, y)) & (
        (np.abs(x - BA.CX) / (A_L - 0.5 * d)) ** n + (np.abs(y - BA.CY) / (B_L - 0.5 * d)) ** n < 1)
    okc &= np.hypot(x - BA.CX, y - BACK_Y_J) > Rb
    okc &= ~in_body_outer(J)
    return ok | okb | okc
def wall_gap(q):
    """least gap of surface samples q to the cavity wall (negative = outside)."""
    d, _ = WALL_T.query(q); ins = inside(q); g = np.where(ins, d, -d); k = int(np.argmin(g)); return g[k], q[k]
# --- samplers
def box(lo, hi, h=0.5):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float); n = np.maximum(2, np.ceil((hi - lo) / h).astype(int) + 1)
    ax = [np.linspace(lo[k], hi[k], n[k]) for k in range(3)]; pts = []
    for k in range(3):
        o = [i for i in range(3) if i != k]; A, B = np.meshgrid(ax[o[0]], ax[o[1]], indexing="ij")
        for v in (lo[k], hi[k]):
            P_ = np.zeros((A.size, 3)); P_[:, k] = v; P_[:, o[0]] = A.ravel(); P_[:, o[1]] = B.ravel(); pts.append(P_)
    q = np.vstack(pts); _FS.log_prim("box", q, lo=lo, hi=hi); return q
def cyl_x(y, z, r, x0, x1, h=0.5):
    n = max(12, int(2 * np.pi * r / h)); t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xs = np.linspace(x0, x1, max(2, int((x1 - x0) / h) + 1)); pts = [np.c_[np.repeat(xs, n), np.tile(y + r * np.cos(t), len(xs)), np.tile(z + r * np.sin(t), len(xs))]]
    for x in (x0, x1):
        for rr in np.linspace(0, r, max(2, int(r / h) + 1)):
            pts.append(np.c_[np.full(n, x), y + rr * np.cos(t), z + rr * np.sin(t)])
    q = np.vstack(pts); _FS.log_prim("cyl", q, a=np.array([x0, y, z], float), b=np.array([x1, y, z], float), r=r); return q
def cyl_z(x, y, r, z0, z1, h=0.5):
    q = cyl_x(y, x, r, z0, z1, h); _FS.PRIMS.pop(); q = np.c_[q[:, 2], q[:, 1], q[:, 0]]
    _FS.log_prim("cyl", q, a=np.array([x, y, z0], float), b=np.array([x, y, z1], float), r=r); return q
def capsule(a, b, r, h=0.5):
    a, b = np.asarray(a, float), np.asarray(b, float); L = np.linalg.norm(b - a); n = max(2, int(L / h) + 1)
    c = a + np.linspace(0, 1, n)[:, None] * (b - a); return c, r     # centre-line, radius
def gap_pts(q1, q2):
    return cKDTree(q1).query(q2)[0].min()
# --- legs: inner arms over 24 poses (motion.legs), the crank pins A and pivots
LEG_PTS, LEG_RAD, LEG_NI, PIV, A_ALL = motion.legs(P)
BAND_OUT = j2r(band_pts(None))
def arm_centres(k_leg, pose, end_r):
    """centre-line samples and radius of the inner arm (from 2 past the pin to the pivot), designed end tube radius."""
    c = LEG_PTS[k_leg, pose, :LEG_NI + 1]
    dense = np.vstack([np.linspace(c[i], c[i + 1], 6) for i in range(len(c) - 1)])
    return dense, end_r
# motion.py's blade radii 2.0 / 2.5 are unscaled there (looks only): scaled x S/0.60 here, motion.py untouched
_kb = S / motion.P0["S"]; _rb = LEG_RAD[LEG_NI + 10:].copy(); _f = (_rb - 2.0) / (P["r_blade"] - 2.0)
_rb2 = 2.0 * _kb + (P["r_blade"] - 2.0 * _kb) * _f; _rb2[0] = max(_rb2[0], 2.5 * _kb)
LEG_RAD = LEG_RAD.copy(); LEG_RAD[LEG_NI + 10:] = _rb2
