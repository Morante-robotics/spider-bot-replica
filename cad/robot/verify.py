"""cad_verify spec for cad/robot (plan.json): base fixed, body snapped on, 8 legs carried per crank pose as
motion.legs does (shells.leg_frame), and the interior's parts merged from interior_verify.py when it exists
(PARTS, poses_interior, RETAIN, JOINTS, MARKS, ASSEMBLY, ACCESS, PRINT_ORIENT, LABELS, MEASURE).

    ../../.venv/bin/python ../../tools/cad_verify.py verify.py --smoke
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT + "/tools", ROOT, HERE):
    if p not in sys.path: sys.path.insert(0, p)
from cad import fits
from cad_verify import rod, tool  # noqa: F401
import shells as SH
try:
    import interior_verify as IV
except ImportError:
    IV = None
LEGS = [f"leg-{k}" for k in range(8)]
MOTION = list(range(24))                       # crank poses k (15 deg each), motion.POSES
PARTS = {"base": {"stl": "out/base.stl", "fixed": True},
         "body": {"stl": "out/body.stl"},
         **{n: {"stl": f"out/{n}.stl"} for n in LEGS}}

def poses(t):
    k = int(t) % 24
    out = {n: SH.leg_frame(i, k) for i, n in enumerate(LEGS)}
    if IV is not None and hasattr(IV, "poses_interior"): out.update(IV.poses_interior(t))
    return out

UP = [0, 0, 1]
RETAIN = {"body": {"spin": None, "slide": None, "play": 0.6},          # two front snap hooks under the ribs + rear tab
          **{n: {"spin": None, "slide": None, "play": 1.25} for n in LEGS}}  # snap bead in the pin's groove + window + body rim
# legs' play 1.25, not 1.0 (Morante, 2026-11-23): the groove lets the bead travel 1.4-1.7 mm over the 24 poses (tube
# tilt + axial drift), so a leg rides up to 1.0 mm along its pin; inward it cannot come off, outward it stays <= 0.75
ALLOWED_CONTACT = {("body", "base"): "body rim seated on the base ledge; snap hooks under the front ribs (fits.PRESS, coupon c1)"}
JOINTS = {("body", "base"): {"fit": fits.PRESS, "why": "front snap fingers under the ribs and rear tab (plan body-front-snaps, body-rear-tab)"},
          **{(n, "base"): {"fit": fits.LEG_OPEN, "why": "leg neck in its open-top window (plan leg-path; LEG_OPEN, 2026-11-23)"} for n in LEGS}}
ASSEMBLY = [("base", None)] + [(n, [0, 0, 1]) for n in LEGS] + [("body", [0, 0, 1])]
ACCESS = [{"at": "body", "tool": tool("finger", [0, 0, 40], [0, 0, 1]), "why": "pressed down by hand: two front clicks"}]
PRINT_ORIENT = {"base": np.eye(4),                                # foot down
                "body": np.diag([1.0, -1.0, -1.0, 1.0])}           # rim up (roof on the bed): 180 deg about x
MARKS = {"body": "body-on mark: crank pose 12 (plan step 17)"}
LABELS = {"es": {"base": "base", "body": "cuerpo", **{n: f"pata {k + 1}" for k, n in enumerate(LEGS)}}}
MEASURE = []
SECTIONS = [([0, 0, 12], [0, 0, 1]), ([0, 0, 0], [1, 0, 0])]
if IV is not None:
    PARTS.update(getattr(IV, "PARTS", {}))
    for nm in ("RETAIN", "JOINTS", "MARKS", "PRINT_ORIENT", "ALLOWED_CONTACT"):
        globals()[nm].update(getattr(IV, nm, {}))
    LABELS["es"].update(getattr(IV, "LABELS", {}).get("es", {}))
    GEARS = list(getattr(IV, "GEARS", []))
    if getattr(IV, "PAIR_GAP", None): PAIR_GAP = dict(IV.PAIR_GAP)
    if getattr(IV, "KEEP_OUT", None): KEEP_OUT = dict(IV.KEEP_OUT)
    MEASURE += getattr(IV, "MEASURE", [])
    ACCESS += getattr(IV, "ACCESS", [])
    ia = [s for s in getattr(IV, "ASSEMBLY", []) if s[0] != "base"]
    _st = lambda e: (e[2] if len(e) > 2 else {}).get("step", 99)
    _cut = getattr(IV, "LEGS_AFTER_STEP", 99)
    ASSEMBLY = ([ASSEMBLY[0]] + [s for s in ia if _st(s) <= _cut] + ASSEMBLY[1:-1]   # interior to step 9, then legs
                + [s for s in ia if _st(s) > _cut] + ASSEMBLY[-1:])                  # holder, motor…, body last
