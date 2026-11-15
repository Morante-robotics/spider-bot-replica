"""cad_verify spec for the chassis, Part A: the drive module with everything it carries (crankshafts, idlers, pins
and keeper, cap, N20 with its pinion and clamp), the 8 legs swept round it, and the bought parts of the master model
(../robot.py) at their places. It is the start of the whole-robot spec: Part B adds the looks chassis, body, front
block, cradle and ballast frame, and the chassis becomes the fixed part.

Fixed here: the drive module (ground of Part A: the chassis it screws to is Part B). The legs are reference bodies:
placed by ../legs poses() at every step to sweep their paths past the module, cap, clamp and motor (LEG_PATH), but
held by the chassis's forks, which do not exist yet: their retention and joints are Part B's. The holder and eyes
board are reference bodies at their master-model places (fitted in Part B).

Motion step t = (crank angle in degrees, cap X shift, motor lift): 10° steps with everything at nominal. Loose parts
at their worst positions: the gears are checked over one tooth (GEAR_MOTION) also with the motor lifted by its seat
clearance under the clamp (MOTOR_SEAT: the pinion's centre distance at its largest); the cap's X play (its skirts,
LOCATOR either way) is in its keep-out zone round the pinion and in the tongues' placing (crankshafts TONGUE_IN, for
a 0.3 play). VERIFY_STEP=30 gives coarse steps for quick runs.
Every gear is at its real angle: crankshaft i at -θ (its gear at gear_offsets()[i]), idler k at idler_phase(k) +
θ·12/n, the pinion at its meshing phase - θ.

    ../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402
from cad_verify import rod, tool  # noqa: E402

B = design("chassis")              # this folder's build.py
C = design("crankshafts")
L = design("legs")

CX, YM, ZM = B.CX, B.YM, B.ZM
SH, IDL = B.SH, B.IDL
OFF = C.gear_offsets()
PHASE = [C.idler_phase(k) for k in range(3)]
YZ = np.eye(4)
YZ[:3, :3] = np.column_stack([[0, 1, 0], [0, 0, 1], [1, 0, 0]])   # build123d Plane.YZ: local x→Y, y→Z, z→X


def rx(a, y, z):
    """Rotation by a (rad) about the X axis through (y, z)."""
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[1:3, 1:3] = [[c, -s], [s, c]]
    M[1:3, 3] = [y - c * y + s * z, z - s * y - c * z]
    return M


def move(v):
    M = np.eye(4)
    M[:3, 3] = v
    return M


def union(*ms):
    return trimesh.boolean.union(list(ms), engine="manifold")


def m3(p_head, axis, length):
    """M3 socket head screw: shank of `length` from p_head along axis, head on the other side."""
    axis = np.asarray(axis, float)
    return union(rod(3.0, length, p_head, axis), rod(K.HEAD_D, K.HEAD_H, p_head, -axis))


def nut(p, axis):
    """M3 nut, 5.5 across flats, from p along axis."""
    return rod(K.NUT_AF / np.cos(np.pi / 6), K.NUT_T, p, axis, n=6)


# ---- the pinion's meshing phase on idler 3 (as crankshafts gear_offsets(): u_idler + u_pinion = 1/2) --------------
_N3 = IDL[2][2]
_U3 = (_N3 * (np.pi / 2 - PHASE[2]) / (2 * np.pi)) % 1.0       # idler 3 towards the pinion: straight up
PINION_PHASE = -np.pi / 2 - 2 * np.pi / R.PINION_TEETH * (0.5 - _U3)


def gear_base(face, y, z):
    return move([CX - face / 2, y, z]) @ YZ


# ---- parts -------------------------------------------------------------------------------------------------------
TOPC = B.TOP + B.CAP_T                       # cap top
TOPK = B.CLAMP_Z0 + B.CLAMP_T                # clamp top
KX0 = B.PIN_X1 + B.KEEPER_T - B.KEEPER_SCREW_L + 0.5
PARTS = {"drive-module": {"stl": "out/drive-module.stl", "fixed": True},
         "cap": {"stl": "out/cap.stl"},
         "motor-clamp": {"stl": "out/motor-clamp.stl"},
         "pinion": {"stl": "out/pinion.stl"},
         "idler-3-v2": {"stl": "out/idler-3-v2.stl"},
         "pin-keeper": {"stl": "out/pin-keeper.stl"},
         # bench tools (not in the robot): placed at the press position on the motor, in the bench steps only
         "gauge-fork": {"stl": "out/gauge-fork.stl", "bench": True},
         "press-jig": {"stl": "out/press-jig.stl", "bench": True},
         "press-cup": {"stl": "out/press-cup.stl", "bench": True},
         "n20": {"mesh": R.n20_body(), "hardware": True, "label": "motor N20 HP 380:1 (catálogo)"},
         "n20-shaft": {"mesh": R.n20_shaft(), "hardware": True, "fixed": True,
                       "label": "eje en D del N20 (parte del motor)"},
         "keeper-screw": {"mesh": m3([CX + B.PIN_X1 + B.KEEPER_T, *B.KEEPER_SCREW], [-1, 0, 0], B.KEEPER_SCREW_L),
                          "hardware": True, "fixed": True, "label": "M3×8 Allen"},
         "keeper-nut": {"mesh": nut([CX + KX0, *B.KEEPER_SCREW], [1, 0, 0]), "hardware": True, "fixed": True,
                        "label": "tuerca M3"},
         "cap-screw": {"mesh": m3([CX + B.SCREW_FRONT[0], B.SCREW_FRONT[1], TOPC], [0, 0, -1], B.CAP_SCREW_L),
                       "hardware": True, "fixed": True, "label": "M3×12 Allen"},
         "cap-nut": {"mesh": nut([CX + B.SCREW_FRONT[0], B.SCREW_FRONT[1], TOPC - B.CAP_SCREW_L + 0.5], [0, 0, 1]),
                     "hardware": True, "fixed": True, "label": "tuerca M3"},
         "shared-screw": {"mesh": m3([CX + B.SCREW_SHARED[0], YM, TOPK], [0, 0, -1], B.CAP_SCREW_L),
                          "hardware": True, "fixed": True, "label": "M3×12 Allen"},
         "shared-nut": {"mesh": nut([CX + B.SCREW_SHARED[0], YM, TOPK - B.CAP_SCREW_L + 0.5], [0, 0, 1]),
                        "hardware": True, "fixed": True, "label": "tuerca M3"},
         "clamp-screw": {"mesh": m3([CX + B.SCREW_CLAMP_X, YM, TOPK], [0, 0, -1], B.CAP_SCREW_L),
                         "hardware": True, "fixed": True, "label": "M3×12 Allen"},
         "clamp-nut": {"mesh": nut([CX + B.SCREW_CLAMP_X, YM, TOPK - B.CAP_SCREW_L + 0.5], [0, 0, 1]),
                       "hardware": True, "fixed": True, "label": "tuerca M3"},
         "holder": {"mesh": R.holder(), "hardware": True, "fixed": True,
                    "label": "portapilas 4×AAA (catálogo, en el cuerpo)"},
         "eyes-board": {"mesh": R.eyes_board(), "hardware": True, "fixed": True,
                        "label": "placa de los ojos (catálogo, en la cabeza)"}}
for i in range(4):
    PARTS[f"crankshaft-{i + 1}"] = {"stl": f"../crankshafts/out/crankshaft-{i + 1}.stl"}
for k in range(2):
    PARTS[f"idler-{k + 1}"] = {"stl": f"../crankshafts/out/idler-{k + 1}.stl"}
for k, (y, z, n) in enumerate(IDL):
    PARTS[f"pin-{k + 1}"] = {"mesh": rod(K.PIN, B.PIN_L, [CX + B.PIN_X0, y, z], [1, 0, 0]), "hardware": True,
                             "fixed": True, "label": "pasador de acero Ø3×10"}
LEGS = {}
for n, f, _ in L.poses(0.0):
    if n.startswith("leg"):
        name = f"leg-{int(n[3]) + 1}{n[4]}"            # 1-based, as the plan: leg-3R passes the motor
        LEGS[name] = n
        PARTS[name] = {"stl": L.stl(f), "fixed": True}

# ---- motion --------------------------------------------------------------------------------------------------------
STEP = int(os.environ.get("VERIFY_STEP", 10))
CAP_PLAY = B.LOC                        # skirts 0.2 a side
LIFT = B.SEAT                           # motor lift under the clamp pads
MOTION = [(a, 0.0, 0.0) for a in range(0, 360, STEP)]
# the gears also with the motor lifted against the clamp (MOTOR_SEAT): the pinion's centre distance at its largest
GEAR_MOTION = [(a, 0.0, 0.0) for a in range(0, 31)] + [(a, 0.0, LIFT) for a in range(0, 31, 3)]


def poses(t):
    deg, dx, dz = t
    a = np.radians(deg)
    out = {f"crankshaft-{i + 1}": move([CX, *SH[i]]) @ rx(-a, 0, 0) for i in range(4)}
    for k in range(2):
        y, z, n = IDL[k]
        out[f"idler-{k + 1}"] = rx(PHASE[k] + a * C.SHAFT_TEETH / n, y, z) @ gear_base(C.GEAR_T - 0.4, y, z)
    y, z, n = IDL[2]
    out["idler-3-v2"] = rx(PHASE[2] + a * C.SHAFT_TEETH / n, y, z) @ gear_base(R.IDLER3_FACE, y, z)
    up = move([0, 0, dz])
    ap = PINION_PHASE - a
    out["pinion"] = up @ rx(ap, YM, ZM) @ gear_base(R.PINION_FACE, YM, ZM)
    out["n20-shaft"] = up @ rx(ap, YM, ZM)
    out["n20"] = up
    out["cap"] = move([dx, 0, 0])
    lp = {n: M for n, _, M in L.poses(a)}
    for name, n in LEGS.items():
        out[name] = lp[n]
    return out


GEARS = [(f"crankshaft-{k + 1}", f"idler-{k + 1}") for k in range(2)] + \
        [(f"crankshaft-{k + 2}", f"idler-{k + 1}") for k in range(2)] + \
        [("crankshaft-3", "idler-3-v2"), ("crankshaft-4", "idler-3-v2"), ("pinion", "idler-3-v2")]
GEAR_GAP = (0.08, 0.5)       # backlash 0.2 at the pitch circle ≈ 0.1 a side along the tooth normal

HW_SCREWS = ["keeper-screw", "cap-screw", "shared-screw", "clamp-screw"]
NUTS = {"keeper-screw": "keeper-nut", "cap-screw": "cap-nut", "shared-screw": "shared-nut",
        "clamp-screw": "clamp-nut"}
PAIR_GAP = {**{(f"pin-{k + 1}", "drive-module"): 0.1 for k in range(3)},      # Ø3 in Ø3.3 (STEEL 0.15)
            **{(f"pin-{k + 1}", i): 0.1 for k, i in enumerate(["idler-1", "idler-2", "idler-3-v2"])},
            **{(s, "drive-module"): 0.1 for s in HW_SCREWS},                  # M3 in Ø3.3
            **{(nn, "drive-module"): 0.1 for nn in NUTS.values()},            # nut in its pocket (+0.15 a side)
            ("cap-screw", "cap"): 0.1, ("shared-screw", "cap"): 0.1, ("shared-screw", "motor-clamp"): 0.1,
            ("clamp-screw", "motor-clamp"): 0.1, ("keeper-screw", "pin-keeper"): 0.1,
            }
for leg in LEGS:                                                              # moving legs: LEG_PATH 0.8
    for other in ["drive-module", "cap", "motor-clamp", "n20", "pin-keeper"] + HW_SCREWS + list(NUTS.values()):
        PAIR_GAP[(leg, other)] = fits.LEG_PATH.side
ALLOWED_CONTACT = {
    ("cap", "drive-module"): "cap plate sits on the walls' tops; tongues 0.3 a side in the slots (TONGUE), skirts "
                             "0.2 off the walls (LOCATOR, touching at the cap's X extremes)",
    ("pin-keeper", "drive-module"): "keeper flat on its recess floor, edges 0.2 (LOCATOR)",
    ("motor-clamp", "cap"): "clamp's -X foot on the cap's -X bridge (the shared screw clamps both)",
    ("motor-clamp", "drive-module"): "clamp's rear foot on the end wall",
    ("n20", "drive-module"): "gearbox on the pad, can on the V saddle's flanks; Y steps 0.5 (WINDOW: out of the "
                             "torque path, the clamp's cheeks take it)",
    ("motor-clamp", "n20"): "gearbox pad 0.3 into the gearbox (fits.MOTOR_PRELOAD, the bar is the spring ≈ 9 N); "
                            "cheeks 0.2 off the gearbox flats (MOTOR_SEAT), can pad 0.2 clear",
    ("n20", "n20-shaft"): "the shaft comes out of the gearbox (one bought part)",
    ("pinion", "n20-shaft"): "D-bore pressed on the D-shaft (DSHAFT)",
    **{(f"pin-{k + 1}", "drive-module"): "pin bottomed in its blind hole at -X" for k in range(3)},
    **{(f"pin-{k + 1}", "pin-keeper"): "keeper on the pin's +X end" for k in range(3)},
    **{(s, n): "screw in its nut" for s, n in NUTS.items()},
    ("keeper-screw", "pin-keeper"): "head clamps the keeper", ("cap-screw", "cap"): "head clamps the cap",
    ("shared-screw", "motor-clamp"): "head clamps the clamp and the cap",
    ("clamp-screw", "motor-clamp"): "head clamps the clamp",
    ("keeper-nut", "drive-module"): "nut pulled against its pocket's +X face",
    ("cap-nut", "drive-module"): "nut pulled up against its pocket",
    ("shared-nut", "drive-module"): "nut pulled up against its pocket",
    ("clamp-nut", "drive-module"): "nut pulled up against its pocket",
}
# crank gear zones (gear train test v2.1): faces + float + 0.8; pinion zone: tip circle + 0.8, faces + 0.8
ZONE_HALF = C.GEAR_T / 2 + C.SHAFT_FLOAT + fits.GEAR_AXIAL.side
ZONE_R = C.MOD * (C.SHAFT_TEETH / 2 + 1)
KEEP_OUT = {f"gear{i + 1}-axial": {
    "part": f"crankshaft-{i + 1}", "mesh": rod(2 * ZONE_R, 2 * ZONE_HALF, [-ZONE_HALF, 0, 0], [1, 0, 0], n=96),
    "why": f"crank gear faces + {C.SHAFT_FLOAT:.2f} float + {fits.GEAR_AXIAL.side} mm axial (fits.GEAR_AXIAL)",
    "except": ["drive-module", "idler-1", "idler-2", "idler-3-v2"],
    "except_why": "idlers mesh in the gear plane (GEARS checks them); the spine walls are 0.25 mm off the gear faces "
                  "(GEAR_THRUST_CRANK, measured on gear train test v2)"} for i in range(4)}
# the cap is free in X by CAP_PLAY: its own zone, wider by that much (the cap at either skirt stop)
KEEP_OUT["pinion-cap"] = {
    "part": "pinion", "mesh": rod(2 * B.PIN_R, R.PINION_FACE + 2 * (B.GAX + CAP_PLAY), [0, 0, -B.GAX - CAP_PLAY],
                                  [0, 0, 1], n=96),
    "why": f"pinion faces + {B.GAX} axial + the cap's X play {CAP_PLAY} (cap only)",
    "except": [p for p in PARTS if p not in ("cap", "pinion")],
    "except_why": "this zone is for the cap at either skirt stop; every other part is in pinion-clear"}
KEEP_OUT["pinion-clear"] = {
    "part": "pinion", "mesh": rod(2 * B.PIN_R, R.PINION_FACE + 2 * B.GAX, [0, 0, -B.GAX], [0, 0, 1], n=96),
    "why": f"pinion tip circle + {B.GAX} radial, faces + {B.GAX} axial (cap, clamp, walls, pad)",
    "except": ["idler-3-v2", "n20-shaft", "n20"],
    "except_why": "idler 3 v2 meshes (GEARS); the shaft is the pinion's own; the gearbox face is the 0.8 gauge "
                  "(the zone's +X face)"}
RETAIN = {**{f"crankshaft-{i + 1}": {"spin": [1, 0, 0], "play": 0.5, "not_by": list(LEGS)} for i in range(4)},
          **{f"idler-{k + 1}": {"spin": [1, 0, 0], "play": 1.0} for k in range(2)},
          "idler-3-v2": {"spin": [1, 0, 0], "play": 1.0},
          "pinion": {"play": 1.0},
          "n20": {"play": 1.0},
          "cap": {"play": 0.5, "not_by": [f"crankshaft-{i + 1}" for i in range(4)]},
          "motor-clamp": {"play": 0.5},
          "pin-keeper": {"play": 0.5}}
ASSEMBLY = [("drive-module", None),
            ("keeper-nut", [0, 0, -1]), ("cap-nut", [-1, 0, 0]), ("shared-nut", [-1, 0, 0]),
            ("clamp-nut", [1, 0, 0]),
            ("idler-1", [0, 0, 1]), ("idler-2", [0, 0, 1]), ("idler-3-v2", [0, 0, 1]),
            ("pin-1", [1, 0, 0]), ("pin-2", [1, 0, 0]), ("pin-3", [1, 0, 0]),
            ("pin-keeper", [1, 0, 0]), ("keeper-screw", [1, 0, 0])] + \
           [(f"crankshaft-{i + 1}", [0, 0, 1]) for i in range(4)] + \
           [("cap", [0, 0, 1]), ("cap-screw", [0, 0, 1]),
            # on the bench, the jig stood on the table (-X face down, open side +Z): pinion into its pocket, the
            # fork into its slot over the pinion, then the motor pushed down (-X) into the socket onto both
            ("pinion", [0, 0, 1], {"bench": ["press-jig"],
                                   "note": "pinion slid into the jig's pocket from the open side, dot up (+X)"}),
            ("gauge-fork", [0, 0, 1], {"bench": ["press-jig", "pinion"],
                                       "note": "fork down into the jig's slot, flat on the pinion"}),
            (("n20", "n20-shaft"), [1, 0, 0],
             {"bench": ["press-jig", "pinion", "gauge-fork"],
              "except": {"n20-shaft": "D-bore pressed on the D-shaft (DSHAFT, modelled at zero clearance)"},
              "note": "shaft's flat over the pinion's dot; motor pushed down by its can into the socket until the "
                      "gearbox face stops on the fork"}),
            ("press-cup", [1, 0, 0],
             {"bench": ["press-jig", "pinion", "gauge-fork", "n20", "n20-shaft"],
              "note": "only if the thumb is not enough: cup over the can's rear, jig and cup between the vise's "
                      "jaws, closed until the gearbox face stops on the fork; then the fork lifts out (+Z) and the "
                      "motor with its pinion slides out of the jig (+Z)"}),
            # one drop: the motor with its pinion (idler 3 is the pinion's GEARS partner: crank 1 turns it)
            (("n20", "n20-shaft", "pinion"), [0, 0, 1]),
            ("motor-clamp", [0, 0, 1]), ("shared-screw", [0, 0, 1]), ("clamp-screw", [0, 0, 1])] + \
           [(leg, None) for leg in LEGS] + [("holder", None), ("eyes-board", None)]
_mouth = TOPC - B.CAP_SCREW_L + 0.5 + K.NUT_T / 2
_mouth2 = TOPK - B.CAP_SCREW_L + 0.5 + K.NUT_T / 2
ACCESS = [
    {"at": "keeper-nut", "tool": tool("pliers", [CX + KX0 + K.NUT_T / 2, B.KEEPER_SCREW[0], B.KEEL_Z],
                                      [0, 0, -1]), "why": "nut pushed up its slot from below, pliers"},
    {"at": "cap-nut", "tool": tool("pliers", [CX - B.W_OUT, B.SCREW_FRONT[1], _mouth], [-1, 0, 0]),
     "why": "nut slid in from -X, pliers"},
    {"at": "shared-nut", "tool": tool("pliers", [CX + B.BOSS_X[0], YM, _mouth2], [-1, 0, 0]),
     "why": "nut slid in from -X, pliers"},
    {"at": "clamp-nut", "tool": tool("pliers", [CX + B.END_X1, YM, _mouth2], [1, 0, 0]),
     "why": "nut slid in from +X, pliers"},
    *[{"at": f"pin-{k + 1}", "tool": tool("hex-key", [CX + B.PIN_X1, y, z], [1, 0, 0]),
       "why": "pin started by finger, pushed flush with the recess floor by the hex key's short arm"}
      for k, (y, z, _) in enumerate(IDL)],
    {"at": "keeper-screw", "tool": tool("hex-key", [CX + B.PIN_X1 + B.KEEPER_T + K.HEAD_H, *B.KEEPER_SCREW],
                                        [1, 0, 0]), "why": "M3×8 from +X, 2.5 hex key"},
    {"at": "cap-screw", "tool": tool("hex-key", [CX + B.SCREW_FRONT[0], B.SCREW_FRONT[1], TOPC + K.HEAD_H],
                                     [0, 0, 1]), "why": "M3×12 from above, 2.5 hex key"},
    {"at": ("n20", "n20-shaft", "pinion"), "tool": tool("finger", [CX + 20.0, YM, R.MOTOR_ENVELOPE[1][2]],
                                                         [0, 0, 1]),
     "why": "motor with its pinion lowered onto the pad and V saddle by hand"},
    # thumb tip on the can's rear rim under the terminal block (the block spans z -2..+4 from the axis, Y ±3)
    {"at": ("n20", "n20-shaft"), "tool": tool("finger", [CX + B.CAN_X1, YM, ZM + R.N20_TERM_Z[0] - 2.6],
                                                 [1, 0, 0], d=5.0, reach=20.0),
     "why": "on the bench: thumb tip on the can's rear rim below the terminals, jig on the table"},
    {"at": "press-cup", "tool": tool("finger", [CX + B.TERM_X1 + B.WIN + B.CUP_T, YM, ZM], [1, 0, 0]),
     "why": "on the bench: cup put on by hand, then the vise jaw on its top plate"},
    {"at": "shared-screw", "tool": tool("hex-key", [CX + B.SCREW_SHARED[0], YM, TOPK + K.HEAD_H], [0, 0, 1]),
     "why": "M3×12 through clamp and cap, from above"},
    {"at": "clamp-screw", "tool": tool("hex-key", [CX + B.SCREW_CLAMP_X, YM, TOPK + K.HEAD_H], [0, 0, 1]),
     "why": "M3×12 from above"},
]
FLIP = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
PRINT_ORIENT = {"drive-module": FLIP,                 # top (deck level) on the bed
                "cap": FLIP,                          # upside down, plate on the bed (test cap v2.1)
                "motor-clamp": FLIP,                  # top on the bed, pads up
                "pin-keeper": trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),   # flat
                "gauge-fork": trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),   # flat: 4 layers
                "press-jig": np.eye(4),                # on its -Z face, the open side up: no overhang
                "press-cup": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])}     # top plate down
SECTIONS = [([CX, 0, 0], [1, 0, 0]),                                  # gear plane: all gears, pinion, end blocks
            ([CX + B.PIN_X1 - 1.0, 0, 0], [1, 0, 0]),                 # +X wall: journals, pins, keeper, pad
            ([CX - 4.8, 0, 0], [1, 0, 0]),                            # -X wall: blind pin ends, shaft U-slot
            ([CX, YM, ZM], [0, 1, 0]),                                # motor axis: pinion, pad, V saddle, clamp
            ([CX, 0, ZM], [0, 0, 1])]                                 # deck level from above
SECTIONS += [([CX, y, z], [0, 1, 0]) for y, z in SH]                  # each journal, tongue and cap
SECTIONS += [([CX, y, z], [0, 1, 0]) for y, z, _ in IDL[:2]]          # idlers 1-2 on their pins
SECTIONS += [([CX, B.SCREW_FRONT[1], 0], [0, 1, 0]), ([CX, B.KEEPER_SCREW[0], 0], [0, 1, 0]),
             ([CX + B.SCREW_CLAMP_X, 0, 0], [1, 0, 0]), ([CX + B.SCREW_SHARED[0], 0, 0], [1, 0, 0])]


def _box(c, s):
    return (c, s)


# joint regions (ground frame): exclude the faces that rest on each other, keep the fit's faces
JOINTS = {
    **{(f"crankshaft-{i + 1}", "drive-module"): {
        "fit": fits.TURN, "where": _box([CX + 3.0, y, z], [2.5, 6, 6]),
        "why": f"journal {i + 1} in its Ø{B.J_HOLE:.1f} hole (+X wall)"} for i, (y, z) in enumerate(SH)},
    **{("drive-module", f"crankshaft-{i + 1}"): {
        "fit": fits.GEAR_THRUST_CRANK, "where": _box([CX, y, z], [2 * B.W_OUT + 0.6, 16, 16]),
        "why": f"crank gear {i + 1} faces and webs to the walls"} for i, (y, z) in enumerate(SH)},
    ("drive-module", "cap"): {"fit": fits.TONGUE, "where": _box([CX, 2.0, 66.0], [9.0, 70.0, 12.0]),
                              "why": "tongues in the journal slots, a side"},
    ("cap", "drive-module"): {"fit": fits.LOCATOR, "where": _box([CX, B.CAP_Y0 + 3.0, B.TOP - 2.0],
                                                                  [14.0, 6.0, 3.8]), "why": "front skirts"},
    **{(f"idler-{k + 1}", f"pin-{k + 1}"): {"fit": fits.STEEL, "why": f"idler {k + 1} on its Ø3 pin"}
       for k in range(2)},
    ("idler-3-v2", "pin-3"): {"fit": fits.STEEL, "why": "idler 3 v2 on its Ø3 pin"},
    **{("drive-module", f"idler-{k + 1}"): {"fit": fits.GEAR_THRUST_IDLER, "why": f"idler {k + 1} between the walls"}
       for k in range(2)},
    ("drive-module", "idler-3-v2"): {"fit": fits.GEAR_THRUST_IDLER, "why": "idler 3 v2 in its 5.9 pocket"},
    **{(f"pin-{k + 1}", "drive-module"): {"fit": fits.STEEL, "where": _box([CX + 2.0, y, z], [3.0, 5, 5]),
                                          "why": f"pin {k + 1} in the +X wall"} for k, (y, z, _) in enumerate(IDL)},
    ("pin-keeper", "drive-module"): {"fit": fits.LOCATOR, "where": _box([CX + B.PIN_X1 + 1.1, 0, 49], [1.4, 60, 30]),
                                     "why": "keeper edges in its recess"},
    ("n20", "drive-module"): {"fit": fits.WINDOW, "where": _box([CX + 4.4, YM, 70.5], [2.0, 14, 7.6]),
                              "why": "gearbox between the +X wall's steps (Y), out of the torque path"},
    ("drive-module", "n20"): {"fit": fits.MOTOR_SEAT, "where": _box([CX + B.STOP_X - 0.1, YM, 67.5], [0.8, 4, 3.0]),
                              "why": "can's rear face to its stop (+X)"},
    ("motor-clamp", "n20"): {"fit": fits.MOTOR_SEAT, "where": _box([CX + (B.GB_X0 + B.GB_X1) / 2, YM, 76.0],
                                                                    [B.GB_X1 - B.GB_X0, 16.0, 3.0]),
                             "why": "clamp cheeks on the gearbox flats (Y, the motor torque)"},
    ("pinion", "n20-shaft"): {"fit": fits.DSHAFT, "why": "D-bore on the D-shaft"},
    ("n20", "motor-clamp"): {"fit": fits.MOTOR_PRELOAD,
                             "where": _box([CX + (B.GB_X0 + B.GAX + B.GB_X1) / 2, YM, B.MOTOR_TOP + 0.25],
                                           [B.GB_X1 - B.GB_X0 - B.GAX - 0.5, 6.0, 1.5]),
                             "why": "clamp's gearbox pad 0.3 into the gearbox top (the bar is the spring)"},
    ("idler-3-v2", "drive-module"): {"fit": fits.GEAR_TIP,
                                     "where": _box([CX, IDL[2][0], (B.KEEL_Z + IDL[2][1]) / 2],
                                                   [4.0, 26.0, IDL[2][1] - B.KEEL_Z]),
                                     "why": "idler 3 v2's tip circle to its pocket's flat floor and sides (radial)"},
    ("cap-screw", "cap"): {"fit": fits.STEEL, "where": _box([CX, B.SCREW_FRONT[1], B.TOP + 2.5], [5, 5, 4]),
                           "why": "cap screw in its hole"},
    ("shared-screw", "motor-clamp"): {"fit": fits.STEEL, "where": _box([CX - 10, YM, B.CLAMP_Z0 + 1.5], [5, 5, 2]),
                                      "why": "shared screw in the clamp"},
    ("clamp-screw", "drive-module"): {"fit": fits.STEEL, "where": _box([CX + B.SCREW_CLAMP_X, YM, 73.0],
                                                                       [5, 5, 1.5]), "why": "clamp screw"},
}
MARKS = {**{f"crankshaft-{i + 1}": f"{i + 1} dots on the +X web, matching the {i + 1} dots beside its slot on the "
                                   f"module's +X wall (and the crank angle: every crank level)" for i in range(4)},
         "idler-1": "none needed: 12 identical teeth, it meshes in any position; the cranks' phase is set by the "
                    "crankshafts' dots", "idler-2": "none needed: as idler 1",
         "idler-3-v2": "a dot on the +X face on tooth 0's line (idler 3's phase); any tooth meshes, the dot shows "
                       "the face that goes to +X",
         "pinion": "a dot on the +X face over the D-bore's flat: line it up with the shaft's flat before pressing",
         "drive-module": "FRONT arrow (pointing -Y) on the front block's +X face; 1-4 dice dots beside each slot",
         "cap": "a dot on its +X edge over every slot (it fits one way only)",
         "n20": "polarity: «+» (red wire, +Y side) and «-» sunk in the end wall's +X face; wires leave on +Y "
                "(leg 3R passes 2.9 mm from the motor's -Y side)"}
LABELS = {"es": {"drive-module": "módulo de transmisión", "cap": "tapa", "motor-clamp": "brida del motor",
                 "pinion": "piñón", "idler-3-v2": "rueda intermedia 3 (v2)", "pin-keeper": "retén de pasadores",
                 "n20": "motor N20", "n20-shaft": "eje del motor", "keeper-screw": "tornillo del retén",
                 "keeper-nut": "tuerca del retén", "cap-screw": "tornillo delantero de la tapa",
                 "cap-nut": "tuerca delantera de la tapa", "shared-screw": "tornillo de tapa y brida",
                 "shared-nut": "tuerca de tapa y brida", "clamp-screw": "tornillo trasero de la brida",
                 "clamp-nut": "tuerca trasera de la brida", "holder": "portapilas",
                 "gauge-fork": "galga de 0,8 mm (horquilla)", "press-jig": "útil para calar el piñón",
                 "press-cup": "copa para el tornillo de banco", "eyes-board": "placa de los ojos",
                 **{f"crankshaft-{i + 1}": f"cigüeñal {i + 1}" for i in range(4)},
                 **{f"idler-{k + 1}": f"rueda intermedia {k + 1}" for k in range(2)},
                 **{f"pin-{k + 1}": f"pasador {k + 1}" for k in range(3)},
                 **{leg: f"pata {leg[4:]}" for leg in LEGS}}}
MEASURE = [
    {"part": "drive-module", "what": "idler 3 pocket width (between the walls' inner faces)", "nominal": 5.9,
     "tol": (-0.05, 0.15), "points": "at idler 3's pin, across X"},
    {"part": "drive-module", "what": "crank gear room between the walls", "nominal": 2 * B.W_IN,
     "tol": (-0.05, 0.15), "points": "next to each journal slot"},
    {"part": "drive-module", "what": "journal slot width", "nominal": B.J_HOLE, "tol": (-0.05, 0.15),
     "points": "each slot, at the top"},
    {"part": "drive-module", "what": "gearbox seat width (between the +X wall's steps)", "nominal": R.N20_W + 2 * B.SEAT,
     "tol": (-0.05, 0.15), "points": "above the pad"},
    {"part": "drive-module", "what": "pad depth from the module top", "nominal": round(B.TOP - B.PAD_Z, 2),
     "tol": (-0.1, 0.1), "points": "depth gauge from the top face to the pad"},
    {"part": "cap", "what": "tongue width (along Y)", "nominal": B.TONGUE_W, "tol": (-0.1, 0.05),
     "points": "each tongue"},
    {"part": "pinion", "what": "D-bore across the flat", "nominal": R.N20_SHAFT_D - R.N20_SHAFT_FLAT,
     "tol": (-0.1, 0.05), "points": "flat to the round side"},
    {"part": "idler-3-v2", "what": "face width", "nominal": R.IDLER3_FACE, "tol": (-0.1, 0.05), "points": "rim"},
    {"part": "pin-keeper", "what": "thickness", "nominal": B.KEEPER_T, "tol": (-0.1, 0.1), "points": "strip"},
    {"part": "gauge-fork", "what": "thickness (the 0.8 gauge), measure before use", "nominal": B.GAX,
     "tol": (-0.05, 0.05), "points": "both prongs, beside the slot", "when": "kit step: before the press"},
    {"part": "pinion", "what": "pinion's gap to the gearbox face, on the bench right after the press (motor still in "
     "the jig, before the drop)", "nominal": B.GAX, "tol": (0.0, 0.1),
     "points": "feeler: the fork comes out (+Z) snug and slides back in snug", "when": "bench check, before the drop"},
]

# ---- keep-in: everything below the deck inside the carcass shell's inner surface (Part B's shell: carcass - WALL) ----
_X = (CX - B.W_THICK_MX - 0.6, CX + B.PIN_X1 + B.KEEPER_T + K.HEAD_H + 0.5)


HEAD_CUT = 80.0   # ray hits above this are the head (z 88-108 over y -46..-24), not the carcass top (≤ 74.4)


def _carcass_top_low(x0, x1, y0, y1, step=0.25):
    """Lowest carcass top under the module's top face (z ≥ TOP - 0.5) over the box: rays down on a 0.25 mm grid, the
    carcass top being the highest hit under HEAD_CUT at each point; where the flat module top stands out the most."""
    m, mod = R.carcass("base"), trimesh.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          "out", "drive-module.stl"))
    xs, ys = np.arange(x0, x1 + 1e-9, step), np.arange(y0, y1 + 1e-9, step)
    o = np.array([[x, y, 200.0] for x in xs for y in ys])
    d = np.tile([0.0, 0.0, -1.0], (len(o), 1))

    def top(mesh, cut=np.inf):
        loc, ri, _ = mesh.ray.intersects_location(o, d)
        k = loc[:, 2] < cut
        t = np.full(len(o), -np.inf)
        np.maximum.at(t, ri[k], loc[k, 2])
        return t

    on = top(mod) >= B.TOP - 0.5
    return float(top(m, HEAD_CUT)[on].min())


FRONT_LOW = _carcass_top_low(_X[0], _X[1], -47.0, -14.0)    # 70.42 under the module's top face (y ≈ -44), under the head
FRONT_OUT = round(B.TOP - FRONT_LOW, 2)                    # 4.38: the module top (74.8) over that point
I7_BODIES = {f"i7-nut-{i + 1}": nut([CX + x, y, z + 0.15], [0, 0, 1]) for i, (x, y, z, _) in enumerate(B.I7_NUTS)}
KEEP_IN = {"carcass-shell": {
    "mesh": R.carcass("base"), "inset": B.WALL, "z": (None, R.DECK_BOT - 0.5),
    # parts: cad_verify's default, every part that does not move over MOTION (module, cap, clamp, keeper, motor,
    # pins, every screw and nut, holder and eyes board): the moving ones (gears, legs) stay inside their pockets
    "bodies": I7_BODIES,
    "why": f"below the deck (z < {R.DECK_BOT - 0.5:.1f}: the deck (72.8-74.8) is Part B; the carcass top is 74.4 over the front block), "
           f"≥ {B.WALL} inside the carcass: the chassis shell's inner surface, Part B's bowl and I7 bosses under it",
    "allow": {
        "keel": {"box": ((_X[0], IDL[0][0] - 10.0, B.KEEL_Z - 1.0), (_X[1], IDL[2][0] + 14.0, 53.0)),
                 "min_z": 42.7,
                 "why": "the gear pockets' keel and the pin keeper under the shell (Morante 2026-11-14, option b: "
                        "flat-bottomed pockets, lowest z ≥ base v1's 42.7); Part B's bowl opens round it"},
        "rear-end": {"box": ((_X[0], 30.5, 50.0), (_X[1], B.Y1 + 0.1, R.DECK_BOT)), "inset": 0.0,
                     "why": "crank 4's gear room ends at y 33.78 (crank 4 at 26.28, fixed by the crank spacing), past "
                            "the shell's inner face (32.75 at CX): the module's rear end stays inside the carcass "
                            "(outer face 34.84 in the gear plane) and Part B's bowl opens its rear wall over it"},
        "front-slope": {"box": ((_X[0], -47.0, 66.0), (_X[1], -14.0, B.TOP)), "inset": -FRONT_OUT,
                        "max_z": B.TOP,
                        "why": "the carcass top dips under the head (z 74.4 at y -16 and at y -46, "
                               f"{FRONT_LOW:.2f} at its lowest under the module's top face; the head above it, z 88-108, "
                               "is not the carcass top); the deck (Part B, flat at 72.8-74.8) replaces it there, the module's top "
                               "band is the deck's height and passes through the deck window; checked up to the "
                               f"module top (z ≤ {B.TOP}; the cap above it is the deck window's); bound: at most {FRONT_OUT:.2f} mm out of the carcass (the "
                               "module top over the carcass top's lowest point there)"}}}}
# bench steps seen as Morante does them: the jig on the table (+X up on the page), its open side (+Z) towards him, a
# little from above; the drop step keeps the default view (its tuple named, or it would take the pinion's)
BENCH_VIEW = (115, 185)
STEP_VIEW = {"pinion": BENCH_VIEW, "gauge-fork": BENCH_VIEW, ("n20", "n20-shaft"): BENCH_VIEW,
             "press-cup": BENCH_VIEW, ("n20", "n20-shaft", "pinion"): (25, -60)}
STEP_NOTES = {   # what the step means, for the documenter (kit «pasos»; keys as workshop_kit: a part or «a + b»)
    "pinion": "on the bench: jig on the table, open side towards you; pinion slid into its pocket, dot up",
    "gauge-fork": "on the bench: measure the fork first (0.8 ± 0.05); slide it down into the jig's slot, flat on the "
                  "pinion",
    "n20 + n20-shaft": "on the bench: shaft's flat over the pinion's dot; push the motor down into the socket by its "
                       "can (thumb on the rim below the terminals) until the gearbox face stops on the fork; note "
                       "whether it went on by thumb or needed the vise",
    "press-cup": "only if the thumb is not enough: cup over the can's rear, jig and cup between the vise's jaws, "
                 "closed until the gearbox face stops on the fork. Then: the fork lifts out snug and slides back in "
                 "snug (the 0.8 gap); fork out, the motor with its pinion slides out of the jig towards you",
    "n20 + n20-shaft + pinion": "lower the motor with its pinion from above onto the pad and the V saddle; turn "
                                "crank 1 a little until the pinion drops into the teeth (380:1: the motor shaft "
                                "cannot be turned by hand)",
    "i7": "service: legs off, robot on its back, 4 screws from below (Part B)"}
