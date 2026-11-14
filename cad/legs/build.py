#!/usr/bin/env python3
"""Spider-Bot legs and their pivot forks, modelled in code (build123d) from the simulator's geometry; and the whole
drive placed by the simulator's kinematics (assembly(), poses()), which the checks and base v1 use.

Parts (all PLA):
  leg-{front,middle,rear}-{right,left}  one rigid bent leg. Its inner end is a tube: the ball on the crank pin slides
                                         in its bore. At the rim it has a cross hole for the pivot pin.
  pivot                                  fork around the leg at the rim: a 3 mm pin across it carries the leg (tilts
                                         up and down) and two printed trunnions on top and bottom let it swing.

The rest of the drive is in ../crankshafts (crankshafts, idlers) and the test rigs in ../gear-train-test and
../test-frame. Coordinates as in ../README.md (mm, Z up, forward = -Y, +X = right). Geometry from
../../sim/toy_leg_3d_rows_cad.json (first entry), through ../common.py. Every part is exported to out/ as STEP (for
Onshape) and STL (for Bambu Studio), in its own frame (print orientation: see README); `--assembly` also writes the
whole drive, placed by the simulator's kinematics, at the given crank angles.

Usage:
    python3 build.py                 # every part into out/
    python3 build.py --part pivot    # one part
    python3 build.py --assembly 0    # plus out/assembly-0.step / .stl at crank angle 0°
    python3 check.py --gaps          # then: collision and gap check over a full turn
"""
import functools
import os
import sys

import numpy as np
from build123d import Box, Compound, Cone, Cylinder, Plane, Pos, Rot, Sphere, export_step, export_stl, mirror

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(CAD, ".."))
from cad import common as K, design  # noqa: E402
from cad.common import (CLR, CLR_STEEL, CX, P_, SCREW, bar, cyl, mirror_x, place, rot_x, rot_z,  # noqa: E402,F401
                        sim, unit)

C = design("crankshafts")
OUT = os.path.join(HERE, "out")

# --- parameters (mm) -----------------------------------------------------------------------------------------
BALL = C.BALL       # ball on the crank pin, in the leg's bore
TUBE = 7.6          # height of the leg's inner tube (round top and bottom)
TUBE_W = 5.6        # its width across: flat sides, so the middle legs' tubes clear each other
LEG_W, LEG_H = 5.0, 6.0     # leg bar: width (across, the print height) × height
ARM_DY = -(TUBE_W - LEG_W) / 2    # arm, boss and knee flush with the tube's -Y face (on the bed when printed)
SHIN_W = 4.5        # shin and foot a little thinner: the middle legs' shins pass 0.8 mm apart
SHIN_DY = -(TUBE_W - SHIN_W) / 2   # shin flush with the leg's -Y face (the face on the bed when printed)
BOSS = 9.0          # leg boss around the pivot pin
YOKE_WALL = 2.0      # fork side walls
YOKE_CAP = 4.0       # fork top and bottom walls, with a blind hole for the M3 screw it swings on
PITCH_MAX = 28.0     # the leg tilts 6-23° up (rear leg most) (the crank is lower than the rim): the fork window allows this much
NAMES = ["front", "middle", "middle", "rear"]


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
@functools.lru_cache(maxsize=None)
def leg(i):
    """Right leg i in its own frame: P at the origin, X along the leg outward, Z up."""
    apmin, apmax = ap_range(i)
    b, s = np.radians(P_["bend"]), np.radians(P_["sweep"])
    K_ = np.array([P_["L1"], 0, 0])
    d = np.array([np.cos(b), -np.sin(b) * np.sin(s), -np.sin(b) * np.cos(s)])
    F = K_ + P_["L2"] * d
    mouth = apmax + BALL / 2 + 0.6
    bottom = apmin - BALL / 2 - 0.6
    t_end = yoke_size()[0] / 2 + 3.0                                           # tube stays out of the fork at 23° tilt
    part = cyl([-(mouth + t_end) / 2, 0, 0], [1, 0, 0], TUBE / 2, mouth - t_end) \
        & Pos(-(mouth + t_end) / 2, 0, 0) * Box(mouth - t_end, TUBE_W, TUBE)     # inner tube, flat sides
    a = np.array([0, ARM_DY, 0])
    part += bar([-t_end - 1, ARM_DY, 0], a, LEG_W, LEG_H, [0, 1, 0])            # through the fork to the boss
    part += cyl(a, [0, 1, 0], BOSS / 2, LEG_W)                                  # boss at the pivot
    part += bar(a, K_ + a, LEG_W, LEG_H, [0, 1, 0])                             # outer arm
    part += cyl(K_ + a, [0, 1, 0], LEG_H / 2, LEG_W)                            # knee
    sh = np.array([0, SHIN_DY, 0])
    part += bar(K_ + sh, F + sh, SHIN_W, LEG_H, [0, 1, 0])                      # shin
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


LEG_I = {"front": 0, "middle": 1, "rear": 3}
PARTS = {**{f"leg-{n}-right": (lambda i=i: leg(i)[0]) for n, i in LEG_I.items()},
         **{f"leg-{n}-left": (lambda i=i: mirror(leg(i)[0], Plane.XZ)) for n, i in LEG_I.items()},
         "pivot": yoke}


# --- the whole drive, placed --------------------------------------------------------------------------------------
def stl(name):
    """Path of a drive part's STL (without .stl in name), in the design folder that builds it."""
    folder = ("crankshafts" if name.startswith(("crankshaft", "idler")) else
              "gear-train-test" if name in ("spine", "test-cap") else
              "test-frame" if name.startswith("test-frame") else "legs")
    return os.path.join(CAD, folder, "out", name + ".stl")


def assembly(theta, parts):
    """Every part placed at crank angle theta (rad): list of (name, shape). parts: name -> shape of every leg, the
    pivot, the crankshafts, the idlers and the gear train test's spine."""
    out = []
    sh = C.shaft_yz()
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
    for k, (y, z, n) in enumerate(C.idlers()):
        a = np.degrees(C.idler_phase(k) + theta * C.SHAFT_TEETH / n)
        out.append((f"idler{k}", Pos(CX - (C.GEAR_T - 0.4) / 2, y, z) *
                    (Rot(a, 0, 0) * (Plane.YZ.location * parts[f"idler-{k + 1}"]))))
    return out


def tmat(R, t):
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R, t
    return M


MIRROR = np.diag([-1.0, 1, 1, 1])
MIRROR[0, 3] = 2 * CX
YZ = np.column_stack([[0, 1, 0], [0, 0, 1], [1, 0, 0]])     # build123d Plane.YZ: local X → Y, Y → Z, Z → X


def poses(theta):
    """(name, stl name, 4×4 matrix) of every part at crank angle theta, as in assembly(); stl(name) gives the file."""
    out = []
    sh = C.shaft_yz()
    for l in legs_at(theta):
        i = l["i"]
        R = leg_frame(l["u"])
        yaw = np.arctan2(l["u"][1], l["u"][0])
        Ml, My = tmat(R, l["P"]), tmat(rot_z(yaw), l["P"])
        out += [(f"leg{i}R", f"leg-{NAMES[i]}-right", Ml), (f"pivot{i}R", "pivot", My),
                (f"leg{i}L", f"leg-{NAMES[i]}-right", MIRROR @ Ml), (f"pivot{i}L", "pivot", MIRROR @ My)]
        out.append((f"crankshaft{i}", f"crankshaft-{i + 1}", tmat(rot_x(-theta), [CX, *sh[i]])))
    out.append(("spine", "spine", np.eye(4)))
    for k, (y, z, n) in enumerate(C.idlers()):
        a = C.idler_phase(k) + theta * C.SHAFT_TEETH / n        # its real angle, meshing both crankshafts
        out.append((f"idler{k}", f"idler-{k + 1}", tmat(rot_x(a) @ YZ, [CX - (C.GEAR_T - 0.4) / 2, y, z])))
    return out


def main():
    def extra(ap):
        ap.add_argument("--assembly", type=float, nargs="*", help="crank angles (degrees) to export the assembly at")
    args = K.part_args(__doc__, PARTS, extra)
    K.build_parts(PARTS, args.part or PARTS, OUT)
    for name, i in LEG_I.items():
        if args.part and not any(p.startswith(f"leg-{name}") for p in args.part):
            continue
        v = leg(i)[1]
        print(f"leg {name}: ball travels {v['apmin']:.1f}-{v['apmax']:.1f} mm from the pivot, bore "
              f"{v['bottom']:.1f}-{v['mouth']:.1f} mm")
    if args.assembly:
        G = design("gear-train-test")
        parts = {n: f() for n, f in PARTS.items()}
        parts.update({n: f() for n, f in C.PARTS.items()})
        parts["spine"] = G.PARTS["spine"]()
        for a in args.assembly:
            asm = assembly(np.radians(a), parts)
            c = Compound(children=[s for _, s in asm])
            export_step(c, os.path.join(OUT, f"assembly-{a:g}.step"))
            export_stl(c, os.path.join(OUT, f"assembly-{a:g}.stl"), tolerance=0.05, angular_tolerance=0.3)
            print(f"wrote assembly-{a:g}")


if __name__ == "__main__":
    main()
