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
from build123d import (Box, Cylinder, Sphere, Pos, Rot, Solid, Shell, Face, Wire, Compound, Vector, Align,
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
RELD, BRELD, PKR = CL.RELD, CL.BRELD, CL.PKR   # arm-sweep pockets: base front relief, body rim notch, eye block
PKT = FE.PKT                            # back-sheet pocket (depth, |x|, z0, z1), Morante 2026-11-21
SNX, SNW, SNT, SNZ, RIBD, SNG = CL.SNX, CL.SNW, CL.SNT, CL.SNZ, CL.RIBD, CL.SNG
PINR = CL.PINR                          # printed crank pin r (Ø3)
END_R = PINR + F.TURN.side + CL.W       # leg end tube: bore TURN over the pin, wall W 1.2
TAIL, HUBCUT = CL.TAIL, CL.HUBCUT       # tail past the pin (m21), real arm kept from HUBCUT past the pin
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
    h = hashlib.sha1(pickle.dumps(key)).hexdigest()[:12]; p = os.path.join(CACHE, f"{name}_{h}.brep")
    if os.path.exists(p): return import_brep(p)
    sh = fn(); export_brep(sh, p); return sh
def stamp(*rel): return [int(os.path.getmtime(os.path.join(ROOT, r))) for r in rel]
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
    x0, xm, x1 = A0[0] - TAIL, A0[0], P["XC"] + CL.PINX + 1.5        # tail .. pin point .. past the pin tip
    def dcone(r):
        a = Cylinder(1, 1)
        from build123d import Cone
        c1 = Pos(x0, A0[1], A0[2]) * Rot(0, 90, 0) * Cone(r + (xm - x0) * math.tan(th), r, xm - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        c2 = Pos(xm, A0[1], A0[2]) * Rot(0, 90, 0) * Cone(r, r + (x1 - xm) * math.tan(th), x1 - xm, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return c1 + c2
    tube = dcone(END_R)
    bore = Pos(-0.01, 0, 0) * dcone(PINR + F.TURN.side)
    bore = bore + Pos(0.02, 0, 0) * dcone(PINR + F.TURN.side)
    joint = _along(Cylinder(P["r_inner"], HUBCUT - 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), A0 + 1.5 * u, u)
    ball = Pos(*P_) * Sphere(PB)
    leg = fuse_all([blade, arm, tube, joint, ball]) - bore
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
    key = ("leg3", i, FLARE_DEG[i], CL.PINX, S, HUBCUT, TAIL, END_R, PB, stamp("cad/legs/build.py", "cad/motion.py"), FE.D23, FE.D23C)
    sh = cached(f"leg{i}", key, lambda: _leg_right(i))
    return sh if Lg < 4 else mirror_x(sh)

FLARE_DEG = [round(pin_swing(i) + 1.0, 1) for i in range(4)]

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
def sweep_hulls(near, r, legs=range(8), poses=range(24), group=3, cell=3.0, rn=None, lift=0.0, planes=False):
    """convex hulls (grown by r) covering the legs' sweep where it comes within r + 1 of the samples `near`.
    rn: only samples within rn of the pivot (window neck); lift: also slide the samples down by lift (body lift-off)."""
    tn = cKDTree(near); hulls = []
    for Lg in legs:
        for g0 in range(0, len(poses), group):
            ks = list(poses)[g0:g0 + group + 1]
            Q = [LP(Lg, k % 24) for k in ks]
            if rn is not None: Q = [q[np.linalg.norm(q - PIV[Lg], axis=1) <= rn] for q in Q]
            q = np.vstack(Q)
            if lift > 0: q = np.vstack([q - [0, 0, t] for t in np.arange(0, lift + 0.01, 1.0)])
            d = tn.query(q, distance_upper_bound=r + 1.0)[0]; q = q[np.isfinite(d)]
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
def cut_many(sh, tools, batch=40):
    for j in range(0, len(tools), batch):
        sh = sh.cut(Compound(tools[j:j + batch]))
    return sh
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
        hulls.append(plane_solid(q, WR))
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
    key = ("win", Lg, S, RN, WR, CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py", "cad/robot/shells.py"))
    return cached(f"win{Lg}", key, lambda: fuse_one(window_cutter(Lg)))
def leg_ring(Lg):
    """leg Lg's pad ring (its window cutter's support polytope grown 1.5), cached by its inputs."""
    key = ("ring", Lg, S, RN, WR, CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py", "cad/robot/shells.py"))
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
    key0 = ("base", S, WALL_PAD, RN, WR, RELD, PKT, SNX, SNW, SNZ, RIBD, CL.LSL, _K, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py", "cad/robot/shells.py"))
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
    b = cached("base_pads", key0 + ("pads",), pads_stage)
    def win_stage():
        c = b
        for side in (range(0, 4), range(4, 8)):         # checked() cuts each on its own local piece; a local_op round it
            c = fuse_cut(c, [(wins[Lg], f"window leg {Lg}") for Lg in side])   # nested two local pieces and gave an inside-out one
            tick(f"4 window cuts, side {side[0]}-{side[-1]}")
        return c
    b = cached("base_win", key0 + ("win",), win_stage)
    near = samples(b)                                           # front leg windows: pocket RELD from the front arms' sweep
    def relief_tools(Lg):
        """leg Lg's relief pocket solid and outward bulge solid (hull cell RCELL), each cached by its inputs."""
        kk = key0 + ("relief", Lg, RCELL, RELD, BA.WALL * S)
        def mk():
            rel = sweep_hulls(near, RELD, legs=(Lg,), planes=True, cell=RCELL)
            grown = sweep_hulls(near, RELD + BA.WALL * S, legs=(Lg,), planes=True, cell=RCELL)
            tick(f"leg {Lg} relief hulls: {len(rel)} + {len(grown)} grown, faces/hull {sorted(len(h.faces()) for h in rel + grown)[-1]} max")
            return rel, grown
        def rs_fn():
            rel, grown = mk(); rs = tree_fuse(rel); tick(f"leg {Lg} relief fused"); return rs
        rs = cached(f"relf{Lg}", kk + ("rs",), rs_fn)
        def gs_fn():
            rel, grown = mk(); return tree_fuse(grown)
        gs = cached(f"relg{Lg}", kk + ("gs",), gs_fn)
        outer = to_robot(BA.skin(0.0, 1.0)); bx = local_box([gs], 1.0)
        bulge = cached(f"relb{Lg}", kk + ("bulge",), lambda: gs - (outer & bx)); tick(f"leg {Lg} bulge")
        return rs, gs, bulge
    def relief_stage():
        c = b
        for Lg in (0, 4):                                       # one local box per front leg
            rs, gs, bulge = relief_tools(Lg)
            c = fuse_cut(c, [(rs, f"relief leg {Lg}")], add=(bulge, f"bulge leg {Lg}")); tick(f"leg {Lg} bulge + relief (local)")
        return c
    b = cached("base_relief", key0 + ("relief", _K), relief_stage)
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
    key = ("base", S, WALL_PAD, RN, WR, RELD, PKT, SNX, SNW, SNZ, RIBD, CL.LSL, stamp("cad/base/build.py", "cad/legs/build.py", "cad/motion.py", "cad/robot/shells.py"))
    return cached("base", key, _base)

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
def _body():
    b = to_robot(BO.body(k=1.0))
    for c in eye_cups(): b = b.fuse(to_robot(c))
    print("    body + eyes:", len(b.solids()), "solid(s)", flush=True)
    for _, fing, _ in snap_geometry(): b = b.fuse(fing)
    tw, ty0, ty1, tz = BO.TAB; ty = (ty0 - ORIGIN[1]) * S          # rear tab notched over the back-sheet pocket
    dp, hx, z0, z1 = PKT
    b = b - Pos(0, ty - 1.0, z0 - 0.5) * Box(2 * hx + 1.0, dp + 1.0, z1 - z0 + 1.0, align=(Align.CENTER, Align.MIN, Align.MIN))
    near = samples(b)
    b = cut_many(b, sweep_hulls(near, BRELD))                  # rim notch + eye-block pocket from the arms' sweep
    b = cut_many(b, sweep_hulls(near, F.NEIGHBOUR.side + 0.1, poses=[KC], group=1, lift=CL.LIFTD))   # lift-off at pose KC
    return one(b)
def body():
    key = ("body", S, BRELD, PKT, SNX, SNW, SNT, SNZ, RIBD, SNG, KC, stamp("cad/body/build.py", "cad/eyes/build.py", "cad/legs/build.py", "cad/motion.py", "cad/robot/shells.py"))
    return cached("body", key, _body)

PARTS = {"base": base, "body": body, **{f"leg-{Lg}": (lambda Lg=Lg: leg(Lg)) for Lg in range(8)}}
