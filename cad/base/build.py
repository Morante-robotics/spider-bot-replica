#!/usr/bin/env python3
"""Spider-Bot base v1: the carcass base made to carry the legs and drive, with a band that lifts the body.

The forks are 22 mm tall and swivel on two M3 screws, one above and one below. At the original height their top half
went into the body, which sits on the base right above the leg notches. So the body is lifted by LIFT mm and a band
(part of this base) fills the gap. The band holds the upper screw of every fork.

What this script does to ../carcass-120/spideybot_base.stl (all meshes, booleans with manifold3d):
  - keeps the bowl below the seam (z 75) and hollows it into a shell with a 2 mm deck on top
  - adds the band (the base's outline, z 75 → 75 + LIFT) and lifts the parts that go up into the body (the front
    block and the two pegs) by LIFT, with their stems made longer; the two posts and the side lips are dropped
  - builds the spine into the bowl (two walls with the journal slots, as in ../drive/spine), with a keel under the
    gears where they go below the bowl
  - cuts each fork's pocket (fork swivel + 0.6 mm, open outwards to slide fork and leg in), adds a boss under each
    fork, drills both swivel screws with a pocket for a captive nut, and cuts the path of every leg (+0.8 mm, up to 30 mm out of its pivot)
  - cuts an opening in the deck over the spine, closed by the cap (cap.stl): its tongues go down the journal slots
    and hold the crankshafts; three M3×10 screws into captive nuts

Writes base-v1.stl, cap.stl, front-block.stl and body-lifted.stl (the carcass body moved up, for the check and the
pictures). The front block is a separate part now: its stems stood over the opening the first crankshaft goes in
through. It drops in through the band after the drive and the cap are in, and stands on the deck and the cap.

Usage:
    python3 build.py
    python3 check.py            # moving parts against base, cap and body over a full turn

Needs the drive's parts (run ../drive/build.py first), trimesh, manifold3d, shapely.
"""
import os
import sys

import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = os.path.join(HERE, "..", "drive")
CARCASS = os.path.join(HERE, "..", "carcass-120")
sys.path.insert(0, DRIVE)
import build as D  # noqa: E402
import check as DC  # noqa: E402

# --- parameters (mm) -----------------------------------------------------------------------------------------
SEAM = 74.8          # top of the original base's deck, where the body sat
WALL = 2.0           # shell and deck thickness
DECK_BOT = SEAM - WALL
FORK_H = D.yoke_size()[3]
FORK_GAP = 0.6       # fork to the boss below and to the band above
SCREW_IN = 3.0       # how far each swivel screw's tip goes into the fork
SCREW_L = 10.0       # M3×10
HEAD_D, HEAD_H = 6.0, 3.2    # M3 cap head and its counterbore
NUT_AF, NUT_T = D.NUT_AF + 0.3, D.NUT_T + 0.3
HOLE = D.SCREW + D.CLR_STEEL
Z_P = 72.0           # leg pivots
FORK_TOP, FORK_BOT = Z_P + FORK_H / 2, Z_P - FORK_H / 2
# band height: the upper screw's head sits flush with the band's top
LIFT = round(FORK_TOP - SCREW_IN + SCREW_L + HEAD_H - SEAM + 0.25, 1)
TOP = SEAM + LIFT
BOSS_R = 5.5         # boss under each fork
LEG_CLR = 0.8        # room around the legs' path
CAP_CLR = 0.3        # cap in its opening
CX = D.CX
SH = D.shaft_yz()


def cyl(r, z0, z1, xy=(0, 0), n=48):
    c = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n)
    c.apply_translation([xy[0], xy[1], (z0 + z1) / 2])
    return c


def boxb(lo, hi):
    return trimesh.creation.box(bounds=[lo, hi])


def prism(poly, z0, z1):
    poly = poly.buffer(0).simplify(0.02)
    if hasattr(poly, "geoms"):
        return U(*[prism(g, z0, z1) for g in poly.geoms if g.area > 0.01])
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    if not m.is_volume:
        m.merge_vertices()
        m.fix_normals()
    m.apply_translation([0, 0, z0])
    return m


def U(*ms):
    ms = [m for m in ms if m is not None and len(m.faces)]
    return trimesh.boolean.union(ms, engine="manifold") if len(ms) > 1 else ms[0]


def S(a, *bs):
    bs = [b for b in bs if b is not None and len(b.faces)]
    return trimesh.boolean.difference([a] + bs, engine="manifold") if bs else a


def I(a, b):
    return trimesh.boolean.intersection([a, b], engine="manifold")


def export(m, path):
    """Write an STL that reads back as one solid: drop the zero-volume slivers the booleans leave behind."""
    m.export(path)
    r = trimesh.load(path)
    r.merge_vertices(digits_vertex=4)
    r = max(r.split(only_watertight=False), key=lambda p: len(p.faces))
    if not r.is_volume:
        raise RuntimeError(f"{path}: not a closed solid")
    r.export(path)
    return r


def section(m, z):
    s = m.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
    if s is None:
        return []
    p, _ = s.to_2D(to_2D=np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -z], [0, 0, 0, 1.0]]))
    return list(p.polygons_full)


def outer(m, z):
    """Outline of the largest piece of m at height z, holes filled."""
    ps = section(m, z)
    return Polygon(max(ps, key=lambda p: p.area).exterior) if ps else None


def hexagon(af, z0, z1, xy, rot=0.0):
    r = af / np.sqrt(3)
    pts = [(xy[0] + r * np.cos(rot + k * np.pi / 3), xy[1] + r * np.sin(rot + k * np.pi / 3)) for k in range(6)]
    return prism(Polygon(pts), z0, z1)


def nut_pocket(xy, z0, out):
    """Captive M3 nut at height z0 with a slot to slide it in from direction `out` (unit 2D vector)."""
    out = np.asarray(out, float) / np.linalg.norm(out)
    ang = np.arctan2(out[1], out[0])
    p = hexagon(NUT_AF, z0, z0 + NUT_T, xy, ang + np.pi / 6)        # flats facing the slot's sides
    far = np.asarray(xy) + out * 12
    n = np.array([-out[1], out[0]]) * NUT_AF / 2
    slot = Polygon([tuple(xy + n), tuple(far + n), tuple(far - n), tuple(xy - n)])
    return U(p, prism(slot, z0, z0 + NUT_T))


# --- pieces of the original base -----------------------------------------------------------------------------
def carcass():
    base = trimesh.load(os.path.join(CARCASS, "spideybot_base.stl"))
    body = trimesh.load(os.path.join(CARCASS, "spideybot_body.stl"))
    lo, hi = base.bounds
    below = I(base, boxb([lo[0] - 1, lo[1] - 1, lo[2] - 1], [hi[0] + 1, hi[1] + 1, SEAM]))
    above = I(base, boxb([lo[0] - 1, lo[1] - 1, SEAM], [hi[0] + 1, hi[1] + 1, hi[2] + 1]))
    pegs, front, stems = [], [], []
    for c in above.split(only_watertight=False):
        x0, y0, _ = c.bounds[0]
        x1, y1, z1 = c.bounds[1]
        big_front = c.volume > 20000                                   # front block, inside the body's face
        peg = (x1 - x0) < 11 and (y1 - y0) < 11 and z1 > 90             # pegs into the body's tubes
        if big_front or peg:
            stem = unary_union(section(c, SEAM + 1.0))
            c = c.copy()
            c.apply_translation([0, 0, LIFT])
            (front if big_front else pegs).append(U(c, prism(stem, SEAM, SEAM + LIFT + 1.5)))
            if big_front:
                stems.append(stem)
        # side lips (covered by the band), the two posts and the small front tabs are dropped
    body.apply_translation([0, 0, LIFT])
    return base, below, pegs, front[0], unary_union(stems), body


def cavity(base):
    """Inside of the bowl below the deck, WALL from the outside (stacked slices, 0.5 mm)."""
    slabs = []
    dz = 0.5
    for z in np.arange(base.bounds[0][2] + WALL, DECK_BOT, dz):
        a, b = outer(base, z + dz), outer(base, z - WALL)
        if a is None or b is None:
            continue
        p = a.buffer(-WALL).intersection(b.buffer(-WALL))
        if p.is_empty or p.area < 1:
            continue
        p = max(getattr(p, "geoms", [p]), key=lambda g: g.area)
        slabs.append(prism(p, z, z + dz + 0.01))
    return U(*slabs)


# --- legs and forks --------------------------------------------------------------------------------------------
def placements(step=15):
    """For every leg: list over crank angles of (leg 4×4, fork 4×4)."""
    out = {}
    for a in np.arange(0, 360, step):
        for n, f, M in DC.poses(np.radians(a)):
            if n.startswith("leg"):
                out.setdefault(n[3:], {}).setdefault("leg", []).append((f, M))
            elif n.startswith("pivot"):
                out.setdefault(n[5:], {}).setdefault("fork", []).append(M)
    return out


def inflate(pts, d):
    dirs = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]] +
                    [[sx, sy, sz] for sx in (1, -1) for sy in (1, -1) for sz in (1, -1)], float)
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    return (pts[:, None, :] + d * dirs[None]).reshape(-1, 3)


def tf(pts, M):
    return pts @ M[:3, :3].T + M[:3, 3]


def leg_path(pl):
    """Swept volume of the legs from its inner end to 30 mm out of the pivot, as hulls of consecutive positions."""
    cache, hulls = {}, []
    for key, d in pl.items():
        seq = d["leg"]
        for (f1, M1), (f2, M2) in zip(seq, seq[1:] + seq[:1]):
            if f1 not in cache:
                m = trimesh.load(os.path.join(DRIVE, f1 + ".stl"))
                m = m.slice_plane([30, 0, 0], [-1, 0, 0])
                cache[f1] = inflate(m.vertices, LEG_CLR)
            loc = cache[f1]
            p = np.vstack([tf(loc, M1), tf(loc, M2)])
            hulls.append(trimesh.convex.convex_hull(p))
    return U(*hulls)


def fork_frames(pl):
    """Per fork: pivot P, outward unit vector (mean of its swivel), and the hull of its swivel inflated."""
    fv = trimesh.load(os.path.join(DRIVE, "pivot.stl")).vertices
    out = []
    for key, d in pl.items():
        Ms = d["fork"]
        P = Ms[0][:3, 3]
        xs = np.array([M[:3, 0] for M in Ms])                    # fork X = along the leg
        u = xs[:, :2].mean(0)
        u /= np.linalg.norm(u)
        pts = np.vstack([tf(fv, M) for M in Ms])
        hull = trimesh.convex.convex_hull(inflate(pts, FORK_GAP))
        out.append(dict(key=key, P=P, u=u, hull=hull, pts=pts))
    return out


def fork_mounts(forks):
    """Added: a boss under every fork with a bracket into the bowl. Cut: the fork's pocket and the slot it slides
    in through, the two swivel screw holes, nut pockets and the upper screw's counterbore."""
    add, cut = [], []
    for f in forks:
        P, u = f["P"], f["u"]
        n = np.array([-u[1], u[0]])
        top_b, bot_b = FORK_BOT - FORK_GAP, FORK_BOT - FORK_GAP - (SCREW_L - SCREW_IN - FORK_GAP)
        boss = cyl(BOSS_R, bot_b, top_b, P[:2])
        inner = P[:2] - u * 14
        w = BOSS_R
        bracket_poly = Polygon([tuple(P[:2] + n * w), tuple(inner + n * w), tuple(inner - n * w), tuple(P[:2] - n * w)])
        add.append(U(boss, prism(bracket_poly, bot_b, top_b)))
        # pocket and the slot to slide the fork in from outside
        pts = f["pts"]
        pts_lo = inflate(pts, FORK_GAP)
        moved = pts_lo + np.array([u[0], u[1], 0]) * 16
        cut.append(trimesh.convex.convex_hull(np.vstack([pts_lo, moved])))
        # lower screw: up through the boss, nut in the middle, tip SCREW_IN into the fork
        cut.append(cyl(HOLE / 2, bot_b - 1, FORK_BOT + 0.5, P[:2]))
        cut.append(nut_pocket(P[:2], (bot_b + top_b) / 2 - NUT_T / 2, u))
        # upper screw: down through the band, nut above the fork, head in a counterbore at the band's top
        cut.append(cyl(HOLE / 2, FORK_TOP - 0.5, TOP + 1, P[:2]))
        cut.append(cyl(HEAD_D / 2 + 0.3, TOP - HEAD_H, TOP + 1, P[:2]))
        cut.append(nut_pocket(P[:2], FORK_TOP + FORK_GAP + 1.2, u))
    return add, cut


# --- spine, keel, deck opening, cap ----------------------------------------------------------------------------
def gears():
    """(y, z, tip radius) of every gear between the spine walls."""
    g = [(y, z, D.MOD * (D.SHAFT_TEETH / 2 + 1)) for y, z in SH]
    g += [(y, z, D.MOD * (n / 2 + 1)) for y, z, n in D.idlers()]
    return g


SPINE_Y0, SPINE_Y1 = SH[0][0] - 14.0, SH[-1][0] + 12.0
CAP_SCREWS = [(CX, SH[0][0] - 11.25, (0, -1)),
              (CX + 8.5, (SH[2][0] + SH[3][0]) / 2, (1, 0)), (CX - 8.5, (SH[2][0] + SH[3][0]) / 2, (-1, 0))]


def spine(shell_solid):
    """Spine walls built into the bowl, a keel under the gears, and the cap's screw bosses."""
    walls = []
    for sx in (1, -1):
        x0, x1 = sorted((CX + sx * D.WALL_IN, CX + sx * D.WALL_OUT))
        walls.append(boxb([x0, SPINE_Y0, 30], [x1, SPINE_Y1, DECK_BOT]))
    # front end block, between the walls, clear of the first gear
    walls.append(boxb([CX - D.WALL_IN - 0.01, SPINE_Y0, 30], [CX + D.WALL_IN + 0.01, SH[0][0] - D.KEEP_GAP, DECK_BOT]))
    # bosses for the cap's side screws
    for x, y, _ in CAP_SCREWS[1:]:
        walls.append(cyl(4.5, DECK_BOT - 9, DECK_BOT, (x, y)))
    keel = []
    for y, z, rt in gears():
        c = trimesh.creation.cylinder(radius=rt + 0.5 + 1.6, height=2 * D.WALL_OUT, sections=64)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([CX, y, z])
        keel.append(I(c, boxb([CX - 10, y - 20, 0], [CX + 10, y + 20, z - 2])))
    keel = U(*keel)
    spine = U(I(U(*walls), shell_solid), keel)
    cut = []
    for y, z, rt in gears():
        c = trimesh.creation.cylinder(radius=rt + 0.5, height=2 * D.WALL_IN, sections=64)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([CX, y, z])
        cut.append(c)
    for y, z in SH:
        c = trimesh.creation.cylinder(radius=(D.JOURNAL + D.CLR) / 2, height=20, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([CX, y, z])
        cut.append(c)
        cut.append(boxb([CX - 10, y - (D.JOURNAL + D.CLR) / 2, z], [CX + 10, y + (D.JOURNAL + D.CLR) / 2, DECK_BOT + 1]))
    for y, z, n in D.idlers():
        c = trimesh.creation.cylinder(radius=(D.PIN + D.CLR_STEEL) / 2, height=20, sections=32)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([CX, y, z])
        cut.append(c)
    for x, y, out in CAP_SCREWS:
        cut.append(cyl(HOLE / 2, DECK_BOT - 9.5, DECK_BOT + 1, (x, y)))
        cut.append(nut_pocket((x, y), DECK_BOT - 6, out))
    return spine, cut


def opening():
    """Deck opening over the spine: as wide as a crankshaft plus room, from the front end block to the last gear."""
    return sbox(CX - 15.0, SPINE_Y0 - 1, CX + 15.0, SH[-1][0] + 9.0)


def cap():
    """Plate that fills the deck opening, with a tongue down every journal slot and three screw holes."""
    plate = prism(opening().buffer(-CAP_CLR, join_style=2), DECK_BOT, SEAM)
    parts = [plate]
    tw = D.JOURNAL + D.CLR - CAP_CLR
    for y, z in SH:
        for sx in (1, -1):
            x0, x1 = sorted((CX + sx * D.WALL_IN, CX + sx * D.WALL_OUT))
            parts.append(boxb([x0, y - tw / 2, z], [x1, y + tw / 2, DECK_BOT + 0.01]))
    part = U(*parts)
    cut = []
    for y, z in SH:
        c = trimesh.creation.cylinder(radius=(D.JOURNAL + D.CLR) / 2, height=20, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([CX, y, z])
        cut.append(c)
    for y, z, rt in gears():                                  # the crankshaft gears turn between the tongues
        if z > 60:
            c = trimesh.creation.cylinder(radius=rt + 0.5, height=2 * D.WALL_IN, sections=64)
            c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            c.apply_translation([CX, y, z])
            cut.append(c)
    for x, y, _ in CAP_SCREWS:
        cut.append(cyl(HOLE / 2, DECK_BOT - 1, SEAM + 1, (x, y)))
    return S(part, *cut)


# --- the band ---------------------------------------------------------------------------------------------------
def band(base, forks, body_lifted, stems):
    """The base's outline (with a lobe round each fork) from the deck up to TOP, hollow inside the body's wall."""
    pts = base.vertices[base.vertices[:, 2] > SEAM - 3]
    hull2d = Polygon(pts[:, :2][ConvexHull(pts[:, :2]).vertices])
    deck = outer(base, SEAM - 0.3)
    lobes = unary_union([Point(*f["P"][:2]).buffer(BOSS_R + 1.5) for f in forks])
    out = unary_union([deck, lobes]).buffer(3, join_style=1).buffer(-3, join_style=1)
    out = out.intersection(hull2d.buffer(BOSS_R + 1.5))
    closed = deck.buffer(10, join_style=1).buffer(-10, join_style=1)        # close the notch at the front
    inside = Polygon(max(getattr(g := closed.buffer(-9.0, join_style=1), "geoms", [g]), key=lambda p: p.area).exterior)
    # open over the cap, so it can be lifted out, and round the front block's stems, so it drops in
    ring = out.difference(inside).difference(opening().buffer(0.5, join_style=2)).difference(stems.buffer(0.3))
    return S(prism(ring, SEAM - 0.5, TOP), body_lifted)


def main():
    base, below, pegs, front, stems, body = carcass()
    print(f"band: body lifted {LIFT} mm, band top at z {TOP}")
    pl = placements()
    forks = fork_frames(pl)
    shell_solid = below
    cav = cavity(base)
    sp, sp_cut = spine(shell_solid)
    add, cut = fork_mounts(forks)
    bd = band(base, forks, body, stems)
    part = U(S(below, cav), sp, bd, *pegs, *add)
    print("cutting the legs' path…")
    lp = leg_path(pl)
    part = S(part, lp, prism(opening(), DECK_BOT - 0.01, SEAM + 1), *sp_cut, *cut)
    part = export(part, os.path.join(HERE, "base-v1.stl"))
    c = export(cap(), os.path.join(HERE, "cap.stl"))
    fb = export(front, os.path.join(HERE, "front-block.stl"))
    body.export(os.path.join(HERE, "body-lifted.stl"))
    for n, m in (("base-v1", part), ("cap", c), ("front-block", fb)):
        s = m.bounds[1] - m.bounds[0]
        print(f"{n:10s} {s[0]:6.1f} × {s[1]:6.1f} × {s[2]:6.1f} mm  volume {m.volume / 1000:6.2f} cm³  "
              f"watertight {m.is_watertight}")


if __name__ == "__main__":
    main()
