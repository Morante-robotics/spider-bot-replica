"""cad_verify spec for the gear train test v2 (print/gear-train-test-v2.3mf): the test spine on its foot, the 4
crankshafts, the 3 idlers on M3×12 screws as axles (nut on the -X side), and the test cap screwed down with 2 × M3×12,
turned by hand over a full crank turn.

Every gear is placed at its real angle: crankshaft i at gear_offsets()[i] - θ (its cranks at their designed phase),
idler k at idler_phase(k) + θ·12/n. The idler phases are the designed ones, not a best fit: if a crankshaft were a
tooth off, the teeth would overlap here.

    python3 ../../../tools/cad_verify.py verify_gear_train.py --out verify-gear-train.txt --render images/verify
"""
import importlib.util
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import build as B  # noqa: E402
from cad_verify import rod  # noqa: E402

# the test must hold the shafts as base v1 does: same top (tongue length) and same tongue clearance
_s = importlib.util.spec_from_file_location("base_build", os.path.join(HERE, "..", "base", "build.py"))
BASE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(BASE)
assert abs(B.TEST_TOP - BASE.DECK_BOT) < 1e-6 and abs(B.CAP_CLR - BASE.CAP_CLR) < 1e-6, "test cap differs from base cap"

SH, IDL = B.shaft_yz(), B.idlers()
OFF = B.gear_offsets()
PHASE = [B.idler_phase(k) for k in range(3)]
YZ = np.eye(4)
YZ[:3, :3] = np.column_stack([[0, 1, 0], [0, 0, 1], [1, 0, 0]])   # build123d Plane.YZ


def rx(a, y, z):
    """Rotation by a (rad) about the X axis through (y, z)."""
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[1:3, 1:3] = [[c, -s], [s, c]]
    M[1:3, 3] = [y - c * y + s * z, z - s * y - c * z]
    return M


def shaft_pose(i, a):
    M = np.eye(4)
    M[:3, 3] = [B.CX, *SH[i]]
    return M @ rx(-a, 0, 0)


def idler_base(k):
    y, z, _ = IDL[k]
    M = np.eye(4)
    M[:3, 3] = [B.CX - (B.GEAR_T - 0.4) / 2, y, z]
    return M @ YZ


def union(*ms):
    return trimesh.boolean.union(list(ms), engine="manifold")


def m3(p_head, axis, length):
    """M3 socket head screw: shank of `length` from p_head along axis, head on the other side of p_head."""
    axis = np.asarray(axis, float)
    return union(rod(3.0, length, p_head, axis), rod(B.HEAD_D, B.HEAD_H, p_head, -axis))


X_OUT = B.CX + B.WALL_OUT
PARTS = {"spine": {"stl": "spine.stl", "fixed": True},
         "cap": {"stl": "test-cap.stl"}}
for i in range(4):
    PARTS[f"crankshaft{i + 1}"] = {"stl": f"crankshaft-{i + 1}.stl"}
for k, (y, z, n) in enumerate(IDL):
    PARTS[f"idler{k + 1}"] = {"stl": f"idler-{k + 1}.stl"}
    # M3×12 as the axle: head on the +X wall, through both walls and the idler, nut on the -X wall
    PARTS[f"axle{k + 1}"] = {"mesh": m3([X_OUT, y, z], [-1, 0, 0], 12), "hardware": True, "fixed": True}
    PARTS[f"axlenut{k + 1}"] = {"mesh": rod(B.NUT_AF / np.cos(np.pi / 6), B.NUT_T, [B.CX - B.WALL_OUT, y, z], [-1, 0, 0],
                                            n=6), "hardware": True, "fixed": True}
CAP_TOP = B.TEST_TOP + B.TEST_CAP_T
for j, (y, _) in enumerate(B.cap_screws()):
    PARTS[f"capscrew{j + 1}"] = {"mesh": m3([B.CX, y, CAP_TOP], [0, 0, -1], B.CAP_SCREW_L),
                                 "hardware": True, "fixed": True}

MOTION = list(range(0, 360, 5))       # crank angle, degrees (5° steps: a tooth is 30° of crank)


def poses(t):
    a = np.radians(t)
    out = {f"crankshaft{i + 1}": shaft_pose(i, a) for i in range(4)}
    for k, (y, z, n) in enumerate(IDL):
        out[f"idler{k + 1}"] = rx(PHASE[k] + a * B.SHAFT_TEETH / n, y, z) @ idler_base(k)
    return out


GEARS = [(f"crankshaft{k + 1}", f"idler{k + 1}") for k in range(3)] + \
        [(f"crankshaft{k + 2}", f"idler{k + 1}") for k in range(3)]
# backlash 0.2 mm at the pitch circle ≈ 0.1 mm a side along the tooth normal; the generic band (0.08-0.5) fits
GEAR_GAP = (0.08, 0.5)
PAIR_GAP = {**{(f"axle{k + 1}", f"idler{k + 1}"): 0.1 for k in range(3)},      # M3 in a Ø3.3 bore (CLR_STEEL)
            **{(f"capscrew{j + 1}", "spine"): 0.1 for j in range(2)}}          # M3 in its Ø3.3 hole
ALLOWED_CONTACT = {
    **{(f"axle{k + 1}", "spine"): "screw head tightened on the +X wall (shank in a Ø3.3 hole)" for k in range(3)},
    **{(f"axlenut{k + 1}", "spine"): "nut tightened on the -X wall" for k in range(3)},
    **{(f"axle{k + 1}", f"axlenut{k + 1}"): "nut on its screw" for k in range(3)},
    **{(f"capscrew{j + 1}", "cap"): "screw head clamps the cap (shank in a Ø3.3 hole)" for j in range(2)},
    ("cap", "spine"): "cap sits on the spine's top, tongues slide in the slots (0.15 mm a side, CAP_CLR)",
}
RETAIN = {**{f"crankshaft{i + 1}": {"spin": [1, 0, 0], "play": 1.0} for i in range(4)},
          **{f"idler{k + 1}": {"spin": [1, 0, 0], "play": 1.0} for k in range(3)},
          "cap": {"play": 1.0}}
# direction = where each part comes in from: idlers dropped between the walls, axles pushed through from +X with the
# nut from -X, crankshafts dropped into their slots front to rear, then the cap and its screws from above
ASSEMBLY = [("spine", None)] + [(f"idler{k + 1}", [0, 0, 1]) for k in range(3)] + \
           [(f"axle{k + 1}", [1, 0, 0]) for k in range(3)] + [(f"axlenut{k + 1}", [-1, 0, 0]) for k in range(3)] + \
           [(f"crankshaft{i + 1}", [0, 0, 1]) for i in range(4)] + [("cap", [0, 0, 1])] + \
           [(f"capscrew{j + 1}", [0, 0, 1]) for j in range(2)]
PRINT_ORIENT = {"cap": trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])}    # upside down, plate on the bed
SECTIONS = [([B.CX, 0, 0], [1, 0, 0]),                                     # gear plane: all 7 gears, end blocks
            ([B.CX + (B.WALL_IN + B.WALL_OUT) / 2, 0, 0], [1, 0, 0])]      # +X wall: journals, tongues, axles
SECTIONS += [([B.CX, y, z], [0, 1, 0]) for y, z in SH]                     # each journal, tongue and cap
SECTIONS += [([B.CX, y, z], [0, 1, 0]) for y, z, _ in IDL]                 # each idler on its axle
SECTIONS += [([B.CX, y, 0], [0, 1, 0]) for y, _ in B.cap_screws()]         # cap screws and their nut pockets
