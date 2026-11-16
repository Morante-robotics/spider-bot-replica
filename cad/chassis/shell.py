#!/usr/bin/env python3
"""Chassis Part B1: the looks shell `chassis` (the robot's ground part, also the v0 shell, decision 8).

A mesh build, as base v1 (../base/build.py): the carcass base at 120 % hollowed, with a band that lifts the body by
LIFT and everything Part B's plan (design-plan-b.md rev 3.1, approved 2026-11-15) puts on it:
  - bowl: the carcass below the seam hollowed to WALL (1.6, mass lever), the deck 72.8-74.8 on top
  - deck A1b: solid over the crank webs' sweep (|x-CX| <= 14.8, the four shafts' y range), round the module window
    and under the front block pads, rear block, switch and the rear-left pocket; open (a ring) elsewhere
  - module window (I7): the module's top outline + WINDOW; the module's own volume + WINDOW cut from the bowl (keel
    opening, rear end), and the 2 mm bump over its rear end (decision 13)
  - 4 I7 bosses up to the module's underside, Ø3.3 holes, heads in counterbores in the bosses' bottoms
  - band: a BAND_SKIN skin on base v1's band outline, a SEAT_T seat plate under the body's wall, the slide lip (the
    body's inner outline at its place and 4 mm back, minus WINDOW: the body's X locator); the rear segment of the
    seat relieved REAR_RELIEF (the rear tab's clamp sets the body there)
  - side lips B1: the carcass's lips, notched along the legs' path (LEG_PATH)
  - fork mounts (I4) as base v1 with every gap from fits.py; an upper boss in the hollow band for each upper screw
  - rear block: floor shelf with the rear screw's hole (M3×8 at CX-9), the tab notch, a groove in the bowl for the
    head, the switch pocket (+X), the battery JST slot and the rear slack pocket (-X) on a deck bridge
  - front block: two pad lips (LOCATOR) and two nut bosses under the deck at y -51
Every clearance comes from ../fits.py; datums from ../robot.py; the module from out/drive-module.stl (Part A).

    ../../.venv/bin/python shell.py              # out/chassis.stl, prints the built mass and each stage's time
    ../../.venv/bin/python shell.py --lite       # out/chassis-lite.stl (or SHELL_LITE=1): for trying a fix
Needs out/drive-module.stl (build.py) and the legs' STLs (../legs/build.py).

Stages are cached in out/.cache/ (stage_cache.py, see build()): a change to one feature's parameter rebuilds that feature
and the last booleans (≈ 15 s), not the carcass, the legs' path or the module's way in. Deleting out/.cache/ is always
safe (a cold full build is ≈ 2 min).
"""
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402

BV = design("base")        # base v1's mesh helpers (carcass split, cavity, leg path, fork mounts)
B = design("chassis")      # Part A: I7 nuts, module rear end
OUT = os.path.join(HERE, "out")
U, S, I, prism, cyl, boxb, section, outer = BV.U, BV.S, BV.I, BV.prism, BV.cyl, BV.boxb, BV.section, BV.outer

# ---- datums and fits ----------------------------------------------------------------------------------------------
CX = R.CX
SEAM, DECK_BOT, TOP = R.DECK_TOP, R.DECK_BOT, R.BAND_TOP      # 74.8, 72.8, 93.5
WIN, LOC, STL_ = fits.WINDOW.side, fits.LOCATOR.side, fits.STEEL.side
LEG = fits.LEG_PATH.side
HOLE = fits.bore(K.SCREW, fits.STEEL)                         # 3.3
CBORE = K.HEAD_D + 2 * WIN                                    # 6.5: a screw head and the hex key pass
RHO = 1.24                                                    # PLA g/cm³ (mass_estimate.py)

# ---- mass levers (plan «Shell mass», Q8: every lever) ---------------------------------------------------------------
WALL = 1.6                 # bowl skin (plan lever: 2.0 -> 1.6, nothing pushes on it but the bosses)
BAND_SKIN = 1.2            # band wall (lever: 2.0 -> 1.2)
SEAT_T = 2.0               # seat plate under the body's wall
LIP_H, LIP_T = 3.0, 1.2    # slide lip: height above the seat, wall
LIP_Y = (-30.0, 30.0)      # the lip runs along both sides only (the face is open at the front)
REAR_RELIEF = 0.3          # seat's rear segment lowered: the tab's clamp sets the body there
REAR_SEG = (22.0, 64.0, 25.0)   # x0, x1, y0 of that segment (the skirt's x range, plan finding 4)

# ---- deck A1b (plan alternative A, Q5) ------------------------------------------------------------------------------
RING = 10.0                # deck kept as a ring this wide inside the bowl's skin
_SH_Y = [y for y, _ in R.SHAFTS]
CRANK_SWEEP = 14.0 + LEG   # |x-CX| of the crank webs' sweep (C.WALL_OUT .. crank end 13.8, rounded) + LEG_PATH
SWEEP_R = 6.01 + LEG       # webs' radius round each shaft + LEG_PATH (Part A WEB_SWEEP)
BRIDGES = [(15.0, 14.0, 33.0, 34.0),        # rear-left pocket and JST (plan rear block)
           (52.0, 25.0, 69.0, 38.0),        # switch
           (24.0, 25.0, 62.0, 40.0)]        # rear block and tab shelf

# ---- rear block (plan «Rear block layout») -----------------------------------------------------------------------------
SCREW_XY = (CX - 9.0, 37.5)                 # M3×8 from below (finding 5)
SHELF = (CX - 16.0, 33.0, CX - 2.0, 41.6, 73.0, SEAM)   # x0 y0 x1 y1 z0 z1
NOTCH = (CX - 16.0, 33.0, CX - 2.0, 60.0, SEAM, 86.0)   # tab notch: open on top and at the rear
GROOVE_R = CBORE / 2       # groove in the bowl's rear face for the head
SWITCH = (54.7, 27.5, 66.7, 36.0, SEAM, 80.8)          # switch + lever envelope (robot.SWITCH + lever 4 + WINDOW)
JST = (17.0, 26.0, 27.0, 31.8, SEAM, 82.0)
SLACK = (17.0, 16.0, 27.0, 24.8, SEAM, 81.0)   # x1: its +X wall (to 28.2) stays off the crank window (x 28.42)
POCKET_WALL = 1.2
DECK_ROOT = DECK_BOT + 0.5   # every feature on the deck starts this deep in it: the carcass's deck top is 74.7, not
                            # SEAM, in places (a post from SEAM - 0.01 floated 0.09 over it and export() dropped it)

# ---- front block (plan «Front block foot») ------------------------------------------------------------------------------
FB_SCREWS = [(25.0, -51.0, (1, 0)), (60.44, -51.0, (-1, 0))]   # (x, y, nut slot direction: towards CX). Mirrored
                           # about CX, 3.4/3.8 inside the Γ-shaped pads (coordinator 2026-11-16, from the front block
                           # designer's probe: the plan's 16 and 69 were the v1 block's bounding box, 2.4-2.5 off the pads)
FB_PAD_SPLIT = 10.0        # pads are the front block's foot left and right of |x-CX| < this (the cap)
FB_LIP_T, FB_LIP_H = 1.2, 1.5
FB_SCREW_L = 10.0
FB_PAD_T = 2.0             # front block v2's pad thickness (B1's front-block-v2)

# ---- bump (decision 13) ---------------------------------------------------------------------------------------------
BUMP_T = 2.0
FORK_ALLOW = 0.2           # fork pocket: + this on LEG_PATH (base v1's vertex inflation falls 0.15 short on diagonals)
FORK_GAP = LEG + FORK_ALLOW   # sideways: the fork's swept outline to its pocket's walls
MESH_TOL = 0.02            # added to a fit cut round another part's mesh (its facets, export's 0.01 merge)
FORK_GAP_Z = fits.TURN.side + MESH_TOL   # up and down: the fork only turns about Z, its top and bottom faces are a turning fit
                              # (coordinator 2026-11-16, option a: at FORK_GAP the fork floated 1.0 each way)
# crank window (Morante 2026-11-15, option b): the deck opens over the crank slots so the module goes in with its
# crankshafts; the crank cover closes it (it replaces Q5's solid strip)
CRANK_HALF = 13.8 + WIN    # crankshaft half width (Part A CRANK_X) + WINDOW
CRANK_WIN = (CX - CRANK_HALF, min(_SH_Y) - SWEEP_R + LEG - WIN, CX + CRANK_HALF, max(_SH_Y) + SWEEP_R - LEG + WIN)
COVER_Z0 = B.CLAMP_Z0 + B.CLAMP_T + WIN   # cover plate underside: the clamp's top + WINDOW (82.85 + 0.5; was written from the motor envelope, which rose 0.1 with the clutch)
COVER_T = 1.6
COVER_Y = (-23.5, 32.3)    # the front block covers ahead of y -24; the rear stops at the bowl's inner wall
COVER_HALF = CRANK_HALF + 1.0
COVER_POSTS = [(CX - 20.0, 9.0, "screw", (1, 0)),    # y 9: 1.3 clear of the rear slack pocket; nut in from +X
                (CX + 20.0, -19.0, "screw", (0, 1)),   # nut in from +Y: the only clear way out at this post   # on the deck kept round the front block's stems
               (CX - 20.0, -20.0, "spigot", None)]   # on the deck top, where the deck survives the legs' path cut
POST_R = 4.5
SPIGOT_D, SPIGOT_H = 5.0, 1.5    # locates the cover (LOCATOR): a cover is never located by its screws alone
COVER_SCREW_L = 10.0
# clamp notch (Morante 2026-11-15): seat ring and slide lip cut over the clamp's end so it drops in from above
CLAMP_NOTCH = (CX + 30.0, 5.0, 19.0)  # x0, y0, y1: the seat's overhang reaches over the clamp from x ≈ 78 (quick check)
# motor leads (I12): clips on the deck, the leads' path in verify.py
LEAD_D = 2.5               # two 26 AWG leads side by side
CLIPS = [(69.5, None)]     # clip 1 on the shell, at the leads' run (LEAD_Y); a clip at x 74 came out floating
LEAD_Z = 81.6              # the leads' run: over the motor's KEEP_OUT (its top + 3 = 81.05), through clip 1 and the
                           # cover's eye, then down to the switch's pins
LEAD_Y = 22.6              # 0.65 in front of the cradle's front wall, 0.57 clear of the motor's KEEP_OUT (y 20.18)
CLIPS = [(x, LEAD_Y if y is None else y) for x, y in CLIPS]
# switch on the crank cover (coordinator 2026-11-16, option b): the cover carries its cradle (floor, walls, the top pad
# that retains it from above); the switch slides in from the open +X end on the bench, its lever out through the
# cradle's rear wall towards the band's lever window, its pins out through the front wall's slot. In the robot the
# shell's stop rib closes the open end. Leg 4R sweeps under the plan's switch place up to z 75.0 (the leg path cut,
# probe p12): the cradle's floor starts above it, so the switch stands 1.7 higher than the plan's 74.8
CRADLE_FLOOR = (75.2, 0.8)          # underside z (leg path top 75.0 + 0.2), thickness (nothing pushes down on it)
SW_Z0 = CRADLE_FLOOR[0] + CRADLE_FLOOR[1] + WIN
SW_LEVER = (3.0, 2.5, 2.0)          # lever x, y (out of the body), z (catalogue; redrawn once measured)
SW_LEVER_TIP = 35.21 - WIN          # the band's inner face over the lever's x range above the switch relief (z > 85.8,
                                    # probe): the lever passes it when the cover is lifted. Recessed 1.7-2.4 from the
                                    # rear face (36.4-37.1): reached through the window with a fingernail or a pen tip
_SW_Y0 = SW_LEVER_TIP - SW_LEVER[1] - R.SWITCH[1]
SW_BODY = (54.7, _SW_Y0, 54.7 + R.SWITCH[0], _SW_Y0 + R.SWITCH[1], SW_Z0, SW_Z0 + R.SWITCH[2])   # x0 y0 x1 y1 z0 z1
SW_TRAVEL = 1.5                     # lever travel either side of centre
SW_PINS = (5.0, 2.0, 0.6)           # pin row x, y (forwards out of the body), z (catalogue; redrawn once measured)
CRADLE_T = 1.2                      # walls and floor (the lever's push is sideways)
SW_RIB_T = 2.0                      # the shell's stop rib at the cradle's open end (a tab: >= 2), WINDOW off the cover
REAR_FACE_Y = 34.84         # the carcass's rear face at CX (Part A Y1 note): the cover's rear lip is flush with it
REAR_LIP_T = 1.2
DRIVE_CLEAR = (CX - 10.5, B.Y0 - 0.5, CX + 10.5, 33.0)   # x0 y0 x1 y1: nothing of the shell above the deck over the
                          # module, cap and clamp (they go in from above); a leftover of the band outline stood here
SWEEP_CHORD = 0.3          # leg path cut: + this on LEG_PATH (10° hull steps fell 0.15 short in the B1 check)
I7_UNDER_HEAD = 1.4       # boss left between an I7 head's counterbore and the module (in compression only)
CBORE_MOUTH = 11.0        # counterbores start this far under the bowl's bottom on their axis: screw 2's mouth stayed
                          # closed on the bowl's slope from 6.0
STOCK_M3 = (6.0, 8.0, 10.0, 12.0, 16.0, 20.0)   # stock M3 socket head lengths (hardware.md)


def mesh_module():
    return trimesh.load(os.path.join(OUT, "drive-module.stl"))


def swept(m, v, n):
    """The union of m moved by k·v for k = 0..n, in log2(n) booleans: each union doubles the span already covered (the
    same set as the n + 1 copies at once, at a fraction of the cost: a 31-copy union of the module group took 110 s)."""
    v = np.asarray(v, float)
    acc, span = m, 0                                       # acc covers the moves 0..span
    while span < n:
        s = min(span + 1, n - span)
        c = acc.copy()
        c.apply_translation(v * s)
        acc, span = U(acc, c), span + s
    return acc


def grid(m, d, axes):
    """m moved to every point of {-d, 0, d} along each of `axes` (a Minkowski sum with that cube), one axis at a time."""
    for ax in axes:
        e = np.zeros(3)
        e[ax] = d
        c = m.copy()
        c.apply_translation(-e)
        m = swept(c, e, 2)
    return m


def inflated(m, d):
    """m grown by at least d in every direction: m at the 27 points of {-d, 0, d}³ (a cube's Minkowski sum: corners
    and edges included, axis moves alone left the corners touching)."""
    return grid(m, d, (0, 1, 2))


def inflated_xy(m, d):
    """m grown sideways by d (the 9 points of {-d, 0, d}² in XY): clears a part's sides, keeps what is under it."""
    return grid(m, d, (0, 1))


def boss_clear(boss, module, dz=0.5):
    """A boss that carries the module from below, cut so the module comes straight down onto it: the module's local
    piece grown sideways by WINDOW and swept upwards (no boss material above any module ledge)."""
    lo, hi = boss.bounds
    local = I(module, boxb([lo[0] - 2, lo[1] - 2, lo[2] - 1], [hi[0] + 2, hi[1] + 2, hi[2] + 1]))
    if not len(local.faces):
        return boss
    side = inflated_xy(local, WIN)
    return S(boss, swept(side, [0, 0, dz], int(round(30 / dz))))


def ray_z(mesh, x, y, up=True):
    o = [[x, y, 0.0 if up else 200.0]]
    loc, _, _ = mesh.ray.intersects_location(o, [[0, 0, 1.0 if up else -1.0]])
    loc = np.asarray(loc).reshape(-1, 3)
    return (loc[:, 2].min() if up else loc[:, 2].max()) if len(loc) else None


def body_interior(body):
    """The lifted body's inside at its seat (z TOP + 0.2): its outline minus its wall, the largest piece."""
    ps = section(body, TOP + 0.2)
    mat = unary_union(ps)
    inside = mat.convex_hull.difference(mat)       # the section is a C (the face is open): hull minus the wall
    return max(getattr(inside, "geoms", [inside]), key=lambda g: g.area)


def band_outline(base, forks):
    """Base v1's band outline: the deck outline with a lobe round each fork, inside the hull."""
    from scipy.spatial import ConvexHull
    pts = base.vertices[base.vertices[:, 2] > SEAM - 3]
    hull2d = Polygon(pts[:, :2][ConvexHull(pts[:, :2]).vertices])
    deck = outer(base, SEAM - 0.3)
    lobes = unary_union([Point(*f["P"][:2]).buffer(BV.BOSS_R + 1.5) for f in forks])
    out = unary_union([deck, lobes]).buffer(3, join_style=1).buffer(-3, join_style=1)
    return out.intersection(hull2d.buffer(BV.BOSS_R + 1.5)), deck


def i7_bosses(base, module):
    """(add, cut, report) for the 4 I7 screws: boss from the bowl's outside up to the module's underside."""
    add, cut, rep = [], [], []
    for (x, y, nz, _) in B.I7_NUTS:
        px, py = CX + x, y
        z_out = ray_z(base, px, py, up=True)              # bowl's outer bottom
        # module's underside beside the hole (on the axis the ray would run up the screw hole)
        r = HOLE / 2 + 0.8
        z_mod = min(z for z in (ray_z(module, px + dx, py + dy, up=True) for dx, dy in
                                ((r, 0), (-r, 0), (0, r), (0, -r))) if z is not None)
        add.append(cyl(CBORE / 2 + 1.25, z_out, z_mod, (px, py)))
        cut.append(cyl(HOLE / 2, z_out - 1, z_mod + 0.5, (px, py)))
        # a stock screw, never cut: the shortest whose tip lands between the nut's top (full thread) and the hole's
        # end (README I7 rule), the counterbore depth set to make it so, with ≥ I7_UNDER_HEAD of boss above the head
        nut_top = nz + K.NUT_T
        tip_max = nut_top + (B.I7_TIP_V if x == B.I7_NUTS[1][0] else B.I7_TIP)
        d_max = z_mod - z_out - I7_UNDER_HEAD                # a deep counterbore is fine (Ø6.5: head and hex key)
        for length in STOCK_M3:
            lo, hi = nut_top - length - z_out, tip_max - length - z_out      # head-face depths that work
            if hi >= 0 and lo <= d_max:
                depth = min(hi, d_max)
                break
        else:
            raise RuntimeError(f"I7 at x {x}: no stock M3 fits")
        if depth > 0:
            cut.append(cyl(CBORE / 2, z_out - CBORE_MOUTH, z_out + depth, (px, py)))   # mouth open on the sloping bowl
        head = z_out + depth                               # head's bearing face
        rep.append(dict(x=x, y=y, z_out=z_out, z_mod=z_mod, head=head, length=length, nut=(nz, nz + K.NUT_T)))
    return add, cut, rep


def rear_block():
    add, cut = [], []
    x0, y0, x1, y1, z0, z1 = SHELF
    add.append(boxb([x0, y0, z0], [x1, y1, z1]))
    cut.append(cyl(HOLE / 2, z0 - 1, z1 + 1, SCREW_XY))
    cut.append(boxb(NOTCH[:2] + (NOTCH[4],), NOTCH[2:4] + (NOTCH[5],)))
    cut.append(cyl(GROOVE_R, 45.0, z0, SCREW_XY))                          # head's path behind the bowl
    for bx, lever in ((SWITCH, True), (JST, False), (SLACK, False)):
        bx0, by0, bx1, by1, bz0, bz1 = bx
        w = POCKET_WALL
        if not lever:                                                      # the switch's walls are its cradle's
            add.append(boxb([bx0 - w, by0 - w, DECK_ROOT], [bx1 + w, by1 + w, bz1]))
        cut.append(boxb([bx0, by0, bz0], [bx1, by1, bz1 + 5]))              # open on top (retainer, plug, loop)
        if lever:                                                          # lever window out of the rear face, at
            xc = (bx0 + bx1) / 2                                           # the switch's height on its cradle
            zl = (SW_BODY[4] + SW_BODY[5]) / 2
            cut.append(boxb([xc - 3.0, by0, zl - 1.5], [xc + 3.0, by1 + 6.0, zl + 1.5]))
    add.append(stop_rib())
    return add, cut


def nut_pocket(xy, z0, out):
    """Captive M3 nut at z0, slid in along `out`: base v1's nut_pocket() with its hexagon turned 30° to the slot, so a
    corner points along the slot and the flats lie on the slot's sides (a nut can only slide in that way). Base v1's
    hexagon had a flat across the slot's end: the nut stopped 0.28 short of the screw's axis (0.8-0.95 mm³ of every
    nut mesh in the walls, hidden by an allowed contact)."""
    out = np.asarray(out, float) / np.linalg.norm(out)
    ang = np.arctan2(out[1], out[0])
    p = BV.hexagon(BV.NUT_AF, z0, z0 + BV.NUT_T, xy, ang)
    far = np.asarray(xy) + out * 12
    n = np.array([-out[1], out[0]]) * BV.NUT_AF / 2
    slot = Polygon([tuple(xy + n), tuple(far + n), tuple(far - n), tuple(xy - n)])
    return U(p, prism(slot, z0, z0 + BV.NUT_T))


def front_block_seat(stems, base):
    add, cut = [], []
    for side in (-1, 1):
        half = sbox(CX + FB_PAD_SPLIT, -200, 400, 200) if side > 0 else sbox(-400, -200, CX - FB_PAD_SPLIT, 200)
        pad = stems.intersection(half)
        if pad.is_empty:
            continue
        ring = pad.buffer(LOC + FB_LIP_T, join_style=2).difference(pad.buffer(LOC, join_style=2))
        add.append(prism(ring.intersection(outer(base, SEAM - 0.3)), DECK_ROOT, SEAM + FB_LIP_H))
    for x, y, d in FB_SCREWS:
        tip = SEAM + FB_PAD_T - FB_SCREW_L
        nut_z = tip + 0.5
        add.append(cyl(CBORE / 2 + 1.25, nut_z - 1.2, DECK_BOT + 0.01, (x, y)))
        cut.append(cyl(HOLE / 2, tip - 0.5, SEAM + 1, (x, y)))
        cut.append(nut_pocket(np.array([x, y]), nut_z, d))
    return add, cut


def bump(module):
    """2 mm cover over the module's rear end where it reaches the carcass's rear face (decision 13)."""
    s = module.section(plane_origin=(0, B.Y1 - 0.3, 0), plane_normal=(0, 1, 0))
    v = s.vertices
    x0, x1, z0 = v[:, 0].min(), v[:, 0].max(), v[:, 2].min()
    g = WIN + BUMP_T
    return boxb([x0 - g, B.Y1 - 4.0, z0 - g], [x1 + g, B.Y1 + g, SEAM])


def revolved(m, y, z, grow):
    """The volume a part sweeps turning a full turn about the X axis through (y, z), grown by `grow`: a solid of
    revolution of its largest radius at each x (exact for a full turn, and cheap)."""
    pts = np.vstack([m.vertices, m.sample(30000)])
    x = pts[:, 0]
    r = np.hypot(pts[:, 1] - y, pts[:, 2] - z)
    edges = np.arange(x.min() - grow, x.max() + grow + 0.25, 0.25)
    prof = []
    for x0, x1 in zip(edges[:-1], edges[1:]):
        k = (x >= x0 - grow) & (x < x1 + grow)
        if k.any():
            prof.append((r[k].max() + grow, x0, x1))
    poly = [(0.0, prof[0][1])] + [q for rr, a, b in prof for q in ((rr, a), (rr, b))] + [(0.0, prof[-1][2])]
    poly = [q for i, q in enumerate(poly) if i == 0 or np.hypot(q[0] - poly[i - 1][0], q[1] - poly[i - 1][1]) > 1e-6]
    sol = trimesh.creation.revolve(np.array(poly), sections=96)
    sol.merge_vertices()
    sol.update_faces(sol.nondegenerate_faces())
    sol.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(sol)
    M = np.eye(4)
    M[:3, :3] = np.column_stack([[0, 1, 0], [0, 0, 1], [1, 0, 0]])   # revolve's axis Z -> X
    sol.apply_transform(M)
    sol.apply_translation([0, y, z])
    return sol


def drive_envelope():
    """Everything the module carries (Part A's spec, verify.py): the static parts grown by WINDOW in every direction,
    the crankshafts (LEG_PATH), idlers and pinion (WINDOW) as solids of revolution of a full turn. The bowl and deck
    open round them (keel, keeper, the motor half through the deck, cap and clamp over the deck)."""
    import verify as A
    static = ("cap", "motor-clamp", "pin-keeper", "n20", "n20-shaft", "keeper-screw", "keeper-nut", "cap-screw",
              "cap-nut", "shared-screw", "shared-nut", "clamp-screw", "clamp-nut", "pin-1", "pin-2", "pin-3")

    def mesh(n):
        p = A.PARTS[n]
        return p["mesh"].copy() if "mesh" in p else trimesh.load(os.path.join(HERE, p["stl"]))
    out = [inflated(mesh(n), WIN) for n in static]
    P = A.poses((0, 0.0, 0.0))
    axes = {f"crankshaft-{i + 1}": (R.SHAFTS[i], LEG) for i in range(4)}
    axes.update({n: ((R.IDLERS[k][0], R.IDLERS[k][1]), WIN) for k, n in enumerate(["idler-1", "idler-2", "idler-3-v2"])})
    axes["pinion"] = ((R.MOTOR_AXIS[1], R.MOTOR_AXIS[2]), WIN)
    for n, ((y, z), g) in axes.items():
        m = mesh(n)
        m.apply_transform(P[n])
        out.append(revolved(m, y, z, g))
    return U(*out)


def module_path(module, dz=1.0):
    """The module's way in, with everything that goes in with it (train, cap, keeper, pins, nuts): grown sideways by
    WINDOW, swept 30 mm up from its place (it drops in from above as one sub-assembly, plan step 10). Cut from the shell: the band's rear wall over its rear end and the bowl's rear lip over its
    keel stood in the way (quick check, 2026-11-16)."""
    import verify as A
    group = [module]
    P = A.poses((0, 0.0, 0.0))
    for n in ("idler-1", "idler-2", "idler-3-v2", "pin-1", "pin-2", "pin-3", "pin-keeper", "keeper-screw", "keeper-nut",
              "crankshaft-1", "crankshaft-2", "crankshaft-3", "crankshaft-4", "cap", "cap-screw", "cap-nut",
              "shared-nut", "clamp-nut"):                 # the whole sub-assembly that goes in (verify.py MODULE_GROUP)
        p = A.PARTS[n]
        m = p["mesh"].copy() if "mesh" in p else trimesh.load(os.path.join(HERE, p["stl"]))
        m.apply_transform(P.get(n, np.eye(4)))
        group.append(m)
    side = inflated_xy(U(*group), WIN)
    return swept(side, [0, 0, dz], int(round(30 / dz)))


def rear_slot():
    """The slot module_path() leaves in the band's rear wall over the module's rear end: x range, wall y, z range."""
    m = mesh_module()
    s = m.section(plane_origin=(0, B.Y1 - 0.3, 0), plane_normal=(0, 1, 0))
    x0, x1 = s.vertices[:, 0].min() - WIN, s.vertices[:, 0].max() + WIN
    return x0, x1


def crank_cover():
    """The crank cover (Morante 2026-11-15, option b): a plate over the crank window, on 3 posts on the deck (2 with
    captive nuts for M3×10 from above, 1 with a spigot that locates it), a hole round the shared screw's head."""
    from shapely.geometry import box as sb
    plate = sb(CX - COVER_HALF, COVER_Y[0], CX + COVER_HALF, COVER_Y[1])
    for x, y, kind, _ in COVER_POSTS:
        plate = plate.union(Point(x, y).buffer(POST_R + 1.0)).union(
            sb(min(x, CX), y - POST_R, max(x, CX), y + POST_R))
    # rear lip: closes the slot the module's way in leaves in the band's rear wall (flush with the bowl's rear face)
    sx0, sx1 = rear_slot()
    lip_x = (sx0 + WIN, sx1 - WIN)
    plate = plate.union(sb(lip_x[0], COVER_Y[1] - 1.0, lip_x[1], REAR_FACE_Y))
    c_add, c_cut = cradle()
    plate = plate.union(cradle_plan())
    m = U(prism(plate, COVER_Z0, COVER_Z0 + COVER_T),
          boxb([lip_x[0], REAR_FACE_Y - REAR_LIP_T, SEAM + WIN], [lip_x[1], REAR_FACE_Y, COVER_Z0 + 0.01]), *c_add)
    cut = [cyl(CBORE / 2, COVER_Z0 - 1, COVER_Z0 + COVER_T + 1, (CX + B.SCREW_SHARED[0], R.MOTOR_AXIS[1]))] + c_cut
    for x, y, kind, _ in COVER_POSTS:
        if kind == "screw":
            cut.append(cyl(HOLE / 2, COVER_Z0 - 1, COVER_Z0 + COVER_T + 1, (x, y)))
        else:
            cut.append(cyl(fits.bore(SPIGOT_D, fits.LOCATOR) / 2, COVER_Z0 - 1, COVER_Z0 + COVER_T + 1, (x, y)))
    # FRONT arrow, 0.5 deep in the top face (printed top up: no support)
    arrow = Polygon([(CX + 6, -14), (CX + 3, -20), (CX + 9, -20)])
    cut.append(prism(arrow, COVER_Z0 + COVER_T - 0.5, COVER_Z0 + COVER_T + 1))
    return S(m, *cut)


def cradle_box():
    """The cradle's outside: x0 y0 x1 y1 z0 (floor's underside) z1 (the plate's underside)."""
    x0, y0, x1, y1, _, _ = SW_BODY
    return (x0 - WIN - CRADLE_T, y0 - WIN - CRADLE_T, x1, y1 + WIN + CRADLE_T, CRADLE_FLOOR[0], COVER_Z0)   # +X: flush
                                    # with the switch's end, so the shell's rib is WINDOW off both


def cradle_plan():
    """The cover plate's extension over the cradle."""
    from shapely.geometry import box as sb
    cx0, cy0, cx1, cy1, _, _ = cradle_box()
    return sb(cx0, cy0, cx1, cy1)


def stop_rib():
    """The shell's rib at the cradle's open +X end, WINDOW off the cover, from the band's rear wall forwards: it stops
    the switch at +X in the robot (the cover goes on from above beside it)."""
    x0, y0, x1, y1, z0, z1 = SW_BODY
    rx = cradle_box()[2] + WIN
    return boxb([rx, y0 - WIN, CRADLE_FLOOR[0]], [rx + SW_RIB_T, 40.0, z1 + WIN + 2.0])


def cradle():
    """The switch's cradle under the cover plate: floor, -X wall, front wall with the pins' slot, rear wall with the
    lever's slot (both slots open to +X, the switch slides in from there), the top pad down to the switch (the
    retainer from above), the leads' eye. (add, cut)."""
    x0, y0, x1, y1, z0, z1 = SW_BODY
    cx0, cy0, cx1, cy1, cz0, cz1 = cradle_box()
    xc = (x0 + x1) / 2
    lx, ly, lz = SW_LEVER
    zl = (z0 + z1) / 2
    add = [boxb([cx0, cy0, cz0], [cx1, cy1, cz1 + 0.01])]
    # the leads' eye: a block hanging from the plate in front of the front wall, a hole along X (leads threaded
    # through it before they are soldered to the pins), so lifting the cover lifts the switch with its leads
    er = LEAD_D / 2 + WIN
    ex0, ex1 = x1 - 4.2, x1 - 0.7       # clear of the leads' drop to the pins (x 60.4); it carries only their weight
    add.append(boxb([ex0, LEAD_Y - er - CRADLE_T, LEAD_Z - er - CRADLE_T], [ex1, cy0 + 0.01, cz1 + 0.01]))
    cut = [boxb([x0 - WIN, y0 - WIN, z0 - WIN], [cx1 + 30, y1 + WIN, z1 + WIN]),              # the switch, in from +X
           boxb([xc - lx / 2 - SW_TRAVEL - WIN, y1 - 1, zl - lz / 2 - WIN], [cx1 + 30, cy1 + 1, zl + lz / 2 + WIN]),
           boxb([xc - SW_PINS[0] / 2 - WIN, cy0 - 1, zl - 1.5], [cx1 + 30, y0 + 1, zl + 1.5]),
           trimesh.creation.cylinder(radius=er, height=ex1 - ex0 + 2.0, sections=24,
                                     transform=trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0],
                                                                                       [0, 0, 0])).apply_translation(
               [(ex0 + ex1) / 2, LEAD_Y, LEAD_Z])]
    return add, cut


def switch_mesh():
    """The SS12D00 (catalogue sizes, robot.SWITCH): body, lever at mid travel, the pin row; for verify.py."""
    x0, y0, x1, y1, z0, z1 = SW_BODY
    xc, zl = (x0 + x1) / 2, (z0 + z1) / 2
    lx, ly, lz = SW_LEVER
    px, py, pz = SW_PINS
    return U(boxb([x0, y0, z0], [x1, y1, z1]), boxb([xc - lx / 2, y1 - 0.01, zl - lz / 2], [xc + lx / 2, y1 + ly, zl + lz / 2]),
             boxb([xc - px / 2, y0 - py, zl - pz / 2], [xc + px / 2, y0 + 0.01, zl + pz / 2]))


def cradle_clear():
    """Cut from the shell: the cradle, the stop boss and the eye grown by WINDOW (the deck opens under them)."""
    add, _ = cradle()
    # and the deck strip left between the crank window, the module window and the cradle: an island nothing stands on
    # (export() dropped it, 44 mm³)
    island = boxb([CRANK_WIN[2] - 0.5, 15.0, DECK_BOT - 1.0], [62.0, cradle_box()[1] + 0.5, SEAM + 1.0])
    return [inflated(a, WIN) for a in add] + [island]


def cover_posts():
    add, cut = [], []
    for x, y, kind, d in COVER_POSTS:
        add.append(cyl(POST_R, DECK_ROOT, COVER_Z0, (x, y)))
        if kind == "screw":
            tip = COVER_Z0 + COVER_T - COVER_SCREW_L
            cut.append(cyl(HOLE / 2, tip - 0.5, COVER_Z0 + 1, (x, y)))
            nz = COVER_Z0 - 1.2 - BV.NUT_T                 # nut 1.2 under the post's top
            cut.append(nut_pocket(np.array([x, y]), nz, d))
        else:
            add.append(cyl(SPIGOT_D / 2, COVER_Z0 - 0.01, COVER_Z0 + SPIGOT_H, (x, y)))
    return add, cut


def clips():
    """Two clips for the motor leads on the deck, a slot open at the top (WINDOW round the leads)."""
    add, cut = [], []
    w = LEAD_D / 2 + WIN
    for x, y in CLIPS:
        add.append(boxb([x - 2.0, y - w - 1.2, DECK_ROOT], [x + 2.0, y + w + 1.2, LEAD_Z + 2.0]))
        cut.append(boxb([x - 3.0, y - w, LEAD_Z - w], [x + 3.0, y + w, LEAD_Z + 3.0]))
    return add, cut


FRONT_ARROW = (CX - 16.0, -47.0)   # arrow centre, tip to -Y: the seat spans y -56 to -39 here (probe on the STL)


def shell_marks(forks, out, inside, fb_upper):
    """FRONT arrow on the band's seat at the front, and the fork number in dots (1-4, front to rear) beside each upper
    screw on the band top: 0.5 deep, on the face printed on the bed."""
    seat = out.buffer(-(BAND_SKIN + 0.4)).difference(sbox(*DRIVE_CLEAR)).difference(fb_upper.buffer(0.6))

    def arrow(ax, ay):
        return Polygon([(ax, ay - 3.0), (ax - 2.5, ay + 3.0), (ax + 2.5, ay + 3.0)])
    # the arrow on the seat nearest FRONT_ARROW, clear of the front block (it covers the seat at the front) and of
    # DRIVE_CLEAR (at CX it was in air)
    spots = sorted(((x, y) for x in np.arange(CX - 45, CX + 45.1, 0.5) for y in np.arange(-60, -20.1, 0.5)),
                   key=lambda q: np.hypot(q[0] - FRONT_ARROW[0], q[1] - FRONT_ARROW[1]))
    ax, ay = next(q for q in spots if seat.contains(arrow(*q).buffer(0.6)))
    print(f"FRONT arrow at x {ax:.1f}, y {ay:.1f}")
    cut = [prism(arrow(ax, ay), TOP - 0.5, TOP + LIP_H + 1)]
    slide = inside.intersection(Polygon(np.asarray(inside.exterior.coords) + [0, SLIDE])).buffer(-WIN)
    free = out.buffer(-(BAND_SKIN + 0.4)).difference(slide.buffer(0.6)).difference(
        sbox(CLAMP_NOTCH[0], CLAMP_NOTCH[1], 400, CLAMP_NOTCH[2])).difference(
        sbox(*DRIVE_CLEAR))
    for f in forks:                       # the first row of dots wholly on the seat (inboard across, else a row away
                                          # from the screw sideways or radially):
        n = int(f["key"][0]) + 1          # inboard, fork 4's row ran under the slide lip and was closed over
        P, u = f["P"][:2], f["u"]
        t = np.array([-u[1], u[0]])
        r = CBORE / 2 + 2.0
        rows = [[P - u * r + t * (k - (n - 1) / 2) * 2.0 for k in range(n)]] + \
               [[P + v * (CBORE / 2 + 1.6 + 2.0 * k) for k in range(n)] for v in (-t, t, -u, u)]   # or a row going away from it
        for dots in rows:
            if all(free.contains(Point(*d).buffer(K.MARK_D / 2 + 0.6)) for d in dots):
                break
        else:
            raise RuntimeError(f"fork {f['key']}: no room on the seat for its {n} dots")
        cut += [cyl(K.MARK_D / 2, TOP - K.MARK_DEPTH, TOP + 1, tuple(d)) for d in dots]
    return cut


# ---- the build, in cached stages (agent rule «Fast iteration»; stage_cache.py) -----------------------------------------
# full: the part that is printed (out/chassis.stl). lite (SHELL_LITE=1 or --lite): for trying a fix, out/chassis-lite.stl:
# the body decimated (102k -> 23k faces, within 0.5 mm: not for judging the skirt's gap), the legs swept every 30°, the
# module's way in, the drive envelope and the I7 bosses shared with full (the same stages, read from out/.cache/shared)
# path_dz: the module path's copies must overlap, so the step stays under the group's thinnest feature in Z (a 0.23 mm
# skin at the module's rear end: at 1.0 the bump survived in the gaps between copies and blocked the module 1.25 mm out)
MODES = {"full": dict(leg_step=10, body_tol=None, path_dz=0.2, boss_dz=0.5),
         "lite": dict(leg_step=30, body_tol=0.5, path_dz=0.2, boss_dz=0.5)}
DEPS = [os.path.join(HERE, "..", f) for f in ("base/build.py", "legs/build.py", "crankshafts/build.py", "robot.py",
                                               "fits.py", "common.py", "chassis/build.py", "chassis/verify.py")] + \
       [os.path.join(HERE, "..", "carcass-120", f) for f in ("spideybot_base.stl", "spideybot_body.stl")] + \
       [os.path.join(OUT, f + ".stl") for f in ("drive-module", "cap", "motor-clamp", "pinion", "idler-3-v2",
                                                 "pin-keeper")] + \
       [os.path.join(HERE, "..", "crankshafts", "out", f"{n}.stl") for n in
        ("crankshaft-1", "crankshaft-2", "crankshaft-3", "crankshaft-4", "idler-1", "idler-2")] + \
       [os.path.join(HERE, "..", "legs", "out", f"{n}.stl") for n in
        ("pivot", "leg-front-left", "leg-front-right", "leg-middle-left", "leg-middle-right", "leg-rear-left",
         "leg-rear-right")]


def simplified(m, tol):
    """m decimated by manifold (stays a closed solid), every vertex within tol of the original surface."""
    import manifold3d as mf
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                             tri_verts=np.asarray(m.faces, np.uint32))).simplify(tol).to_mesh()
    return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)


def set_base_globals():
    """Base v1's helpers read these module values: set once, before any stage's key is made (a key reads them)."""
    BV.WALL, BV.DECK_BOT = WALL, DECK_BOT              # cavity()
    BV.FORK_GAP = FORK_GAP                             # fork pocket and boss gaps: the swivel moves (LEG_PATH)
    BV.LEG_CLR = LEG + SWEEP_CHORD                    # leg_path(): the 10° steps are joined by hulls, chord allowance


def fork_frames_cached():
    """The forks' frames (pivot P, outward u: the nut slots' direction) from the full build's cache (verify.py)."""
    from stage_cache import Stages
    set_base_globals()
    st = Stages(os.path.join(OUT, ".cache"), DEPS, tag="full")
    return st.run("forks", st_forks, st.run("placements", st_placements, MODES["full"]["leg_step"]))


def st_carcass(body_tol):
    base, below, _pegs, _front, stems, body = BV.carcass()
    if body_tol:
        body = simplified(body, body_tol)
    return base, below, stems, body


def st_placements(step):
    return BV.placements(step=step)


def st_forks(pl):
    return BV.fork_frames(pl)


def st_bowl(base, below):
    return S(below, BV.cavity(base))


def st_outline(base, forks, body):
    out, deck = band_outline(base, forks)
    return out, deck, body_interior(body)


def st_band(out, inside, body):
    slide = inside.intersection(Polygon(np.asarray(inside.exterior.coords) + [0, SLIDE, ])).buffer(-WIN)
    slide = max(getattr(slide, "geoms", [slide]), key=lambda g: g.area)
    lip = slide.difference(slide.buffer(-LIP_T)).intersection(sbox(-400, LIP_Y[0], 400, LIP_Y[1]))
    seat = out.difference(slide.buffer(-LIP_T))
    band = U(prism(out.difference(out.buffer(-BAND_SKIN)), SEAM - 0.5, TOP),
             prism(seat, TOP - SEAT_T, TOP), prism(lip, TOP - 0.01, TOP + LIP_H))
    band = S(band, boxb([REAR_SEG[0], REAR_SEG[2], TOP - REAR_RELIEF], [REAR_SEG[1], 80, TOP + 1]))
    x1 = out.bounds[2] - BAND_SKIN                      # clamp notch: seat and lip cut over the clamp's footprint
    band = S(band, boxb([CLAMP_NOTCH[0], CLAMP_NOTCH[1], TOP - SEAT_T - 0.5], [x1, CLAMP_NOTCH[2], TOP + LIP_H + 1]))
    for v in ([0, 0, 0], [0, -WIN, 0], [0, 0, -WIN]):                    # the skirt: WINDOW off the band
        b = body.copy()
        b.apply_translation(v)
        band = S(band, b)
    return band


def st_lips(base, out):
    """Side lips B1: the carcass's lips (they stand at their original height, inside the band's z range), inside the
    band's skin (no edge-on touch)."""
    lo, hi = base.bounds
    above = I(base, boxb([lo[0] - 1, lo[1] - 1, SEAM], [hi[0] + 1, hi[1] + 1, hi[2] + 1]))
    lips = [c for c in above.split(only_watertight=False) if c.bounds[1][2] < 90 and c.volume > 1000]
    return [I(c, prism(out.buffer(-0.05), SEAM - 1, TOP)) for c in lips]


def grown_fork(pts, gxy, gz, n=16):
    """The fork's swept points grown by gxy sideways (n directions round Z, so the diagonals are not short as base
    v1's 14-direction inflate was) and by gz up and down: the points of an elliptic cylinder round each point."""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.column_stack([np.cos(a), np.sin(a), np.zeros(n)]) * gxy / np.cos(np.pi / n)   # circumscribed polygon
    offs = np.vstack([ring + [0, 0, gz], ring - [0, 0, gz]])
    return (pts[:, None, :] + offs[None]).reshape(-1, 3)


def st_fork_mounts(forks):
    """Fork mounts as base v1's fork_mounts() (boss and bracket under each fork, the pocket and its slide-in slot, two
    swivel screws, nut pockets, the upper screw's counterbore) with the shell's own gaps: FORK_GAP sideways (the leg
    path), FORK_GAP_Z up and down (a turning fit), the corrected nut_pocket(); and an upper boss in the hollow band."""
    add, cut = [], []
    gz = FORK_GAP_Z
    for f in forks:
        P, u = f["P"], f["u"]
        n = np.array([-u[1], u[0]])
        top_b, bot_b = BV.FORK_BOT - gz, BV.FORK_BOT - (BV.SCREW_L - BV.SCREW_IN)
        inner = P[:2] - u * 14
        w = BV.BOSS_R
        bracket = Polygon([tuple(P[:2] + n * w), tuple(inner + n * w), tuple(inner - n * w), tuple(P[:2] - n * w)])
        add.append(U(cyl(BV.BOSS_R, bot_b, top_b, P[:2]), prism(bracket, bot_b, top_b)))
        add.append(cyl(BV.BOSS_R, BV.FORK_TOP + gz, TOP, P[:2]))
        g = grown_fork(f["pts"], FORK_GAP, gz)
        cut.append(trimesh.convex.convex_hull(np.vstack([g, g + np.array([u[0], u[1], 0]) * 16])))
        cut.append(cyl(HOLE / 2, bot_b - 1, BV.FORK_BOT + 0.5, P[:2]))
        cut.append(nut_pocket(P[:2], (bot_b + top_b) / 2 - BV.NUT_T / 2, u))
        cut.append(cyl(HOLE / 2, BV.FORK_TOP - 0.5, TOP + 1, P[:2]))
        cut.append(cyl(BV.HEAD_D / 2 + 0.3, TOP - BV.HEAD_H, TOP + 1, P[:2]))
        cut.append(nut_pocket(P[:2], BV.FORK_TOP + gz + 1.2, u))
    return add, cut


def st_i7(base, module, boss_dz):
    i_add, i_cut, i7 = i7_bosses(base, module)
    return [boss_clear(b, module, boss_dz) for b in i_add], i_cut, i7    # the bosses carry the module, WINDOW off it


def st_leg_path(pl):
    return BV.leg_path(pl)


def st_module_inflated(module):
    return inflated(module, WIN)


def st_openings(deck, stems, module):
    """Deck A1b: the ring's inside opened except the strip over the cranks, the module window's surround and bridges;
    the crank window, the drive's clear space over the deck, the module window."""
    keep = unary_union([sbox(CRANK_WIN[0] - 4.0, CRANK_WIN[1] - 3.0, CRANK_WIN[2] + 4.0, CRANK_WIN[3])] +
                       [Point(x, y).buffer(POST_R + 2.0) for x, y, _, _ in COVER_POSTS] +
                       [Point(x, y).buffer(5.0) for x, y in CLIPS] + [sbox(*b) for b in BRIDGES] +
                       [Point(x, y).buffer(CBORE / 2 + 4) for x, y, _ in FB_SCREWS] +
                       [p.buffer(3.0) for p in [stems]])
    opening = deck.buffer(-(WALL + RING)).difference(keep)
    window = unary_union(section(module, SEAM - 0.8)).buffer(WIN, join_style=2)
    return [prism(sbox(*CRANK_WIN), DECK_BOT - 1.0, SEAM + 1.0),
            prism(sbox(*DRIVE_CLEAR), SEAM + 0.3, TOP + LIP_H + 1.0),
            prism(window, DECK_BOT - 1.0, SEAM + 1.0), prism(opening, DECK_BOT - 0.5, SEAM + 0.5)]


def st_fb_clear(fb_key):
    """The band, seat, slide lip and band skin cut round front block v2, as base v1's band round the stems: its foot
    (pads + LOCATOR, deck top to FOOT_TOP) and its outline above (+ WINDOW, from the lips' top up). The outlines come
    from front_block.clear_outline() (one source); fb_key is the hash of out/front-block-v2.stl and front_block.py, so
    this stage re-keys when the block changes. The front block lips stay: they stand outside the foot."""
    import front_block as FB
    foot, upper = FB.clear_outline()
    # the block's screw bores and counterbores are holes in its outline: filled, or the band stands in them as loose
    # columns (export() dropped 106 mm³ of them)
    upper = unary_union([Polygon(g.exterior) for g in getattr(upper, "geoms", [upper])])
    return [prism(foot, SEAM, FB.FOOT_TOP), prism(upper, FB.LIP_TOP, TOP + LIP_H + 2.0)], upper


def file_key(*paths):
    import hashlib
    h = hashlib.sha1()
    for p in paths:
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def st_final(carved, i_add, i_cut):
    return S(U(carved, *i_add), *i_cut)                 # I7 bosses up to the module's underside (it rests on them)


def build(mode="full", st=None):
    """The raw boolean result and the I7 report. Stages whose inputs and parameters did not change come from
    out/.cache/<mode>; the slow, stable cuts (legs' path, module, its way in, drive envelope) are one cached union, and
    the often-edited features are applied after it."""
    from stage_cache import Stages
    set_base_globals()
    o = MODES[mode]
    st = st or Stages(os.path.join(OUT, ".cache"), DEPS, tag=mode)
    module = mesh_module()
    base, below, stems, body = st.run("carcass", st_carcass, o["body_tol"])
    pl = st.run("placements", st_placements, o["leg_step"])
    forks = st.run("forks", st_forks, pl)
    bowl = st.run("bowl", st_bowl, base, below)
    out, deck, inside = st.run("outline", st_outline, base, forks, body)
    band = st.run("band", st_band, out, inside, body)
    lips = st.run("lips", st_lips, base, out)
    f_add, f_cut = st.run("fork-mounts", st_fork_mounts, forks)
    i_add, i_cut, i7 = st.run("i7", st_i7, base, module, o["boss_dz"], shared=True)
    r_add, r_cut = st.run("rear-block", rear_block)
    fb_add, fb_cut = st.run("front-block", front_block_seat, stems, base)
    c_add, c_cut = st.run("cover-posts", cover_posts)
    c_cut = c_cut + st.run("cradle-clear", cradle_clear)
    l_add, l_cut = st.run("clips", clips)
    bmp = st.run("bump", bump, module)
    holes = st.run("openings", st_openings, deck, stems, module)
    fb_clear, fb_upper = st.run("fb-clear", st_fb_clear, file_key(os.path.join(OUT, "front-block-v2.stl"),
                                                         os.path.join(HERE, "front_block.py")), shared=True)
    marks = st.run("marks", shell_marks, forks, out, inside, fb_upper)
    slow = st.run("cuts-slow", U, st.run("leg-path", st_leg_path, pl),
                  st.run("module-grown", st_module_inflated, module, shared=True),
                  st.run("module-path", module_path, module, o["path_dz"], shared=True),
                  st.run("drive-envelope", drive_envelope, shared=True))
    big = st.run("adds-big", U, bowl, band, *lips, *f_add)
    solid = st.run("adds", U, big, *r_add, *fb_add, bmp, *c_add, *l_add)
    carved = st.run("carved", S, solid, slow, *f_cut, *r_cut, *fb_cut, *c_cut, *l_cut, *marks, *holes, *fb_clear)
    part = st.run("final", st_final, carved, i_add, i_cut)
    return part, i7


SLIDE = 4.0                # the body is lowered this far behind its place, then slid forward (decision: plan I9)


PINCH_R = 0.1              # a pinch edge (two solids touching along a line) is notched by a cylinder this wide
EXPORT_TOL = 0.01          # mm: well under a layer, over the read-back merge (0.001)
EXPORT_PASSES = 8          # notch passes: a notch can leave a new pinch edge next to it (the 0.2 mm module path steps)


def pinch_edges(m):
    """Edges shared by 4 faces once the STL is read back (vertices merged to 0.001 mm): two solids touching on a line."""
    r = m.copy()
    r.merge_vertices(digits_vertex=3)
    r.update_faces(r.nondegenerate_faces())
    r.remove_unreferenced_vertices()
    u, c = np.unique(r.edges_sorted, axis=0, return_counts=True)
    bad = u[c > 2]
    return r.vertices[bad[:, 0]], r.vertices[bad[:, 1]]


def notch(a, b):
    v = b - a
    L = max(np.linalg.norm(v), 0.05)
    c = trimesh.creation.cylinder(radius=PINCH_R, height=L + 2 * PINCH_R, sections=8)
    z = np.array([0, 0, 1.0])
    d = v / L if np.linalg.norm(v) > 1e-9 else z
    c.apply_transform(trimesh.geometry.align_vectors(z, d))
    c.apply_translation((a + b) / 2)
    return c


def export(m, path):
    """Keep the largest solid of the boolean result (loose slivers the cuts sever are reported and dropped), notch any
    pinch edge, and write an STL that reads back as one closed solid (vertices merged to 0.001 mm)."""
    for it in range(EXPORT_PASSES):
        pieces = m.split(only_watertight=False)
        keep = max(pieces, key=lambda p: p.volume)
        dropped = sorted(round(p.volume, 1) for p in pieces if p is not keep)
        if dropped:
            print(f"dropped {len(dropped)} loose pieces, {sum(dropped):.0f} mm³ in all (largest {dropped[-1]} mm³)")
        a, b = pinch_edges(keep)
        if not len(a):
            break
        print(f"notching {len(a)} pinch edges (r {PINCH_R})")
        m = S(keep, *[notch(p, q) for p, q in zip(a, b)])
    keep = simplified(keep, EXPORT_TOL)                 # vertices closer than this merged by manifold (stays closed):
    keep.export(path)                                   # the STL's float32 and the 0.001 merge then close nothing
    r = trimesh.load(path)
    r.merge_vertices(digits_vertex=3)
    r.update_faces(r.nondegenerate_faces())
    r.remove_unreferenced_vertices()
    ps = r.split(only_watertight=False)
    r = max(ps, key=lambda p: abs(p.volume))
    if not (r.is_watertight and r.is_volume):
        raise RuntimeError(f"{path}: does not read back as one closed solid ({len(ps)} pieces)")
    r.export(path)
    return r


def main():
    import argparse
    import time
    from stage_cache import Stages
    ap = argparse.ArgumentParser()
    ap.add_argument("--lite", action="store_true", help="decimated carcass, coarse sweeps: out/chassis-lite.stl")
    lite = ap.parse_args().lite or os.environ.get("SHELL_LITE") == "1"
    mode = "lite" if lite else "full"
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    st = Stages(os.path.join(OUT, ".cache"), DEPS, tag=mode)
    part, i7 = build(mode, st)
    name = "chassis-lite" if lite else "chassis"
    part.export(os.path.join(OUT, f"{name}-raw.ply"))   # the boolean result, for re-cleaning without a rebuild
    t1 = time.time()
    m = export(part, os.path.join(OUT, f"{name}.stl"))
    t_clean = time.time() - t1
    cv = export(st.run("crank-cover", crank_cover, shared=True), os.path.join(OUT, "crank-cover.stl"))
    st.prune()
    st.report()
    print(f"  {'clean (export)':<16} {t_clean:6.1f} s\n  total {time.time() - t0:.1f} s ({mode})")
    print(f"crank-cover: {cv.volume / 1000:.2f} cm³ = {cv.volume / 1000 * RHO:.1f} g")
    print(f"{name}: {np.round(m.bounds, 1).tolist()}  volume {m.volume / 1000:.2f} cm³ = {m.volume / 1000 * RHO:.1f} g "
          f"(solid; budget 86)  watertight {m.is_watertight}  raw {part.volume / 1000:.3f} cm³")
    print("I7 screws (x from CX, y): bowl outside z, module underside z, head face z, stock screw, tip:")
    for r in i7:
        print(f"  {r['x']:+6.2f} {r['y']:7.2f}: {r['z_out']:.2f}  {r['z_mod']:.2f}  {r['head']:.2f}  M3×{r['length']:g}  "
              f"tip {r['head'] + r['length']:.2f} (nut {r['nut'][0]:.1f}-{r['nut'][1]:.1f})")


if __name__ == "__main__":
    main()
