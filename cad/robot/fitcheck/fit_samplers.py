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
