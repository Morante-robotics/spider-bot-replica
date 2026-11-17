"""cad_verify spec for the gear train test v2 (print/gear-train-test-v2.3mf): the test spine on its foot, the 4
crankshafts, the 3 idlers on M3×12 screws as axles (nut on the -X side), and the test cap screwed down with 2 × M3×12,
turned by hand over a full crank turn.

Test cap v2.1 (2026-11-12): the v2 cap jammed the gears, its tongues 0.25 mm off the gear faces with everything at
nominal; the cap was free in X and the shaft floats 0.25. So the cap is posed at both X extremes as well
(TEST_SKIRT_CLR either way), and KEEP_OUT carries a zone round every crankshaft gear: its faces thickened by its axial
float plus GEAR_AXIAL_CLR (0.8). No stationary part may enter it, except the spine walls (see the zone's note).
VERIFY_STEP=30 in the environment gives coarse steps for quick runs.

Every gear is placed at its real angle: crankshaft i at gear_offsets()[i] - θ (its cranks at their designed phase),
idler k at idler_phase(k) + θ·12/n. The idler phases are the designed ones, not a best fit: if a crankshaft were a
tooth off, the teeth would overlap here.

    python3 ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits  # noqa: E402
from cad_verify import rod, tool  # noqa: E402

B = design("gear-train-test")      # spine and test cap
C = design("crankshafts")          # crankshafts, idlers, gear phases
# the test must hold the shafts as base v1 does: same top (tongue length) and same tongue clearance
BASE = design("base")
assert abs(B.TEST_TOP - BASE.DECK_BOT) < 1e-6 and abs(C.CAP_CLR - BASE.CAP_CLR) < 1e-6, "test cap differs from base cap"

SH, IDL = C.shaft_yz(), C.idlers()
OFF = C.gear_offsets()
PHASE = [C.idler_phase(k) for k in range(3)]
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
    M[:3, 3] = [K.CX, *SH[i]]
    return M @ rx(-a, 0, 0)


def idler_base(k):
    y, z, _ = IDL[k]
    M = np.eye(4)
    M[:3, 3] = [K.CX - (C.GEAR_T - 0.4) / 2, y, z]
    return M @ YZ


def union(*ms):
    return trimesh.boolean.union(list(ms), engine="manifold")


def m3(p_head, axis, length):
    """M3 socket head screw: shank of `length` from p_head along axis, head on the other side of p_head."""
    axis = np.asarray(axis, float)
    return union(rod(3.0, length, p_head, axis), rod(K.HEAD_D, K.HEAD_H, p_head, -axis))


X_OUT = K.CX + C.WALL_OUT
PARTS = {"spine": {"stl": "out/spine.stl", "fixed": True},
         "cap": {"stl": "out/test-cap.stl"}}
for i in range(4):
    PARTS[f"crankshaft{i + 1}"] = {"stl": f"../crankshafts/out/crankshaft-{i + 1}.stl"}
for k, (y, z, n) in enumerate(IDL):
    PARTS[f"idler{k + 1}"] = {"stl": f"../crankshafts/out/idler-{k + 1}.stl"}
    # M3×12 as the axle: head on the +X wall, through both walls and the idler, nut on the -X wall
    PARTS[f"axle{k + 1}"] = {"mesh": m3([X_OUT, y, z], [-1, 0, 0], 12), "hardware": True, "fixed": True,
                              "label": "M3×12 Allen (eje de la rueda intermedia)"}
    PARTS[f"axlenut{k + 1}"] = {"mesh": rod(K.NUT_AF / np.cos(np.pi / 6), K.NUT_T, [K.CX - C.WALL_OUT, y, z], [-1, 0, 0],
                                            n=6), "hardware": True, "fixed": True, "label": "tuerca M3"}
CAP_TOP = B.TEST_TOP + B.TEST_CAP_T
for j, (y, _) in enumerate(B.cap_screws()):
    PARTS[f"capscrew{j + 1}"] = {"mesh": m3([K.CX, y, CAP_TOP], [0, 0, -1], B.CAP_SCREW_L),
                                 "hardware": True, "fixed": True, "label": "M3×12 Allen (tapa)"}

# step = (crank angle in degrees, cap X shift in mm). 5° steps with the cap centred (a tooth is 30° of crank); then the
# cap against each skirt stop. The gear zone is a full disc, so the shifted steps need not be fine: 30°
STEP = int(os.environ.get("VERIFY_STEP", 5))
CAP_PLAY = B.TEST_SKIRT_CLR
MOTION = [(a, 0.0) for a in range(0, 360, STEP)] + \
         [(a, s * CAP_PLAY) for s in (1, -1) for a in range(0, 360, max(STEP, 30))]


def poses(t):
    deg, dx = t
    a = np.radians(deg)
    out = {f"crankshaft{i + 1}": shaft_pose(i, a) for i in range(4)}
    cap = np.eye(4)
    cap[0, 3] = dx
    out["cap"] = cap
    for k, (y, z, n) in enumerate(IDL):
        out[f"idler{k + 1}"] = rx(PHASE[k] + a * C.SHAFT_TEETH / n, y, z) @ idler_base(k)
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
    ("cap", "spine"): "cap sits on the spine's top, tongues slide in the slots (0.15 mm a side, CAP_CLR), skirts "
                      "0.2 mm off the walls' outer faces (they touch at the X extremes)",
}
# gear zone: tip disc, faces at ±(GEAR_T/2 + float + 0.8), in the crankshaft's own frame (axis X, gear at x = 0)
ZONE_HALF = C.GEAR_T / 2 + C.SHAFT_FLOAT + C.GEAR_AXIAL_CLR
ZONE_R = C.MOD * (C.SHAFT_TEETH / 2 + 1)
KEEP_OUT = {f"gear{i + 1}-axial": {
    "part": f"crankshaft{i + 1}", "mesh": rod(2 * ZONE_R, 2 * ZONE_HALF, [-ZONE_HALF, 0, 0], [1, 0, 0], n=96),
    "why": f"gear faces + {C.SHAFT_FLOAT:.2f} float + {C.GEAR_AXIAL_CLR} mm axial",
    "except": ["spine"] + [f"idler{k + 1}" for k in range(3)],
    "except_why": "idlers mesh in the gear plane (GEARS checks them); the spine walls are 0.25 mm off the gear faces "
                  "(0-0.5 with the float) as in v2, which turned freely without the cap, 2026-11-12"}
    for i in range(4)}
# crankshafts: journal lift and axial float within 0.5 mm. Cap: located in X and Y by the spine alone (skirts and
# tongues), without its screws and without the crankshafts; it is free to lift (+Z) until the screws go in
RETAIN = {**{f"crankshaft{i + 1}": {"spin": [1, 0, 0], "play": 0.5} for i in range(4)},
          **{f"idler{k + 1}": {"spin": [1, 0, 0], "play": 1.0} for k in range(3)},
          "cap": {"slide": [0, 0, 1], "play": 0.5,
                  "not_by": [f"crankshaft{i + 1}" for i in range(4)] + ["capscrew1", "capscrew2"]}}
# direction = where each part comes in from: idlers dropped between the walls, axles pushed through from +X with the
# nut from -X, crankshafts dropped into their slots front to rear, then the cap and its screws from above
ASSEMBLY = [("spine", None)] + [(f"idler{k + 1}", [0, 0, 1]) for k in range(3)] + \
           [(f"axle{k + 1}", [1, 0, 0]) for k in range(3)] + [(f"axlenut{k + 1}", [-1, 0, 0]) for k in range(3)] + \
           [(f"crankshaft{i + 1}", [0, 0, 1]) for i in range(4)] + [("cap", [0, 0, 1])] + \
           [(f"capscrew{j + 1}", [0, 0, 1]) for j in range(2)]
PRINT_ORIENT = {"cap": trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])}    # upside down, plate on the bed
SECTIONS = [([K.CX, 0, 0], [1, 0, 0]),                                     # gear plane: all 7 gears, end blocks
            ([K.CX + (C.WALL_IN + C.WALL_OUT) / 2, 0, 0], [1, 0, 0])]      # +X wall: journals, tongues, axles
SECTIONS += [([K.CX, y, z], [0, 1, 0]) for y, z in SH]                     # each journal, tongue and cap
SECTIONS += [([K.CX, y, z], [0, 1, 0]) for y, z, _ in IDL]                 # each idler on its axle
SECTIONS += [([K.CX, y, 0], [0, 1, 0]) for y, _ in B.cap_screws()]         # cap screws and their nut pockets

FLIP = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
PRINT_ORIENT = {"spine": np.eye(4),                       # on its foot, as modelled
                "cap": FLIP,                              # upside down, plate on the bed
                **{f"crankshaft{i + 1}": np.eye(4) for i in range(4)},   # as in ../crankshafts/verify.py
                **{f"idler{k + 1}": np.eye(4) for k in range(3)}}

# the gear pairs repeat every tooth: checked finer over one tooth pitch only
GEAR_MOTION = [(a, 0.0) for a in range(0, 31)]

_Y0, _Y1, _, _ZT = B.spine_box()
_SY = [y for y, _ in SH]
JOINTS = {
    **{(f"crankshaft{i + 1}", "spine"): {
        "fit": fits.TURN, "where": ([K.CX + (C.WALL_IN + C.WALL_OUT) / 2, y, z], [C.WALL_OUT - C.WALL_IN, 6, 6]),
        "why": f"journal {i + 1} in its hole (+X wall)"} for i, (y, z) in enumerate(SH)},
    **{("spine", f"crankshaft{i + 1}"): {
        "fit": fits.GEAR_THRUST_CRANK, "where": ([K.CX, y, z], [2 * C.WALL_OUT + 0.6, 16, 16]),
        "why": f"crank gear {i + 1} faces and webs to the walls"} for i, (y, z) in enumerate(SH)},
    **{("spine", f"idler{k + 1}"): {"fit": fits.GEAR_THRUST_IDLER, "why": f"idler {k + 1} between the walls"}
       for k in range(3)},
    **{(f"idler{k + 1}", f"axle{k + 1}"): {"fit": fits.STEEL, "why": f"idler {k + 1} on its M3 axle"}
       for k in range(3)},
    **{(f"axle{k + 1}", "spine"): {"fit": fits.STEEL, "where": ([K.CX + (C.WALL_IN + C.WALL_OUT) / 2, y, z], [2.5, 5, 5]),
                                   "why": f"axle {k + 1} in the +X wall"} for k, (y, z, _) in enumerate(IDL)},
    ("spine", "cap"): {"fit": fits.TONGUE_SHORT,
                       "where": ([K.CX, (_SY[0] + _SY[-1]) / 2, B.TEST_TOP - 3.0], [9.0, _SY[-1] - _SY[0] + 6.0, 4.0]),
                       "why": "tongues in the journal slots, a side (measured on this very cap, 0.15)"},
    # not joints here: the cap's skirts (LOCATOR, TEST_SKIRT_CLR 0.2 a side) and its screw holes (STEEL 0.15) touch
    # by design when the cap is pushed to an X extreme (ALLOWED_CONTACT); the motion sweep proves they do not
    # overlap, and the two asserts below keep the typed numbers at the measured fits
}
assert B.TEST_SKIRT_CLR >= fits.LOCATOR.side - 1e-9, "skirts tighter than the measured LOCATOR"
assert (B.SCREW + B.CLR_STEEL - B.SCREW) / 2 >= fits.STEEL.side - 1e-9, "cap screw holes tighter than STEEL"
MARKS = {**{f"crankshaft{i + 1}": f"{i + 1} dots on the +X web, matching the {i + 1} dots beside its slot on the "
                                  f"spine (and the crank angle)" for i in range(4)},
         **{f"idler{k + 1}": "none needed: identical teeth, it meshes in any position; the cranks' phase is set by "
                             "the crankshafts' dots" for k in range(3)},
         "spine": "1-4 dots beside each journal slot, as the crankshafts' dots",
         "cap": "a dot on its +X edge over every slot (it fits one way only)"}
LABELS = {"es": {"spine": "columna de prueba", "cap": "tapa de prueba",
                 **{f"crankshaft{i + 1}": f"cigüeñal {i + 1}" for i in range(4)},
                 **{f"idler{k + 1}": f"rueda intermedia {k + 1}" for k in range(3)},
                 **{f"axle{k + 1}": f"tornillo eje {k + 1}" for k in range(3)},
                 **{f"axlenut{k + 1}": f"tuerca del eje {k + 1}" for k in range(3)},
                 **{f"capscrew{j + 1}": f"tornillo de la tapa {j + 1}" for j in range(2)}}}
_TW = B.JOURNAL + B.CLR - C.CAP_CLR
_TX = K.CX + (C.TONGUE_IN + C.TONGUE_OUT) / 2
_SK = C.WALL_OUT + B.TEST_SKIRT_CLR
MEASURE = [
    {"part": "cap", "what": "tongue width across Y (the slot is 4.5)", "nominal": round(_TW, 2), "tol": 0.1,
     "points": "each tongue, mid-height", "when": "kit step: before fitting the cap",
     "point": [_TX, SH[0][0], B.TEST_TOP - 2.0], "normal": [1, 0, 0],
     "from": [_TX, SH[0][0] - _TW / 2, B.TEST_TOP - 2.0], "to": [_TX, SH[0][0] + _TW / 2, B.TEST_TOP - 2.0]},
    {"part": "cap", "what": "skirt-to-skirt inside width across X", "nominal": round(2 * _SK, 2), "tol": 0.15,
     "points": "between the skirts' inner faces", "when": "kit step: before fitting the cap",
     "point": [K.CX, _Y0 + 3.0, B.TEST_TOP - 1.0], "normal": [0, 1, 0],
     "from": [K.CX - _SK, _Y0 + 3.0, B.TEST_TOP - 1.0], "to": [K.CX + _SK, _Y0 + 3.0, B.TEST_TOP - 1.0]},
    {"part": "crankshaft1", "what": "journal diameter", "nominal": C.JOURNAL, "tol": 0.15,
     "points": "either journal, two directions", "when": "kit step: before assembly",
     "point": [K.CX + 3.0, *SH[0]], "normal": [1, 0, 0],
     "from": [K.CX + 3.0, SH[0][0], SH[0][1] - C.JOURNAL / 2], "to": [K.CX + 3.0, SH[0][0], SH[0][1] + C.JOURNAL / 2]},
]
ACCESS = [{"at": f"axle{k + 1}", "tool": tool("hex-key", [X_OUT + K.HEAD_H, y, z], [1, 0, 0]),
           "why": "M3×12 from +X through the wall, the idler and the other wall, 2.5 hex key"}
          for k, (y, z, _) in enumerate(IDL)] + \
         [{"at": f"axlenut{k + 1}", "tool": tool("finger", [X_OUT - 12 - 0.5, y, z], [-1, 0, 0]),
           "why": "nut started by a fingertip past the screw tip (12 long, 1.1 past the nut); the screw then turns it in"}
          for k, (y, z, _) in enumerate(IDL)] + \
         [{"at": f"capscrew{j + 1}", "tool": tool("hex-key", [K.CX, y, CAP_TOP + K.HEAD_H], [0, 0, 1]),
           "why": "M3×12 from above, 2.5 hex key"} for j, (y, _) in enumerate(B.cap_screws())]
