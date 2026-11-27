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
# the corner legs 0, 3 and their mirrors 4, 7 slide up to 1.40 / 1.50 mm towards their crank (0 and 7 at pose 0-7,
# 4 at pose 10, 3 at pose 12; measured at all 24 poses 2026-11-23: only the groove stops them since the base front is
# smooth): accepted by Morante 2026-11-23 («Aceptar 1,6 mm hacia dentro»); outward every leg stays <= 1.15 mm
for _n in ("leg-0", "leg-3", "leg-4", "leg-7"):
    RETAIN[_n]["play"] = 1.65
# legs' play 1.25, not 1.0 (Morante, 2026-11-23): the groove lets the bead travel 1.4-1.7 mm over the 24 poses (tube
# tilt + axial drift), so a leg rides up to 1.0 mm along its pin; inward it cannot come off, outward it stays <= 0.75
ALLOWED_CONTACT = {("body", "base"): "body rim seated on the base ledge; snap hooks under the front ribs (fits.PRESS, coupon c1)"}
JOINTS = {("body", "base"): {"fit": fits.PRESS, "why": "front snap fingers under the ribs and rear tab (plan body-front-snaps, body-rear-tab)"},
          **{(n, "base"): {"fit": fits.LEG_OPEN, "why": "leg neck in its open-top window (plan leg-path; LEG_OPEN, 2026-11-23)"} for n in LEGS}}
import cutters as CU                              # the leg path is the one the base windows are cut for (cutters.py)
LEG_DROP = CU.LEG_DROP                            # leg path: lowered LEG_DROP beside its pin with its tube LEG_SLIDE[k] outboard along the pin's own axis
LEG_SLIDE = CU.LEG_SLIDE                          # (u: crank pin end -> leg pivot at its crank pose), then slid inward along -u: the bead clicks in.
ASM_POSE = CU.ASM_POSE                            # legs 5 and 6 start 10 mm out (the drive unit's lug); legs 0 and 3 go on after half a crank turn (pose 12)
def _leg_u(k):
    u = np.asarray(SH.PIV[k], float) - np.asarray(SH.A_ALL[k, ASM_POSE[k]], float)
    return u / np.linalg.norm(u)
_LEG_ASM = [(n, [[0, 0, -LEG_DROP], [float(x) for x in -_leg_u(k) * LEG_SLIDE[k]]],
             {"except": {f"crank-{k % 4 + 1}": "the snap bead flexes over the pin tip (slit, fits.PRESS, coupon c1)"}, "at": ASM_POSE[k],
              "note": "lowered beside the pin, then slid inward along the pin's axis: the bead clicks into the groove"})
            for k, n in sorted(enumerate(LEGS), key=lambda kn: (ASM_POSE[kn[0]], kn[0]))]
ASSEMBLY = [("base", None)] + _LEG_ASM + [("body", [0, 0, 1], {"at": SH.KC})]
BODY_TOP = 80.5                                  # body roof's top (z, body.stl bbox): the finger presses on the outside, not from inside the shell
ACCESS = [{"at": "body", "tool": tool("finger", [0, 0, BODY_TOP], [0, 0, 1]), "why": "pressed down by hand on the roof: two front clicks"}]
PRINT_ORIENT = {"base": np.eye(4),                                # foot down
                "body": np.diag([1.0, -1.0, -1.0, 1.0])}           # rim up (roof on the bed): 180 deg about x
MARKS = {"body": "body-on mark: crank pose 12 (plan step 17)"}
LABELS = {"es": {"base": "base", "body": "cuerpo", **{n: f"pata {k + 1}" for k, n in enumerate(LEGS)}}}
MEASURE = []
def _junction_sections():
    """The thinnest plane through each leg's tube -> neck rod -> arm junction (shells.JOINT_R, SNAP_WALL): planes normal to the
    rod from the pin tip's plane to the hub cut, and normal to x through the tube's closed end (the part's own STL frame)."""
    from cad import motion
    out = []
    for k, n in enumerate(LEGS):
        P_, A0, *_ = motion.neutral_leg(k % 4, SH.P, n=13)
        u = (P_ - A0) / np.linalg.norm(P_ - A0); sx = 1.0 if k < 4 else -1.0
        mir = np.array([sx, 1.0, 1.0]); A0m, um = A0 * mir, u * mir
        tip = SH.P["XC"] + SH.CL.PINX
        sa = (tip - A0[0]) / u[0]
        out.append({"part": n, "origin": [float(v) for v in A0m], "axis": [float(v) for v in um], "s0": float(sa), "s1": float(SH.HUBCUT - 0.25),
                    "min": 15.0, "why": "tube -> neck rod -> arm, planes normal to the rod (rod alone 17.3)"})
        out.append({"part": n, "origin": [float(sx * (SH.P["XC"] + SH.CL.PINX + SH.SNAP_END + 0.1)), float(A0[1]), float(A0[2])], "axis": [sx, 0.0, 0.0],
                    "s0": 0.0, "s1": float(SH.SNAP_WALL - 0.2), "min": 15.0, "why": "the tube's closed end wall and the rod running into it"})
    return out
SECTION_MIN = _junction_sections()
SECTIONS = [([0, 0, 12], [0, 0, 1]), ([0, 0, 0], [1, 0, 0])]
if IV is not None:
    PARTS.update(getattr(IV, "PARTS", {}))
    for nm in ("RETAIN", "JOINTS", "MARKS", "PRINT_ORIENT", "ALLOWED_CONTACT"):
        globals()[nm].update(getattr(IV, nm, {}))
    LABELS["es"].update(getattr(IV, "LABELS", {}).get("es", {}))
    GEARS = list(getattr(IV, "GEARS", []))
    if getattr(IV, "PAIR_GAP", None): PAIR_GAP = dict(IV.PAIR_GAP)
    if getattr(IV, "KEEP_OUT", None): KEEP_OUT = dict(IV.KEEP_OUT)
    for nm in ("MINIMUMS", "GEAR_GEOM", "MARK_GEOM"):
        if getattr(IV, nm, None) is not None: globals()[nm] = getattr(IV, nm)
    MEASURE += getattr(IV, "MEASURE", [])
    ACCESS += getattr(IV, "ACCESS", [])
    ia = [s for s in getattr(IV, "ASSEMBLY", []) if s[0] != "base"]
    _st = lambda e: (e[2] if len(e) > 2 else {}).get("step", 99)
    _cut = getattr(IV, "LEGS_AFTER_STEP", 99)
    ASSEMBLY = ([ASSEMBLY[0]] + [s for s in ia if _st(s) <= _cut] + ASSEMBLY[1:-1]   # interior to step 9, then legs
                + [s for s in ia if _st(s) > _cut] + ASSEMBLY[-1:])                  # holder, motor…, body last
    if any(s[0] == "ss12d00-switch" for s in ia):                                        # switch and LEDs are fitted to the body on the bench: they go on with it
        ASSEMBLY[-1] = (("body", "ss12d00-switch", "leds"), [0, 0, 1], {"note": "body with its switch and LEDs, pressed on from above", "at": SH.KC})
# Gap Morante accepted under 0.2 (2026-11-23): the snap bead against its groove's neck on crank 4 (0.19 at poses 19/7,
# a turning part). The body's hairlines to the fixed parts inside are the coarse class now (cad_verify COARSE).
PAIR_GAP = {**globals().get("PAIR_GAP", {}), ("crank-4", "leg-3"): 0.18, ("crank-4", "leg-7"): 0.18}
