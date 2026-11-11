#!/usr/bin/env python3
"""Collision check of the moving parts against base v1, its cap and the lifted body, over a full crank turn.

Places the legs, forks, crankshafts and idlers as ../drive/check.py does and reports every overlap with the base,
the cap or the body, and every gap under 1 mm. Fork against base is reported only for overlaps: the swivel screws'
holes are in both, so their nearest faces are 0.6 mm apart by design.

Usage:
    python3 check.py              # every 30°
    python3 check.py --step 15

Needs trimesh and manifold3d.
"""
import argparse
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = os.path.join(HERE, "..", "drive")
sys.path.insert(0, DRIVE)
import check as DC  # noqa: E402


def to_manifold(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", type=float, default=30)
    args = ap.parse_args()
    fixed = {n: trimesh.load(os.path.join(HERE, n + ".stl")) for n in ("base-v1", "cap", "front-block", "body-lifted")}
    fixed_mf = {n: to_manifold(m) for n, m in fixed.items()}
    near = {n: trimesh.proximity.ProximityQuery(m) for n, m in fixed.items()}
    cache, worst, gaps = {}, {}, {}
    for a in np.arange(0, 360, args.step):
        for n, f, M in DC.poses(np.radians(a)):
            if n == "spine":
                continue
            if f not in cache:
                cache[f] = trimesh.load(os.path.join(DRIVE, f + ".stl"))
            m = cache[f].copy()
            m.apply_transform(M)
            mm = to_manifold(m)
            for fn, fm in fixed.items():
                lo, hi = m.bounds
                if np.any(lo > fm.bounds[1] + 2) or np.any(fm.bounds[0] > hi + 2):
                    continue
                v = (mm ^ fixed_mf[fn]).volume()
                key = (n, fn)
                if v > 0.01:
                    if v > worst.get(key, (0, 0))[0]:
                        worst[key] = (v, a)
                elif not n.startswith("pivot"):
                    p = m.sample(1500)
                    p = p[np.all((p > fm.bounds[0] - 2) & (p < fm.bounds[1] + 2), axis=1)]
                    if len(p):
                        g = near[fn].on_surface(p)[1].min()
                        if g < gaps.get(key, (np.inf, 0))[0]:
                            gaps[key] = (g, a)
        print(f"{a:g}°", end=" ", flush=True)
    print()
    if not worst:
        print(f"no overlaps over a full turn (every {args.step:g}°)")
    for (n1, n2), (v, a) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
        print(f"{n1:14s} × {n2:12s} {v:8.2f} mm³ (worst at {a:g}°)")
    close = sorted((g, a, k) for k, (g, a) in gaps.items() if g < 1.0)
    print(f"{len(close)} pairs closer than 1 mm" + (":" if close else ""))
    for g, a, (n1, n2) in close:
        print(f"{n1:14s} × {n2:12s} gap {g:5.2f} mm (closest at {a:g}°)")


if __name__ == "__main__":
    main()
