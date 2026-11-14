#!/usr/bin/env python3
"""Spider-Bot crankshafts and idler gears, modelled in code (build123d) from the simulator's geometry.

Parts (all PLA):
  crankshaft-{1..4}  one piece: gear in the middle, a journal and a crank either side, a ball on each crank pin. Front
                     to rear; the cranks are printed at their phase. Each gear is turned by its own offset to the
                     cranks (gear_offsets()), so every idler meshes both neighbours; dots on the +X web give its number.
  idler-{1..3}       idler gears between the crankshafts, so all four turn the same way.

Also the numbers every part that holds the crankshafts uses: the spine walls (WALL_IN, WALL_OUT), where the shafts
and idlers sit (shaft_yz(), idlers()), and how close a cap's tongues may come to the gears (TONGUE_IN, TONGUE_OUT).

Coordinates as in ../README.md (mm, Z up, forward = -Y, +X = right). Geometry from ../../sim/toy_leg_3d_rows_cad.json
(first entry), through ../common.py. Every part is exported to out/ as STEP and STL; the crankshafts in robot
orientation with the gear centred on x = 0 (print them axis horizontal), the idlers flat.

Usage:
    python3 build.py               # every part
    python3 build.py --part idler-3
    python3 check_gear_train.py    # every mesh in 2D, every 1°
"""
import os
import sys

import numpy as np
from build123d import Cone, Cylinder, Plane, Polygon, Pos, Rot, Sphere, extrude

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K  # noqa: E402
from cad.common import CLR_STEEL, P_, PIN, bar, cyl, marks, sim  # noqa: E402,F401

OUT = os.path.join(HERE, "out")

# --- parameters (mm) -----------------------------------------------------------------------------------------
BALL = 3.6          # ball on the crank pin
STUB = 2.2          # crank pin stub that carries the ball
JOURNAL = 4.0       # crankshaft journal diameter
GEAR_T = 3.0        # gear face width
MOD = 1.0           # gear module
SHAFT_TEETH = 12
WALL_IN, WALL_OUT = 1.75, 4.25     # spine walls span |x| from WALL_IN to WALL_OUT about the body axis
WEB_IN, WEB_OUT = 4.5, 6.5         # crank web, |x|
WEB_OUT_REAR = 6.0  # crankshaft 4's webs are thinner: the rear leg's tube came 0.15 mm from the web's outer face
KEEP_GAP = 8.5      # end blocks of whatever holds the shafts start this far (y) from an end shaft, clear of the gear's
                    # tips (radius 7): test frame, gear train test spine, base v1's front end block
# gear train v2 (the v1 test jammed: idlers 1-2 could not mesh both neighbours, zero backlash, shafts lifted out)
PRESSURE = 20.0      # pressure angle (deg), as in gear_profile()
IDLER_MIN_TEETH = 12 # fewest idler teeth: under 12 the involute is undercut without profile shift (v1 had 11 and 10)
BACKLASH = 0.20      # circumferential backlash per mesh at the pitch circle (brief: 0.1-0.25). 0.20, not 0.15: the
                     # crank gears print axis-horizontal (rougher flanks), and cad_verify wants >= 0.08 mm a side
CD_EXTRA = BACKLASH / (2 * np.tan(np.radians(PRESSURE)))   # centre distance added per mesh for that backlash (0.27)
# cap tongues (gear train test cap and base v1 cap). Gear train test v2, 2026-11-12: with tongues over the whole wall
# (|x| 1.75-4.25) the gears turned 0.25 mm from the tongues' faces, nominal; with the cap free in X, the shaft's float
# and the print a little fat, the tongues pinched the gears and nothing turned. Now they stand over the outer part of
# each wall only, GEAR_AXIAL_CLR clear of the gear faces with the cap and the shaft at their worst X positions
CAP_CLR = 0.3        # tongue in its journal slot (../base/build.py CAP_CLR)
SHAFT_FLOAT = WEB_IN - WALL_OUT    # crankshaft's axial float either way: webs against the walls' outer faces (0.25)
GEAR_AXIAL_CLR = 0.8 # least axial gap from a spinning gear face to a stationary printed face (cap tongue)
CAP_X_PLAY = CAP_CLR # worst X play of a cap either way: base v1's cap in its deck opening (../base/build.py:
                     # opening().buffer(-CAP_CLR)); the test cap's skirts allow less (gear-train-test TEST_SKIRT_CLR)
TONGUE_IN = GEAR_T / 2 + SHAFT_FLOAT + CAP_X_PLAY + GEAR_AXIAL_CLR   # tongue's inner face, |x| (2.85)
TONGUE_OUT = WALL_OUT - CAP_X_PLAY # outer face (3.95): never past the walls' outer faces, so the webs only touch the walls


# --- parts ---------------------------------------------------------------------------------------------------
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
    """Crankshaft of leg pair i, along X, centred on the body axis (x = 0 here), at crank angle 0. Its gear is turned by
    gear_offsets()[i] relative to the cranks, so every idler meshes with both neighbours at the designed crank phases;
    i + 1 dots on the +X web's outer face tell the shafts apart and which end goes to the right (+X) legs."""
    r, xc = P_["r"], P_["XC"]
    web_out = WEB_OUT_REAR if i == 3 else WEB_OUT
    part = Rot(np.degrees(gear_offsets()[i]), 0, 0) * (Plane.YZ.location * gear(SHAFT_TEETH))
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
    part -= marks(i + 1, web_out, 0, 0)          # on the hub of the +X web, round the axis (hub radius 3.2)
    return part


def shaft_yz():
    return [(sim.crank_centre(P_, "rows", i, l[2], l[3])[1], sim.NOTCH_Z + P_["H"])
            for i, l in enumerate(x for x in sim.pivots() if x[0] == "R")]


def idlers():
    """(y, z, teeth) of the idler between each pair of neighbouring shafts, below the line of shafts. At least
    IDLER_MIN_TEETH teeth, and CD_EXTRA further from both shafts than the theoretical centre distance (backlash)."""
    sh = shaft_yz()
    rs = MOD * SHAFT_TEETH / 2
    out = []
    for (y1, z), (y2, _) in zip(sh, sh[1:]):
        half = (y2 - y1) / 2
        n = IDLER_MIN_TEETH
        while rs + MOD * n / 2 < half + 1.5:
            n += 1
        cd = rs + MOD * n / 2 + CD_EXTRA
        out.append(((y1 + y2) / 2, z - np.sqrt(cd ** 2 - half ** 2), n))
    return out


def _mesh_angles(k):
    """Directions (rad, in the YZ plane from +Y towards +Z) from shaft k and from shaft k + 1 to idler k."""
    (ya, za), (yb, zb) = shaft_yz()[k], shaft_yz()[k + 1]
    y, z, _ = idlers()[k]
    return np.arctan2(z - za, y - ya), np.arctan2(z - zb, y - yb)


def gear_offsets():
    """Angle (rad, about +X) of each crankshaft's gear relative to its cranks, so that every idler meshes with both
    neighbours while the cranks keep their designed phases (sim.GROUP).

    Along the line from a gear's centre towards its partner, u = N (β - φ) / 2π (mod 1) says where the teeth are
    (0: a tooth points at the partner; φ = angle of tooth 0). Two gears mesh, centred in their backlash, when
    u_gear + u_partner = 1/2 (mod 1), and that sum stays the same while they turn. Writing it for idler k against
    shaft k and against shaft k + 1 and subtracting gives the offset of shaft k + 1 from that of shaft k. Shaft 1
    keeps its gear as in v1 (offset 0); the others follow, each printed with its own offset."""
    out = [0.0]
    pitch = 2 * np.pi / SHAFT_TEETH
    for k, (_, _, n) in enumerate(idlers()):
        ba, bb = _mesh_angles(k)
        out.append((out[-1] - (SHAFT_TEETH + n) * (ba - bb) / SHAFT_TEETH) % pitch)
    return out


def idler_phase(k):
    """Angle (rad, about +X) of idler k's tooth 0 at crank angle 0, meshing both its shafts. At crank angle θ the shafts
    turn by -θ and the idler by +θ·SHAFT_TEETH/n."""
    n = idlers()[k][2]
    ba, _ = _mesh_angles(k)
    da = gear_offsets()[k]
    return (ba + np.pi - (np.pi - SHAFT_TEETH * (ba - da)) / n) % (2 * np.pi / n)


def idler_part(n):
    """Idler gear, printed flat. The first 0.2 mm layer's outline is 0.2 mm smaller and the bore has a 0.4 mm chamfer
    at the bed (elephant's foot)."""
    t = GEAR_T - 0.4
    import shapely.geometry as sg
    small = sg.polygon.orient(sg.Polygon(gear_profile(n)).buffer(-0.2, join_style=2), 1.0)   # CCW: extrudes up
    g = extrude(Polygon(*list(small.exterior.coords)[:-1], align=None), amount=0.2)
    g += Pos(0, 0, 0.2) * extrude(Polygon(*gear_profile(n), align=None), amount=t - 0.2)
    g -= Cylinder((PIN + CLR_STEEL) / 2, 20)
    g -= Pos(0, 0, -0.01) * Cone((PIN + CLR_STEEL) / 2 + 0.4, (PIN + CLR_STEEL) / 2, 0.41, align=None)
    return g


PARTS = {**{f"crankshaft-{i + 1}": (lambda i=i: crankshaft(i)) for i in range(4)},
         **{f"idler-{k + 1}": (lambda k=k: idler_part(idlers()[k][2])) for k in range(3)}}


def main():
    args = K.part_args(__doc__, PARTS)
    K.build_parts(PARTS, args.part or PARTS, OUT)
    print("idlers (y, z, teeth):", [(round(y, 2), round(z, 2), n) for y, z, n in idlers()])
    print(f"centre distance + {CD_EXTRA:.3f} mm per mesh (backlash {BACKLASH} mm)")
    print("crankshaft gear offsets (deg):", [round(np.degrees(a), 2) for a in gear_offsets()])
    print("idler phases at crank 0 (deg):", [round(np.degrees(idler_phase(k)), 2) for k in range(3)])


if __name__ == "__main__":
    main()
