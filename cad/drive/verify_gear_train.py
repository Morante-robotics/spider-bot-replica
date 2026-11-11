"""cad_verify spec for the gear train test (print/gear-train-test.3mf): the loose spine, the 4 crankshafts and the
3 idlers on M3×12 screws as axles, turned by hand.

    python3 ../../../tools/cad_verify.py verify_gear_train.py --out verify-gear-train.txt --render images/verify
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import build as B  # noqa: E402
from cad_verify import overlap, rod, to_manifold  # noqa: E402
import trimesh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SH, IDL = B.shaft_yz(), B.idlers()
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


PARTS = {"spine": {"stl": "spine.stl", "fixed": True}}
for i in range(4):
    PARTS[f"crankshaft{i + 1}"] = {"stl": f"crankshaft-{i + 1}.stl"}
for k in range(3):
    PARTS[f"idler{k + 1}"] = {"stl": f"idler-{k + 1}.stl"}
    PARTS[f"axle{k + 1}"] = {"mesh": rod(3.0, 12, [B.CX - 6, IDL[k][0], IDL[k][1]], [1, 0, 0]),
                             "hardware": True, "fixed": True}


def _phase(k):
    """Idler k's starting angle that meshes best with its two crankshafts at 0° (the user turns it until it fits)."""
    y, z, n = IDL[k]
    stl = trimesh.load(os.path.join(HERE, f"idler-{k + 1}.stl"))
    nb = [to_manifold(trimesh.load(os.path.join(HERE, f"crankshaft-{j + 1}.stl"))).transform(shaft_pose(j, 0)[:3])
          for j in (k, k + 1)]
    best = min(np.linspace(0, 2 * np.pi / n, 24, endpoint=False),
               key=lambda p: sum(overlap(to_manifold(stl).transform((rx(p, y, z) @ idler_base(k))[:3]), m) for m in nb))
    return best


PHASE = [_phase(k) for k in range(3)]
MOTION = list(range(0, 360, 10))       # crank angle, degrees


def poses(t):
    a = np.radians(t)
    out = {f"crankshaft{i + 1}": shaft_pose(i, a) for i in range(4)}
    for k, (y, z, n) in enumerate(IDL):
        out[f"idler{k + 1}"] = rx(PHASE[k] + a * B.SHAFT_TEETH / n, y, z) @ idler_base(k)
    return out


GEARS = [(f"crankshaft{k + 1}", f"idler{k + 1}") for k in range(3)] + \
        [(f"crankshaft{k + 2}", f"idler{k + 1}") for k in range(3)]
PAIR_GAP = {(f"axle{k + 1}", f"idler{k + 1}"): 0.1 for k in range(3)}   # M3 in a Ø3.3 bore, as designed (CLR_STEEL)
ALLOWED_CONTACT ={(f"axle{k + 1}", "spine"): "screw threads into its hole" for k in range(3)}
RETAIN = {**{f"crankshaft{i + 1}": {"spin": [1, 0, 0], "play": 1.0} for i in range(4)},
          **{f"idler{k + 1}": {"spin": [1, 0, 0], "play": 1.0} for k in range(3)}}
# direction = where each part comes in from: idlers dropped between the walls, axles pushed through from the side
ASSEMBLY = [("spine", None)] + [(f"idler{k + 1}", [0, 0, 1]) for k in range(3)] + \
           [(f"axle{k + 1}", [1, 0, 0]) for k in range(3)] + [(f"crankshaft{i + 1}", [0, 0, 1]) for i in range(4)]
SECTIONS = [([B.CX, 0, 0], [1, 0, 0]), ([B.CX, SH[1][0], SH[1][1]], [0, 1, 0])]
