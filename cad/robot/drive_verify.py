"""cad_verify spec of the drive (drive.py), merged into verify.py by interior_verify.py: spine, 4 cranks, 3 idlers and
the transfer on M3 shanks (plan B, no sleeves), journal-cap, motor-u, transfer-cheek (plan A, all flat, no support),
pinion, the N10 (hardware, its datasheet box) and the M3 screws. Poses: crank pose t of 24 (cad/motion.py POSES, the
pins' angle falls 15 deg a pose), every gear turned by its ratio."""
import math
import numpy as np
import trimesh
from cad import fits
from cad_verify import rod, tool
import drive as D

CRANKS = [f"crank-{i+1}" for i in range(4)]; IDLERS = [f"idler-{i+1}" for i in range(3)]
DRV = ["journal-cap", "motor-u", "transfer-cheek"]
PRINTED = ["spine"] + CRANKS + IDLERS + ["transfer"] + DRV + ["pinion"]


def m3(length, p_head, axis, button=False):
    """M3 socket cap (ISO 4762, head Ø5.5 x 3) or button head (ISO 7380, Ø5.7 x 1.65) at p_head (its bearing face), shank along axis."""
    a = np.asarray(axis, float); p = np.asarray(p_head, float)
    hr, hh = (D.BTN_R, D.BTN_H) if button else (D.M3_HEAD_R, D.M3_HEAD_H)
    return trimesh.util.concatenate([rod(2 * D.IPR, length, p, a), rod(2 * hr, hh, p - a * hh, a)])


def motor():
    my, mz = D.MC
    b = trimesh.creation.box(extents=[D.N10_L, D.N10_W, D.N10_H]); b.apply_translation([(D.MX0 + D.MX1) / 2, my, mz])
    return trimesh.util.concatenate([b, rod(2 * D.SHAFT_R, D.SHAFT_X1 - D.MX1, [D.MX1, my, mz], [1, 0, 0])])


XH = D.LUG_X0                                       # idler axle button heads on the lugs's -x face
SCREWS = {"axle-1": (10, [XH, *D.I[0]], [1, 0, 0]), "axle-2": (10, [XH, *D.I[1]], [1, 0, 0]),
          "axle-3": (10, [XH, *D.I[2]], [1, 0, 0]), "transfer-pin": (16, [D.TP_X, *D.T], [1, 0, 0]),
          "strap-screw": (10, [D.STRAP_X, D.STRAP_Y, D.ZS1], [0, 0, -1]),
          **{f"keel-{k+1}": (L, [x, y, zh], [0, 0, 1]) for k, (x, y, zh, L) in enumerate(D.KEEL_SCREWS)}}
PARTS = {**{n: {"stl": f"out/{n}.stl"} for n in PRINTED},
         "n10-motor": {"mesh": motor(), "hardware": True, "label": "motor N10 3 V (caja metálica, eje D Ø3)",
                       "label_en": "N10 motor 3 V (metal gearbox, D shaft Ø3)"}}
BUTTON = ("axle-1", "axle-2", "axle-3", "transfer-pin")      # ISO 7380 button heads, 2 mm hex key
for n, (L, p, a) in SCREWS.items():
    b = n in BUTTON
    PARTS[n] = {"mesh": m3(L, p, a, b), "hardware": True, "label": f"M3×{L:g} cabeza botón (ISO 7380)" if b else f"M3×{L:g} Allen",
                "label_en": f"M3×{L:g} button head (ISO 7380)" if b else f"M3×{L:g} socket head"}


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
_SCREW_IN = "self-tapping M3 in its pilot Ø2.5 (plan m3-screws, assumed, coupon c2)"
ALLOWED_CONTACT = {
    ("journal-cap", "spine"): "rails on the wall tops (plan cap-on-spine)",
    ("motor-u", "spine"): "web and lugs 1, 2 on the -x wall's outer face (plan motor-u-on-spine)",
    ("motor-u", "journal-cap"): "ledge, boss and ear 2 on the cap top; web on the cap rail's -x face (plan motor-u-on-spine)",
    ("transfer-cheek", "motor-u"): "strap on the U wall tops and the -y ear (plan cheek-on-u)",
    ("n10-motor", "motor-u"): "in its U at MOTOR_SEAT 0.2 (the JOINTS row checks the fit)",
    ("pinion", "n10-motor"): "pressed on the D-shaft (fits.DSHAFT 0, assumed: coupon of 3 bores with the motor)",
    ("spine", "base"): "keel foot on the bowl floor (plan spine-on-keel)",
    **{(f"axle-{k+1}", "spine"): "M3 thread in the -x wall's pilot Ø2.5, tip in the +x wall's STEEL hole (plan B)" for k in range(3)},
    **{(f"axle-{k+1}", "motor-u"): "head on the motor-u lug (plan motor-u-on-spine)" for k in range(2)},
    ("axle-3", "journal-cap"): "head on the cap's lug 3 (plan cap-on-spine)",
    ("transfer-pin", "motor-u"): "head on the web's -x face, " + _SCREW_IN + " (web + boss, 4 mm)",
    ("strap-screw", "transfer-cheek"): "head on the strap", ("strap-screw", "motor-u"): _SCREW_IN + " (the -y ear)",
    **{(f"keel-{k+1}", "spine"): "keel M3 from below, " + _SCREW_IN for k in range(2)},
    **{(f"keel-{k+1}", "base"): "head in its counterbored boss on the bowl floor" for k in range(2)},
}
PAIR_GAP = {**{(i, f"axle-{k+1}"): fits.STEEL.side - 0.01 for k, i in enumerate(IDLERS)},      # designed gaps below MIN_GAP: STEEL on the shank
            ("transfer", "transfer-pin"): fits.STEEL.side - 0.01}
SPIN = {"spin": [1, 0, 0], "slide": None, "play": 0.6}
RETAIN = {"spine": {"spin": None, "slide": None, "play": 0.3},                      # 2 keel M3 into the base
          **{n: dict(SPIN) for n in CRANKS},                                         # slots, webs, cap tongues 1-4 (F)
          **{n: dict(SPIN, tilt=8.0) for n in IDLERS + ["transfer"]},               # STEEL on the shank + THRUST_IDLER faces
          **{n: {"spin": None, "slide": None, "play": 0.3} for n in DRV},           # cap: lug 3 + tongues; motor-u: axles 1, 2 + ledge; cheek: strap screw + pin pocket
          "pinion": {"spin": [1, 0, 0], "slide": [1, 0, 0], "play": 0.3},            # along x: the press on the D-shaft
          "n10-motor": {"spin": None, "slide": [1, 0, 0], "play": 0.3},              # along x: the strap's press (no end stop: the pinion's tip covers the gearbox face)
          **{n: {"spin": SCREWS[n][2], "slide": SCREWS[n][2], "play": 0.3} for n in SCREWS}}   # along its axis: its thread in the pilot
JOINTS = {**{(c, "spine"): {"fit": fits.TURN, "why": "journal in its open-top slot (plan crank-in-spine)"} for c in CRANKS},
          **{(c, "journal-cap"): {"fit": fits.TURN, "why": "cap tongue over the journal, 1-4 (plan crank-in-spine, F)"} for c in CRANKS},
          **{(i, f"axle-{k+1}"): {"fit": fits.STEEL, "why": "idler on its M3 shank (plan idler-on-shank)"} for k, i in enumerate(IDLERS)},
          **{(i, "spine"): {"fit": fits.GEAR_THRUST_IDLER, "why": "idler faces to the walls"} for i in IDLERS},
          ("transfer", "transfer-pin"): {"fit": fits.STEEL, "why": "transfer on its M3 x 16 (plan transfer-on-pin)"},
          ("transfer", "journal-cap"): {"fit": fits.GEAR_TIP, "why": "notch and hub cut round the tips (GEAR_TIP); small gear 0.45 off the rails (THRUST_IDLER)"},
          ("transfer", "motor-u"): {"fit": fits.GEAR_THRUST_IDLER, "why": "small gear's -x face to the pin boss"},
          ("transfer", "transfer-cheek"): {"fit": fits.GEAR_AXIAL, "why": "big gear's +x face to the cheek (plan transfer-on-pin)"},
          ("n10-motor", "motor-u"): {"fit": fits.MOTOR_SEAT, "why": "N10 in its U (plan motor-in-u)"}}
def _st(n, e):                                      # entry e with its assembly step number (opts "step")
    return (e[0], e[1], {**(e[2] if len(e) > 2 else {}), "step": n})
SET = ["spine"] + CRANKS + IDLERS + ["journal-cap", "axle-3", "transfer", "motor-u", "axle-1", "axle-2", "transfer-pin"]
_A = [
    *[_st(3, (c, [0, 0, 1], {"bench": ["spine"], "note": "spine set on the bench: crank down into its slots, pose 0 marks"})) for c in CRANKS],
    *[_st(4, (i, [0, 0, 1], {"bench": ["spine"] + CRANKS, "note": "idler meshes both cranks, held at its hole"})) for i in IDLERS],
    _st(5, ("journal-cap", [0, 0, 1], {"bench": SET[:8], "note": "rails flat on the wall tops, 8 tongues in slots 1-4"})),
    _st(6, ("axle-3", [-1, 0, 0], {"bench": SET[:9], "except": {"spine": _SCREW_IN + " (-x wall)"}})),
    _st(7, ("transfer", [0, 0, 1], {"bench": SET[:10], "note": "before the motor-u (its U floor is over the transfer): small gear into the cap notch, meshes idler 2"})),
    _st(8, ("motor-u", [0, 0, 1], {"bench": SET[:11], "note": "ledge on the cap, lugs over idler holes 1, 2, boss beside the transfer"})),
    *[_st(9, (f"axle-{k+1}", [-1, 0, 0], {"bench": SET[:12], "except": {"spine": _SCREW_IN + " (-x wall)"}})) for k in range(2)],
    _st(10, ("transfer-pin", [-1, 0, 0], {"bench": SET[:14], "except": {"motor-u": _SCREW_IN + " (boss)"}, "note": "through the web hole, the boss and the transfer: it turns free"})),
    _st(11, (tuple(SET), [[0, -1, -30], [0, 1, 0]], {"note": "spine set onto the keel bosses, lowered 1 mm toward the front of the base (crank 4's +x web and gear tip clear the base's rear top lip, 0.4 mm), then slid 1 mm back onto its bosses; crank 4 held by the cap (F)"})),
    *[_st(12, (f"keel-{k+1}", [0, 0, -1], {"except": {"spine": _SCREW_IN}})) for k in range(2)],
    _st(15, ("pinion", [1, 0, 0], {"bench": ["n10-motor"], "note": "pressed on the D-shaft to its stop, flat to the D"})),
    _st(16, (("n10-motor", "pinion"), [0, 0, 1], {"note": "drops into the U, the pinion meshes the big transfer gear"})),
    _st(17, ("transfer-cheek", [0, 0, 1], {"note": "lowered: cheek beyond the big gear and the pin tip, strap on the U and the -y ear"})),
    _st(18, ("strap-screw", [0, 0, 1], {"except": {"motor-u": _SCREW_IN + " (-y ear)"}})),
]
ASSEMBLY = _A
_key = lambda n: np.asarray(SCREWS[n][1]) - np.asarray(SCREWS[n][2]) * (D.BTN_H if n in BUTTON else D.M3_HEAD_H)
ACCESS = [*[{"at": n, "tool": tool("hex-key", _key(n), [-1, 0, 0]), "why": "2 mm hex key from -x (ISO 7380 button head)"}
            for n in ("axle-1", "axle-2", "axle-3", "transfer-pin")],
          {"at": "strap-screw", "tool": tool("hex-key", _key("strap-screw"), [0, 0, 1]), "why": "2.5 mm hex key from above"},
          *[{"at": f"keel-{k+1}", "tool": tool("hex-key", [0, y, zh - D.M3_HEAD_H], [0, 0, -1]), "why": "2.5 mm hex key from below, base on its flank"}
            for k, (_x, y, zh, _L) in enumerate(D.KEEL_SCREWS)],
          {"at": "journal-cap", "tool": tool("finger", [0, D.Oy[3], D.CAP_Z1], [0, 0, 1], d=10.0), "why": "pressed down by hand on the plate"},
          {"at": "motor-u", "tool": tool("finger", [D.LUG_X0 + 1, D.I[1][0], D.UZ1], [0, 0, 1], d=6.0), "why": "pressed down by hand on the U's -x end"},
          {"at": "transfer-cheek", "tool": tool("finger", [D.XO + 1, -12.0, D.ZS1], [0, 0, 1], d=6.0), "why": "pressed down by hand on the strap"},
          {"at": tuple(SET), "tool": tool("finger", [0, D.Oy[3], D.CAP_Z1], [0, 0, 1], d=10.0), "why": "set onto the keel seat by hand, pressed on the cap"},
          {"at": ("n10-motor", "pinion"), "tool": tool("finger", [D.MX0 + 3, D.MC[0], D.MC[1] + D.N10_H / 2], [0, 0, 1], d=10.0), "why": "pressed down into the U by hand"}]
_X2Z = np.array([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1.0]])   # robot +x up (about y)
_MX2Z = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1.0]])  # robot -x up
PRINT_ORIENT = {"spine": np.eye(4), **{n: _X2Z for n in CRANKS + IDLERS + ["transfer", "pinion"]},
                "journal-cap": np.diag([1.0, -1.0, -1.0, 1.0]),               # top face on the bed (180 deg about x): rails, tongues, lug 3 rise
                "motor-u": _X2Z,                                              # -x face on the bed, the U rises along +x
                "transfer-cheek": _MX2Z}                                      # +x face on the bed, the strap rises along -x
MARKS = {**{c: f"number {i+1} engraved (≈ 3 mm high, 0.5 deep) on the +x web hub (which crank, which end right); its gear is printed at its phase: set at crank pose 0" for i, c in enumerate(CRANKS)},
         **{n: "any tooth: the cranks' phases are printed in their gears, the idler meshes as it drops in at pose 0" for n in IDLERS},
         "transfer": "any tooth (meshes idler 2 and the pinion as it goes in)", "pinion": "any tooth",
         "journal-cap": "one way: lug 3 on the -x side over idler hole 3, 8 tongues in the 4 slots",
         "motor-u": "one way: lugs over idler holes 1, 2 on the -x wall, U over the cap",
         "transfer-cheek": "one way: cheek on the +x side of the big gear, strap over the U"}
MINIMUMS = {"parts": PRINTED, "module": 1.0, "wall": 2.0, "mark": 3.0}   # Morante 2026-11-26 (datasheet): module 1.0, walls 2.0, numbers ≈ 3 high
_GX = lambda n, x, c, z: {"part": n, "origin": [x, *c], "axis": [1, 0, 0], "width": D.GW, "teeth": z}
_I2 = (D.I[1][0] + 0.02, D.I[1][1])               # idler 2: the reader's polar bin at -y holds no edge of its root arc from the exact centre; 0.02 off it reads 10 teeth
GEAR_GEOM = [*[_GX(c, 0.0, D.CENTRE[c], D.ZT) for c in CRANKS], *[_GX(n, 0.0, _I2 if i == 1 else D.I[i], D.ZI[i]) for i, n in enumerate(IDLERS)],
             _GX("transfer", 0.0, D.T, D.ZS), _GX("transfer", D.XB0 + D.GW / 2, D.T, D.ZB), _GX("pinion", D.XB0 + D.GW / 2, D.MC, D.ZP)]
def _mark(i):                                       # crank i's engraved number as built (drive.mark_cutter), as a mesh in the part's frame
    import tempfile, os
    from build123d import export_stl
    o = D.CENTRE[CRANKS[i]]; cut = D.mark_cutter(i)
    hub = D.cylx(o[0], o[1], D.WEBR, D.WB0, D.WB1)          # the web hub before the engraving: the cutter must remove material from it
    assert (hub & cut).volume > 0.5, f"{CRANKS[i]}: the number's cutter removes no material from the +x web hub"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "mark.stl"); export_stl(cut, p, tolerance=0.01, angular_tolerance=0.2)
        return trimesh.load(p, force="mesh")
MARK_GEOM = {**{c: _mark(i) for i, c in enumerate(CRANKS)}, **{n: None for n in IDLERS + ["transfer", "pinion"]}}
LABELS = {"es": {"spine": "espina", **{c: f"cigüeñal {i+1}" for i, c in enumerate(CRANKS)},
                 **{n: f"engranaje loco {i+1}" for i, n in enumerate(IDLERS)}, "transfer": "engranaje doble", "journal-cap": "tapa de los ejes", "motor-u": "soporte U del motor",
                 "transfer-cheek": "mejilla y brida del motor",
                 "pinion": "piñón", "n10-motor": "motor N10", **{n: f"tornillo M3×{SCREWS[n][0]} ({n})" for n in SCREWS}}}
_A = D.A_ALL[0, 0]
MEASURE = [{"what": "crank pin Ø3", "point": [8.0, float(_A[1]), float(_A[2])], "normal": [1, 0, 0],
            "from": [8.0, float(_A[1]) - D.PINR, float(_A[2])], "to": [8.0, float(_A[1]) + D.PINR, float(_A[2])], "nominal": 2 * D.PINR, "tol": 0.1, "tool": "caliper"},
           {"what": "journal slot width", "point": [D.WX1, D.Oy[0], D.YTOP - 1], "normal": [1, 0, 0],
            "from": [D.WX1, D.Oy[0] - D.SLW, D.YTOP - 1], "to": [D.WX1, D.Oy[0] + D.SLW, D.YTOP - 1], "nominal": 2 * D.SLW, "tol": 0.1, "tool": "caliper"}]
