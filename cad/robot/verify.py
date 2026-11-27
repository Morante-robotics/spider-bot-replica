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
PLAY = 1.0
RETAIN = {"body": {"spin": None, "slide": None, "play": 0.6},          # two front snap hooks under the ribs + rear tab
          **{n: {"spin": None, "slide": None, "play": PLAY} for n in LEGS}}  # snap bead in the pin's groove + window + body rim
# option D (the leg rides with its pin point on the crank pin, groove = the bead's sweep + 2 x TURN): the legs' play is what retention measures,
# PLAY mm along the pin (was 1.25, 1.65 on the corner legs 0, 3, 4, 7 while the leg slid 1.4-1.7 mm along it)
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
        out.append({"part": n, "origin": [float(sx * (SH.TUBE_X1[k % 4] + 0.1)), float(A0[1]), float(A0[2])], "axis": [sx, 0.0, 0.0],
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


# --- checks ask exactly their pair's fit (2026-11-27; datasheet «Parked: leg <-> crank joint») ---
# (a) leg k turns on crank k%4+1: pin in its bore and the mouth against the web are a turning joint (fits.TURN): contact
# is the joint, not MIN_GAP. Morante's accepted 0.18 on crank-4 / leg-3, 7 (above) stays the asked gap for those two.
_ACCEPTED = {("crank-4", "leg-3"): 0.18, ("crank-4", "leg-7"): 0.18}
for _k, _n in enumerate(LEGS):
    _c = f"crank-{_k % 4 + 1}"
    JOINTS[(_n, _c)] = {"fit": _ACCEPTED.get((_c, _n), fits.TURN), "why": "leg pin in its bore and mouth on the web: a turning joint (fits.TURN)"}
    ALLOWED_CONTACT[(_n, _c)] = "turning joint: the JOINTS row asks its fit (fits.TURN), not MIN_GAP"
# (b) a leg to every part it sweeps past (other legs, body, the interior; its own crank is the joint above, the base the
# LEG_OPEN window in JOINTS): fits.LEG_PATH, not MIN_GAP
for _n in LEGS:
    for _m in PARTS:
        if _m != _n and _m != "base" and not (_m.startswith("crank-") and (_n, _m) in JOINTS) and not PARTS[_m].get("hardware"):
            PAIR_GAP.setdefault((_n, _m), fits.LEG_PATH.side)
# (c) check 13 reads the legs' joint region only: the end tube and its closed end (bore, snap groove/bead, slit), boxed from
# shells.py (x: tail .. closed end, radius END_R + flare, + 1 mm); the arms, claws and foot tips are the looks' shape (printed at 0.70).
# Everything else of the leg is an except box (the complement of the tube box, in the leg's STL frame). The wall is fits.WALL_MIN.
STEP_X = 2.6    # the neck blend's step meets the tilted tube's outer cone up to here past the pin point (1.4 with the tube about x: the tilt lowers the cone's flank by 0.1-0.2 at x 2)
def _leg_except():
    from cad import motion
    import math
    out, B = [], 300.0
    for k, n in enumerate(LEGS):
        P_, A0, *_ = motion.neutral_leg(k % 4, SH.P, n=13)
        sx = 1.0 if k < 4 else -1.0
        x0 = A0[0] - SH.CL.TAIL; xe = SH.TUBE_X1[k % 4] + SH.SNAP_WALL
        r = SH.END_RS[k % 4] + (xe - A0[0]) * math.tan(math.radians(SH.CONE_FLARE[k % 4])) + 1.0
        cy = float((xe - A0[0]) * SH.CONE_AXIS[k % 4][1] / SH.CONE_AXIS[k % 4][0]); cz = float((xe - A0[0]) * SH.CONE_AXIS[k % 4][2] / SH.CONE_AXIS[k % 4][0])     # the tilted axis at the closed end
        xa, xb = sorted((sx * (x0 - 1.0), sx * (xe + 1.0)))
        ya, yb, za, zb = float(A0[1] - r + min(0, cy)), float(A0[1] + r + max(0, cy)), float(A0[2] - r + min(0, cz)), float(A0[2] + r + max(0, cz))
        why = "leg looks outside the joint (jenscolt's shape, printed at 0.70): only the end tube is asked"
        for lo, hi in (([-B, -B, -B], [xa, B, B]), ([xb, -B, -B], [B, B, B]), ([xa, -B, -B], [xb, ya, B]),
                       ([xa, yb, -B], [xb, B, B]), ([xa, ya, -B], [xb, yb, za]), ([xa, ya, zb], [xb, yb, B])):
            out.append({"part": n, "box": [lo, hi], "why": why})
        # the mouth: the outer chamfer (FACE_CHAMFER, 45 deg) thins the rim edge to 1.4-1.5 over 0.5 mm, and the neck's blend cone meets the tube in a 0.27 high step
        # at xrel 0.7: sharp edges, where the inward ray meets the neighbouring face within 0.0-0.2. Measured on the exact BREP (0.004 tessellation, section at
        # four angles): bore-to-outer wall >= 2.0 everywhere along the tube from x = A0x + 0.7 on; at the chamfer edge 1.43 (rim edge, a chamfer, not a wall)
        xm_ = sorted((sx * (A0[0] - SH.TAIL - 0.2), sx * (A0[0] + STEP_X)))
        out.append({"part": n, "box": [[xm_[0], float(A0[1] - r), float(A0[2] - r)], [xm_[1], float(A0[1] + r), float(A0[2] + r)]],
                    "why": "tube mouth: the outer chamfer edge (rim 1.43 over 0.5 mm) and the neck blend's 0.27 step: sharp edges the inward ray reads as thin; bore-to-outer wall measured on the BREP >= WALL_MIN beyond x A0 + 0.7"})
        # the slit's two outer chamfers (SLIT_CHAMFER x 45 deg): the inward ray from a chamfer face leaves through the slit's side face within 1.4-1.9 mm. Not a wall: the wall
        # across (radial from the bore to the outer cone, normal to the cone) is WALL_MIN everywhere at the slit (BORE_R + WALL_MIN / cos(flare) by construction; sections at
        # x A0 + 1.7 and 2.2: outer - bore radius >= 2.0 on every 30 deg sector). The box is the slit's radial strip, bore side excluded (r from BORE_R + 0.9).
        P_n = np.asarray(P_, float); u_ = P_n - np.asarray(A0, float); u_[0] = 0.0; u_ = -u_ / np.linalg.norm(u_)     # the slit's direction, as shells.py
        ca_ = SH.CONE_AXIS[k % 4]; xe_ = SH.TUBE_X1[k % 4] + SH.SLIT_END; xs0 = A0[0] - SH.TAIL
        r_in = SH.BORE_R[k % 4] + 0.9; r_out = SH.END_RS[k % 4] + (xe_ - A0[0]) * math.tan(math.radians(SH.CONE_FLARE[k % 4])) + 0.3
        w_ = SH.SNAP_SLIT / 2 + SH.SLIT_CHAMFER + 0.2; tg_ = np.array([-u_[2], u_[1]])
        pts_ = [np.asarray(A0[1:3], float) + (xx - A0[0]) * np.array([ca_[1], ca_[2]]) / ca_[0] + rd * u_[1:3] + td * tg_
                for xx in (xs0, xe_) for rd in (r_in, r_out) for td in (-w_, w_)]
        pts_ = np.array(pts_); xr_ = sorted((sx * (xs0 - 0.7), sx * (xe_ + 0.5)))
        out.append({"part": n, "box": [[xr_[0], float(pts_[:, 0].min()), float(pts_[:, 1].min())], [xr_[1], float(pts_[:, 0].max()), float(pts_[:, 1].max())]],
                    "why": "the slit's outer chamfers (45 deg, SLIT_CHAMFER): inward rays leave through the slit's side face at 1.4-1.9 mm; the wall across is WALL_MIN (sections at x A0 + 1.7 / 2.2: outer - bore radius >= 2.0 all round)"})
        # the snap bead: a deliberate ring SNAP_BW (0.72) wide, a ridge on the bore that flexes over the pin (fits.PRESS, coupon c1); it is not a wall
        xs = sorted((sx * (A0[0] - SH.SNAP_BW / 2 - 0.15), sx * (A0[0] + SH.SNAP_BW / 2 + 0.15))); rr = SH.BORE_R[k % 4] + 0.5
        out.append({"part": n, "box": [[xs[0], float(A0[1] - rr), float(A0[2] - rr)], [xs[1], float(A0[1] + rr), float(A0[2] + rr)]],
                    "why": "the snap bead: a deliberate ring SNAP_BW wide on the bore, flexing over the pin tip (fits.PRESS, coupon c1)"})
    return out
MINIMUMS = dict(MINIMUMS or {"module": 1.0, "mark": 3.0}, parts=list((MINIMUMS or {}).get("parts", [])) + LEGS, wall=fits.WALL_MIN,
                **{"except": list((MINIMUMS or {}).get("except", [])) + _leg_except()})
