#!/usr/bin/env python3
"""Repair STL meshes so they are closed and manifold (watertight) without changing their shape, optionally scaling them.

Steps for each file:
  1. merge vertices closer than 0.1 µm (tiny gaps between triangles that should touch);
  2. drop degenerate (zero-area) triangles;
  3. drop triangles that appear twice or more (zero-thickness walls inside the part);
  4. if edges are still shared by more than two triangles (two surfaces "pinched" together along an edge, or
     separate shells touching), split the vertices there (PyMeshLab) and move each copy 0.01 mm into its own side,
     so the surfaces no longer touch;
  5. close any small holes left;
  6. scale about the origin (assembled parts stay assembled) and write a binary STL.
The result is checked after writing it and reading it back, as a slicer would: watertight or not, and the largest
distance between the original and the repaired surface. MeshFix-style rebuilding is not used: on this model it
removed a 1.5 mm relief from a leg.

Usage:
    python3 repair_stl.py OUT_DIR part1.stl part2.stl ... [--scale 1.2]

Needs numpy, trimesh, pymeshlab, scipy (pip install numpy trimesh pymeshlab scipy networkx rtree).
"""
import argparse
import os

import numpy as np
import pymeshlab
import trimesh

NUDGE = 0.01  # mm


def edge_report(m):
    _, counts = np.unique(m.edges_sorted, axis=0, return_counts=True)
    return int((counts == 1).sum()), int((counts > 2).sum())


def drop_duplicate_faces(m):
    key = np.sort(m.faces, axis=1)
    _, first, count = np.unique(key, axis=0, return_index=True, return_counts=True)
    keep = np.zeros(len(m.faces), bool)
    keep[first[count == 1]] = True
    m.update_faces(keep)
    m.remove_unreferenced_vertices()
    return int((count > 1).sum())


def clean(m):
    m.merge_vertices(digits_vertex=4)
    good = m.nondegenerate_faces(height=1e-6)
    m.update_faces(good)
    return int((~good).sum()), drop_duplicate_faces(m)


def unpinch(m):
    """Split vertices on edges with more than two triangles and move each copy NUDGE mm into its own side."""
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(np.asarray(m.vertices, dtype=np.float64), np.asarray(m.faces, dtype=np.int32)))
    for _ in range(3):
        ms.meshing_repair_non_manifold_edges(method="Split Vertices")
        ms.meshing_repair_non_manifold_vertices(vertdispratio=0)
    cm = ms.current_mesh()
    v, f = cm.vertex_matrix().copy(), cm.face_matrix()
    out = trimesh.Trimesh(v, f, process=False)
    _, inverse, count = np.unique(np.round(v, 5), axis=0, return_inverse=True, return_counts=True)
    shared = count[inverse] > 1
    v[shared] -= NUDGE * out.vertex_normals[shared]
    return trimesh.Trimesh(v, f, process=False), int(shared.sum())


def max_distance(a, b, n=30000):
    """Largest distance between the surfaces of a and b, sampled both ways (mm)."""
    da = trimesh.proximity.closest_point(b, a.sample(n, seed=1))[1]
    db = trimesh.proximity.closest_point(a, b.sample(n, seed=1))[1]
    return max(da.max(), db.max())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--scale", type=float, default=1.0)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print("| File | Before: open / non-manifold edges | Fixed | After: open / non-manifold edges | Watertight "
          "| Max deviation (mm, at 100 %) |")
    print("|---|---|---|---|---|---|")
    for path in args.stl:
        orig = trimesh.load(path)
        before = edge_report(orig)
        m = orig.copy()
        degenerate, duplicates = clean(m)
        fixed = f"{degenerate} degenerate, {duplicates} duplicate triangles"
        open_edges, pinched = edge_report(m)
        if pinched:
            m, _ = unpinch(m)
            fixed += f", {pinched} pinched edges split (surface moved {NUDGE} mm)"
        if open_edges:
            trimesh.repair.fill_holes(m)
            fixed += f", {open_edges} open edges closed"
        dev = max_distance(m, orig)
        m.apply_scale(args.scale)
        out = os.path.join(args.out_dir, os.path.basename(path))
        m.export(out)
        back = trimesh.load(out)  # read back as a slicer would: vertices merged by position
        after = edge_report(back)
        ok = back.is_watertight and back.is_winding_consistent
        print(f"| `{os.path.basename(path)}` | {before[0]} / {before[1]} | {fixed} | {after[0]} / {after[1]} "
              f"| {'yes' if ok else 'NO'} | {dev:.3f} |")


if __name__ == "__main__":
    main()
