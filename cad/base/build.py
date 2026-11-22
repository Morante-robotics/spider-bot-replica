#!/usr/bin/env python3
"""base: jenscolt's bowl (skin, wall, rim ear, leg windows, wall windows) as parameters; his inside is left out.

Part: base  a hollow bowl, open on top. Frame = jenscolt's (mm, Z up, forward = -Y, mirror plane x = CX).

    ../../.venv/bin/python build.py            # out/base.stl + .step
    ../../.venv/bin/python build.py --sweep    # S 0.65, wall 0.8x/1.2x, section scale 0.8x/1.2x: each one valid solid

Structure (r01):
  skin   the bowl below the ledge: plan sections are superellipses (exponent N_FOOT .. N_TOP) whose half-widths follow two
         smooth meridian curves w(z) = W * (1 - ((ZE - z) / H)^P)^(1/P) (one across x, one along y, front = back);
         14 loft stations are sampled from those 9 numbers (stations are not parameters). Above the ledge a
         vertical band (the top section grown by LEDGE) carries the side ears.
  wall   the inner skin is the same table shrunk by WALL (W - WALL, H - WALL; the band inside goes straight up), cut from the outer
         skin in the single boolean; skin and wall are separate parameters.
  rim    the ear on each side: a side-view polyline RIM_EAR (y, z) over the ledge height RIM_Z; above it, gone.
  back   a vertical cylinder scoops the back; the wall on that cylinder is kept as the back sheet.
  front  leg windows: one parameter set (an arch, axis along y, plus a flat front face beside it), mirrored.
  details  WWIN_* wall windows and RIM_SLOT_* rim slots: one list of angles, mirrored about the mirror plane.
Every number was measured in a scratch probe on cad/carcass-jenscolt/spideybot_base_bowl.stl (named beside it);
build.py reads no mesh.
"""
import argparse
import math
import os
import sys
import time

from build123d import Align, Box, Cylinder, Edge, Face, Polyline, PositionMode, Pos, Rot, Solid, Spline, Vector, Wire, export_step, export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---- parameters (mm, jenscolt's frame; each with its source probe in the scratchpad, r01/)
S = 1.0                       # scale
WALL = 1.2                    # wall thickness, inward from the reference (outer) surface
CX = 35.6                     # mirror plane x: bounds x -15.0 .. 86.2 -> centre 35.6 (mesh_ref info)
CY = -4.0                     # bowl axis y: section centres at z 40..42 (prof.py)
Z_FOOT = 38.0                 # flat foot of the bowl (bounds z min)
# meridians (fitm.py / fitm3.py: least squares on the section half-widths z 38..62)
X_W, X_ZE, X_H, X_P = 49.3, 57.5, 19.8, 1.37    # across x: rms 0.86, max 2.1 (the foot bulge at z 42)
Y_W, Y_ZE, Y_H, Y_P = 47.3, 52.45, 14.6, 1.71   # along y, front and back alike: rms 0.33, max 0.7
N_FOOT, N_TOP = 1.6, 2.0      # plan superellipse exponent, linear in z from the foot to the ledge (fitm2.py: 1.6-1.8
                              # best below z 56; ray hit r 49.9 at alpha 60 on the band needs 2.0, probe2.py)
Z_LEDGE = 62.0                # the bowl ends and the vertical band starts (x extent steps 49.3 -> 50.6 here, prof.py)
LEDGE = 1.3                   # the band stands out of the bowl by this all round (50.6 - 49.3): the rim ledge; the
                              # band wall is LEDGE + WALL/2 thick everywhere (ref ear 1.0 .. 1.3 thick, probe2.py)
BAND_TOP = 76.0               # above the highest rim
# rim: ear on each side wall, side view (y, z), straight above the ledge z RIM_Z (rays.py: highest wall hit per angle)
RIM_Z = 62.0
EAR_DX = 30.0                 # the ears stand on the side walls only, beyond this from the mirror plane (the back
                              # sheet and the front stay at RIM_Z: rays.py, wall top z 62 at alpha 140..220)
RIM_EAR = [(-38.5, 62.0), (-21.0, 72.5), (-9.0, 72.5), (4.7, 70.0), (29.5, 66.0), (36.8, 62.0)]
# back scoop: vertical cylinder (circle through (35.6, 29.7) [back sheet] and (2.2, 36.2) [z 62 loop's ends])
BACK_R, BACK_Y = 85.0, 114.7
# front leg windows, one parameter set mirrored about x = CX (probe2.py front depth map):
WIN_FLOOR_Z = 56.5            # arch bottom on the mirror plane (window floor z 56 .. 57 at dx < 6)
WIN_ARCH_R = 45.0             # arch radius: floor z 57.6 at dx 10, 58.7 at 14, 62 at 21.6
WIN_BACK_Y = -30.2            # the arch cut stops here (front wall only)
SIDE_Y = -38.0                # flat front face beside each window (ref y -40 .. -37, x 1..10 and 61..70)
SIDE_DX = 20.9                # beside each window a pocket: the flat face starts this far from the mirror plane at
SIDE_LEAN = 0.41              # SIDE_Z, at a cheek face facing out that leans out upward (cheek.py: ref faces nx -0.85
                              # .. -0.96 at dx 20.7 (z 50) .. 25.6 (z 62)); the pocket's walls are WALL thick
POST_DX = 24.0                # between the arch and the cheek the wall stands up to POST_TOP as a post
POST_TOP = 65.0               # (rays.py: wall to z 65 at alpha 34..36; probe2.py: x 9.5..11 at z 63..65)
SIDE_Z = 49.5                 # pocket floor (cheek.py: faces nz -1 at z 48 .. 50)
# wall windows (win.py: ray gaps per angle, alpha from straight ahead; +x side 58.6 81.6 99.3 132.6, -x side 58.9
# 87.1 103.2 135.2 -> means, mirrored)
WWIN_ALPHA = [58.75, 84.4, 101.2, 133.9]
WWIN_W = 4.0                  # 4.5 deg at r 50
WWIN_Z0, WWIN_Z1 = 57.8, 62.2
# rim slot on each ear (win.py: gap alpha 88.0 .. 89.0 at z 70.5 .. 71 on both sides)
RIM_SLOT_ALPHA = 88.5
RIM_SLOT_W = 1.0
RIM_SLOT_DEPTH = 2.0          # from the ear top
N_STATIONS = 14               # loft stations sampled from the meridians (not parameters)
PTS = 16                      # spline points per station
NUMBERS = 4 + 4 + 2 + 2 + 1 + 1 + 1 + 1 + 1 + 1 + 3 + 2 * len(RIM_EAR) + 2 + 6 + len(WWIN_ALPHA) + 3 + 3


def meridian(W, ZE, H, P, z):
    v = min(1.0, max(0.0, (ZE - z) / H))
    return W * max(0.0, 1.0 - v ** P) ** (1.0 / P)


def plan_n(z):
    return N_FOOT + (N_TOP - N_FOOT) * min(1.0, max(0.0, (z - Z_FOOT) / (Z_LEDGE - Z_FOOT)))


def section_pts(z, a, b, n, pts=PTS):
    """The pts points of the superellipse section at height z, half-widths a (x) and b (y), about the bowl axis."""
    p = []
    for i in range(pts):
        t = 2 * math.pi * i / pts
        c, s = math.cos(t), math.sin(t)
        p.append((CX + a * math.copysign(abs(c) ** (2 / n), c), CY + b * math.copysign(abs(s) ** (2 / n), s), z))
    return p


def section(z, a, b, n, pts=PTS):
    """Closed superellipse wire at height z, half-widths a (x) and b (y), about the bowl axis: the periodic chord-length
    spline through the pts points, re-interpolated through pts * 2 points of itself (the pts points and the curve's
    midpoint between each pair) with uniform parameters. The shape is the spline's (< 0.01 mm), but every station has
    the same knot vector, so the loft needs no extra knots (a 35 x 32 pole skin, not 175 x 16 poles: every boolean on
    the bowl is far faster)."""
    p = section_pts(z, a, b, n, pts)
    e = Edge.make_spline(p, periodic=True)
    c = [0.0]
    for u, v in zip(p, p[1:] + p[:1]):
        c.append(c[-1] + math.dist(u, v))
    q = [e.position_at((c[i] + c[i + 1]) / 2 / c[-1], position_mode=PositionMode.PARAMETER) for i in range(pts)]
    two = [x for i in range(pts) for x in (Vector(*p[i]), q[i])]
    return Wire([Edge.make_spline(two, periodic=True, parameters=[float(i) for i in range(2 * pts + 1)])])


def skin(d, k):
    """Bowl (foot .. ledge) plus band (ledge .. top), shrunk by d (0 = outer, WALL = inner)."""
    z0 = Z_FOOT + d
    st = [z0 + (Z_LEDGE - z0) * (1 - math.cos(math.pi / 2 * i / (N_STATIONS - 1))) for i in range(N_STATIONS)]
    hw = lambda z: (k * meridian(X_W - d, X_ZE, X_H - d, X_P, z), k * meridian(Y_W - d, Y_ZE, Y_H - d, Y_P, z))
    secs = [section(z, *hw(z), plan_n(z)) for z in st]
    bowl = Solid.make_loft(secs)
    top = BAND_TOP + 4 * d                         # the inner band pokes out above the outer one
    # outer band: the bowl's top section grown by LEDGE; inner: the outer bowl's top section less half the wall, so the
    # band wall (LEDGE + WALL/2 thick) overlaps the bowl wall by WALL/2 at the ledge for any wall
    a, b = hw(Z_LEDGE) if d == 0 else (k * meridian(X_W, X_ZE, X_H, X_P, Z_LEDGE), k * meridian(Y_W, Y_ZE, Y_H, Y_P, Z_LEDGE))
    grow = LEDGE * k if d == 0 else -0.5 * d
    band = Solid.extrude(Face(section(Z_LEDGE, a + grow, b + grow, N_TOP)), Vector(0, 0, top - Z_LEDGE))
    return bowl.fuse(band)


def prism_yz(pts, x0, x1):
    """A polygon in the (y, z) plane extruded along x from x0 to x1."""
    return Solid.extrude(Face(Wire(Polyline(*[(x0, y, z) for y, z in pts], close=True))), Vector(x1 - x0, 0, 0))


def radial_box(alpha, sx, w, z0, z1, k):
    """A box through the wall at angle alpha (deg from straight ahead, toward +x if sx = 1), width w, z0..z1."""
    a = math.radians(alpha)
    b = Box(30, w, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    r = (meridian(X_W, X_ZE, X_H, X_P, Z_LEDGE) - WALL) * k
    return Pos(CX + sx * r * math.sin(a), CY - r * math.cos(a), z0) * Rot(0, 0, sx * alpha - 90) * b


def cut_all(shape, tools):
    """One boolean cut of every tool, run in parallel with oriented bounding boxes (3x faster than Shape.cut here)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.collections import List_TopoDS_Shape
    args, tl = List_TopoDS_Shape(), List_TopoDS_Shape()
    args.Append(shape.wrapped)
    for t in tools:
        tl.Append(t.wrapped)
    op = BRepAlgoAPI_Cut()
    op.SetArguments(args)
    op.SetTools(tl)
    op.SetRunParallel(True)
    op.SetUseOBB(True)
    op.Build()
    if not op.IsDone():
        raise RuntimeError("cut failed")
    from build123d.topology.utils import downcast  # noqa
    from build123d import Shape  # noqa
    return Shape.cast(downcast(op.Shape()))


def pocket(sx, g, k):
    """The pocket beside the window on side sx, grown by g on its back, cheek and floor faces."""
    z0 = SIDE_Z - g
    cheek = lambda z: CX + sx * ((SIDE_DX + SIDE_LEAN * (z - SIDE_Z)) * k - g)
    y0 = CY + (SIDE_Y - CY) * k + g
    pts = [(cheek(z0), z0), (CX + sx * 80, z0), (CX + sx * 80, z0 + 40), (cheek(z0 + 40), z0 + 40)]
    return Solid.extrude(Face(Wire(Polyline(*[(x, y0, z) for x, z in pts], close=True))), Vector(0, -60 - g, 0))


def bowl(wall=WALL, k=1.0):
    t0 = time.time()
    outer, inner = skin(0.0, k), skin(wall, k)
    ky = lambda y: CY + (y - CY) * k                 # plan positions follow the section scale about the bowl axis
    back = Pos(CX, ky(BACK_Y), 30) * Cylinder(BACK_R * k, 120, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ring = Pos(CX, ky(BACK_Y), 30) * Cylinder(BACK_R * k + wall, 120, align=(Align.CENTER, Align.CENTER, Align.MIN))
    keep = [prism_yz([(ky(y), z) for y, z in RIM_EAR], CX + sx * EAR_DX * k, CX + sx * 80) for sx in (-1, 1)]
    keep += [Pos(CX + sx * (POST_DX if sx > 0 else POST_DX + 4) * k, ky(SIDE_Y) - 30, RIM_Z - 1)
             * Box(4 * k, 30 + 1, POST_TOP - RIM_Z + 1, align=(Align.MIN, Align.MIN, Align.MIN))
             for sx in (-1, 1)]
    rim = Pos(CX, CY, RIM_Z) * Box(200, 200, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)) - keep
    zc = WIN_FLOOR_Z + WIN_ARCH_R * k
    arch = Pos(CX, ky(WIN_BACK_Y), zc) * Rot(90, 0, 0) * Cylinder(WIN_ARCH_R * k, 80, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pockets = [pocket(sx, 0.0, k) for sx in (-1, 1)]
    # the hollow spares the back sheet (the wall on the scoop cylinder) and a WALL-thick layer round each pocket (its
    # back, cheek and floor walls), so the one cut below leaves those walls: no fuse
    hollow = inner.cut(ring - back, *[pocket(sx, wall, k) for sx in (-1, 1)])
    cutters = [hollow, back, rim, arch] + pockets
    for sx in (-1, 1):                               # the mirrored half of every named feature
        cutters += [radial_box(al, sx, WWIN_W, WWIN_Z0, WWIN_Z1, k) for al in WWIN_ALPHA]
        top = max(z for _, z in RIM_EAR)
        cutters.append(radial_box(RIM_SLOT_ALPHA, sx, RIM_SLOT_W, top - RIM_SLOT_DEPTH, top + 5, k))
    out = cut_all(outer, cutters).clean()
    print(f"    skin + cuts {time.time() - t0:.1f} s", flush=True)
    return out


def scale(sh, f):
    """Scale about the origin (build123d's scale() works about the shape's own location)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetScaleFactor(f)
    return type(sh)(BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape())


def build(S_=S, wall=WALL, k=1.0):
    sh = bowl(wall, k)
    return scale(sh, S_) if S_ != 1.0 else sh


def solid_ok(sh):
    try:
        solids = sh.solids()
        ok = len(solids) == 1 and sh.is_valid and sh.volume > 100
        return ok, f"{len(solids)} solid(s), valid={sh.is_valid}, volume {sh.volume / 1000:.1f} cm3"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def export(name, shape):
    os.makedirs(OUT, exist_ok=True)
    export_step(shape, os.path.join(OUT, f"{name}.step"))
    export_stl(shape, os.path.join(OUT, f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    sh = build()
    ok, why = solid_ok(sh)
    print(f"{'PASS' if ok else 'FAIL'} base: {why}")
    print(f"build time {time.time() - t0:.1f} s; {NUMBERS} numbers")
    export("base", sh)
    bad = not ok
    if a.sweep:
        variants = [("S0.65", dict(S_=0.65)), ("wall 0.8x", dict(wall=WALL * 0.8)), ("wall 1.2x", dict(wall=WALL * 1.2)),
                    ("section 0.8x", dict(k=0.8)), ("section 1.2x", dict(k=1.2))]
        for vn, kw in variants:
            try:
                ok2, why2 = solid_ok(build(**kw))
            except Exception as e:  # noqa: BLE001
                ok2, why2 = False, f"{type(e).__name__}: {e}"
            print(f"  ok {vn}: {why2}" if ok2 else f"FAIL {vn}: {why2}")
            bad |= not ok2
        if not bad:
            print("PASS sweep")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
