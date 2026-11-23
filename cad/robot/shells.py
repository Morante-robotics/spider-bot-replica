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
import os, sys, math, hashlib, pickle
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT, ROOT + "/cad", HERE + "/fitcheck"):
    if p not in sys.path: sys.path.insert(0, p)
from build123d import (Shape, Box, Cylinder, Sphere, Pos, Rot, Solid, Shell, Face, Wire, Compound, Vector, Align,
                       export_step, export_stl, import_brep, export_brep)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Pnt, gp_Dir
from scipy.spatial import ConvexHull, cKDTree
import fit_env as FE                    # S, P (motion lengths x S/0.60), PIV, A_ALL (cranks 2/3 D23 patch), inside()
from cad import design, fits as F
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
WALL_PAD = 1.2                          # mm robot, plan: pads 1.2 where loaded (rules §3.2), base wall is BA.WALL x S
RN, WR = CL.RN, CL.WR                   # window: neck within RN of the pivot, dilated WR (LEG_PATH + sampling)
STRIP_X, STRIP_X2, STRIP_Y0, STRIP_Y1, STRIP_Z0, STRIP_Z1, STRIP_Z2 = 20.05, 19.25, 6.4, 12.8, 19.0, 23.65, 23.9   # body strip under the cell holder, cut away
WR_EXTRA = {4: 0.6}                     # leg 4: its window dilated 0.6 more (no path or crank pose cleared it, 24 poses tested); leg 0's block is the front relief (PATH_DROP)
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
_ICO = np.array([[0, 1, 1.618], [0, -1, 1.618], [0, 1, -1.618], [0, -1, -1.618], [1, 1.618, 0], [-1, 1.618, 0],
                 [1, -1.618, 0], [-1, -1.618, 0], [1.618, 0, 1], [-1.618, 0, 1], [1.618, 0, -1], [-1.618, 0, -1]])
_ICO = _ICO / np.linalg.norm(_ICO[0]) / 0.7947       # circumscribes the unit sphere (inradius 1)
_K = 200
_EXC = 0.08
def _fib(K):
    i = np.arange(K) + 0.5; ph = np.arccos(1 - 2 * i / K); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph), np.cos(ph)]
def plane_data(pts, r, K=None):
    """support-plane polytope of pts grown by r: K Fibonacci directions d, h(d) = max(pts.d) + r (exact support of
    pts + ball r), so it always contains pts + ball r. Returns (vertices, faces as vertex-index loops)."""
    from scipy.spatial import HalfspaceIntersection
    K = K or _K; pts = np.asarray(pts, float); ch = ConvexHull(pts); pts = pts[ch.vertices]
    D = _fib(K); eq = ConvexHull((pts[:, None, :] + r * _ICO[None]).reshape(-1, 3)).equations   # the icosahedron hull's planes
    for it in range(20):                   # add the facet normal of conv(pts) wherever a vertex pokes > _EXC out of the true grown hull
        hh = (pts @ D.T).max(0) + r; hs = HalfspaceIntersection(np.c_[D, -hh], pts.mean(0))
        viol = hs.intersections @ eq[:, :3].T + eq[:, 3]; vm = viol.max(1)
        bad = vm > _EXC
        if not bad.any(): break
        nd = np.unique(np.round(eq[viol[bad].argmax(1), :3] / 0.002).astype(int), axis=0) * 0.002
        nd = nd / np.linalg.norm(nd, axis=1)[:, None]; D = np.vstack([D, nd])
    else:
        hh = (pts @ D.T).max(0) + r; hs = HalfspaceIntersection(np.c_[D, -hh], pts.mean(0))
    K = len(D)
    X = hs.intersections; key = np.round(X / 1e-5).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel(); V = X[first]
    loops = []
    per = [set() for _ in range(K)]
    for j, df in enumerate(hs.dual_facets):
        for i in df: per[i].add(int(inv[j]))
    for i in range(K):
        ids = sorted(per[i])
        if len(ids) < 3: continue
        P = V[ids]; n = D[i]; u = np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u); w = np.cross(n, u)
        m = P.mean(0); ang = np.arctan2((P - m) @ w, (P - m) @ u); loops.append([ids[k] for k in np.argsort(ang)])
    return V, loops
def plane_solid(pts, r, K=None):
    V, loops = plane_data(pts, r, K)
    faces = [Face(Wire.make_polygon([Vector(*V[k]) for k in lp], close=True)) for lp in loops]
    return Solid(Shell(faces))
def hull_solid(pts, r=0.0):
    """convex polyhedron round pts, grown by r (Minkowski with an icosahedron that holds a sphere of radius r)."""
    pts = np.asarray(pts, float)
    if r > 0: pts = (pts[:, None, :] + r * _ICO[None]).reshape(-1, 3)
    h = ConvexHull(pts); c = pts[h.vertices].mean(0); faces = []
    for s in h.simplices:
        a, b, d = pts[s]
        if np.dot(np.cross(b - a, d - a), a - c) < 0: b, d = d, b
        faces.append(Face(Wire.make_polygon([Vector(*a), Vector(*b), Vector(*d)], close=True)))
    return Solid(Shell(faces))
def cached(name, key, fn):
    """BREP cache in out/.cache, keyed by a hash of key (inputs and parameters)."""
    h = khash(key); p = os.path.join(CACHE, f"{name}_{h}.brep"); H[name] = h
    if os.path.exists(p): return import_brep(p)
    sh = fn(); export_brep(sh, p); return sh
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
def leg_frame(Lg, k):
    """4x4 that carries leg Lg's neutral-pose part to crank pose k (motion.legs: V' = P + (V - P) @ R0.T @ R_k)."""
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
_LP = {}
def LP(Lg, k):
    if (Lg, k) not in _LP: _LP[(Lg, k)] = leg_points(Lg, k)
    return _LP[(Lg, k)]

# ---- sweep cutters (hulls of the legs' samples, chunked along the leg and over 3 poses each)
PATH_DROP = 30.0                         # verify.py LEG_DROP: the leg is lowered this far beside its pin, then slid in by LSL
PATH_RELIEF = {0: True}                  # legs whose front relief also clears the assembly path's down move (leg 4 clears without)
def path_samples(Lg, k=0, step=1.0):
    """leg Lg's samples (crank pose k, the bench placement) along the down move of its assembly path: LSL outboard, 0..PATH_DROP above."""
    u = PIV[Lg] - A_ALL[Lg, 0]; u /= np.linalg.norm(u); q = LP(Lg, k) + u * CL.LSL
    return [q + [0, 0, t] for t in np.arange(0, PATH_DROP + 0.01, step)]
def sweep_hulls(near, r, legs=range(8), poses=range(24), group=3, cell=3.0, rn=None, lift=0.0, planes=False, reach=None, path=False):
    """convex hulls (grown by r) covering the legs' sweep where it comes within r + 1 of the samples `near`.
    rn: only samples within rn of the pivot (window neck); lift: also slide the samples down by lift (body lift-off).
    reach: keep samples within reach of `near` (default r + 1): a cutter that must cover every sample another cutter (a bulge
    grown further) covers takes that cutter's reach."""
    tn = cKDTree(near); hulls = []
    for Lg in legs:
        groups = [[LP(Lg, k % 24) for k in list(poses)[g0:g0 + group + 1]] for g0 in range(0, len(poses), group)]
        if path:                                                # + the assembly path's down move (path_samples), same chunks
            ps = path_samples(Lg); groups += [ps[g0:g0 + group + 1] for g0 in range(0, len(ps), group)]
        for Q in groups:
            if rn is not None: Q = [q[np.linalg.norm(q - PIV[Lg], axis=1) <= rn] for q in Q]
            q = np.vstack(Q)
            if lift > 0: q = np.vstack([q - [0, 0, t] for t in np.arange(0, lift + 0.01, 1.0)])
            d = tn.query(q, distance_upper_bound=(r + 1.0) if reach is None else reach)[0]; q = q[np.isfinite(d)]
            if len(q) < 8: continue
            cid = np.floor(q / cell).astype(int); _, inv = np.unique(cid, axis=0, return_inverse=True)
            for c in range(inv.max() + 1):
                qc = q[inv.ravel() == c]
                if len(qc) >= 4:
                    try: hulls.append(plane_solid(qc, r) if planes else hull_solid(qc, r))
                    except Exception: pass
    return hulls
def samples(sh, tol=0.3):
    V, _ = sh.tessellate(tol, 0.5); return np.array([[v.X, v.Y, v.Z] for v in V])
DENSE = 1.0                              # mm: surface sample spacing of the `near` cloud of the sweep cutters (see dense())
def dense(sh, edge=DENSE, tol=0.3):
    """surface samples of sh at most `edge` mm apart. samples() are the tessellation's vertices only (a flat wall has a
    vertex every 4-9 mm): sweep_hulls keeps a leg sample only within r + 1 of `near`, so with that cloud the samples of a leg
    in mid-face (2.3-4.7 mm from the nearest vertex) were never in a hull and the wall kept them (smoke 2026-11-22: base x
    legs 0/4 91/28 mm3, body x legs up to 20 mm3, while the point-cloud fit check, which has every wall point, gave 0 failing)."""
    from trimesh.remesh import subdivide_to_size
    V, Fc = sh.tessellate(tol, 0.5); V = np.array([[v.X, v.Y, v.Z] for v in V])
    return subdivide_to_size(V, np.array(Fc), max_edge=edge)[0]
def cut_many(sh, tools, batch=40):
    for j in range(0, len(tools), batch):
        sh = sh.cut(Compound(tools[j:j + batch]))
    return sh
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
def window_cutter(Lg):
    """open-top window of leg Lg: its neck (RN of the pivot) over 24 poses, slid LSL off the pin, pushed up past the
    rim, grown by WR; one convex hull per 3-pose group."""
    u = PIV[Lg] - A_ALL[Lg, 0]; u /= np.linalg.norm(u); ZTOP = RIMR + 1.0; LSL = CL.LSL; hulls = []
    for g0 in range(0, 24, 3):
        q = np.vstack([LP(Lg, k % 24) for k in range(g0, g0 + 4)]); q = q[np.linalg.norm(q - PIV[Lg], axis=1) <= RN]
        q = np.vstack([q + t * u for t in np.linspace(0, LSL, 4)])
        q = np.vstack([q, q + [0, 0, ZTOP - q[:, 2].min()]])
        hulls.append(plane_solid(q, wr_of(Lg)))
    return hulls
def back_pocket(inner):
    """back sheet 1.6 outward in |x| <= PKT[1], z PKT[2..3]: cut on the cavity side, the same added on the scoop side."""
    d = BA.WALL; cx, cy = (BA.CX - ORIGIN[0]) * S, (BA.BACK_Y - ORIGIN[1]) * S
    rb_in, rb_out = (BA.BACK_R + d) * S, BA.BACK_R * S; dp, hx, z0, z1 = PKT
    # clip round the back sheet only (y cy - rb_in .. a few mm in front of it); it was y cy-30..cy, which misses the sheet
    # at S 0.70 (cy 82.4, sheet at y ~22-26), so the pocket was never cut (found by the volume check, 2026-11-22)
    clip = Pos(0, cy - rb_in - 1.0, z0) * Box(2 * hx, 10.0, z1 - z0, align=(Align.CENTER, Align.MIN, Align.MIN))
    ring = lambda r0, r1: (Pos(cx, cy, z0) * (Cylinder(r1, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                               - Cylinder(r0, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))))
    cut = ring(rb_in - dp, rb_in) & clip
    add = ring(rb_out - dp, rb_out) & clip
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
_T0 = [0.0]
def tick(msg):
    import time
    t = time.time(); print(f"    [base] {msg}: {t - _T0[0]:.1f} s", flush=True); _T0[0] = t
def fuse_one(shs):
    """one solid from overlapping solids (a single multi-argument fuse)."""
    return shs[0] if len(shs) == 1 else shs[0].fuse(*shs[1:]).clean()
RCELL = 6.0
def tree_fuse(shs):
    """overlapping solids fused pairwise, then pairs of pairs (never one Compound tool)."""
    shs = list(shs)
    while len(shs) > 1:
        shs = [shs[i].fuse(shs[i + 1]).clean() if i + 1 < len(shs) else shs[i] for i in range(0, len(shs), 2)]
    return shs[0]
def leg_window(Lg):
    """leg Lg's window cutter as one solid (its 8 hulls fused), cached by its inputs."""
    key = ("win", Lg, S, RN, wr_of(Lg), CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py"),
           srch(window_cutter, plane_solid, plane_data, _fib, leg_points, leg_frame, fuse_one))
    return cached(f"win{Lg}", key, lambda: fuse_one(window_cutter(Lg)))
def leg_ring(Lg):
    """leg Lg's pad ring (its window cutter's support polytope grown 1.5), cached by its inputs."""
    key = ("ring", Lg, S, RN, wr_of(Lg), CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py"),
           srch(window_cutter, plane_solid, plane_data, _fib, leg_points, leg_frame, fuse_one, samples))
    return cached(f"ring{Lg}", key, lambda: plane_solid(samples(leg_window(Lg)), 1.5))
def local_box(tools, m=10.0):
    """axis box round the union bbox of tools, m mm wider on every side (fully contains the tools)."""
    bbs = [t.bounding_box() for t in tools]
    lo = np.min([[q.min.X, q.min.Y, q.min.Z] for q in bbs], axis=0) - m; hi = np.max([[q.max.X, q.max.Y, q.max.Z] for q in bbs], axis=0) + m
    return Pos(*((lo + hi) / 2)) * Box(*(hi - lo))
VTOL = 0.03                              # volume invariant: removed / added vs the intersection, 3 % (GProp on the
                                         # BSpline skin is ~1 % noisy: pads leg 4 +227.3 vs +224.5; real failures were 50-100 %)
VABS = 5.0                               # mm3 floor under the 3 % (small overlaps)
def pvol(sh, eps=1e-6):
    """exact-tolerance volume: Shape.volume integrates the BSpline skin about 0.5 % off (base 3934.9 vs 3953.4 mm3)."""
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(sh.wrapped, g, eps, False, False); return g.Mass()
def _bool(kind, a, b, fuzz=0.0):
    """one OCCT boolean (cut / fuse / and) of a and b with an optional fuzzy value."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
    from OCP.collections import List_TopoDS_Shape as TopTools_ListOfShape
    from build123d import Shape
    op = {"cut": BRepAlgoAPI_Cut, "fuse": BRepAlgoAPI_Fuse, "and": BRepAlgoAPI_Common}[kind]()
    A = TopTools_ListOfShape(); A.Append(a.wrapped); B = TopTools_ListOfShape(); B.Append(b.wrapped)
    op.SetArguments(A); op.SetTools(B); op.SetRunParallel(True)
    if fuzz: op.SetFuzzyValue(fuzz)
    op.Build()
    if not op.IsDone(): raise RuntimeError(f"boolean {kind} failed (fuzz {fuzz})")
    return Shape.cast(op.Shape())
def _close(got, want): return abs(got - want) <= VTOL * abs(want) + VABS
def checked(kind, P, T, label, touch=True, m=10.0):
    """P cut/fused with T, the volume invariant enforced: cut removes vol(P & T); fuse adds vol(T) - vol(P & T), both
    within 1 %. A mismatch retries the op on a local piece with fuzzy 1e-4, then 1e-3, then on all of P at 1e-3;
    still wrong: raise. touch: a cut tool that does not meet P at all (< 1 mm3) is an error too."""
    v0 = pvol(P); vt = pvol(T); bx = local_box([T], m)
    inter = 0.0                                                           # the reference overlap, on the local piece:
    for f in (0.0, 1e-4):                                                 # fuzzy 0 first (fuzzy 1e-4 gave 0 mm3 for
        inter = pvol(_bool("and", _bool("and", P, bx, f), T, f))          # window 1, which meets the base in 226.8)
        if inter >= 1.0: break
    if touch and inter < 1.0: raise RuntimeError(f"[{label}] {kind}: tool meets the part in only {inter:.3f} mm3")
    exp = -inter if kind == "cut" else vt - inter
    last = None
    for att, (loc, f) in enumerate([(True, 0.0), (True, 1e-4), (True, 1e-3), (False, 1e-3)]):
        try:
            if loc:
                piece = _bool("and", P, bx, f); rest = _bool("cut", P, bx, f); out = _bool("fuse", rest, _bool(kind, piece, T, f), f)
            else: out = _bool(kind, P, T, f)
        except RuntimeError as ex: last = str(ex); continue
        d = pvol(out) - v0; last = f"{d:+.2f} vs {exp:+.2f}"
        if out.is_valid and _close(d, exp):
            print(f"    [{label}] {kind}: {'removed' if kind == 'cut' else 'added'} {abs(d):.2f} mm3 (expected {abs(exp):.2f}, attempt {att})", flush=True)
            return out
    raise RuntimeError(f"[{label}] {kind}: volume change {last} mm3 after all retries")
def local_op(b, tools, fn, m=10.0):
    """fn(piece) applied to b's piece inside a box round tools only: b = (b - box) + fn(b & box). The skin's
    BSpline faces meet the tools' faces only inside the small piece, which is what makes the boolean cheap."""
    bx = local_box(tools, m); piece = b & bx; rest = b - bx
    new = fn(piece); want = pvol(rest) + pvol(new)
    for f in (0.0, 1e-4, 1e-3):
        out = _bool("fuse", rest, new, f); ss = out.solids()
        if len(ss) == 1 and out.is_valid and abs(pvol(out) - want) <= 1e-3 * want: return ss[0]
    raise AssertionError(f"local_op: {len(ss)} solids, valid {out.is_valid}, volume {pvol(out):.1f} vs {want:.1f}")
def _base():
    import time; _T0[0] = time.time()
    key0 = ("base", S, WALL_PAD, RN, WR, tuple(sorted(WR_EXTRA.items())), RELD, PKT, SNX, SNW, SNZ, RIBD, CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py"),
            srch(to_robot, checked, _bool, local_box, pvol, fuse_cut, one, back_pocket, snap_geometry, tree_fuse, dense, sweep_hulls, plane_solid, plane_data, _fib,
                 leg_points, leg_frame, window_cutter, leg_window, leg_ring, samples, fuse_one, _close, cut_many))
    b = to_robot(BA.build(1.0)); tick("base skin + cuts")
    wins = [leg_window(Lg) for Lg in range(8)]; tick("8 window cutters (cached per leg)")
    rings = [leg_ring(Lg) for Lg in range(8)]; tick("8 pad rings (cached per leg)")
    def pads_stage():
        # pads: the wall round each window thickened to WALL_PAD on the inside (outer skin unchanged); each piece is cut
        # from the wall inside its ring's own box, the 8 pieces are fused together, then into the base
        outer = to_robot(BA.skin(0.0, 1.0)); inner = to_robot(BA.skin(WALL_PAD / S, 1.0)); wall = outer - inner
        pcs = [(wall & local_box([r], 0.5)) & r for r in rings]; tick("8 pad pieces")
        c = b
        for Lg, pc in enumerate(pcs): c = checked("fuse", c, pc, f"pads leg {Lg}", touch=False)
        tick("pads into base")
        cut, add = back_pocket(None); c = checked("fuse", c, add, "pocket add", touch=False); c = checked("cut", c, cut, "pocket cut")
        for n, (rib, _, _) in enumerate(snap_geometry()): c = checked("fuse", c, rib, f"snap rib {n}", touch=False)
        tick("back pocket + snap ribs"); return one(c)
    b = cached("base_pads", key0 + ("pads", srch(pads_stage), H["win0"], H["ring0"]), pads_stage)
    def win_stage():
        c = b
        for side in (range(0, 4), range(4, 8)):         # checked() cuts each on its own local piece; a local_op round it
            c = fuse_cut(c, [(wins[Lg], f"window leg {Lg}") for Lg in side])   # nested two local pieces and gave an inside-out one
            tick(f"4 window cuts, side {side[0]}-{side[-1]}")
        return c
    b = cached("base_win", key0 + ("win", srch(win_stage), H["base_pads"]), win_stage)
    near = dense(b)                                             # front leg windows: pocket RELD from the front arms' sweep
    def relief_tools(Lg):
        """leg Lg's relief pocket solid and outward bulge solid (hull cell RCELL), each cached by its inputs."""
        kk = key0 + ("relief", Lg, RCELL, RELD, BA.WALL * S, H["base_win"], PATH_RELIEF.get(Lg, False), PATH_DROP)
        pth = PATH_RELIEF.get(Lg, False)
        def mk():
            rel = sweep_hulls(near, RELD, legs=(Lg,), planes=True, cell=RCELL, reach=RELD + BA.WALL * S + 1.0, path=pth)   # same samples as the bulge's hulls:
            # a leg sample inside the bulge but > RELD + 1 from the wall was left in it (relief cut 41 mm3, bulge 268 mm3 round the leg)
            grown = sweep_hulls(near, RELD + BA.WALL * S, legs=(Lg,), planes=True, cell=RCELL, path=pth)
            tick(f"leg {Lg} relief hulls: {len(rel)} + {len(grown)} grown, faces/hull {sorted(len(h.faces()) for h in rel + grown)[-1]} max")
            return rel, grown
        def rs_fn():
            rel, grown = mk(); rs = tree_fuse(rel); tick(f"leg {Lg} relief fused"); return rs
        rs = cached(f"relf{Lg}", kk + ("rs",), rs_fn)
        def gs_fn():
            rel, grown = mk(); return tree_fuse(grown)
        gs = cached(f"relg{Lg}", kk + ("gs",), gs_fn)
        outer = to_robot(BA.skin(0.0, 1.0)); bx = local_box([gs], 1.0)
        def bulge_fn():
            # the bulge (gs - outer) is the hull cutters' grown shell: the part of the leg between those hulls (samples that are
            # not within reach of the wall) is inside it too (smoke: 459 leg-0 samples at pose 0). Carve it with the sweep of
            # every leg sample within RELD + 1 of the bulge itself: it keeps RELD from the leg, like the relief.
            b0 = gs - (outer & bx); nb = dense(b0)
            return b0 - tree_fuse(sweep_hulls(nb, RELD, legs=(Lg,), planes=True, cell=RCELL, path=pth))
        bulge = cached(f"relb{Lg}", kk + ("bulge2",), bulge_fn); tick(f"leg {Lg} bulge")
        return rs, gs, bulge
    def relief_stage():
        c = b
        for Lg in (0, 4):                                       # one local box per front leg
            rs, gs, bulge = relief_tools(Lg)
            c = fuse_cut(c, [(rs, f"relief leg {Lg}")], add=(bulge, f"bulge leg {Lg}")); tick(f"leg {Lg} bulge + relief (local)")
        return c
    b = cached("base_relief", key0 + ("relief", _K, srch(relief_stage, relief_tools), H["base_win"]), relief_stage)
    b = one(b); ss = b.solids()
    assert len(ss) == 1 and b.is_valid and pvol(b) > 0, f"base: {len(ss)} solids, valid {b.is_valid}, volume {pvol(b)}"
    pv = []
    for Lg in range(8):
        bxl = Pos(*PIV[Lg]) * Box(14, 14, 18); pv.append(pvol(_bool("and", b, bxl)))
    for i in range(4):
        d = abs(pv[i] - pv[i + 4]) / max(pv[i], pv[i + 4])
        print(f"    [base] pivot box leg {i}: {pv[i]:.1f}  leg {i + 4}: {pv[i + 4]:.1f} mm3  diff {100 * d:.2f} %{'  WARN > 1 %' if d > 0.01 else ''}", flush=True)
    print(f"    [base] volume {pvol(b):.1f} mm3, valid, 1 solid", flush=True)
    return b
def fuse_cut(P, cuts, add=None):
    """P (+ add = (solid, label)), minus each of cuts in turn ((solid, label)), every op with its volume invariant."""
    if add is not None: P = checked("fuse", P, add[0], add[1], touch=False)
    for t, lab in cuts: P = checked("cut", P, t, lab)
    return P
def base():
    key = ("base", S, WALL_PAD, RN, WR, tuple(sorted(WR_EXTRA.items())), RELD, PKT, SNX, SNW, SNZ, RIBD, CL.LSL, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py"), srch(_base),
           srch(to_robot, checked, _bool, local_box, pvol, fuse_cut, one, back_pocket, snap_geometry, tree_fuse, dense, sweep_hulls, plane_solid, plane_data, leg_window, leg_ring))
    # the booleans leave coplanar fragments that touch along a line (28 non-manifold STL edges); unifying same-domain faces
    # merges them (volume unchanged, 1 valid solid) and the STL exports watertight. Outside the cache so the stages stay valid.
    b = one(unify(cached("base", key, _base), faces_only=True))
    assert b.is_valid and len(b.solids()) == 1, "base: clean() left it invalid"
    def keel_stage():
        """the keel's two M2 bosses (drive.py KEEL_SCREWS): a boss from the floor up to ZKEEL0 round each screw, the head's
        counterbore (STEEL a side) from the foot up to the head's bearing face, the shank's STEEL hole above it. After the
        clean(): clean() of a base with the bosses in it left an invalid shape (volume 18751 mm3)."""
        import drive as DR
        zf = b.bounding_box().min.Z; c = b; cyl = lambda x, y, r, z0, z1: Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for n, (x, y, zh, ln) in enumerate(DR.KEEL_SCREWS):
            c = checked("fuse", c, cyl(x, y, KEEL_BOSS_R, zf + DR.BASE_FLOOR * 0.5, DR.ZKEEL0), f"keel boss {n}", touch=True)
        for n, (x, y, zh, ln) in enumerate(DR.KEEL_SCREWS):
            c = checked("cut", c, cyl(x, y, DR.M2_HEAD_R + F.STEEL.side, zf - 1.0, zf + zh), f"keel counterbore {n}")
            c = checked("cut", c, cyl(x, y, DR.M2_HOLE_R, zf + zh - 0.5, DR.ZKEEL0 + 1.0), f"keel hole {n}")
        return c
    import drive as _DR
    b = one(cached("base_keel", ("base_keel", H["base"], srch(unify), "faces-only", srch(keel_stage, checked, _bool, local_box, pvol), KEEL_BOSS_R, _DR.KEEL_SCREWS, _DR.ZKEEL0, _DR.M2_HEAD_R,
                                 _DR.M2_HOLE_R, _DR.BASE_FLOOR), keel_stage))
    assert b.is_valid and len(b.solids()) == 1, "base: keel bosses left it invalid"
    return b

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
# back y -50 / -44: the archived tools/assemble_jenscolt.py (flat face back, dome forward); sensor where jenscolt put it
def eye_cups():
    cups = []
    for x, yb, z, n in EYES:
        c = EY.cup(**dict(EY.CUPS[n], C=(0, 0, 0))); R, L = EY.CUPS[n]["R"], EY.CUPS[n]["L"]
        if n == "eye":                                          # collar to the bore wall: the cup is held by the body
            c = c + Pos(0, L - 1.0, 0) * Rot(-90, 0, 0) * (Cylinder(BO.EYE_BORE_R + 0.1, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                           - Cylinder(R - 0.3, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cups.append(Pos(x, yb - L, z) * c)
    cups.append(EY.build("sensor"))
    return cups
LED_R = 2.5                                  # 5 mm LED (datasheet: Ø5 body, flange Ø5.8 x 1): the bore is LED_R + TURN a side, the floor's back face stops the flange
SW_THROW = 1.5                               # SS12D00 lever travel between positions: 1.5 mm (the usual SS12D00 pitch; hardware.md gives no figure)
SW_SLOT_Y = 12.0                             # lever slot length along y (through the back wall)
SW_KEEP_REACH = 0.0                          # keeper ribs/top bar reach this far behind the switch's back face (the switch sits embedded in the wall: they end on that face, inside the skin)
W_KEEP = 1.2                                 # keeper wall (loaded, rules 3.2)
def grow(part, r):
    """part grown by r: each solid offset by r (sharp corners, else rounded), else its bounding box grown by r."""
    from build123d import offset, Kind
    out = []
    for so in part.solids():
        for kind in (Kind.INTERSECTION, Kind.ARC):
            try:
                g = offset(so, amount=r, kind=kind)
                if g.is_valid and g.volume > so.volume: out.append(g); break
            except Exception: pass
        else:
            bb = so.bounding_box(); out.append(Pos((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2) *
                                               Box(bb.size.X + 2 * r, bb.size.Y + 2 * r, bb.size.Z + 2 * r))
            print(f"    [grow] solid {len(out)}: offset failed, bounding box grown by {r}", flush=True)
    return fuse_one(out)
def led_pos(sx):
    """LED sx (+-1) axis point on the big eye's bore floor, robot frame (check.py: ex, ey, ez)."""
    return sx * BO.EYE_DX * S, (BO.EYE_BORE_BACK - ORIGIN[1]) * S, (BO.EYE_Z - ORIGIN[2]) * S
LEDB0, LEDB1 = 0.3, 1.3  # LED through-bore: from 0.3 behind the bore floor to 1.3 past it (cavity face is 0.7 past, ray scan of body.stl)
LEDF = 0.7                                   # the bore floor's back (cavity) face, behind led_pos's y (ray scan of body.stl): the LED's flange stops on it
CRUMB = 0.1          # mm3: a loose solid under this left by a cut is dropped with a note (a 0.4 mm nozzle lays ~0.03 mm3 a mm)
def local_seq(P, ops, label, crumb=None):
    """ops = [(kind, tool, label, touch)] applied in turn to P, each on its own local piece: checked() sees only the piece
    (pvol of the whole BSpline skin costs about a minute), the piece goes back by one fuse with the rest. The whole
    volume is integrated only once, at the end of _body."""
    tot = 0.0
    for kind, T, lab, touch in ops:
        bx = local_box([T], 10.0); piece = _bool("and", P, bx); rest = _bool("cut", P, bx); vp = pvol(piece)
        new = checked(kind, piece, T, lab, touch=touch); dv = pvol(new) - vp
        for f in (0.0, 1e-4, 1e-3):                          # no whole-skin volume per op (pvol of the rest is 30 s)
            out = _bool("fuse", rest, new, f)
            ss = out.solids(); crumbs = [s for s in ss if s.volume < (CRUMB if crumb is None else crumb)]
            if crumbs and len(ss) - len(crumbs) == 1:            # a cut can leave a loose crumb between hulls (rim leg 3:
                print(f"    [{lab}] dropped {len(crumbs)} loose crumb(s), {sum(s.volume for s in crumbs):.3f} mm3", flush=True)
                out = max(ss, key=lambda s: s.volume)             # 0.01 mm3, 0.6 x 0.6 x 0.2 mm): not printable, said, not silent
            if len(out.solids()) == 1 and out.is_valid: break
        else: raise RuntimeError(f"[{lab}] local fuse: {len(out.solids())} solids, valid {out.is_valid}")
        P = out; tot += dv
    ss = P.solids()
    if len(ss) != 1 or not P.is_valid: raise RuntimeError(f"[{label}] {len(ss)} solids, valid {P.is_valid}")
    print(f"    [{label}] {len(ops)} ops, sum of op changes {tot:+.2f} mm3, 1 valid solid", flush=True)
    return ss[0]
def one_count(sh): return sh.solids()
def _body():
    import time; _T0[0] = time.time()
    key0 = ("body", S, BRELD, PKT, SNX, SNW, SNT, SNZ, RIBD, SNG, KC, RCELL, stamp("cad/body/build.py", "cad/eyes/build.py", "cad/legs/build.py", "cad/motion.py"),
            srch(to_robot, checked, _bool, local_box, pvol, one, tree_fuse, dense, sweep_hulls, plane_solid, plane_data, _fib, leg_points, leg_frame, snap_geometry, finger_root))
    def skin_stage():
        b = to_robot(BO.body(k=1.0)); tick("body skin"); return b
    b = cached("body_skin", key0 + ("skin", srch(skin_stage)), skin_stage)
    def eyes_stage():
        ops = [("fuse", to_robot(cup), f"cup {n}", False) for n, cup in enumerate(eye_cups())]
        # the sensor dome floats 4.07 mm under the body's chin (jenscolt's separate mesh): a 1.2 mm stem up into the chin
        bb = to_robot(eye_cups()[-1]).bounding_box()
        stem = Pos((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, bb.max.Z - 2.4) * Cylinder(1.2, 27.4 - (bb.max.Z - 2.4), align=(Align.CENTER, Align.CENTER, Align.MIN))
        ops.insert(len(ops) - 1, ("fuse", stem, "sensor stem", False))      # stem before the sensor cup
        # the LEDs sit in the big eyes (power_stage); the small eyes' LED through-bores (Ø4.2) are gone
        c = local_seq(b, ops, "eyes"); tick("eye cups + sensor stem"); return c
    b = cached("body_eyes", key0 + ("eyes", "stem", srch(eyes_stage, eye_cups), H["body_skin"]), eyes_stage)
    def fit_stage():
        ops = []
        for n, (_, fing, _) in enumerate(snap_geometry()):       # finger lengthened up into the front wall (finger_root), else it
            ops.append(("fuse", finger_root(fing), f"snap finger {n}", True))     # would be a 2nd solid, dropped by one()
        tw, ty0, ty1, tz = BO.TAB; ty = (ty0 - ORIGIN[1]) * S          # rear tab notched over the back-sheet pocket
        dp, hx, z0, z1 = PKT
        notch = Pos(0, ty - 1.0, z0 - 0.5) * Box(2 * hx + 1.0, dp + 1.0, z1 - z0 + 1.0, align=(Align.CENTER, Align.MIN, Align.MIN))
        ops.append(("cut", notch, "tab notch", True)); c = local_seq(b, ops, "fit"); tick("snap fingers + tab notch"); return c
    b = cached("body_fit", key0 + ("fit", srch(fit_stage), H["body_eyes"]), fit_stage)
    near = dense(b)
    def per_leg(name, r, **kw):
        """one fused cutter per leg (its hulls tree-fused, cached per leg), cut in turn with the volume invariant."""
        ops = []
        for Lg in range(8):
            def mk(Lg=Lg):
                hs = sweep_hulls(near, r, legs=(Lg,), planes=True, cell=RCELL, **kw)
                tick(f"{name} leg {Lg}: {len(hs)} hulls")
                return tree_fuse(hs) if hs else None
            # cutter keyed on the skin, not the stages after it: the cut is the legs' sweep against the wall, and what the later
            # stages change (eye bores, LED bores) is far from it
            t = cached(f"body_{name}{Lg}", key0 + (name, Lg, r, repr(sorted(kw.items())), H["body_skin"]), lambda: mk() or Box(0.01, 0.01, 0.01))
            if pvol(t) > 0.01: ops.append(("cut", t, f"{name} leg {Lg}", False))
        return local_seq(b, ops, name)
    def rim_stage():
        c = per_leg("rim", BRELD); tick("rim cuts"); return c
    b = cached("body_rim", key0 + ("rim", srch(rim_stage, per_leg), H["body_fit"]), rim_stage)
    def lift_stage():
        c = per_leg("lift", F.NEIGHBOUR.side + 0.1, poses=[KC], group=1, lift=CL.LIFTD); tick("lift cuts"); return c
    b = cached("body_lift", key0 + ("lift", srch(lift_stage), H["body_rim"]), lift_stage)
    def power_stage():
        """what the power parts need from the body: the two 5 mm LED bores (big eyes, where check.py has them, flange stop on
        the floor's back face), the switch's lever slot and keeper, the pockets round the cell holder, lid, cells, switch and
        LEDs, and a stop post per leg against its sliding off the pin."""
        import power as PW
        ops = []
        for sx in (-1, 1):                                      # LED bores
            x, y, z = led_pos(sx)
            ops.append(("cut", Pos(x, y - LEDB0, z) * Rot(-90, 0, 0) * Cylinder(LED_R + F.TURN.side, LEDB1 + LEDB0, align=(Align.CENTER, Align.CENTER, Align.MIN)),
                        f"led bore {sx:+d}", True))
        for sx in (-1, 1):                                      # the small eyes' tube bores would be sealed voids under their cups: opened to the cavity
            ops.append(("cut", Pos((BO.CX + sx * BO.SEYE_DX - ORIGIN[0]) * S, (BO.SEYE_BACK - ORIGIN[1]) * S - LEDB0, (BO.SEYE_Z - ORIGIN[2]) * S) * Rot(-90, 0, 0)
                        * Cylinder(BO.SEYE_BORE * S, LEDB1 + LEDB0, align=(Align.CENTER, Align.CENTER, Align.MIN)), f"small-eye vent {sx:+d}", True))
        bx, by, bz = PW.SW_BODY; lx, ly, lz = PW.SW_LEVER; y1 = PW.SWY1; zs = PW.SWZ; st = F.STEEL.side
        MIN = (Align.MIN, Align.MIN, Align.MIN)
        slot = Pos(-(lx / 2 + SW_THROW / 2 + st), y1 - 0.5, zs - lz / 2 - st) * Box(lx + SW_THROW + 2 * st, SW_SLOT_Y, lz + 2 * st, align=MIN)
        ops.append(("cut", slot, "switch lever slot", True))
        yk = y1 - by - st; xk = bx / 2 + st; zb, zt = zs - bz / 2, zs + bz / 2 + st; yr = y1 + SW_KEEP_REACH
        keeper = [Pos(-xk - W_KEEP, yk - W_KEEP, zb) * Box(2 * (xk + W_KEEP), W_KEEP, zt + W_KEEP - zb, align=MIN),        # plate behind the switch
                  Pos(-xk - W_KEEP, yk - W_KEEP, zt) * Box(2 * (xk + W_KEEP), yr - yk + W_KEEP, W_KEEP, align=MIN)]          # top bar to the wall
        for sx in (-1, 1): keeper.append(Pos(sx * (xk + W_KEEP / 2) - W_KEEP / 2, yk - W_KEEP, zb) * Box(W_KEEP, yr - yk + W_KEEP, zt - zb, align=MIN))   # side ribs
        ops.append(("fuse", fuse_one(keeper), "switch keeper", True))
        for nm, part, r in (("holder", PW.holder(), F.LOCATOR.side), ("lid", PW.lid(), F.LOCATOR.side), ("cells", PW.cells(), F.LOCATOR.side),
                            ("switch", PW.switch(), F.LOCATOR.side)):   # no LED pocket: the LEDs sit in their bores (power.py's leds() still stand at the small eyes: it was 86 mm3 there)
            ops.append(("cut", grow(part, r), f"pocket {nm}", False))
        # the inner wall strip under the cell holder (x 17.6..20.05, y 8.5..12.8, z 19.95..23.85, found on body_power 2026-11-23) blocked the
        # body's bench path (0.25 mm) and touched the cells: cut away, to the wall where the holder's pocket widens (|x| 19.25, z 23.65)
        ops.append(("cut", fuse_one([Pos(-STRIP_X, STRIP_Y0, STRIP_Z0) * Box(2 * STRIP_X, STRIP_Y1 - STRIP_Y0, STRIP_Z1 - STRIP_Z0, align=MIN),
                                     Pos(-STRIP_X2, STRIP_Y0 - 0.5, STRIP_Z0) * Box(2 * STRIP_X2, STRIP_Y1 - STRIP_Y0 + 0.5, STRIP_Z2 - STRIP_Z0, align=MIN)]),
                    "holder strip", True))
        # the pockets round the holder and the lid leave two thin loose webs (17.5 mm3 each, x +-18, y 8..12, z 28..37) between them: not
        # printable and not attached, so they go (crumb limit 30 mm3, said in the log)
        c = local_seq(b, ops, "power", crumb=30.0); tick("LED bores, switch slot + keeper, pockets")
        near = dense(c); posts = []
        for Lg in range(4):
            r = xstop_post(Lg, near)
            if r is None: print(f"    [power] leg {Lg}: no stop post fits", flush=True); continue
            ps = post_solid(r[0], r[1]); posts.append((Lg, ps)); print(f"    [power] leg {Lg}: stop post {np.round(r[0], 1)} -> {np.round(r[1], 1)}, leg moves {r[2]:.2f} before it", flush=True)
        ops = []
        for Lg, ps in posts:
            ops.append(("fuse", ps, f"stop post {Lg}", True)); ops.append(("fuse", mirror_x(ps), f"stop post {Lg + 4}", True))
        c = local_seq(c, ops, "posts") if ops else c; tick("stop posts"); return c
    import power as _PW
    b = cached("body_power", key0 + ("power", STRIP_X, STRIP_X2, STRIP_Y0, STRIP_Y1, STRIP_Z0, STRIP_Z1, STRIP_Z2, srch(power_stage, xstop_post, post_solid, led_pos, grow), LEDB0, LEDB1, LED_R, BO.SEYE_BORE, SW_THROW, SW_SLOT_Y, SW_KEEP_REACH, W_KEEP, XS_RP, XS_HIT,
                                      stamp("cad/robot/power.py"), srch(_PW.holder, _PW.lid, _PW.cells, _PW.switch), H["body_lift"]), power_stage)
    assert len(b.solids()) == 1 and b.is_valid and pvol(b) > 0, f"body: {len(b.solids())} solids, valid {b.is_valid}"
    print(f"    [body] volume {pvol(b):.1f} mm3, valid, 1 solid", flush=True)
    return b
def body():
    key = ("body", S, BRELD, PKT, SNX, SNW, SNT, SNZ, RIBD, SNG, KC, RCELL, stamp("cad/body/build.py", "cad/eyes/build.py", "cad/legs/build.py", "cad/motion.py"), srch(_body))
    b0 = one(cached("body", key, _body)); b = one(unify(b0))          # coplanar fragments: unify as base() does, outside the cache
    if not (b.is_valid and len(b.solids()) == 1):
        print("    [body] WARN clean() left it invalid (the power stage's pockets/keeper): the unified faces are kept as built", flush=True)
        b = one(cached("body", key, _body))                            # clean() edits its argument in place (shared TShapes): reload the cached, valid one
    assert b.is_valid and len(b.solids()) == 1, "body: not valid"
    return b

PARTS = {"base": base, "body": body, **{f"leg-{Lg}": (lambda Lg=Lg: leg(Lg)) for Lg in range(8)}}
