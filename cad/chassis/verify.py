"""cad_verify spec for the walking robot (Part C step 1: Part A, the shell and the front block, one spec).

What is in it: the drive module with everything it carries (crankshafts, idlers, pins and keeper, cap, N20 with its
pinion and clamp), the 8 legs swept round it, the shell `chassis` (ground part), the crank cover with its switch and
motor leads, the 8 forks with their swivel screws, the front block v2 with its screws, the bought parts of the master
model (../robot.py) at their places, and the I7, I4, cover and front-block hardware. It was three specs (Part A's,
verify_b1.py's and verify_fb.py's); their checks and exceptions are kept as they were.

Fixed: the shell `chassis`. The drive module stands on the shell's 4 bosses, its top in the deck window, held by 4 stock
M3 from below (I7); the 8 forks swivel on 2 M3×10 each (I4); the front block's pads stand in the shell's lips, held by
2 M3×10 (I8). The legs are placed by ../legs poses() at every step to sweep their paths past everything (LEG_PATH):
the lips' notches, the bump, the band, the rear screw column at CX-9, the front block nut bosses at y -51, the
rear-left deck bridge, the module, cap, clamp, motor and the cover. The holder and eyes board are reference bodies at
their master-model places (the body v2, cradle and frame are Part B rest).

The assembly follows the plan (design-plan-b.md «Assembly sequence»): the module is built on the bench (Part A's
steps, checked against the bench parts only), goes into the shell from above as one sub-assembly (no motor), then the
legs and forks, then the motor with its pinion, the clamp, the crank cover with its switch, the front block, and the
I7 screws from below with the robot on its back.

Motion step t = (crank angle in degrees, cap X shift, motor lift): 10° steps with everything at nominal. Loose parts
at their worst positions: the gears are checked over one tooth (GEAR_MOTION) also with the motor lifted by its seat
clearance under the clamp (MOTOR_SEAT: the pinion's centre distance at its largest); the cap's X play (its skirts,
LOCATOR either way) is in its keep-out zone round the pinion and in the tongues' placing (crankshafts TONGUE_IN, for
a 0.3 play). VERIFY_STEP=30 gives coarse steps for quick runs.
Every gear is at its real angle: crankshaft i at -θ (its gear at gear_offsets()[i]), idler k at idler_phase(k) +
θ·12/n, the pinion at its meshing phase - θ.

Front block (I8): the body's way in (lowered 4 mm behind its place, slid forward) is cut from the block in
front_block.py; the carcass body is not a part here (body v2 is B2, its L-slots take the tongues; its spec checks the
slide). Probe on the lifted carcass body, tongues excluded (2026-11-16): no overlap at its place, slid 2 and 4 mm, and
lowered at +4 Y from 5 and 15 mm up; smallest gap 0.39 mm. The shell must be cut round the block
(front_block.clear_outline()); FB_CHASSIS=<stl> runs this spec on a what-if shell cut so.

    ../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
    VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify.py --quick --only chassis
    SHELL_LITE=1 VERIFY_STEP=30 …                 # the same on shell.py --lite's out/chassis-lite.stl
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design, fits, robot as R  # noqa: E402
from cad_verify import rod, tool  # noqa: E402
import shell as SHL  # noqa: E402  (the shell, Part B1)
import front_block as FB  # noqa: E402  (front block v2, I8)

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


DROP = ("n20", "n20-shaft", "clutch-sleeve", "pinion", "wave-washer", "shim", "clutch-collar")   # the motor with its clutch


def own(x0):
    """A clutch part built in its own frame (axis Z, z 0 = its -X face) placed with that face at x0 (from CX)."""
    return move([CX + x0, YM, ZM]) @ YZ


def washer(d_in, d_out, x0, x1):
    """Steel washer (wave washer at its compressed height, shim) on the motor axis, x from CX."""
    m = trimesh.creation.annulus(d_in / 2, d_out / 2, x1 - x0, sections=64)
    m.apply_transform(move([CX + (x0 + x1) / 2, YM, ZM]) @ YZ)
    return m


# ---- parts -------------------------------------------------------------------------------------------------------
TOPC = B.TOP + B.CAP_T                       # cap top
TOPK = B.CLAMP_Z0 + B.CLAMP_T                # clamp top
KX0 = B.PIN_X1 + B.KEEPER_T - B.KEEPER_SCREW_L + 0.5
PARTS = {"drive-module": {"stl": "out/drive-module.stl", "fixed": True},
         "cap": {"stl": "out/cap.stl"},
         "motor-clamp": {"stl": "out/motor-clamp.stl"},
         "pinion": {"stl": "out/pinion.stl"},
         "clutch-sleeve": {"stl": "out/clutch-sleeve.stl"},
         "clutch-collar": {"stl": "out/clutch-collar.stl"},
         "wave-washer": {"mesh": washer(B.SPRING[0], B.SPRING[1], B.SPRING_X1, R.PINION_X0), "hardware": True,
                         "label": "arandela ondulada DIN 137 B M3 (acero)"},
         "shim": {"mesh": washer(B.SHIM[0], B.SHIM[1], B.COLLAR_X1, B.SPRING_X1), "hardware": True,
                  "label": "arandela de ajuste DIN 988 3×6×0,1 (0 a 3, según el ajuste)"},
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
         "holder": {"mesh": R.holder(), "hardware": True,
                    "label": "portapilas 4×AAA (catálogo, en el cuerpo)"},
         "eyes-board": {"mesh": R.eyes_board(), "hardware": True,
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
    out["pinion"] = up @ rx(ap, YM, ZM) @ own(R.PINION_X0)
    out["clutch-sleeve"] = up @ rx(ap, YM, ZM) @ own(B.SLEEVE_X0)
    out["clutch-collar"] = up @ rx(ap, YM, ZM) @ own(B.COLLAR_X0)
    out["wave-washer"] = out["shim"] = up
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
            ("pinion", "clutch-sleeve"): 0.08,            # slip bore Ø5.2 on Ø5 (SLIP_BORE 0.1 a side)
            ("wave-washer", "n20-shaft"): 0.08,           # DIN 137 B M3 bore Ø3.2 on the Ø3 shaft
            ("wave-washer", "clutch-sleeve"): 0.15,       # sleeve ends 0.2 inside the pinion's -X face
            ("wave-washer", "clutch-collar"): 0.05,       # one 0.1 shim between them (0 to 0.3 by the setting)
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
    ("clutch-sleeve", "n20-shaft"): "sleeve's D-bore pressed on the D-shaft (DSHAFT)",
    ("clutch-collar", "n20-shaft"): "collar's D-bore pressed on the shaft's tip (DSHAFT)",
    ("pinion", "clutch-sleeve"): "pinion's +X face on the shoulder: the clutch's +X friction face (bore SLIP_BORE 0.1)",
    ("pinion", "wave-washer"): "the wave washer presses the pinion's -X face: the clutch's -X friction face",
    ("shim", "wave-washer"): "stack: wave washer on the shims", ("clutch-collar", "shim"): "stack: shims on the collar",
    ("n20-shaft", "shim"): "DIN 988 bore Ø3 on the Ø3 shaft (modelled at the shaft's size)",
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
_CL = B.SHOULDER_X[1] - R.PINION_X0          # pinion + shoulder along X (5.0): the zone covers both
KEEP_OUT["pinion-cap"] = {
    "part": "pinion", "mesh": rod(2 * B.PIN_R, _CL + 2 * (B.GAX + CAP_PLAY), [0, 0, -B.GAX - CAP_PLAY],
                                  [0, 0, 1], n=96),
    "why": f"pinion faces + {B.GAX} axial + the cap's X play {CAP_PLAY} (cap only)",
    "except": [p for p in PARTS if p not in ("cap", "pinion")],
    "except_why": "this zone is for the cap at either skirt stop; every other part is in pinion-clear"}
KEEP_OUT["pinion-clear"] = {
    "part": "pinion", "mesh": rod(2 * B.PIN_R, _CL + 2 * B.GAX, [0, 0, -B.GAX], [0, 0, 1], n=96),
    "why": f"pinion tip circle + {B.GAX} radial; pinion's -X face and the sleeve's shoulder + {B.GAX} axial "
           f"(cap, clamp, walls, pad)",
    "except": ["idler-3-v2", "n20-shaft", "n20", "clutch-sleeve", "wave-washer", "shim", "clutch-collar"],
    "except_why": "idler 3 v2 meshes (GEARS); shaft, sleeve, wave washer, shims and collar are the clutch "
                  "itself; the gearbox face is the 0.8 gauge (the zone's +X face)"}
KEEP_OUT["collar-clear"] = {
    "part": "clutch-collar", "mesh": rod(2 * (B.COLLAR_D / 2 + B.GAX), B.COLLAR_L + B.GAX, [0, 0, -B.GAX], [0, 0, 1],
                                         n=96),
    "why": f"spinning collar + {B.GAX} radial and to -X (the -X wall's notch r {B.NOTCH_R}, the cap's window)",
    "except": ["n20-shaft", "shim", "wave-washer", "pinion", "clutch-sleeve"],
    "except_why": "the clutch's own parts (shaft, shims on its +X face)"}
KEEP_OUT["idler3-ring"] = {
    "part": "n20-shaft",
    "mesh": rod(2 * (R.PINION_TIP_R - 2.0 - 0.23), 2 * (R.IDLER3_FACE / 2 + fits.GEAR_THRUST_IDLER.side),
                [CX - R.IDLER3_FACE / 2 - fits.GEAR_THRUST_IDLER.side, YM, ZM], [1, 0, 0], n=96),
    "why": "ring r 4.77 round the motor axis over |x| ≤ 2.95 (idler 3 at either float): idler 3's tip (r 5.27 "
           "floated, 5.37 nominal) stays out of it, so the clutch's shoulder (r 4.5) and wave washer (r 4.0) inside "
           "it clear idler 3 by ≥ GEAR_TIP 0.5 (design-plan-clutch.md 3b)",
    "except": ["pinion", "clutch-sleeve", "wave-washer", "shim", "clutch-collar", "n20", "drive-module"],
    "except_why": "the clutch itself; the module's pinion zone is checked by pinion-clear"}
RETAIN = {**{f"crankshaft-{i + 1}": {"spin": [1, 0, 0], "play": 0.5, "not_by": list(LEGS)} for i in range(4)},
          **{f"idler-{k + 1}": {"spin": [1, 0, 0], "play": 1.0} for k in range(2)},
          "idler-3-v2": {"spin": [1, 0, 0], "play": 1.0},
          # the clutch: pinion, wave washer and shims spin on the shaft (that is the clutch); sleeve and collar are
          # held by their press (DSHAFT, K1 pull-off) and, like the old pinion, have the 0.8 gauge / notch end behind
          "pinion": {"spin": [1, 0, 0], "play": 1.0},
          "clutch-sleeve": {"play": 1.0}, "clutch-collar": {"play": 1.0},
          "wave-washer": {"spin": [1, 0, 0], "play": 0.5}, "shim": {"spin": [1, 0, 0], "play": 0.5},
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
            # on the bench, the jig stood on the table (-X face down, open side +Z): the clutch stacked in its
            # pockets from the bottom up (collar, shim, wave washer, pinion, sleeve), the fork over the sleeve's
            # shoulder, then the motor pushed down (-X): its shaft presses into the sleeve and the collar at once
            ("clutch-collar", [0, 0, 1], {"bench": ["press-jig"],
                                          "note": "collar into the jig's Ø9.5 pocket, dot up (+X), turned so the dot "
                                                  "points the way the motor shaft's flat points"}),
            ("shim", [1, 0, 0], {"bench": ["press-jig", "clutch-collar"],
                                 "note": "shims (0.1 to start) dropped onto the collar from above"}),
            ("wave-washer", [1, 0, 0], {"bench": ["press-jig", "clutch-collar", "shim"],
                                        "note": "wave washer dropped onto the shims"}),
            ("pinion", [0, 0, 1], {"bench": ["press-jig", "clutch-collar", "shim", "wave-washer"],
                                   "note": "pinion slid into its pocket from the open side, onto the step"}),
            ("clutch-sleeve", [1, 0, 0], {"bench": ["press-jig", "clutch-collar", "shim", "wave-washer", "pinion"],
                                          "note": "sleeve dropped into the pinion, shoulder up, its dot the same way "
                                                  "as the collar's"}),
            ("gauge-fork", [0, 0, 1], {"bench": ["press-jig", "clutch-collar", "shim", "wave-washer", "pinion", "clutch-sleeve"],
                                       "note": "fork down into the jig's slot, flat on the sleeve's shoulder"}),
            (("n20", "n20-shaft"), [1, 0, 0],
             {"bench": ["press-jig", "clutch-collar", "shim", "wave-washer", "pinion", "clutch-sleeve", "gauge-fork"],
              "except": {"clutch-sleeve": "D-bore pressed on the D-shaft (DSHAFT, modelled at zero clearance)",
                         "clutch-collar": "D-bore pressed on the shaft's tip (DSHAFT)",
                         "shim": "DIN 988 bore Ø3 on the Ø3 shaft (modelled at the shaft's size)"},
              "note": "shaft's flat over the two dots; motor pushed down by its can into the socket until the "
                      "gearbox face stops on the fork"}),
            ("press-cup", [1, 0, 0],
             {"bench": ["press-jig", "clutch-collar", "shim", "wave-washer", "pinion", "clutch-sleeve", "gauge-fork", "n20", "n20-shaft"],
              "note": "only if the thumb is not enough: cup over the can's rear, jig and cup between the vise's "
                      "jaws, closed until the gearbox face stops on the fork; then the fork lifts out (+Z) and the "
                      "motor with its clutch slides out of the jig (+Z); lever test, shims changed if needed"}),
            # one drop: the motor with its clutch (idler 3 is the pinion's GEARS partner: crank 1 turns it)
            (DROP, [0, 0, 1]),
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
    {"at": DROP, "tool": tool("finger", [CX + 20.0, YM, R.MOTOR_ENVELOPE[1][2]], [0, 0, 1]),
     "why": "motor with its clutch lowered onto the pad and V saddle by hand"},
    *[{"at": n, "tool": tool("finger", [CX + B.JIG_TOP + 0.5, YM, ZM], [1, 0, 0], d=10.0, reach=20.0),
       "why": "on the bench: dropped from the fingertips into the jig's socket mouth (jig standing, +X up); it "
              "falls onto the part below"} for n in ("shim", "wave-washer")],
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
                "press-jig": np.eye(4),
                "pinion": np.eye(4), "clutch-collar": np.eye(4),   # flat, -X face down (own frame z 0)
                "clutch-sleeve": FLIP,                 # shoulder (+X face) down, the D-bore vertical                # on its -Z face, the open side up: no overhang
                "press-cup": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])}     # top plate down
SECTIONS = [([CX, 0, 0], [1, 0, 0]),                                  # gear plane: all gears, pinion, end blocks
            ([CX + B.PIN_X1 - 1.0, 0, 0], [1, 0, 0]),                 # +X wall: journals, pins, keeper, pad
            ([CX - 4.8, 0, 0], [1, 0, 0]),                            # -X wall: blind pin ends, shaft U-slot
            ([CX, YM, ZM], [0, 1, 0]),                                # motor axis: clutch, pad, V saddle, clamp
            ([CX + (B.COLLAR_X0 + B.COLLAR_X1) / 2, 0, 0], [1, 0, 0]),  # collar in the -X wall's notch
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
    ("clutch-sleeve", "n20-shaft"): {"fit": fits.DSHAFT, "why": "sleeve's D-bore pressed on the D-shaft"},
    ("clutch-collar", "n20-shaft"): {"fit": fits.DSHAFT, "why": "collar's D-bore pressed on the shaft's tip"},
    ("pinion", "clutch-sleeve"): {"fit": fits.SLIP_BORE,
                                  "where": _box([CX + R.PINION_X0 + R.PINION_FACE / 2, YM, ZM],
                                                [R.PINION_FACE - 0.4, 8.0, 8.0]),
                                  "why": "pinion's Ø5.2 bore turning on the Ø5 sleeve (slip bore, CL1)"},
    ("clutch-collar", "drive-module"): {"fit": fits.GEAR_AXIAL,
                                        "where": _box([CX + (B.NOTCH_X0 + B.COLLAR_X1) / 2, YM, ZM - 3.0],
                                                      [B.COLLAR_X1 - B.NOTCH_X0 + 1.0, 14.0, 6.0]),
                                        "why": "spinning collar in the -X wall's notch: 1.0 radial, 0.8 to its end"},
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
         "pinion": "none needed: round bore, both faces alike (it goes on either way round)",
         "clutch-sleeve": "a dot on the shoulder's +X face over the D-bore's flat: line it up with the shaft's flat",
         "clutch-collar": "a dot on the +X face over the D-bore's flat: the same way as the sleeve's dot",
         "wave-washer": "none needed: symmetric", "shim": "none needed: flat, symmetric",
         "drive-module": "FRONT arrow (pointing -Y) on the front block's +X face; 1-4 dice dots beside each slot",
         "cap": "a dot on its +X edge over every slot (it fits one way only)",
         "n20": "polarity: «+» (red wire, +Y side) and «-» sunk in the end wall's +X face; wires leave on +Y "
                "(leg 3R passes 2.9 mm from the motor's -Y side)"}
LABELS = {"es": {"drive-module": "módulo de transmisión", "cap": "tapa", "motor-clamp": "brida del motor",
                 "pinion": "piñón", "clutch-sleeve": "casquillo del embrague",
                 "clutch-collar": "collarín del embrague", "wave-washer": "arandela ondulada",
                 "shim": "arandelas de ajuste", "idler-3-v2": "rueda intermedia 3 (v2)", "pin-keeper": "retén de pasadores",
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
    {"part": "clutch-sleeve", "what": "D-bore across the flat", "nominal": R.N20_SHAFT_D - R.N20_SHAFT_FLAT,
     "tol": (-0.1, 0.05), "points": "flat to the round side"},
    {"part": "clutch-collar", "what": "D-bore across the flat", "nominal": R.N20_SHAFT_D - R.N20_SHAFT_FLAT,
     "tol": (-0.1, 0.05), "points": "flat to the round side"},
    {"part": "clutch-sleeve", "what": "journal diameter (the pinion turns on it)", "nominal": B.SLEEVE_OD,
     "tol": (-0.1, 0.05), "points": "two places 90° apart"},
    {"part": "pinion", "what": "bore diameter (slip bore)", "nominal": B.PINION_BORE, "tol": (-0.05, 0.1),
     "points": "pin gauge or caliper's inside jaws, both faces"},
    {"part": "pinion", "what": "face width", "nominal": R.PINION_FACE, "tol": (-0.1, 0.05), "points": "rim"},
    {"part": "pinion", "what": "slip torque (lever test, N·mm): weight on the CL1 arm's 30 mm hole that makes it slip, "
     "3 trials; window 129-196 N·mm = 440-665 g at 30 mm", "nominal": 162.5, "tol": (-33.5, 33.5),
     "points": "motor held (380:1 does not back-drive), arm on the pinion, weight hung at the hole, raised slowly; "
               "add a shim if it slips below 440 g, take one off above 665 g",
     "when": "bench, after the press, before the drop (and once a year)"},
    {"part": "pinion", "what": "CL1-heat: motor run 60 s at 4.8 V with the crank blocked (slip torque after, N·mm)",
     "nominal": 162.5, "tol": (-33.5, 33.5), "points": "no fusing or smear on the faces; slip torque re-measured "
               "(lever test) inside the window; if it fails, the time it lasted / 2 goes into the kit rule",
     "when": "coupon CL1, before the robot's first run"},
    {"part": "idler-3-v2", "what": "face width", "nominal": R.IDLER3_FACE, "tol": (-0.1, 0.05), "points": "rim"},
    {"part": "pin-keeper", "what": "thickness", "nominal": B.KEEPER_T, "tol": (-0.1, 0.1), "points": "strip"},
    {"part": "gauge-fork", "what": "thickness (the 0.8 gauge), measure before use", "nominal": B.GAX,
     "tol": (-0.05, 0.05), "points": "both prongs, beside the slot", "when": "kit step: before the press"},
    {"part": "clutch-sleeve", "what": "the shoulder's gap to the gearbox face, on the bench right after the press (motor still in "
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
             "press-cup": BENCH_VIEW, "clutch-collar": BENCH_VIEW, "shim": BENCH_VIEW, "wave-washer": BENCH_VIEW,
             "clutch-sleeve": BENCH_VIEW, DROP: (25, -60)}
STEP_NOTES = {   # what the step means, for the documenter (kit «pasos»; keys as workshop_kit: a part or «a + b»)
    "clutch-collar": "on the bench: jig on the table, open side towards you; collar into the small deep pocket, "
                     "dot up, turned to point the way the motor shaft's flat points",
    "shim": "drop the shims onto the collar (one 0.1 to start)",
    "wave-washer": "drop the wave washer onto the shims",
    "pinion": "pinion slid into its pocket from the open side, flat on the step (either face up)",
    "clutch-sleeve": "sleeve dropped into the pinion, shoulder up, its dot the same way as the collar's",
    "gauge-fork": "on the bench: measure the fork first (0.8 ± 0.05); slide it down into the jig's slot, flat on the "
                  "sleeve's shoulder",
    "n20 + n20-shaft": "on the bench: shaft's flat over the two dots; push the motor down into the socket by its "
                       "can (thumb on the rim below the terminals) until the gearbox face stops on the fork; note "
                       "whether it went on by thumb or needed the vise",
    "press-cup": "only if the thumb is not enough: cup over the can's rear, jig and cup between the vise's jaws, "
                 "closed until the gearbox face stops on the fork. Then: the fork lifts out snug and slides back in "
                 "snug (the 0.8 gap); fork out, the motor with its pinion slides out of the jig towards you",
    "n20 + n20-shaft + clutch-sleeve + pinion + wave-washer + shim + clutch-collar": "lever test first (440-665 g at "
    "30 mm; a shim more or less: collar pried off, a new one pressed); then lower the motor with its clutch from above onto the pad and the V saddle; turn "
                                "crank 1 a little until the pinion drops into the teeth (380:1: the motor shaft "
                                "cannot be turned by hand)",
    "i7": "service: legs off, robot on its back, 4 screws from below (Part B)"}


# =====================================================================================================================
# The shell, the forks, the cover and the front block on top of Part A (was verify_b1.py and verify_fb.py)
# =====================================================================================================================
BV = SHL.BV
MIN_GAP = 0.2
SECTIONS += [([CX - 9.0, 0, 0], [1, 0, 0]),                      # rear screw, shelf, groove
             ([CX, 0, 0], [1, 0, 0])]

# the carcass keep-in was Part A's stand-in for the shell: it applies to Part A's static parts, not the shell itself
_static = [n for n, p in PARTS.items() if not p.get("bench") and not n.startswith(("crankshaft", "idler-1",
                                                                                    "idler-2", "leg-"))]
KEEP_IN = {k: {**v, "parts": [n for n in _static if n not in ("idler-3-v2", "n20-shaft") + DROP]}
           for k, v in KEEP_IN.items()}

# ---- parts: the shell -----------------------------------------------------------------------------------------------
LITE = os.environ.get("SHELL_LITE") == "1"                 # shell.py --lite's mesh, while trying a fix (never final)
# FB_CHASSIS=<stl>: a what-if shell (e.g. the shell cut by front_block.clear_outline(), before shell.py does it)
PARTS["chassis"] = {"stl": os.environ.get("FB_CHASSIS", "out/chassis-lite.stl" if LITE else "out/chassis.stl"),
                    "fixed": True}
if LITE:
    print("verify: SHELL_LITE=1, checking out/chassis-lite.stl (decimated body, legs every 30°): not a final result")
PARTS["drive-module"]["fixed"] = False                     # it now stands on the shell (I7)

# I7: positions and stock lengths from shell.py (one source)
_base = R.carcass("base")
_mod = trimesh.load(os.path.join(HERE, "out", "drive-module.stl"))
I7 = SHL.i7_bosses(_base, _mod)[2]
for k, r in enumerate(I7):
    p = [CX + r["x"], r["y"], r["head"]]
    PARTS[f"i7-screw-{k + 1}"] = {"mesh": m3(p, [0, 0, 1], r["length"]), "hardware": True, "fixed": True,
                                  "label": f"M3×{r['length']:g} Allen"}
    PARTS[f"i7-nut-{k + 1}"] = {"mesh": nut([CX + r["x"], r["y"], r["nut"][0] + 0.15], [0, 0, 1]),
                                "hardware": True, "fixed": True, "label": "tuerca M3"}

# I4: forks and their swivel screws (base v1's fork_mounts with the shell's gaps: shell.py sets FORK_GAP = LEG_PATH)
GAP = SHL.FORK_GAP_Z                               # shell.py: the fork's faces up and down, a turning fit (TURN)
FORK_BOT, FORK_TOP = BV.FORK_BOT, BV.FORK_TOP
BOSS_TOP = FORK_BOT - GAP
BOSS_BOT = BOSS_TOP - (BV.SCREW_L - BV.SCREW_IN - GAP)
FORKS = {}
_U = {f"fork-{int(f['key'][0]) + 1}{f['key'][1]}": f["u"] for f in SHL.fork_frames_cached()}   # nut slot directions


def _turned(m, x, y, d):
    """A nut mesh turned as its pocket (shell.nut_pocket: a corner along the slot, the flats on its sides)."""
    m.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(d[1], d[0]), [0, 0, 1], [x, y, 0]))
    return m


for n, f, M in L.poses(0.0):
    if n.startswith("pivot"):
        name = f"fork-{int(n[5]) + 1}{n[6]}"
        FORKS[name] = n
        PARTS[name] = {"stl": L.stl(f)}
        P = M[:3, 3]
        PARTS[f"{name}-screw-low"] = {"mesh": m3([P[0], P[1], BOSS_BOT], [0, 0, 1], BV.SCREW_L), "hardware": True,
                                      "fixed": True, "label": "M3×10 Allen"}
        PARTS[f"{name}-screw-up"] = {"mesh": m3([P[0], P[1], R.BAND_TOP - BV.HEAD_H], [0, 0, -1], BV.SCREW_L),
                                     "hardware": True, "fixed": True, "label": "M3×10 Allen"}
        PARTS[f"{name}-nut-low"] = {"mesh": _turned(nut([P[0], P[1], (BOSS_BOT + BOSS_TOP) / 2 - BV.NUT_T / 2 + 0.15],
                                                        [0, 0, 1]), P[0], P[1], _U[name]),
                                    "hardware": True, "fixed": True, "label": "tuerca M3"}
        PARTS[f"{name}-nut-up"] = {"mesh": _turned(nut([P[0], P[1], FORK_TOP + GAP + 1.2 + 0.15], [0, 0, 1]),
                                                   P[0], P[1], _U[name]),
                                   "hardware": True, "fixed": True, "label": "tuerca M3"}
FORK_HW = [f"{f}-{s}" for f in FORKS for s in ("screw-low", "screw-up", "nut-low", "nut-up")]

# crank cover (Morante 2026-11-15, option b): on 3 posts, 2 × M3×10 from above into nuts in the posts
PARTS["crank-cover"] = {"stl": "out/crank-cover.stl"}
COVER_SCREWS = [(x, y, d) for x, y, kind, d in SHL.COVER_POSTS if kind == "screw"]
for k, (x, y, d) in enumerate(COVER_SCREWS):
    top = SHL.COVER_Z0 + SHL.COVER_T
    PARTS[f"cover-screw-{k + 1}"] = {"mesh": m3([x, y, top], [0, 0, -1], SHL.COVER_SCREW_L), "hardware": True,
                                     "fixed": True, "label": "M3×10 Allen"}
    _n = _turned(nut([x, y, SHL.COVER_Z0 - 1.2 - BV.NUT_T + 0.15], [0, 0, 1]), x, y, d)
    PARTS[f"cover-nut-{k + 1}"] = {"mesh": _n,                    # turned as its pocket (a corner along the slot)
                                   "hardware": True, "fixed": True, "label": "tuerca M3"}


def _tube(points, d):
    """A wire bundle along a polyline (Ø d), with round joints."""
    segs = []
    for a, b in zip(points[:-1], points[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        segs.append(rod(d, float(np.linalg.norm(b - a)), a, b - a))
        segs.append(trimesh.creation.icosphere(subdivisions=1, radius=d / 2).apply_translation(b))
    return trimesh.boolean.union(segs, engine="manifold")


# motor leads (I12): out of the terminals on +Y, up, along the clips to the switch's inner face
_T = R.MOTOR_ENVELOPE[1][0] - 1.0
_LZ0 = R.MOTOR_AXIS[2] + R.N20_TERM_Z[1] + 0.5      # just over the terminal block, under the clamp
_SB = SHL.SW_BODY
_ZL = (_SB[4] + _SB[5]) / 2
LEAD_PATH = [(_T, R.MOTOR_AXIS[1] + 4.0, _LZ0), (_T, SHL.LEAD_Y, _LZ0), (_T, SHL.LEAD_Y, SHL.LEAD_Z),   # up the terminals
             ((_SB[0] + _SB[2]) / 2 - 0.3, SHL.LEAD_Y, SHL.LEAD_Z),        # through clip 1 (shell) and the cover's eye
             ((_SB[0] + _SB[2]) / 2 - 0.3, SHL.LEAD_Y, _ZL),               # down in front of the cradle's front wall
             ((_SB[0] + _SB[2]) / 2 - 0.3, SHL.LEAD_Y + 0.9, _ZL)]        # into the pins' slot (soldered to them)
# the switch on the crank cover (coordinator 2026-11-16, option b), its stop screw and nut
PARTS["switch"] = {"mesh": SHL.switch_mesh(), "hardware": True, "label": "interruptor SS12D00 (medidas de catálogo)"}
PARTS["motor-leads"] = {"mesh": _tube(LEAD_PATH, SHL.LEAD_D), "hardware": True, "fixed": True,
                        "label": "cables del motor (2 × 26 AWG) por sus pinzas hasta el interruptor"}

# ---- parts: the front block v2 (I8) ---------------------------------------------------------------------------------
NAME = FB.NAME
PARTS[NAME] = {"stl": f"out/{NAME}.stl"}
HEAD_Z = R.DECK_TOP + FB.PAD_T                          # head face on the boss (76.8)
NUT_Z = HEAD_Z - FB.SCREW_L + 0.5                       # shell.front_block_seat: nut 0.5 above the tip
for k, (x, y, d) in enumerate(FB.FB_SCREWS_FULL):
    PARTS[f"fb-screw-{k + 1}"] = {"mesh": m3([x, y, HEAD_Z], [0, 0, -1], FB.SCREW_L), "hardware": True,
                                  "fixed": True, "label": "M3×10 Allen"}
    _n = nut([x, y, NUT_Z + 0.15], [0, 0, 1])
    # turned as its pocket in the shell (base v1 nut_pocket: flats facing the slot's sides, a corner towards the slot;
    # measured on out/chassis.stl 2026-11-16: flats at 2.9 across ±Y for a slot along X)
    _n.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(d[1], d[0]), [0, 0, 1], [x, y, 0]))
    PARTS[f"fb-nut-{k + 1}"] = {"mesh": _n, "hardware": True, "fixed": True, "label": "tuerca M3"}
FB_HW = [f"fb-{s}-{k + 1}" for k in range(2) for s in ("screw", "nut")]

_poses_a = poses


def poses(t):
    out = _poses_a(t)
    lp = {n: M for n, _, M in L.poses(np.radians(t[0]))}
    for name, n in FORKS.items():
        out[name] = lp[n]
    return out


# ---- gaps and contacts ----------------------------------------------------------------------------------------------
for m in LEGS:                                           # moving legs: LEG_PATH 0.8 to the shell
    PAIR_GAP[(m, "chassis")] = fits.LEG_PATH.side
for m in FORKS:                                          # forks: TURN up and down (JOINTS); sideways the pocket is
    PAIR_GAP[(m, "chassis")] = fits.TURN.side            # FORK_GAP (LEG_PATH + 0.2) by construction (shell.py)
for f in FORKS:
    for s in ("screw-low", "screw-up"):
        PAIR_GAP[(f"{f}-{s}", "chassis")] = 0.1          # M3 in Ø3.3 (STEEL)
        PAIR_GAP[(f"{f}-{s}", f)] = 0.1                  # the fork turns on the screw's shank
    for s in ("nut-low", "nut-up"):
        PAIR_GAP[(f"{f}-{s}", "chassis")] = 0.1          # nut in its pocket (+0.15 a side)
for k in range(len(COVER_SCREWS)):
    PAIR_GAP[(f"cover-screw-{k + 1}", "chassis")] = 0.1
    PAIR_GAP[(f"cover-screw-{k + 1}", "crank-cover")] = 0.1
    PAIR_GAP[(f"cover-nut-{k + 1}", "chassis")] = 0.1
PAIR_GAP[("motor-leads", "chassis")] = 0.1                 # in the clips' slots (WINDOW round the leads)
PAIR_GAP[("motor-leads", "crank-cover")] = 0.1               # through the eye (WINDOW round the leads)
for leg in LEGS:
    PAIR_GAP[(leg, "crank-cover")] = fits.LEG_PATH.side
for leg in LEGS:
    PAIR_GAP[(leg, "motor-leads")] = fits.LEG_PATH.side
for k in range(4):
    PAIR_GAP[(f"i7-screw-{k + 1}", "chassis")] = 0.1
    PAIR_GAP[(f"i7-screw-{k + 1}", "drive-module")] = 0.1
    PAIR_GAP[(f"i7-nut-{k + 1}", "drive-module")] = 0.1
# front block (I8)
for leg in LEGS:
    PAIR_GAP[(leg, NAME)] = fits.LEG_PATH.side
PAIR_GAP[(NAME, "cap")] = fits.WINDOW.side
PAIR_GAP[(NAME, "cap-screw")] = fits.WINDOW.side
PAIR_GAP[(NAME, "crank-cover")] = fits.WINDOW.side
for k in range(2):
    PAIR_GAP[(f"fb-screw-{k + 1}", "chassis")] = 0.1      # M3 in Ø3.3 (STEEL 0.15)
    PAIR_GAP[(f"fb-screw-{k + 1}", NAME)] = 0.1
    PAIR_GAP[(f"fb-nut-{k + 1}", "chassis")] = 0.1        # nut in its pocket (+0.15 a side)

ALLOWED_CONTACT[("drive-module", "chassis")] = "module on its 4 bosses; its top in the deck window, WINDOW 0.5 a side"
for k in range(4):
    ALLOWED_CONTACT[(f"i7-screw-{k + 1}", "chassis")] = "head clamps the boss from below"
    ALLOWED_CONTACT[(f"i7-screw-{k + 1}", f"i7-nut-{k + 1}")] = "screw in its nut"
    ALLOWED_CONTACT[(f"i7-nut-{k + 1}", "drive-module")] = "nut pulled down onto its pocket"
ALLOWED_CONTACT[("crank-cover", "chassis")] = "cover on its 3 posts; the spigot in its hole (LOCATOR)"
for k in range(len(COVER_SCREWS)):
    ALLOWED_CONTACT[(f"cover-screw-{k + 1}", "crank-cover")] = "head clamps the cover"
    ALLOWED_CONTACT[(f"cover-screw-{k + 1}", f"cover-nut-{k + 1}")] = "screw in its nut"
ALLOWED_CONTACT[("motor-leads", "n20")] = "the leads are soldered to the motor's terminals"
ALLOWED_CONTACT[("motor-leads", "switch")] = "the leads are soldered to the switch's pins"

for f in FORKS:
    ALLOWED_CONTACT[(f"{f}-screw-low", "chassis")] = "head clamps the boss from below"
    ALLOWED_CONTACT[(f"{f}-screw-up", "chassis")] = "head in its counterbore at the band top"
    ALLOWED_CONTACT[(f"{f}-screw-low", f"{f}-nut-low")] = "screw in its nut"
    ALLOWED_CONTACT[(f"{f}-screw-up", f"{f}-nut-up")] = "screw in its nut"
    leg = "leg-" + f[5:]
    ALLOWED_CONTACT[(f, leg)] = "the leg pivots in its fork (legs design: the fork's window, its pivot pin)"
    ALLOWED_CONTACT[(f"{f}-screw-low", f)] = "the screw's tip is the fork's lower swivel (3 mm into the fork)"
    ALLOWED_CONTACT[(f"{f}-screw-up", f)] = "the screw's tip is the fork's upper swivel"
# front block (I8)
ALLOWED_CONTACT[(NAME, "chassis")] = "the pads stand on the deck (z 74.8) inside their LOCATOR lips (JOINTS measures " \
                                     "the lips)"
for k in range(2):
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", NAME)] = "head clamps the pad's boss"
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", f"fb-nut-{k + 1}")] = "screw in its nut"
    ALLOWED_CONTACT[(f"fb-nut-{k + 1}", "chassis")] = "nut pulled up against its pocket under the deck"
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", "chassis")] = "the shank passes the deck and the boss to its nut"

# ---- keep-out ---------------------------------------------------------------------------------------------------------
# wires (I12): never under the crank cover (the crank webs and the window), never on the module's top or the motor
_cw = SHL.CRANK_WIN
KEEP_OUT["wires-crank-window"] = {
    "part": "chassis", "mesh": trimesh.creation.box(bounds=[(_cw[0], _cw[1], 57.0), (_cw[2], _cw[3], SHL.COVER_Z0)]),
    "why": "the crank webs sweep under the deck here; the crank cover closes it: no wire may lie in it",
    "except": [n for n in PARTS if n != "motor-leads"],
    "except_why": "this zone is for wires; the parts in it are checked by the motion and joints checks"}
KEEP_OUT["wires-motor"] = {
    "part": "chassis", "mesh": trimesh.creation.box(bounds=[np.array(R.MOTOR_ENVELOPE[0]) - [3, 3, 3],
                                                            (R.MOTOR_ENVELOPE[1][0] - R.N20_TERM_L, R.MOTOR_ENVELOPE[1][1] + 3,
                                                             R.MOTOR_ENVELOPE[1][2] + 3)]),
    "why": "motor gearbox and can + 3 mm: the leads leave behind them, at the terminals",
    "except": [n for n in PARTS if n != "motor-leads"],
    "except_why": "this zone is for wires"}
_h = trimesh.creation.cylinder(radius=K.HEAD_D / 2 + fits.WINDOW.side, height=K.HEAD_H + fits.WINDOW.side, sections=48)
_h.apply_translation([FB.CAP_SCREW_XY[0], FB.CAP_SCREW_XY[1], FB.CAP_TOP + (K.HEAD_H + fits.WINDOW.side) / 2])
KEEP_OUT["cap-screw-head"] = {
    "part": "chassis", "mesh": _h,
    "why": "the cap's front screw head + WINDOW (plan: the block >= 83.35 over it): the cap comes off with the block off",
    "except": ["cap-screw", "cap", "chassis"], "except_why": "the screw, the cap it clamps, the shell's clear space"}
# the block stays inside the carcass's front block (base v1, lifted) but for the tongues (body v2's L-slots take them)
_v1 = trimesh.load(os.path.join(HERE, "..", "base", "out", "front-block.stl"))
_fbm = trimesh.load(os.path.join(HERE, "out", f"{NAME}.stl"))
_t0, _t1 = _fbm.bounds[0][0] + FB.TONGUE_OUT, _fbm.bounds[1][0] - FB.TONGUE_OUT     # the side faces, read on the part
KEEP_IN["carcass-front-block"] = {
    "mesh": _v1, "inset": 0.0, "parts": [NAME],
    "why": "front block v2 is the carcass's front block made hollow and cut: nothing of it outside the carcass shape",
    "allow": {"tongue-L": {"box": ((_t0 - FB.TONGUE_OUT - 0.5, FB.TONGUE_Y[0] - 0.5, 90.0),
                                   (_t0 + 0.5, FB.TONGUE_Y[1] + 0.5, FB.TONGUE_TOP)),
                           "inset": -(FB.TONGUE_OUT + 0.2), "why": "the -X hook tongue (plan C1), into body v2's L-slot"},
              **{f"tube-{k + 1}": {"box": ((x - 4.5, y - 4.5, FB.FOOT_TOP - 0.1), (x + 4.5, y + 4.5, 110.0)),
                                  "inset": -0.6, "why": "the access tube's 0.8 wall (rev 3.2 screw place) stands up to "
                                  "0.45 mm proud of the carcass's face curve at y -55, under the body's head"}
                 for k, (x, y) in enumerate(FB.FB_SCREWS)},
              "tongue-R": {"box": ((_t1 - 0.5, FB.TONGUE_Y[0] - 0.5, 90.0),
                                   (_t1 + FB.TONGUE_OUT + 0.5, FB.TONGUE_Y[1] + 0.5, FB.TONGUE_TOP)),
                           "inset": -(FB.TONGUE_OUT + 0.2), "why": "the +X hook tongue"}}}

# ---- retention -------------------------------------------------------------------------------------------------------
RETAIN["drive-module"] = {"play": 0.5}
RETAIN["crank-cover"] = {"play": 0.5}
RETAIN["switch"] = {"play": 0.9, "tilt": 11.0}   # WINDOW 0.5 a side round its catalogue size (plan: redrawn once
                       # measured): 0.87 along a box diagonal, and a 6 × 6 section rocks 10.6° in 7 × 7 about its long
                       # axis (the lever moves ±0.5 in its 3 mm window). Once measured the cradle goes to LOCATOR          # cradle walls, floor and top pad (WINDOW); at +X the shell's stop rib
for f in FORKS:
    RETAIN[f] = {"spin": [0, 0, 1], "play": 0.5, "not_by": ["leg-" + f[5:]]}   # swivels on its 2 screws
RETAIN[NAME] = {"play": 0.5}       # pads in LOCATOR lips (0.2 a side, 1.5 tall); deck below; 2 screws above

# ---- assembly (plan order) -------------------------------------------------------------------------------------------
MODULE_GROUP = ("drive-module", "idler-1", "idler-2", "idler-3-v2", "pin-1", "pin-2", "pin-3", "pin-keeper",
                "keeper-screw", "keeper-nut", "crankshaft-1", "crankshaft-2", "crankshaft-3", "crankshaft-4", "cap",
                "cap-screw", "cap-nut", "shared-nut", "clamp-nut", "i7-nut-1", "i7-nut-2", "i7-nut-3", "i7-nut-4")
_ASSEMBLY_A = ASSEMBLY
_bench, ASSEMBLY = ["drive-module"], [("chassis", None)]
# cover nuts on the bare shell: pushed 6 mm along their slots by the pliers' nose (ACCESS checks it, 25 mm reach);
# the 60 mm straight-path test does not apply (every way out of a post meets the switch block, the band or the clip
# 33-43 mm away), so they are placed, as the fork nuts are
ASSEMBLY += [(f"cover-nut-{k + 1}", None) for k in range(len(COVER_SCREWS))]
# front block nuts, step 9a, on the bare shell before the module (its slot runs 12 mm towards CX, into the module's
# space): pushed along the slot by the pliers' nose (ACCESS); the 60 mm straight-path test does not apply (the bowl's
# far wall stands 29-36 mm away), so they are placed, as the cover nuts are
ASSEMBLY += [(f"fb-nut-{k + 1}", None) for k in range(2)]
for step in _ASSEMBLY_A:
    names, d, *o = step
    if names == "drive-module":
        continue
    if names in (DROP, "motor-clamp", "shared-screw", "clamp-screw") or \
            (isinstance(names, str) and names.startswith("leg-")) or names in ("holder", "eyes-board"):
        continue                                          # these go in on the shell, below
    opts = dict(o[0]) if o else {}
    if "bench" not in opts:                               # module steps, on the bench with what is there
        opts["bench"] = list(_bench)
        _bench += [names] if isinstance(names, str) else list(names)
    ASSEMBLY.append((names, d, opts))
ASSEMBLY += [(f"i7-nut-{k + 1}", [n[3][0], n[3][1], 0], {"bench": list(_bench)})      # slid in along its slot
             for k, n in enumerate(B.I7_NUTS)]
ASSEMBLY.append((MODULE_GROUP, [0, 0, 1], {"note": "the module with its train and cap, no motor, into the deck "
                                                   "window from above (plan step 10)"}))
for f in FORKS:
    ASSEMBLY += [(f"{f}-nut-low", None), (f"{f}-nut-up", None), (f, None), ("leg-" + f[5:], None),
                 (f"{f}-screw-low", [0, 0, -1]), (f"{f}-screw-up", [0, 0, 1])]
ASSEMBLY += [(DROP, [0, 0, 1]), ("motor-clamp", [0, 0, 1]), ("shared-screw", [0, 0, 1]),
             ("clamp-screw", [0, 0, 1])]
# the switch goes into the cover on the bench (cover upside down; leads threaded through the eye, then soldered)
ASSEMBLY += [("switch", [1, 0, 0], {"bench": ["crank-cover"],
                                    "note": "slid in from the open +X end, lever and pins in their slots"})]
COVER_GROUP = ("crank-cover", "switch")
ASSEMBLY += [(COVER_GROUP, [0, 0, 1], {"note": "after the clamp: the cover with its switch, over the crank window, "
                                               "its spigot in the post; the leads' loop follows it"})]
ASSEMBLY += [("motor-leads", None)]
ASSEMBLY += [(f"cover-screw-{k + 1}", [0, 0, 1]) for k in range(len(COVER_SCREWS))]
ASSEMBLY += [(NAME, [0, 0, 1], {"note": "step 13: pads down into their lips, over the cap"})]
ASSEMBLY += [(f"fb-screw-{k + 1}", [0, 0, 1], {"note": "down the access tube, 2.5 hex key"}) for k in range(2)]
ASSEMBLY += [(f"i7-screw-{k + 1}", [0, 0, -1]) for k in range(4)]

ACCESS += [{"at": f"i7-nut-{k + 1}", "tool": tool("pliers", [CX + x + d[0] * 8.0, y + d[1] * 8.0, nz + K.NUT_T / 2],
                                                  [d[0], d[1], 0]),
            "why": "on the bench: nut pushed along its slot into the module, pliers"}
           for k, (x, y, nz, d) in enumerate(B.I7_NUTS)]
ACCESS += [{"at": MODULE_GROUP, "tool": tool("finger", [CX, -10.0, R.DECK_TOP + 6.0], [0, 0, 1]),
            "why": "the module with its train and cap lowered into the deck window by hand"}]
ACCESS += [{"at": f"i7-screw-{k + 1}", "tool": tool("hex-key", [CX + r["x"], r["y"], r["head"] - K.HEAD_H],
                                                     [0, 0, -1]),
            "why": f"M3×{r['length']:g} from below, robot on its back, 2.5 hex key"} for k, r in enumerate(I7)]
ACCESS += [{"at": f"cover-screw-{k + 1}", "tool": tool("hex-key", [x, y, SHL.COVER_Z0 + SHL.COVER_T + K.HEAD_H],
                                                      [0, 0, 1]), "why": "M3×10 from above, 2.5 hex key"}
           for k, (x, y, _) in enumerate(COVER_SCREWS)]
ACCESS += [{"at": "switch", "tool": tool("finger", [SHL.SW_BODY[2] + 12.0, (_SB[1] + _SB[3]) / 2, _ZL], [1, 0, 0]),
            "why": "on the bench: the switch pushed into its cradle from +X"},
           {"at": COVER_GROUP, "tool": tool("finger", [CX, 0.0, SHL.COVER_Z0 + SHL.COVER_T + 8.0], [0, 0, 1]),
            "why": "the cover with its switch lowered over the crank window by hand"}]
ACCESS += [{"at": f"cover-nut-{k + 1}", "tool": tool("pliers", [x + d[0] * 6, y + d[1] * 6, SHL.COVER_Z0 - 2.5],
                                                     [d[0], d[1], 0], d=6.0, reach=25.0),
            "why": "on the bare shell (step 9a): nut slid into its post from the side, the pliers' nose"}
           for k, (x, y, d) in enumerate(COVER_SCREWS)]
for f, n in FORKS.items():
    P = PARTS[f"{f}-screw-up"]["mesh"].centroid
    ACCESS += [{"at": f"{f}-screw-up", "tool": tool("hex-key", [P[0], P[1], R.BAND_TOP], [0, 0, 1]),
                "why": "upper swivel screw from the band top (body off), 2.5 hex key"},
               {"at": f"{f}-screw-low", "tool": tool("hex-key", [P[0], P[1], BOSS_BOT - K.HEAD_H], [0, 0, -1]),
                "why": "lower swivel screw from below, robot on its back"}]
# front block (I8)
ACCESS += [{"at": f"fb-screw-{k + 1}", "tool": tool("hex-key", [x, y, HEAD_Z + K.HEAD_H], [0, 0, 1]),
            "why": "M3×10 down the Ø6.5 access tube from the block's top, 2.5 hex key (body off)"}
           for k, (x, y, _) in enumerate(FB.FB_SCREWS_FULL)]
ACCESS += [{"at": f"fb-nut-{k + 1}", "tool": tool("pliers", [x + d[0] * 6.0, y + d[1] * 6.0, NUT_Z + K.NUT_T / 2],
                                                 [d[0], d[1], 0], d=2.0, reach=25.0),
            "why": "step 9a on the bare shell: nut pushed along its 2.7 mm slot into the boss by the pliers' nose tip "
                   "(or a small screwdriver)"}
           for k, (x, y, d) in enumerate(FB.FB_SCREWS_FULL)]

# ---- joints ----------------------------------------------------------------------------------------------------------
JOINTS[("drive-module", "chassis")] = {"fit": fits.WINDOW, "where": ((CX, -8.0, 73.8), (16.0, 90.0, 1.8)),
                                       "why": "I7: the module's top in the deck window, a side"}
for k, r in enumerate(I7):
    z0, z1 = r["head"] + 0.5, r["z_mod"] - 0.2         # the shank in its hole, above the head
    JOINTS[(f"i7-screw-{k + 1}", "chassis")] = {"fit": fits.STEEL,
                                                "where": ((CX + r["x"], r["y"], (z0 + z1) / 2), (5.0, 5.0, z1 - z0)),
                                                "why": f"I7 screw {k + 1}'s shank in its Ø3.3 hole"}
_sp = [(x, y) for x, y, kind, _ in SHL.COVER_POSTS if kind == "spigot"][0]
JOINTS[("chassis", "crank-cover")] = {"fit": fits.LOCATOR, "where": ((*_sp, SHL.COVER_Z0 + 0.8), (7.0, 7.0, 1.4)),
                                      "why": "the post's spigot in the cover's hole: locates the cover"}
JOINTS[("crank-cover", "switch")] = {"fit": fits.WINDOW, "where": (((_SB[0] + _SB[2]) / 2, (_SB[1] + _SB[3]) / 2, _ZL),
                                                                    (_SB[2] - _SB[0] + 1.5, _SB[3] - _SB[1] + 1.5, 8.0)),
                                      "why": "the switch in its cradle (catalogue size + WINDOW, redrawn once measured)"}
JOINTS[("motor-leads", "chassis")] = {"fit": fits.WINDOW, "where": ((SHL.CLIPS[0][0], SHL.LEAD_Y, SHL.LEAD_Z), (5.0, 8.0, 5.0)),
                                      "why": "motor leads in their clips' slots"}
for f in FORKS:
    P = PARTS[f"{f}-screw-up"]["mesh"].centroid
    JOINTS[(f"{f}-screw-low", "chassis")] = {"fit": fits.STEEL, "where": ((P[0], P[1], BOSS_TOP - 2.0),
                                                                          (5.0, 5.0, 2.5)),
                                             "why": "I4: lower swivel screw's shank in the boss"}
    JOINTS[(f"{f}-screw-up", "chassis")] = {"fit": fits.STEEL, "where": ((P[0], P[1], FORK_TOP + GAP + 0.6),
                                                                         (5.0, 5.0, 0.8)),
                                            "why": "I4: upper swivel screw's shank in the band"}
    JOINTS[("chassis", f)] = {"fit": fits.TURN, "where": ((P[0], P[1], (FORK_BOT + FORK_TOP) / 2),
                                                          (2 * BV.BOSS_R, 2 * BV.BOSS_R, FORK_TOP - FORK_BOT + 2.0)),
                              "why": "I4 in Z: the fork turns between the boss below and the upper boss (TURN, coupon "
                                     "K7); sideways its pocket is FORK_GAP"}
# front block (I8)
_lz = R.DECK_TOP + SHL.FB_LIP_H / 2
_hz0, _hz1 = FB.FOOT_TOP, R.BAND_TOP + SHL.LIP_H + 0.5
JOINTS[(NAME, "chassis")] = {"fit": fits.LOCATOR, "where": ((CX, -43.0, _lz), (90.0, 44.0, SHL.FB_LIP_H - 0.4)),
                             "why": "I8: both pads in their lips, a side (the deck contact is below this box)"}
JOINTS[("chassis", NAME)] = {"fit": fits.WINDOW, "where": ((CX, -43.0, (_hz0 + _hz1) / 2), (90.0, 44.0, _hz1 - _hz0)),
                             "why": "above the lips: the shell's band, seat and slide lip round the block (shell cuts "
                                    "front_block.clear_outline())"}
for k, (x, y, _) in enumerate(FB.FB_SCREWS_FULL):
    JOINTS[(f"fb-screw-{k + 1}", NAME)] = {"fit": fits.STEEL, "where": ((x, y, R.DECK_TOP + FB.PAD_T / 2),
                                                                         (5.0, 5.0, FB.PAD_T - 0.4)),
                                           "why": f"I8 screw {k + 1}'s shank in the pad's Ø3.3 hole"}
    JOINTS[(f"fb-screw-{k + 1}", "chassis")] = {"fit": fits.STEEL, "where": ((x, y, R.DECK_TOP - 1.0), (5.0, 5.0, 1.6)),
                                                "why": f"I8 screw {k + 1}'s shank in the deck's Ø3.3 hole"}
    JOINTS[(f"fb-nut-{k + 1}", "chassis")] = {"fit": fits.STEEL, "where": ((x, y, NUT_Z + K.NUT_T / 2), (8.0, 8.0, 1.6)),
                                              "why": f"I8 nut {k + 1} in its pocket (NUT_AF + 2 × STEEL)"}

_pl = FB.pads(FB.BV.carcass()[4])[0]
_seg = _pl.intersection(__import__("shapely.geometry", fromlist=["LineString"]).LineString([(20.0, -45.0), (20.0, -20.0)]))
_pad_d = _seg.length

# ---- marks, labels, print, measure ----------------------------------------------------------------------------------
MARKS.update({f: "the leg's own L/R label (legs design); the fork fits its pocket either way up" for f in FORKS})
MARKS["chassis"] = ("FRONT arrow (tip to -Y) sunk 0.5 in the seat at the front left, beside the front block (x 26.2, y -41.5, placed by shell_marks()); the fork number (1-4 dots, front to rear) beside each "
                    "upper swivel screw on the band top")
MARKS["crank-cover"] = ("FRONT arrow on its top face; it fits one way (the spigot and the shared screw's hole); the "
                        "switch fits its cradle one way (lever to the rear slot, pins to the front slot)")
MARKS[NAME] = ("none needed: it fits one way only (the pads' outlines in their lips and the face's curve); the eyes "
               "JST seat and the slack box show its left side")
LABELS = {"es": {**LABELS["es"], "chassis": "carcasa base (chasis de vista)",
                 **{f"i7-screw-{k + 1}": f"tornillo I7 {k + 1}" for k in range(4)},
                 "crank-cover": "tapa de los cigüeñales", "motor-leads": "cables del motor",
                 "switch": "interruptor",
                 **{f"cover-screw-{k + 1}": f"tornillo de la tapa de los cigüeñales {k + 1}" for k in range(2)},
                 **{f"cover-nut-{k + 1}": f"tuerca de la tapa de los cigüeñales {k + 1}" for k in range(2)},
                 **{f"i7-nut-{k + 1}": f"tuerca I7 {k + 1}" for k in range(4)},
                 **{f: f"horquilla {f[5:]}" for f in FORKS},
                 **{f"{f}-screw-low": f"tornillo inferior de la horquilla {f[5:]}" for f in FORKS},
                 **{f"{f}-screw-up": f"tornillo superior de la horquilla {f[5:]}" for f in FORKS},
                 **{f"{f}-nut-low": f"tuerca inferior de la horquilla {f[5:]}" for f in FORKS},
                 **{f"{f}-nut-up": f"tuerca superior de la horquilla {f[5:]}" for f in FORKS},
                 NAME: "bloque frontal v2",
                 **{f"fb-screw-{k + 1}": f"tornillo del bloque frontal {k + 1}" for k in range(2)},
                 **{f"fb-nut-{k + 1}": f"tuerca del bloque frontal {k + 1}" for k in range(2)}}}
PRINT_ORIENT["chassis"] = FLIP          # band top (slide lip) on the bed (plan A1b)
PRINT_ORIENT["crank-cover"] = FLIP     # top face (sunk arrow) on the bed, the rear lip standing up: no support (upright
                                         # it printed its whole plate over the bed). The lip (1.2 × 8.5, 7.6 tall) closes the
                                         # module path's slot in the band's rear wall: nothing pushes on it (the WARN on it)
PRINT_ORIENT[NAME] = np.eye(4)      # base (the pads) on the bed, as built
MEASURE += [
    {"part": "chassis", "what": "crank window width across X", "nominal": round(2 * SHL.CRANK_HALF, 2),
     "tol": (0.0, 0.3), "points": "at crank 2's slot, deck edge to deck edge"},
    {"part": "chassis", "what": "slide lip height over the seat", "nominal": SHL.LIP_H, "tol": (-0.2, 0.2),
     "points": "either side, at y 0"},
    {"part": "chassis", "what": "fork pocket height (boss top to band underside)",
     "nominal": round(FORK_TOP - FORK_BOT + 2 * GAP, 2), "tol": (0.0, 0.3), "points": "any fork pocket, at the screw"},
    {"part": "chassis", "what": "cover post spigot diameter", "nominal": SHL.SPIGOT_D, "tol": (-0.1, 0.05),
     "points": "the front-left post"},
    {"part": "crank-cover", "what": "spigot hole diameter", "nominal": fits.bore(SHL.SPIGOT_D, fits.LOCATOR),
     "tol": (-0.05, 0.15), "points": "front-left hole"},
    {"part": NAME, "what": "left pad's depth along Y at x 20 (its rear block)", "nominal": round(_pad_d, 2),
     "tol": (-0.1, 0.1), "points": "front face to rear face of the pad, 1 mm above the bed"},
    {"part": NAME, "what": "JST seat across X", "nominal": round(FB.SEAT[2] - FB.SEAT[0], 2), "tol": (0.0, 0.2),
     "points": "the seat at the slack box's bottom"},
    {"part": NAME, "what": "access tube bore", "nominal": SHL.CBORE, "tol": (-0.1, 0.3), "points": "either tube, at the top"},
    {"part": NAME, "what": "hook tongue height at its tip", "nominal": FB.TONGUE_TIP, "tol": (-0.1, 0.1),
     "points": "either tongue, outer edge"},
    {"part": NAME, "what": "hook tongue reach from the side face", "nominal": FB.TONGUE_OUT, "tol": (-0.1, 0.1),
     "points": "either tongue, top face"},
    {"part": NAME, "what": "boss thickness under the head", "nominal": FB.PAD_T, "tol": (-0.1, 0.1),
     "points": "depth gauge down the access tube, from the bed face"}]
SECTIONS += [([FB.FB_SCREWS[0][0], 0, 0], [1, 0, 0]), ([33.7, 0, 0], [1, 0, 0]), ([0, -51.0, 0], [0, 1, 0]),
             ([0, -31.0, 0], [0, 1, 0])]


# =====================================================================================================================
# Part B2: body-v2, holder-cradle, body-lug, and the 6 screws + 6 nuts that hold them (design-plan-b.md «B2 state»)
# =====================================================================================================================
import body_v2 as BD  # noqa: E402  (every number of the three parts and their hardware places: one source)

BODY, CRADLE, LUG, ETAB = "body-v2", "holder-cradle", "body-lug", "eyes-tab"
for _n in (BODY, CRADLE, LUG, ETAB):
    PARTS[_n] = {"stl": f"out/{_n}.stl"}
_PL = BD.screw_places()
_Z = [0, 0, 1]
# cradle: M3×10 up through the block's floor, the ear and the roof into the nut above the roof (nut slid in from the
# block's inboard face)
for _k, (_x, _y, _z) in enumerate(_PL["cradle"]):
    PARTS[f"cradle-screw-{_k + 1}"] = {"mesh": m3([_x, _y, _z], _Z, BD.CR_SCREW_L), "hardware": True, "fixed": True,
                                       "label": "M3×10 Allen"}
    PARTS[f"cradle-nut-{_k + 1}"] = {"mesh": nut([_x, _y, BD.NUTP_Z0 + 0.15], _Z), "hardware": True, "fixed": True,
                                     "label": "tuerca M3"}
# eyes board: M3×10 whose head is the board's bottom tab, nut in the boss (slid in from -X)
_ex, _ey, _ez = _PL["eyes"]
PARTS["eyes-screw"] = {"mesh": m3([_ex, _ey, _ez], _Z, BD.EB_SCREW_L), "hardware": True, "fixed": True,
                       "label": "M3×10 Allen"}
PARTS["eyes-nut"] = {"mesh": nut([_ex, _ey, BD.EB_SCREW_Z + BD.EB_SCREW_L - BD.NUT_H - 0.5 + 0.15], _Z),
                     "hardware": True, "fixed": True, "label": "tuerca M3"}
# lug: 2 × M3×10 from below into nuts in the root block; the M3×8 from below (at the shell's screw place) into the
# lug's own nut
for _k, (_x, _y, _z) in enumerate(_PL["lug"]):
    PARTS[f"lug-screw-{_k + 1}"] = {"mesh": m3([_x, _y, _z], _Z, BD.LUG_SCREW_L), "hardware": True, "fixed": True,
                                    "label": "M3×10 Allen"}
    PARTS[f"lug-nut-{_k + 1}"] = {"mesh": nut([_x, _y, BD.ROOT_NUT_Z0 + 0.15], _Z), "hardware": True, "fixed": True,
                                  "label": "tuerca M3"}
PARTS["rear-screw"] = {"mesh": m3([BD.SX, BD.SY, R.DECK_TOP - 1.8], _Z, 8.0), "hardware": True, "fixed": True,
                       "label": "M3×8 Allen"}
PARTS["rear-nut"] = {"mesh": nut([BD.SX, BD.SY, BD.NUT_Z[0] + 0.15], _Z), "hardware": True, "fixed": True,
                     "label": "tuerca M3"}
for _n in (BODY, CRADLE, LUG, ETAB):
    PARTS[_n]["fixed"] = False

# ---- retention: what holds each part ------------------------------------------------------------------------------
RETAIN[BODY] = {"play": 0.5}       # slide lip (X), tongues in the L-slots (-Y, +Z), the M3×8 (+Y), band top (-Z)
RETAIN[LUG] = {"play": 0.5}        # 2 screws up into the root block's nuts, the notch's walls 1.0 either side
RETAIN[CRADLE] = {"play": 1.0}     # the ears in the grooves (WINDOW 0.5 above and below = 1.0 of travel), the screws
RETAIN["holder"] = {"play": 1.0}   # WINDOW 0.5 each side in the tray = 1.0 of travel; the snap lips under, the frame over
RETAIN["eyes-board"] = {"play": 1.0, "tilt": 5.0}   # pocket WINDOW 0.5 a side; the printed tab 0.5 under its left edge
RETAIN[ETAB] = {"play": 0.5}       # the screw's head under it pulls it up against the boss, the slot's walls WINDOW round it

# ---- gaps and contacts ----------------------------------------------------------------------------------------------
_HW_BODY = [f"cradle-screw-{k + 1}" for k in range(2)] + ["eyes-screw"] + [f"lug-screw-{k + 1}" for k in range(2)]
for _s, _n in [(f"cradle-screw-{k + 1}", f"cradle-nut-{k + 1}") for k in range(2)] + [("eyes-screw", "eyes-nut"),
                                                                                      ("rear-screw", "rear-nut")] + \
        [(f"lug-screw-{k + 1}", f"lug-nut-{k + 1}") for k in range(2)]:
    ALLOWED_CONTACT[(_s, _n)] = "screw in its nut"
    PAIR_GAP[(_n, BODY)] = 0.1                        # nut in its pocket (+0.15 a side)
    PAIR_GAP[(_n, LUG)] = 0.1
    PAIR_GAP[(_s, BODY)] = 0.1                        # M3 in Ø3.3 (STEEL 0.15)
PAIR_GAP[("rear-screw", LUG)] = 0.1
for _f in ("fork-4L", "fork-4R"):
    PAIR_GAP[(BODY, f"{_f}-screw-up")] = 0.1       # head top 0.2 under the band top (shell: counterbore), the scan's
                                                   # seat 0.09 into the band top: 0.11 between them, both given
PAIR_GAP[("rear-screw", "chassis")] = 0.1
PAIR_GAP[("rear-nut", "chassis")] = 0.1
for _k in range(2):
    PAIR_GAP[(f"cradle-screw-{_k + 1}", CRADLE)] = 0.1
    PAIR_GAP[(f"lug-screw-{_k + 1}", LUG)] = 0.1
    ALLOWED_CONTACT[(f"cradle-screw-{_k + 1}", BODY)] = "head clamps the block's floor"
    ALLOWED_CONTACT[(f"lug-screw-{_k + 1}", LUG)] = "head clamps the lug's rear part"
    ALLOWED_CONTACT[(f"lug-nut-{_k + 1}", BODY)] = "nut pulled down onto its pocket in the root block"
    ALLOWED_CONTACT[(f"cradle-nut-{_k + 1}", BODY)] = "nut pulled down onto its pocket over the groove's roof"
ALLOWED_CONTACT[("eyes-screw", BODY)] = "shank through the boss's hole"
ALLOWED_CONTACT[("eyes-screw", ETAB)] = "head clamps the tab up against the boss, shank through its hole"
ALLOWED_CONTACT[(ETAB, BODY)] = "the tab pulled up against the boss's underside"
PAIR_GAP[("eyes-screw", ETAB)] = 0.1
PAIR_GAP[(ETAB, BODY)] = 0.1
ALLOWED_CONTACT[("eyes-nut", BODY)] = "nut pulled down onto its pocket in the boss"
ALLOWED_CONTACT[("rear-screw", "chassis")] = "head clamps the floor shelf from below, shank through its hole"
ALLOWED_CONTACT[("rear-screw", LUG)] = "shank through the lug and its ring, tip in the nut"
ALLOWED_CONTACT[("rear-nut", LUG)] = "nut pulled down onto its pocket in the lug"
ALLOWED_CONTACT[(LUG, "chassis")] = "the lug's Ø7 × 0.5 ring bears on the floor shelf, clamped by the M3×8"
ALLOWED_CONTACT[(LUG, BODY)] = "the lug's rear part against the root block's underside (2 screws pull it up)"
ALLOWED_CONTACT[(BODY, "chassis")] = "the body's seat rests on the band top (flat at z BAND_TOP, rear segment relieved 0.3: it bears at " \
    "the sides and front) and slides on it for the last 4 mm: a designed sliding contact; the path check counts only " \
    "overlap above the one at the place"

# ---- assembly: on the bench first (body on its own), then the body with everything in it goes on the shell ------------
# plan B «Assembly order» steps 14-16: nuts slid into the body, lug screwed on, cradle with its holder slid into the
# grooves and screwed, eyes board into its pocket and held by its screw head; then the whole body lowered 30 mm behind
# its place, slid 4 mm forward (-Y: tongues to the L-slot ends), and the M3×8 from below with the robot on its back.
BODY_GROUP = (BODY, LUG, "rear-nut", "lug-screw-1", "lug-screw-2", "lug-nut-1", "lug-nut-2", CRADLE, "holder",
              "cradle-screw-1", "cradle-screw-2", "cradle-nut-1", "cradle-nut-2", "eyes-board", "eyes-screw", "eyes-nut", ETAB)
_bb = [BODY]


def _bench(names, d, note="", **kw):
    """One bench step on the body with what is already on it; it joins the bench afterwards."""
    ent = (names, d, {"bench": list(_bb), "note": note, **kw})
    _bb.extend([names] if isinstance(names, str) else list(names))
    return ent


_SL = BD.CRADLE_SLIDE
ASSEMBLY += [
    _bench("lug-nut-1", [-1, 0, 0], "M3 nut slid into the root block's left pocket from -X (the lug is not on yet)"),
    _bench("lug-nut-2", [1, 0, 0], "the same, right pocket, from +X"),
    ((LUG, "rear-nut"), [0, 0, -1], {"bench": list(_bb), "note": "the lug with the M3×8's nut already in it (slid in "
                                     "from -X on its own, step before) raised against the root block's underside"}),
]
_bb.extend([LUG, "rear-nut"])
ASSEMBLY += [
    _bench("lug-screw-1", [0, 0, -1], "M3×10 from below through the lug into the root block's nut"),
    _bench("lug-screw-2", [0, 0, -1], "the same, right"),
    _bench("cradle-nut-1", [[-20, 0, 0]], "nut slid into the left groove block from its inboard face (+X), before the "
                                       "cradle: the cradle's wall then closes the slot"),
    _bench("cradle-nut-2", [[20, 0, 0]], "the same, right block, from -X"),
    _bench("eyes-nut", [-1, 0, 0], "nut slid into the eyes boss from -X"),
    ("holder", [0, 0, -1], {"bench": [CRADLE], "except": {CRADLE: "snap lips under the case's long edges flex 1.0 "
                                                                   "(wall 1.2 × 18: ε 0.56 %)"},
                            "note": "holder pushed up from below into the tray until the lips snap under its edges"}),
]
_bb.append("holder-cradle-pending")
_bb.pop()
ASSEMBLY += [
    ((CRADLE, "holder"), [[0, 0, 30], [0, _SL, 0]], {"bench": list(_bb), "note": "the cradle with its holder up from "
     "below into the grooves' entry notches 11.5 mm forward of their place, then slid back 11.5 mm to the end stops"}),
]
_bb.extend([CRADLE, "holder"])
ASSEMBLY += [
    _bench("cradle-screw-1", [0, 0, -1], "M3×10 up through the floor, the ear and the roof into the nut"),
    _bench("cradle-screw-2", [0, 0, -1], "the same, right"),
    _bench("eyes-board", [0, 0, -1], "the board up into its pocket from below, its right edge first"),
    _bench(ETAB, [0, 0, -1], "the printed tab up into its slot under the boss, its end towards the pocket"),
    _bench("eyes-screw", [0, 0, -1], "M3×10 up through the tab and the boss into the nut: the tab's end clamps the "
                                     "board's left bottom edge"),
    (BODY_GROUP, [[0, 0, -30], [0, -BD.SLIDE, 0]], {"note": "step 16: the body with the holder, eyes board, lug and "
     "all its screws lowered 30 mm behind its place (tongues at the L-slots' entries, the lug into its notch), slid "
     "4 mm forward"}),
    ("rear-screw", [0, 0, -1], {"note": "robot on its back: M3×8 up through the shelf and the lug's ring into the "
                                       "nut, hand tight"}),
]

_bt = trimesh.load(os.path.join(HERE, "out", f"{BODY}.stl")).bounds[1][2]
ACCESS += [
    {"at": "lug-nut-1", "tool": tool("pliers", [BD.LUG_X[0] - 8.0, BD.LUG_SCREW_Y, BD.ROOT_NUT_Z0 + K.NUT_T / 2],
                                      [-1, 0, 0], reach=20.0), "why": "on the bench: nut pushed along its slot from -X, pliers"},
    {"at": "lug-nut-2", "tool": tool("pliers", [BD.LUG_X[1] + 8.0, BD.LUG_SCREW_Y, BD.ROOT_NUT_Z0 + K.NUT_T / 2],
                                      [1, 0, 0], reach=20.0), "why": "on the bench: nut pushed along its slot from +X, pliers"},
    {"at": (LUG, "rear-nut"), "tool": tool("finger", [BD.SX, BD.SY, BD.LUG_Z0 - 0.5], [0, 0, -1], d=12.0, reach=30.0),
     "why": "on the bench: the lug (nut in it) pushed up by hand against the root block"},
    *[{"at": f"lug-screw-{k + 1}", "tool": tool("hex-key", [x, y, z - K.HEAD_H], [0, 0, -1]),
       "why": "on the bench: M3×10 from below, 2.5 hex key"} for k, (x, y, z) in enumerate(_PL["lug"])],
    *[{"at": f"cradle-nut-{k + 1}", "tool": tool("pliers", [x + (1 if k == 0 else -1) * 8.0, y,
                                                            BD.NUTP_Z0 + K.NUT_T / 2], [1 if k == 0 else -1, 0, 0], reach=25.0),
       "why": "on the bench: nut pushed along its slot from the block's inboard face, pliers"}
      for k, (x, y, z) in enumerate(_PL["cradle"])],
    {"at": "eyes-nut", "tool": tool("pliers", [BD.EB_BOSS[0] - 8.0, _ey, BD.EB_SCREW_Z + BD.EB_SCREW_L - BD.NUT_H +
                                                K.NUT_T / 2 - 0.5], [-1, 0, 0]),
     "why": "on the bench: nut pushed along its slot from -X, pliers"},
    {"at": "holder", "tool": tool("finger", [CX, BD.HC[1], BD.H0[2]], [0, 0, -1], d=16.0, reach=30.0),
     "why": "on the bench: the holder pushed up into the tray by the thumbs (the middle of its bottom is open)"},
    {"at": (CRADLE, "holder"), "tool": tool("finger", [CX, BD.HC[1], BD.CR_Z0], [0, 0, -1], d=16.0, reach=30.0),
     "why": "on the bench: the cradle with its holder lifted by hand from below"},
    *[{"at": f"cradle-screw-{k + 1}", "tool": tool("hex-key", [x, y, z - K.HEAD_H], [0, 0, -1]),
       "why": "on the bench: M3×10 from below, 2.5 hex key"} for k, (x, y, z) in enumerate(_PL["cradle"])],
    {"at": "eyes-board", "tool": tool("finger", [CX, _ey, BD.E0[2]], [0, 0, -1], d=8.0, reach=30.0),
     "why": "on the bench: the board pushed up into its pocket from below by the fingertips"},
    {"at": ETAB, "tool": tool("finger", [BD.EB_SCREW[0], _ey, BD.EB_SCREW_Z], [0, 0, -1], d=8.0, reach=30.0),
     "why": "on the bench: the tab pushed up into its slot by a fingertip"},
    {"at": "eyes-screw", "tool": tool("hex-key", [_ex, _ey, _ez - K.HEAD_H], [0, 0, -1]),
     "why": "on the bench: M3×10 from below, 2.5 hex key"},
    {"at": BODY_GROUP, "tool": tool("finger", [CX, 0.0, _bt], [0, 0, 1], d=30.0, reach=40.0),
     "why": "the whole body held by the hands over it and lowered onto the shell"},
    {"at": "rear-screw", "tool": tool("hex-key", [BD.SX, BD.SY, R.DECK_TOP - 1.8 - K.HEAD_H], [0, 0, -1]),
     "why": "robot on its back: M3×8 from below, 2.5 hex key"},
]

# ---- joints (fits from fits.py; boxes in the robot frame) ----------------------------------------------------------
_pz = (BD.POST_Z[0] + BD.POST_Z[1]) / 2
for _sg, _side, _key in ((-1, BD.SIDE_L, (BODY, NAME)), (1, BD.SIDE_R, (NAME, BODY))):
    _c = _side + _sg * (BD.HOOK_X + BD.FB.TONGUE_OUT) / 2
    JOINTS[_key] = {"fit": fits.WINDOW, "where": ((_c, (BD.T_Y0 + BD.T_Y1) / 2, (BD.T_Z0 + BD.T_Z1) / 2),
                                                   (BD.HOOK_X + BD.FB.TONGUE_OUT + 0.4, BD.T_Y1 - BD.T_Y0 + 2 * BD.WIN
                                                    - 0.1, BD.T_Z1 - BD.T_Z0 + 2 * BD.WIN - 0.1)),
                    "why": f"I9: the {'left' if _sg < 0 else 'right'} hook tongue in the post's L-slot, WINDOW in Y "
                           "and Z (1.2 a side in X)"}
JOINTS[(CRADLE, BODY)] = {"fit": fits.WINDOW, "where": ((BD.CR_X0 - BD.EAR_OUT / 2, BD.EAR_Y[0] + 4.0, (BD.GROOVE_Z[0] +
                                                         BD.GROOVE_Z[1]) / 2),
                                                        (BD.EAR_OUT + 2.0, 8.0, BD.GROOVE_Z[1] - BD.GROOVE_Z[0] - 0.2)),
                          "why": "I10: the left ear in its groove, WINDOW up, down and at its tip"}
JOINTS[("holder", CRADLE)] = {"fit": fits.WINDOW, "where": ((CX, BD.HC[1], BD.HC[2] + 2.0), (BD.HX + 2.0, BD.HY + 2.0,
                                                           BD.HZ - 2.0)),
                              "why": "I10: the holder in its tray: WINDOW all round (the lips are 0.5 under it)"}
JOINTS[("eyes-board", BODY)] = {"fit": fits.WINDOW, "where": ((CX, (BD.E0[1] + BD.E1[1]) / 2, BD.E1[2] - 4.0),
                                                              (BD.E1[0] - BD.E0[0] + 2.0, BD.E1[1] - BD.E0[1] + 2.0,
                                                               8.0)),
                                "why": "I11: the board in its pocket, WINDOW a side; its top and sides"}
JOINTS[(ETAB, BODY)] = {"fit": fits.WINDOW, "where": ((BD.P0[0] - 0.6, _ey + BD.TAB_W / 2 + BD.WIN / 2, BD.EB_SCREW_Z + 1.0),
                                                      (1.0, 1.0, 1.6)),
                        "why": "I11: the printed tab in its slot under the boss, WINDOW round it"}
JOINTS[(LUG, "chassis")] = {"fit": fits.WINDOW, "where": ((SHL.NOTCH[0] + 0.5, 38.0, (BD.LUG_Z0 + BD.LUG_TOP) / 2),
                                                         (1.6, 5.0, 2.0)),
                            "why": "I9: the tab in the shell's notch, the -X wall (1.0 off; the +X side is open to the "
                                   "cover's slot)"}
for _k, (_x, _y, _z) in enumerate(_PL["cradle"]):
    JOINTS[(f"cradle-screw-{_k + 1}", BODY)] = {"fit": fits.STEEL, "where": ((_x, _y, BD.BLK_Z0 + 1.0), (5.0, 5.0, 1.8)),
                                                "why": "I10: the screw's shank in the block's Ø3.3 hole"}
    JOINTS[(f"cradle-screw-{_k + 1}", CRADLE)] = {"fit": fits.STEEL, "where": ((_x, _y, (BD.EAR_Z[0] + BD.EAR_Z[1]) / 2),
                                                                              (5.0, 5.0, 2.0)),
                                                  "why": "I10: the screw's shank in the ear's Ø3.3 hole"}
JOINTS[("eyes-screw", BODY)] = {"fit": fits.STEEL, "where": ((_ex, _ey, BD.EB_HEAD_TOP + 3.0), (5.0, 5.0, 4.0)),
                                "why": "I11: the screw's shank in the boss's Ø3.3 hole"}
for _k, (_x, _y, _z) in enumerate(_PL["lug"]):
    JOINTS[(f"lug-screw-{_k + 1}", LUG)] = {"fit": fits.STEEL, "where": ((_x, _y, BD.LUG_REAR_Z0 + 2.5), (5.0, 5.0, 3.0)),
                                            "why": "I9: lug screw's shank in the lug's Ø3.3 hole"}
JOINTS[("rear-screw", "chassis")] = {"fit": fits.STEEL, "where": ((BD.SX, BD.SY, R.DECK_TOP - 0.5), (5.0, 5.0, 1.0)),
                                     "why": "I9: the M3×8's shank in the shelf's Ø3.3 hole"}
JOINTS[("rear-screw", LUG)] = {"fit": fits.STEEL, "where": ((BD.SX, BD.SY, BD.LUG_Z0 + 1.0), (5.0, 5.0, 2.0)),
                               "why": "I9: the M3×8's shank in the lug's Ø3.3 hole"}

# ---- marks, labels, print, measure, sections -----------------------------------------------------------------------
MARKS[BODY] = ("it fits one way (the hook posts, the lug and the eyes pocket are all asymmetric to a turned body); "
               "the slide's direction is arrowed by the posts' L-slots; no marking printed")
MARKS[CRADLE] = ("«insert here» arrows NOT modelled: they are marked by hand with a pen on the cradle's ears (2 "
                 "arrows, each over a groove block's entry notch, tips +Y); the holder fits one way (the +Y end wall; "
                 "the crossbar at -Y), the ears fit their grooves one way")
MARKS[ETAB] = "none needed: it fits one way (the hole at its outboard end, the long end towards the pocket)"
MARKS[LUG] = "none needed: it fits one way (the nut slot opens on -X, the ring on the bottom, the rear part on +Y)"
LABELS["es"].update({BODY: "cuerpo v2", CRADLE: "cuna del portapilas", LUG: "pestaña trasera del cuerpo",
                     **{f"cradle-screw-{k + 1}": f"tornillo de la cuna {k + 1}" for k in range(2)},
                     **{f"cradle-nut-{k + 1}": f"tuerca de la cuna {k + 1}" for k in range(2)},
                     "eyes-screw": "tornillo de la placa de los ojos", ETAB: "arandela-pestaña de la placa de los ojos", "eyes-nut": "tuerca de la placa de los ojos",
                     **{f"lug-screw-{k + 1}": f"tornillo de la pestaña {k + 1}" for k in range(2)},
                     **{f"lug-nut-{k + 1}": f"tuerca de la pestaña {k + 1}" for k in range(2)},
                     "rear-screw": "tornillo trasero M3×8 (cuerpo al chasis)", "rear-nut": "tuerca del tornillo trasero"})
# print: the body upright on the skirt's lip (as built), 1 wall loop + gyroid 10 % (85.5 g bare, S1), «more loops»
# modifier boxes round every screw and hook (read by the plater; cad_verify does not use them)
PRINT_ORIENT[BODY] = np.eye(4)
PRINT_ORIENT[CRADLE] = np.eye(4)        # its floor lips on the bed: top frame up (the lips are 1.2 thick, flat)
PRINT_ORIENT[ETAB] = np.eye(4)           # flat on the bed
PRINT_ORIENT[LUG] = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])   # on its -X face (the nut slot's walls print as perimeters)
PRINT_SETTINGS = {BODY: {"wall_loops": 1, "infill": "gyroid 10 %", "top_shell_thickness": "see plater",
                         "modifiers": {n: {"box": (tuple(map(float, a)), tuple(map(float, b))), "wall_loops": 3,
                                           "infill": "gyroid 40 %"} for n, (a, b) in BD.FEATURE_BOXES.items()},
                         "why": "grams from the slicer (85.5 g bare, 93.2 g with the features); more loops where "
                                "a screw or a hook loads the wall"}}
MEASURE += [
    {"part": BODY, "what": "hook post slot width across Z", "nominal": round(BD.SLOT_Z[1] - BD.SLOT_Z[0], 2),
     "tol": (-0.1, 0.2), "points": "either post, in the horizontal leg"},
    {"part": BODY, "what": "eyes pocket width across X", "nominal": round(BD.P1[0] - BD.P0[0], 2), "tol": (-0.1, 0.3),
     "points": "caliper at the pocket's mouth, board's width + 2 WINDOW"},
    {"part": BODY, "what": "cradle groove height (Z)", "nominal": round(BD.GROOVE_Z[1] - BD.GROOVE_Z[0], 2),
     "tol": (-0.1, 0.3), "points": "either groove, at its end stop"},
    {"part": CRADLE, "what": "tray inside width across X", "nominal": round(BD.HX + 2 * BD.CR_IN, 2), "tol": (-0.1, 0.3),
     "points": "between the walls, mid-height"},
    {"part": CRADLE, "what": "ear thickness", "nominal": round(BD.EAR_Z[1] - BD.EAR_Z[0], 2), "tol": (-0.1, 0.1),
     "points": "either ear"},
    {"part": LUG, "what": "nut pocket across the flats", "nominal": round(BD.NUT_AF, 2), "tol": (-0.1, 0.2),
     "points": "the M3×8's pocket, from the open slot's side"},
]
SECTIONS += [([BD._PL_X, 0, 0], [1, 0, 0]) if False else ([_PL["cradle"][0][0], 0, 0], [1, 0, 0]),
             ([BD.SX, 0, 0], [1, 0, 0]), ([0, BD.LUG_SCREW_Y, 0], [0, 1, 0]), ([0, _ey, 0], [0, 1, 0])]
