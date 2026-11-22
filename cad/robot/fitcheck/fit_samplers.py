"""Samplers along any axis, shared by check.py."""
import numpy as np
def cyl_ax(a, b, r, h=0.5):
    a, b = np.asarray(a, float), np.asarray(b, float); u = (b - a) / np.linalg.norm(b - a)
    ref = [0, 0, 1.0] if abs(u[2]) < 0.9 else [1.0, 0, 0]
    v = np.cross(u, ref); v /= np.linalg.norm(v); w = np.cross(u, v); n = max(12, int(2 * np.pi * r / h))
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); L_ = np.linalg.norm(b - a); s_ = np.linspace(0, L_, max(2, int(L_ / h) + 1))
    ring = r * (np.cos(t)[:, None] * v + np.sin(t)[:, None] * w); pts = [(a + s_[:, None, None] * u + ring[None]).reshape(-1, 3)]
    for e in (a, b):
        for rr in np.linspace(0, r, 4): pts.append(e + rr / max(r, 1e-9) * ring)
    return np.vstack(pts)
def swept_x(y, z, rr, r0, x0, x1, h=0.5):
    """a disc of radius r0 at distance rr from axis (y, z) along x, swept over a full turn: annulus rr-r0 .. rr+r0."""
    out = []
    for R in (max(rr - r0, 0), rr + r0):
        n = max(12, int(2 * np.pi * max(R, .5) / h)); t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        xs = np.linspace(x0, x1, max(2, int((x1 - x0) / h) + 1))
        out.append(np.c_[np.repeat(xs, n), np.tile(y + R * np.cos(t), len(xs)), np.tile(z + R * np.sin(t), len(xs))])
    return np.vstack(out)


# ---------------- solids behind the samples: a surface sample cloud cannot tell «touching» from «one part inside the
# other» (the holder screw's head sat 1.25 inside an AG13 cell and read as a 0.15 gap, 2026-11-22). Every box and
# cylinder sampler logs its primitive here; solids_of() finds the primitives a part's cloud is made of, and
# inside_depth() says how deep other points sit inside them (> 0: inside).
PRIMS = []
def log_prim(kind, pts, **kw):
    if len(pts): PRIMS.append(dict(kind=kind, keys=pts[[0, len(pts) // 2, -1]].copy(), **kw))
def solids_of(cloud, tree=None):
    """the logged primitives whose sample points are all in this cloud (checked on 3 of their points)"""
    from scipy.spatial import cKDTree
    t = tree if tree is not None else cKDTree(cloud); lo, hi = cloud.min(0) - 1e-6, cloud.max(0) + 1e-6
    out = []
    for p in PRIMS:
        k = p["keys"]
        if np.all((k >= lo) & (k <= hi)) and t.query(k)[0].max() < 1e-7: out.append(p)
    return out
EXTRA_SOLIDS = {}                                    # printed parts' solids a sample cloud cannot give (a box cut by a slot): part -> [prim]
def add_solid(part, lo, hi):
    EXTRA_SOLIDS.setdefault(part, []).append(dict(kind="box", lo=np.asarray(lo, float), hi=np.asarray(hi, float)))
def inside_depth(q, prims):
    """depth of each point of q inside the union of these primitives (0 outside); only the points in a primitive's bbox are tested"""
    q = np.asarray(q, float); d = np.zeros(len(q))
    for p in prims:
        if p["kind"] == "box":
            lo, hi = p["lo"], p["hi"]; m = np.all((q > lo) & (q < hi), axis=1)
            if m.any(): d[m] = np.maximum(d[m], np.minimum(q[m] - lo, hi - q[m]).min(1))
        else:
            a, b, r = np.asarray(p["a"], float), np.asarray(p["b"], float), p["r"]; L = np.linalg.norm(b - a); u = (b - a) / L
            m = np.all((q > np.minimum(a, b) - r) & (q < np.maximum(a, b) + r), axis=1)
            if not m.any(): continue
            qm = q[m]; t = (qm - a) @ u; rad = np.linalg.norm(qm - a - t[:, None] * u, axis=1); e = np.minimum(np.minimum(t, L - t), r - rad)
            d[m] = np.maximum(d[m], np.maximum(e, 0))
    return d
_cyl_ax0 = cyl_ax
def cyl_ax(a, b, r, h=0.5):
    q = _cyl_ax0(a, b, r, h); log_prim("cyl", q, a=np.asarray(a, float), b=np.asarray(b, float), r=r); return q
