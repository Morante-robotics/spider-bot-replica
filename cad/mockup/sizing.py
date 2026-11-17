"""N0 sizing: smallest jenscolt scale whose body (convex hull of body + base, minus a wall) holds a fixed-height
gear layer, the cells, the motor and the switch. Convex inside test = half-spaces: every check is numpy, ms."""
import itertools, time
T = time.time()
import numpy as np, trimesh
from scipy.spatial import ConvexHull

J = "cad/carcass-jenscolt/spideybot_"
P = np.vstack([trimesh.load(J + n + ".stl").vertices for n in ("body", "base")])
P = P - [(P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2, P[:, 2].min()]
WALL, GAP, STEP = 1.6, 1.0, 1.0
GEAR_H = 12.0  # crankshafts + gears, module 0.6 (12 T ≈ Ø8.4) + walls: fixed, does not scale
PACKS = {"6×AG13 (3S2P, 4,5 V)": (19.2, 26.2, 14.6), "3×AG13 (4,5 V)": (19.2, 14.6, 14.6),
         "4×NiMH botón V80H (4,8 V)": (27.0, 19.0, 17.0), "3×AAAA (4,5 V)": (45.5, 27.0, 10.3)}
MOTORS = {"Ø6 planetario": (9, 9, 28), "N10": (15, 13, 30), "N20": (15, 13, 38)}
SWITCH = (14, 8, 8)


H0 = ConvexHull(P)
V0 = np.unique(np.round(P[H0.vertices] / 4) * 4, axis=0)                # hull vertices on a 4 mm grid: N0 detail
V0 = V0[ConvexHull(V0).vertices]
STEP = 2.0                                                             # N0: 5 mm tolerance, 2 mm voxels


def solve(s, comps):
    H = ConvexHull(V0 * s)
    n, d = H.equations[:, :3], H.equations[:, 3] + WALL
    lo, hi = (V0 * s).min(0), (V0 * s).max(0)
    ax = [np.arange(lo[i], hi[i] + STEP, STEP) for i in range(3)]
    G = np.stack(np.meshgrid(*ax, indexing="ij"), -1)
    occ = ((G.reshape(-1, 3) @ n.T + d) <= 0).all(1).reshape(G.shape[:3])   # voxel inside the wall
    taken = np.zeros_like(occ)

    def fit(dims, zmin):
        k = [int(np.ceil(x / STEP)) for x in dims]
        sh = [occ.shape[i] - k[i] for i in range(3)]
        if min(sh) <= 0:
            return None
        ok = np.ones(sh, bool)
        for c in itertools.product(*[(0, k[i]) for i in range(3)]):     # convex: the 8 corners decide
            ok &= occ[c[0]:c[0] + sh[0], c[1]:c[1] + sh[1], c[2]:c[2] + sh[2]]
        # no overlap with what is placed: integral image of «taken» over the box (+1 voxel gap)
        t = np.pad(taken, 1).cumsum(0).cumsum(1).cumsum(2)
        t = np.pad(t, ((1, 0), (1, 0), (1, 0)))
        K = [k[i] + 2 for i in range(3)]
        tot = np.zeros(sh)
        for c in itertools.product((0, 1), repeat=3):
            sl = tuple(slice(K[i] * c[i], K[i] * c[i] + sh[i]) for i in range(3))
            tot += (-1) ** (3 - sum(c)) * t[sl]
        ok &= tot == 0
        ok[:, :, : max(0, int(np.ceil((zmin - lo[2]) / STEP)))] = False
        idx = np.argwhere(ok)
        if not len(idx):
            return None
        return idx, k

    gx, gy = (hi[0] - lo[0]) * 0.7, 12.0          # gear strip along the body; the crankshafts are thin shafts across
    r = fit((gx, gy, GEAR_H), lo[2])
    if r is None:
        return None
    idx, k = r
    cx, cy = (occ.shape[0] - k[0]) / 2, (occ.shape[1] - k[1]) / 2
    idx = idx[(np.abs(idx[:, 0] - cx) <= 1) & (np.abs(idx[:, 1] - cy) <= 1)]
    if not len(idx):
        return None
    i = idx[idx[:, 2].argmin()]
    taken[i[0]:i[0] + k[0], i[1]:i[1] + k[1], i[2]:i[2] + k[2]] = True
    ztop = lo[2] + (i[2] + k[2]) * STEP
    boxes = [(lo + i * STEP, lo + (i + k) * STEP)]
    for dims in comps:
        best = None
        for dd in set(itertools.permutations(dims)):
            r = fit(dd, ztop)
            if r:
                j = r[0][r[0][:, 2].argmin()]
                if best is None or j[2] < best[0][2]:
                    best = (j, r[1])
        if best is None:
            return None
        j, k = best
        taken[j[0]:j[0] + k[0], j[1]:j[1] + k[1], j[2]:j[2] + k[2]] = True
        boxes.append((lo + j * STEP, lo + (j + np.array(k)) * STEP))
    return boxes


if __name__ == "__main__":
    out = {}
    for pk, pd in PACKS.items():
        for mo, md in MOTORS.items():
            for s in np.arange(0.40, 1.21, 0.05):
                if solve(s, [pd, md, SWITCH]):
                    out[(pk, mo)] = s
                    break
            s = out.get((pk, mo), np.nan)
            print(f"{pk:26s} + {mo:14s}: {s:4.0%}  ->  robot ≈ {224*s:3.0f} × {154*s:3.0f} × {118*s:3.0f} mm")
    print(f"total {time.time()-T:.1f} s")
