"""cad_verify spec for chassis Part B1's `front-block-v2` (I8), on the looks shell as the ground part.

A small spec, folded into the whole-robot spec in Part C. It takes from Part A's spec (verify.py) only what stands
round the front block: the drive module, its cap and the cap's front screw, the crankshafts and the 8 legs (swept a
full turn every STEP degrees); from the shell (shell.py) the ground `chassis` (out/chassis.stl), the crank cover and
the front block's interface (pads, lips, nut bosses at y -51). Part A's parts and the crank cover are fixed here: their
own joints, retention and assembly are checked in verify.py and verify_b1.py; this spec checks the front block against
them.

What it checks for the front block:
- the pads in the shell's LOCATOR lips (JOINTS), the 2 × M3×10 in their holes (STEEL) and their nuts under the deck;
- held in 6 directions: the lips ±X ±Y, the deck -Z, the screws +Z (RETAIN);
- clear of the cap (WINDOW, the bridge) and of its front screw's head (KEEP_OUT), of the crank cover and its posts;
- the legs' path past it over a full turn (LEG_PATH);
- the nuts slid into their bosses from below before the module goes in, the block down from above, the screws through
  the access tubes (ASSEMBLY, ACCESS);
- the body's way in (lowered 4 mm behind its place, slid forward) is cut from the block in front_block.py; the carcass
  body is not a part here (body v2 is B2, its L-slots take the tongues; its spec checks the slide). Probe on the lifted
  carcass body, tongues excluded (2026-11-16): no overlap at its place, slid 2 and 4 mm, and lowered at +4 Y from 5
  and 15 mm up; smallest gap 0.39 mm.
- the shell must be cut round the block (front_block.clear_outline(): the pads + LOCATOR to the lips' top, the
  block's outline + WINDOW above). Until shell.py does it, FB_CHASSIS=<stl> runs this spec on a shell cut so.

    VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify_fb.py --quick --only front-block-v2
    ../../.venv/bin/python ../../tools/cad_verify.py verify_fb.py --out verify-result-fb.txt --render images/verify-fb
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
import front_block as FB  # noqa: E402
from cad import common as K, fits, robot as R  # noqa: E402
from cad_verify import tool  # noqa: E402

CX = A.CX
STEP = A.STEP
MOTION = A.MOTION
NAME = FB.NAME

# ---- parts --------------------------------------------------------------------------------------------------------
_AROUND = ["drive-module", "cap", "cap-screw", "cap-nut"] + [f"crankshaft-{i + 1}" for i in range(4)] + list(A.LEGS)
PARTS = {n: {**A.PARTS[n], "fixed": True} for n in _AROUND}     # checked in verify.py / verify_b1.py
# FB_CHASSIS=<stl>: a what-if shell (e.g. the shell cut by front_block.clear_outline(), before shell.py does it)
PARTS["chassis"] = {"stl": os.environ.get("FB_CHASSIS", "out/chassis.stl"), "fixed": True}
PARTS["crank-cover"] = {"stl": "out/crank-cover.stl", "fixed": True}
PARTS[NAME] = {"stl": f"out/{NAME}.stl"}

HEAD_Z = R.DECK_TOP + FB.PAD_T                          # head face on the boss (76.8)
NUT_Z = HEAD_Z - FB.SCREW_L + 0.5                       # shell.front_block_seat: nut 0.5 above the tip
for k, (x, y, d) in enumerate(FB.FB_SCREWS_FULL):
    PARTS[f"fb-screw-{k + 1}"] = {"mesh": A.m3([x, y, HEAD_Z], [0, 0, -1], FB.SCREW_L), "hardware": True,
                                  "fixed": True, "label": "M3×10 Allen"}
    _n = A.nut([x, y, NUT_Z + 0.15], [0, 0, 1])
    # turned as its pocket in the shell (base v1 nut_pocket: flats facing the slot's sides, a corner towards the slot;
    # measured on out/chassis.stl 2026-11-16: flats at 2.9 across ±Y for a slot along X)
    _n.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(d[1], d[0]), [0, 0, 1], [x, y, 0]))
    PARTS[f"fb-nut-{k + 1}"] = {"mesh": _n, "hardware": True, "fixed": True, "label": "tuerca M3"}
FB_HW = [f"fb-{s}-{k + 1}" for k in range(2) for s in ("screw", "nut")]
LEGS = A.LEGS


def poses(t):
    P = A.poses(t)
    return {n: M for n, M in P.items() if n in PARTS}


GEARS = []                     # no gear touches the front block; the train's meshes are verify.py's

# ---- gaps and contacts ----------------------------------------------------------------------------------------------
PAIR_GAP = {**{k: v for k, v in A.PAIR_GAP.items() if k[0] in PARTS and k[1] in PARTS},   # Part A's, for its parts
            **{(leg, NAME): fits.LEG_PATH.side for leg in LEGS},
            **{(leg, "chassis"): fits.LEG_PATH.side for leg in LEGS},
            (NAME, "cap"): fits.WINDOW.side, (NAME, "cap-screw"): fits.WINDOW.side,
            (NAME, "crank-cover"): fits.WINDOW.side}
for k in range(2):
    PAIR_GAP[(f"fb-screw-{k + 1}", "chassis")] = 0.1      # M3 in Ø3.3 (STEEL 0.15)
    PAIR_GAP[(f"fb-screw-{k + 1}", NAME)] = 0.1
    PAIR_GAP[(f"fb-nut-{k + 1}", "chassis")] = 0.1        # nut in its pocket (+0.15 a side)
ALLOWED_CONTACT = {
    (NAME, "chassis"): "the pads stand on the deck (z 74.8) inside their LOCATOR lips (JOINTS measures the lips)",
    ("cap", "drive-module"): A.ALLOWED_CONTACT[("cap", "drive-module")],
    ("cap-screw", "cap"): "head clamps the cap", ("cap-screw", "cap-nut"): "screw in its nut",
    ("cap-nut", "drive-module"): "nut pulled up against its pocket",
    ("drive-module", "chassis"): "module on its 4 bosses (verify_b1.py checks it)",
    ("crank-cover", "chassis"): "cover on its 3 posts (verify_b1.py checks it)",
    **{(f"crankshaft-{i + 1}", "drive-module"): "journals in their holes (verify.py checks them)" for i in range(4)},
    **{(f"crankshaft-{i + 1}", "cap"): "the cap's tongues hold the journals down (verify.py)" for i in range(4)},
    **{(leg, f"crankshaft-{i + 1}"): "the leg rides its crank (legs design)" for leg in LEGS for i in range(4)},
}
for k in range(2):
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", NAME)] = "head clamps the pad's boss"
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", f"fb-nut-{k + 1}")] = "screw in its nut"
    ALLOWED_CONTACT[(f"fb-nut-{k + 1}", "chassis")] = "nut pulled up against its pocket under the deck"
    ALLOWED_CONTACT[(f"fb-screw-{k + 1}", "chassis")] = "the shank passes the deck and the boss to its nut"

_h = trimesh.creation.cylinder(radius=K.HEAD_D / 2 + fits.WINDOW.side, height=K.HEAD_H + fits.WINDOW.side, sections=48)
_h.apply_translation([FB.CAP_SCREW_XY[0], FB.CAP_SCREW_XY[1], FB.CAP_TOP + (K.HEAD_H + fits.WINDOW.side) / 2])
KEEP_OUT = {"cap-screw-head": {
    "part": "chassis", "mesh": _h,
    "why": "the cap's front screw head + WINDOW (plan: the block >= 83.35 over it): the cap comes off with the block off",
    "except": ["cap-screw", "cap", "chassis"], "except_why": "the screw, the cap it clamps, the shell's clear space"}}
# the block stays inside the carcass's front block (base v1, lifted) but for the tongues (body v2's L-slots take them)
_v1 = trimesh.load(os.path.join(HERE, "..", "base", "out", "front-block.stl"))
_fbm = trimesh.load(os.path.join(HERE, "out", f"{NAME}.stl"))
_t0, _t1 = _fbm.bounds[0][0] + FB.TONGUE_OUT, _fbm.bounds[1][0] - FB.TONGUE_OUT     # the side faces, read on the part
KEEP_IN = {"carcass-front-block": {
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
                           "inset": -(FB.TONGUE_OUT + 0.2), "why": "the +X hook tongue"}}}}

# ---- retention -------------------------------------------------------------------------------------------------------
RETAIN = {NAME: {"play": 0.5}}       # pads in LOCATOR lips (0.2 a side, 1.5 tall); deck below; 2 screws above

# ---- assembly (plan steps 9a, 10-13) ---------------------------------------------------------------------------------
ASSEMBLY = [("chassis", None)]
# step 9a, on the bare shell before the module (its slot runs 12 mm towards CX, into the module's space): pushed along
# the slot by the pliers' nose (ACCESS); the 60 mm straight-path test does not apply (the bowl's far wall stands
# 29-36 mm away), so they are placed, as verify_b1.py places the cover nuts
ASSEMBLY += [(f"fb-nut-{k + 1}", None) for k in range(2)]
ASSEMBLY += [(n, None) for n in _AROUND if not n.startswith("leg")] + [(leg, None) for leg in LEGS]
ASSEMBLY += [("crank-cover", None)]
ASSEMBLY += [(NAME, [0, 0, 1], {"note": "step 13: pads down into their lips, over the cap"})]
ASSEMBLY += [(f"fb-screw-{k + 1}", [0, 0, 1], {"note": "down the access tube, 2.5 hex key"}) for k in range(2)]

ACCESS = [{"at": f"fb-screw-{k + 1}", "tool": tool("hex-key", [x, y, HEAD_Z + K.HEAD_H], [0, 0, 1]),
           "why": "M3×10 down the Ø6.5 access tube from the block's top, 2.5 hex key (body off)"}
          for k, (x, y, _) in enumerate(FB.FB_SCREWS_FULL)]
ACCESS += [{"at": f"fb-nut-{k + 1}", "tool": tool("pliers", [x + d[0] * 6.0, y + d[1] * 6.0, NUT_Z + K.NUT_T / 2],
                                                 [d[0], d[1], 0], d=2.0, reach=25.0),
            "why": "step 9a on the bare shell: nut pushed along its 2.7 mm slot into the boss by the pliers' nose tip "
                   "(or a small screwdriver)"}
           for k, (x, y, d) in enumerate(FB.FB_SCREWS_FULL)]

# ---- joints ----------------------------------------------------------------------------------------------------------
_lz = R.DECK_TOP + SH.FB_LIP_H / 2
_hz0, _hz1 = FB.FOOT_TOP, R.BAND_TOP + SH.LIP_H + 0.5
JOINTS = {
    (NAME, "chassis"): {"fit": fits.LOCATOR, "where": ((CX, -43.0, _lz), (90.0, 44.0, SH.FB_LIP_H - 0.4)),
                        "why": "I8: both pads in their lips, a side (the deck contact is below this box)"},
    ("chassis", NAME): {"fit": fits.WINDOW, "where": ((CX, -43.0, (_hz0 + _hz1) / 2), (90.0, 44.0, _hz1 - _hz0)),
                        "why": "above the lips: the shell's band, seat and slide lip round the block (shell cuts "
                               "front_block.clear_outline())"}}
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
MARKS = {NAME: "none needed: it fits one way only (the pads' outlines in their lips and the face's curve); the eyes "
               "JST seat and the slack box show its left side"}
LABELS = {"es": {**{n: A.LABELS["es"].get(n, n) for n in _AROUND}, "chassis": "carcasa base (chasis de vista)",
                 "crank-cover": "tapa de los cigüeñales", NAME: "bloque frontal v2",
                 **{f"fb-screw-{k + 1}": f"tornillo del bloque frontal {k + 1}" for k in range(2)},
                 **{f"fb-nut-{k + 1}": f"tuerca del bloque frontal {k + 1}" for k in range(2)}}}
PRINT_ORIENT = {NAME: np.eye(4)}      # base (the pads) on the bed, as built
SECTIONS = [([FB.FB_SCREWS[0][0], 0, 0], [1, 0, 0]), ([33.7, 0, 0], [1, 0, 0]), ([CX, 0, 0], [1, 0, 0]), ([0, -51.0, 0], [0, 1, 0]),
            ([0, -31.0, 0], [0, 1, 0])]
MEASURE = [
    {"part": NAME, "what": "left pad's depth along Y at x 20 (its rear block)", "nominal": round(_pad_d, 2),
     "tol": (-0.1, 0.1), "points": "front face to rear face of the pad, 1 mm above the bed"},
    {"part": NAME, "what": "JST seat across X", "nominal": round(FB.SEAT[2] - FB.SEAT[0], 2), "tol": (0.0, 0.2),
     "points": "the seat at the slack box's bottom"},
    {"part": NAME, "what": "access tube bore", "nominal": SH.CBORE, "tol": (-0.1, 0.3), "points": "either tube, at the top"},
    {"part": NAME, "what": "hook tongue height at its tip", "nominal": FB.TONGUE_TIP, "tol": (-0.1, 0.1),
     "points": "either tongue, outer edge"},
    {"part": NAME, "what": "hook tongue reach from the side face", "nominal": FB.TONGUE_OUT, "tol": (-0.1, 0.1),
     "points": "either tongue, top face"},
    {"part": NAME, "what": "boss thickness under the head", "nominal": FB.PAD_T, "tol": (-0.1, 0.1),
     "points": "depth gauge down the access tube, from the bed face"}]
