"""cad_verify spec of the drive (drive.py), merged into verify.py by interior_verify.py: spine, 4 cranks, 3 idlers and
the transfer on their sleeves, drive unit, pinion, the N10 (hardware, its datasheet box) and the M2 screws. Poses:
crank pose t of 24 (cad/motion.py POSES, the pins' angle falls 15 deg a pose), every gear turned by its ratio.
GEARS / PAIR_GAP are defined here too: verify.py does not merge them yet (coordinator: one line in interior_verify.py
and verify.py)."""
import math
import numpy as np
import trimesh
from cad import fits
from cad_verify import rod, tool
import drive as D

CRANKS = [f"crank-{i+1}" for i in range(4)]; IDLERS = [f"idler-{i+1}" for i in range(3)]
SLEEVES = [f"sleeve-{i+1}" for i in range(3)]
PRINTED = ["spine"] + CRANKS + IDLERS + SLEEVES + ["transfer", "transfer-sleeve", "drive-unit", "pinion"]


def m2(length, p_head, axis):
    """M2 socket cap (ISO 4762): head Ø3.8 x 2 at p_head (its bearing face), shank along axis."""
    a = np.asarray(axis, float); p = np.asarray(p_head, float)
    return trimesh.util.concatenate([rod(2 * D.IPR, length, p, a), rod(2 * D.M2_HEAD_R, D.M2_HEAD_H, p - a * D.M2_HEAD_H, a)])


def motor():
    my, mz = D.MC
    b = trimesh.creation.box(extents=[D.N10_L, D.N10_W, D.N10_H]); b.apply_translation([(D.MX0 + D.MX1) / 2, my, mz])
    return trimesh.util.concatenate([b, rod(2 * D.SHAFT_R, D.SHAFT_X1 - D.MX1, [D.MX1, my, mz], [1, 0, 0])])


XL = -D.WX1 - D.W                                   # lug / inner cheek outer face (-x): heads of axles 1, 2 and t
XH = XL + D.CB_DEPTH                                # heads of axles 1, 2 sunk into the lug's counterbore
SCREWS = {"axle-1": (6, [XH, *D.I[0]], [1, 0, 0]), "axle-2": (6, [XH, *D.I[1]], [1, 0, 0]),
          "axle-3": (5, [-D.WX1, *D.I[2]], [1, 0, 0]), "axle-t": (12, [XL, *D.T], [1, 0, 0]),
          **{f"keel-{k+1}": (L, [x, y, zh], [0, 0, 1]) for k, (x, y, zh, L) in enumerate(D.KEEL_SCREWS)}}
PARTS = {**{n: {"stl": f"out/{n}.stl"} for n in PRINTED},
         "n10-motor": {"mesh": motor(), "hardware": True, "label": "motor N10 3 V (caja metálica, eje D Ø3)",
                       "label_en": "N10 motor 3 V (metal gearbox, D shaft Ø3)"}}
for n, (L, p, a) in SCREWS.items():
    PARTS[n] = {"mesh": m2(L, p, a), "hardware": True, "label": f"M2×{L:g} Allen", "label_en": f"M2×{L:g} socket head"}


def _rx(a, c):
    """4x4: turn a (rad) about +x through (0, c[0], c[1])."""
    T = np.eye(4); ca, sa = math.cos(a), math.sin(a)
    T[1:3, 1:3] = [[ca, -sa], [sa, ca]]; T[1:3, 3] = np.array(c) - T[1:3, 1:3] @ np.array(c); return T


def poses_interior(t):
    a = D.crank_angle(int(t) % 24); out = {}
    for n in CRANKS + IDLERS: out[n] = _rx(D.RATIO[n] * a, D.CENTRE[n])
    out["transfer"] = _rx(D.RATIO["transfer"] * a, D.T); out["pinion"] = _rx(D.RATIO["pinion"] * a, D.MC)
    return out


GEARS = [(CRANKS[i], IDLERS[i]) for i in range(3)] + [(CRANKS[i + 1], IDLERS[i]) for i in range(3)] + \
        [(IDLERS[D.TI], "transfer"), ("transfer", "pinion")]
_SCREW_IN = "self-tapping M2 in its pilot Ø1.6 (plan m2-screws, assumed, coupon c2)"
ALLOWED_CONTACT = {
    **{(s, "spine"): "sleeve clamped wall to wall by its M2 axle (plan idlers)" for s in SLEEVES},
    ("transfer-sleeve", "drive-unit"): "sleeve clamped cheek to cheek by the transfer M2",
    ("drive-unit", "spine"): "cheeks on the wall tops, lugs on the -x wall (plan drive-on-spine)",
    ("n10-motor", "drive-unit"): "in its clamp at MOTOR_SEAT 0.2 (the JOINTS row checks the fit; MIN_GAP 0.2 sits on it)",
    ("pinion", "n10-motor"): "pressed on the D-shaft (fits.DSHAFT 0, assumed: coupon of 3 bores with the motor)",
    ("spine", "base"): "keel foot on the bowl floor (plan spine-on-keel)",
    **{(f"axle-{k+1}", f"sleeve-{k+1}"): _SCREW_IN for k in range(3)},
    **{(f"axle-{k+1}", "spine"): "M2 through the -x wall (STEEL), tip in the +x wall pilot" for k in range(3)},
    **{(f"axle-{k+1}", "drive-unit"): "head on the drive unit's lug (plan drive-on-spine)" for k in range(2)},
    ("axle-3", "spine"): "head on the -x wall, " + _SCREW_IN,
    ("axle-t", "transfer-sleeve"): _SCREW_IN, ("axle-t", "drive-unit"): "head on the inner cheek, tip in the +x cheek pilot",
    **{(f"keel-{k+1}", "spine"): "keel M2 from below, " + _SCREW_IN for k in range(2)},
    **{(f"keel-{k+1}", "base"): "head in its counterbored boss on the bowl floor (needs its STEEL hole in the base: shells.py)" for k in range(2)},
}
SPIN = {"spin": [1, 0, 0], "slide": None, "play": 0.6}
RETAIN = {"spine": {"spin": None, "slide": None, "play": 0.3},                      # 2 keel M2 into the base
          **{n: dict(SPIN) for n in CRANKS},                                         # slots, webs, cap tongues (4: holder post)
          **{n: dict(SPIN, tilt=8.0) for n in IDLERS + ["transfer"]},               # sleeve TURN + walls: THRUST_IDLER 0.45 on a 4.2 tip tilts 6 deg
          **{n: {"spin": [1, 0, 0], "slide": None, "play": 0.3} for n in SLEEVES + ["transfer-sleeve"]},
          "drive-unit": {"spin": None, "slide": None, "play": 0.3},                  # tongues in slots 1-3, lugs on idler axles 1, 2
          "pinion": {"spin": [1, 0, 0], "slide": [1, 0, 0], "play": 0.3},            # along x: the press on the D-shaft
          "n10-motor": {"spin": None, "slide": [1, 0, 0], "play": 0.3},              # along x: the clamp's press (MOTOR_SEAT)
          **{n: {"spin": SCREWS[n][2], "slide": SCREWS[n][2], "play": 0.3} for n in SCREWS}}   # along its axis: its thread in the pilot
JOINTS = {**{(c, "spine"): {"fit": fits.TURN, "why": "journal in its open-top slot (plan crank-in-spine)"} for c in CRANKS},
          **{(c, "drive-unit"): {"fit": fits.TURN, "why": "cap tongue over the journal (plan crank-in-spine)"} for c in CRANKS[:3]},
          **{(i, s): {"fit": fits.TURN, "why": "idler on its sleeve (plan idlers)"} for i, s in zip(IDLERS, SLEEVES)},
          **{(i, "spine"): {"fit": fits.GEAR_THRUST_IDLER, "why": "idler faces to the walls"} for i in IDLERS},
          ("transfer", "transfer-sleeve"): {"fit": fits.TURN, "why": "transfer on its sleeve"},
          ("n10-motor", "drive-unit"): {"fit": fits.MOTOR_SEAT, "why": "N10 in its clamp (plan motor-in-clamp)"}}
def _st(n, e):                                      # entry e with its plan.json assembly step number (opts "step")
    return (e[0], e[1], {**(e[2] if len(e) > 2 else {}), "step": n})
_A = [
    *[_st(3, (c, [0, 0, 1], {"bench": ["spine"], "note": "spine set on the bench: crank down into its slots, pose 0 marks"})) for c in CRANKS],
    *[_st(4, ((i, s), [0, 0, 1], {"bench": ["spine"] + CRANKS, "note": "idler with its sleeve, meshes both cranks"})) for i, s in zip(IDLERS, SLEEVES)],
    _st(5, (("transfer", "transfer-sleeve"), [0, 0, -1], {"bench": ["drive-unit"], "note": "drive unit upside down: compound and sleeve between its cheeks"})),
    _st(5, ("axle-t", [-1, 0, 0], {"bench": ["drive-unit", "transfer", "transfer-sleeve"], "except": {"transfer-sleeve": _SCREW_IN, "drive-unit": _SCREW_IN}})),
    _st(5, (("drive-unit", "transfer", "transfer-sleeve", "axle-t"), [0, 0, 1], {"bench": ["spine"] + CRANKS + IDLERS + SLEEVES,
                                                                       "note": "tongues in slots 1-3, lugs flat on the -x wall"})),
    *[_st(6, (f"axle-{k+1}", [-1, 0, 0], {"bench": ["spine", "drive-unit"] + CRANKS + IDLERS + SLEEVES,
                                   "except": {f"sleeve-{k+1}": _SCREW_IN, "spine": "tip into the +x wall pilot"}})) for k in range(3)],
    _st(7, (tuple(["spine"] + CRANKS + IDLERS + SLEEVES + ["drive-unit", "transfer", "transfer-sleeve", "axle-t", "axle-1", "axle-2", "axle-3"]),
     [0, 0, 1], {"note": "spine set onto the keel seat; crank 4 held by a rubber band until the holder caps it"})),
    *[_st(8, (f"keel-{k+1}", [0, 0, -1], {"except": {"spine": _SCREW_IN}})) for k in range(2)],
    _st(11, ("pinion", [1, 0, 0], {"bench": ["n10-motor"], "note": "pressed on the D-shaft to its stop, flat to the D"})),
    _st(12, (("n10-motor", "pinion"), [[38.0, 0, 0]], {"note": "after the cell holder: slid in along +x, pinion in the plates' grooves, meshes"})),
]
ASSEMBLY = _A
ACCESS = [*[{"at": n, "tool": tool("hex-key", np.asarray(SCREWS[n][1]) - [D.M2_HEAD_H, 0, 0], [-1, 0, 0]), "why": "1.5 mm hex key from -x"}
            for n in ("axle-1", "axle-2", "axle-3", "axle-t")],
          *[{"at": f"keel-{k+1}", "tool": tool("hex-key", [0, y, zh - D.M2_HEAD_H], [0, 0, -1]), "why": "1.5 mm hex key from below, base on its flank"}
            for k, (_x, y, zh, _L) in enumerate(D.KEEL_SCREWS)],
          {"at": ("drive-unit", "transfer", "transfer-sleeve", "axle-t"), "tool": tool("finger", [0, D.HOLDER_SCREW["y"], D.HOLDER_SCREW["ear_top_z"]], [0, 0, 1], d=10.0),
           "why": "set down by hand on ear 2: tongues into slots 1-3"},
          {"at": tuple(["spine"] + CRANKS + IDLERS + SLEEVES + ["drive-unit", "transfer", "transfer-sleeve", "axle-t", "axle-1", "axle-2", "axle-3"]),
           "tool": tool("finger", [0, D.HOLDER_SCREW["y"], D.HOLDER_SCREW["ear_top_z"]], [0, 0, 1], d=10.0), "why": "set onto the keel seat by hand, pressed on ear 2"},
          {"at": ("n10-motor", "pinion"), "tool": tool("finger", [D.MX0, D.MC[0], D.MC[1]], [-1, 0, 0], d=10.0), "why": "pushed in along +x by hand"}]
_X2Z = np.array([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1.0]])   # axis x onto z (about y)
PRINT_ORIENT = {"spine": np.eye(4), **{n: _X2Z for n in CRANKS + IDLERS + SLEEVES + ["transfer", "transfer-sleeve", "pinion"]},
                "drive-unit": np.diag([1.0, -1.0, -1.0, 1.0])}                   # ear faces down
MARKS = {**{c: f"{i+1} dots on the +x web hub (which crank, which end right); its gear is printed at its phase: set at crank pose 0" for i, c in enumerate(CRANKS)},
         **{n: "any tooth: the cranks' phases are printed in their gears, the idler meshes as it drops in at pose 0" for n in IDLERS},
         "transfer": "any tooth (meshes idler 2 and the pinion as it goes in)", "pinion": "any tooth"}
LABELS = {"es": {"spine": "espina", **{c: f"cigüeñal {i+1}" for i, c in enumerate(CRANKS)},
                 **{n: f"engranaje loco {i+1}" for i, n in enumerate(IDLERS)}, **{n: f"casquillo {i+1}" for i, n in enumerate(SLEEVES)},
                 "transfer": "engranaje doble", "transfer-sleeve": "casquillo del doble", "drive-unit": "soporte del motor",
                 "pinion": "piñón", "n10-motor": "motor N10", **{n: f"tornillo M2×{SCREWS[n][0]} ({n})" for n in SCREWS}}}
_A = D.A_ALL[0, 0]
MEASURE = [{"what": "crank pin Ø3", "point": [8.0, float(_A[1]), float(_A[2])], "normal": [1, 0, 0],
            "from": [8.0, float(_A[1]) - D.PINR, float(_A[2])], "to": [8.0, float(_A[1]) + D.PINR, float(_A[2])], "nominal": 2 * D.PINR, "tol": 0.1, "tool": "caliper"},
           {"what": "journal slot width", "point": [D.WX1, D.Oy[0], D.YTOP - 1], "normal": [1, 0, 0],
            "from": [D.WX1, D.Oy[0] - D.SLW, D.YTOP - 1], "to": [D.WX1, D.Oy[0] + D.SLW, D.YTOP - 1], "nominal": 2 * D.SLW, "tol": 0.1, "tool": "caliper"}]
