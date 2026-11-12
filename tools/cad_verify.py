#!/usr/bin/env python3
"""Generic checks for a 3D-printed mechanism before it is printed.

A design is described by a *spec*: a Python file next to the design that tells this tool which parts exist, where each
one is at every step of the motion, and what is allowed. The tool then runs seven checks and writes one report:

  1. integrity    every printed part is one closed, consistently oriented solid with positive volume, fits the bed,
                  and has no walls thinner than MIN_WALL (sampled by casting rays inwards)
  2. motion       every pair of parts, at every motion step: no overlap (unless the pair is declared), and no gap
                  smaller than MIN_GAP. Meshing gears are checked too, never skipped: their gap is the backlash
  3. gears        declared gear pairs must keep a gap inside GEAR_GAP at every step: too small binds, too large skips
  4. retention    every part that is not fixed is pushed 3 mm in 26 directions and tilted ±10° about 3 axes: if
                  nothing stops it within its allowed play, it can fall or lift out (a crankshaft in an open slot).
                  Its gear partners do not count as holding it: they would turn and let it out
  5. assembly     each part in ASSEMBLY can be moved in along its direction past the parts placed before it
                  (its gear partners are ignored: they can be turned to let it in)
  6. print        overhang area per printed part in its print orientation (information for supports)
  7. keep-out     optional zones carried by a part (e.g. a spinning gear's faces thickened by the axial clearance it
                  needs, plus its float): no other part may enter them at any step, except the parts listed

Spec file (all names optional except PARTS and poses):

    PARTS = {"frame": {"stl": "frame.stl", "fixed": True},
             "shaft": {"stl": "shaft.stl"},
             "pin":   {"mesh": rod(3.0, 12, [0, 0, 0], [1, 0, 0]), "hardware": True}}
    MOTION = [0, 30, 60, ...]                 # values passed to poses(); default [0]
    def poses(t): return {"shaft": 4x4 matrix, ...}   # parts left out stay where their STL puts them
    ALLOWED_CONTACT = {("pin", "frame"): "press fit"}  # pairs allowed to touch or overlap, with the reason
    GEARS = [("shaft", "idler")]              # meshing pairs
    RETAIN = {"shaft": {"spin": [1, 0, 0], "slide": None, "play": 1.0}}   # free rotation axis, free slide axis
    ASSEMBLY = [("frame", None), ("shaft", [0, 0, 1])]   # order, and the direction each part comes in from
    PRINT_ORIENT = {"shaft": 4x4}             # how each part lies on the bed (default: as in its STL)
    SECTIONS = [([0, 0, 0], [1, 0, 0])]       # cut planes (point, normal) for the pictures
    PAIR_GAP = {("pin", "shaft"): 0.1}       # smallest gap for a pair, where MIN_GAP does not fit (a pin in its bore)
    KEEP_OUT = {"gear-faces": {"part": "shaft", "mesh": m, "except": ["frame"], "why": "0.8 mm axial"}}
                                              # m in the part's own frame, moves with it; "except": parts allowed in
    MIN_GAP, GEAR_GAP, MIN_WALL, BED = 0.2, (0.08, 0.5), 0.8, (256, 256, 256)

Usage:
    python3 tools/cad_verify.py path/to/spec.py [--out check-result.txt] [--render images/check] [--quick]

Exit code 0 when every check passes, 1 otherwise. Needs numpy, trimesh, manifold3d, rtree, matplotlib.
"""
import argparse
import importlib.util
import itertools
import os
import sys
import time

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

EPS_VOL = 1e-3          # mm³: anything below is numerical noise
TRAVEL, STEP = 3.0, 0.1     # retention: how far each part is pushed, and in what steps (mm)
TILT, TILT_STEP = 10.0, 0.5   # retention: how far it is tilted (degrees)


# ---------------------------------------------------------------- helpers for spec files

def rod(d, length, p0, axis, n=32):
    """Cylinder for a screw, pin or shaft (steel hardware), from p0 along axis."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    m = trimesh.creation.cylinder(radius=d / 2, height=length, sections=n)
    m.apply_translation([0, 0, length / 2])
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
    m.apply_translation(p0)
    return m


def rot(axis, deg, about=(0, 0, 0)):
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis, about)


def move(v):
    return trimesh.transformations.translation_matrix(v)


# ---------------------------------------------------------------- geometry

def to_manifold(m):
    return Manifold(Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                         tri_verts=np.asarray(m.faces, np.uint32)))


def overlap(a, b):
    return (a ^ b).volume()


def boxes_near(b1, b2, d):
    return np.all(b1[0] <= b2[1] + d) and np.all(b2[0] <= b1[1] + d)


def mbox(m):
    b = m.bounding_box()
    return np.array([b[:3], b[3:]])


def directions():
    v = [np.array(d, float) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
    return [d / np.linalg.norm(d) for d in v]


def name_dir(d):
    return "".join(f"{'+' if c > 0 else '-'}{a}" for c, a in zip(d, "XYZ") if abs(c) > 1e-9)


# ---------------------------------------------------------------- the checks

class Report:
    def __init__(self):
        self.lines, self.fails, self.warns = [], 0, 0

    def head(self, s):
        self.lines += ["", f"== {s}"]

    def ok(self, s):
        self.lines.append(f"  ok    {s}")

    def info(self, s):
        self.lines.append(f"        {s}")

    def warn(self, s):
        self.warns += 1
        self.lines.append(f"  WARN  {s}")

    def fail(self, s):
        self.fails += 1
        self.lines.append(f"  FAIL  {s}")

    def text(self):
        verdict = "PASS" if not self.fails else "FAIL"
        return "\n".join([f"cad_verify: {verdict} ({self.fails} failures, {self.warns} warnings)"] + self.lines) + "\n"


def wall_thickness(mesh, n=3000):
    """Local thickness at n surface samples: distance along the inward normal to the opposite surface."""
    pts, fi = trimesh.sample.sample_surface_even(mesh, n)
    nrm = mesh.face_normals[fi]
    origins = pts - nrm * 1e-3
    locs, idx, _ = mesh.ray.intersects_location(origins, -nrm, multiple_hits=False)
    t = np.full(len(pts), np.inf)
    t[idx] = np.linalg.norm(locs - origins[idx], axis=1)
    return pts, t


def check_integrity(spec, meshes, rep, quick):
    rep.head("1 integrity (printed parts)")
    bed = np.array(getattr(spec, "BED", (256, 256, 256)))
    min_wall = getattr(spec, "MIN_WALL", 0.8)
    orient = getattr(spec, "PRINT_ORIENT", {})
    for name, p in spec.PARTS.items():
        if p.get("hardware"):
            continue
        m = meshes[name]
        bad = []
        if not m.is_watertight:
            bad.append("not watertight")
        if not m.is_winding_consistent:
            bad.append("inconsistent winding")
        if m.volume <= 0:
            bad.append(f"volume {m.volume:.1f} mm³ (inside out?)")
        bodies = len(m.split(only_watertight=False))
        if bodies != p.get("bodies", 1):
            bad.append(f"{bodies} separate bodies (expected {p.get('bodies', 1)})")
        degen = int((m.area_faces < 1e-9).sum())
        if degen:
            bad.append(f"{degen} zero-area faces")
        o = m.copy()
        if name in orient:
            o.apply_transform(orient[name])
        size = o.extents
        if np.any(np.sort(size)[::-1] > np.sort(bed)[::-1]):
            bad.append(f"does not fit the bed: {size.round(1)} mm")
        if bad:
            rep.fail(f"{name}: " + "; ".join(bad))
            continue
        msg = f"{name}: closed solid, {m.volume:.0f} mm³, {' × '.join(f'{s:.1f}' for s in size)} mm"
        if quick:
            rep.ok(msg)
            continue
        pts, t = wall_thickness(m)
        thin = t < min_wall
        frac = thin.mean()
        if frac > 0.005:
            where = pts[thin][:3].round(1).tolist()
            rep.warn(f"{msg}; {frac:.1%} of the surface is thinner than {min_wall} mm "
                     f"(thinnest {t.min():.2f} mm, e.g. at {where})")
        else:
            rep.ok(f"{msg}; walls ≥ {min_wall} mm")


def placed(spec, meshes, t):
    pose = spec.poses(t) if hasattr(spec, "poses") else {}
    out = {}
    for name in spec.PARTS:
        M = pose.get(name, np.eye(4))
        out[name] = to_manifold(meshes[name]).transform(np.asarray(M, float)[:3, :])
    return out


def pair_key(a, b):
    return frozenset((a, b))


def check_motion(spec, meshes, rep):
    rep.head("2 motion: overlaps and gaps at every step   3 gears: backlash")
    motion = list(getattr(spec, "MOTION", [0]))
    min_gap = getattr(spec, "MIN_GAP", 0.2)
    gmin, gmax = getattr(spec, "GEAR_GAP", (0.08, 0.5))
    allowed = {pair_key(*k): v for k, v in getattr(spec, "ALLOWED_CONTACT", {}).items()}
    gears = {pair_key(*k) for k in getattr(spec, "GEARS", [])}
    pair_gap = {pair_key(*k): v for k, v in getattr(spec, "PAIR_GAP", {}).items()}
    worst_overlap, closest, gear_overlap = {}, {}, {}
    gear_gap = {g: (np.inf, -np.inf, None, None) for g in gears}
    for t in motion:
        ms = placed(spec, meshes, t)
        bx = {n: mbox(m) for n, m in ms.items()}
        for a, b in itertools.combinations(ms, 2):
            k = pair_key(a, b)
            if not boxes_near(bx[a], bx[b], max(1.0, gmax)):
                continue
            v = overlap(ms[a], ms[b])
            if v > EPS_VOL:
                if k in gears:
                    gear_overlap[k] = max(gear_overlap.get(k, (0, None)), (v, t), key=lambda x: x[0])
                elif k not in allowed and v > worst_overlap.get(k, (0, None))[0]:
                    worst_overlap[k] = (v, t)
                g = 0.0
            else:
                g = ms[a].min_gap(ms[b], 2.0)
            if k in gears:
                lo, hi, tlo, thi = gear_gap[k]
                gear_gap[k] = (min(lo, g), max(hi, g), t if g < lo else tlo, t if g > hi else thi)
            elif k not in allowed and g < closest.get(k, (np.inf, None))[0]:
                closest[k] = (g, t)
    if worst_overlap:
        for k, (v, t) in sorted(worst_overlap.items(), key=lambda x: -x[1][0]):
            rep.fail(f"{' × '.join(sorted(k))}: overlap {v:.2f} mm³ (worst at {t})")
    else:
        rep.ok(f"no undeclared overlaps over {len(motion)} steps")
    for k, (g, t) in sorted(closest.items(), key=lambda x: x[1][0]):
        if k in worst_overlap:
            continue
        need = pair_gap.get(k, min_gap)
        if g < need:
            rep.fail(f"{' × '.join(sorted(k))}: gap {g:.2f} mm < {need} (at {t})")
        elif g < 1.0:
            rep.info(f"{' × '.join(sorted(k))}: gap {g:.2f} mm (closest at {t})")
    for k, reason in allowed.items():
        rep.info(f"{' × '.join(sorted(k))}: contact allowed ({reason})")
    for k, (lo, hi, tlo, thi) in gear_gap.items():
        pair = " × ".join(sorted(k))
        if k in gear_overlap:
            v, t = gear_overlap[k]
            rep.fail(f"gears {pair}: teeth overlap {v:.2f} mm³ (worst at {t}): they interfere and will jam")
        elif lo < gmin:
            rep.fail(f"gears {pair}: gap {lo:.2f} mm at {tlo} < {gmin}: no backlash, they will bind")
        elif hi > gmax:
            rep.fail(f"gears {pair}: gap {hi:.2f} mm at {thi} > {gmax}: teeth disengage, they will skip")
        else:
            rep.ok(f"gears {pair}: gap {lo:.2f}–{hi:.2f} mm over the motion")


def check_retention(spec, meshes, rep, quick):
    rep.head("4 retention: can a part fall, lift or tip out?")
    retain = getattr(spec, "RETAIN", {})
    motion = list(getattr(spec, "MOTION", [0]))
    samples = motion[:1] if quick else motion[:: max(1, len(motion) // 3)][:3]
    dirs = directions()
    for name, p in spec.PARTS.items():
        if p.get("fixed"):
            continue
        r = retain.get(name, {})
        play = r.get("play", 1.0)
        spin = np.asarray(r["spin"], float) / np.linalg.norm(r["spin"]) if r.get("spin") is not None else None
        slide = np.asarray(r["slide"], float) / np.linalg.norm(r["slide"]) if r.get("slide") is not None else None
        # a meshing gear never holds its partner in: it turns and lets the teeth out. Same for parts named in not_by
        not_by = set(r.get("not_by", [])) | {b for a, b in getattr(spec, "GEARS", []) if a == name} | \
            {a for a, b in getattr(spec, "GEARS", []) if b == name}
        problems = []
        for t in samples:
            ms = placed(spec, meshes, t)
            me = ms.pop(name)
            for other in not_by:
                ms.pop(other, None)
            bme = mbox(me)
            near = [m for m in ms.values() if boxes_near(bme, mbox(m), TRAVEL + 1)]
            base = [overlap(me, o) for o in near]

            def blocked(moved):
                return any(overlap(moved, o) > b0 + EPS_VOL for o, b0 in zip(near, base))

            for d in dirs:
                if slide is not None and abs(d @ slide) > 0.98:
                    continue
                free = TRAVEL
                for s in np.arange(STEP, TRAVEL + 1e-9, STEP):
                    if blocked(me.translate(list(d * s))):
                        free = s - STEP
                        break
                if free >= play:
                    problems.append(f"moves {free:.1f}{'+' if free >= TRAVEL else ''} mm towards {name_dir(d)} "
                                    f"(at {t})")
            c = (bme[0] + bme[1]) / 2
            for ax in np.eye(3):
                if spin is not None and abs(ax @ spin) > 0.98:
                    continue
                for sgn in (1, -1):
                    free = TILT
                    for a in np.arange(TILT_STEP, TILT + 1e-9, TILT_STEP):
                        M = rot(ax * sgn, a, c)
                        if blocked(me.transform(M[:3, :])):
                            free = a - TILT_STEP
                            break
                    if free >= r.get("tilt", 5.0):
                        problems.append(f"tilts {free:.1f}{'+' if free >= TILT else ''}° about "
                                        f"{'+' if sgn > 0 else '-'}{'XYZ'[int(np.argmax(ax))]} (at {t})")
        if problems:
            rep.fail(f"{name} is not held: " + "; ".join(dict.fromkeys(problems)))
        else:
            rep.ok(f"{name}: held within {play} mm / {r.get('tilt', 5.0)}° "
                   f"(free: {'spin' if spin is not None else ''}{' slide' if slide is not None else ''})")


def check_keep_out(spec, meshes, rep):
    zones = getattr(spec, "KEEP_OUT", {})
    if not zones:
        return
    rep.head("7 keep-out zones (moving with their part, at every step)")
    motion = list(getattr(spec, "MOTION", [0]))
    worst = {z: {} for z in zones}
    closest = {z: (np.inf, None, None) for z in zones}
    zm = {z: to_manifold(d["mesh"]) for z, d in zones.items()}
    for t in motion:
        pose = spec.poses(t) if hasattr(spec, "poses") else {}
        ms = placed(spec, meshes, t)
        for z, d in zones.items():
            me = zm[z].transform(np.asarray(pose.get(d["part"], np.eye(4)), float)[:3, :])
            skip = set(d.get("except", [])) | {d["part"]}
            for n, m in ms.items():
                if n in skip or not boxes_near(mbox(me), mbox(m), 1.0):
                    continue
                v = overlap(me, m)
                if v > EPS_VOL:
                    if v > worst[z].get(n, (0, None))[0]:
                        worst[z][n] = (v, t)
                else:
                    g = me.min_gap(m, 2.0)
                    if g < closest[z][0]:
                        closest[z] = (g, n, t)
    for z, d in zones.items():
        if worst[z]:
            for n, (v, t) in sorted(worst[z].items(), key=lambda x: -x[1][0]):
                rep.fail(f"{n} enters {z} ({d.get('why', '')}): {v:.2f} mm³ (worst at {t})")
        else:
            g, n, t = closest[z]
            extra = f"; closest {n}, {g:.2f} mm outside it (at {t})" if n else ""
            rep.ok(f"{z} ({d.get('why', '')}): clear over {len(motion)} steps{extra}")
        if d.get("except"):
            rep.info(f"{z}: not checked against {', '.join(d['except'])}" +
                     (f" ({d['except_why']})" if d.get("except_why") else ""))


def check_assembly(spec, meshes, rep):
    seq = getattr(spec, "ASSEMBLY", None)
    rep.head("5 assembly order")
    if not seq:
        rep.warn("no ASSEMBLY order in the spec: cannot tell whether the parts can be put together")
        return
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0])
    done = []
    for name, d in seq:
        if d is None:
            done.append(name)
            continue
        d = np.asarray(d, float) / np.linalg.norm(d)
        me = ms[name]
        partners = {b for a, b in getattr(spec, "GEARS", []) if a == name} | \
            {a for a, b in getattr(spec, "GEARS", []) if b == name}
        others = [ms[n] for n in done if n not in partners]
        base = [overlap(me, o) for o in others]
        hit = None
        for s in np.arange(0.25, 60, 0.25):
            mv = me.translate(list(d * s))
            if any(overlap(mv, o) > b0 + EPS_VOL for o, b0 in zip(others, base)):
                hit = s
                break
        if hit is None:
            rep.ok(f"{name} goes in from {name_dir(np.sign(d.round(3)))}")
        else:
            rep.fail(f"{name} cannot go in from {name_dir(np.sign(d.round(3)))}: blocked {hit:.2f} mm out")
        done.append(name)
    missing = set(spec.PARTS) - {n for n, _ in seq}
    if missing:
        rep.warn(f"not in ASSEMBLY: {', '.join(sorted(missing))}")


def check_print(spec, meshes, rep):
    rep.head("6 print (overhangs over 45°, in print orientation)")
    orient = getattr(spec, "PRINT_ORIENT", {})
    for name, p in spec.PARTS.items():
        if p.get("hardware"):
            continue
        m = meshes[name].copy()
        if name in orient:
            m.apply_transform(orient[name])
        z0 = m.bounds[0][2]
        nz = m.face_normals[:, 2]
        zc = m.triangles_center[:, 2]
        over = (nz < -np.cos(np.radians(45))) & (zc > z0 + 0.3)
        a = m.area_faces[over].sum()
        rep.info(f"{name}: {a:.0f} mm² of overhang needing support" if a > 1 else f"{name}: no overhangs")


# ---------------------------------------------------------------- pictures

def render(spec, meshes, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    os.makedirs(outdir, exist_ok=True)
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0])
    tri = {}
    for n, m in ms.items():
        mm = m.to_mesh()
        tri[n] = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)
    cmap = plt.get_cmap("tab20")
    col = {n: cmap(i % 20) for i, n in enumerate(tri)}
    lo = np.min([t.bounds[0] for t in tri.values()], axis=0)
    hi = np.max([t.bounds[1] for t in tri.values()], axis=0)
    fig = plt.figure(figsize=(15, 5))
    for k, (el, az) in enumerate([(25, -60), (25, 30), (80, -90)]):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        for n, t in tri.items():
            ax.add_collection3d(Poly3DCollection(t.triangles, facecolor=col[n], edgecolor="none", alpha=0.9))
        c, r = (lo + hi) / 2, (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r), ax.set_ylim(c[1] - r, c[1] + r), ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(el, az)
        ax.set_xlabel("X"), ax.set_ylabel("Y"), ax.set_zlabel("Z")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=col[n]) for n in tri], labels=list(tri), loc="lower center",
               ncol=min(8, len(tri)), fontsize=8)
    fig.savefig(os.path.join(outdir, "assembly.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)
    for i, (o, nrm) in enumerate(getattr(spec, "SECTIONS", [])):
        fig, ax = plt.subplots(figsize=(8, 8))
        nrm = np.asarray(nrm, float) / np.linalg.norm(nrm)
        to2d = trimesh.geometry.plane_transform(origin=o, normal=nrm)
        for n, t in tri.items():
            s = t.section(plane_origin=o, plane_normal=nrm)
            if s is None:
                continue
            s.vertices = s.vertices - np.outer(s.vertices @ nrm - np.dot(o, nrm), nrm)   # snap onto the plane
            p2, _ = s.to_2D(to_2D=to2d)
            for poly in p2.polygons_full:
                xs, ys = poly.exterior.xy
                ax.fill(xs, ys, color=col[n], alpha=0.8, label=n)
                for hole in poly.interiors:
                    hx, hy = hole.xy
                    ax.fill(hx, hy, color="white")
        h, l = ax.get_legend_handles_labels()
        u = dict(zip(l, h))
        ax.legend(u.values(), u.keys(), fontsize=8)
        ax.set_aspect("equal")
        ax.set_title(f"section {i}: point {[round(float(v), 1) for v in o]}, normal {[round(float(v), 2) for v in nrm]}")
        fig.savefig(os.path.join(outdir, f"section-{i}.png"), dpi=110, bbox_inches="tight")
        plt.close(fig)


# ---------------------------------------------------------------- main

def load_spec(path):
    path = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(path))
    s = importlib.util.spec_from_file_location("cad_spec", path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", help="write the report here as well")
    ap.add_argument("--render", metavar="DIR", help="write assembly.png and section-N.png here")
    ap.add_argument("--quick", action="store_true", help="skip wall thickness; retention at the first step only")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    base = os.path.dirname(os.path.abspath(args.spec))
    meshes = {}
    for name, p in spec.PARTS.items():
        meshes[name] = p["mesh"] if "mesh" in p else trimesh.load(os.path.join(base, p["stl"]), force="mesh")
    rep = Report()
    timing = []
    for label, fn in (("integrity", lambda: check_integrity(spec, meshes, rep, args.quick)),
                      ("motion", lambda: check_motion(spec, meshes, rep)),
                      ("retention", lambda: check_retention(spec, meshes, rep, args.quick)),
                      ("assembly", lambda: check_assembly(spec, meshes, rep)),
                      ("print", lambda: check_print(spec, meshes, rep)),
                      ("keep-out", lambda: check_keep_out(spec, meshes, rep))):
        t0 = time.perf_counter()
        fn()
        timing.append(f"{label} {time.perf_counter() - t0:.0f} s")
        print(f"[{timing[-1]}]", file=sys.stderr, flush=True)
    txt = rep.text()
    print(txt)
    if args.out:
        with open(args.out, "w") as f:
            f.write(txt)
    if args.render:
        render(spec, meshes, args.render)
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
