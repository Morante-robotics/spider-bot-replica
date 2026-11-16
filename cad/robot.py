"""Spider-Bot robot master model: the datums, the carcass envelope, the interfaces between designs and the envelopes
of the bought parts. Every design imports it, so a number shared by two designs has one home.

    sys.path.insert(0, ROOT); from cad import robot as R
    R.MOTOR_AXIS, R.DECK_TOP, R.INTERFACES["I6"], R.n20_body()

Frame and names as ../cad/README.md and common.py: mm, Z up, forward = -Y, +X = the robot's right; the body axis is
sim.CENTER. Numbers that come from another design are imported from it, not copied. Bought parts are not bought yet
(chassis plan, decision 9): their sizes are catalogue values, flagged in CATALOGUE, and are replaced by caliper
readings (measurements.csv) when the parts arrive.

    python3 cad/robot.py        # prints the datums, the interface table and the catalogue values
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from cad import common as K, design, fits  # noqa: E402

C = design("crankshafts")          # shafts, idlers, gears, spine walls

# ---- datums ------------------------------------------------------------------------------------------------------
CX, CY = (float(v) for v in K.sim.CENTER)     # body axis (x, y)
GROUND_Z = 15.6            # ground under the feet (sim/motor-sizing-result.txt «ground z 15.6»)
PIVOT_Z = float(K.sim.NOTCH_Z)                 # leg pivots, 72.0
DECK_BOT, DECK_TOP = 72.8, 74.8                # deck of the chassis (base v1 DECK_BOT, SEAM: ../base/build.py)
LIFT = 18.7                # the body is raised by the band (base v1 LIFT)
BAND_TOP = DECK_TOP + LIFT # body seat, 93.5
SHAFTS = [(float(y), float(z)) for y, z in C.shaft_yz()]           # crankshaft axes (y, z), along X at CX
IDLERS = [(float(y), float(z), n) for y, z, n in C.idlers()]       # idler axes (y, z, teeth)
GEAR_PLANE = C.WALL_IN     # |x - CX| of the crank gears' room between the walls (1.75)

# ---- carcass envelope (carcass at 120 %, ../carcass-120) ----------------------------------------------------------
CARCASS = os.path.join(HERE, "carcass-120")
CARCASS_FILES = {"base": "spideybot_base.stl", "body": "spideybot_body.stl", "eye": "spideybot_eye.stl"}
CARCASS_BOUNDS = {"base": ((-18.0, -62.23, 45.6), (103.44, 44.0, 108.0))}   # from the STL, for quick checks


def carcass(name="base", lifted=False):
    """Carcass mesh (trimesh); lifted=True moves the body up by LIFT, as it sits on the band."""
    import trimesh
    m = trimesh.load(os.path.join(CARCASS, CARCASS_FILES[name]))
    if lifted:
        m.apply_translation([0, 0, LIFT])
    return m


# The scanned carcass is for the looks parts and figures. Every computation (cuts, KEEP_IN, probes, gaps) uses the proxy
# or the envelope below: the body's scan is 102k triangles and every boolean or gap against it costs minutes.
PROXY_TOL = 0.2            # mm: every proxy vertex within this of the scan (measured: body 102k -> 31k faces, max 0.23)


def carcass_proxy(name="base", lifted=False, tol=PROXY_TOL):
    """The carcass decimated by manifold within tol (a closed solid), cached in carcass-120/.proxy/ by the STL's hash:
    the mesh every check and cut uses instead of carcass()."""
    import hashlib
    import trimesh
    from manifold3d import Manifold, Mesh
    src = os.path.join(CARCASS, CARCASS_FILES[name])
    with open(src, "rb") as f:
        key = hashlib.sha1(f.read()).hexdigest()[:12]
    cache = os.path.join(CARCASS, ".proxy", f"{name}-{tol}-{key}.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        m = trimesh.Trimesh(z["v"], z["f"], process=False)
    else:
        s = trimesh.load(src)
        r = Manifold(Mesh(vert_properties=np.asarray(s.vertices, np.float32),
                          tri_verts=np.asarray(s.faces, np.uint32))).simplify(tol).to_mesh()
        m = trimesh.Trimesh(np.asarray(r.vert_properties[:, :3], float), np.asarray(r.tri_verts), process=False)
        # no merge_vertices(): manifold's output is closed as it is; trimesh's merge pinches it into 170 pieces
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.savez(cache, v=m.vertices, f=m.faces)
    if lifted:
        m.apply_translation([0, 0, LIFT])
    return m


def carcass_envelope(name="base", lifted=False, dz=2.0):
    """The carcass as a stack of boxes, one per dz slab (each the slab's section bounds): an outer bound for coarse
    checks (does it fit at all, which slab is tight) in milliseconds. Returns [(z0, z1, (x0, y0), (x1, y1))]."""
    m = carcass_proxy(name, lifted)
    z0, z1 = m.bounds[:, 2]
    out = []
    for z in np.arange(z0, z1, dz):
        h = min(dz, z1 - z)
        sec = m.section(plane_origin=[0, 0, z + h / 2], plane_normal=[0, 0, 1])
        if sec is not None:
            (x0, y0, _), (x1, y1, _) = sec.bounds
            out.append((float(z), float(z + h), (float(x0), float(y0)), (float(x1), float(y1))))
    return out


# ---- bought parts: catalogue values until bought and measured -----------------------------------------------------
# N20: Pololu Micro Metal Gearmotor HP 6 V 380:1 (#4794), hardware.md
N20_W, N20_H = 10.0, 12.0  # gearbox and can section: 10 across the flats (Y) × 12 round (Z)
N20_GEARBOX_L = 9.0        # gearbox length
N20_CAN_L = 17.0           # motor can with its end cap
N20_TERM_L = 5.7           # terminals and solder behind the can (to x CX+35, the plan's envelope)
N20_TERM_W, N20_TERM_Z = 6.0, (-2.0, 4.0)      # terminal block across Y, and its z range from the axis
N20_SHAFT_D, N20_SHAFT_FLAT, N20_SHAFT_L = 3.0, 0.5, 9.0   # D-shaft: Ø3, flat 0.5 deep, 9 long from the gearbox face
N20_MASS = 10.0            # g
HOLDER = (49.0, 64.0, 16.0)            # 4×AAA holder x, y, z (long side along Y), ≤ 64 × 49 × 16
HOLDER_CENTRE = (CX, 11.0, 106.5)      # on the body (plan: holder in the body)
SWITCH = (12.0, 6.0, 6.0)              # SS12D00 body, lever extra 4 mm
EYES_BOX = ((18.0, -55.0, 117.0), (68.0, -45.0, 139.0))   # eyes board pocket in the head
EYES_BOARD = (50.0, 22.0, 10.0)        # perfboard + 2 LEDs + 2 resistors, fits the pocket
CATALOGUE = {"N20_W": N20_W, "N20_H": N20_H, "N20_GEARBOX_L": N20_GEARBOX_L, "N20_CAN_L": N20_CAN_L,
             "N20_TERM_L": N20_TERM_L, "N20_TERM_W": N20_TERM_W, "N20_TERM_Z": N20_TERM_Z,
             "N20_SHAFT_D": N20_SHAFT_D, "N20_SHAFT_FLAT": N20_SHAFT_FLAT, "N20_SHAFT_L": N20_SHAFT_L,
             "N20_MASS": N20_MASS, "HOLDER": HOLDER, "SWITCH": SWITCH, "EYES_BOARD": EYES_BOARD}

# ---- the motor at M1: pinion on idler 3, axis along +X -------------------------------------------------------------
PINION_TEETH = 12
PINION_FACE = 4.0          # clutch pinion (design-plan-clutch.md, Morante 2026-11-16: 4 mm; was 5 = idler 3's face)
IDLER3_FACE = 5.0
PINION_X0 = -IDLER3_FACE / 2   # pinion's -X face, x from CX: flush with idler 3's -X face (-2.5); +X face at +1.5
CLUTCH_SHOULDER = 1.0      # clutch sleeve's shoulder between the pinion's +X face and the 0.8 gauge (x +1.5..+2.5)
MOTOR_CD_EXTRA = 0.1       # motor axis 0.1 further from idler 3 than C.CD_EXTRA: covers the slip bore's 0.1 a side
_Y3, _Z3, _N3 = IDLERS[2]  # (backlash worst +0.054, design-plan-clutch.md rev 2 item 4; Morante 2026-11-16)
MOTOR_AXIS = (CX, _Y3, _Z3 + C.MOD * (PINION_TEETH + _N3) / 2 + C.CD_EXTRA + MOTOR_CD_EXTRA)   # (CX, 12.18, 72.14)
PINION_TIP_R = C.MOD * (PINION_TEETH / 2 + 1)
# gearbox face: pinion's +X face + the sleeve's shoulder + the 0.8 gauge (3.3, unchanged by the clutch)
GEARBOX_X = CX + PINION_X0 + PINION_FACE + CLUTCH_SHOULDER + fits.GEAR_AXIAL.side
MOTOR_ENVELOPE = ((GEARBOX_X, _Y3 - N20_W / 2, MOTOR_AXIS[2] - N20_H / 2),
                  (GEARBOX_X + N20_GEARBOX_L + N20_CAN_L + N20_TERM_L, _Y3 + N20_W / 2, MOTOR_AXIS[2] + N20_H / 2))


def _box(lo, hi):
    import trimesh
    return trimesh.creation.box(bounds=[lo, hi])


def n20_body():
    """N20 gearbox, can and terminals in place (trimesh, robot frame), without the shaft (n20_shaft())."""
    import trimesh
    x0, y, z = GEARBOX_X, MOTOR_AXIS[1], MOTOR_AXIS[2]
    x1 = x0 + N20_GEARBOX_L
    x2 = x1 + N20_CAN_L
    gb = _box((x0, y - N20_W / 2, z - N20_H / 2), (x1, y + N20_W / 2, z + N20_H / 2))
    can = trimesh.creation.cylinder(radius=N20_H / 2, height=N20_CAN_L, sections=64)
    can.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    can.apply_translation([(x1 + x2) / 2, y, z])
    can = trimesh.boolean.intersection([can, _box((x1, y - N20_W / 2, z - 7), (x2, y + N20_W / 2, z + 7))],
                                       engine="manifold")
    term = _box((x2, y - N20_TERM_W / 2, z + N20_TERM_Z[0]), (x2 + N20_TERM_L, y + N20_TERM_W / 2, z + N20_TERM_Z[1]))
    return trimesh.boolean.union([gb, can, term], engine="manifold")


def d_profile(d=N20_SHAFT_D, flat=N20_SHAFT_FLAT, n=48):
    """D outline (u, v) round the origin, the flat at v = d/2 - flat."""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.column_stack([d / 2 * np.cos(a), d / 2 * np.sin(a)])
    pts[:, 1] = np.minimum(pts[:, 1], d / 2 - flat)
    keep = [0] + [i for i in range(1, n) if np.linalg.norm(pts[i] - pts[i - 1]) > 1e-6]
    return pts[keep]


def n20_shaft():
    """The D-shaft in place at angle 0 (flat towards +Z), from the gearbox face along -X (trimesh)."""
    import trimesh
    from shapely.geometry import Polygon
    m = trimesh.creation.extrude_polygon(Polygon(d_profile()), N20_SHAFT_L)
    # local: (u, v) in XY, length along +Z  ->  robot: u -> Y, v -> Z, length -> -X from the gearbox face
    M = np.eye(4)
    M[:3, :3] = np.column_stack([[0, 1, 0], [0, 0, 1], [-1, 0, 0]])
    M[:3, 3] = [GEARBOX_X, MOTOR_AXIS[1], MOTOR_AXIS[2]]
    m.apply_transform(M)
    return m


def holder():
    c = np.array(HOLDER_CENTRE)
    return _box(c - np.array(HOLDER) / 2, c + np.array(HOLDER) / 2)


def eyes_board():
    lo, hi = np.array(EYES_BOX[0]), np.array(EYES_BOX[1])
    c = (lo + hi) / 2
    s = np.array([EYES_BOARD[0], EYES_BOARD[2], EYES_BOARD[1]])     # 50 along X, 10 deep (Y), 22 tall (Z)
    return _box(c - s / 2, c + s / 2)


# ---- centre of mass targets (mass_estimate.py, plan rev 4) --------------------------------------------------------
COM_FINAL = (43.1, -1.1, 93.9)        # absolute; from the body axis x +0.4, y +2.5
COM_BOX = 5.0                          # ± mm about the body axis
V0_BALLAST = {"mass": 125.4, "com": (42.5, -2.6, 127.4)}

# ---- interfaces between designs (plan «Robot master model: interface table») --------------------------------------
INTERFACES = {
    "I1": {"between": ("crankshafts", "drive-module"), "fits": ("TURN", "GEAR_THRUST_CRANK"), "hardware": None},
    "I2": {"between": ("idlers", "drive-module"), "fits": ("STEEL", "GEAR_THRUST_IDLER"),
           "hardware": "3 × Ø3 pin 10, pin-keeper + M3×8"},
    "I3": {"between": ("crankshafts", "legs"), "fits": ("TURN",), "hardware": None},
    "I4": {"between": ("legs", "forks", "chassis"), "fits": ("STEEL", "WINDOW"), "hardware": "M3×16 pivots, M3×10"},
    "I5": {"between": ("cap", "drive-module"), "fits": ("LOCATOR", "TONGUE"), "hardware": "2 × M3×12 (one shared "
                                                                                        "with the clamp)"},
    "I6": {"between": ("N20", "clutch (sleeve, pinion, spring, shims, collar)", "drive-module", "idler-3-v2"),
           "fits": ("MOTOR_SEAT", "DSHAFT", "SLIP_BORE"), "gear_backlash": fits.GEAR_BACKLASH,
           "pinion_face": PINION_FACE, "motor_cd_extra": MOTOR_CD_EXTRA,
           "hardware": "motor-clamp, 2 × M3×12; wave washer DIN 137 B M3, shims DIN 988 3×6"},
    "I7": {"between": ("drive-module", "chassis"), "fits": ("WINDOW", "STEEL"),
           "hardware": "4 × M3 from below into the module's 4 nut traps (positions in chassis/build.py I7_NUTS, "
                       "lengths per nut: chassis README I7 table); deck lip WINDOW (88 mm outline)"},
    "I8": {"between": ("front-block", "chassis", "body"), "fits": ("LOCATOR", "WINDOW"), "hardware": "2 × M3×10"},
    "I9": {"between": ("body or ballast frame", "chassis"), "fits": ("WINDOW", "STEEL"),
           "hardware": "M3×12 from below"},
    "I10": {"between": ("holder", "cradle", "body"), "fits": ("WINDOW", "LOCATOR"), "hardware": "2 × M3×10"},
    "I11": {"between": ("eyes board", "body"), "fits": ("WINDOW",), "hardware": "1 screw"},
    "I12": {"between": ("wiring",), "fits": (), "hardware": "SS12D00, 2 × JST-XH, 60 mm slack"},
}
DATUMS = {"frame": "carcass 120 %, Z up, -Y forward, body axis sim.CENTER", "body_axis": (CX, CY),
          "ground_z": GROUND_Z, "pivot_z": PIVOT_Z, "deck": (DECK_BOT, DECK_TOP), "band_top": BAND_TOP,
          "gear_plane": GEAR_PLANE, "motor_axis": MOTOR_AXIS, "motor_envelope": MOTOR_ENVELOPE,
          "holder_box": (HOLDER, HOLDER_CENTRE), "eyes_box": EYES_BOX, "com_final": COM_FINAL, "com_box": COM_BOX,
          "body_lug_top_max": 81.2, "skirt_z": 81.9}


def report():
    out = ["datums:"] + [f"  {k:15s} {v}" for k, v in DATUMS.items()]
    out += ["interfaces:"] + [f"  {k:4s} {' ↔ '.join(v['between']):45s} {', '.join(v['fits']):28s} "
                              f"{v['hardware'] or ''}" for k, v in INTERFACES.items()]
    out += ["catalogue (to measure when bought):"] + [f"  {k:15s} {v}" for k, v in CATALOGUE.items()]
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
