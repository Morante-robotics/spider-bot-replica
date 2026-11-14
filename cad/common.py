"""Shared by the designs modelled in build123d from the simulator's geometry (legs, crankshafts, gear-train-test,
test-frame; base v1 takes them through those): the simulator's geometry, the hardware's sizes, the two clearances
these designs were made with, and the build123d helpers they all use.

Moved here unchanged from the old cad/drive/build.py (2026-11-13), so each design's parts come out byte-identical.
New designs take their clearances from fits.py instead of CLR / CLR_STEEL.
"""
import json
import os
import sys

import numpy as np
from build123d import Box, Cylinder, Plane, Polygon, Pos, Sphere, export_step, export_stl, extrude, mirror

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "sim")
sys.path.insert(0, SIM)
import toy_leg_3d as sim  # noqa: E402

# --- the simulator's geometry ---------------------------------------------------------------------------------
GEO = json.load(open(os.path.join(SIM, "toy_leg_3d_rows_cad.json")))[0]
P_ = {k: GEO[k] for k in sim.ranges("rows")}
CX = sim.CENTER[0]

# --- clearances these designs were made with (fits.TURN and fits.STEEL are the same numbers, measured) ----------
CLR = 0.5           # hole clearance on the diameter for a printed part turning or sliding in a printed hole
                    # (clearance test 2026-11-11: +0.4 was the only one that turned, roughly; 0.2 before)
CLR_STEEL = 0.3     # the same for a steel screw or pin turning in a printed hole (test: +0.3 turns, +0.2 grips)

# --- hardware (hardware.md) -------------------------------------------------------------------------------------
PIN = 3.0           # steel pins: pivot pin (or an M3 screw) and idler pins
SCREW = 3.0         # M3 screws: pivot pin across the fork, and the two vertical screws the fork swings on
TAP = 2.5           # blind hole an M3 screw cuts its own thread in (not used: M3 would not go into it, 2026-11-11)
NUT_T = 2.4         # M3 nut thickness
NUT_AF = 5.5        # M3 nut across flats
HEAD_D, HEAD_H = 5.5, 3.0          # M3 socket head

# --- index marks -------------------------------------------------------------------------------------------------
MARK_D, MARK_DEPTH = 1.2, 0.5      # index dots: crankshaft number, on the +X (right legs') side


# --- build123d helpers -------------------------------------------------------------------------------------------
def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def bar(a, b, w, h, wdir):
    """Box from point a to b (local coordinates), w across along wdir, h in the remaining direction."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = unit(b - a)
    wd = unit(np.asarray(wdir, float) - np.dot(wdir, d) * d)
    hd = np.cross(d, wd)
    pl = Plane(origin=tuple((a + b) / 2), x_dir=tuple(d), z_dir=tuple(hd))
    return pl.location * Box(np.linalg.norm(b - a), w, h)


def cyl(c, axis, r, length):
    """Cylinder centred on c along axis."""
    ax = unit(axis)
    x = unit(np.cross(ax, [0, 0, 1]) if abs(ax[2]) < 0.9 else np.cross(ax, [1, 0, 0]))
    return Plane(origin=tuple(np.asarray(c, float)), x_dir=tuple(x), z_dir=tuple(ax)).location * Cylinder(r, length)


def hexagon(af, h, corner_dir):
    """Hexagonal prism (nut pocket) across flats af, height h (z from 0), with a corner pointing along corner_dir (2D)."""
    a0 = np.arctan2(corner_dir[1], corner_dir[0])
    r = af / np.sqrt(3)
    pts = [(r * np.cos(a0 + j * np.pi / 3), r * np.sin(a0 + j * np.pi / 3)) for j in range(6)]
    return extrude(Polygon(*pts, align=None), amount=h)


def dice(n, pitch=1.3):
    """Dot positions (u, v) of a dice face showing n (1-4)."""
    c = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)]}
    return [(pitch * u, pitch * v) for u, v in c[n]]


def marks(n, x, yc, zc, sx=1):
    """Index dots (dice face n) sunk into a face at x whose outward normal is sx·X, centred on (yc, zc)."""
    out = None
    for u, v in dice(n):
        s = Pos(x, yc + u, zc + v) * Sphere(MARK_D / 2 + 0.1)
        s = s.translate((sx * (MARK_D / 2 + 0.1 - MARK_DEPTH), 0, 0))
        out = s if out is None else out + s
    return out


# --- placement ----------------------------------------------------------------------------------------------------
def place(shape, R, t):
    """Shape moved by rotation matrix R (right-handed) and translation t."""
    pl = Plane(origin=tuple(t), x_dir=tuple(R[:, 0]), z_dir=tuple(R[:, 2]))
    return pl.location * shape


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def mirror_x(shape):
    return mirror(shape, Plane(origin=(CX, 0, 0), z_dir=(1, 0, 0)))


# --- output -------------------------------------------------------------------------------------------------------
def watertight(stl):
    """OpenCascade leaves an occasional hairline gap where a sphere meets a box; close it so the STL is a solid."""
    import trimesh
    m = trimesh.load(stl)
    if m.is_volume:
        return
    m.merge_vertices(digits_vertex=3)
    m.update_faces(m.nondegenerate_faces())
    trimesh.repair.fill_holes(m)
    m.fix_normals()
    if not m.is_volume:
        raise RuntimeError(f"{stl}: could not make it watertight")
    m.export(stl)


def export(name, p, out):
    """STEP (Onshape) and STL (printing) of part p into folder out, and its size."""
    os.makedirs(out, exist_ok=True)
    export_step(p, os.path.join(out, f"{name}.step"))
    stl = os.path.join(out, f"{name}.stl")
    export_stl(p, stl, tolerance=0.02, angular_tolerance=0.15)
    watertight(stl)
    bb = p.bounding_box()
    print(f"{name:22s} {bb.size.X:6.1f} × {bb.size.Y:6.1f} × {bb.size.Z:6.1f} mm  volume {p.volume / 1000:5.2f} cm³")


def build_parts(parts, names, out):
    """Build and export the named parts: parts maps a name to a function that builds it."""
    for name in names:
        export(name, parts[name](), out)


def part_args(doc, parts, extra=None):
    """Command line of every build.py: --part <name> (repeatable) rebuilds only those parts."""
    import argparse
    ap = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append", choices=sorted(parts), help="build only this part (repeatable)")
    if extra:
        extra(ap)
    return ap.parse_args()
