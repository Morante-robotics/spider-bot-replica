#!/usr/bin/env python3
"""A reference mesh (a downloaded STL) as the measure of a parametric part rebuilt from it.

Printed parts are build123d code, never meshes (Morante, 2026-11-20); a mesh we copy (jenscolt's carcass and legs)
is only a reference. This tool turns a mesh into numbers a designer models from (sections), the gates a conversion
round runs (compare, source) and the pictures its judge sees (views): how far the part's surface is from the
reference's, both ways, so «it looks like it» becomes a figure in mm. The `mesh-to-cad` agent's method rests on it.

    uv run python tools/mesh_ref.py info REF.stl
    uv run python tools/mesh_ref.py sections REF.stl --axis z --n 12 [--json out.json] [--png out.png]
    uv run python tools/mesh_ref.py compare PART.stl REF.stl [--p95 MM] [--max MM] [--png heat.png]
                                            [--samples 20000] [--view all|above|below]
    uv run python tools/mesh_ref.py source BUILD.py      # FAIL if the build script reads a mesh
    uv run python tools/mesh_ref.py views OUT.png --ref A.stl [B.stl ...] [--parts a.stl [b.stl ...]]
                                          [--edits OUT2.png x.stl[=label] ...]

Fidelity limits (defaults of compare): relative to the part's size, both ways, at the reference's scale: p95 ≤ 3 %
and max ≤ 6 % of the reference's largest extent, never below 1.0 / 2.0 mm (Morante, 2026-11-21: the robot has to look
«more or less» like the Spider-Bot, so the limits are three times the 1 % / 2 % of 2026-11-20, which made
exceptions for the arm, base and body). The gate guards the form; the looks judge and Morante decide the look.
Other limits for one part only as an exception Morante approved, with his reason (`rounds.py except`).

`compare` samples both surfaces evenly and measures each sample's distance to the other surface (the «max» limit
is checked on the 99.9th percentile, so a single stray sample does not decide; the true max is printed too):
part → ref (the part has nothing the reference lacks) and ref → part (the part misses nothing of the reference).
It prints `PASS fidelity ...` or one `FAIL fidelity ...` line per limit broken, so a rounds.py command gate reads it
with `"fail_regex": "^FAIL"`; the exit code is 0 unless it could not run (2). Neither mesh needs to be watertight.
Both meshes must be in the same frame and scale: the part's build script exports it in the reference's frame.
`--view` compares only the faces a viewer outside sees (both meshes alike): for a reference whose inside is not
kept (jenscolt's body: his eye block, bosses and frame), «above» for a part seen on its base, «below» for one seen
from under it.
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import trimesh


P95_REL, MAX_REL = 0.03, 0.06   # default fidelity limits: fractions of the reference's largest extent (docstring)
P95_MIN, MAX_MIN = 1.0, 2.0     # mm, the floors (a small part is not held to less than a print can show)


def limits(ref):
    """Default (p95, max) limits in mm for a reference mesh (or its largest extent in mm)."""
    size = float(ref if np.isscalar(ref) else np.max(ref.extents))
    return round(max(P95_REL * size, P95_MIN), 2), round(max(MAX_REL * size, MAX_MIN), 2)
# A build script that reads a mesh: trimesh, build123d's mesh import, or a load/open/read of an .stl/.obj/.3mf/.ply
READS_MESH = re.compile(r"^[^#]*(import trimesh|trimesh\.|import_stl|import_mesh|Mesher|"
                        r"(load|open|read)\(.*\.(stl|obj|3mf|ply)\b)", re.I)
VIEWS = [(25, -130, "3/4"), (0, -90, "front"), (0, 0, "side"), (90, -90, "top")]
LIGHT = np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8])


def load(path):
    m = trimesh.load(path, force="mesh")
    if not isinstance(m, trimesh.Trimesh) or len(m.faces) == 0:
        raise ValueError(f"{path}: no triangles")
    return m


VIEW_HORIZON = 0.10          # «above» keeps viewers down to 0.1 below the horizon (and «below» up to 0.1 above it)


def view_dirs(view, n=160):
    """Unit directions from a viewer far outside toward the part (Fibonacci sphere), for a viewer «all» round,
    «above» (seen from above and the sides: what a part on its base shows) or «below» (from below and the sides)."""
    k = np.arange(n) + 0.5
    phi, th = np.arccos(1 - 2 * k / n), np.pi * (1 + 5 ** 0.5) * k
    viewer = np.c_[np.sin(phi) * np.cos(th), np.sin(phi) * np.sin(th), np.cos(phi)]   # where the viewer stands
    keep = {"all": np.ones(n, bool), "above": viewer[:, 2] >= -VIEW_HORIZON,
            "below": viewer[:, 2] <= VIEW_HORIZON}[view]
    return -viewer[keep]


def visible(m, view="all", n=160):
    """The faces of m a viewer outside can see (the first face hit along some direction of view_dirs), as a mesh.
    A reference's inside (posts, blocks, the inner wall) and a part's inside drop out alike, so `compare --view`
    measures the look, not what the converted part was told to leave out."""
    dirs = view_dirs(view, n)
    C = m.triangles_center
    R = float(np.linalg.norm(m.extents)) + 1.0
    seen = np.zeros(len(m.faces), bool)
    for d in dirs:
        idx = m.ray.intersects_first(C - d * R, np.repeat(d[None], len(C), 0))
        hit = idx >= 0
        seen[idx[hit]] = True
    out = m.submesh([np.nonzero(seen)[0]], append=True)
    return out


def surface_distance(src, dst, n, seed=0):
    """Distances from n points sampled evenly on src's surface to dst's surface, and the points."""
    pts, _ = trimesh.sample.sample_surface_even(src, n, seed=seed)
    if len(pts) < n // 2:                     # even sampling can fall short on slivers: top up at random
        extra, _ = trimesh.sample.sample_surface(src, n - len(pts), seed=seed)
        pts = np.vstack([pts, extra])
    _, d, _ = trimesh.proximity.closest_point(dst, pts)
    return d, pts


MAX_Q = 99.9                 # the «max» limit is checked on this percentile: one stray sample (a sliver left in a
                             # reference, 1 of 20 000) does not decide; the true max is still printed


def stats(d):
    return {"max": float(d.max()), "p999": float(np.percentile(d, MAX_Q)), "p95": float(np.percentile(d, 95)),
            "mean": float(d.mean())}


def compare(part, ref, n=20000, view=None):
    if view:
        part, ref = visible(part, view), visible(ref, view)
    d_pr, p_pr = surface_distance(part, ref, n)
    d_rp, p_rp = surface_distance(ref, part, n)
    return {"part_to_ref": stats(d_pr), "ref_to_part": stats(d_rp),
            "volume_ratio": float(part.volume / ref.volume) if ref.is_volume and part.is_volume else None,
            "_samples": (p_pr, d_pr, p_rp, d_rp)}


def sections(m, axis="z", n=12):
    """n plane sections across the mesh along axis: each as closed/open polylines in 3D (mm)."""
    k = "xyz".index(axis)
    lo, hi = m.bounds[0][k], m.bounds[1][k]
    out = []
    for t in np.linspace(lo, hi, n + 2)[1:-1]:
        o, nv = np.zeros(3), np.zeros(3)
        o[k], nv[k] = t, 1.0
        s = m.section(plane_origin=o, plane_normal=nv)
        if s is None:
            continue
        loops = [e.tolist() for e in s.discrete]
        out.append({"at": float(t), "loops": [[[round(c, 3) for c in p] for p in lp] for lp in loops]})
    return out


def source_check(path):
    """The lines of a build script that read a mesh (a printed part comes from parameters, never from a mesh)."""
    with open(path) as f:
        return [(i + 1, ln.rstrip()) for i, ln in enumerate(f) if READS_MESH.search(ln)]


def _ax3d(fig, k, n, c, r, el, az, title, zoom=1.45):
    ax = fig.add_subplot(1, n, k + 1, projection="3d")
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1), zoom=zoom)
    ax.view_init(el, az)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10)
    return ax


def _draw(ax, m, tone):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    shade = np.clip(tone + 0.35 * (m.face_normals @ LIGHT), 0.05, 0.95)
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=plt.cm.Greys_r(shade), edgecolor="none"))


def views(out, refs, parts=None, edits=None):
    """Four fixed views, flat grey, no labels on the part, framed on the REFERENCE meshes' bounds: with parts, the
    design; without, the reference itself. Both come from this one function, so the judge compares like with like.
    edits = (out2, [(stl, label)]): a second picture of edited variants, each framed on itself."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    b = np.vstack([load(p).bounds for p in refs])
    c, r = (b.min(0) + b.max(0)) / 2, (b.max(0) - b.min(0)).max() / 2 * 1.05
    meshes = [load(p) for p in (parts or refs)]
    tones = np.linspace(0.50, 0.32, max(len(meshes), 2))      # parts told apart by tone, one colour
    fig = plt.figure(figsize=(16, 5.2))
    for k, (el, az, title) in enumerate(VIEWS):
        ax = _ax3d(fig, k, len(VIEWS), c, r, el, az, title)
        for m, t in zip(meshes, tones):
            _draw(ax, m, t)
    plt.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close(fig)
    if edits:
        out2, items = edits
        fig = plt.figure(figsize=(4 * len(items), 5.6))
        fig.suptitle("EDIT TEST (not the reference shape): the same part, only its parameters changed", fontsize=11)
        for k, (p, label) in enumerate(items):
            m = load(p)
            ax = _ax3d(fig, k, len(items), m.bounds.mean(0), m.extents.max() / 2 * 1.05, 20, -120, label, 1.3)
            _draw(ax, m, 0.5)
        plt.tight_layout()
        fig.savefig(out2, dpi=100)
        plt.close(fig)


def heat_png(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    p_pr, d_pr, p_rp, d_rp = res["_samples"]
    vmax = max(float(np.percentile(np.r_[d_pr, d_rp], 99)), 0.2)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.5))
    views = [((0, 2), "front (X, Z)"), ((1, 2), "side (Y, Z)"), ((0, 1), "top (X, Y)")]
    for row, (pts, d, label) in enumerate([(p_pr, d_pr, "part → reference"), (p_rp, d_rp, "reference → part")]):
        o = np.argsort(d)                                        # the far points drawn last, on top
        for col, ((i, j), vt) in enumerate(views):
            ax = axes[row, col]
            sc = ax.scatter(pts[o, i], pts[o, j], c=d[o], s=2, cmap="magma_r", vmin=0, vmax=vmax)
            ax.set_aspect("equal")
            ax.set_title(f"{label} · {vt}", fontsize=9)
            ax.tick_params(labelsize=7)
    fig.colorbar(sc, ax=axes, shrink=0.6, label="distance (mm)")
    fig.savefig(path, dpi=110)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("info")
    a.add_argument("ref")
    s = sub.add_parser("sections")
    s.add_argument("ref")
    s.add_argument("--axis", default="z", choices=list("xyz"))
    s.add_argument("--n", type=int, default=12)
    s.add_argument("--json")
    s.add_argument("--png")
    c = sub.add_parser("compare")
    c.add_argument("part")
    c.add_argument("ref")
    c.add_argument("--max", type=float, help="limit on the largest distance either way (mm; default: limits())")
    c.add_argument("--p95", type=float, help="limit on the 95th percentile either way (mm; default: limits())")
    c.add_argument("--samples", type=int, default=20000)
    c.add_argument("--view", choices=["all", "above", "below"],
                   help="compare only what a viewer outside sees (both meshes): «above» for a part on its base")
    c.add_argument("--png")
    c.add_argument("--json")
    so = sub.add_parser("source")
    so.add_argument("build")
    v = sub.add_parser("views")
    v.add_argument("out")
    v.add_argument("--ref", nargs="+", required=True)
    v.add_argument("--parts", nargs="+")
    v.add_argument("--edits", nargs="+", help="OUT2.png then variant.stl[=label] ...")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "info":
            m = load(a.ref)
            print(json.dumps({"triangles": len(m.faces), "watertight": bool(m.is_watertight),
                              "extents": np.round(m.extents, 2).tolist(), "bounds": np.round(m.bounds, 2).tolist(),
                              "volume": round(float(m.volume), 1) if m.is_volume else None}))
        elif a.cmd == "source":
            hits = source_check(a.build)
            for n, ln in hits:
                print(f"FAIL {os.path.basename(a.build)}:{n} reads a mesh: {ln.strip()[:120]}")
            if not hits:
                print(f"PASS source: {os.path.basename(a.build)} reads no mesh (the shape comes from its parameters)")
        elif a.cmd == "views":
            ed = None
            if a.edits:
                items = [(x.split("=", 1)[0], x.split("=", 1)[1] if "=" in x else os.path.basename(x))
                         for x in a.edits[1:]]
                ed = (a.edits[0], items)
            views(a.out, a.ref, a.parts, ed)
        elif a.cmd == "sections":
            secs = sections(load(a.ref), a.axis, a.n)
            if a.json:
                with open(a.json, "w") as f:
                    json.dump({"axis": a.axis, "sections": secs}, f)
            for sc in secs:
                pts = np.vstack([np.array(lp) for lp in sc["loops"]])
                k = [i for i in range(3) if i != "xyz".index(a.axis)]
                ext = pts[:, k].max(0) - pts[:, k].min(0)
                print(f"{a.axis}={sc['at']:8.2f}  loops {len(sc['loops'])}  extent "
                      f"{'xyz'[k[0]]} {ext[0]:6.2f}  {'xyz'[k[1]]} {ext[1]:6.2f}")
            if a.png:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                k = [i for i in range(3) if i != "xyz".index(a.axis)]
                fig, ax = plt.subplots(figsize=(7, 7))
                for sc in secs:
                    for lp in sc["loops"]:
                        lp = np.array(lp)
                        ax.plot(lp[:, k[0]], lp[:, k[1]], lw=0.8)
                ax.set_aspect("equal")
                fig.savefig(a.png, dpi=110)
        else:
            part, ref = load(a.part), load(a.ref)
            dp, dm = limits(ref)
            src = "" if a.p95 or a.max else f", {P95_REL:.0%} / {MAX_REL:.0%} of {np.max(ref.extents):.0f} mm"
            a.p95, a.max = a.p95 or dp, a.max or dm
            res = compare(part, ref, a.samples, a.view)
            fails = []
            for way in ("part_to_ref", "ref_to_part"):
                st = res[way]
                if st["p999"] > a.max:
                    fails.append(f"FAIL fidelity {way} max (p{MAX_Q:g}) {st['p999']:.2f} mm > {a.max} mm")
                if st["p95"] > a.p95:
                    fails.append(f"FAIL fidelity {way} p95 {st['p95']:.2f} mm > {a.p95} mm")
            summary = "  ".join(f"{w}: max {res[w]['max']:.2f} (p{MAX_Q:g} {res[w]['p999']:.2f}) p95 {res[w]['p95']:.2f} "
                                f"mean {res[w]['mean']:.2f}"
                                for w in ("part_to_ref", "ref_to_part"))
            vr = res["volume_ratio"]
            vw = f", visible from {a.view}" if a.view else ""
            print("\n".join(fails) if fails else f"PASS fidelity (max ≤ {a.max}, p95 ≤ {a.p95} mm{src}{vw})")
            print(f"  {summary}" + (f"  volume part/ref {vr:.3f}" if vr else ""))
            if a.png:
                heat_png(res, a.png)
                print(f"  heat map: {a.png}")
            if a.json:
                with open(a.json, "w") as f:
                    json.dump({k: v for k, v in res.items() if not k.startswith("_")} | {"fails": fails}, f,
                              indent=1)
    except Exception as e:                                       # noqa: BLE001  (the gate must say it could not run)
        print(f"ERROR mesh_ref {a.cmd}: {e}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
