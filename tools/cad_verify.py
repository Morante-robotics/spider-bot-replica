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
                  (its gear partners are ignored: they can be turned to let it in). A step may move a tuple of
                  parts as one body (a sub-assembly), or be done on the bench against its own bench parts only
  6. print        overhang area per printed part in its print orientation (information for supports)
  7. keep-out     optional zones carried by a part (e.g. a spinning gear's faces thickened by the axial clearance it
                  needs, plus its float): no other part may enter them at any step, except the parts listed
  8. access       for each pin, screw or snap in ASSEMBLY, the finger or tool that pushes or turns it (a cylinder
                  from tool(), from the fastener out along its approach line) must reach it past every part placed
                  before it. Hardware left out of ASSEMBLY is a failure: a pin nobody can push in is not a design
  9. joints       every joint in JOINTS keeps at least its measured fit (cad/fits.py) on every side,
                  at every motion step, measured inside the joint's own region when the parts also touch elsewhere
 10. marks        every gear (GEARS) and every part flagged "phased" has an alignment mark declared in MARKS
  (6. print also reports overhangs whose support would stand on the part itself, in a pocket or under a bridge:
      support nobody can reach, or, with «On build plate only», an overhang printed over air; and pegs or posts
      printed upright thinner than Ø4, which break along the layers)
 11. seats        every part in SEATS sits fully home on its seat: pushed further along its direction, it is
                  stopped at once
 12. keep-in      every part listed in a KEEP_IN envelope stays inside a reference mesh inset by a wall (a
                  carcass shell's inner surface) within a z range: its surface is sampled and every sample must be at
                  least `inset` inside the mesh. Named exceptions are boxes where samples may be outside, each with
                  its reason and an optional bound (min_z): a keel allowed under the shell, but never below min_z
                  (base v2 chassis, 2026-11-14: 17 % of the module was outside the carcass and nothing said so)

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
                                              # or a PATH: ("body", [[0, 0, -30], [0, 4, 0]]) = lowered 30 mm, then
                                              # slid 4 mm along +Y into place (moves in mm, in the order it goes in)
                                              # a step may move parts as one body: (("motor", "pinion"), d); and
                                              # take opts: (("pinion",), d, {"bench": ["motor", "jig"],
                                              # "except": {"shaft": "press fit"}, "note": "..."}): done on the bench,
                                              # checked against the bench parts only, places nothing in the machine
                                              # PARTS[...]["bench"] = True: a jig used on the bench, not in the
                                              # machine (only assembly, integrity, print and pictures see it)
    PRINT_ORIENT = {"shaft": 4x4}             # how each part lies on the bed (default: as in its STL)
    SECTIONS = [([0, 0, 0], [1, 0, 0])]       # cut planes (point, normal) for the pictures
    PAIR_GAP = {("pin", "shaft"): 0.1}       # smallest gap for a pair, where MIN_GAP does not fit (a pin in its bore)
    KEEP_OUT = {"gear-faces": {"part": "shaft", "mesh": m, "except": ["frame"], "why": "0.8 mm axial"}}
                                              # m in the part's own frame, moves with it; "except": parts allowed in
    ACCESS = [{"at": "pin", "tool": tool("finger", [0, 0, 6], [1, 0, 0]), "why": "push the pin in by hand"}]
                                              # at: the ASSEMBLY entry it serves (a part, or a step's tuple); tool
                                              # from the fastener's outer end
                                              # outwards; "except": parts the tool may touch (the fastener itself)
    JOINTS = {("cap", "frame"): {"fit": fits.WINDOW, "where": (center, size), "why": "cap in its opening"},
              ("pin", "shaft"): {"fit": fits.STEEL}}
                                              # fit: a fits.Fit (or anything with .side); where: optional box in the
                                              # ground frame where the gap is measured (when the pair touches;
                                              # a negative fit is an interference: the parts must overlap there
                                              # elsewhere, e.g. a cap resting on its frame); "moves": True to box
                                              # the region with the first part instead
    MARKS = {"shaft": "dot on the tooth that meets the idler's dot", "idler": "dot between two teeth"}
    SEATS = {"gear": {"on": "frame", "dir": [0, 0, -1], "why": "big gear in its pocket"}}   # tol: 0.2 mm default (one layer)
    GEAR_MOTION = [(a, 0) for a in range(0, 31)]   # optional: meshing pairs checked over these steps only (one
                                              # tooth pitch, finer) instead of MOTION; every other pair over MOTION
    KEEP_IN = {"shell": {"mesh": carcass, "inset": 2.0, "z": (None, 72.5), "parts": ["module"],
                         "allow": {"keel": {"box": ((x0, y0, z0), (x1, y1, z1)), "min_z": 42.7, "why": "..."},
                                   "end": {"box": ..., "inset": 0.0, "why": "inside the shell, not its inner face"}},
                         "bodies": {"nut-1": mesh}, "why": "inside the shell's inner surface"}}
                                              # mesh: closed reference mesh (ground frame); parts placed at MOTION[0]
                                              # (WARN if a listed part moves); parts left out: every part that does
                                              # not move over MOTION; bodies: extra meshes (not parts), the same;
                                              # an allowance takes min_z, max_z or inset (WARN with none of them);
                                              # allow: boxes (first match wins), skipped or checked at their own inset;
                                              # samples: surface points per part (default 20000)
    MIN_GAP, GEAR_GAP, MIN_WALL, BED = 0.2, (0.08, 0.5), 0.8, (256, 256, 256)

Usage:
    python3 tools/cad_verify.py path/to/spec.py [--out check-result.txt] [--render images/check] [--quick]
                                [--only part1,part2] [--per-pose] [--full]

Only a summary is printed (verdict, every FAIL, a count per check, the 10 closest gaps); the full report goes to
--out, or to .verify-last.txt next to the spec. --full prints it all. Read the summary, grep the file for one part.

GROUPS = {name: [parts]} in a spec names one interface's parts, for --only <name> (check one interface, not
the whole robot).
--smoke checks the rest pose only, without the motion sweep, assembly, access and print checks: seconds, after
every small fix (always PARTIAL).
--quick skips the wall thickness and checks retention at the first motion step only: use it while iterating.
--only checks only what involves these parts (pairs with them, their retention, joints, marks): after a change to
one part, run with --only that part, and the full check once at the end.
Pairs whose relative position repeats (static parts, parts moving together) are computed once and reused, and the
results are kept between runs in .cad_verify_cache.pkl next to the spec (--no-cache to ignore it): after a change
to one part, only the pairs with that part cost time again.
Swept envelopes (the default): a part that does not move over MOTION against one that does (the shell against each
leg, fork and crankshaft) is one gap query against the moving part's swept envelope (its mesh at all its poses in
one mesh, built once per run and shared by every still part), not one overlap and one gap per step. Only a pair
whose envelope comes closer than every gap the report prints or checks (1 mm, MIN_GAP, PAIR_GAP) is scanned step by
step, so the report names its worst step exactly as before: gaps only when the envelope proves the pair never
overlaps, overlaps too when it touches. Declared contacts (ALLOWED_CONTACT) between a still and a moving part are
not computed at all (nothing about them is reported). GEARS pairs and pairs where both parts move are always
scanned step by step. The envelope results are cached like the pairs (by both parts' hashes and all the poses),
and so is how each pair ended: after a fix to the shell, a pair that came closer last time goes straight to the
step-by-step scan it needs (the envelope would only add a query), and the scan records whether it still is.
--per-pose turns the envelopes off: every pair at every step, as before. Either way each part becomes a manifold
once per run, not once per step.

--render writes assembly.png (3 views), assembly-steps.png (one panel per ASSEMBLY step: the parts already in place
in grey, the incoming part lifted out along its direction, the access tools in red) and section-N.png.

Exit code 0 when every check passes, 1 otherwise. Needs numpy, trimesh, manifold3d, rtree, matplotlib.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
import re
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

    def to_dict(self):
        """The report as data, for tools/rounds.py: the verdict, and per check its ok / WARN / FAIL counts and lines."""
        checks, sec = {}, None
        for ln in self.lines:
            if ln.startswith("== "):
                sec = checks.setdefault(re.sub(r"^\d+\s+", "", re.split(r"[:(]", ln[3:])[0].strip()),
                                        {"ok": 0, "warn": 0, "fail": 0, "fails": [], "warns": []})
            elif sec is not None:
                if ln.startswith("  ok "):
                    sec["ok"] += 1
                elif ln.startswith("  WARN"):
                    sec["warn"] += 1
                    sec["warns"].append(ln.strip()[6:])
                elif ln.startswith("  FAIL"):
                    sec["fail"] += 1
                    sec["fails"].append(ln.strip()[6:])
        verdict = self.text().splitlines()[0].split(": ", 1)[1].split(" (")[0]
        return {"verdict": verdict, "partial": self.partial, "fails": self.fails, "warns": self.warns,
                "checks": checks, "fail_lines": [ln.strip()[6:] for ln in self.lines if ln.startswith("  FAIL")],
                "warn_lines": [ln.strip()[6:] for ln in self.lines if ln.startswith("  WARN")]}

    def summary(self, full_path, n_gaps=5, width=300):
        """What is printed on screen (the full report goes to a file): the verdict, every FAIL, a count per check,
        the closest gaps. Kept short so an agent reading it does not spend its context on hundreds of ok lines."""
        out = self.text().splitlines()[:1]
        out += [ln for ln in self.lines if ln.startswith("PARTIAL CHECK")]
        counts, sec = [], None
        for ln in self.lines:
            if ln.startswith("== "):
                sec = [re.split(r"[:(]", ln[3:])[0].strip(), 0, 0, 0]
                counts.append(sec)
            elif sec is not None:
                for i, tag in ((1, "  ok "), (2, "  WARN"), (3, "  FAIL")):
                    if ln.startswith(tag):
                        sec[i] += 1
        out.append("checks: " + "; ".join(f"{s} {o} ok" + (f", {w} warn" if w else "") + (f", {f} FAIL" if f else "")
                                          for s, o, w, f in counts))
        fails = [ln for ln in self.lines if ln.startswith("  FAIL")]
        if fails:
            out += ["failures:"] + [ln if len(ln) <= width else ln[:width] + " …" for ln in fails]
        gaps = []
        for ln in self.lines:
            m = re.search(r"gap (-?[\d.]+) mm", ln)
            if m:
                gaps.append((float(m.group(1)), ln.strip()))
        if gaps:
            out += [f"closest gaps ({min(n_gaps, len(gaps))} of {len(gaps)}):"]
            out += [f"  {ln[:width]}" for _, ln in sorted(gaps)[:n_gaps]]
        out.append(f"full report ({len(self.lines)} lines, {self.warns} warnings): {full_path}  "
                   f"(grep it for one part; --full prints it all)")
        return "\n".join(out) + "\n"


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


_BASE = {}      # id(mesh) -> (mesh, its manifold): each mesh becomes a manifold once per run, not once a step


def base_manifold(m):
    hit = _BASE.get(id(m))
    if hit is None or hit[0] is not m:
        hit = _BASE[id(m)] = (m, to_manifold(m))
    return hit[1]


def placed(spec, meshes, t, bench=False, names=None):
    """Every part as a manifold at motion step t (only those in `names`, if given). Bench parts (PARTS[...]["bench"]:
    a jig or gauge used on the bench, not in the machine) only with bench=True: the motion, retention, keep-out, joint
    and access checks never see them."""
    pose = spec.poses(t) if hasattr(spec, "poses") else {}
    out = {}
    for name in spec.PARTS:
        if (spec.PARTS[name].get("bench") and not bench) or (names is not None and name not in names):
            continue
        M = pose.get(name, np.eye(4))
        out[name] = base_manifold(meshes[name]).transform(np.asarray(M, float)[:3, :])
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


def mesh_hash(m):
    """Fingerprint of a mesh's geometry: same hash, same shape (for the cache between runs)."""
    h = hashlib.md5(np.ascontiguousarray(m.vertices, dtype=np.float64).tobytes())
    h.update(np.ascontiguousarray(m.faces, dtype=np.int64).tobytes())
    return h.hexdigest()[:16]


# Results of pair computations kept between runs, next to the spec (.cad_verify_cache.pkl, not committed): a pair is
# recomputed only when one of its two meshes or their relative position changes, so after editing one part only the
# pairs with that part cost time
DISK, NEW, HASH = {}, {}, {}


def load_cache(spec_path, meshes):
    import pickle
    DISK.clear(), NEW.clear(), HASH.clear(), _ENV.clear()
    HASH.update({n: mesh_hash(m) for n, m in meshes.items()})
    f = os.path.join(os.path.dirname(os.path.abspath(spec_path)), ".cad_verify_cache.pkl")
    try:
        with open(f, "rb") as fh:
            DISK.update(pickle.load(fh))
    except (OSError, EOFError, pickle.UnpicklingError):
        pass
    return f


def save_cache(f):
    import pickle
    if not NEW:
        return
    DISK.update(NEW)
    if len(DISK) > 200000:                      # keep the file small: drop the oldest half
        for k in list(DISK)[:len(DISK) // 2]:
            del DISK[k]
    with open(f, "wb") as fh:
        pickle.dump(DISK, fh)


def scan_radius(spec, gmax):
    """How far the gap search looks: gaps beyond 1 mm (or the largest gap a pair needs) are neither reported nor
    checked, and a shorter search is much faster (a gap past it reads as the search length)."""
    return max([1.0, getattr(spec, "MIN_GAP", 0.2), gmax] + list(getattr(spec, "PAIR_GAP", {}).values())) + 0.05


def pair_wanted(spec, a, b, only, which, gears):
    g_pair = pair_key(a, b) in gears
    return involves(only, a, b) and not ((which == "gears" and not g_pair) or (which == "others" and g_pair))


def scan_pairs(spec, meshes, steps, only, gmax, which="all", skip=frozenset(), disjoint=frozenset()):
    """Overlap volume and gap of every pair of parts that come near each other, at each step:
    [(t, a, b, overlap, gap)]. A pair whose relative position repeats is computed once (and, through the disk cache,
    once across runs). which: "all", "gears" (only GEARS pairs) or "others" (every pair but GEARS). skip: pairs
    (pair_key) already settled by their swept envelope; disjoint: pairs whose envelope proved they never overlap
    (their overlap is 0 at every step: only the gap is computed)."""
    cache, hits, rows = {}, 0, []
    gears = {pair_key(*k) for k in getattr(spec, "GEARS", [])}
    radius = scan_radius(spec, gmax)
    names = [n for n in spec.PARTS if not spec.PARTS[n].get("bench")]
    todo = [(a, b) for a, b in itertools.combinations(names, 2)
            if pair_key(a, b) not in skip and pair_wanted(spec, a, b, only, which, gears)]
    need = {n for ab in todo for n in ab}
    for t in steps:
        ms = placed(spec, meshes, t, names=need)
        P = poses_at(spec, t)
        bx = {n: mbox(m) for n, m in ms.items()}
        for a, b in todo:
            if not boxes_near(bx[a], bx[b], max(1.0, gmax)):
                continue
            rk = rel_key(P[a], P[b])
            ck = (a, b, rk)
            dk = (HASH.get(a), HASH.get(b), rk, round(radius, 3))
            if ck in cache:
                v, g = cache[ck]
                hits += 1
            elif dk[0] and dk in DISK:
                v, g = cache[ck] = DISK[dk]
                hits += 1
            else:
                v = 0.0 if pair_key(a, b) in disjoint else overlap(ms[a], ms[b])
                g = 0.0 if v > EPS_VOL else ms[a].min_gap(ms[b], radius)
                cache[ck] = (v, g)
                if dk[0]:
                    NEW[dk] = (v, g)
            rows.append((t, a, b, v, g))
    return rows, len(cache), hits


# ---------------------------------------------------------------- swept envelopes
# A part that does not move over the motion, against a part that does: instead of one overlap and one gap per step,
# one gap query against the moving part's swept envelope (all its poses in one mesh). Only a pair that comes closer
# than every gap the report prints or checks, or overlaps, is scanned pose by pose, so the report names its worst
# step exactly as before.

SWEEP = True            # main() sets it False with --per-pose
_ENV = {}               # envelopes built in this run: key -> Manifold


def pose_key(M):
    return (np.round(np.asarray(M, float)[:3, :], 5) + 0.0).tobytes()


def envelope(name, mesh, poses):
    """The swept envelope of a part: its mesh at each of `poses` (4×4), concatenated into one mesh (overlapping
    copies, not a union: a gap query only needs the surfaces, and a union of 36 poses takes minutes). Built once per
    run and shared by every still part it is checked against; the query results are kept on disk (DISK) by both
    parts' hashes and the poses, so the envelope itself is not stored (it is ~6 MB a part and faster to rebuild)."""
    key = (HASH.get(name) or mesh_hash(mesh), b"".join(pose_key(P) for P in poses))
    if key not in _ENV:
        v0, f0 = np.asarray(mesh.vertices, float), np.asarray(mesh.faces, np.int64)
        V = np.vstack([v0 @ np.asarray(P, float)[:3, :3].T + np.asarray(P, float)[:3, 3] for P in poses])
        F = np.vstack([f0 + i * len(v0) for i in range(len(poses))])
        _ENV[key] = Manifold(Mesh(vert_properties=np.ascontiguousarray(V, np.float32),
                                  tri_verts=np.ascontiguousarray(F, np.uint32)))
    return _ENV[key]


def close_at(ms, mesh, Pm, radius, clear):
    """Does the moving part, at pose Pm, overlap or come closer than `clear` to the still part ms? (one step: a
    cheap probe before building an envelope for a pair that is close everywhere, a shaft in its bore)"""
    mm = base_manifold(mesh).transform(np.asarray(Pm, float)[:3, :])
    return overlap(ms, mm) > EPS_VOL or ms.min_gap(mm, radius) < clear


def sweep_pairs(spec, meshes, steps, only, gmax, which="all"):
    """Settle every pair of (a part that does not move over `steps`) × (a part that moves) with one query against
    the moving part's swept envelope. Returns (rows, skip, disjoint, stats):
      rows      one row (t, a, b, 0, gap) per settled pair: it never overlaps and its gap at every step is at least
                every gap the report prints or checks (so its step does not matter)
      skip      the pairs settled here, plus declared contacts (ALLOWED_CONTACT: nothing about them is reported)
      disjoint  pairs that never overlap but come closer: scan_pairs computes only their gap, pose by pose
    Every other such pair (an overlap, or surfaces touching) is scanned pose by pose as before, and so is a pair
    that came closer the last time it was checked (an earlier version of one of its parts; stats["learn"] lists
    them for check_motion to record how they end this time). GEARS pairs and pairs where both parts move are never
    swept."""
    gears = {pair_key(*k) for k in getattr(spec, "GEARS", [])}
    allowed = {pair_key(*k) for k in getattr(spec, "ALLOWED_CONTACT", {})}
    radius = scan_radius(spec, gmax)
    clear = radius - 0.05 + 0.01        # every gap the report prints (< 1 mm) or checks (MIN_GAP, PAIR_GAP), + 0.01
    margin = max(1.0, gmax)
    names = [n for n in spec.PARTS if not spec.PARTS[n].get("bench")]
    P = [poses_at(spec, t) for t in steps]
    keys = {n: [pose_key(Pt[n]) for Pt in P] for n in names}
    static = {n for n in names if len(set(keys[n])) == 1}
    rows, skip, disjoint = [], set(), set()
    st = {"far": 0, "settled": 0, "disjoint": 0, "scanned": 0, "allowed": 0, "cached": 0, "hinted": 0, "probed": 0,
          "learn": [], "clear": clear}
    uniq, boxes = {}, {}
    for a, b in itertools.combinations(names, 2):
        k = pair_key(a, b)
        if (a in static) == (b in static) or k in gears or not pair_wanted(spec, a, b, only, which, gears):
            continue
        if k in allowed:
            skip.add(k)
            st["allowed"] += 1
            continue
        s, m = (a, b) if a in static else (b, a)
        if m not in uniq:          # the moving part's distinct poses, in step order, with their boxes
            u = list(dict.fromkeys(keys[m]))
            first = {kk: keys[m].index(kk) for kk in u}
            uniq[m] = [(kk, P[first[kk]][m]) for kk in u]
            bm = base_manifold(meshes[m])
            boxes[m] = {kk: mbox(bm.transform(Pm[:3, :])) for kk, Pm in uniq[m]}
        ms = base_manifold(meshes[s]).transform(P[0][s][:3, :])
        bs = mbox(ms)
        near = [i for i, kk in enumerate(keys[m]) if boxes_near(boxes[m][kk], bs, margin)]
        if not near:                                    # never near: no rows, as pose by pose
            skip.add(k)
            st["far"] += 1
            continue
        dk = ("sweep", HASH.get(s), keys[s][0], HASH.get(m), hashlib.md5(b"".join(kk for kk, _ in uniq[m])).hexdigest(),
              round(radius, 3))
        last = ("sweep-last", s, m)             # how this pair ended last time, whatever the parts' versions
        if dk[1] and dk[3] and dk in DISK:
            g, nested = DISK[dk]
            st["cached"] += 1
        elif DISK.get(last) == "close" or (DISK.get(last) is None and close_at(ms, meshes[m], P[near[0]][m], radius,
                                                                                    clear)):
            # it came closer last time (the shell before this fix), or, never seen, at its first step near: the
            # envelope would only add a query to the scan step by step it needs anyway. check_motion learns from
            # the scan whether it is still close
            st["hinted" if DISK.get(last) == "close" else "probed"] += 1
            st["learn"].append((k, last))
            continue
        else:
            env = envelope(m, meshes[m], [Pm for _, Pm in uniq[m]])
            # min_gap boxes every face of its argument and looks it up in the other's tree: pass the smaller mesh
            g = env.min_gap(ms, radius) if env.num_tri() >= ms.num_tri() else ms.min_gap(env, radius)
            # surfaces apart at every pose can still overlap if one part is wholly inside the other: only possible
            # where one box holds the other; there the overlap is computed (exactly, as pose by pose)
            nested = False
            if g > 1e-3:
                bm = base_manifold(meshes[m])
                for kk, Pm in uniq[m]:
                    b_ = boxes[m][kk]
                    inside = np.all(b_[0] >= bs[0]) and np.all(b_[1] <= bs[1]) or \
                        np.all(bs[0] >= b_[0]) and np.all(bs[1] <= b_[1])
                    if inside and overlap(ms, bm.transform(Pm[:3, :])) > EPS_VOL:
                        nested = True
                        break
            if dk[1] and dk[3]:
                NEW[dk] = (g, nested)
                NEW[last] = "clear" if g > 1e-3 and not nested and g >= clear else "close"
        apart = g > 1e-3 and not nested         # surfaces at least 1 µm apart at every pose: no overlap anywhere
        if apart and g >= clear:
            skip.add(k)
            rows.append((steps[near[0]], a, b, 0.0, g))
            st["settled"] += 1
        elif apart:
            disjoint.add(k)
            st["disjoint"] += 1
        else:
            st["scanned"] += 1
    return rows, frozenset(skip), frozenset(disjoint), st


SPEC_PATH, JOBS = None, 1     # set by main(): worker processes load the spec themselves
_W = {}


def _worker_init(path):
    _W["spec"] = load_spec(path)
    _W["meshes"] = load_meshes(_W["spec"], path)
    load_cache(path, _W["meshes"])


def _worker_scan(args):
    NEW.clear()
    rows, n, hits = scan_pairs(_W["spec"], _W["meshes"], *args)
    return rows, n, hits, dict(NEW)


def scan_pairs_parallel(spec, meshes, steps, only, gmax, which="all", skip=frozenset(), disjoint=frozenset()):
    """scan_pairs split over JOBS processes, in contiguous chunks of the motion (so repeats stay in one chunk)."""
    if JOBS <= 1 or SPEC_PATH is None or len(steps) < 60:     # each process spends ~5-10 s loading the spec
        return scan_pairs(spec, meshes, steps, only, gmax, which, skip, disjoint)
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    chunks = [list(c) for c in np.array_split(np.arange(len(steps)), JOBS)]
    args = [([steps[i] for i in c], only, gmax, which, skip, disjoint) for c in chunks if len(c)]
    with ProcessPoolExecutor(JOBS, mp_context=multiprocessing.get_context("spawn"), initializer=_worker_init,
                             initargs=(SPEC_PATH,)) as ex:
        parts = list(ex.map(_worker_scan, args))
    for p in parts:
        NEW.update(p[3])
    return [r for p in parts for r in p[0]], sum(p[1] for p in parts), sum(p[2] for p in parts)


def check_motion(spec, meshes, rep, only=None, sweep=None):
    rep.head("2 motion: overlaps and gaps at every step   3 gears: backlash")
    motion = list(getattr(spec, "MOTION", [0]))
    min_gap = getattr(spec, "MIN_GAP", 0.2)
    gmin, gmax = getattr(spec, "GEAR_GAP", (0.08, 0.5))
    allowed = {pair_key(*k): v for k, v in getattr(spec, "ALLOWED_CONTACT", {}).items()}
    gears = {pair_key(*k) for k in getattr(spec, "GEARS", [])}
    pair_gap = {pair_key(*k): v for k, v in getattr(spec, "PAIR_GAP", {}).items()}
    worst_overlap, closest, gear_overlap = {}, {}, {}
    gear_gap = {g: (np.inf, -np.inf, None, None) for g in gears if involves(only, *g)}
    gear_motion = getattr(spec, "GEAR_MOTION", None)
    sweep = SWEEP if sweep is None else sweep
    # parts that do not move × parts that do: settled by the moving part's swept envelope where they stay clear
    which = "others" if gear_motion is not None else "all"
    rs, skip, disjoint, st = sweep_pairs(spec, meshes, motion, only, gmax, which) if sweep else \
        ([], frozenset(), frozenset(), None)
    if gear_motion is not None:
        # meshing pairs repeat every tooth: they are checked, finer, over GEAR_MOTION only; the rest over MOTION
        r1, n1, h1 = scan_pairs_parallel(spec, meshes, motion, only, gmax, "others", skip, disjoint)
        r2, n2, h2 = scan_pairs_parallel(spec, meshes, list(gear_motion), only, gmax, "gears")
        rows, ncache, hits = rs + r1 + r2, n1 + n2, h1 + h2
    else:
        rows, ncache, hits = scan_pairs_parallel(spec, meshes, motion, only, gmax, "all", skip, disjoint)
        rows = rs + rows
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
    if st:
        rep.info(f"swept envelopes (still part × moving part): {st['settled']} pairs clear at every step in one query"
                 f" each, {st['disjoint']} closer (gaps step by step, no overlap); scanned step by step: "
                 f"{st['scanned']} overlapping or touching, {st['hinted']} close last time, {st['probed']} close at their first step; "
                 f"{st['far']} never near, {st['allowed']} declared contacts skipped; {st['cached']} envelope results "
                 f"from the cache")
        for k, last in st["learn"]:        # a pair scanned for being close last time: is it still close?
            close = any(pair_key(a, b) == k and (v > EPS_VOL or g < st["clear"]) for _, a, b, v, g in rows)
            NEW[last] = "close" if close else "clear"
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
        if p.get("fixed") or p.get("bench") or not involves(only, name):
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
            # every pair is cut to what can touch (≈ 10× faster with a 74k-triangle body on either side, same volumes):
            # no point moves farther than `reach` (push, or tilt about the box centre), so only the neighbour within
            # `reach` of the part's box, and only the part within `reach` of the neighbour's box, can ever overlap
            reach = max(travel, np.linalg.norm(bme[1] - bme[0]) / 2 * np.radians(ttravel)) + 1.0

            def cut(m, b):
                return m ^ Manifold.cube(list(b[1] - b[0] + 2 * reach)).translate(list(b[0] - reach))

            pairs = [(cut(me, mbox(o)), cut(o, bme)) for o in ms.values() if boxes_near(bme, mbox(o), travel + 1)]
            base = [overlap(a, o) for a, o in pairs]

            def blocked(move):
                return any(overlap(move(a), o) > b0 + EPS_VOL for (a, o), b0 in zip(pairs, base))

            for d in dirs:
                if slide is not None and abs(d @ slide) > 0.98:
                    continue
                free = travel
                for s in np.arange(step, travel, step):
                    if blocked(lambda m: m.translate(list(d * s))):
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
                        if blocked(lambda m: m.transform(M[:3, :])):
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


def steps(spec):
    """ASSEMBLY normalised: one dict per step. An entry is (name, d) or (name, d, opts); name is one part or a tuple
    of parts moved in as one body (a sub-assembly: a motor with its pressed-on pinion). d is the side the part comes
    in from (a vector), or a PATH: a list of moves in mm in the order the part moves going in, e.g.
    [[0, 0, -30], [0, 4, 0]] = lowered 30 mm, then slid 4 mm along +Y into place ("path" holds the moves; "d" is
    then the side the last move comes from). opts: "bench": the parts on
    the bench in this step (the step is done off the machine: the moving body is checked against these only, and
    the step places nothing in the machine; its parts go in with a later step); "except": {part: why} the moving
    body may pass through (a press fit modelled at zero clearance); "note": what the step means."""
    out = []
    for e in getattr(spec, "ASSEMBLY", None) or []:
        names, d = e[0], e[1]
        opts = e[2] if len(e) > 2 else {}
        path = None
        if d is not None and np.ndim(d) == 2:      # a path: the moves in mm, in the order the part moves going in
            path = [np.asarray(m, float) for m in d]
            d = -path[-1]                          # d stays the side the last move comes from, as for a straight step
        names = (names,) if isinstance(names, str) else tuple(names)
        exc = opts.get("except", {})
        exc = exc if isinstance(exc, dict) else {n: "" for n in exc}
        out.append({"names": names, "d": None if d is None else np.asarray(d, float) / np.linalg.norm(d), "path": path,
                    "bench": list(opts["bench"]) if opts.get("bench") is not None else None, "except": exc,
                    "note": opts.get("note", "")})
    return out


def step_label(st):
    return " + ".join(st["names"])


def gear_partners(spec, names):
    g = getattr(spec, "GEARS", [])
    return {b for a, b in g if a in names} | {a for a, b in g if b in names}


def before_step(spec, seq, k):
    """Parts already there when step k is done: on the bench its bench parts, in the machine every part placed by
    the machine steps before it."""
    if seq[k]["bench"] is not None:
        return [n for n in seq[k]["bench"] if n not in seq[k]["names"]]
    done = []
    for st in seq[:k]:
        if st["bench"] is None:
            done += [n for n in st["names"] if n not in done]
    return done


def move_words(m):
    """A move in mm, in words: «down 30 mm», «+Y 4 mm»."""
    m = np.asarray(m, float)
    i = int(np.argmax(np.abs(m)))
    ax = "XYZ"[i]
    w = ("down" if m[i] < 0 else "up") if ax == "Z" else f"{'+' if m[i] > 0 else '-'}{ax}"
    return f"{w} {abs(m[i]):g} mm" if np.count_nonzero(np.abs(m) > 1e-9) == 1 else f"{name_dir(m)} {np.linalg.norm(m):g} mm"


def sweep_path(me, others, path):
    """Move `me` (at its place) along `path` (moves in mm, in order, ending at the place). Overlap above the one at
    the place with any of `others` = blocked. Returns (move number, mm into that move) of the first block, or None."""
    base = [overlap(me, o) for o in others]
    bme = mbox(me)
    pos = -sum(path)                          # offset of the start from the place
    for i, mv in enumerate(path):
        ln = float(np.linalg.norm(mv))
        if ln < 1e-9:
            continue
        u = mv / ln
        off = np.array([bme[0] + pos, bme[1] + pos])
        grid = np.arange(0.0 if i == 0 else 0.25, ln, 0.25).tolist() + [ln]
        near = [(o, b0, box_span(off, mbox(o), u)) for o, b0 in zip(others, base)]
        near = [(o, b0, lo, hi) for o, b0, (lo, hi) in near if hi >= 0 and lo <= ln]
        for s in grid:
            live = [(o, b0) for o, b0, lo, hi in near if lo - 0.25 <= s <= hi + 0.25]
            if not live:
                continue
            m2 = me.translate(list(pos + u * s))
            if any(overlap(m2, o) > b0 + EPS_VOL for o, b0 in live):
                return i + 1, s
        pos = pos + mv
    return None


def check_assembly(spec, meshes, rep):
    seq = steps(spec)
    rep.head("5 assembly order")
    if not seq:
        rep.warn("no ASSEMBLY order in the spec: cannot tell whether the parts can be put together")
        return
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0], bench=True)
    for k, st in enumerate(seq):
        names, d = st["names"], st["d"]
        where = " on the bench" if st["bench"] is not None else ""
        if d is None:
            if where:
                rep.info(f"{step_label(st)}: set out{where}")
            continue
        bad = [n for n in names if n not in ms]
        if bad:
            rep.fail(f"ASSEMBLY step {k + 1}: no such parts {', '.join(bad)}")
            continue
        me = ms[names[0]]
        for n in names[1:]:
            me = me + ms[n]
        skip = set(names) | set(st["except"]) | gear_partners(spec, names)
        others = [ms[n] for n in before_step(spec, seq, k) if n not in skip]
        what = step_label(st) + (" (as one body)" if len(names) > 1 else "")
        if st["path"] is not None:
            words = ", then ".join(move_words(m) for m in st["path"])
            hit = sweep_path(me, others, st["path"])
            if hit is None:
                rep.ok(f"{what} goes in: {words}{where}")
            else:
                rep.fail(f"{what} cannot go in: {words}{where}: blocked on move {hit[0]} at {hit[1]:.2f} mm")
            for n, why in st["except"].items():
                rep.info(f"{what}: not checked against {n}" + (f" ({why})" if why else ""))
            continue
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
        what = step_label(st) + (" (as one body)" if len(names) > 1 else "")
        if hit is None:
            rep.ok(f"{what} goes in from {name_dir(np.sign(d.round(3)))}{where}")
        else:
            rep.fail(f"{what} cannot go in from {name_dir(np.sign(d.round(3)))}{where}: blocked {hit:.2f} mm out")
        for n, why in st["except"].items():
            rep.info(f"{what}: not checked against {n}" + (f" ({why})" if why else ""))
    named = {n for st in seq for n in st["names"]} | {n for st in seq for n in (st["bench"] or [])}
    missing = set(spec.PARTS) - named
    hw = sorted(n for n in missing if spec.PARTS[n].get("hardware"))
    if hw:
        rep.fail(f"hardware not in ASSEMBLY (how does it go in?): {', '.join(hw)}")
    if missing - set(hw):
        rep.warn(f"not in ASSEMBLY: {', '.join(sorted(missing - set(hw)))}")
    in_machine = {n for st in seq if st["bench"] is None for n in st["names"]}
    for n in sorted(named - in_machine):
        if not spec.PARTS.get(n, {}).get("bench"):
            rep.fail(f"{n}: only in bench steps, never goes into the machine (mark it PARTS[...]['bench'] if it is "
                     f"a jig)")


def access_step(seq, at):
    """Index of the ASSEMBLY step an ACCESS entry serves: its "at" is a step's part, or its tuple of parts."""
    key = (at,) if isinstance(at, str) else tuple(at)
    for k, st in enumerate(seq):
        if st["names"] == key:
            return k
    for k, st in enumerate(seq):
        if len(key) == 1 and key[0] in st["names"]:
            return k
    return None


def check_access(spec, meshes, rep):
    rep.head("8 access: can a finger or tool reach each fastener when it goes in?")
    seq = steps(spec)
    acc = getattr(spec, "ACCESS", [])
    hw_steps = [k for k, st in enumerate(seq) if st["d"] is not None and
                any(spec.PARTS.get(n, {}).get("hardware") for n in st["names"])]
    if not acc:
        if hw_steps:
            rep.fail(f"no ACCESS entries, but fasteners go in: {', '.join(step_label(seq[k]) for k in hw_steps)}")
        else:
            rep.info("no fasteners in ASSEMBLY, nothing to reach")
        return
    served = {access_step(seq, a["at"]) for a in acc}
    for k in hw_steps:
        if k not in served:
            rep.fail(f"{step_label(seq[k])}: no ACCESS entry (which finger or tool pushes it in, and from where?)")
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0], bench=True)
    for a in acc:
        at = a["at"]
        k = access_step(seq, at)
        label = at if isinstance(at, str) else " + ".join(at)
        if k is None:
            rep.fail(f"ACCESS for {label}: not an ASSEMBLY entry")
            continue
        skip = set(a.get("except", [])) | set(seq[k]["names"])
        before = [n for n in before_step(spec, seq, k) if n not in skip]
        tm = to_manifold(a["tool"])
        hits = []
        for n in before:
            if boxes_near(mbox(tm), mbox(ms[n]), 0.5):
                v = overlap(tm, ms[n])
                if v > EPS_VOL:
                    hits.append(f"{n} ({v:.0f} mm³)")
        if hits:
            rep.fail(f"{label}: the tool ({a.get('why', '')}) hits {', '.join(hits)}")
        else:
            rep.ok(f"{label}: reachable ({a.get('why', '')})")


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
        slender = upright_slender(m)
        for z0_, z1_, c, a_ in slender[:3]:
            rep.warn(f"{name}: upright feature thinner than Ø4 ({a_:.1f} mm² section) from z {z0_:.1f} to {z1_:.1f} at "
                     f"{c} in print orientation: it breaks along the layers; make it Ø4 or more, lay it down, or use a "
                     f"steel pin")
        if trapped > 5:
            pts = m.triangles_center[idx[on_part]]
            where = [round(float(v), 1) for v in pts[np.argmax(m.area_faces[idx[on_part]])]]
            rep.warn(f"{msg}, {trapped:.0f} mm² of it over the part itself (support standing in a pocket or under a "
                     f"bridge, or printed over air with «On build plate only»; largest near {where} in print "
                     f"orientation): open it, split the part, or give the reason in the design review")
        else:
            rep.info(f"{msg}, all of it over the bed")


def upright_slender(m, min_area=np.pi * 2.0 ** 2, min_height=2.0, dz=0.4):
    """Pegs, posts and pins printed upright with a section under Ø4 (in print orientation), standing for at least
    min_height: [(z_from, z_to, [x, y], smallest area)]. They break along the layers (base v1, 2026-11-13)."""
    z0, z1 = m.bounds[0][2], m.bounds[1][2]
    zs = np.arange(z0 + dz, z1 - dz / 2, dz)
    if len(zs) < 2:
        return []
    secs = m.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=zs)
    tracks, done = [], []
    for z, sec in zip(zs, secs):
        islands = []
        if sec is not None:
            for poly in sec.polygons_full:
                if poly.area < min_area:
                    islands.append((np.array(poly.centroid.coords[0]), poly.area))
        nxt = []
        for c, a_ in islands:
            for t in tracks:
                if np.linalg.norm(t["c"] - c) < 1.0:
                    t.update(c=c, z1=z, a=min(t["a"], a_))
                    nxt.append(t)
                    break
            else:
                nxt.append({"c": c, "z0": z, "z1": z, "a": a_})
        done += [t for t in tracks if all(t is not u for u in nxt)]
        tracks = nxt
    done += tracks
    out = [(t["z0"], t["z1"], [round(float(v), 1) for v in t["c"]], t["a"]) for t in done
           if t["z1"] - t["z0"] >= min_height - 1e-9]
    return sorted(out, key=lambda x: x[3])


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
                ms = placed(spec, meshes, t, names={a, b})
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
        if need < 0:            # a designed interference (preload): the parts must overlap in the joint's region
            if g > 0:
                rep.fail(f"{label}: {g:.2f} mm apart at {t}, the fit is a {-need:.2f} mm interference")
            else:
                rep.ok(f"{label}: overlap at every step (interference {-need:.2f}{', ' + status if status else ''})")
        elif g < need - 0.01:
            rep.fail(f"{label}: {g:.2f} mm a side at {t}, measured fit needs {need:.2f}")
        else:
            rep.ok(f"{label}: ≥ {g:.2f} mm a side (fit {need:.2f}{', ' + status if status else ''})")
        if status == "assumed":
            rep.warn(f"{a} × {b}: fit not measured yet ({getattr(fit, 'source', '')}): prove it on a coupon first")


def check_seats(spec, meshes, rep, only=None):
    """A part that must sit fully home (a gear in its pocket, a block on its ledge) touches its seat: pushed further
    along its direction it is stopped at once. If it can move further, it floats above its seat as designed (base v1,
    2026-11-13: the big gear did not go fully into its pocket)."""
    seats = getattr(spec, "SEATS", {})
    if not seats:
        return
    rep.head("11 seats: does each part sit fully home?")
    motion = list(getattr(spec, "MOTION", [0]))
    ms = placed(spec, meshes, motion[0])
    for name, st in seats.items():
        if not involves(only, name, st["on"]):
            continue
        d = np.asarray(st["dir"], float) / np.linalg.norm(st["dir"])
        tol = st.get("tol", 0.2)          # one 0.2 layer: less is mesh noise, not a part off its seat (was 0.05)
        me, on = ms[name], ms[st["on"]]
        v0 = overlap(me, on)
        free = None
        for s_ in np.arange(0.02, 2.0 + 1e-9, 0.02):
            if overlap(me.translate(list(d * s_)), on) > v0 + EPS_VOL:
                free = s_ - 0.02
                break
        label = f"{name} on {st['on']} ({st.get('why', '')})"
        if free is None:
            rep.fail(f"{label}: nothing under it along {name_dir(np.sign(d.round(3)))} within 2 mm")
        elif free > tol:
            rep.fail(f"{label}: {free:.2f} mm above its seat as designed (more than {tol} mm): it is not home")
        else:
            rep.ok(f"{label}: home (≤ {max(free, 0):.2f} mm)")


def static_parts(spec):
    """Parts that do not move over MOTION (and are not bench jigs): the default KEEP_IN parts list."""
    motion = list(getattr(spec, "MOTION", [0]))
    P = [poses_at(spec, t) for t in motion]
    return [n for n, p in spec.PARTS.items() if not p.get("bench") and
            all(np.allclose(Pt[n], P[0][n], atol=1e-6) for Pt in P[1:])]


def signed_distance(env, env_key, pts):
    """trimesh's signed distance (positive inside), kept in the disk cache by envelope and points: the points come
    from a part's mesh and pose (seeded sampling), so an unchanged part costs nothing on the next run."""
    key = ("keep-in", env_key, hashlib.md5(np.ascontiguousarray(pts, dtype=np.float64).tobytes()).hexdigest()[:16])
    if key in DISK:
        return DISK[key]
    d = NEW[key] = trimesh.proximity.signed_distance(env, pts)
    return d


def check_keep_in(spec, meshes, rep, only=None):
    """Parts that must stay inside an envelope (a carcass shell inset by its wall) do: sampled surface points, signed
    distance to the reference mesh (positive inside) at least `inset`, except inside named, bounded allowances.
    The parts are placed at MOTION[0] only: a listed part that moves over MOTION gets a WARN (check it in a pose
    of its own). "parts" left out: every part that does not move over MOTION. An allowance with no bound (no
    min_z, max_z or inset) gets a WARN: it lets anything out in its box. An allowance's box is checked over its
    full height, past the entry's "z" range too (a bound above the deck is checked where it applies)."""
    envs = getattr(spec, "KEEP_IN", {})
    if not envs:
        return
    rep.head("12 keep-in: does every part stay inside its envelope?")
    motion = list(getattr(spec, "MOTION", [0]))
    pose = spec.poses(motion[0]) if hasattr(spec, "poses") else {}
    static = set(static_parts(spec))
    for en, e in envs.items():
        inset, tol = e.get("inset", 0.0), e.get("tol", 0.02)
        env_key = mesh_hash(e["mesh"])
        z0, z1 = e.get("z", (None, None))
        allow = e.get("allow", {})
        plist = e["parts"] if e.get("parts") is not None else [n for n in spec.PARTS if n in static]
        if e.get("parts") is None:
            rep.info(f"{en}: parts by default, every part that does not move over MOTION: {', '.join(plist)}")
        for an, a in allow.items():
            if all(a.get(k) is None for k in ("min_z", "max_z", "inset")):
                rep.warn(f"{en} / {an}: allowance with no bound (no min_z, max_z or inset): anything in its box may "
                         f"stand out of the envelope ({a.get('why', '')})")
        moving = [pn for pn in plist if pn not in static and pn in spec.PARTS]
        if moving:
            rep.warn(f"{en}: {', '.join(moving)} move over MOTION but are checked at MOTION[0] only")
        bodies = {pn: None for pn in plist} | dict(e.get("bodies", {}))
        for pn, body in bodies.items():
            if body is None and not involves(only, pn):
                continue
            if body is None:
                m = meshes[pn].copy()
                m.apply_transform(np.asarray(pose.get(pn, np.eye(4)), float))
            else:
                m = body
            pts, _ = trimesh.sample.sample_surface_even(m, e.get("samples", 20000), seed=1)
            pts = np.vstack([pts, m.vertices])
            keep = np.ones(len(pts), bool)
            if z0 is not None:
                keep &= pts[:, 2] >= z0
            if z1 is not None:
                keep &= pts[:, 2] <= z1
            for a in allow.values():            # an allowance's box is checked over its full height, past "z" too
                lo, hi = (np.asarray(v, float) for v in a["box"])
                keep |= np.all((pts >= lo) & (pts <= hi), axis=1)
            pts = pts[keep]
            if not len(pts):
                rep.info(f"{en}: {pn} has no surface in z {z0}..{z1}")
                continue
            free = np.zeros(len(pts), bool)
            for an, a in allow.items():
                lo, hi = (np.asarray(v, float) for v in a["box"])
                inb = np.all((pts >= lo) & (pts <= hi), axis=1) & ~free
                if not inb.any():
                    continue
                low, top = pts[inb, 2].min(), pts[inb, 2].max()
                bounds = []
                if a.get("min_z") is not None:
                    bounds.append(f"z ≥ {a['min_z']}")
                    if low < a["min_z"] - tol:
                        rep.fail(f"{en} / {an}: {pn} reaches z {low:.2f}, below its bound {a['min_z']} ({a['why']})")
                if a.get("max_z") is not None:
                    bounds.append(f"z ≤ {a['max_z']}")
                    if top > a["max_z"] + tol:
                        rep.fail(f"{en} / {an}: {pn} reaches z {top:.2f}, above its bound {a['max_z']} ({a['why']})")
                bound = f" (bound {', '.join(bounds)})" if bounds else ""
                rep.info(f"{en} / {an}: {pn} allowed outside here, {inb.sum()} samples, z {low:.2f}..{top:.2f}"
                         f"{bound}: {a['why']}")
                if a.get("inset") is not None:          # a smaller inset here instead of none
                    da = signed_distance(e["mesh"], env_key, pts[inb])
                    if (da < a["inset"] - tol).any():
                        rep.fail(f"{en} / {an}: {pn} {(da < a['inset'] - tol).sum()} samples less than "
                                 f"{a['inset']} inside (worst {a['inset'] - da.min():.2f} mm out)")
                    else:
                        rep.ok(f"{en} / {an}: {pn} ≥ {a['inset']:g} inside here (closest {da.min() - a['inset']:+.2f})")
                free |= inb
            chk = pts[~free]
            d = signed_distance(e["mesh"], env_key, chk) if len(chk) else np.zeros(0)
            bad = d < inset - tol
            label = f"{en}: {pn} ({e.get('why', '')})"
            if bad.any():
                w = int(np.argmin(d))
                rep.fail(f"{label}: {bad.sum()} of {len(chk)} samples ({100 * bad.mean():.1f} %) less than {inset} "
                         f"inside; worst {inset - d[w]:.2f} mm out at ({', '.join(f'{v:.1f}' for v in chk[w])})")
            else:
                rep.ok(f"{label}: {len(chk)} samples ≥ {inset} inside (closest {d.min() - inset:+.2f} mm)"
                       if len(chk) else f"{label}: every sample in an allowance")


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

CAD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cad")
SHARED = [os.path.join(CAD, f) for f in ("common.py", "fits.py", "motion.py")]   # imported by every build.py


def stale(stl):
    """The sources an exported STL is older than: its design's build.py (the folder that holds its out/) and the shared
    modules every build imports. Checks measure the parametric model through its export, so an export older than its
    model would measure a design that no longer exists (Morante, 2026-11-20)."""
    d = os.path.dirname(os.path.dirname(os.path.abspath(stl)))
    build = os.path.join(d, "build.py")
    if not os.path.exists(build):
        return []
    t = os.path.getmtime(stl)
    return [os.path.relpath(f, d) for f in [build] + SHARED if os.path.exists(f) and os.path.getmtime(f) > t]


def load_meshes(spec, path):
    """Every part's mesh: the STL its build.py exported (or an in-memory mesh). FAIL, before any check, if an STL is
    missing or older than the model it comes from: rebuild it with build.py."""
    base = os.path.dirname(os.path.abspath(path))
    bad = []
    for name, p in spec.PARTS.items():
        if "mesh" in p:
            continue
        f = os.path.join(base, p["stl"])
        if not os.path.exists(f):
            bad.append(f"{name}: {p['stl']} missing")
        elif stale(f):
            bad.append(f"{name}: {p['stl']} is older than {', '.join(stale(f))}")
    if bad:
        print("FAIL stale or missing STL (run build.py first):\n  " + "\n  ".join(bad))
        sys.exit(1)
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
    ap.add_argument("--out", help="write the full report here (default: .verify-last.txt next to the spec)")
    ap.add_argument("--full", action="store_true",
                    help="print the full report; by default only a summary is printed (verdict, FAILs, closest gaps)")
    ap.add_argument("--json", metavar="PATH", help="also write the report as data (for tools/rounds.py)")
    ap.add_argument("--render", metavar="DIR", help="write assembly.png and section-N.png here")
    ap.add_argument("--quick", action="store_true", help="skip wall thickness; retention at the first step only")
    ap.add_argument("--smoke", action="store_true",
                    help="seconds: the rest pose only (first MOTION step, no sweep), no wall thickness, assembly, "
                         "access or print checks; the check after every small fix (always PARTIAL)")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                    help="processes for the motion check (default: all cores; 1 to run in one process)")
    ap.add_argument("--only", help="comma-separated parts or GROUPS names from the spec: check only what involves "
                                   "them (while iterating)")
    ap.add_argument("--no-cache", action="store_true",
                    help="ignore and do not write .cad_verify_cache.pkl")
    ap.add_argument("--per-pose", action="store_true",
                    help="no swept envelopes: every pair is computed at every motion step (the old mode)")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    global SPEC_PATH, JOBS, SWEEP
    SPEC_PATH, JOBS, SWEEP = os.path.abspath(args.spec), max(1, args.jobs), not args.per_pose
    spec = load_spec(args.spec)
    if args.smoke:
        args.quick = True
        spec.MOTION = list(getattr(spec, "MOTION", [0]))[:1]
        if getattr(spec, "GEAR_MOTION", None) is not None:
            spec.GEAR_MOTION = list(spec.GEAR_MOTION)[:1]
        SWEEP = False
    meshes = load_meshes(spec, args.spec)
    cache_file = None if args.no_cache else load_cache(args.spec, meshes)
    rep = Report()
    timing = []
    groups = getattr(spec, "GROUPS", {})     # {"i7": ["drive-module", "chassis", ...]}: one interface's parts
    if only:
        only = set().union(*({*groups[o]} if o in groups else {o} for o in only))
    if only and only - set(spec.PARTS):
        sys.exit(f"--only: no such parts in the spec: {', '.join(sorted(only - set(spec.PARTS)))}")
    if args.smoke:
        rep.partial = True
        rep.lines.append("PARTIAL CHECK: smoke (rest pose only; no motion sweep, assembly, access or print checks)")
    if only:
        rep.partial = True
        rep.lines.append(f"PARTIAL CHECK: only what involves {', '.join(sorted(only))}. Run the full check before "
                         f"returning")
    try:
        run_checks(spec, meshes, rep, args, only)
    finally:
        if cache_file:              # even when a check crashes, keep what was computed
            save_cache(cache_file)
    txt = rep.text()
    full_path = args.out or os.path.join(os.path.dirname(SPEC_PATH), ".verify-last.txt")
    with open(full_path, "w") as f:
        f.write(txt)
    print(txt if args.full else rep.summary(full_path, n_gaps=3 if args.smoke else 5))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rep.to_dict(), f, indent=1, ensure_ascii=False)
    if args.render:
        render(spec, meshes, args.render)
    sys.exit(1 if rep.fails else 0)


def run_checks(spec, meshes, rep, args, only):
    timing = []
    smoke = getattr(args, "smoke", False)
    for label, fn in (("integrity", lambda: check_integrity(spec, meshes, rep, args.quick, only)),
                      ("motion", lambda: check_motion(spec, meshes, rep, only)),
                      ("retention", lambda: check_retention(spec, meshes, rep, args.quick, only)),
                      ("assembly", None if smoke else lambda: check_assembly(spec, meshes, rep)),
                      ("print", None if smoke else lambda: check_print(spec, meshes, rep)),
                      ("keep-out", lambda: check_keep_out(spec, meshes, rep, only)),
                      ("access", None if smoke else lambda: check_access(spec, meshes, rep)),
                      ("joints", lambda: check_joints(spec, meshes, rep, only)),
                      ("seats", lambda: check_seats(spec, meshes, rep, only)),
                      ("keep-in", lambda: check_keep_in(spec, meshes, rep, only)),
                      ("marks", lambda: check_marks(spec, rep, only))):
        if fn is None:
            continue
        t0 = time.perf_counter()
        fn()
        timing.append(f"{label} {time.perf_counter() - t0:.0f} s")
        print(f"[{timing[-1]}]", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
