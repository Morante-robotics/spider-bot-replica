#!/usr/bin/env python3
"""Spider-Bot legs and drive, modelled in code (build123d) from the simulator's geometry.

Parts (all PLA):
  leg-{front,middle,rear}-{right,left}  one rigid bent leg. Its inner end is a tube: the ball on the crank pin slides
                                         in its bore. At the rim it has a cross hole for the pivot pin.
  pivot                                  fork around the leg at the rim: a 3 mm pin across it carries the leg (tilts
                                         up and down) and two printed trunnions on top and bottom let it swing.
  crankshaft-{1..4}                      one piece: gear in the middle, a journal and a crank either side, a ball on
                                         each crank pin. Front to rear; the cranks are printed at their phase.
  idler-{1..3}                           idler gears between the crankshafts, so all four turn the same way.
  spine                                  two walls holding the crankshafts (slots open at the top) and the idler pins.
  test-frame                             desk stand for one middle leg, its pivot and crankshaft 2, turned by hand.

Coordinates as in ../carcass-120 and ../../sim (mm, z up, forward = -Y). Geometry from
../../sim/toy_leg_3d_rows_cad.json (first entry). Every part is exported as STEP (for Onshape) and STL (for Bambu
Studio), in its own frame (print orientation: see README); `--assembly` also writes the whole drive, placed by the
simulator's kinematics, at the given crank angles.

Usage:
    python3 build.py                 # all parts into this folder
    python3 build.py --assembly 0    # plus assembly-0.step / .stl at crank angle 0°
    python3 check.py --gaps          # then: collision and gap check over a full turn

Needs build123d (Python 3.12: pip install build123d), numpy, trimesh and manifold3d.
"""
import argparse
import itertools
import json
import os
import sys

import numpy as np
from build123d import (Axis, Box, Cone, Cylinder, Plane, Pos, Rot, Sphere, Polygon, export_step, export_stl,
                       extrude, Compound, Location, mirror)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "sim"))
import toy_leg_3d as sim  # noqa: E402

# --- parameters (mm) -----------------------------------------------------------------------------------------
CLR = 0.5           # hole clearance on the diameter for a printed part turning or sliding in a printed hole
                    # (clearance test 2026-11-11: +0.4 was the only one that turned, roughly; 0.2 before)
CLR_STEEL = 0.3     # the same for a steel screw or pin turning in a printed hole (test: +0.3 turns, +0.2 grips)
PIN = 3.0           # steel pins: pivot pin (or an M3 screw) and idler pins
BALL = 3.6          # ball on the crank pin
STUB = 2.2          # crank pin stub that carries the ball
TUBE = 7.6          # height of the leg's inner tube (round top and bottom)
TUBE_W = 5.6        # its width across: flat sides, so the middle legs' tubes clear each other
LEG_W, LEG_H = 5.0, 6.0     # leg bar: width (across, the print height) × height
ARM_DY = -(TUBE_W - LEG_W) / 2    # arm, boss and knee flush with the tube's -Y face (on the bed when printed)
SHIN_W = 4.5        # shin and foot a little thinner: the middle legs' shins pass 0.8 mm apart
SHIN_DY = -(TUBE_W - SHIN_W) / 2   # shin flush with the leg's -Y face (the face on the bed when printed)
BOSS = 9.0          # leg boss around the pivot pin
JOURNAL = 4.0       # crankshaft journal diameter
GEAR_T = 3.0        # gear face width
MOD = 1.0           # gear module
SHAFT_TEETH = 12
WALL_IN, WALL_OUT = 1.75, 4.25     # spine walls span |x| from WALL_IN to WALL_OUT about the body axis
WEB_IN, WEB_OUT = 4.5, 6.5         # crank web, |x|
WEB_OUT_REAR = 6.0  # crankshaft 4's webs are thinner: the rear leg's tube came 0.15 mm from the web's outer face
YOKE_WALL = 2.0      # fork side walls
YOKE_CAP = 4.0       # fork top and bottom walls, with a blind hole for the M3 screw it swings on
PITCH_MAX = 28.0     # the leg tilts 6-23° up (rear leg most) (the crank is lower than the rim): the fork window allows this much
SCREW = 3.0          # M3 screws: pivot pin across the fork, and the two vertical screws the fork swings on
TAP = 2.5            # blind hole an M3 screw cuts its own thread in (not used: M3 would not go into it, 2026-11-11)
NUT_T = 2.4          # M3 nut thickness
NUT_AF = 5.5         # M3 nut across flats
KEEP_Y = 14.0        # test frame: the shaft's walls reach this far either side of the shaft (end blocks beyond KEEP_GAP)
KEEP_GAP = 8.5       # end blocks start here, clear of the gear's tips (radius 7)
KEEP_SCREW_Y = 11.25 # keeper screws, either side of the shaft

GEO = json.load(open(os.path.join(HERE, "..", "..", "sim", "toy_leg_3d_rows_cad.json")))[0]
P_ = {k: GEO[k] for k in sim.ranges("rows")}
CX = sim.CENTER[0]
NAMES = ["front", "middle", "middle", "rear"]


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


# --- simulator kinematics ------------------------------------------------------------------------------------
def legs_at(theta):
    """Right-side legs at crank angle theta (rad): P, A, u, crank centre O, phase."""
    out = []
    for side, i, P, rhat in sim.pivots():
        if side != "R":
            continue
        O = sim.crank_centre(P_, "rows", i, P, rhat)
        ph = np.pi * sim.GROUP["R"][i]
        s = sim.solve_leg(P_, "rows", "crank", P, rhat, np.array([theta + ph]), O)
        out.append(dict(i=i, P=P, A=s["A"][0], u=s["u"][0], O=O, F=s["F"][0]))
    return out


def ap_range(i):
    th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    l = [x for x in sim.pivots() if x[0] == "R" and x[1] == i][0]
    O = sim.crank_centre(P_, "rows", i, l[2], l[3])
    s = sim.solve_leg(P_, "rows", "crank", l[2], l[3], th, O)
    ap = np.linalg.norm(s["P"] - s["A"], axis=1)
    return ap.min(), ap.max()


def leg_frame(u):
    """Right-handed leg frame: X along the leg (outward), Z up in the leg's plane, Y = Z × X."""
    fwd = unit(np.cross([0, 0, 1.0], u))
    if fwd[1] > 0:
        fwd = -fwd
    down = unit(np.cross(u, fwd))
    if down[2] > 0:
        down = -down
    X, Z = unit(u), -down
    return np.column_stack([X, np.cross(Z, X), Z])


# --- parts ---------------------------------------------------------------------------------------------------
def leg(i):
    """Right leg i in its own frame: P at the origin, X along the leg outward, Z up."""
    apmin, apmax = ap_range(i)
    b, s = np.radians(P_["bend"]), np.radians(P_["sweep"])
    K = np.array([P_["L1"], 0, 0])
    d = np.array([np.cos(b), -np.sin(b) * np.sin(s), -np.sin(b) * np.cos(s)])
    F = K + P_["L2"] * d
    mouth = apmax + BALL / 2 + 0.6
    bottom = apmin - BALL / 2 - 0.6
    t_end = yoke_size()[0] / 2 + 3.0                                           # tube stays out of the fork at 23° tilt
    part = cyl([-(mouth + t_end) / 2, 0, 0], [1, 0, 0], TUBE / 2, mouth - t_end) \
        & Pos(-(mouth + t_end) / 2, 0, 0) * Box(mouth - t_end, TUBE_W, TUBE)     # inner tube, flat sides
    a = np.array([0, ARM_DY, 0])
    part += bar([-t_end - 1, ARM_DY, 0], a, LEG_W, LEG_H, [0, 1, 0])            # through the fork to the boss
    part += cyl(a, [0, 1, 0], BOSS / 2, LEG_W)                                  # boss at the pivot
    part += bar(a, K + a, LEG_W, LEG_H, [0, 1, 0])                              # outer arm
    part += cyl(K + a, [0, 1, 0], LEG_H / 2, LEG_W)                             # knee
    sh = np.array([0, SHIN_DY, 0])
    part += bar(K + sh, F + sh, SHIN_W, LEG_H, [0, 1, 0])                       # shin
    part += Pos(*(F + sh)) * Sphere(SHIN_W / 2)                                  # foot, as wide as the shin
    bore_len = mouth - bottom
    part -= cyl([-(mouth + bottom) / 2, 0, 0], [1, 0, 0], (BALL + CLR) / 2, bore_len)
    part -= Plane(origin=(-mouth, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)).location * \
        Cone(TUBE / 2 - 0.6, (BALL + CLR) / 2, 2.5, align=None)                # flared mouth for the tilting stub
    part -= cyl(a, [0, 1, 0], (SCREW + CLR_STEEL) / 2, LEG_W + 2)                      # pivot screw hole
    return part, dict(mouth=mouth, bottom=bottom, apmin=apmin, apmax=apmax, F=F)


def yoke_size():
    """Fork window (x along the leg, y across, z up) and outer height."""
    win_x = BOSS + 1.6
    win_z = 2 * (TUBE / 2 + win_x / 2 * np.tan(np.radians(PITCH_MAX))) + 0.8
    return win_x, LEG_W + 2 * CLR, win_z, win_z + 2 * YOKE_CAP     # CLR a side: 0.2 was too tight on one print (2026-11-11)


def yoke():
    """Pivot fork, in its own frame: P at the origin, leg along X, pivot screw along Y. It swings on two M3 screws used
    as pins: each is held in the rim (or the test frame) by a nut and its tip turns in a blind hole in the fork's top
    or bottom."""
    win_x, win_y, win_z, h = yoke_size()
    out = Box(win_x, win_y + 2 * YOKE_WALL, h)
    out -= Pos(0, ARM_DY, 0) * Box(win_x + 1, win_y, win_z)                    # window follows the leg's offset
    out -= cyl([0, 0, 0], [0, 1, 0], (SCREW + CLR_STEEL) / 2, 30)
    for sz in (1, -1):
        out -= Pos(0, 0, sz * (h / 2 - 1.75)) * Cylinder((SCREW + CLR_STEEL) / 2, 3.6)       # pin hole for the M3's tip
    return out


def gear_profile(teeth, m=MOD, n=12):
    """Involute spur gear outline (20° pressure angle), points in the XY plane."""
    rp = m * teeth / 2
    rb = rp * np.cos(np.radians(20))
    ra, rf = rp + m, rp - 1.25 * m
    inv = lambda a: np.tan(a) - a
    t_p = np.arccos(rb / rp)
    half = np.pi / (2 * teeth) + inv(t_p)                     # half tooth angle at the base circle
    pts = []
    for k in range(teeth):
        c = 2 * np.pi * k / teeth
        rs = np.linspace(max(rb, rf), ra, n)
        a = np.arccos(np.clip(rb / rs, -1, 1))
        side = [(r, half - inv(t)) for r, t in zip(rs, a)]
        flank = [(rf, half)] + side if rf < rb else side
        for r, ang in flank:
            pts.append((r * np.cos(c - ang), r * np.sin(c - ang)))
        for r, ang in reversed(flank):
            pts.append((r * np.cos(c + ang), r * np.sin(c + ang)))
    return pts


def gear(teeth, t=GEAR_T):
    return extrude(Polygon(*gear_profile(teeth), align=None), amount=t)


def shaft_phases(i):
    return np.pi * sim.GROUP["R"][i], np.pi * sim.GROUP["L"][i]


def crankshaft(i):
    """Crankshaft of leg pair i, along X, centred on the body axis (x = 0 here), at crank angle 0."""
    r, xc = P_["r"], P_["XC"]
    web_out = WEB_OUT_REAR if i == 3 else WEB_OUT
    part = Plane.YZ.location * gear(SHAFT_TEETH)
    part = Pos(-GEAR_T / 2, 0, 0) * part
    part += cyl([0, 0, 0], [1, 0, 0], JOURNAL / 2, 2 * WEB_IN + 0.01)
    for sx, ph in zip((1, -1), shaft_phases(i)):
        # pin offset in the crank plane: e1 = -Y, e2 = Z (as in the simulator)
        off = np.array([0, -r * np.cos(ph), r * np.sin(ph)])
        xw = sx * (WEB_IN + web_out) / 2
        part += cyl([xw, 0, 0], [1, 0, 0], JOURNAL / 2 + 1.2, web_out - WEB_IN)
        part += cyl([xw + off[0], off[1], off[2]], [1, 0, 0], STUB / 2 + 1.0, web_out - WEB_IN)
        part += bar([xw, 0, 0], [xw, off[1], off[2]], web_out - WEB_IN, STUB + 2, [1, 0, 0])
        x0, x1 = sx * web_out, sx * xc
        part += cyl([(x0 + x1) / 2, off[1], off[2]], [1, 0, 0], STUB / 2, abs(x1 - x0))
        part += Pos(x1, off[1], off[2]) * Sphere(BALL / 2)
    return part


def shaft_yz():
    return [(sim.crank_centre(P_, "rows", i, l[2], l[3])[1], sim.NOTCH_Z + P_["H"])
            for i, l in enumerate(x for x in sim.pivots() if x[0] == "R")]


def idlers():
    """(y, z, teeth) of the idler between each pair of neighbouring shafts, below the line of shafts."""
    sh = shaft_yz()
    rs = MOD * SHAFT_TEETH / 2
    out = []
    for (y1, z), (y2, _) in zip(sh, sh[1:]):
        half = (y2 - y1) / 2
        n = 10
        while rs + MOD * n / 2 < half + 1.5:
            n += 1
        cd = rs + MOD * n / 2
        out.append(((y1 + y2) / 2, z - np.sqrt(cd ** 2 - half ** 2), n))
    return out


def spine():
    """Two walls along Y at |x| = WALL_IN..WALL_OUT, joined by end blocks; journal slots open at the top."""
    sh, idl = shaft_yz(), idlers()
    z_top = sh[0][1] + 6
    z_bot = min(z - MOD * (n / 2 + 1) for _, z, n in idl) - 1.5
    y0, y1 = sh[0][0] - 12, sh[-1][0] + 12              # end blocks clear of the gear teeth (tip radius 7)
    t = WALL_OUT - WALL_IN
    part = None
    for sx in (1, -1):
        w = Pos(sx * (WALL_IN + WALL_OUT) / 2, (y0 + y1) / 2, (z_top + z_bot) / 2) * Box(t, y1 - y0, z_top - z_bot)
        part = w if part is None else part + w
    for y in (y0 + 1.5, y1 - 1.5):
        part += Pos(0, y, (z_top + z_bot) / 2) * Box(2 * WALL_OUT, 3, z_top - z_bot)
    for y, z in sh:
        part -= cyl([0, y, z], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
        part -= Pos(0, y, (z + z_top) / 2 + 1) * Box(20, JOURNAL + CLR, z_top - z + 2)
    for y, z, n in idl:
        part -= cyl([0, y, z], [1, 0, 0], (PIN + CLR_STEEL) / 2, 20)
    return Pos(CX, 0, 0) * part, (y0, y1, z_bot, z_top)


def idler_part(n):
    g = gear(n, GEAR_T - 0.4)
    return g - Cylinder((PIN + CLR_STEEL) / 2, 20)


# --- placement ------------------------------------------------------------------------------------------------
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


def assembly(theta, parts):
    """Every part placed at crank angle theta (rad): list of (name, shape)."""
    out = []
    sh = shaft_yz()
    for l in legs_at(theta):
        i = l["i"]
        R = leg_frame(l["u"])
        yaw = np.arctan2(l["u"][1], l["u"][0])
        lg = place(parts[f"leg-{NAMES[i]}-right"], R, l["P"])
        yk = place(parts["pivot"], rot_z(yaw), l["P"])
        out += [(f"leg{i}R", lg), (f"pivot{i}R", yk), (f"leg{i}L", mirror_x(lg)), (f"pivot{i}L", mirror_x(yk))]
        # the simulator's pin is O + r(cos θ e1 + sin θ e2) with e1 = -Y, e2 = Z: a rotation by -θ about +X
        out.append((f"crankshaft{i}", place(parts[f"crankshaft-{i + 1}"], rot_x(-theta), [CX, *sh[i]])))
    out.append(("spine", parts["spine"]))
    for k, (y, z, n) in enumerate(idlers()):
        out.append((f"idler{k}", Pos(CX - (GEAR_T - 0.4) / 2, y, z) * (Plane.YZ.location * parts[f"idler-{k + 1}"])))
    return out


def test_frame(parts):
    """Stand for the right middle leg (i = 1) and crankshaft 2, in robot coordinates; returns the frame part."""
    l = [x for x in sim.pivots() if x[0] == "R" and x[1] == 1][0]
    P = l[2]
    sp_box = parts["_spine_box"]
    y_sh, z_sh = shaft_yz()[1]
    th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    feet = np.array([legs_at(t)[1]["F"] for t in th])
    z_floor = feet[:, 2].min() - 3                         # plate top just under the lowest foot
    plate_t = 4
    x0, x1 = CX - WALL_OUT - 6, P[0] + 12
    ya, yb = y_sh - 14, y_sh + 14
    frame = Pos((x0 + x1) / 2, (ya + yb) / 2, z_floor - plate_t / 2) * Box(x1 - x0, yb - ya, plate_t)
    # spine slice: two walls with the journal slot, from the plate up to the shaft + 6
    zt = z_sh + 6
    for sx in (1, -1):
        frame += Pos(CX + sx * (WALL_IN + WALL_OUT) / 2, y_sh, (zt + z_floor) / 2) * \
            Box(WALL_OUT - WALL_IN, 2 * KEEP_Y, zt - z_floor)
    # end blocks between the walls, clear of the gear (tip radius 7), each with a nut pocket for a keeper screw
    for sy in (1, -1):
        yc = y_sh + sy * (KEEP_GAP + KEEP_Y) / 2
        frame += Pos(CX, yc, (zt + z_floor) / 2) * Box(2 * WALL_IN + 0.01, KEEP_Y - KEEP_GAP, zt - z_floor)
        ys = y_sh + sy * KEEP_SCREW_Y
        frame -= Pos(CX, ys, zt - 4.5) * Cylinder((SCREW + CLR_STEEL) / 2, 9.2)
        frame -= Pos(CX, (ys + y_sh + sy * (KEEP_Y + 1)) / 2, zt - 5.5) * \
            Box(NUT_AF + 0.3, abs(y_sh + sy * (KEEP_Y + 1) - ys) + (NUT_AF + 0.3) / 2, NUT_T + 0.3)
    frame -= cyl([CX, y_sh, z_sh], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
    frame -= Pos(CX, y_sh, (z_sh + zt) / 2 + 1) * Box(20, JOURNAL + CLR, zt - z_sh + 2)
    # the gear must clear the plate: cut a pocket under it
    frame -= Pos(CX, y_sh, z_floor - plate_t / 2) * Box(2 * WALL_IN - 0.5, 2 * (SHAFT_TEETH / 2 + 1.5), plate_t + 1)
    # pivot bracket: two arms above and below the fork, reaching past it from a post beside the leg (+Y, behind it).
    # An M3×10 through each arm, locked to the arm by a nut on its inner face; the screw's tip goes 3 mm into the
    # fork and is the vertical axis it swings on
    _, win_y, _, h = yoke_size()
    arm_t, gap = 3.0, NUT_T + 0.4
    post_y = P[1] + (win_y + 2 * YOKE_WALL) / 2 + 7
    z_up, z_dn = P[2] + h / 2 + gap + arm_t / 2, P[2] - h / 2 - gap - arm_t / 2
    for zc in (z_up, z_dn):
        ya, yb_ = P[1] - 5, post_y + 3                                              # the hole is 5 mm from the arm's end
        frame += Pos(P[0], (ya + yb_) / 2, zc) * Box(8, yb_ - ya, arm_t)
        frame -= Pos(P[0], P[1], zc) * Cylinder((SCREW + CLR_STEEL) / 2, arm_t + 1)
    frame += Pos(P[0], post_y + 1.5, (z_up + arm_t / 2 + z_floor) / 2) * Box(8, 6, z_up + arm_t / 2 - z_floor)
    # plate reaches the post
    frame += Pos(P[0], (yb + post_y + 4.5) / 2, z_floor - plate_t / 2) * Box(12, post_y + 4.5 - yb + 1, plate_t)
    return frame, z_floor


def keeper(parts):
    """Cap over the test frame's journal slots, in robot coordinates (print it upside down): a bridge on top of the
    walls and end blocks, a pocket for the gear's tips, and a tongue down each slot whose round end completes the
    journal hole. Two M3×12 down through it into nuts in the end blocks."""
    y_sh, z_sh = shaft_yz()[1]
    zt = z_sh + 6
    t = 4.0
    part = Pos(CX, y_sh, zt + t / 2) * Box(2 * WALL_OUT, 2 * KEEP_Y, t)
    part -= Pos(CX, y_sh, zt) * Box(2 * WALL_IN, 2 * (MOD * (SHAFT_TEETH / 2 + 1) + 0.6), 2 * 1.6 + 0.6)
    tw = JOURNAL + CLR - CLR                                  # tongue: the slot's width less a sliding clearance
    for sx in (1, -1):
        xc = CX + sx * (WALL_IN + WALL_OUT) / 2
        tongue = Pos(xc, y_sh, (z_sh + zt) / 2 + 0.01) * Box(WALL_OUT - WALL_IN, tw, zt - z_sh + 0.02)
        part += tongue
    part -= cyl([CX, y_sh, z_sh], [1, 0, 0], (JOURNAL + CLR) / 2, 20)
    for sy in (1, -1):
        part -= Pos(CX, y_sh + sy * KEEP_SCREW_Y, zt + t / 2) * Cylinder((SCREW + CLR_STEEL) / 2, t + 1)
    return part


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--assembly", type=float, nargs="*", help="crank angles (degrees) to export the assembly at")
    ap.add_argument("--out", default=HERE)
    args = ap.parse_args()

    parts, info = {}, {}
    for i, name in ((0, "front"), (1, "middle"), (3, "rear")):
        p, inf = leg(i)
        parts[f"leg-{name}-right"] = p
        parts[f"leg-{name}-left"] = mirror(p, Plane.XZ)
        info[name] = inf
    parts["pivot"] = yoke()
    for i in range(4):
        parts[f"crankshaft-{i + 1}"] = crankshaft(i)
    sp, box = spine()
    parts["spine"] = sp
    parts["_spine_box"] = box
    for k, (_, _, n) in enumerate(idlers()):
        parts[f"idler-{k + 1}"] = idler_part(n)
    frame, z_floor = test_frame(parts)
    parts["test-frame"] = frame
    parts["test-frame-keeper"] = keeper(parts)

    for name, p in parts.items():
        if name.startswith("_"):
            continue
        export_step(p, os.path.join(args.out, f"{name}.step"))
        stl = os.path.join(args.out, f"{name}.stl")
        export_stl(p, stl, tolerance=0.02, angular_tolerance=0.15)
        watertight(stl)
        bb = p.bounding_box()
        print(f"{name:22s} {bb.size.X:6.1f} × {bb.size.Y:6.1f} × {bb.size.Z:6.1f} mm  volume {p.volume / 1000:5.2f} cm³")
    for name, v in info.items():
        print(f"leg {name}: ball travels {v['apmin']:.1f}-{v['apmax']:.1f} mm from the pivot, bore "
              f"{v['bottom']:.1f}-{v['mouth']:.1f} mm")
    print("idlers (y, z, teeth):", [(round(y, 1), round(z, 1), n) for y, z, n in idlers()])
    print(f"test frame plate top at z {z_floor:.1f}")
    for a in args.assembly or []:
        asm = assembly(np.radians(a), parts)
        c = Compound(children=[s for _, s in asm])
        export_step(c, os.path.join(args.out, f"assembly-{a:g}.step"))
        export_stl(c, os.path.join(args.out, f"assembly-{a:g}.stl"), tolerance=0.05, angular_tolerance=0.3)
        print(f"wrote assembly-{a:g}")


if __name__ == "__main__":
    main()
