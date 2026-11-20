#!/usr/bin/env python3
"""jenscolt's base without his inside: the bowl skin and rim, as the reference for converting the base.

His base is solid at the top and carries the posts and mounts of his own motor and lights; ours is hollow and
holds our mechanism (Morante, 2026-11-20: convert only the outer bowl). This writes spideybot_base_bowl.stl next to
it, a derived reference under the same licence (CC BY-NC-SA, LICENSE.txt), the way cad/mockup/n1.py emptied it:
the top deck and the inner blocks off, the largest connected piece kept, the inner static-leg tabs off, and
the loose slivers their cut leaves dropped.

    uv run python cad/carcass-jenscolt/derive_bowl.py
"""
import os

import numpy as np
import trimesh
from trimesh.proximity import signed_distance

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_Z = (61.9, 62.5)        # his flat top face (mm, his frame): opened, as ours is hollow
BLOCK = (60.0, 11.0, 60.0)   # z above, x between: his inner posts and mounts (hidden by the dome)
BOWL_C = (35.6, -7.6, 80.0)  # centre for the outward rays that find the inner tabs
TAB_DEPTH = 1.0              # an inner face this deep inside the hull is a tab, not skin
# Two zero-thickness fins inside the rear rim, what is left of his static-leg plugs (cad/base fixer probe,
# 2026-11-20): x, y, z boxes in his frame. Inside the bowl, which is ours, so not part of the reference.
FINS = [((63.5, 71.0), (23.0, 31.0), (57.5, 62.5)), ((-1.0, 5.0), (24.0, 30.0), (57.5, 62.5))]


def main():
    m = trimesh.load(os.path.join(HERE, "spideybot_base.stl"), process=False)
    V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
    T = V[F]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nz = n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-9)
    z, xc = T[:, :, 2].mean(1), T[:, :, 0].mean(1)
    deck = (abs(nz) > 0.9) & (z > DECK_Z[0]) & (z < DECK_Z[1])
    block = (z > BLOCK[0]) & (xc > BLOCK[1]) & (xc < BLOCK[2])
    M = trimesh.Trimesh(V, F[~(deck | block)], process=True)
    M = max(M.split(only_watertight=False), key=lambda c: len(c.faces))
    C = M.triangles_center
    d = C - np.array(BOWL_C)
    d /= np.linalg.norm(d, axis=1)[:, None]
    _, ri, _ = M.ray.intersects_location(C + d * 0.05, d)
    inner = np.bincount(ri, minlength=len(C)) >= 1
    tab = inner & (signed_distance(M.convex_hull, C) > TAB_DEPTH)
    out = trimesh.Trimesh(M.vertices, M.faces[~tab], process=True)
    out = max(out.split(only_watertight=False), key=lambda c: c.area)   # the tabs' cut leaves loose slivers: drop them
    C = out.triangles_center
    fin = np.zeros(len(C), bool)
    for (x0, x1), (y0, y1), (z0, z1) in FINS:
        fin |= (C[:, 0] > x0) & (C[:, 0] < x1) & (C[:, 1] > y0) & (C[:, 1] < y1) & (C[:, 2] > z0) & (C[:, 2] < z1)
    n = out.face_normals
    # keep the wall's own faces in those boxes: the outer skin faces point outward from the bowl's axis
    radial = C[:, :2] - np.array(BOWL_C[:2])
    radial /= np.linalg.norm(radial, axis=1)[:, None]
    fin &= np.abs((n[:, :2] * radial).sum(1)) < 0.5               # a fin runs radially: its normal is tangential
    out = trimesh.Trimesh(out.vertices, out.faces[~fin], process=True)
    path = os.path.join(HERE, "spideybot_base_bowl.stl")
    out.export(path)
    print(f"wrote {path}: {len(out.faces)} triangles, extents {np.round(out.extents, 1).tolist()}")


if __name__ == "__main__":
    main()
