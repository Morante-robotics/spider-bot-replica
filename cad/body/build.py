#!/usr/bin/env python3
"""body: jenscolt's top shell (spideybot_body.stl) rebuilt as parameters.

    ../../.venv/bin/python build.py            # out/body.stl (coarse) + out/body.step
    ../../.venv/bin/python build.py --fine     # finer STL
    ../../.venv/bin/python build.py --sweep    # also S 0.65, wall 0.8x / 1.2x, section scale 0.8x / 1.2x

Frame: the reference's (mm, S = 1), mirror plane x = CX, front -y, rim at the bottom (z = Z_RIM), top +z.
Structure:
- outer skin: a loft of horizontal superellipse sections along z (the spine is the vertical line x = CX, y = 0);
  8 control sections of 5 numbers (half-width a along x, front and back half-lengths bf / bb along -y / +y,
  front and back exponents nf / nb), interpolated (PCHIP) along z to the built sections;
- wall: an inner skin lofted from the same control table, each meridian eroded by WALL (inner_rows), cut from the
  outer one and open at the rim, so the outer form and the wall thickness are separate parameters (an OCCT offset
  of the loft hangs for minutes);
- details, each a named feature placed on the skin by its own numbers: eye block with the two big eye bores,
  the knurled big-eye rings, the nose plate between them, the two small eye tubes with rings, the chin arch, the
  two screw bosses, the rear tab, the panel-line grooves on the top.
Every number's source is the probe named next to it (scratch probes on the reference mesh, never read here).
"""
import argparse
import os
import sys
import time

import numpy as np
from scipy.interpolate import PchipInterpolator
from build123d import (Axis, Box, Cylinder, Face, Location, Plane, Pos, Rot, Solid, Spline, Torus, Wire,
                       export_step, export_stl, extrude, loft, Polygon)
from OCP.BRep import BRep_Tool
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Pnt, gp_Trsf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
STL_TOL = {False: (0.08, 0.3), True: (0.02, 0.15)}

# ---------------------------------------------------------------- parameters (mm, reference frame, S = 1)
S = 1.0
CX = 35.6            # mirror plane x (mesh bounds -12.4 .. 83.6, centre)
Z_RIM = 62.3         # rim, bottom of the outer skin (p5: lowest hit 1.5-4 mm inside the outer ring: 62.3)
WALL = 4.6           # wall, normal to the skin (p3: horizontal ray wall 4.3-6.0 at +-x / +y)

# outer skin control sections: z, a, bf, bb, nf, nb (p4: robust superellipse fit to the outermost horizontal ray
# hits about (CX, 0) every 4 deg; bf at z 78-94 from p5's front profile at x = 28 and CX, front face y = -52.4)
SKIN_CTRL = [
    (62.3, 40.3, 42.0, 46.4, 2.75, 2.45),
    (70.0, 44.85, 47.7, 51.36, 2.65, 2.39),
    (78.0, 46.36, 52.4, 53.48, 2.38, 2.34),
    (94.0, 44.9, 52.4, 51.4, 2.35, 2.42),
    (104.0, 37.9, 44.5, 43.0, 2.4, 2.6),
    (110.0, 29.45, 38.7, 35.68, 2.47, 2.3),
    (116.0, 18.27, 26.57, 22.97, 3.51, 3.22),
    (118.5, 8.8, 13.8, 10.2, 6.0, 6.0),
]
SKIN_Z = [62.3, 64, 66, 68, 70, 73, 76, 79, 83, 87, 91, 95, 99, 102, 105, 108, 110.5, 112.5, 114.5, 116, 117.2,
          118, 118.5]                                # built sections (interpolated, not parameters)
SKIN_PTS = 24                                        # points per built section

# eyes (p6: sections y = -50 and -54.5; p5: front profile at x = 28 / 15)
EYE_DX, EYE_Z = 13.3, 92.8          # big eyes at x = CX -+ EYE_DX (loops centred 22.0 / 48.7, z 93.0 / 92.6)
EYE_BORE_R = 9.5                    # bore radius (q1 x = 22: bore top z 102.5, bottom 84 at y -55..-45)
EYE_BORE_BACK = -21.0               # bore floor y (p5: rays through the bore hit y = -21.0)
RING_R_OUT, RING_Y = 12.3, -55.5    # ring outer radius and front face y (p5: x = 28 hits -55.4 at z 82 / 102)
RING_TEETH, RING_TOOTH = 24, 1.0    # knurl: teeth round the ring, tooth size (simplified)
RING_BACK = -38.0                   # ring tube's back end y, inside the skin (the skin at the ring's top is y -43.6)
FACE_Y = -52.4                      # front face (p5 x = CX, z 78-82)
NOSE = (30.0, 41.2, 84.0, 98.0, -56.0)   # nose plate x0, x1, z0, z1, front y (p5 x = CX: -55 .. -56 at z 84-98)
BLOCK_Y, BLOCK_Z0, BLOCK_Z1 = -20.0, 82.0, 105.0   # eye block behind the face (p2 y = -30, x = 15 sections)
BLOCK_HW = 27.0                     # eye block half-width (q1 y = -35: frame walls at x 8.6 / 62.6)
SEYE_DX, SEYE_Z = 28.0, 100.0       # small eyes at x = CX -+ SEYE_DX (p1 ring pieces x 7.5 / 63.3, z 95.8-103)
SEYE_R_OUT, SEYE_BORE, SEYE_Y = 4.6, 3.0, -47.3     # small eye tube outer, bore radius, front y (q3 z = 100)
SEYE_BACK = -21.0                   # small eye bore floor y (q3: rays down the bore stop at y -21.0)
REAR_LIP = (14.0, 42.0, 49.0, 102.3)  # rear lip on the top: half-width, y0, y1, flat top z (q3: ref z 101.6-102.3
                                    # at y 46-48 for x 24-45, then a step down to 96.9 at y 50)
CHIN = (25.0, 13.5)                 # chin arch half-width and height above the rim (q2 front map: open x 11-60, to z 76)
BOSS_DX, BOSS_Y = 30.6, 10.1        # screw bosses at x = CX -+ BOSS_DX (q1 y = 10: tube walls x 0 / 10, y 10.1)
BOSS_R, BOSS_HOLE, BOSS_Z0 = 5.5, 4.5, 66.5         # q1 y = 10: outer r 5.5, hole r 4.5 through the top, from z 66.5
TAB = (19.0, 30.5, 44.5, 52.4)      # rear tab, a wedge under the rim: half-width, front y, back y (in the wall),
                                    # bottom z (q1 x = 22: front face y 30.5 z 53-62.3, slope to the rim at y 42)
GROOVE_W, GROOVE_D = 1.6, 2.0       # panel line: width, depth into the skin (q2 top map: 1.5 wide, 2-4 deep)
GROOVE_Y, GROOVE_X0 = 0.8, 11.0     # it runs over each side in the plane y = GROOVE_Y, from |x - CX| > GROOVE_X0 down
                                    # to the rim (q2 top map: x < 25 and x > 47 at y 0-1.5; side maps z 68-112)
BLOCK_OPEN_Y = -45.0                # below the eye axis the block stops here: the bores open into the shell behind
                                    # (q1 x = 22: bore bottom only at y -55..-45; q2 front map: lower halves deep)
FRAME_T, FRAME_Z0 = 2.0, 63.0       # the eye block's side plates below the eyes (outer face at x = CX -+ BLOCK_HW,
                                    # y BLOCK_OPEN_Y .. BLOCK_Y, down to FRAME_Z0; q2 / heat map: walls x 8-10 / 60-62)
BRIDGE = (7.5, -30.0, 74.0)         # chin bridge under the nose: half-width, back y, bottom z (q1 y = -35: x 28-43,
                                    # z 74-82, from the block's front part back to y -30)
SCOOP = (30.0, 90.5, 18.0, 44.0, 24.0, 2.5, 22.0)   # side scoops, a crescent in (y, z) proud of the skin on each
                                    # side: outer circle y, z, r; inner circle y, r (same z); proud; from |x - CX|
                                    # (q2 side maps: crescent y 12-28, z 72-108, 2-4 proud; top map x -10 / 82)

SKIN_NUMBERS = len(SKIN_CTRL) * 5
BARE = "--bare" in sys.argv                         # skin and wall only (while fitting)


# ---------------------------------------------------------------- helpers
def scaled(shp, k):
    """shp scaled by k about the global origin."""
    if k == 1.0:
        return shp
    tr = gp_Trsf()
    tr.SetScale(gp_Pnt(0, 0, 0), k)
    return Solid(BRepBuilderAPI_Transform(shp.wrapped, tr, True).Shape())


def ctrl_interp(ks=1.0):
    c = np.array(SKIN_CTRL, float)
    f = PchipInterpolator(c[:, 0], c[:, 1:], axis=0)
    rows = f(np.array(SKIN_Z))
    rows[:, :3] *= ks
    return rows


def se_points(z, a, bf, bb, nf, nb, n=SKIN_PTS):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    b = np.where(s > 0, bb, bf)
    e = np.where(s > 0, nb, nf)
    x = CX + a * np.sign(c) * np.abs(c) ** (2 / e)
    y = b * np.sign(s) * np.abs(s) ** (2 / e)
    return [(float(xi), float(yi), float(z)) for xi, yi in zip(x, y)]


def skin(ks=1.0, da=0.0):
    """The outer skin; da widens every section's half-width a (the side scoops' proud layer)."""
    secs = []
    for z, row in zip(SKIN_Z, ctrl_interp(ks) + np.array([da, 0, 0, 0, 0])):
        secs.append(Face(Wire([Spline(*se_points(z, *row), periodic=True)])))
    return loft(secs)


def inner_rows(w, ks=1.0):
    """The inner skin's sections, derived from the same control table: each meridian (a along x, bf along -y,
    bb along +y) eroded by the wall w in its own (r, z) plane (the largest r whose disk of radius w stays inside the
    outer meridian and under the top), the exponents kept. No new numbers: the wall is one parameter."""
    c = np.array(SKIN_CTRL, float)
    f = PchipInterpolator(c[:, 0], c[:, 1:], axis=0)
    ztop = c[-1, 0]
    zf = np.linspace(Z_RIM, ztop, 241)
    rf = f(zf)
    rf[:, :3] *= ks
    zin = [Z_RIM - 1.0] + [z for z in SKIN_Z if Z_RIM < z < ztop - w - 0.4] + [ztop - w]
    rows = []
    for z in zin:
        zq = max(z, Z_RIM)
        dz = zf - zq
        near = np.abs(dz) < w
        reach = np.sqrt(np.maximum(w * w - dz[near] ** 2, 0.0))
        r = [float(np.min(rf[near, j] - reach)) for j in range(3)]
        e = f(min(zq + w * 0.5, ztop))[3:]
        rows.append((z, *r, *e))
    return rows


def wall_skin(w, ks=1.0):
    secs = [Face(Wire([Spline(*se_points(z, a, bf, bb, nf, nb), periodic=True)]))
            for z, a, bf, bb, nf, nb in inner_rows(w, ks)]
    return loft(secs)


def shell(wall=1.0, ks=1.0):
    """Outer skin minus the inner skin: the wall, open at the rim."""
    return skin(ks).cut(wall_skin(WALL * wall, ks))


def ycyl(r, y0, y1, x, z):
    """Cylinder along y from y0 to y1 (y0 < y1), axis at (x, z)."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def knurl(ex):
    """The 24 teeth as one solid: a toothed outline in the XZ plane extruded 2.4 along +y from RING_Y."""
    h = RING_TOOTH / 2
    pts = []
    for i in range(RING_TEETH):
        a = 2 * np.pi * i / RING_TEETH
        c, s = np.cos(a), np.sin(a)
        for r, t in ((RING_R_OUT - h, -h), (RING_R_OUT + h, -h), (RING_R_OUT + h, h), (RING_R_OUT - h, h)):
            pts.append((ex + r * c - t * s, EYE_Z + r * s + t * c))
    prof = Plane.XZ.offset(-RING_Y - 2.4) * Polygon(*pts, align=None)      # XZ's normal is -y: offset d is y = -d
    return extrude(prof, 2.4)


def body(wall=1.0, ks=1.0, k=None):
    k = S if k is None else k
    outer = skin(ks)
    inner = wall_skin(WALL * wall, ks)
    shl = outer.cut(inner)
    if BARE:
        return scaled(shl.solids()[0], k)
    eyes_x = (CX - EYE_DX, CX + EYE_DX)
    seyes_x = (CX - SEYE_DX, CX + SEYE_DX)
    # inside, kept within the outer skin: eye block, bosses, small eye tubes
    inside = (box(CX - BLOCK_HW, CX + BLOCK_HW, -60, BLOCK_Y, EYE_Z, BLOCK_Z1)
              + box(CX - BLOCK_HW, CX + BLOCK_HW, -60, BLOCK_OPEN_Y, BLOCK_Z0, EYE_Z + 1)
              + box(CX - BLOCK_HW, CX - BLOCK_HW + FRAME_T, -60, BLOCK_Y, FRAME_Z0, EYE_Z + 1)
              + box(CX + BLOCK_HW - FRAME_T, CX + BLOCK_HW, -60, BLOCK_Y, FRAME_Z0, EYE_Z + 1)
              + box(CX - BRIDGE[0], CX + BRIDGE[0], -60, BRIDGE[1], BRIDGE[2], BLOCK_Z0 + 1))
    for sx in (-1, 1):
        inside += Pos(CX + sx * BOSS_DX, BOSS_Y, (BOSS_Z0 + 110) / 2) * Cylinder(BOSS_R, 110 - BOSS_Z0)
    inside = inside & outer
    add = [inside]
    # proud of the skin: rings, nose plate, small eye tubes, rear tab
    for ex in eyes_x:
        add.append(ycyl(RING_R_OUT, RING_Y, RING_BACK, ex, EYE_Z))    # tube back into the skin: meets it at the top
        add.append(knurl(ex))
    add.append(box(NOSE[0], NOSE[1], NOSE[4], FACE_Y + 1.0, NOSE[2], NOSE[3]))
    for sx in seyes_x:
        add.append(ycyl(SEYE_R_OUT, SEYE_Y, SEYE_BACK + 1.0, sx, SEYE_Z))
    tw, ty0, ty1, tz = TAB
    tab = Plane.YZ.offset(CX - tw) * Polygon((ty0, tz), (ty1, Z_RIM + 1.2), (ty0, Z_RIM + 1.2), align=None)
    tab = extrude(tab, 2 * tw)
    add.append(tab)
    add.append(box(CX - REAR_LIP[0], CX + REAR_LIP[0], REAR_LIP[1], REAR_LIP[2], REAR_LIP[3] - 10, REAR_LIP[3]))
    yo, zo, ro, yi, ri, pr, xs = SCOOP
    cres = (Pos(0, yo, zo) * Rot(0, 90, 0) * Cylinder(ro, 300)) - (Pos(0, yi, zo) * Rot(0, 90, 0) * Cylinder(ri, 300))
    puffed = skin(ks, pr)
    sides = box(CX - 80, CX - xs, -60, 60, 50, 130) + box(CX + xs, CX + 80, -60, 60, 50, 130)
    scoops = (puffed & cres & sides) - inner
    if ks != 1.0:                                    # details follow the skin's section scale
        add = [inside] + [scaled_xy(f, ks, ks, (CX, 0.0)) for f in add[1:]]
    part = shl.fuse(add[0].fuse(*add[1:]), scoops)    # the small pieces first (cheap), the big shell once
    # cuts: eye bores, small eye bores, boss holes, chin arch, top grooves
    cuts = []
    for ex in eyes_x:
        cuts.append(ycyl(EYE_BORE_R, -70, EYE_BORE_BACK, ex, EYE_Z))
    for sx in seyes_x:
        cuts.append(ycyl(SEYE_BORE, -70, SEYE_BACK, sx, SEYE_Z))
    for sx in (-1, 1):
        cuts.append(Pos(CX + sx * BOSS_DX, BOSS_Y, (BOSS_Z0 + 125) / 2) * Cylinder(BOSS_HOLE, 125 - BOSS_Z0))
    cw, ch = CHIN
    chin = Pos(CX, -40, Z_RIM) * Rot(90, 0, 0) * Cylinder(1, 40)
    cuts.append(scaled_xz(chin, cw, ch, (CX, Z_RIM)))
    inset = wall_skin(GROOVE_D, ks)
    for sx in (-1, 1):
        x0 = CX + sx * GROOVE_X0
        x1 = CX + sx * 70
        band = box(min(x0, x1), max(x0, x1), GROOVE_Y - GROOVE_W / 2, GROOVE_Y + GROOVE_W / 2, Z_RIM - 2, 125)
        cuts.append(band - inset)
    if ks != 1.0:
        cuts = [scaled_xy(f, ks, ks, (CX, 0.0)) for f in cuts]
    part = part.cut(*cuts)
    return scaled(part.solids().sort_by(lambda s: -s.volume)[0] if len(part.solids()) > 1 else part.solids()[0], k)


def _aniso(shp, sx, sy, sz, c):
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    g = gp_GTrsf()
    g.SetVectorialPart(gp_Mat(sx, 0, 0, 0, sy, 0, 0, 0, sz))
    g.SetTranslationPart(gp_XYZ(c[0] * (1 - sx), c[1] * (1 - sy), c[2] * (1 - sz)))
    return Solid(BRepBuilderAPI_GTransform(shp.wrapped, g, True).Shape())


def scaled_xy(shp, sx, sy, cxy):
    return _aniso(shp, sx, sy, 1.0, (cxy[0], cxy[1], 0.0))


def scaled_xz(shp, sx, sz, cxz):
    return _aniso(shp, sx, 1.0, sz, (cxz[0], 0.0, cxz[1]))


def solid_ok(shape):
    sols = shape.solids()
    if len(sols) != 1:
        return False, f"{len(sols)} solids"
    s = sols[0]
    if not s.is_valid:
        return False, "not valid"
    if s.volume <= 0:
        return False, "volume <= 0"
    shells = s.shells()
    if len(shells) != 1 or not BRep_Tool.IsClosed_s(shells[0].wrapped):
        return False, f"{len(shells)} shells / not closed"
    return True, f"volume {s.volume / 1000:.2f} cm3"


def export(name, shape, fine):
    os.makedirs(OUT, exist_ok=True)
    export_step(shape, os.path.join(OUT, f"{name}.step"))
    tol, ang = STL_TOL[fine]
    export_stl(shape, os.path.join(OUT, f"{name}.stl"), tolerance=tol, angular_tolerance=ang)
    bb = shape.bounding_box()
    print(f"{name} {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f} mm  "
          f"STEP {os.path.getsize(os.path.join(OUT, name + '.step')) / 1024:.0f} kB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fine", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--bare", action="store_true", help="skin and wall only")
    a = ap.parse_args()
    t0 = time.time()
    shape = body()
    ok, why = solid_ok(shape)
    print(f"{'PASS' if ok else 'FAIL'} body: {why}  (geometry {time.time() - t0:.1f} s)")
    export("body", shape, a.fine)
    print(f"build time {time.time() - t0:.1f} s")
    bad = not ok
    if a.sweep:
        t1 = time.time()
        variants = [("S 0.65", lambda: body(k=0.65)), ("wall 0.8x", lambda: body(wall=0.8)),
                    ("wall 1.2x", lambda: body(wall=1.2)), ("section 0.8x", lambda: body(ks=0.8)),
                    ("section 1.2x", lambda: body(ks=1.2))]
        for vname, fn in variants:
            try:
                vok, vwhy = solid_ok(fn())
            except Exception as e:                              # noqa: BLE001
                vok, vwhy = False, f"{type(e).__name__}: {e}"
            print(f"{'  ok' if vok else 'FAIL'} {vname}: {vwhy}")
            bad |= not vok
        print(f"sweep time {time.time() - t1:.1f} s")
    lim = SKIN_NUMBERS <= 60 and len(SKIN_CTRL) <= 8
    print(f"{'PASS' if lim else 'FAIL'} skin: {SKIN_NUMBERS} numbers, {len(SKIN_CTRL)} control sections")
    sys.exit(1 if bad or not lim else 0)


if __name__ == "__main__":
    main()
