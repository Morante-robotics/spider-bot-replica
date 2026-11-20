#!/usr/bin/env python3
"""jenscolt's left leg rebuilt as parametric build123d code (pilot): leg-blade (L_leg1) and leg-arm (L_leg2).

    ../../.venv/bin/python build.py            # both parts into out/ (coarse STL + STEP), in jenscolt's frame
    ../../.venv/bin/python build.py --sweep    # also S 0.65, blade thickness and arm section scale 0.8x / 1.2x
    ../../.venv/bin/python build.py --edit     # only the edit test: out/edit-*.stl, images/edit-demo.png
    ../../.venv/bin/python build.py --fine     # fine STL

The shape comes only from the parameters below; their values were measured on jenscolt's meshes with
`tools/mesh_ref.py sections` and plane sections / ray height maps in a scratch probe (never read here).

Blade: a skin lofted along a spine (a cubic spline through 5 points) from 6 control sections (asymmetric
superellipses, a cubic spline through each number along the spine) with rounded ends: 50 numbers. The arm's socket,
the eye and the seam grooves are carried in the spine's frame, so a new spine (--edit: N0's leg curve, a longer
blade, a bow) bends the whole blade.
Arm: a 6 mm plate (hub) whose outline is a polar spline, between two fitted planes, with the axle hole, the raised
ring and three gears on its back face; a neck lofted from superellipse sections with three rings, the top block
that goes into the blade's socket, the tab tube (ellipse swept on a straight axis, three rings) and its tab.
"""
import argparse
import functools
import math
import os
import sys
import textwrap
import time

from build123d import (Align, Axis, Box, Cylinder, Edge, Face, Keep, Location, Plane, Polyline, Pos, Rot, Solid,
                       Sphere, Spline, Vector, Wire, export_step, export_stl, extrude, loft, make_face, scale)

from OCP.BRep import BRep_Tool  # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform  # noqa: E402
from OCP.gp import gp_Pnt, gp_Trsf  # noqa: E402
import numpy as np  # noqa: E402
from scipy.interpolate import CubicSpline  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
STL_TOL = {True: (0.02, 0.15), False: (0.05, 0.3)}       # same as cad/common.py (linear mm, angular rad)

# ============================================================================================================
# BLADE (jenscolt spideybot_L_leg1.stl). Local frame: x across the blade, y its thickness (flat face at -y,
# outward), z along it (tip at -z). Source: PCA of the mesh vertices (probe), origin = vertex mean.
# ============================================================================================================
BLADE_ORIGIN = (109.72, -68.46, 47.53)                      # mm, global; probe: vertex mean of L_leg1
BLADE_X = (0.76797, 0.64047, -0.0042)                       # probe: 2nd principal axis (width)
BLADE_Z = (-0.21594, 0.26509, 0.93973)                      # probe: 1st principal axis (length, tip at -z)

# The skin: a spine and a few control sections (SKIN_NUMBERS numbers in all). Convention of N1's warp() (cad/mockup/n1.py, archived at the tag n2-on-meshes-2026-11-20):
# a section lies in the plane normal to the spine; its x axis is the «side» vector made normal to the tangent
# (b = side - (t.side) t), its y axis T x b with T the tangent toward the top; side = local x here, cross(z, rd)
# on N0's leg. Source: least-squares fit of every number at once to v1's 26-section skin (scratch probe fit.py:
# both-way distance of dense samples; 6 sections: the fewest that pass, datasheet.md), v1's skin being the fit of mesh_ref sections of L_leg1.
BLADE_SPINE = [(3.559, 5.425, -48.144),
               (3.317, 1.249, -24.392),
               (2.242, 1.653, 1.123),
               (1.425, 3.065, 20.123),
               (0.711, 0.691, 46.081)]
# Control sections at arc-length fractions 0, 1/(K-1) .. 1 along the spine (foot to top), a cubic spline through
# each column: a = half-width, bB / bT = half-thickness below (-y, flat face) / above (+y, ridge), nB / nT = superellipse
# exponent of the lower / upper half (2 = ellipse, 4+ = box-like).
BLADE_CTRL = [(3.775, 1.270, 2.821, 3.128, 5.442),
              (8.004, 4.464, 3.011, 2.420, 4.333),
              (11.343, 5.734, 4.588, 4.030, 4.053),
              (11.290, 6.850, 8.230, 3.936, 2.835),
              (9.236, 6.851, 6.894, 3.910, 2.004),
              (3.112, 2.648, 2.853, 2.894, 3.858)]
BLADE_TILT = 0.0689     # rad, every section turned about the spine (v1: 0.04-0.08 per row)
# Rounded ends: within L mm of an end the section shrinks as r + (1 - r) sqrt(1 - (1 - d/L)^2), d = distance to it
# (L scales with the spine's length, like every position along it)
BLADE_CAP = ((3.50, 0.546), (8.38, 0.420))       # ((L, r) at the foot, (L, r) at the top)
SKIN_MAX = (60, 5, 8)             # numbers, spine points, sections (spec)
SKIN_NUMBERS = 3 * len(BLADE_SPINE) + 5 * len(BLADE_CTRL) + 1 + 4
BLADE_STATIONS = 28               # lofted sections generated from the above (smoothness, not shape parameters)
BLADE_PTS = 14                    # points per section spline (smoothness only)
N_MIN = 1.6                       # exponents clamped above this (no cusp)

# Socket for the arm's top block: a rectangular slot tilted about x, open through the ridge. Source: mesh section
# at x = 0.9 (probe), floor (23.2, 2.0) -> (35.0, -2.3) in (z, y), walls square to the floor. Carried rigidly in the
# spine's frame at SOCKET_REF.
SOCKET_X = (-4.10, 5.70)          # mm, its side walls (hull-minus-section, z 26-35)
SOCKET_FLOOR0 = (23.2, 2.0)       # (z, y) the floor's near corner
SOCKET_SLOPE = -0.364             # floor dy/dz; the walls are square to it
SOCKET_LEN = 11.8                 # mm along z from the near to the far corner
SOCKET_TOP = 14.0                 # mm (y), above the blade (cuts through the ridge)
SOCKET_REF = 29.1                 # z of the spine frame it is carried in (its middle)
# Seam grooves along both sides: a channel GROOVE_W wide, GROOVE_D deep, following the side, its centre line
# a polyline in (z, y). Source: half-width scan of the mesh sections every 1.5 mm in z at y -2.5..3 (probe).
# Each station of the band is carried in the spine's frame at its own z (so the groove bends with the spine).
GROOVE_R = [(-11.0, -3.4), (-7.6, -2.4), (-5.0, 0.0), (-3.5, 1.25), (33.0, 2.55), (40.0, 2.6)]   # right side (+x)
GROOVE_L = [(-7.0, -0.4), (-3.0, 1.2), (33.0, 2.9), (40.0, 3.0)]                                # left side (-x)
GROOVE_W = 1.3
GROOVE_D = 0.9
RIDGE_DY = 1.9                    # the front-edge ridge: centre line = the right seam's, this far toward +y
RIDGE_W = 0.8                     # width (y)
RIDGE_H = 0.45                    # height over the skin
RIDGE_Z = (-3.0, 33.0)            # span (z); in the spine's frame like the grooves
GROOVE_Z = (-15.3, 42.0)          # z span of the inset skin (the groove's floor)
# The «eye»: a low spherical boss on the flat face. Source: section at x 0.9 (z 31.5-37.6, 0.9 proud).
EYE = (1.0, 34.5, 3.5, 1.3)      # x, z, radius on the face, height
EYE_FACE_Y = -3.75                # the flat face's y at the eye


def closed_spline_face(pts):
    return Face(Wire([Spline(*pts, periodic=True)]))


def scaled(shp, k):
    """shp scaled by k about the global origin (build123d's scale() works about the shape's own location)."""
    tr = gp_Trsf()
    tr.SetScale(gp_Pnt(0, 0, 0), k)
    return Solid(BRepBuilderAPI_Transform(shp.solids()[0].wrapped, tr, True).Shape())


class Spine:
    """A cubic spline through the control points (not-a-knot, uniform parameter u 0..1, foot to top), with its
    arc length and the section frames of the convention above."""

    def __init__(self, ctrl, side=(1.0, 0.0, 0.0)):
        self.ctrl = np.asarray(ctrl, float)
        self.cs = CubicSpline(np.linspace(0, 1, len(self.ctrl)), self.ctrl)
        self.side = np.asarray(side, float)
        self.uu = np.linspace(0, 1, 801)
        self.pp = self.cs(self.uu)
        self.ss = np.r_[0, np.cumsum(np.linalg.norm(np.diff(self.pp, axis=0), axis=1))]
        self.L = self.ss[-1]
        self.knots = np.interp(np.linspace(0, 1, len(self.ctrl)), self.uu, self.ss)   # arc length at each point

    def u(self, s):
        return np.interp(s, self.ss, self.uu)

    def s_at_z(self, z):
        """Arc length where the spine crosses local z (the spine runs monotonic in z)."""
        return np.interp(z, self.pp[:, 2], self.ss)

    def frame(self, s):
        u = self.u(s)
        p = self.cs(u)
        t = self.cs(u, 1)
        t = t / np.linalg.norm(t)
        b = self.side - (t @ self.side) * t
        b = b / np.linalg.norm(b)
        return p, np.stack([b, np.cross(t, b), t])          # rows: section x, section y, tangent (to the top)


def ctrl_at(u, ctrl=None):
    c = np.asarray(ctrl if ctrl is not None else BLADE_CTRL, float)
    return CubicSpline(np.linspace(0, 1, len(c)), c)(u)


def cap(s, L, k=1.0):
    """Section scale at arc length s of a spine L long; k = L / the original spine's length."""
    f = 1.0
    for d, (lc, r) in ((s, BLADE_CAP[0]), (L - s, BLADE_CAP[1])):
        w = min(max(1 - d / (lc * k), 0.0), 1.0)
        f *= r + (1 - r) * math.sqrt(max(1 - w * w, 0.0))
    return f


def section_xy(row, f, ks, thick, da=0.0, n=BLADE_PTS):
    a, bB, bT, nB, nT = row
    a = a * f * ks - da
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        b, e = (bT, max(nT, N_MIN)) if s >= 0 else (bB, max(nB, N_MIN))
        x = a * math.copysign(abs(c) ** (2 / e), c)
        y = b * f * ks * thick * math.copysign(abs(s) ** (2 / e), s)
        out.append((math.cos(BLADE_TILT) * x - math.sin(BLADE_TILT) * y,
                    math.sin(BLADE_TILT) * x + math.cos(BLADE_TILT) * y))
    return out


def skin(sp, ks=1.0, thick=1.0, s0=None, s1=None, da=0.0, n=BLADE_STATIONS, ctrl=None, kl=1.0):
    """Loft of n sections along the spine between arc lengths s0..s1 (denser near the ends of a full skin);
    sections at arc-length fraction s / L, cross-section scale ks, kl = this spine's length / the original's."""
    full = s0 is None
    s0, s1 = (0.0, sp.L) if full else (s0, s1)
    alpha = 0.7 if full else 0.0
    faces = []
    for i in range(n):
        t = i / (n - 1)
        s = s0 + (s1 - s0) * (t - alpha * math.sin(2 * math.pi * t) / (2 * math.pi))
        p, R = sp.frame(s)
        row = ctrl_at(s / sp.L, ctrl)
        q = [p + x * R[0] + y * R[1] for x, y in section_xy(row, cap(s, sp.L, kl), ks, thick, da)]
        faces.append(closed_spline_face([Vector(*v) for v in q]))
    return loft(faces, ruled=False)


class Carry:
    """Moves points / shapes given in the original blade's local frame onto another spine: the original spine's
    frame at a point is mapped onto the new spine's frame at the same arc-length fraction (as the sections and
    n1's warp), the offsets from the spine kept in that frame and scaled by ks. A shape (socket, eye) is carried
    rigidly with the frame at its reference z; the grooves station by station, so they bend with the spine.
    by_knot: the arc length is mapped piecewise linearly between the spines' control points instead of as one
    fraction of the whole (the arm: its pivot point lands on the new spine's pivot point, as n1's breakpoints)."""

    def __init__(self, sp0, sp, ks, by_knot=False):
        self.sp0, self.sp, self.ks, self.by_knot = sp0, sp, ks, by_knot

    def s_new(self, s0):
        if self.by_knot:
            return float(np.interp(s0, self.sp0.knots, self.sp.knots))
        return s0 * self.sp.L / self.sp0.L

    def pair(self, z):
        s0 = self.sp0.s_at_z(z)
        return self.sp0.frame(s0), self.sp.frame(self.s_new(s0))

    def points(self, X, z):
        (p0, R0), (p1, R1) = self.pair(z)
        return p1 + self.ks * (np.asarray(X, float) - p0) @ R0.T @ R1

    def shape(self, shp, z):
        (p0, R0), (p1, R1) = self.pair(z)
        l0 = Location(Plane(origin=tuple(p0), x_dir=tuple(R0[0]), z_dir=tuple(R0[2])))
        l1 = Location(Plane(origin=tuple(p1), x_dir=tuple(R1[0]), z_dir=tuple(R1[2])))
        if self.sp is self.sp0 and abs(self.ks - 1) < 1e-9:
            return shp
        rel = l0.inverse() * shp
        if abs(self.ks - 1) > 1e-9:
            rel = scaled(rel, self.ks)
        return l1 * rel


def blade_features(thick=1.0):
    """Socket and eye in the original local frame (as v1)."""
    z0, y0 = SOCKET_FLOOR0
    z1, y1 = z0 + SOCKET_LEN, y0 + SOCKET_SLOPE * SOCKET_LEN
    lean = -SOCKET_SLOPE                          # walls square to the floor: dz/dy = -slope
    prof = [(z0, y0 * thick), (z1, y1 * thick), (z1 + lean * (SOCKET_TOP - y1 * thick), SOCKET_TOP),
            (z0 + lean * (SOCKET_TOP - y0 * thick), SOCKET_TOP)]
    pl = Plane(origin=(SOCKET_X[0], 0, 0), x_dir=(0, 0, 1), z_dir=(1, 0, 0))
    face = make_face(Polyline(*[(a, -b) for a, b in prof], close=True))   # plane y = global -y
    sock = extrude(Location(pl) * face, amount=SOCKET_X[1] - SOCKET_X[0], dir=(1, 0, 0))
    ex, ez, er, ed = EYE
    rs = (er ** 2 + ed ** 2) / (2 * ed)               # sphere through the dimple's rim and floor
    yb = EYE_FACE_Y * thick - ed                      # the boss's lowest point
    eye = Pos(ex, yb + rs, ez) * Sphere(rs)
    eye &= Pos(ex, yb + 1.5, ez) * Box(4 * er, 3, 4 * er)
    return sock, eye


def groove_bands(carry, thick=1.0, paths=None, w=None):
    """Both seam bands as ruled lofts of rectangles, each station carried at its own z."""
    bands = []
    for path, (xa, xb) in paths or ((GROOVE_R, (0.0, 25.0)), (GROOVE_L, (-25.0, 0.0))):
        W = w or GROOVE_W
        top, bot = [], []
        for i, (z, y) in enumerate(path):          # offset the centre line by +-W/2 (mitre at the corners)
            a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
            tz, ty = b[0] - a[0], (b[1] - a[1]) * thick
            n = math.hypot(tz, ty)
            nz, ny = -ty / n, tz / n
            top.append((z + nz * W / 2, y * thick + ny * W / 2))
            bot.append((z - nz * W / 2, y * thick - ny * W / 2))
        top, bot = np.array(top), np.array(bot)
        zs = np.unique(np.r_[top[:, 0], bot[:, 0]])
        zs = zs[(zs >= max(top[0, 0], bot[0, 0])) & (zs <= min(top[-1, 0], bot[-1, 0]))]
        secs = []
        for z in zs:
            yt, yb = np.interp(z, top[:, 0], top[:, 1]), np.interp(z, bot[:, 0], bot[:, 1])
            X = carry.points([(xa, yb, z), (xb, yb, z), (xb, yt, z), (xa, yt, z)], z)
            secs.append(Face(Wire.make_polygon([Vector(*v) for v in X], close=True)))
        bands.append(loft(secs, ruled=True))
    return bands


def blade_on(sp, ks=1.0, thick=1.0, sp0=None):
    """The blade on spine sp (any frame), cross-section scale ks; features carried from the original spine sp0."""
    sp0 = sp0 or sp
    carry = Carry(sp0, sp, ks)
    kl = sp.L / sp0.L
    body = skin(sp, ks, thick, kl=kl)
    sock, eye = blade_features(thick)
    sock, eye = carry.shape(sock, SOCKET_REF), carry.shape(eye, EYE[1])
    g0, g1 = (carry.sp.L / sp0.L * sp0.s_at_z(z) for z in GROOVE_Z)
    inset = skin(sp, ks, thick, g0, g1, GROOVE_D * ks, n=12, kl=kl)
    bands = groove_bands(carry, thick)
    groove = (bands[0] + bands[1]) - inset
    rpath = [(z, float(np.interp(z, *zip(*GROOVE_R))) + RIDGE_DY) for z in RIDGE_Z]
    rb = groove_bands(carry, thick, [(rpath, (0.0, 25.0))], RIDGE_W)[0]
    outer = skin(sp, ks, thick, g0, g1, -RIDGE_H * ks, n=12, kl=kl)
    ridge = rb & outer
    return (body + eye + ridge) - [sock, groove]


def spine_local(thick=1.0):
    return Spine([(x, y * thick, z) for x, y, z in BLADE_SPINE])


def blade_local(k=1.0, thick=1.0):
    sp = spine_local(thick)
    shp = blade_on(sp, 1.0, thick)
    return scaled(shp, k) if k != 1.0 else shp


def blade(k=1.0, thick=1.0):
    pl = Plane(origin=BLADE_ORIGIN, x_dir=BLADE_X, z_dir=BLADE_Z)     # scaled variants grow about the origin
    return Location(pl) * blade_local(k, thick)


# ============================================================================================================
# ARM (jenscolt spideybot_L_leg2.stl). Local frame: u = (x - y)/sqrt2 (the plate's plane, toward the blade),
# w = (x + y)/sqrt2 (across the plate, the gear face at -w), z. Source: the mesh's flat faces have normals
# exactly (±1, ±1, 0)/sqrt2 (probe). The part is built in (u, w, z) and turned -45 deg about Z; no offset.
# ============================================================================================================
HUB_C = (90.0, 45.0)              # (u, z) centre of the hub outline's polar radii
HUB_R = [12.43, 12.87, 12.77, 12.32, 11.92, 11.85, 12.25, 13.16, 13.53,      # radii every 20 deg from -180 deg;
         14.26, 15.38, 17.00, 16.00, 12.86, 11.36, 11.01, 11.40, 11.72]       # probe: section w = 33 (40, 60, 140
#                                                                               deg: under the neck / tab, blended)
HUB_BACK = (34.582, -0.0119, -0.0626)    # back plane w = a + b u + c z; probe: fit, p95 residual 0.46 mm
HUB_FRONT = (40.569, -0.0062, -0.0775)   # front plane; probe: fit, p95 residual 0.63 mm
HUB_STEP = (100.3, 35.8)          # front face: right of u 100.3 it is flat at w 35.8; probe: front height map
HOLE_C = (90.0, 40.0)             # (u, z) axle hole; probe: back height map
HOLE_R = 2.75
RING_R = 4.80                     # raised ring round the hole on the back face
RING_W = 29.45                    # its top (w); probe: back height map row z 40
GEARS = [(86.5, 48.3, 3.5), (93.5, 51.5, 3.7), (96.2, 45.0, 3.2)]   # (u, z, tip radius); probe: back height map
GEAR_TEETH = 9
GEAR_DEPTH = 1.1                  # tooth depth, radial
GEAR_BORE = 1.0                   # the gear's centre circle (not raised)
GEAR_RISE = 0.8                   # above the back plane; probe: back height map, gears at w 29.9

# Neck (hub -> top block) lofted along ARM_SPINE, a cubic spline through 5 points (same Spine class as the blade;
# section x axis = ARM_SIDE made normal to the tangent). Knot 0 is the axle hole, the crank pin: the hub, its ring
# and gears, the tab tube and the static-leg tab hang rigidly from the spine's frame there. Every other feature sits
# at its own z of this original spine, i.e. at an arc length mapped knot to knot onto a new spine (Carry by_knot):
# knot 2 is the pivot at the body's rim (z 61: N1's build_leg breakpoint, tag n2-on-meshes-2026-11-20), knot 4 the knee (the block).
# Source: the v1 neck stations' centres (z sections of L_leg2, probe), the hub hole HOLE_C.
ARM_SPINE = [(90.0, 33.6, 40.0),       # knot 0: axle hole (crank pin), mid-plate (fitted planes: w 31.0-36.9)
             (99.5, 32.7, 50.0),       # knot 1: the neck's root in the hub (v1 station z 50)
             (101.7, 32.35, 61.0),     # knot 2: pivot at the rim (v1 stations z 56 / 62 interpolated)
             (103.2, 31.65, 71.0),     # knot 3 (v1 stations z 68 / 74 interpolated)
             (105.9, 31.4, 80.9)]      # knot 4: knee, the neck's end in the top block (v1 station z 80.9)
ARM_SIDE = (0.0, 1.0, 0.0)             # w, across the plate: the leg plane's normal (n1: cross(z, radial))
# Neck sections (z on the original spine, half-width in the plate (u), half-thickness across it (w)), superellipse
# exponent NECK_N; interpolated linearly along the spine from knot 1. Probe: z sections of L_leg2 (v1's stations).
NECK = [(50.0, 5.0, 3.1), (56.0, 5.1, 3.1), (62.0, 5.1, 3.1), (68.0, 5.0, 3.1), (74.0, 5.0, 3.1),
        (78.0, 3.8, 2.9), (80.9, 2.4, 2.4)]
# Root: a straight ruled tube from knot 0 to knot 1 (half-width u, half-thickness w), thin enough to stay inside the
# plate (fitted planes w 31.0-36.9 there), so the neck stays joined to the hub however far a new spine moves the
# neck's root (N0's inner arm: 10.7 mm from the pin at S 0.6, the hub's edge 9 mm away); hidden in jenscolt's shape.
NECK_ROOT = (3.0, 1.6)
NECK_STATIONS = 12                # lofted sections generated from the above (smoothness only)
NECK_N = 2.6
SEC_PTS = 12                      # points per tube section spline (smoothness only)
NECK_RINGS = [57.6, 60.9, 64.2]   # ring centres (z); probe: front height map bands
RING_BAND = 1.0                   # ring width along the tube
NECK_RISE = 0.65                  # neck ring height over the tube
RING_RISE = 0.45                  # ring height over the tube
TOP_BLOCK = ((108.4, 115.4), (26.8, 35.8), (69.0, 80.9))   # u, w, z ranges; probe: z sections 69-80.9
# Flare from the neck into the block (each hexagon carried at its own z, so it bends with the spine), the block
# rigid at the knee. A ruled loft of (u, w) hexagons, z 71.5 -> 80.9 (fused to the block from z 72.5). Probe: z sections 72, 74.3,
# 78 (ref vs model overlay) and height-map rows z 75.5 and 80.
FLARE = [(71.5, [(100.5, 29.4), (106.0, 28.8), (108.0, 29.5), (108.0, 33.5), (106.0, 34.2), (100.5, 33.6)]),
         (72.5, [(100.3, 29.2), (106.5, 28.6), (108.6, 28.6), (108.6, 34.4), (106.5, 34.4), (100.3, 33.6)]),
         (74.3, [(99.6, 29.6), (105.5, 27.9), (108.6, 27.3), (108.6, 35.3), (105.5, 34.9), (99.6, 33.6)]),
         (78.0, [(101.0, 29.5), (106.2, 26.8), (108.6, 26.8), (108.6, 35.8), (106.2, 35.8), (101.0, 33.8)]),
         (80.9, [(103.3, 29.3), (106.6, 26.8), (108.6, 26.8), (108.6, 35.8), (106.6, 35.8), (103.3, 33.4)])]
BUMP = (104.5, 68.2, 1.3, 28.0)   # boss on the neck's back: u, z, radius, top w; probe: back height map

# Tab tube: straight, elliptical. Probe: sections normal to its axis, t = 0..12.
TAB_P0 = (83.1, 33.45, 50.0)      # (u, w, z) axis point inside the hub
TAB_DIR = (-0.5, 0.0, 0.866)      # axis direction (30 deg from vertical, toward -u)
TAB_LEN = 11.5
TAB_A = 3.10                      # half-width in the plate's plane
TAB_B = 2.10                      # half-thickness across it
TAB_RINGS = [4.0, 6.5, 9.0]       # ring centres along the axis
TAB_BOX = ((67.9, 80.0), (31.9, 35.7), (58.5, 62.3))     # the static-leg tab: u, w, z; probe: z sections 59-62

# The right leg: jenscolt's R meshes are the L ones mirrored about the plane x = MIRROR_X (probe mirror.py: every
# vertex within 0.0000 mm both ways, both parts). One model; side "R" mirrors it.
MIRROR_X = 35.45


def arm_on(sp, ks=1.0, sec=1.0, sp0=None):
    """The arm on spine sp (any frame), cross-section scale ks; features carried from the original spine sp0
    (arm-local frame) knot to knot. sec scales the neck and tab tube sections only (--sweep)."""
    sp0 = sp0 or sp
    carry = Carry(sp0, sp, ks, by_knot=True)
    z_hub = ARM_SPINE[0][2]

    # hub plate: polar spline outline extruded across w, trimmed by the two fitted planes (arm-local frame)
    pts = [Vector(HUB_C[0] + r * math.cos(math.radians(-180 + 20 * i)), 24.0,
                  HUB_C[1] + r * math.sin(math.radians(-180 + 20 * i))) for i, r in enumerate(HUB_R)]
    hub = extrude(closed_spline_face(pts), amount=16, dir=(0, 1, 0))

    def plane(coef):
        a, b, c = coef
        u0, z0 = HUB_C
        return Plane(origin=(u0, a + b * u0 + c * z0, z0), z_dir=(-b, 1, -c))
    hub = hub.split(plane(HUB_BACK), keep=Keep.TOP).split(plane(HUB_FRONT), keep=Keep.BOTTOM)
    su, sw = HUB_STEP
    hub -= Pos(su + 10, sw + 5, 45) * Box(20, 10, 40)

    def back_w(u, z):
        a, b, c = HUB_BACK
        return a + b * u + c * z

    def cyl_w(u, z, r, w_top, w_bot):              # cylinder along w between w_top (< w_bot)
        return Pos(u, w_top, z) * Rot(-90, 0, 0) * Cylinder(r, w_bot - w_top, align=(Align.CENTER, Align.CENTER,
                                                                                      Align.MIN))

    rigid = [hub, cyl_w(*HOLE_C, RING_R, RING_W, back_w(*HOLE_C) + 1.0)]   # carried with the frame at knot 0
    for gu, gz, gr in GEARS:
        tooth = []
        for i in range(GEAR_TEETH):                # flat-topped teeth: root, tip, tip, root per tooth
            for f, r in ((0.0, gr - GEAR_DEPTH), (0.18, gr), (0.32, gr), (0.5, gr - GEAR_DEPTH)):
                a = 2 * math.pi * (i + f) / GEAR_TEETH
                tooth.append((gu + r * math.cos(a), gz + r * math.sin(a)))
        wt = back_w(gu, gz) - GEAR_RISE
        g = extrude(Location(Plane(origin=(0, wt, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))) *
                    make_face(Polyline(*[(a, -b) for a, b in tooth], close=True)), amount=GEAR_RISE + 1.0,
                    dir=(0, 1, 0))
        rigid.append(g - cyl_w(gu, gz, GEAR_BORE, wt - 1, wt + GEAR_RISE))
    d = Vector(*TAB_DIR).normalized()                # tab tube: ellipse normal to its axis, extruded along it
    tp = Plane(origin=TAB_P0, x_dir=Vector(0, 1, 0).cross(d), z_dir=d)

    def ell(a, b, t0, length):
        return extrude(Location(tp) * Pos(0, 0, t0) * Face(Wire([Edge.make_ellipse(a * sec, b * sec)])), amount=length)
    rigid.append(ell(TAB_A, TAB_B, 0, TAB_LEN))
    rigid += [ell(TAB_A + RING_RISE, TAB_B + RING_RISE, t - RING_BAND / 2, RING_BAND) for t in TAB_RINGS]
    (u0, u1), (w0, w1), (z0, z1) = TAB_BOX
    rigid.append(Pos((u0 + u1) / 2, (w0 + w1) / 2, (z0 + z1) / 2) * Box(u1 - u0, w1 - w0, z1 - z0))
    body = [carry.shape(s, z_hub) for s in rigid]

    # neck: sections in the spine's frame (x = across the plate, w; y = in the plate, u)
    zn = [r[0] for r in NECK]

    def ring_face(z, rise=0.0, root=False):
        p, R = carry.pair(z)[1]
        hu, hw = NECK_ROOT if root else (float(np.interp(z, zn, [r[j] for r in NECK])) for j in (1, 2))
        q = []
        for i in range(SEC_PTS):
            t = 2 * math.pi * i / SEC_PTS
            c, s = math.cos(t), math.sin(t)
            x = (hw * sec + rise) * math.copysign(abs(c) ** (2 / NECK_N), c)
            y = (hu * sec + rise) * math.copysign(abs(s) ** (2 / NECK_N), s)
            q.append(Vector(*(p + ks * (x * R[0] + y * R[1]))))
        return closed_spline_face(q)
    body.append(loft([ring_face(z) for z in np.linspace(zn[0], zn[-1], NECK_STATIONS)]))
    body.append(loft([ring_face(z, root=True) for z in (z_hub, ARM_SPINE[1][2])], ruled=True))
    body += [loft([ring_face(zr - RING_BAND / 2, NECK_RISE), ring_face(zr + RING_BAND / 2, NECK_RISE)], ruled=True)
             for zr in NECK_RINGS]
    body.append(loft([Face(Wire.make_polygon([Vector(*v) for v in carry.points([(u, w, z) for u, w in ring], z)],
                                             close=True)) for z, ring in FLARE], ruled=True))
    (u0, u1), (w0, w1), (z0, z1) = TOP_BLOCK
    body.append(carry.shape(Pos((u0 + u1) / 2, (w0 + w1) / 2, (z0 + z1) / 2) * Box(u1 - u0, w1 - w0, z1 - z0),
                            ARM_SPINE[-1][2]))
    bu, bz, br, bw = BUMP
    body.append(carry.shape(cyl_w(bu, bz, br, bw, back_w(bu, bz) + 2.0), bz))
    body = body[0].fuse(*body[1:])
    return body - carry.shape(cyl_w(*HOLE_C, HOLE_R, 20, 45), z_hub)


def arm_spine_local():
    return Spine(ARM_SPINE, side=ARM_SIDE)


def arm(k=1.0, sec=1.0):
    shp = arm_on(arm_spine_local(), 1.0, sec)
    return Rot(0, 0, -45) * (scaled(shp, k) if k != 1.0 else shp)


# ============================================================================================================
# N1's entry point: both parts of one leg on any two spines (pure function of its inputs, cached).
# ============================================================================================================
def mirrored(shp, origin, normal):
    """shp mirrored about the plane through origin with that normal (one solid)."""
    return shp.mirror(Plane(origin=tuple(map(float, origin)), z_dir=tuple(map(float, normal))))


def _tup(a):
    return None if a is None else tuple(tuple(float(v) for v in p) for p in np.atleast_2d(a))


def leg(side="L", blade_spine=None, arm_spine=None, S=1.0, across=None, thick=1.0, sec=1.0):
    """One leg's two solids, (blade, arm). Pure function of its inputs (memoised: same arguments, same objects;
    the solids are shared, so transform copies of them, e.g. `loc * blade`, never edit them in place).

    side         "L": jenscolt's L_leg1 / L_leg2 (the leg at +x in jenscolt's frame: N0's right side, as n1 uses
                 it today); "R": its mirror image (jenscolt's R meshes exactly).
    blade_spine  5 points (x, y, z) in the caller's frame, foot -> blade top (the knee); None: jenscolt's frame.
    arm_spine    5 points, crank pin (axle hole) -> neck root -> pivot (body rim) -> middle -> knee; None: jenscolt's
                 frame. The hub hangs rigidly from the first point; the other features follow knot to knot.
    S            cross-section scale (every offset from the spine); with a None spine, the part's scale about
                 jenscolt's origin.
    across       the leg plane's normal in the caller's frame (n1: cross(z, radial)); default from the blade
                 spine: cross(z, horizontal(foot - top)), i.e. the radial direction taken as the foot's.
    thick, sec   blade thickness and arm section scale (1.0 = jenscolt).
    For side "R" with spines: the L part built on the spines mirrored about the plane through their first point
    normal to `across`, then mirrored back, so the R leg lies on the given spines."""
    return _leg(side, _tup(blade_spine), _tup(arm_spine), float(S), None if across is None else
                tuple(float(v) for v in across), float(thick), float(sec))


@functools.lru_cache(maxsize=32)
def _leg(side, bsp, asp, S, across, thick, sec):
    if side not in ("L", "R"):
        raise ValueError(f"side {side!r}: 'L' or 'R'")
    if across is None and bsp is not None:
        d = np.subtract(bsp[0], bsp[-1])
        across = tuple(np.cross([0, 0, 1.0], [d[0], d[1], 0]) / math.hypot(d[0], d[1]))
    n = None if across is None else np.asarray(across, float) / np.linalg.norm(across)
    if side == "R" and bsp is None and asp is None:   # jenscolt's frame: the L parts (cached) mirrored
        return tuple(mirrored(s, (MIRROR_X, 0, 0), (1, 0, 0)) for s in _leg("L", None, None, S, None, thick, sec))

    def on(spine, kind, origin):
        if spine is None:                              # jenscolt's frame
            shp = blade(S, thick) if kind == "blade" else arm(S, sec)
            return mirrored(shp, (MIRROR_X, 0, 0), (1, 0, 0)) if side == "R" else shp
        P = np.asarray(spine, float)
        if side == "R":                                # build L on the mirrored spine, mirror back
            P = P - 2 * ((P - origin) @ n)[:, None] * n
        sp = Spine(P, side=n)
        shp = (blade_on(sp, S, thick, sp0=spine_local(thick)) if kind == "blade"
               else arm_on(sp, S, sec, sp0=arm_spine_local()))
        return mirrored(shp, origin, n) if side == "R" else shp
    o = np.asarray((bsp or asp or ((0, 0, 0),))[0], float)
    return on(bsp, "blade", o), on(asp, "arm", o)


# ============================================================================================================
# EDIT TEST (--edit): both parts changed through their spines only. Variants: (a) the blade's spine on N0's
# right-front blade curve (cad/motion.py leg_shape with P0, imported) in N0's frame, sections at N0's S;
# (b) length +EDIT_LENGTH; (c) bow EDIT_BOW mm outward (toward -y, the flat face) at the middle; (d) the arm's
# spine on N0's right-front inner arm + upper leg (crank pin A0 -> pivot P -> knee K), at N0's S.
# ============================================================================================================
N0_LEG = 0                        # motion.P0["angles"][0]: the right-front leg
EDIT_LENGTH = 1.10                # (b) spine stretched along z about its top end
EDIT_BOW = 3.0                    # mm, (c) spine's middle moved outward (-y) by this, sin(pi u) along it
EDIT_SPINE_DEV = 0.5              # mm, (a) pass limit: spine to N0's curve, both ways (spec)


def n0_blade(n):
    """N0's right-front blade curve, foot to top (n + 4 points), its S and radial direction (cad/motion.py)."""
    sys.path.insert(0, os.path.dirname(HERE)) if os.path.dirname(HERE) not in sys.path else None
    import motion                                     # noqa: E402  (the approved motion stays in cad/motion.py)
    p = motion.P0
    _, _, ang, pts, _, ni = motion.neutral_leg(N0_LEG, p, n=n)
    return pts[ni + n:][::-1], p["S"], np.array([math.cos(ang), math.sin(ang), 0.0])


def n0_upper(n):
    """N0's right-front inner arm + upper leg (crank pin A0 -> pivot P -> knee K): the 5 arm spine points (A0, the
    neck root at the original's knot 1 fraction of A0 -> P, P, the upper curve's middle, K) and a dense polyline."""
    sys.path.insert(0, os.path.dirname(HERE)) if os.path.dirname(HERE) not in sys.path else None
    import motion                                     # noqa: E402
    p = motion.P0
    P, A0, ang, pts, _, ni = motion.neutral_leg(N0_LEG, p, n=n)     # upper = pts[ni:ni + n], P .. K
    up = pts[ni:ni + n]
    sp0 = arm_spine_local()
    f = sp0.knots[1] / sp0.knots[2]
    ctrl = [A0, A0 + f * (P - A0), P, up[(n - 1) // 2], up[-1]]
    return np.array(ctrl), np.vstack([np.linspace(A0, P, 20)[:-1], up]), p["S"], np.array([math.cos(ang),
                                                                                            math.sin(ang), 0.0])


def poly_dist(Q, P):
    """Distance of each point Q to the polyline P."""
    a, b = P[:-1], P[1:]
    ab = b - a
    t = np.clip(np.einsum("qsk,sk->qs", Q[:, None] - a[None], ab) / (ab * ab).sum(1), 0, 1)
    return np.linalg.norm(Q[:, None] - (a[None] + t[..., None] * ab[None]), axis=2).min(1)


def edit_variants():
    sp0 = spine_local()
    cur, S, rd = n0_blade(13)                          # 17 points: u = 0, 1/4 .. 1 are rows 0, 4, 8, 12, 16
    m = len(BLADE_SPINE)
    ctrl_a = [tuple(cur[round(i * 16 / (m - 1))]) for i in range(m)]
    sp_a = Spine(ctrl_a, side=np.cross([0, 0, 1.0], rd))
    ztop = BLADE_SPINE[-1][2]
    sp_b = Spine([(x, y, ztop - EDIT_LENGTH * (ztop - z)) for x, y, z in BLADE_SPINE])
    sp_c = Spine([(x, y - EDIT_BOW * math.sin(math.pi * i / (m - 1)), z) for i, (x, y, z) in enumerate(BLADE_SPINE)])
    dense, _, _ = n0_blade(197)
    q = sp_a.cs(np.linspace(0, 1, 801))
    dev = max(poly_dist(q, dense).max(), poly_dist(dense, q).max())
    uu = np.linspace(0, 1, 801)
    bow = np.abs(sp_c.cs(uu) - sp0.cs(uu)).max()
    actrl, adense, _, ard = n0_upper(201)
    sp_d = Spine(actrl, side=np.cross([0, 0, 1.0], ard))
    adev = poly_dist(sp_d.cs(uu), adense).max()
    a0 = arm_spine_local()
    return [("n0", sp_a, S, f"spine to N0's curve {dev:.3f} mm (limit {EDIT_SPINE_DEV}), length {sp_a.L:.1f} mm "
                               f"(original x S {sp0.L * S:.1f}), S {S}", dev > EDIT_SPINE_DEV),
            ("length", sp_b, 1.0, f"spine length {sp_b.L:.1f} / {sp0.L:.1f} mm = x{sp_b.L / sp0.L:.3f}", False),
            ("bow", sp_c, 1.0, f"spine's middle moved {bow:.2f} mm outward", False),
            ("arm-n0", sp_d, S, f"arm spine to N0's inner + upper curve {adev:.2f} mm (its corner at the pivot "
                                f"rounded; not a limit), length {sp_d.L:.1f} mm (original x S {a0.L * S:.1f}), S {S}",
             False)], sp0, dense, adense


def mesh_of(shape, tol=0.2):
    V, F = [], []
    for face in shape.faces():
        try:
            v, f = face.tessellate(tol, 0.5)
        except AttributeError:                            # a face OCC leaves without triangles: not drawn
            continue
        F += [[i + len(V) for i in t] for t in f]
        V += [(p.X, p.Y, p.Z) for p in v]
    return np.array(V), np.array(F)


def edit_figure(results, sp0, dense, adense, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    orig = mesh_of(blade_on(sp0))
    fig, axs = plt.subplots(1, 4, figsize=(20, 6.2))

    def draw(ax, V, F, proj, color, label):
        P2 = proj(V)
        ax.add_collection(PolyCollection(P2[F], facecolor=color, edgecolor="none", alpha=0.35, label=label))

    for ax, (name, sp, ks, why, bad, shape) in zip(axs, results):
        V, F = mesh_of(shape)
        if name == "arm-n0":
            rd = np.cross(sp.side, [0, 0, 1.0])
            proj = lambda X: np.c_[X @ rd, X[:, 2]]
            draw(ax, *mesh_of(results[0][5]), proj, "tab:blue", "(a) blade on N0")
            draw(ax, V, F, proj, "tab:purple", "(d) arm on N0")
            ax.plot(*proj(adense).T, "r--", lw=1.5, label="N0 inner arm + upper leg")
            ax.plot(*proj(dense).T, "m--", lw=1.0, label="N0 blade curve")
            ax.plot(*proj(sp.cs(np.linspace(0, 1, 200))).T, "k-", lw=0.8, label="arm spine")
            ax.plot(*proj(sp.ctrl).T, "ko", ms=3)
            ax.set_xlabel("radial (mm, N0 frame)")
            ax.set_ylabel("z (mm, N0 frame)")
        elif name == "n0":
            rd = np.cross(sp.side, [0, 0, 1.0])                # back to the radial direction
            proj = lambda X: np.c_[X @ rd, X[:, 2]]
            (p0, R0), (p1, R1) = sp0.frame(sp0.L), sp.frame(sp.L)        # hung from the top end, unbent
            V0 = p1 + ks * (orig[0] - p0) @ R0.T @ R1
            draw(ax, V0, orig[1], proj, "0.5", "original x S, hung from the same top")
            draw(ax, V, F, proj, "tab:blue", "(a) bent onto N0")
            ax.plot(*proj(dense).T, "r--", lw=1.5, label="N0 right-front blade curve")
            ax.plot(*proj(sp.cs(np.linspace(0, 1, 200))).T, "k-", lw=0.8, label="spine")
            ax.set_xlabel("radial (mm, N0 frame)")
            ax.set_ylabel("z (mm, N0 frame)")
        else:
            proj = lambda X: np.c_[X[:, 2], X[:, 1]]
            draw(ax, *orig, proj, "0.5", "original")
            draw(ax, V, F, proj, "tab:orange" if name == "length" else "tab:green",
                 "(b) length +10 %" if name == "length" else f"(c) bow +{EDIT_BOW:g} mm")
            ax.plot(*proj(sp0.cs(np.linspace(0, 1, 200))).T, "k:", lw=0.8, label="original spine")
            ax.plot(*proj(sp.cs(np.linspace(0, 1, 200))).T, "k-", lw=0.8, label="new spine")
            ax.set_xlabel("z along the blade (mm, local)")
            ax.set_ylabel("y thickness (mm, local; -y = flat face, outward)")
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.set_title(f"{name}: {'FAIL' if bad else 'ok'}\n" + "\n".join(textwrap.wrap(why, 60)), fontsize=9)
        ax.legend(fontsize=7, loc="best")
    fig.suptitle("leg edit test: the same parameters, a new spine (blade a-c, arm d)")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def run_edit(fine):
    t0 = time.time()
    variants, sp0, dense, adense = edit_variants()
    a0 = arm_spine_local()
    results, fails = [], 0
    for name, sp, ks, why, bad, in variants:
        try:
            shape = arm_on(sp, ks, sp0=a0) if name.startswith("arm") else blade_on(sp, ks, sp0=sp0)
            ok, what = solid_ok(shape)
        except Exception as e:                              # noqa: BLE001
            shape, ok, what = None, False, f"{type(e).__name__}: {e}"
        if ok:
            export(f"edit-{name}", shape, fine, step=False)
        if not ok or bad:
            print(f"FAIL edit {name}: {what}; {why}")
            fails += 1
        else:
            print(f"  ok edit {name}: {what}; {why}")
        results.append((name, sp, ks, why, bad or not ok, shape))
    if all(r[5] is not None for r in results):
        os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
        edit_figure(results, sp0, dense, adense, os.path.join(HERE, "images", "edit-demo.png"))
    if not fails:
        print("PASS edit")
    print(f"edit time {time.time() - t0:.1f} s")
    return fails


# ============================================================================================================
def solid_ok(shape):
    """(ok, why): one valid closed solid."""
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
        return False, "shell not closed"
    return True, f"volume {s.volume / 1000:.2f} cm3"


PARTS = {"leg-blade": lambda: leg("L")[0], "leg-arm": lambda: leg("L")[1],
         "leg-blade-r": lambda: leg("R")[0], "leg-arm-r": lambda: leg("R")[1]}


def export(name, shape, fine, step=True):
    os.makedirs(OUT, exist_ok=True)
    s = shape.solids()[0] if len(shape.solids()) == 1 else shape
    if step:
        export_step(s, os.path.join(OUT, f"{name}.step"))
    tol, ang = STL_TOL[fine]
    export_stl(s, os.path.join(OUT, f"{name}.stl"), tolerance=tol, angular_tolerance=ang)
    bb = s.bounding_box()
    print(f"{name:10s} {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f} mm  "
          + (f"STEP {os.path.getsize(os.path.join(OUT, name + '.step')) / 1024:.0f} kB" if step else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append", choices=sorted(PARTS))
    ap.add_argument("--fine", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--edit", action="store_true", help="only the edit test: out/edit-*.stl, images/edit-demo.png")
    a = ap.parse_args()
    if a.edit:
        sys.exit(1 if run_edit(a.fine) else 0)
    t0 = time.time()
    bad = False
    for name in a.part or sorted(PARTS):
        tp = time.time()
        shape = PARTS[name]()
        print(f"  {name} geometry {time.time() - tp:.1f} s")
        ok, why = solid_ok(shape)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {why}")
        bad |= not ok
        export(name, shape, a.fine)
    print(f"build time {time.time() - t0:.1f} s")
    if a.sweep:
        t1 = time.time()
        variants = [("blade S0.65", lambda: leg("L", S=0.65)[0]), ("arm S0.65", lambda: leg("L", S=0.65)[1]),
                    ("blade-r S0.65", lambda: leg("R", S=0.65)[0]), ("arm-r S0.65", lambda: leg("R", S=0.65)[1]),
                    ("blade thick 0.8x", lambda: blade(thick=0.8)), ("blade thick 1.2x", lambda: blade(thick=1.2)),
                    ("arm section 0.8x", lambda: arm(sec=0.8)), ("arm section 1.2x", lambda: arm(sec=1.2))]
        fails = 0
        for vname, fn in variants:
            try:
                ok, why = solid_ok(fn())
            except Exception as e:                              # noqa: BLE001
                ok, why = False, f"{type(e).__name__}: {e}"
            if not ok:
                print(f"FAIL {vname}: {why}")
                fails += 1
            else:
                print(f"  ok {vname}: {why}")
        if not fails and not bad:
            print("PASS sweep")
        print(f"sweep time {time.time() - t1:.1f} s")
    lim = SKIN_NUMBERS <= SKIN_MAX[0] and len(BLADE_SPINE) <= SKIN_MAX[1] and len(BLADE_CTRL) <= SKIN_MAX[2]
    print(f"{'PASS' if lim else 'FAIL'} blade skin: {SKIN_NUMBERS} numbers ({len(BLADE_SPINE)} spine points, "
          f"{len(BLADE_CTRL)} sections; limits {SKIN_MAX})")
    bad |= not lim
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
