#!/usr/bin/env python3
"""Generic checks for a 3D-printed mechanism before it is printed.

A design is described by a *spec*: a Python file next to the design that tells this tool which parts exist, where each
one is at every step of the motion, and what is allowed. The tool then runs eight checks and writes one report:

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
  8. access       for each pin, screw or snap in ASSEMBLY, the finger or tool that pushes or turns it (a cylinder
                  from tool(), from the fastener out along its approach line) must reach it past every part placed
                  before it. Hardware left out of ASSEMBLY is a failure: a pin nobody can push in is not a design
  9. joints       every joint in JOINTS keeps at least its measured fit (the capstone's cad/fits.py) on every side,
                  at every motion step, measured inside the joint's own region when the parts also touch elsewhere
 10. marks        every gear (GEARS) and every part flagged "phased" has an alignment mark declared in MARKS
  (6. print also reports overhangs whose support would stand on the part itself, in a pocket or under a bridge:
      support nobody can reach, or, with «On build plate only», an overhang printed over air)

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
    ACCESS = [{"at": "pin", "tool": tool("finger", [0, 0, 6], [1, 0, 0]), "why": "push the pin in by hand"}]
                                              # at: the ASSEMBLY entry it serves; tool from the fastener's outer end
                                              # outwards; "except": parts the tool may touch (the fastener itself)
    JOINTS = {("cap", "frame"): {"fit": fits.WINDOW, "where": (center, size), "why": "cap in its opening"},
              ("pin", "shaft"): {"fit": fits.STEEL}}
                                              # fit: a fits.Fit (or anything with .side); where: optional box in the
                                              # ground frame where the gap is measured (when the pair touches
                                              # elsewhere, e.g. a cap resting on its frame); "moves": True to box
                                              # the region with the first part instead
    MARKS = {"shaft": "dot on the tooth that meets the idler's dot", "idler": "dot between two teeth"}
    MIN_GAP, GEAR_GAP, MIN_WALL, BED = 0.2, (0.08, 0.5), 0.8, (256, 256, 256)

Usage:
    python3 tools/cad_verify.py path/to/spec.py [--out check-result.txt] [--render images/check] [--quick]
                                [--only part1,part2]

--quick skips the wall thickness and checks retention at the first motion step only: use it while iterating.
--only checks only what involves these parts (pairs with them, their retention, joints, marks): after a change to
one part, run with --only that part, and the full check once at the end.
Pairs whose relative position repeats (static parts, parts moving together) are computed once and reused.

--render writes assembly.png (3 views), assembly-steps.png (one panel per ASSEMBLY step: the parts already in place
in grey, the incoming part lifted out along its direction, the access tools in red) and section-N.png.

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


# ---------------------------------------------------------------- helpers for spec files

def rod(d, length, p0, axis, n=32):
    """Cylinder for a screw, pin or shaft (steel hardware), from p0 along axis."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    m = trimesh.creation.cylinder(radius=d / 2, height=length, sections=n)
    m.apply_translation([0, 0, length / 2])
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
    m.apply_translation(p0)
    return m


# Hands and tools Morante has (diameter, reach in mm), for ACCESS. A finger needs room for the fingertip and the
# knuckle behind it; the screwdriver is its shaft only (the handle is beyond the reach).
TOOLS = {"finger": (16.0, 40.0), "screwdriver": (6.0, 100.0), "pliers": (10.0, 60.0), "hex-key": (4.0, 50.0)}


def tool(kind, p0, axis, d=None, reach=None):
    """Room a finger or tool needs: a cylinder from p0 (the fastener's outer end) outwards along axis."""
    d0, r0 = TOOLS[kind]
    return rod(d or d0, reach or r0, p0, axis)


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


def box_span(b_moving, b_fixed, d, pad=0.5):
    """Range of s for which box b_moving moved by d·s touches box b_fixed (padded); (inf, -inf) if never."""
    lo, hi = -np.inf, np.inf
    for i in range(3):
        a0, a1 = b_moving[0][i], b_moving[1][i]
        c0, c1 = b_fixed[0][i] - pad, b_fixed[1][i] + pad
        if abs(d[i]) < 1e-12:
            if a1 < c0 or a0 > c1:
                return np.inf, -np.inf
            continue
        s0, s1 = (c0 - a1) / d[i], (c1 - a0) / d[i]
        lo, hi = max(lo, min(s0, s1)), min(hi, max(s0, s1))
    return (lo, hi) if lo <= hi else (np.inf, -np.inf)


def directions():
    v = [np.array(d, float) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
    return [d / np.linalg.norm(d) for d in v]


def name_dir(d):
    return "".join(f"{'+' if c > 0 else '-'}{a}" for c, a in zip(d, "XYZ") if abs(c) > 1e-9)


# ---------------------------------------------------------------- the checks

class Report:
    def __init__(self):
        self.lines, self.fails, self.warns, self.partial = [], 0, 0, False

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
        verdict = ("PASS" if not self.fails else "FAIL") if not self.partial else \
            ("PARTIAL PASS" if not self.fails else "PARTIAL FAIL")
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


def check_integrity(spec, meshes, rep, quick, only=None):
    rep.head("1 integrity (printed parts)")
    bed = np.array(getattr(spec, "BED", (256, 256, 256)))
    min_wall = getattr(spec, "MIN_WALL", 0.8)
    orient = getattr(spec, "PRINT_ORIENT", {})
    for name, p in spec.PARTS.items():
        if p.get("hardware") or not involves(only, name):
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


def poses_at(spec, t):
    pose = spec.poses(t) if hasattr(spec, "poses") else {}
    return {n: np.asarray(pose.get(n, np.eye(4)), float) for n in spec.PARTS}


def rel_key(Ma, Mb):
    """Position of b relative to a, rounded: the same key means the same overlap and gap."""
    return (np.round(np.linalg.solve(Ma, Mb)[:3, :], 5) + 0.0).tobytes()     # + 0.0 turns -0.0 into 0.0


def involves(only, *names):
    return only is None or any(n in only for n in names)


def scan_pairs(spec, meshes, steps, only, gmax):
    """Overlap volume and gap of every pair of parts that come near each other, at each step:
    [(t, a, b, overlap, gap)]. A pair whose relative position repeats is computed once."""
    cache, hits, rows = {}, 0, []
    # gaps beyond 1 mm are neither reported nor checked: a shorter search is much faster (a gap past it reads as the
    # search length)
    radius = max([1.0, getattr(spec, "MIN_GAP", 0.2), gmax] + list(getattr(spec, "PAIR_GAP", {}).values())) + 0.05
    for t in steps:
        ms = placed(spec, meshes, t)
        P = poses_at(spec, t)
        bx = {n: mbox(m) for n, m in ms.items()}
        for a, b in itertools.combinations(ms, 2):
            if not involves(only, a, b) or not boxes_near(bx[a], bx[b], max(1.0, gmax)):
                continue
            ck = (a, b, rel_key(P[a], P[b]))
            if ck in cache:
                v, g = cache[ck]
                hits += 1
            else:
                v = overlap(ms[a], ms[b])
                g = 0.0 if v > EPS_VOL else ms[a].min_gap(ms[b], radius)
                cache[ck] = (v, g)
            rows.append((t, a, b, v, g))
    return rows, len(cache), hits


SPEC_PATH, JOBS = None, 1     # set by main(): worker processes load the spec themselves
_W = {}


def _worker_init(path):
    _W["spec"] = load_spec(path)
    _W["meshes"] = load_meshes(_W["spec"], path)


def _worker_scan(args):
    return scan_pairs(_W["spec"], _W["meshes"], *args)


def scan_pairs_parallel(spec, meshes, steps, only, gmax):
    """scan_pairs split over JOBS processes, in contiguous chunks of the motion (so repeats stay in one chunk)."""
    if JOBS <= 1 or SPEC_PATH is None or len(steps) < 60:     # each process spends ~5-10 s loading the spec
        return scan_pairs(spec, meshes, steps, only, gmax)
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    chunks = [list(c) for c in np.array_split(np.arange(len(steps)), JOBS)]
    args = [([steps[i] for i in c], only, gmax) for c in chunks if len(c)]
    with ProcessPoolExecutor(JOBS, mp_context=multiprocessing.get_context("spawn"), initializer=_worker_init,
                             initargs=(SPEC_PATH,)) as ex:
        parts = list(ex.map(_worker_scan, args))
    return [r for p in parts for r in p[0]], sum(p[1] for p in parts), sum(p[2] for p in parts)


def check_motion(spec, meshes, rep, only=None):
    rep.head("2 motion: overlaps and gaps at every step   3 gears: backlash")
    motion = list(getattr(spec, "MOTION", [0]))
    min_gap = getattr(spec, "MIN_GAP", 0.2)
    gmin, gmax = getattr(spec, "GEAR_GAP", (0.08, 0.5))
    allowed = {pair_key(*k): v for k, v in getattr(spec, "ALLOWED_CONTACT", {}).items()}
    gears = {pair_key(*k) for k in getattr(spec, "GEARS", [])}
    pair_gap = {pair_key(*k): v for k, v in getattr(spec, "PAIR_GAP", {}).items()}
    worst_overlap, closest, gear_overlap = {}, {}, {}
    gear_gap = {g: (np.inf, -np.inf, None, None) for g in gears if involves(only, *g)}
    rows, ncache, hits = scan_pairs_parallel(spec, meshes, motion, only, gmax)
    for t, a, b, v, g in rows:
        k = pair_key(a, b)
        if v > EPS_VOL:
            if k in gears:
                gear_overlap[k] = max(gear_overlap.get(k, (0, None)), (v, t), key=lambda x: x[0])
            elif k not in allowed and v > worst_overlap.get(k, (0, None))[0]:
                worst_overlap[k] = (v, t)
        if k in gears:
            lo, hi, tlo, thi = gear_gap[k]
            gear_gap[k] = (min(lo, g), max(hi, g), t if g < lo else tlo, t if g > hi else thi)
        elif k not in allowed and g < closest.get(k, (np.inf, None))[0]:
            closest[k] = (g, t)
    if worst_overlap:
        for k, (v, t) in sorted(worst_overlap.items(), key=lambda x: -x[1][0]):
            rep.fail(f"{' × '.join(sorted(k))}: overlap {v:.2f} mm³ (worst at {t})")
    else:
        rep.ok(f"no undeclared overlaps over {len(motion)} steps" + (f" (only pairs with {', '.join(sorted(only))})"
                                                                     if only else ""))
    rep.info(f"{ncache} pair positions computed, {hits} repeats reused")
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
    for k, (lo, hi, tlo, thi) in sorted(gear_gap.items(), key=lambda x: sorted(x[0])):
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


def check_retention(spec, meshes, rep, quick, only=None):
    rep.head("4 retention: can a part fall, lift or tip out?")
    retain = getattr(spec, "RETAIN", {})
    motion = list(getattr(spec, "MOTION", [0]))
    samples = motion[:1] if quick else motion[:: max(1, len(motion) // 3)][:3]
    dirs = directions()
    for name, p in spec.PARTS.items():
        if p.get("fixed") or not involves(only, name):
            continue
        r = retain.get(name, {})
        play = r.get("play", 1.0)
        max_tilt = r.get("tilt", 5.0)
        # push only as far as the allowed play (in quarters of it, so the answer is exact): a part that gets that far
        # is not held, however much further it could go
        step, travel = play / 4, play + 1e-9
        tstep, ttravel = max_tilt / 5, max_tilt + 1e-9
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
            near = [m for m in ms.values() if boxes_near(bme, mbox(m), travel + 1)]
            base = [overlap(me, o) for o in near]

            def blocked(moved):
                return any(overlap(moved, o) > b0 + EPS_VOL for o, b0 in zip(near, base))

            for d in dirs:
                if slide is not None and abs(d @ slide) > 0.98:
                    continue
                free = travel
                for s in np.arange(step, travel, step):
                    if blocked(me.translate(list(d * s))):
                        free = s - step
                        break
                if free >= play - 1e-9:
                    problems.append(f"moves {play:g}+ mm towards {name_dir(d)} (at {t})")
            c = (bme[0] + bme[1]) / 2
            for ax in np.eye(3):
                if spin is not None and abs(ax @ spin) > 0.98:
                    continue
                for sgn in (1, -1):
                    free = ttravel
                    for a in np.arange(tstep, ttravel, tstep):
                        M = rot(ax * sgn, a, c)
                        if blocked(me.transform(M[:3, :])):
                            free = a - tstep
                            break
                    if free >= max_tilt - 1e-9:
                        problems.append(f"tilts {max_tilt:g}+° about "
                                        f"{'+' if sgn > 0 else '-'}{'XYZ'[int(np.argmax(ax))]} (at {t})")
        if problems:
            rep.fail(f"{name} is not held: " + "; ".join(dict.fromkeys(problems)))
        else:
            rep.ok(f"{name}: held within {play} mm / {max_tilt}° "
                   f"(free: {'spin' if spin is not None else ''}{' slide' if slide is not None else ''})")


def check_keep_out(spec, meshes, rep, only=None):
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
                if n in skip or not involves(only, d["part"], n) or not boxes_near(mbox(me), mbox(m), 1.0):
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
        bme = mbox(me)
        grid = np.arange(0.25, 60, 0.25)
        # only the travel where the moving part's box crosses an obstacle's box can collide: test those steps only
        spans = [box_span(bme, mbox(o), d) for o in others]
        near = [(o, lo, hi) for o, (lo, hi) in zip(others, spans) if hi >= grid[0] and lo <= grid[-1]]
        base = [overlap(me, o) for o, _, _ in near]
        hit = None
        for s in grid:
            live = [(o, b0) for (o, lo, hi), b0 in zip(near, base) if lo - 0.25 <= s <= hi + 0.25]
            if not live:
                continue
            mv = me.translate(list(d * s))
            if any(overlap(mv, o) > b0 + EPS_VOL for o, b0 in live):
                hit = s
                break
        if hit is None:
            rep.ok(f"{name} goes in from {name_dir(np.sign(d.round(3)))}")
        else:
            rep.fail(f"{name} cannot go in from {name_dir(np.sign(d.round(3)))}: blocked {hit:.2f} mm out")
        done.append(name)
    missing = set(spec.PARTS) - {n for n, _ in seq}
    hw = sorted(n for n in missing if spec.PARTS[n].get("hardware"))
    if hw:
        rep.fail(f"hardware not in ASSEMBLY (how does it go in?): {', '.join(hw)}")
    if missing - set(hw):
        rep.warn(f"not in ASSEMBLY: {', '.join(sorted(missing - set(hw)))}")


def check_access(spec, meshes, rep):
    rep.head("8 access: can a finger or tool reach each fastener when it goes in?")
    seq = getattr(spec, "ASSEMBLY", None) or []
    acc = getattr(spec, "ACCESS", [])
    order = [n for n, _ in seq]
    hw_in = [n for n, d in seq if spec.PARTS.get(n, {}).get("hardware") and d is not None]
    if not acc:
        if hw_in:
            rep.fail(f"no ACCESS entries, but fasteners go in: {', '.join(hw_in)}")
        else:
            rep.info("no fasteners in ASSEMBLY, nothing to reach")
        return
    served = {a["at"] for a in acc}
    for n in hw_in:
        if n not in served:
            rep.fail(f"{n}: no ACCESS entry (which finger or tool pushes it in, and from where?)")
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0])
    for a in acc:
        at = a["at"]
        if at not in order:
            rep.fail(f"ACCESS for {at}: not an ASSEMBLY entry")
            continue
        skip = set(a.get("except", [])) | {at}
        before = [n for n in order[:order.index(at)] if n not in skip]
        tm = to_manifold(a["tool"])
        hits = []
        for n in before:
            if boxes_near(mbox(tm), mbox(ms[n]), 0.5):
                v = overlap(tm, ms[n])
                if v > EPS_VOL:
                    hits.append(f"{n} ({v:.0f} mm³)")
        if hits:
            rep.fail(f"{at}: the tool ({a.get('why', '')}) hits {', '.join(hits)}")
        else:
            rep.ok(f"{at}: reachable ({a.get('why', '')})")


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
        if a <= 1:
            rep.info(f"{name}: no overhangs")
            continue
        # straight down from each overhang: does it reach the bed, or land on the part itself?
        idx = np.nonzero(over)[0]
        origins = m.triangles_center[idx] + np.array([0, 0, -1e-3])
        on_part = m.ray.intersects_any(origins, np.tile([0.0, 0.0, -1.0], (len(idx), 1)))
        trapped = m.area_faces[idx[on_part]].sum()
        msg = f"{name}: {a:.0f} mm² of overhang needing support"
        if trapped > 5:
            pts = m.triangles_center[idx[on_part]]
            where = [round(float(v), 1) for v in pts[np.argmax(m.area_faces[idx[on_part]])]]
            rep.warn(f"{msg}, {trapped:.0f} mm² of it over the part itself (support standing in a pocket or under a "
                     f"bridge, or printed over air with «On build plate only»; largest near {where} in print "
                     f"orientation): open it, split the part, or give the reason in the design review")
        else:
            rep.info(f"{msg}, all of it over the bed")


def check_joints(spec, meshes, rep, only=None):
    joints = getattr(spec, "JOINTS", {})
    rep.head("9 joints: every fit at least its measured clearance, at every step")
    if not joints:
        rep.warn("no JOINTS in the spec: fits are not checked against the measured values (cad/fits.py)")
        return
    motion = list(getattr(spec, "MOTION", [0]))
    for (a, b), j in joints.items():
        if not involves(only, a, b):
            continue
        fit = j["fit"]
        need = getattr(fit, "side", fit)
        status = getattr(fit, "status", "")
        where = j.get("where")
        worst, cache = (np.inf, None), {}
        for t in motion:
            P = poses_at(spec, t)
            ck = rel_key(P[a], P[b])
            if ck in cache and where is None:
                g = cache[ck]
            else:
                ms = placed(spec, meshes, t)
                ma, mb = ms[a], ms[b]
                if where is not None:
                    c, s = np.asarray(where[0], float), np.asarray(where[1], float)
                    box = Manifold.cube(list(s), center=True).translate(list(c))
                    if j.get("moves"):
                        box = box.transform(P[a][:3, :])
                    ma, mb = ma ^ box, mb ^ box
                    if ma.is_empty() or mb.is_empty():
                        rep.fail(f"{a} × {b}: the joint region {where} misses one of the parts (at {t})")
                        break
                g = 0.0 if overlap(ma, mb) > EPS_VOL else ma.min_gap(mb, need + 1.0)
                cache[ck] = g
            if g < worst[0]:
                worst = (g, t)
        g, t = worst
        label = f"{a} × {b} ({j.get('why', getattr(fit, 'what', ''))})"
        if g < need - 0.01:
            rep.fail(f"{label}: {g:.2f} mm a side at {t}, measured fit needs {need:.2f}")
        else:
            rep.ok(f"{label}: ≥ {g:.2f} mm a side (fit {need:.2f}{', ' + status if status else ''})")
        if status == "assumed":
            rep.warn(f"{a} × {b}: fit not measured yet ({getattr(fit, 'source', '')}): prove it on a coupon first")


def check_marks(spec, rep, only=None):
    rep.head("10 marks: can each part that must be lined up be lined up?")
    marks = getattr(spec, "MARKS", {})
    need = {n for pair in getattr(spec, "GEARS", []) for n in pair} | \
        {n for n, p in spec.PARTS.items() if p.get("phased")}
    for n in sorted(need):
        if not involves(only, n):
            continue
        if n in marks:
            rep.ok(f"{n}: {marks[n]}")
        else:
            rep.fail(f"{n}: meshes or is phased but has no alignment mark in MARKS (where is it, how is it lined up?)")
    for n in sorted(set(marks) - need):
        rep.info(f"{n}: {marks[n]}")


# ---------------------------------------------------------------- pictures

def render(spec, meshes, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0])
    tri = {}
    for n, m in ms.items():
        mm = m.to_mesh()
        tri[n] = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)
    # assembly pictures in the house style (tools/figures.py): correct depth order, outlines, words for directions;
    # the sections use the same colour per part
    import figures
    col = figures.colours(spec)
    figures.exploded(spec, meshes, os.path.join(outdir, "assembly.png"))
    figures.assembly_steps(spec, meshes, os.path.join(outdir, "assembly-steps.png"))
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

def load_meshes(spec, path):
    base = os.path.dirname(os.path.abspath(path))
    return {name: p["mesh"] if "mesh" in p else trimesh.load(os.path.join(base, p["stl"]), force="mesh")
            for name, p in spec.PARTS.items()}


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
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                    help="processes for the motion check (default: all cores; 1 to run in one process)")
    ap.add_argument("--only", help="comma-separated parts: check only what involves them (while iterating)")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    global SPEC_PATH, JOBS
    SPEC_PATH, JOBS = os.path.abspath(args.spec), max(1, args.jobs)
    spec = load_spec(args.spec)
    meshes = load_meshes(spec, args.spec)
    rep = Report()
    timing = []
    if only and only - set(spec.PARTS):
        sys.exit(f"--only: no such parts in the spec: {', '.join(sorted(only - set(spec.PARTS)))}")
    if only:
        rep.partial = True
        rep.lines.append(f"PARTIAL CHECK: only what involves {', '.join(sorted(only))}. Run the full check before "
                         f"returning")
    for label, fn in (("integrity", lambda: check_integrity(spec, meshes, rep, args.quick, only)),
                      ("motion", lambda: check_motion(spec, meshes, rep, only)),
                      ("retention", lambda: check_retention(spec, meshes, rep, args.quick, only)),
                      ("assembly", lambda: check_assembly(spec, meshes, rep)),
                      ("print", lambda: check_print(spec, meshes, rep)),
                      ("keep-out", lambda: check_keep_out(spec, meshes, rep, only)),
                      ("access", lambda: check_access(spec, meshes, rep)),
                      ("joints", lambda: check_joints(spec, meshes, rep, only)),
                      ("marks", lambda: check_marks(spec, rep, only))):
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
