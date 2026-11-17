#!/usr/bin/env python3
"""Chassis Part B1: `front-block-v2`, the face filler screwed onto the looks shell (plan design-plan-b.md rev 3.2, I8).

A mesh build (the outline is the carcass's): base v1's front block (the carcass's front block above the seam, lifted
by LIFT, its stems run down to the deck; ../base/build.py carcass()) made into a designed part:
  - foot: two pads, the stems' section left and right of the cap (|x - CX| >= shell.FB_PAD_SPLIT), exactly the outline
    the shell's LOCATOR lips are drawn round (shell.front_block_seat); between the pads the block bridges the cap
    (>= its plate + WINDOW) and the cap's front screw head (>= its top + WINDOW)
  - the body's way in: the body (carcass, lifted) at its place, slid 4 mm back and lowered from 30 mm above at +4 Y,
    grown by WINDOW + LOCATOR sideways and WINDOW down, is cut from the block. This is the plan's «step's front face
    moved back 4.5 mm» (4 + WINDOW), done on the real mesh: it also cuts what else the slide meets
  - hollow, open at the bottom: walls WALL (1.2) where the tongues' and screws' loads pass, LIGHT_WALL (0.8) where
    nothing pushes, PAD_WALL (2.0) in the foot up to the lips' top; every inside roof at 45° or a bridge <= BRIDGE wide:
    no support inside
  - 2 x M3x10 from above (plan E1) at rev 3.2's (25, -51) and (60.44, -51), inside the pads: a solid boss under each
    head (FB_PAD_T, the shell's number), a Ø6.5 access tube with a 1.2 wall from the block's top (hex key and screw
    pass), the nuts in the shell's bosses under the deck
  - the rear face (y -24) open between the loaded side columns, from 2 mm over the lips to 1.5 mm under the top
    (Morante 2026-11-16, mass lever 1): it faces the band's inside, under the body
  - hook tongues (plan C1) on the ±X faces, read on the cut block, solid roots; their L-slots are body v2's (B2)
  - the front slack box (I12, rev 3.2): between the left tube and the centre, under the eyes pocket's opening; the eyes
    JST seat at its bottom (floor 1.2 at z 88); the switch lead leaves the seat's bottom by a tunnel to the rear face
Every clearance from ../fits.py; shell numbers from shell.py (FB_SCREWS, pad split, lip, pad thickness, JST size).

    ../../.venv/bin/python front_block.py          # out/front-block-v2.stl, mass, times (--step: + .step as a mesh)
"""
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402
import shell as SH  # noqa: E402  (the shell's interface numbers: one source)

BV = SH.BV
B = SH.B
OUT = os.path.join(HERE, "out")
U, S, I, prism, cyl, boxb, section = BV.U, BV.S, BV.I, BV.prism, BV.cyl, BV.boxb, BV.section
NAME = "front-block-v2"

# ---- datums and fits ----------------------------------------------------------------------------------------------
CX, SEAM = R.CX, R.DECK_TOP
WIN, LOC, STL_ = fits.WINDOW.side, fits.LOCATOR.side, fits.STEEL.side
HOLE = fits.bore(K.SCREW, fits.STEEL)                 # 3.3
CBORE = SH.CBORE                                      # 6.5: head and hex key pass (shell's number)
RHO = SH.RHO

# ---- interface with the shell (shell.py, imported) -----------------------------------------------------------------
# plan rev 3.2 (2026-11-16): the screws moved inside the pads, (25, -51) and (60.44, -51) (mirrored about CX); rev 3.1's
# (16, -51) and (69, -51) lay 2.5 mm outside the pads' outline. Until shell.py carries them they are assumed here.
FB_SCREWS_REV32 = [(25.0, -51.0, (1, 0)), (2 * R.CX - 25.0, -51.0, (-1, 0))]
_shell_xy = [(round(x, 2), round(y, 2)) for x, y, _ in SH.FB_SCREWS]
SHELL_HAS_REV32 = _shell_xy == [(round(x, 2), round(y, 2)) for x, y, _ in FB_SCREWS_REV32]
FB_SCREWS_FULL = list(SH.FB_SCREWS) if SHELL_HAS_REV32 else FB_SCREWS_REV32
FB_SCREWS = [(x, y) for x, y, _ in FB_SCREWS_FULL]
PAD_SPLIT = SH.FB_PAD_SPLIT                           # pads where |x - CX| >= this
PAD_T = SH.FB_PAD_T                                   # head face at SEAM + PAD_T (the shell's nut height uses it)
SCREW_L = SH.FB_SCREW_L                               # M3x10
LIP_TOP = SEAM + SH.FB_LIP_H                          # 76.3: the shell's lips' top
FOOT_TOP = LIP_TOP + WIN + 0.02                       # below this the block is the pads' outline only (+ MESH_TOL)

# ---- the cap under the bridge (Part A build.py) ---------------------------------------------------------------------
CAP_TOP = B.TOP + B.CAP_T                             # 79.85
BRIDGE_Z = CAP_TOP + WIN                              # 80.35: block's underside between the pads
CAP_CLEAR_X = B.CAP_W + WIN                           # 10.5: the pads stop this far from CX (the cap's sides + WINDOW;
                                                      # shell.FB_PAD_SPLIT's 10.0 touched the cap at x 52.72)
CAP_SCREW_XY = (CX + B.SCREW_FRONT[0], B.SCREW_FRONT[1])
HEAD_TOP = CAP_TOP + K.HEAD_H                         # 82.85
HEAD_CLEAR_R = K.HEAD_D / 2 + WIN                     # 3.25 round the head, up to HEAD_TOP + WIN (83.35)
POSTS = [(x, y) for x, y, _, _ in SH.COVER_POSTS]     # crank cover posts behind the block (shell)
MESH_TOL = 0.02                                       # added to a WINDOW cut from another part's mesh (its facets)

# ---- the body's way in (plan I9) -------------------------------------------------------------------------------------
SLIDE = SH.SLIDE                                      # 4: lowered 4 mm behind its place, then slid forward
DROP = 30.0                                           # lowered from this far above
BODY_SIDE = WIN + LOC                                 # 0.7: the slide lip's play + the pads' play (plan X stack-up)
BODY_DOWN = WIN                                       # under the head, at its place
BODY_BOX = ((-5.0, -72.0, 80.0), (91.0, -18.0, 150.0))   # the body's front, round the block
BODY_STEP = 0.25                                      # body sections and slide steps

# ---- walls (plan part list; rev 3.2 mass levers) -------------------------------------------------------------------
WALL = 1.2                                            # loaded: from the tongues down to the foot
LIGHT_WALL = 0.85                                     # two lines (>= 0.8) where nothing pushes, everywhere but LOADED:
                                                      # 0.05 over the rule so the 0.5 mm slabs never leave less
LOADED_Y = (-37.0, -23.0)                             # the plate's ±X side columns carry the tongues' loads to the pads:
LOADED_DX = 8.0                                       # WALL within this of each side face, from the foot to the tongues
PAD_WALL = 2.0                                        # the foot, only up to the lips' top (Morante's lever)
DZ = 0.5                                              # slab height of the hollow
SEC_DZ = 0.25                                         # the outside's sections that set each slab's walls and roof
CAVITY_STEP = DZ                                      # each slab of the hollow within the one above grown by this: 45°
BRIDGE = 8.0                                          # or a flat inside roof this wide at most (agent rule: <= ~10)
BOSS_R = CBORE / 2 + WALL                             # 4.45: solid under each head, and the access tube's wall

# ---- hook tongues (plan C1; plan figure: 3 out, y -34..-28, z 100-103) --------------------------------------------
TONGUE_Y = (-34.0, -28.0)
TONGUE_TOP = 103.0
TONGUE_OUT = 3.0                                      # proud of the side face
TONGUE_TIP = 2.0                                      # tip height (>= 2 mm, strength rule); the underside at 45°
TONGUE_ROOT = 4.0                                     # solid behind the tongue, into the block
TONGUE_PROBE = ((TONGUE_Y[0] + TONGUE_Y[1]) / 2, TONGUE_TOP - TONGUE_TIP)   # (y, z) where the side faces are read

# ---- slack box, eyes JST seat, switch lead tunnel (plan I12; rev 3.2) ------------------------------------------------
# rev 3.1's box (x 20.5-31) is where the access tube now stands, and x 13-22.5 has no block under the body (probe: 38 %
# of the footprint, top below 100); the right pad mirrors the same tube. The box goes between the left tube and the
# centre, under the eyes pocket's opening (x >= 18), the JST seat at its bottom
JST_X, JST_Y, JST_Z = SH.JST[2] - SH.JST[0], SH.JST[3] - SH.JST[1], SH.JST[5] - SH.JST[4]   # 10 x 5.8 x 7.2 seat
SEAT_X0 = FB_SCREWS[0][0] + CBORE / 2 + WALL          # 29.45: 1.2 off the access tube
SEAT = (SEAT_X0, -56.9, SEAT_X0 + JST_Y, -56.9 + JST_X)   # x0 y0 x1 y1: the housing upright, its long side along Y
SEAT_Z0 = 88.0                                        # seat floor (plan box floor z 88), 1.2 floor under it
SLACK_GROW = 1.0                                      # the box above the seat: the seat + this, inside WALL of the outside
SLACK_FLOOR = 1.2
CABLE_W = SH.LEAD_D / 2 + 2 * WIN                     # 2.25: the switch lead's tunnel, its 2 leads (shell LEAD_D: 2 side
CABLE_H = SH.LEAD_D + 2 * WIN                         # by side, Ø1.25 each) one over the other: 2.25 wide, 3.5 tall
TUNNEL_XC = 33.0                                      # the strip's middle at its narrowest (x 30.6-35.4 at y -44): walls 1.25
TUNNEL_X = (TUNNEL_XC - CABLE_W / 2, TUNNEL_XC + CABLE_W / 2)   # from the seat's bottom back to the rear face, z >= 86
TUNNEL_Y1 = -20.0                                     # out through the rear face

# ---- marks ------------------------------------------------------------------------------------------------------------
MARK_DEPTH = K.MARK_DEPTH


def pads(stems):
    """The two pads: the stems' section either side of the cap (shell.front_block_seat draws its lips round these)."""
    out = []
    for side in (-1, 1):
        half = sbox(CX + PAD_SPLIT, -200, 400, 200) if side > 0 else sbox(-400, -200, CX - PAD_SPLIT, 200)
        p = stems.intersection(half)
        out.append(max(getattr(p, "geoms", [p]), key=lambda g: g.area))
    return out


def st_carcass():
    _base, _below, _pegs, front, stems, body = BV.carcass()
    local = I(body, boxb(*BODY_BOX))
    return front, stems, local


def swept(m, v, n):
    return SH.swept(m, v, n)


def st_body_path(local):
    """The body's way in, grown, as a stack of slabs (2D sections: seconds, where the 3D sweep took minutes). At each
    height z the block must avoid: the body's sections in [z - DZ, z + BODY_DOWN] slid 0..SLIDE back (its place and the
    slide), and at +SLIDE every body section below z + BODY_DOWN down to DROP under it (the body lowered from above);
    all grown sideways by BODY_SIDE."""
    from shapely.affinity import translate
    lo, hi = local.bounds
    q = BODY_STEP
    zs = np.arange(BODY_BOX[0][2], BODY_BOX[1][2] + q, q)
    secs = [unary_union(section(local, z)) if section(local, z) else Polygon() for z in zs]
    slabs = []
    for k, z in enumerate(np.arange(BODY_BOX[0][2], BODY_BOX[1][2], DZ)):
        near = unary_union([secs[i] for i, zz in enumerate(zs) if z - DZ - 1e-6 <= zz <= z + DZ + BODY_DOWN + 1e-6])
        below = unary_union([secs[i] for i, zz in enumerate(zs) if z - DROP <= zz <= z + DZ + BODY_DOWN + 1e-6])
        slide = unary_union([translate(near, 0, s) for s in np.arange(0, SLIDE + 1e-6, q)])
        p = unary_union([slide, translate(below, 0, SLIDE)]).buffer(BODY_SIDE)
        if not p.is_empty:
            slabs.append(prism(p, z, z + DZ + 0.01))
    return U(*slabs)


def slack_poly(front, path):
    """The slack box's outline above the seat: the seat grown by SLACK_GROW, kept WALL inside the block's outside."""
    blk = S(front, path)
    inner = None
    for z in np.arange(SEAT_Z0, SEAT_Z0 + 12.0, 2.0):
        p = unary_union(section(blk, z)).buffer(-WALL, join_style=2)
        inner = p if inner is None else inner.intersection(p)
    tube = Point(*FB_SCREWS[0]).buffer(BOSS_R)
    return sbox(*SEAT).buffer(SLACK_GROW, join_style=2).intersection(inner).difference(tube).union(sbox(*SEAT))


def st_outer(front, stems, path):
    """The block's outside: base v1's block, the foot cut to the pads, the cap's bridge, the body's way in, the
    access tubes, slack box, JST seat and lead tunnel (holes in the outside: the hollow then leaves walls round them)."""
    pl, pr = pads(stems)
    top = front.bounds[1][2] + 1
    mid = sbox(CX - CAP_CLEAR_X, -200, CX + CAP_CLEAR_X, 200)
    # a wall round each access tube above the lips (the pads' outline passes 3.4 mm from the screw), up to the block's
    # top there (lowest top round the tube: no chimney above the face)
    blk = S(front, path)
    tubes = []
    for x, y in FB_SCREWS:
        rr = CBORE / 2 + LIGHT_WALL                                              # nothing pushes on the tube
        a = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        o = np.column_stack([x + rr * np.cos(a), y + rr * np.sin(a), np.full_like(a, 300.0)])
        loc, ray, _ = blk.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(a), 1)), multiple_hits=False)
        z_top = float(loc[:, 2].min()) if len(loc) else FOOT_TOP
        tubes.append(cyl(rr, FOOT_TOP, z_top, (x, y)))
    outer = U(front, *tubes)
    cuts = [prism(mid, SEAM - 1, BRIDGE_Z),                                   # between the pads: over the cap
            cyl(HEAD_CLEAR_R, SEAM - 1, HEAD_TOP + WIN, CAP_SCREW_XY),         # the cap's front screw head
            path]
    cuts += [cyl(SH.POST_R + WIN, SEAM - 1, SH.COVER_Z0 + SH.SPIGOT_H + WIN, p) for p in POSTS]
    cuts += [cover_clear()]                                                   # the crank cover's plate + WINDOW
    foot = unary_union([pl, pr])
    lo, hi = front.bounds
    below = sbox(lo[0] - 5, lo[1] - 5, hi[0] + 5, hi[1] + 5).difference(foot)
    cuts.append(prism(below, SEAM - 1, FOOT_TOP))
    for x, y in FB_SCREWS:
        cuts.append(cyl(CBORE / 2, SEAM + PAD_T, top, (x, y)))                # access tube: key and screw
    cuts.append(prism(sbox(*SEAT), SEAT_Z0, top))                             # JST seat, then the box above it
    cuts.append(prism(slack_poly(front, path), SEAT_Z0 + JST_Z, top))
    cuts.append(boxb([TUNNEL_X[0], SEAT[1] + 1.0, SEAT_Z0], [TUNNEL_X[1], TUNNEL_Y1, SEAT_Z0 + CABLE_H]))
    return S(outer, *cuts)


def cover_clear():
    """The crank cover (out/crank-cover.stl, shell.py) grown by WINDOW: its plan outline, from the deck up to its
    plate's top (the cover goes on before the block, plan step 12b: nothing of the block may stand under its plate)."""
    cv = trimesh.load(os.path.join(OUT, "crank-cover.stl"))
    zc = SH.COVER_Z0 + SH.COVER_T / 2
    plan = unary_union(section(cv, zc)).buffer(WIN + MESH_TOL, join_style=2)
    return prism(plan, SEAM - 1.0, SH.COVER_Z0 + SH.COVER_T + WIN + MESH_TOL)


def clear_outline():
    """For the shell (its band, seat, slide lip and band skin are cut by these, as base v1's band was cut round the
    stems, base v1 band(): stems.buffer(0.3)): (foot, upper). foot: the pads grown by LOCATOR, from the deck's top to
    FOOT_TOP (the lips stand outside it); upper: the block's plan outline above the foot (out/front-block-v2.stl,
    sections every 0.1 mm up to the slide lip's top) grown by WINDOW, from LIP_TOP up (the block's overhangs start at
    FOOT_TOP = LIP_TOP + WINDOW: whatever of the shell stays under them ends at the lips' top)."""
    import shell as _sh
    m = trimesh.load(os.path.join(OUT, f"{NAME}.stl"))
    foot = unary_union(pads(BV.carcass()[4])).buffer(LOC, join_style=2)
    z1 = R.BAND_TOP + _sh.LIP_H + 1.0
    upper = unary_union([unary_union(section(m, z)) for z in np.arange(FOOT_TOP + 0.01, z1, 0.1)])
    # the rear face's opening (Morante 2026-11-16) leaves the outline as it was: the plate above still reaches y -24
    xl, xr = m.bounds[0][0] + TONGUE_OUT, m.bounds[1][0] - TONGUE_OUT
    upper = upper.union(sbox(xl + LOADED_DX, REAR_Y - REAR_OPEN_D, xr - LOADED_DX, REAR_Y))
    return foot, upper.buffer(WIN + MESH_TOL, join_style=2)


def tongue_faces(outer):
    """The side faces' x where the tongues go, read on the cut block (the body's way in trims the plate's sides)."""
    y, z = TONGUE_PROBE
    out = []
    for o, d in (([-50.0, y, z], [1.0, 0, 0]), ([150.0, y, z], [-1.0, 0, 0])):
        loc, _, _ = outer.ray.intersects_location([o], [d])
        xs = loc[:, 0]
        out.append(float(xs.min() if d[0] > 0 else xs.max()))
    return tuple(out)


def st_hollow(outer):
    """The hollow, open at the bottom: each slab the outside inset by its wall, minus the solid inserts (bosses,
    tongue roots), and within the slab above grown by CAVITY_STEP (its roof at 45°, or a bridge of that ring)."""
    lo, hi = outer.bounds
    zs = np.arange(SEAM, hi[2], DZ)

    def sec(z):
        ps = section(outer, z)
        return unary_union(ps) if ps else Polygon()

    secs = {round(z, 3): sec(z + 0.01) for z in np.arange(SEAM, hi[2] + WALL + DZ, SEC_DZ)}
    foot = sec(SEAM + 0.01)

    def at(z):
        return secs.get(round(z, 3), Polygon())

    keep = []
    faces = tongue_faces(outer)
    for x, y in FB_SCREWS:
        keep.append((SEAM - 1, SEAM + PAD_T, Point(x, y).buffer(BOSS_R)))
    for xf, sgn in zip(faces, (1, -1)):
        xa, xb = sorted((xf, xf + sgn * TONGUE_ROOT))
        keep.append((TONGUE_TOP - TONGUE_TIP - TONGUE_OUT - 1.0, TONGUE_TOP + 0.5,
                     sbox(xa, TONGUE_Y[0] - 1.0, xb, TONGUE_Y[1] + 1.0)))
    def band(z, w):
        """The outside's sections within w above and below z, intersected: inset by w, the wall is >= w across a
        sloping face and under a roof."""
        a = at(z)
        n = int(np.ceil(w / SEC_DZ))
        for k in range(-n, int(np.ceil((w + DZ) / SEC_DZ)) + 1):   # above: the slab's own top + w
            if k:
                zk = z + k * SEC_DZ
                a = a.intersection(at(zk) if zk >= SEAM else foot)
        return a

    raw = []
    for z in zs:
        w = PAD_WALL if z < LIP_TOP else WALL
        p = band(z, w).buffer(-w, join_style=2)
        if z >= LIP_TOP:                    # 0.8 where nothing pushes, 1.2 in the loaded side columns below the tongues
            light = band(z, LIGHT_WALL).buffer(-LIGHT_WALL, join_style=2)
            loaded = unary_union([sbox(xf - LOADED_DX, LOADED_Y[0], xf + LOADED_DX, LOADED_Y[1]) for xf in faces])
            p = light.difference(loaded).union(p) if z <= TONGUE_TOP + 1.0 else light
        for z0, z1, poly in keep:
            if z0 - WALL <= z <= z1:
                p = p.difference(poly.buffer(WALL))
        raw.append(p)
    cav = [None] * len(zs)
    above = Polygon()
    for k in range(len(zs) - 1, -1, -1):                            # top down: 45° roofs
        r = raw[k]
        ring = r.difference(r.buffer(-BRIDGE / 2))               # under a flat roof: a bridge <= BRIDGE wide
        c = r.intersection(unary_union([above.buffer(CAVITY_STEP), ring]))
        c = c.buffer(-0.05).buffer(0.05)                             # no slivers
        cav[k] = c
        above = c
    slabs = []
    for k, z in enumerate(zs):
        c = cav[k]
        if c.is_empty or c.area < 0.5:
            continue
        z0 = SEAM - 1.0 if k == 0 else z                            # open at the bottom
        slabs.append(prism(c, z0, z + DZ + 0.01))
    return U(*slabs)


def tongue(xf, sgn):
    """A hook tongue on the side face at x = xf (sgn = +1 on the -X face, -1 on the +X face): flat top, a TONGUE_TIP
    tip, its underside at 45° down to the face (no support), 1 mm into the solid root."""
    t = TONGUE_TOP
    xo, xi = xf - sgn * TONGUE_OUT, xf + sgn * 1.0
    prof = [(xi, t), (xo, t), (xo, t - TONGUE_TIP), (xf, t - TONGUE_TIP - TONGUE_OUT), (xi, t - TONGUE_TIP - TONGUE_OUT)]
    pts = [(x, y, z) for x, z in prof for y in TONGUE_Y]
    return trimesh.convex.convex_hull(np.array(pts))


# rear face opened (Morante 2026-11-16, mass lever 1): the skin at y -24 faces the band's inside, under the body; kept:
# the loaded side columns (LOADED_DX from each side face), a rim along the foot (the pads' rear lips locate them in +Y)
# and one under the top
REAR_Y = -24.0
REAR_OPEN_D = LIGHT_WALL + 0.15                       # the skin and a little more: the hollow behind it opens
REAR_RIM_LOW = LIP_TOP + 2.0                          # 78.3: the foot's rear wall stays to here
REAR_RIM_TOP = 1.5                                    # mm of the rear face kept under the top
SHEET = 0.45               # thinner than one hollow slab (DZ), a horizontal sheet is a slab-grid leftover: cut


def sheets(m):
    """Horizontal sheets thinner than SHEET (where the hollow's 0.5 mm slabs meet a bottom face off their grid, e.g. the
    lifted carcass block's bottom at 93.5): at each downward horizontal face's height z, material at z + 0.01 with
    nothing at z - 0.05 (air under it) and nothing at z + SHEET (air over it). Cut, they open the hollow at the bottom
    there, as everywhere else. Stepped walls and roofs are not touched: they have material over or under each step."""
    n = m.face_normals
    zf = m.triangles_center[:, 2]
    zs = np.unique(np.round(zf[n[:, 2] < -0.999], 3))
    cuts = []
    for z in zs:
        mid = unary_union(section(m, z + 0.01))
        if mid.is_empty:
            continue
        thin = mid.difference(unary_union(section(m, z + SHEET)).buffer(0.01)).difference(
            unary_union(section(m, z - 0.05)).buffer(0.01))
        thin = thin.buffer(-0.02).buffer(0.02)
        if thin.area > 0.05:
            cuts.append(prism(thin.buffer(0.05, join_style=2), z - 0.05, z + SHEET + 0.01))
    return cuts


def st_final(outer, hollow):
    xl, xr = tongue_faces(outer)
    adds = [tongue(xl, 1), tongue(xr, -1)]
    cuts = [hollow]
    for x, y in FB_SCREWS:
        cuts.append(cyl(HOLE / 2, SEAM - 1, SEAM + PAD_T + 1, (x, y)))
    m = S(U(outer, *adds), *cuts)
    top = outer.bounds[1][2]
    m = S(m, boxb([xl + LOADED_DX, REAR_Y - REAR_OPEN_D, REAR_RIM_LOW], [xr - LOADED_DX, REAR_Y + 1.0, top - REAR_RIM_TOP]))
    sh = sheets(m)
    if sh:
        print(f"cutting {len(sh)} thin sheets")
        m = S(m, *sh)
    return m


DEPS = [os.path.join(HERE, "..", f) for f in ("base/build.py", "robot.py", "fits.py", "common.py", "chassis/build.py")] + \
       [os.path.join(OUT, "crank-cover.stl")] + \
       [os.path.join(HERE, "..", "carcass-120", f) for f in ("spideybot_base.stl", "spideybot_body.stl")]


def build(st=None):
    from stage_cache import Stages
    st = st or Stages(os.path.join(OUT, ".cache"), DEPS, tag="fb")
    front, stems, local = st.run("fb-carcass", st_carcass)
    path = st.run("fb-body-path", st_body_path, local)
    outer = st.run("fb-outer", st_outer, front, stems, path)
    hollow = st.run("fb-hollow", st_hollow, outer)
    return st.run("fb-final", st_final, outer, hollow), st


def main():
    import time
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    part, st = build()
    m = export(part, os.path.join(OUT, f"{NAME}.stl"))
    st.report()
    lo, hi = m.bounds
    print(f"{NAME}: {np.round(m.bounds, 2).tolist()}  {m.volume / 1000:.2f} cm³ = {m.volume / 1000 * RHO:.1f} g "
          f"(budget 13-15)  watertight {m.is_watertight}  total {time.time() - t0:.1f} s")
    if "--step" not in sys.argv:                                     # STEP of a mesh: for Onshape viewing only, 22 s
        return
    try:
        write_step(m, os.path.join(OUT, f"{NAME}.step"))
    except Exception as e:
        print(f"STEP not written: {e}")


EXPORT_PASSES = 12
NOTCH_R = 0.15             # a pinch edge (two solids touching along a line) is notched by a cylinder this wide


def notch(a, b):
    v = b - a
    L = max(np.linalg.norm(v), 0.05)
    c = trimesh.creation.cylinder(radius=NOTCH_R, height=L + 2 * NOTCH_R, sections=8)
    d = v / L if np.linalg.norm(v) > 1e-9 else np.array([0, 0, 1.0])
    c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1.0], d))
    c.apply_translation((a + b) / 2)
    return c


def readback(path):
    r = trimesh.load(path)
    r.merge_vertices(digits_vertex=3)
    r.update_faces(r.nondegenerate_faces())
    r.remove_unreferenced_vertices()
    return r


def export(m, path):
    """As shell.export (largest solid kept: closed voids filled, slivers dropped; pinch edges notched; vertices closer
    than shell.EXPORT_TOL merged), checked on the STL as written, notching again until it reads back closed."""
    for it in range(EXPORT_PASSES):
        pieces = m.split(only_watertight=False)
        keep = max(pieces, key=lambda p: p.volume)
        dropped = sorted(round(p.volume, 1) for p in pieces if p is not keep)
        if dropped:
            print(f"pass {it}: {len(dropped)} pieces dropped or filled, {sum(dropped):.0f} mm³ in all")
        keep = SH.simplified(keep, SH.EXPORT_TOL)
        keep.export(path)
        r = readback(path)
        a, b = SH.pinch_edges(r)
        if not len(a) and r.is_watertight and r.is_volume and len(r.split(only_watertight=False)) == 1:
            r.export(path)
            return r
        print(f"pass {it}: notching {len(a)} pinch edges (r {NOTCH_R})")
        m = S(keep, *[notch(p, q) for p, q in zip(a, b)])
    raise RuntimeError(f"{path}: does not read back as one closed solid")


def write_step(m, path):
    """The STL as a STEP for Onshape: a faceted solid (each triangle a planar face, sewn, ≈ 10 s). The part is a mesh
    build, so this is its geometry, not a parametric one."""
    import build123d as bd
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS, TopoDS_Shape
    sh = TopoDS_Shape()
    StlAPI_Reader().Read(sh, os.path.join(OUT, f"{NAME}.stl"))
    sew = BRepBuilderAPI_Sewing(1e-4)
    sew.Add(sh)
    sew.Perform()
    ex, ms = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL), BRepBuilderAPI_MakeSolid()
    while ex.More():
        ms.Add(TopoDS.Shell(ex.Current()))
        ex.Next()
    sol = bd.Solid(ms.Solid())
    if abs(sol.volume - m.volume) > 0.01 * m.volume:
        raise RuntimeError(f"STEP solid {sol.volume:.0f} mm³ against the STL's {m.volume:.0f}")
    bd.export_step(sol, path)


if __name__ == "__main__":
    main()
