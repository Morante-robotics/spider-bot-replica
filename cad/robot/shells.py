"""Robot shells at S (spec.json S_start, 0.70): cad/base, cad/body, cad/eyes and cad/legs built as they are, moved into
the robot frame (motion.to_frame: (q - ORIGIN) x S) and given the plan's local features here, without editing those
designs. Every shell number is the fit check's (cad/robot/fitcheck/check.py LAYOUT and fit_env.py, 0 failing of 327),
imported, never copied:
  base   leg windows (the real legs' neck sweep, RN 8 + WR 0.9, pushed up past the rim, slid LSL off the pin),
         1.2 mm pads round each window, front-window reliefs (RELD 0.85 from the arms' 24-pose sweep), back-sheet pocket
         (PKT 1.6 outward, |x| <= 11, z 7..17), two front snap ribs
  body   two front snap fingers (SNT 0.8 x SNW 5, L RIMR - SNZ), rear tab notched over the back-sheet pocket, rim notch
         and eye-block pocket (BRELD / PKR 0.85 from the arms' sweep), the two eye cups (cad/eyes) in their bores
  legs   cad/legs leg() bent on motion's neutral leg; the jenscolt hub replaced by the end tube (bore TURN on the Ø3
         printed pin, wall 1.2, tail TAIL 0.7) and the root ball r_root at the pivot
Robot frame, mm. Legs are written in their neutral pose (verify.py carries them per pose as motion.legs does).
"""
import os, sys, math, hashlib, pickle, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT, ROOT + "/cad", HERE + "/fitcheck", ROOT + "/tools"):
    if p not in sys.path: sys.path.insert(0, p)
from build123d import (Shape, Box, Cylinder, Sphere, Pos, Rot, Solid, Shell, Face, Wire, Compound, Vector, Align,
                       export_step, export_stl, import_brep, export_brep, extrude, Plane, Polygon)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Pnt, gp_Dir
from scipy.spatial import ConvexHull, cKDTree
import fit_env as FE                    # S, P (motion lengths x S/0.60), PIV, A_ALL (cranks 2/3 D23 patch), inside()
from cad import design, fits as F
import timebudget as _tb
motion = FE.motion
class _Layout:
    """the fit check's numbers, read from check.py's source (importing it would run the 8-minute check): LAYOUT
    first, then each E("NAME", default) and the plain constants it uses."""
    def __init__(self):
        import re, ast
        src = open(os.path.join(HERE, "fitcheck", "check.py")).read()
        blk = re.search(r"LAYOUT = dict\((.*?)\)\n", src, re.S).group(1)
        lay = {k: v for k, v in re.findall(r"(\w+)=([-\d.]+)", blk)}
        for m in re.finditer(r'E\("(\w+)",\s*([-\d.]+)\)', src): setattr(self, m.group(1), float(m.group(2)))
        for k in ("PINR", "W", "HUBCUT", "GW", "WEB_T"):
            setattr(self, k, float(re.search(rf"\b{k} = ([\d.]+)", src).group(1)))
        for k, v in lay.items(): setattr(self, k, float(v))
        TH = F.GEAR_THRUST_CRANK.side; wb1 = self.GW / 2 + TH + self.W + TH + self.WEB_T
        self.LSL = (P["XC"] + self.PINX) - wb1 + 1.0
CL = None
BA, BO, EY, LB = design("base"), design("body"), design("eyes"), design("legs")
S, P, PIV, A_ALL, ORIGIN = FE.S, FE.P, FE.PIV, FE.A_ALL, motion.ORIGIN
CL = _Layout()
OUT = os.path.join(HERE, "out"); CACHE = os.path.join(OUT, ".cache"); os.makedirs(CACHE, exist_ok=True)

# ---- numbers (sources in the comments; nothing typed that fits.py or the fit check holds)
BASE_WALL = FE.BASE_WALL_R              # mm robot: the base wall (BA.WALL x S, 0.84); no pads: the open-top windows carry no load
RN, WR = CL.RN, CL.WR                   # window: neck within RN of the pivot, dilated WR (LEG_PATH + sampling)
STRIP_X, STRIP_X2, STRIP_Y0, STRIP_Y1, STRIP_Z0, STRIP_Z1, STRIP_Z2 = 20.05, 19.25, 6.4, 12.8, 19.0, 23.65, 23.9   # body strip under the cell holder, cut away
WR_EXTRA = {4: 0.6}                     # leg 4: its window dilated 0.6 more (no path or crank pose cleared it, 24 poses tested); leg 0 clears the smooth front wall by 0.40 (no relief)
def wr_of(Lg): return WR + WR_EXTRA.get(Lg, 0.0)
RELD, BRELD, PKR = CL.RELD, CL.BRELD, CL.PKR   # arm-sweep pockets: base front relief, body rim notch, eye block
PKT = FE.PKT                            # back-sheet pocket (depth, |x|, z0, z1), Morante 2026-11-21
SNX, SNW, SNT, SNZ, RIBD, SNG = CL.SNX, CL.SNW, CL.SNT, CL.SNZ, CL.RIBD, CL.SNG
PINR = CL.PINR                          # printed crank pin r (Ø3)
END_R = PINR + F.TURN.side + CL.W       # leg end tube: bore TURN over the pin, wall W 1.2
# leg snap on the crank pin (option A, build-log N2 r00): a groove on the pin, a ring bead in the end tube's bore, an axial slit
# in the tube so it opens over the pin tip. The snap fit is fits.PRESS (assumed): coupon list, not printed now.
SNAP_NECK_R = 1.0                       # pin neck r in the groove (Ø2.0, brief: neck Ø >= 2.0)
SNAP_BW = 0.5                           # bead width (axial)
SNAP_END = 1.0                          # tube mouth past the pin tip (was 1.5: leg-1 and leg-2 tube ends came within 0.11)
SNAP_SLIT = 0.6                         # slit width (tangential)
def snap_bead_r(i): return SNAP_NECK_R + F.TURN.side + BORE_DRIFT[i]       # bead inner r: turns on the neck (TURN), bore axis drift as the bore
SNAP_MARGIN = F.TURN.side             # axial room each side of the bead's travel (TURN; 0.10 left crank x leg 0.06-0.09 over the poses; slide stays within RETAIN 1.25)
def snap_groove(i):
    """(x0, x1) of the pin groove (robot |x|, right side): the axial span the bead's inner edge sweeps where it is within the pin's
    shoulder radius (PINR), over the 24 poses (tilt of the tube on the pin and the leg's axial drift), plus SNAP_MARGIN a side."""
    P_, A0 = motion.neutral_leg(i, P, n=13)[:2]; A0 = np.asarray(A0, float); rb = snap_bead_r(i); lo = 1e9; hi = -1e9
    th = np.linspace(0, 2 * np.pi, 181)
    ring = np.array([[A0[0], A0[1] + r * np.cos(t), A0[2] + r * np.sin(t), 1.0] for r in (rb, (rb + PINR) / 2) for t in th])
    for k in range(24):
        Q = (leg_frame(i, k) @ ring.T).T[:, :3]
        rho = np.hypot(Q[:, 1] - A_ALL[i, k][1], Q[:, 2] - A_ALL[i, k][2]); m = rho < PINR
        if m.any(): lo = min(lo, Q[m, 0].min() - SNAP_BW / 2); hi = max(hi, Q[m, 0].max() + SNAP_BW / 2)
    return round(float(lo - SNAP_MARGIN), 2), round(float(hi + SNAP_MARGIN), 2)
TAIL, HUBCUT = CL.TAIL, CL.HUBCUT       # tail past the pin (m21), real arm kept from HUBCUT past the pin
KEEL_BOSS_R = 3.0                       # keel boss radius: counterbore (M2 head 1.9 + STEEL) + 0.95 of wall
PB = P["r_root"]                        # root ball radius at the pivot
RIMR = (BO.Z_RIM - ORIGIN[2]) * S       # body rim height, robot
def pin_swing(i):
    """largest angle (deg) between the crank pin (x) and the leg's neutral x over the 24 poses, in the leg's frame."""
    a = 0.0
    for k in range(24):
        Ti = np.linalg.inv(leg_frame(i, k)); d = Ti[:3, :3] @ [1.0, 0, 0]; a = max(a, math.degrees(math.acos(min(1, abs(d[0])))))
    return a
KC = 12                                 # body-on pose (plan step 17)

FLARE_DEG = None    # set below from pin_swing(): measured + 1 deg
# ---- helpers
def to_robot(sh):
    """jenscolt frame (100 %) -> robot frame: translate by -ORIGIN, scale S about the origin."""
    t = gp_Trsf(); t.SetScale(gp_Pnt(0, 0, 0), S); m = gp_Trsf(); m.SetTranslation(gp_Vec(*(-ORIGIN)))
    t.Multiply(m)
    return Solid(BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape())
def mirror_x(sh):
    t = gp_Trsf(); t.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)))
    return Solid(BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape())
def cached(name, key, fn):
    """BREP cache in out/.cache, keyed by a hash of key (inputs and parameters)."""
    h = khash(key); p = os.path.join(CACHE, f"{name}_{h}.brep"); H[name] = h
    t = time.time()
    if os.path.exists(p):
        sh = import_brep(p); _tb.log(name, time.time() - t, False); return sh
    _tb.start()
    with _tb.stage(name): sh = fn()
    export_brep(sh, p); _tb.log(name, time.time() - t, True); return sh
H = {}                                   # name -> hash of the last key a stage was cached under (the next stage chains on it)
def stamp(*rel): return [int(os.path.getmtime(os.path.join(ROOT, r))) for r in rel]
def srch(*fns):
    """short hash of the source of the functions a stage calls: an edit to another function leaves the stage's cache warm."""
    import inspect
    return hashlib.sha1("".join(inspect.getsource(f) for f in fns).encode()).hexdigest()[:10]
def khash(key): return hashlib.sha1(pickle.dumps(key)).hexdigest()[:12]
def fuse_all(shs):
    out = shs[0]
    for s in shs[1:]: out = out.fuse(s)
    return out

# ---- legs: one solid per leg, neutral pose (robot frame); right legs 0-3, left 4-7 their mirror
_LF = {}
def leg_frame(Lg, k):
    """4x4 that carries leg Lg's neutral-pose part to crank pose k (motion.legs: V' = P + (V - P) @ R0.T @ R_k).
    Memoised (a copy is returned): the checks ask for it ~11 000 times and each call rebuilt the leg's shape (9 s)."""
    if (Lg, k) not in _LF: _LF[(Lg, k)] = _leg_frame(Lg, k)
    return _LF[(Lg, k)].copy()
def _leg_frame(Lg, k):
    i = Lg % 4; right = Lg < 4
    P_, A0 = motion.neutral_leg(i, P, n=13)[:2]
    u0 = (P_ - A0) / np.linalg.norm(P_ - A0); R0 = motion.frame(u0[None])[0]
    A = A_ALL[Lg, k] * ([1, 1, 1] if right else [-1, 1, 1])
    u = (P_ - A) / np.linalg.norm(P_ - A); M = R0.T @ motion.frame(u[None])[0]
    T = np.eye(4); T[:3, :3] = M.T; T[:3, 3] = P_ - M.T @ P_
    if not right:
        Mx = np.diag([-1.0, 1, 1, 1]); T = Mx @ T @ Mx
    return T
def _leg_right(i):
    P_, A0, ang, pts, rad, ni = motion.neutral_leg(i, P, n=13)
    rd = np.array([np.cos(ang), np.sin(ang), 0.0]); across = np.cross([0, 0, 1.0], rd)
    bl = pts[ni + 13:][::-1]; bsp = [tuple(bl[round(j * 16 / 4)]) for j in range(5)]
    _, _, _, pts2, _, _ = motion.neutral_leg(i, P, n=201)
    up = pts2[ni:ni + 201]; sp0 = LB.arm_spine_local(); f = sp0.knots[1] / sp0.knots[2]
    asp = [A0, A0 + f * (P_ - A0), P_, up[100], up[-1]]
    blade, arm = LB.leg("L", bsp, asp, S, tuple(across))
    u = (P_ - A0) / np.linalg.norm(P_ - A0)
    # the hub (s < HUBCUT from the pin along u) is replaced by the end tube
    hs = Cylinder(60, HUBCUT + 20, align=(Align.CENTER, Align.CENTER, Align.MAX))
    hs = _along(hs, A0 + HUBCUT * u, u)
    arm = arm - hs
    th = math.radians(FLARE_DEG[i])                  # bore and tube flare: the pin's swing in the leg frame + 1 deg
    x0, xm, x1 = A0[0] - TAIL, A0[0], P["XC"] + CL.PINX + SNAP_END   # tail .. pin point .. past the pin tip
    def dcone(r):
        a = Cylinder(1, 1)
        from build123d import Cone
        c1 = Pos(x0, A0[1], A0[2]) * Rot(0, 90, 0) * Cone(r + (xm - x0) * math.tan(th), r, xm - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        c2 = Pos(xm, A0[1], A0[2]) * Rot(0, 90, 0) * Cone(r, r + (x1 - xm) * math.tan(th), x1 - xm, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return c1 + c2
    tube = dcone(END_R)
    bore = Pos(-0.01, 0, 0) * dcone(PINR + F.TURN.side + BORE_DRIFT[i])
    bore = bore + Pos(0.02, 0, 0) * dcone(PINR + F.TURN.side + BORE_DRIFT[i])
    joint = _along(Cylinder(P["r_inner"], HUBCUT - 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), A0 + 1.5 * u, u)
    ball = Pos(*P_) * Sphere(PB)
    rb = snap_bead_r(i)
    ring = Pos(xm - SNAP_BW / 2, A0[1], A0[2]) * Rot(0, 90, 0) * (Cylinder(PINR + F.TURN.side + BORE_DRIFT[i] + 0.4, SNAP_BW, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                                  - Cylinder(rb, SNAP_BW, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    leg = fuse_all([blade, arm, tube, joint, ball]) - bore
    uh = u - np.dot(u, [1.0, 0, 0]) * np.array([1.0, 0, 0]); uh = uh / np.linalg.norm(uh)             # the arm's side of the tube
    if sorted(x.volume for x in leg.solids())[-2:-1] and sorted(x.volume for x in leg.solids())[-2] > 30:     # a piece bigger than the hub's 12 mm3 sliver
        # the arm leaves the tube's flare cone (leg 2/6: u mostly along x), so the joint never reaches the wall and the tube came off
        # (r00: «leg-2's tube detached»). A strut from the wall at the tube's mouth to the joint axis ties them.
        xw = x1 - 0.3; rw = (rb + END_R) / 2 + (xw - xm) * math.tan(th) + 0.2
        W_ = np.array([xw, A0[1], A0[2]]) + rw * np.array([0, uh[1], uh[2]]) ; J_ = A0 + 6.0 * u
        v_ = J_ - W_; strut = _along(Cylinder(1.0, float(np.linalg.norm(v_)), align=(Align.CENTER, Align.CENTER, Align.MIN)), W_, v_)
        leg = fuse_all([leg, strut]) - bore
    leg = fuse_all([leg, ring])
    up_ = u - np.dot(u, [1.0, 0, 0]) * np.array([1.0, 0, 0]); up_ = -up_ / np.linalg.norm(up_)     # slit on the side away from the arm
    sx0 = x0 + 0.2
    slit = Box(x1 + 1 - sx0, SNAP_SLIT, END_R + 1.5, align=(Align.MIN, Align.CENTER, Align.MIN))     # x, tangent, radial
    slit = Pos(sx0, A0[1], A0[2]) * Rot(math.degrees(math.atan2(up_[2], up_[1])) - 90, 0, 0) * slit   # +z of the box -> up_
    leg = leg - (slit & tube)
    return one(leg)          # a 12 mm3 sliver of the cut hub dropped
def _along(sh, p0, u):
    """sh built along +z from the origin, turned onto u and moved to p0."""
    u = np.asarray(u, float) / np.linalg.norm(u); z = np.array([0, 0, 1.0]); v = np.cross(z, u); s = np.linalg.norm(v)
    if s > 1e-9:
        ang = math.degrees(math.atan2(s, np.dot(z, u))); t = gp_Trsf()
        from OCP.gp import gp_Ax1
        t.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(*(v / s))), math.radians(ang)); sh = Solid(BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape())
    return Pos(*p0) * sh
def leg(Lg):
    i = Lg % 4
    key = ("leg8", i, SNAP_END, SNAP_NECK_R, SNAP_BW, SNAP_SLIT, FLARE_DEG[i], BORE_DRIFT[i], CL.PINX, S, HUBCUT, TAIL, END_R, PB, stamp("cad/legs/build.py", "cad/motion.py"), FE.D23, FE.D23C,
           srch(_leg_right, _along))
    sh = cached(f"leg{i}", key, lambda: _leg_right(i))
    return sh if Lg < 4 else mirror_x(sh)

_LM = {}
def leg_mesh(Lg, samples=False):
    """leg Lg as a trimesh (neutral pose, robot frame), or its surface samples (cutters.LEG_STEP apart), cached as arrays
    beside its BREP: the checks and the designed cutters need its surface, not the solid (the 8 BREPs took 10.5 s)."""
    import trimesh
    i = Lg % 4
    if i not in _LM:
        leg(i); p = os.path.join(CACHE, f"legmesh{i}_{H[f'leg{i}']}.npz")
        if not os.path.exists(p):
            import cutters as CU
            from trimesh.remesh import subdivide_to_size
            m = CU.mesh_of(leg(i)); np.savez(p, v=m.vertices, f=m.faces, s=subdivide_to_size(m.vertices, m.faces, max_edge=CU.LEG_STEP)[0])
        _LM[i] = dict(np.load(p))
    d = _LM[i]; mx = np.array([-1.0, 1, 1]) if Lg >= 4 else np.ones(3)
    if samples: return d["s"] * mx
    return trimesh.Trimesh(d["v"] * mx, d["f"][:, ::-1] if Lg >= 4 else d["f"], process=False)
FLARE_DEG = [round(pin_swing(i) + 1.0, 1) for i in range(4)]
def bore_drift(i):
    """worst offset (mm, across the pin axis x) between the pin centre A_k and the bore axis the rigid leg carries over the 24
    poses: leg_frame keeps the pivot P fixed while |P - A| changes by SL, so the neutral A0 lands off the pin (smoke 2026-11-23:
    gaps 0.08 / 0.14 / 0.19 against TURN 0.25). The bore is widened by it: a loose leg on its pin is fine in this toy."""
    P_, A0 = motion.neutral_leg(i, P, n=13)[:2]; A0 = np.asarray(A0, float); w = 0.0
    for k in range(24):
        d = (leg_frame(i, k) @ np.r_[A0, 1.0])[:3] - A_ALL[i, k]; w = max(w, float(np.hypot(d[1], d[2])))
    return round(w + 0.01, 2)
BORE_DRIFT = [bore_drift(i) for i in range(4)]

_LV = {}
def leg_points(Lg, k, edge=0.8):
    """surface samples of leg Lg at pose k (robot frame), from its coarse tessellation (sampled once per leg)."""
    if (Lg, edge) not in _LV:
        sh = leg(Lg); V, Fc = sh.tessellate(0.2, 0.4); V = np.array([[v.X, v.Y, v.Z] for v in V])
        from trimesh.remesh import subdivide_to_size
        _LV[(Lg, edge)] = subdivide_to_size(V, np.array(Fc), max_edge=edge)[0]
    T = leg_frame(Lg, k); return _LV[(Lg, edge)] @ T[:3, :3].T + T[:3, 3]

def unify(sh, faces_only=False):
    """unify same-domain faces so coplanar fragments merge and the STL exports watertight. Default: clean() (on a copy: it
    also alters the shape it is called on), faces-only if that is invalid. faces_only: straight to faces-only (no edges);
    the base of 2026-11-23: clean() invalid, clean() of a copy valid but 18 open STL edges, faces-only 1 valid solid with a
    watertight STL (3124.2 -> 3120.3 mm3, the BSpline volume's noise)."""
    import copy
    if not faces_only:
        c = copy.deepcopy(sh).clean()
        if c.is_valid: return c
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    u = ShapeUpgrade_UnifySameDomain(sh.wrapped, False, True, True); u.Build(); c = Shape.cast(u.Shape())
    print(f"    [unify] faces-only, valid {c.is_valid}", flush=True)
    return c
def one(sh):
    """largest solid of a boolean result (a cut may leave slivers)."""
    ss = sh.solids(); return max(ss, key=lambda s: s.volume) if len(ss) > 1 else (ss[0] if ss else sh)

# ---- base
def back_pocket(inner=None):
    """back sheet PKT[0] outward in |x| <= PKT[1], z PKT[2..3], as a cup: the sheet moved out by the depth, with side,
    top and bottom walls of the wall's own thickness joining it to the bowl (moved out by more than the wall is thick,
    a bare sheet came loose: 265 mm3 dropped, 2026-11-23). Returns (cut on the cavity side, cup added on the scoop side)."""
    d = BASE_WALL / S; w = BASE_WALL; cx, cy = (BA.CX - ORIGIN[0]) * S, (BA.BACK_Y - ORIGIN[1]) * S
    rb_in, rb_out = (BA.BACK_R + d) * S, BA.BACK_R * S; dp, hx, z0, z1 = PKT
    # clip round the back sheet only (y cy - rb_in .. a few mm in front of it); it was y cy-30..cy, which misses the sheet
    # at S 0.70 (cy 82.4, sheet at y ~22-26), so the pocket was never cut (found by the volume check, 2026-11-22)
    clip = lambda m: Pos(0, cy - rb_in - 1.0, z0 - m) * Box(2 * (hx + m), 10.0, z1 - z0 + 2 * m, align=(Align.CENTER, Align.MIN, Align.MIN))
    ring = lambda r0, r1, m: (Pos(cx, cy, z0 - m) * (Cylinder(r1, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                     - Cylinder(r0, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))))
    cut = ring(rb_in - dp, rb_in, 0.0) & clip(0.0)
    add = ring(rb_out - dp, rb_in - 0.05, w) & clip(w)
    return cut, add
def snap_geometry():
    """front snap rib (base) and finger + hook (body) at x +-SNX, as check.py (innermost wall face yw from inside())."""
    out = []
    for sx in (1, -1):
        xc = sx * SNX; zz = np.arange(SNZ, RIMR - 0.3, 0.2); yy = np.arange(-40, -20, 0.05)
        yw = max(yy[FE.inside(np.c_[np.full(len(yy), xc), yy, np.full(len(yy), z)])].min() for z in zz)
        yf = yw + RIBD + SNG; x0, x1 = xc - SNW / 2, xc + SNW / 2
        bx = lambda a, b: Pos(*((np.array(a) + b) / 2)) * Box(*(np.array(b) - a))
        rib = bx(np.array([x0 - 0.5, yw - 0.6, SNZ + 0.9]), np.array([x1 + 0.5, yw + RIBD, SNZ + 1.9]))
        finger = bx(np.array([x0, yf, SNZ]), np.array([x1, yf + SNT, RIMR + 0.6]))
        hook = bx(np.array([x0, yw + F.WINDOW.side, SNZ]), np.array([x1, yf + 0.01, SNZ + 0.8]))
        out.append((rib, finger + hook, yw))
    return out
FING_Z0, FING_Z1, FING_IN = 24.5, 27.5, 1.2   # snap finger root: a block from z FING_Z0 to FING_Z1, FING_IN mm further out than the
# finger (-y), embedded in the body's front wall (inner face y -29.6 at z 26 .. -30.4 at 27.5 at x +-6, outer -33.7 .. -34.0)
def finger_root(fing):
    """the finger (top at z RIMR + 0.6) did not reach the body: its front wall starts at z 25.5 there (7.2 mm above the finger).
    Returns finger + a plate of its own section (x span, SNT thick on its back face) up to FING_Z0 and a block FING_IN
    further out (-y) to FING_Z1, embedded in the wall: one solid, to be fused into the body."""
    bb = fing.bounding_box(); x0, x1, y0, y1, z1 = bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.max.Z
    plate = Pos((x0 + x1) / 2, y1 - SNT / 2, (z1 - 0.3 + FING_Z0 + 0.3) / 2) * Box(x1 - x0, SNT, FING_Z0 + 0.3 - (z1 - 0.3))
    block = Pos((x0 + x1) / 2, (y1 - SNT - FING_IN + y1) / 2, (FING_Z0 + FING_Z1) / 2) * Box(x1 - x0, SNT + FING_IN, FING_Z1 - FING_Z0)
    return fing.fuse(plate, block).clean()
PANEL_T = CL.W                           # front panel thickness 1.2 (rules 3.2: PLA wall >= 1.2); the face sits in the body's outer 1.2, the finger plates (y +1.4 behind) stay free
PANEL_XW = 18.0                          # panel half-width: the arch (BO.CHIN[0] x S = 17.5) + 0.5, where the base's front wall meets the body rim (brief 2026-11-24: by |x| 18)
PANEL_M = 0.8                            # the panel's top follows the arch ellipse grown by this: it fuses into the wall round the arch (wall 3.2)
PANEL_RAY = 0.15                         # the outer face is the skin's y this far above the arch edge (step to the skin <= 0.4)
PANEL_BASE_TOP = ((0, 12.96), (4, 13.22), (8, 14.00), (12, 15.35), (14, 16.27), (16, 16.80), (18, 17.01))   # |x|, base front wall top z: measured on the base (robot frame, brief 2026-11-24); 18 = body rim RIMR
PANEL_GAP = F.LOCATOR.side               # fixed-part gap panel to base top (large parts keep LOCATOR 0.2)
def front_panel(b0):
    """closes the mouth at the front face: the skin's outer face over the chin arch (at the arch edge, y(x) of the skin just above
    it), swept straight down (z) to the base's front-wall top + PANEL_GAP; PANEL_T thick along the plan normal; one solid
    to be fused into the body (the arch edge, PANEL_M inside the wall)."""
    import cutters as CU
    m = CU.mesh_of(b0, 0.05, 0.3)
    cw, ch = BO.CHIN[0] * S, BO.CHIN[1] * S; cx = (BO.CX - ORIGIN[0]) * S
    ell = lambda x, g=0.0: RIMR + (ch + g) * math.sqrt(max(1 - (x / (cw + g)) ** 2, 0.0))
    xs = np.linspace(-PANEL_XW, PANEL_XW, 73)
    org = np.array([[x, -60.0, ell(x - cx) + PANEL_RAY if abs(x - cx) < cw else RIMR + 0.5] for x in xs])
    hit = m.ray.intersects_location(org, np.tile([0, 1, 0], (len(xs), 1)), multiple_hits=True)
    yo = np.full(len(xs), np.nan)
    for loc, ri in zip(hit[0], hit[1]):
        if np.isnan(yo[ri]) or loc[1] < yo[ri]: yo[ri] = loc[1]
    assert not np.isnan(yo).any(), "front_panel: a ray missed the skin"
    ax = np.abs(xs); c = np.polyfit(ax ** 2, yo, 4); yo = np.polyval(c, ax ** 2)       # smooth, symmetric
    sl = np.gradient(yo, xs); nr = np.sqrt(1 + sl ** 2)
    outer = [(x, y) for x, y in zip(xs, yo)]
    inner = [(x - PANEL_T * s / n, y + PANEL_T / n) for x, y, s, n in zip(xs, yo, sl, nr)][::-1]
    zl, zh = 12.0, ell(0, PANEL_M) + 0.5
    strip = extrude(Plane.XY.offset(zl) * Polygon(*(outer + inner), align=None), zh - zl)
    bt = lambda x: float(np.interp(abs(x), [a for a, _ in PANEL_BASE_TOP], [b for _, b in PANEL_BASE_TOP])) + PANEL_GAP
    top = [(x, ell(x - cx, PANEL_M)) for x in xs[::-1]]
    reg = extrude(Plane.XZ.offset(15) * Polygon(*([(x, bt(x)) for x in xs] + top), align=None), 30)
    return strip & reg
_T0 = [0.0]
def tick(msg):
    t = time.time(); print(f"    [shells] {msg}: {t - _T0[0]:.1f} s", flush=True); _T0[0] = t
def fuse_one(shs):
    """one solid from overlapping solids (a single multi-argument fuse)."""
    return shs[0] if len(shs) == 1 else shs[0].fuse(*shs[1:]).clean()
def base():
    """the base: jenscolt's bowl (cad/base, wall BASE_WALL) in the robot frame, the designed leg windows (cutters.py: one
    few-sided prism per leg), the back-sheet pocket, the front snap ribs and the keel's two M2 bosses. One fuse, one cut;
    then every leg is checked against it at its 24 poses and along its assembly path (cutters.leg_gaps)."""
    import cutters as CU, drive as DR
    from build123d import Plane, Polygon as BPoly, extrude
    _T0[0] = time.time()
    b0 = base_skin(); tick("skin")
    legs = {Lg: leg_mesh(Lg) for Lg in range(8)}
    W = CU.Windows(CU.mesh_of(b0, 0.02, 0.2), legs, leg_frame, PIV, A_ALL, wr_of, RN, b0.bounding_box().max.Z + 3.0,
                   samples={Lg: leg_mesh(Lg, samples=True) for Lg in range(8)}); tick("window outlines")
    def prism(poly, fr, dr):
        t, z, n = fr; pl = Plane(origin=tuple(n * dr[0]), x_dir=tuple(t), z_dir=tuple(n))
        return extrude(pl * BPoly(*[tuple(p) for p in CU.ccw(poly)], align=None), dr[1] - dr[0])
    pk_cut, pk_add = back_pocket()
    zf = b0.bounding_box().min.Z; cyl = lambda x, y, r, z0, z1: Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    adds = [pk_add] + [rib for rib, _, _ in snap_geometry()] + [cyl(x, y, KEEL_BOSS_R, zf + DR.BASE_FLOOR * 0.5, DR.ZKEEL0) for x, y, _, _ in DR.KEEL_SCREWS]
    cuts = [prism(*W.window(Lg)) for Lg in range(8)] + [pk_cut] \
        + [cyl(x, y, DR.M2_HEAD_R + F.STEEL.side, zf - 1.0, zf + zh) for x, y, zh, _ in DR.KEEL_SCREWS] \
        + [cyl(x, y, DR.M2_HOLE_R, zf + zh - 0.5, DR.ZKEEL0 + 1.0) for x, y, zh, _ in DR.KEEL_SCREWS]
    b = b0.fuse(*adds); tick(f"fuse {len(adds)}")
    b = b.cut(*cuts); tick(f"cut {len(cuts)}")
    ss = sorted(b.solids(), key=lambda x: -x.volume)
    for x in ss[1:]:
        bb = x.bounding_box(); print(f"    [base] dropped a loose piece of {x.volume:.2f} mm3 at {np.round([bb.min.X, bb.min.Y, bb.min.Z], 1).tolist()}..{np.round([bb.max.X, bb.max.Y, bb.max.Z], 1).tolist()}", flush=True)
    b = one(unify(ss[0], faces_only=True)); tick("unify")
    assert b.is_valid and len(b.solids()) == 1, f"base: valid {b.is_valid}, {len(b.solids())} solids"
    rows = CU.leg_gaps(CU.mesh_of(b, 0.02, 0.2), legs, leg_frame, PIV, A_ALL)
    for Lg, what, g, at in rows:
        need = 0.4 if what == "poses" else 0.0
        print(f"    [base] leg {Lg} {what:8s} min gap {g:.2f} at {at}{'  FAIL' if g <= need else ''}", flush=True)
    tick("leg gaps"); print(f"    [base] volume {b.volume:.1f} mm3, {len(b.faces())} faces, valid, 1 solid", flush=True)
    return b
def base_skin():
    """cad/base's bowl at wall BASE_WALL in the robot frame (6 s), kept as a BREP keyed by cad/base/build.py's text."""
    key = (hashlib.sha1(open(os.path.join(ROOT, "cad", "base", "build.py"), "rb").read()).hexdigest()[:12], BASE_WALL, S, srch(to_robot))
    p = os.path.join(CACHE, f"base_skin_{khash(key)}.brep")
    if os.path.exists(p): return import_brep(p)
    sh = to_robot(BA.build(1.0, wall=BASE_WALL / S)); export_brep(sh, p); return sh

# ---- leg x-stop: a post from the body wall that stops the leg sliding off its pin (plan leg-on-pin "-x window": the window is slid
# LSL along u for assembly, so it does not hold x). Found per right leg (left = mirror) from the leg's own samples.
XS_RP = 0.4                              # post radius (Ø0.8: two lines)
XS_EMB = 0.8                             # mm the post goes into the wall
XS_HIT = 0.9                             # the leg may move this far in its sliding direction before the post stops it (< 1 mm)
XS_GRID = 0.25
XS_NCAND, XS_REACH = 1500, 10.0           # candidate free ends tried (nearest the wall first) and the wall reach for the post's other end
def xstop_post(Lg, near):
    """(a, b) end points of leg Lg's stop post (Lg 0..3, sliding +x): a free end in the +x shadow of the leg's neutral pose,
    b inside the wall. The post keeps LEG_PATH (+ its radius) from the leg over the 24 poses and from every other leg, and
    NEIGHBOUR from the leg at the lift pose KC slid down by LIFTD (the body lifts off over the posts). None if no post fits."""
    import trimesh
    P_ = PIV[Lg]; sh = leg(Lg); V, Fc = sh.tessellate(0.1, 0.3); V = np.array([[v.X, v.Y, v.Z] for v in V])
    T = leg_frame(Lg, 0); m0 = trimesh.Trimesh(V @ T[:3, :3].T + T[:3, 3], np.array(Fc))
    c24 = cKDTree(np.vstack([leg_points(Lg, k, edge=0.4) for k in range(24)]))
    q = leg_points(Lg, KC, edge=0.4); lift = cKDTree(np.vstack([q - [0, 0, t] for t in np.arange(0, CL.LIFTD + 0.01, 0.5)]))
    oth = cKDTree(np.vstack([leg_points(L, k, edge=0.8) for L in range(8) if L != Lg for k in range(0, 24, 2)]))
    q0 = leg_points(Lg, 0, edge=0.3); rl = F.NEIGHBOUR.side + 0.1; lp = F.LEG_PATH.side
    g = np.arange(-9, 9.01, XS_GRID); X, Y, Z = np.meshgrid(g, g, g, indexing="ij"); pts = np.c_[X.ravel(), Y.ravel(), Z.ravel()] + P_
    d24 = c24.query(pts)[0]; pts = pts[d24 >= lp + XS_RP + 0.02]
    sh_ = np.zeros(len(pts), bool)
    for t in (0.6, 0.8, 1.0, 1.2): sh_ |= m0.contains(pts - [t, 0, 0])
    R = pts[sh_]; R = R[(lift.query(R)[0] >= rl + XS_RP) & (oth.query(R)[0] >= lp + XS_RP)]
    kn = cKDTree(near); dw = kn.query(R)[0]; order = np.argsort(dw)
    for i in order[:XS_NCAND]:
        a = R[i]
        for j in kn.query_ball_point(a, XS_REACH)[::7][:60]:
            w = near[j]; dr = (w - a) / np.linalg.norm(w - a); b = w + XS_EMB * dr; path = a + np.linspace(0, 1, 16)[:, None] * (b - a)
            if (c24.query(path)[0] < lp + XS_RP).any() or (lift.query(path)[0] < rl + XS_RP).any() or (oth.query(path)[0] < lp + XS_RP).any(): continue
            ab = b - a; hit = None
            for t in np.arange(0, 3.01, 0.05):
                pp = q0 + [t, 0, 0]; u_ = np.clip(((pp - a) @ ab) / (ab @ ab), 0, 1)
                if np.linalg.norm(pp - (a + u_[:, None] * ab), axis=1).min() < XS_RP: hit = t; break
            if hit is not None and hit <= XS_HIT: return a, b, hit
    return None
def post_solid(a, b, r=XS_RP):
    a, b = np.asarray(a, float), np.asarray(b, float); L = np.linalg.norm(b - a)
    return one(_along(Cylinder(r, L, align=(Align.CENTER, Align.CENTER, Align.MIN)), a, (b - a) / L).fuse(Pos(*a) * Sphere(r)).clean())

# ---- body
EYES = [(BO.CX - BO.EYE_DX, -50.0, BO.EYE_Z, "eye"), (BO.CX + BO.EYE_DX, -50.0, BO.EYE_Z, "eye"),     # x, back y, z
        (BO.CX - BO.SEYE_DX, -44.0, BO.SEYE_Z, "small-eye"), (BO.CX + BO.SEYE_DX, -44.0, BO.SEYE_Z, "small-eye")]
# back y -50 / -44: the archived tools/assemble_jenscolt.py (flat face back, dome forward). jenscolt's front sensor (a dome
# on a stem in the mouth) is not placed: it held a sensor in his toy, here it did nothing (Morante, 2026-11-24)
def eye_cups():
    cups = []
    for x, yb, z, n in EYES:
        c = EY.cup(**dict(EY.CUPS[n], C=(0, 0, 0))); R, L = EY.CUPS[n]["R"], EY.CUPS[n]["L"]
        if n == "eye":                                          # collar to the bore wall: the cup is held by the body
            c = c + Pos(0, L - 1.0, 0) * Rot(-90, 0, 0) * (Cylinder(BO.EYE_BORE_R + 0.1, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                           - Cylinder(R - 0.3, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cups.append(Pos(x, yb - L, z) * c)
    return cups
LED_R = 2.5                                  # 5 mm LED (datasheet: Ø5 body, flange Ø5.8 x 1): the bore is LED_R + TURN a side, the floor's back face stops the flange
SW_THROW = 1.5                               # SS12D00 lever travel between positions: 1.5 mm (the usual SS12D00 pitch; hardware.md gives no figure)
SW_SLOT_Y = 12.0                             # lever slot length along y (through the back wall)
SW_KEEP_REACH = 0.0                          # keeper ribs/top bar reach this far behind the switch's back face (the switch sits embedded in the wall: they end on that face, inside the skin)
W_KEEP = 1.2                                 # keeper wall (loaded, rules 3.2)
def led_pos(sx):
    """LED sx (+-1) axis point on the big eye's bore floor, robot frame (check.py: ex, ey, ez)."""
    return sx * BO.EYE_DX * S, (BO.EYE_BORE_BACK - ORIGIN[1]) * S, (BO.EYE_Z - ORIGIN[2]) * S
LEDB0, LEDB1 = 0.3, 1.3  # LED through-bore: from 0.3 behind the bore floor to 1.3 past it (cavity face is 0.7 past, ray scan of body.stl)
LEDF = 0.7                                   # the bore floor's back (cavity) face, behind led_pos's y (ray scan of body.stl): the LED's flange stops on it
XS_POSTS = {0: ((34.288, -22.683, 19.65), (29.073, -15.758, 26.0)),    # leg x-stop posts (free end a, end in the wall b), found
            3: ((27.013, 18.242, 16.65), (24.305, 8.136, 17.04))}     # once by xstop_post (60-100 s a leg, 2026-11-23: the leg moves
                                                                       # 0.70 / 0.75 before its post stops it; none fits legs 1 and 2).
                                                                       # Re-run xstop_post by hand only if the legs or the body wall move.
def body_skin():
    """cad/body's shell in the robot frame (17-20 s), kept as a BREP keyed by cad/body/build.py's text."""
    key = (hashlib.sha1(open(os.path.join(ROOT, "cad", "body", "build.py"), "rb").read()).hexdigest()[:12], S, srch(to_robot))
    p = os.path.join(CACHE, f"body_skin_{khash(key)}.brep")
    if os.path.exists(p): return import_brep(p)
    sh = to_robot(BO.body(k=1.0)); export_brep(sh, p); return sh
def _file_key(*rel): return [hashlib.sha1(open(os.path.join(ROOT, r), "rb").read()).hexdigest()[:12] for r in rel]
def body_static():
    """what the body has whatever the legs do (cached BREP, keyed by the text of cad/body, cad/eyes, power.py and this
    function): the shell, the eye cups, the snap fingers, the switch keeper (one fuse); the tab's notch
    over the back pocket, the LED bores, the small eyes' vents, the lever slot, box pockets round the cell holder, lid,
    cells and switch (their bounding boxes + LOCATOR) and the strip under the holder (one cut)."""
    import power as PW
    key = (_file_key("cad/body/build.py", "cad/eyes/build.py", "cad/robot/power.py"), S, srch(body_static, body_skin, eye_cups, snap_geometry, finger_root, front_panel, led_pos, to_robot),
           PKT, SNX, SNW, SNT, SNZ, RIBD, SNG, PANEL_T, PANEL_XW, PANEL_M, PANEL_RAY, PANEL_BASE_TOP, PANEL_GAP, LEDB0, LEDB1, LED_R, SW_THROW, SW_SLOT_Y, SW_KEEP_REACH, W_KEEP, STRIP_X, STRIP_X2, STRIP_Y0, STRIP_Y1, STRIP_Z0, STRIP_Z1, STRIP_Z2)
    p = os.path.join(CACHE, f"body_static_{khash(key)}.brep")
    if os.path.exists(p) and os.path.exists(p + ".npz"):
        import trimesh
        d = np.load(p + ".npz"); return import_brep(p), trimesh.Trimesh(d["v"], d["f"], process=False)
    MIN = (Align.MIN, Align.MIN, Align.MIN)
    cylA = lambda p, r, L: Pos(*p) * Rot(-90, 0, 0) * Cylinder(r, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b0 = body_skin()
    cups = [to_robot(c) for c in eye_cups()]
    bx, by, bz = PW.SW_BODY; lx, ly, lz = PW.SW_LEVER; y1 = PW.SWY1; zs = PW.SWZ; st = F.STEEL.side
    yk = y1 - by - st; xk = bx / 2 + st; zb, zt = zs - bz / 2, zs + bz / 2 + st; yr = y1 + SW_KEEP_REACH
    keeper = [Pos(-xk - W_KEEP, yk, zt) * Box(2 * (xk + W_KEEP), yr - yk, W_KEEP, align=MIN)]       # top bar from the switch's front face back
    # (it overhung the front by W_KEEP: the fingertip that pushes the switch in touched it, verify 2026-11-23)
    keeper += [Pos(sx * (xk + W_KEEP / 2) - W_KEEP / 2, yk - W_KEEP, zb) * Box(W_KEEP, yr - yk + W_KEEP, zt - zb, align=MIN) for sx in (-1, 1)]
    adds = cups + [finger_root(f) for _, f, _ in snap_geometry()] + keeper + [front_panel(b0)]
    b = b0.fuse(*adds)
    tw, ty0, ty1, tz = BO.TAB; ty = (ty0 - ORIGIN[1]) * S; dp, hx, z0, z1 = PKT
    cuts = [Pos(0, ty - 1.0, z0 - 0.5) * Box(2 * hx + 1.0, dp + 1.0, z1 - z0 + 1.0, align=(Align.CENTER, Align.MIN, Align.MIN))]
    for sx in (-1, 1):
        x, y, z = led_pos(sx); cuts.append(cylA((x, y - LEDB0, z), LED_R + F.TURN.side, LEDB1 + LEDB0))
        cuts.append(cylA(((BO.CX + sx * BO.SEYE_DX - ORIGIN[0]) * S, (BO.SEYE_BACK - ORIGIN[1]) * S - LEDB0, (BO.SEYE_Z - ORIGIN[2]) * S), BO.SEYE_BORE * S, LEDB1 + LEDB0))
    cuts.append(Pos(-(lx / 2 + SW_THROW / 2 + st), y1 - 0.5, zs - lz / 2 - st) * Box(lx + SW_THROW + 2 * st, SW_SLOT_Y, lz + 2 * st, align=MIN))
    r = F.LOCATOR.side
    for part in (PW.holder(), PW.lid(), PW.cells(), PW.switch()):
        for so in part.solids():
            q = so.bounding_box(); cuts.append(Pos(q.min.X - r, q.min.Y - r, q.min.Z - r) * Box(q.size.X + 2 * r, q.size.Y + 2 * r, q.size.Z + 2 * r, align=MIN))
    cuts += [Pos(-STRIP_X, STRIP_Y0, STRIP_Z0) * Box(2 * STRIP_X, STRIP_Y1 - STRIP_Y0, STRIP_Z1 - STRIP_Z0, align=MIN),
             Pos(-STRIP_X2, STRIP_Y0 - 0.5, STRIP_Z0) * Box(2 * STRIP_X2, STRIP_Y1 - STRIP_Y0 + 0.5, STRIP_Z2 - STRIP_Z0, align=MIN)]
    b = b.cut(*cuts); export_brep(b, p)
    import cutters as CU
    m = CU.mesh_of(b, 0.05, 0.3); np.savez(p + ".npz", v=m.vertices, f=m.faces); return b, m
def body():
    """the body: its fixed features (body_static, cached), the legs' designed notches and pockets (cutters.body_cutters:
    one cut) and the frozen x-stop posts (one fuse). Then every leg is checked against it at its 24 poses and while the
    body is put on (cutters.body_gaps)."""
    import cutters as CU
    _T0[0] = time.time()
    b, bm = body_static(); tick("skin + fixed features")
    legs = {Lg: leg_mesh(Lg) for Lg in range(8)}
    lc = CU.body_cutters(bm, {Lg: leg_mesh(Lg, samples=True) for Lg in range(8)}, leg_frame, PIV,
                         BRELD, F.NEIGHBOUR.side + 0.1, KC, CL.LIFTD, RIMR); tick(f"{len(lc)} leg cutters")
    from build123d import Plane, Polygon as BPoly, extrude
    def prism(poly, fr, dr):
        t, z, n = fr; pl = Plane(origin=tuple(n * dr[0]), x_dir=tuple(t), z_dir=tuple(n))
        return extrude(pl * BPoly(*[tuple(p) for p in CU.ccw(poly)], align=None), dr[1] - dr[0])
    for poly, fr, dr, what in lc: print(f"    [body] {what}: {len(poly.exterior.coords) - 1} sides, {dr[1] - dr[0]:.1f} deep", flush=True)
    cuts = [prism(*x[:3]) for x in lc]
    b = b.cut(*cuts); tick(f"cut {len(cuts)}")
    ss = sorted(b.solids(), key=lambda x: -x.volume)
    for x in ss[1:]:
        q = x.bounding_box(); print(f"    [body] dropped a loose piece of {x.volume:.2f} mm3 at {np.round([q.min.X, q.min.Y, q.min.Z], 1).tolist()}..{np.round([q.max.X, q.max.Y, q.max.Z], 1).tolist()}", flush=True)
    b = ss[0]
    posts = [post_solid(*XS_POSTS[i]) for i in sorted(XS_POSTS)]; posts += [mirror_x(p) for p in posts]
    if posts: b = b.fuse(*posts); tick(f"fuse {len(posts)} stop posts")
    b = one(unify(b, faces_only=True)); tick("unify")
    assert b.is_valid and len(b.solids()) == 1, f"body: valid {b.is_valid}, {len(b.solids())} solids"
    for Lg, what, g, at in CU.body_gaps(CU.mesh_of(b, 0.05, 0.3), legs, leg_frame, KC, CL.LIFTD):
        need = 0.2 if what == "poses" else 0.1
        print(f"    [body] leg {Lg} {what:8s} min gap {g:.2f} at {at}{'  FAIL' if g < need else ''}", flush=True)
    tick("leg gaps"); print(f"    [body] volume {b.volume:.1f} mm3, {len(b.faces())} faces, valid, 1 solid", flush=True)
    return b

PARTS = {"base": base, "body": body, **{f"leg-{Lg}": (lambda Lg=Lg: leg(Lg)) for Lg in range(8)}}
