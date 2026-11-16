"""Interim cad_verify spec for chassis Part B1 (the looks shell), while Part B is modelled.

Part A's spec (verify.py) with the shell `chassis` as the ground part:
- the drive module stands on the shell's 4 bosses, its top in the deck window, held by 4 stock M3 from below (I7);
- the 8 forks swivel on 2 M3×10 each, one up from below through the boss and one down from the band top (I4);
- the legs are swept every STEP degrees past everything (LEG_PATH): the lips' notches, the bump, the band, the rear
  screw column at CX-9, the front block nut bosses at y -51, the rear-left deck bridge.

The assembly follows the plan (design-plan-b.md «Assembly sequence»): the module is built on the bench (Part A's
steps, checked against the bench parts only), goes into the shell from above as one sub-assembly (no motor), then
the legs and forks, then the motor with its pinion, the clamp, and the I7 screws from below with the robot on its back.

It becomes verify.py, the whole-robot spec, in Part C (front block v2, body, cradle, frame). Until then Part A's
verify-result.txt stays the reference PASS for Part A.

    VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify_b1.py --quick --only chassis
    SHELL_LITE=1 VERIFY_STEP=30 …                 # the same on shell.py --lite's out/chassis-lite.stl
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import verify as A  # noqa: E402  (Part A's spec)
import shell as SH  # noqa: E402
from cad import common as K, design, fits, robot as R  # noqa: E402
from cad_verify import rod, tool  # noqa: E402

L = design("legs")
BV = SH.BV
CX = A.CX
STEP = A.STEP
MOTION = A.MOTION
GEAR_MOTION = A.GEAR_MOTION
GEARS = A.GEARS
GEAR_GAP = A.GEAR_GAP
MIN_GAP = getattr(A, "MIN_GAP", 0.2)
SECTIONS = A.SECTIONS + [([CX - 9.0, 0, 0], [1, 0, 0]),                      # rear screw, shelf, groove
                         ([CX, 0, 0], [1, 0, 0])]

# ---- parts --------------------------------------------------------------------------------------------------------
PARTS = {n: dict(p) for n, p in A.PARTS.items()}
LITE = os.environ.get("SHELL_LITE") == "1"                 # shell.py --lite's mesh, while trying a fix (never final)
PARTS["chassis"] = {"stl": "out/chassis-lite.stl" if LITE else "out/chassis.stl", "fixed": True}
if LITE:
    print("verify_b1: SHELL_LITE=1, checking out/chassis-lite.stl (decimated body, legs every 30°): not a final result")
PARTS["drive-module"]["fixed"] = False                     # it now stands on the shell (I7)

# I7: positions and stock lengths from shell.py (one source)
_base = R.carcass("base")
_mod = trimesh.load(os.path.join(HERE, "out", "drive-module.stl"))
I7 = SH.i7_bosses(_base, _mod)[2]
for k, r in enumerate(I7):
    p = [CX + r["x"], r["y"], r["head"]]
    PARTS[f"i7-screw-{k + 1}"] = {"mesh": A.m3(p, [0, 0, 1], r["length"]), "hardware": True, "fixed": True,
                                  "label": f"M3×{r['length']:g} Allen"}
    PARTS[f"i7-nut-{k + 1}"] = {"mesh": A.nut([CX + r["x"], r["y"], r["nut"][0] + 0.15], [0, 0, 1]),
                                "hardware": True, "fixed": True, "label": "tuerca M3"}

# I4: forks and their swivel screws (base v1's fork_mounts with the shell's gaps: shell.py sets FORK_GAP = LEG_PATH)
GAP = SH.FORK_GAP_Z                                # shell.py: the fork's faces up and down, a turning fit (TURN)
FORK_BOT, FORK_TOP = BV.FORK_BOT, BV.FORK_TOP
BOSS_TOP = FORK_BOT - GAP
BOSS_BOT = BOSS_TOP - (BV.SCREW_L - BV.SCREW_IN - GAP)
FORKS = {}
_U = {f"fork-{int(f['key'][0]) + 1}{f['key'][1]}": f["u"] for f in SH.fork_frames_cached()}   # nut slot directions


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
        PARTS[f"{name}-screw-low"] = {"mesh": A.m3([P[0], P[1], BOSS_BOT], [0, 0, 1], BV.SCREW_L), "hardware": True,
                                      "fixed": True, "label": "M3×10 Allen"}
        PARTS[f"{name}-screw-up"] = {"mesh": A.m3([P[0], P[1], R.BAND_TOP - BV.HEAD_H], [0, 0, -1], BV.SCREW_L),
                                     "hardware": True, "fixed": True, "label": "M3×10 Allen"}
        PARTS[f"{name}-nut-low"] = {"mesh": _turned(A.nut([P[0], P[1], (BOSS_BOT + BOSS_TOP) / 2 - BV.NUT_T / 2 + 0.15],
                                                          [0, 0, 1]), P[0], P[1], _U[name]),
                                    "hardware": True, "fixed": True, "label": "tuerca M3"}
        PARTS[f"{name}-nut-up"] = {"mesh": _turned(A.nut([P[0], P[1], FORK_TOP + GAP + 1.2 + 0.15], [0, 0, 1]),
                                                   P[0], P[1], _U[name]),
                                   "hardware": True, "fixed": True, "label": "tuerca M3"}
FORK_HW = [f"{f}-{s}" for f in FORKS for s in ("screw-low", "screw-up", "nut-low", "nut-up")]

# crank cover (Morante 2026-11-15, option b): on 3 posts, 2 × M3×10 from above into nuts in the posts
PARTS["crank-cover"] = {"stl": "out/crank-cover.stl"}
COVER_SCREWS = [(x, y, d) for x, y, kind, d in SH.COVER_POSTS if kind == "screw"]
for k, (x, y, d) in enumerate(COVER_SCREWS):
    top = SH.COVER_Z0 + SH.COVER_T
    PARTS[f"cover-screw-{k + 1}"] = {"mesh": A.m3([x, y, top], [0, 0, -1], SH.COVER_SCREW_L), "hardware": True,
                                     "fixed": True, "label": "M3×10 Allen"}
    _n = _turned(A.nut([x, y, SH.COVER_Z0 - 1.2 - BV.NUT_T + 0.15], [0, 0, 1]), x, y, d)
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
_SB = SH.SW_BODY
_ZL = (_SB[4] + _SB[5]) / 2
LEAD_PATH = [(_T, R.MOTOR_AXIS[1] + 4.0, _LZ0), (_T, SH.LEAD_Y, _LZ0), (_T, SH.LEAD_Y, SH.LEAD_Z),   # up the terminals
             ((_SB[0] + _SB[2]) / 2 - 0.3, SH.LEAD_Y, SH.LEAD_Z),        # through clip 1 (shell) and the cover's eye
             ((_SB[0] + _SB[2]) / 2 - 0.3, SH.LEAD_Y, _ZL),               # down in front of the cradle's front wall
             ((_SB[0] + _SB[2]) / 2 - 0.3, SH.LEAD_Y + 0.9, _ZL)]        # into the pins' slot (soldered to them)
# the switch on the crank cover (coordinator 2026-11-16, option b), its stop screw and nut
PARTS["switch"] = {"mesh": SH.switch_mesh(), "hardware": True, "label": "interruptor SS12D00 (medidas de catálogo)"}
PARTS["motor-leads"] = {"mesh": _tube(LEAD_PATH, SH.LEAD_D), "hardware": True, "fixed": True,
                        "label": "cables del motor (2 × 26 AWG) por sus pinzas hasta el interruptor"}
LEGS = A.LEGS


def poses(t):
    out = A.poses(t)
    lp = {n: M for n, _, M in L.poses(np.radians(t[0]))}
    for name, n in FORKS.items():
        out[name] = lp[n]
    return out


# ---- gaps and contacts ----------------------------------------------------------------------------------------------
PAIR_GAP = dict(A.PAIR_GAP)
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
for leg in A.LEGS:
    PAIR_GAP[(leg, "crank-cover")] = fits.LEG_PATH.side
for leg in A.LEGS:
    PAIR_GAP[(leg, "motor-leads")] = fits.LEG_PATH.side
for k in range(4):
    PAIR_GAP[(f"i7-screw-{k + 1}", "chassis")] = 0.1
    PAIR_GAP[(f"i7-screw-{k + 1}", "drive-module")] = 0.1
    PAIR_GAP[(f"i7-nut-{k + 1}", "drive-module")] = 0.1

ALLOWED_CONTACT = dict(A.ALLOWED_CONTACT)
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

KEEP_OUT = dict(A.KEEP_OUT)
# wires (I12): never under the crank cover (the crank webs and the window), never on the module's top or the motor
_cw = SH.CRANK_WIN
KEEP_OUT["wires-crank-window"] = {
    "part": "chassis", "mesh": trimesh.creation.box(bounds=[(_cw[0], _cw[1], 57.0), (_cw[2], _cw[3], SH.COVER_Z0)]),
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
# the carcass keep-in was Part A's stand-in for the shell: it applies to Part A's static parts, not the shell itself
_static = [n for n, p in A.PARTS.items() if not p.get("bench") and not n.startswith(("crankshaft", "idler-1",
                                                                                      "idler-2", "leg-"))]
KEEP_IN = {k: {**v, "parts": [n for n in _static if n not in ("idler-3-v2", "pinion", "n20-shaft")]}
           for k, v in A.KEEP_IN.items()}

# ---- retention -------------------------------------------------------------------------------------------------------
RETAIN = dict(A.RETAIN)
RETAIN["drive-module"] = {"play": 0.5}
RETAIN["crank-cover"] = {"play": 0.5}
RETAIN["switch"] = {"play": 0.9, "tilt": 11.0}   # WINDOW 0.5 a side round its catalogue size (plan: redrawn once
                       # measured): 0.87 along a box diagonal, and a 6 × 6 section rocks 10.6° in 7 × 7 about its long
                       # axis (the lever moves ±0.5 in its 3 mm window). Once measured the cradle goes to LOCATOR          # cradle walls, floor and top pad (WINDOW); at +X the shell's stop rib
for f in FORKS:
    RETAIN[f] = {"spin": [0, 0, 1], "play": 0.5, "not_by": ["leg-" + f[5:]]}   # swivels on its 2 screws

# ---- assembly (plan order) -------------------------------------------------------------------------------------------
MODULE_GROUP = ("drive-module", "idler-1", "idler-2", "idler-3-v2", "pin-1", "pin-2", "pin-3", "pin-keeper",
                "keeper-screw", "keeper-nut", "crankshaft-1", "crankshaft-2", "crankshaft-3", "crankshaft-4", "cap",
                "cap-screw", "cap-nut", "shared-nut", "clamp-nut", "i7-nut-1", "i7-nut-2", "i7-nut-3", "i7-nut-4")
_bench, ASSEMBLY = ["drive-module"], [("chassis", None)]
# cover nuts on the bare shell: pushed 6 mm along their slots by the pliers' nose (ACCESS checks it, 25 mm reach);
# the 60 mm straight-path test does not apply (every way out of a post meets the switch block, the band or the clip
# 33-43 mm away), so they are placed, as the fork nuts are
ASSEMBLY += [(f"cover-nut-{k + 1}", None) for k in range(len(COVER_SCREWS))]
for step in A.ASSEMBLY:
    names, d, *o = step
    if names == "drive-module":
        continue
    if names in (("n20", "n20-shaft", "pinion"), "motor-clamp", "shared-screw", "clamp-screw") or \
            (isinstance(names, str) and names.startswith("leg-")) or names in ("holder", "eyes-board"):
        continue                                          # these go in on the shell, below
    opts = dict(o[0]) if o else {}
    if "bench" not in opts:                               # module steps, on the bench with what is there
        opts["bench"] = list(_bench)
        _bench += [names] if isinstance(names, str) else list(names)
    ASSEMBLY.append((names, d, opts))
ASSEMBLY += [(f"i7-nut-{k + 1}", [n[3][0], n[3][1], 0], {"bench": list(_bench)})      # slid in along its slot
             for k, n in enumerate(A.B.I7_NUTS)]
ASSEMBLY.append((MODULE_GROUP, [0, 0, 1], {"note": "the module with its train and cap, no motor, into the deck "
                                                   "window from above (plan step 10)"}))
for f in FORKS:
    ASSEMBLY += [(f"{f}-nut-low", None), (f"{f}-nut-up", None), (f, None), ("leg-" + f[5:], None),
                 (f"{f}-screw-low", [0, 0, -1]), (f"{f}-screw-up", [0, 0, 1])]
ASSEMBLY += [(("n20", "n20-shaft", "pinion"), [0, 0, 1]), ("motor-clamp", [0, 0, 1]), ("shared-screw", [0, 0, 1]),
             ("clamp-screw", [0, 0, 1])]
# the switch goes into the cover on the bench (cover upside down; leads threaded through the eye, then soldered)
ASSEMBLY += [("switch", [1, 0, 0], {"bench": ["crank-cover"],
                                    "note": "slid in from the open +X end, lever and pins in their slots"})]
COVER_GROUP = ("crank-cover", "switch")
ASSEMBLY += [(COVER_GROUP, [0, 0, 1], {"note": "after the clamp: the cover with its switch, over the crank window, "
                                               "its spigot in the post; the leads' loop follows it"})]
ASSEMBLY += [("motor-leads", None)]
ASSEMBLY += [(f"cover-screw-{k + 1}", [0, 0, 1]) for k in range(len(COVER_SCREWS))]
ASSEMBLY += [(f"i7-screw-{k + 1}", [0, 0, -1]) for k in range(4)] + [("holder", None), ("eyes-board", None)]

ACCESS = list(A.ACCESS)
ACCESS += [{"at": f"i7-nut-{k + 1}", "tool": tool("pliers", [CX + x + d[0] * 8.0, y + d[1] * 8.0, nz + K.NUT_T / 2],
                                                  [d[0], d[1], 0]),
            "why": "on the bench: nut pushed along its slot into the module, pliers"}
           for k, (x, y, nz, d) in enumerate(A.B.I7_NUTS)]
ACCESS += [{"at": MODULE_GROUP, "tool": tool("finger", [CX, -10.0, R.DECK_TOP + 6.0], [0, 0, 1]),
            "why": "the module with its train and cap lowered into the deck window by hand"}]
ACCESS += [{"at": f"i7-screw-{k + 1}", "tool": tool("hex-key", [CX + r["x"], r["y"], r["head"] - K.HEAD_H],
                                                     [0, 0, -1]),
            "why": f"M3×{r['length']:g} from below, robot on its back, 2.5 hex key"} for k, r in enumerate(I7)]
ACCESS += [{"at": f"cover-screw-{k + 1}", "tool": tool("hex-key", [x, y, SH.COVER_Z0 + SH.COVER_T + K.HEAD_H],
                                                      [0, 0, 1]), "why": "M3×10 from above, 2.5 hex key"}
           for k, (x, y, _) in enumerate(COVER_SCREWS)]
ACCESS += [{"at": "switch", "tool": tool("finger", [SH.SW_BODY[2] + 12.0, (_SB[1] + _SB[3]) / 2, _ZL], [1, 0, 0]),
            "why": "on the bench: the switch pushed into its cradle from +X"},
           {"at": COVER_GROUP, "tool": tool("finger", [CX, 0.0, SH.COVER_Z0 + SH.COVER_T + 8.0], [0, 0, 1]),
            "why": "the cover with its switch lowered over the crank window by hand"}]
ACCESS += [{"at": f"cover-nut-{k + 1}", "tool": tool("pliers", [x + d[0] * 6, y + d[1] * 6, SH.COVER_Z0 - 2.5],
                                                     [d[0], d[1], 0], d=6.0, reach=25.0),
            "why": "on the bare shell (step 9a): nut slid into its post from the side, the pliers' nose"}
           for k, (x, y, d) in enumerate(COVER_SCREWS)]
for f, n in FORKS.items():
    P = PARTS[f"{f}-screw-up"]["mesh"].centroid
    ACCESS += [{"at": f"{f}-screw-up", "tool": tool("hex-key", [P[0], P[1], R.BAND_TOP], [0, 0, 1]),
                "why": "upper swivel screw from the band top (body off), 2.5 hex key"},
               {"at": f"{f}-screw-low", "tool": tool("hex-key", [P[0], P[1], BOSS_BOT - K.HEAD_H], [0, 0, -1]),
                "why": "lower swivel screw from below, robot on its back"}]

# ---- joints ----------------------------------------------------------------------------------------------------------
JOINTS = dict(A.JOINTS)
JOINTS[("drive-module", "chassis")] = {"fit": fits.WINDOW, "where": ((CX, -8.0, 73.8), (16.0, 90.0, 1.8)),
                                       "why": "I7: the module's top in the deck window, a side"}
for k, r in enumerate(I7):
    z0, z1 = r["head"] + 0.5, r["z_mod"] - 0.2         # the shank in its hole, above the head
    JOINTS[(f"i7-screw-{k + 1}", "chassis")] = {"fit": fits.STEEL,
                                                "where": ((CX + r["x"], r["y"], (z0 + z1) / 2), (5.0, 5.0, z1 - z0)),
                                                "why": f"I7 screw {k + 1}'s shank in its Ø3.3 hole"}
_sp = [(x, y) for x, y, kind, _ in SH.COVER_POSTS if kind == "spigot"][0]
JOINTS[("chassis", "crank-cover")] = {"fit": fits.LOCATOR, "where": ((*_sp, SH.COVER_Z0 + 0.8), (7.0, 7.0, 1.4)),
                                      "why": "the post's spigot in the cover's hole: locates the cover"}
JOINTS[("crank-cover", "switch")] = {"fit": fits.WINDOW, "where": (((_SB[0] + _SB[2]) / 2, (_SB[1] + _SB[3]) / 2, _ZL),
                                                                    (_SB[2] - _SB[0] + 1.5, _SB[3] - _SB[1] + 1.5, 8.0)),
                                      "why": "the switch in its cradle (catalogue size + WINDOW, redrawn once measured)"}
JOINTS[("motor-leads", "chassis")] = {"fit": fits.WINDOW, "where": ((SH.CLIPS[0][0], SH.LEAD_Y, SH.LEAD_Z), (5.0, 8.0, 5.0)),
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

# ---- marks, labels, print, measure ----------------------------------------------------------------------------------
MARKS = dict(A.MARKS)
MARKS.update({f: "the leg's own L/R label (legs design); the fork fits its pocket either way up" for f in FORKS})
MARKS["chassis"] = ("FRONT arrow (tip to -Y) sunk 0.5 in the seat at the front left, beside the front block (x 26.2, y -41.5, placed by shell_marks()); the fork number (1-4 dots, front to rear) beside each "
                    "upper swivel screw on the band top")
MARKS["crank-cover"] = ("FRONT arrow on its top face; it fits one way (the spigot and the shared screw's hole); the "
                        "switch fits its cradle one way (lever to the rear slot, pins to the front slot)")
LABELS = {"es": {**A.LABELS["es"], "chassis": "carcasa base (chasis de vista)",
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
                 **{f"{f}-nut-up": f"tuerca superior de la horquilla {f[5:]}" for f in FORKS}}}
PRINT_ORIENT = dict(A.PRINT_ORIENT)
PRINT_ORIENT["chassis"] = A.FLIP          # band top (slide lip) on the bed (plan A1b)
PRINT_ORIENT["crank-cover"] = A.FLIP     # top face (sunk arrow) on the bed, the rear lip standing up: no support (upright
                                         # it printed its whole plate over the bed). The lip (1.2 × 8.5, 7.6 tall) closes the
                                         # module path's slot in the band's rear wall: nothing pushes on it (the WARN on it)
MEASURE = list(A.MEASURE) + [
    {"part": "chassis", "what": "crank window width across X", "nominal": round(2 * SH.CRANK_HALF, 2),
     "tol": (0.0, 0.3), "points": "at crank 2's slot, deck edge to deck edge"},
    {"part": "chassis", "what": "slide lip height over the seat", "nominal": SH.LIP_H, "tol": (-0.2, 0.2),
     "points": "either side, at y 0"},
    {"part": "chassis", "what": "fork pocket height (boss top to band underside)",
     "nominal": round(FORK_TOP - FORK_BOT + 2 * GAP, 2), "tol": (0.0, 0.3), "points": "any fork pocket, at the screw"},
    {"part": "chassis", "what": "cover post spigot diameter", "nominal": SH.SPIGOT_D, "tol": (-0.1, 0.05),
     "points": "the front-left post"},
    {"part": "crank-cover", "what": "spigot hole diameter", "nominal": fits.bore(SH.SPIGOT_D, fits.LOCATOR),
     "tol": (-0.05, 0.15), "points": "front-left hole"}]
STEP_VIEW = getattr(A, "STEP_VIEW", {})
if hasattr(A, "VIEW"):                     # a VIEW of None crashed the renders: only set it if Part A has one
    VIEW = A.VIEW
