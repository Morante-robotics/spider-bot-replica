"""Robot shells at S (spec.json S_start, 1.0): cad/base, cad/body, cad/eyes and cad/legs built as they are, moved into
the robot frame (motion.to_frame: (q - ORIGIN) x S) and given the plan's local features here, without editing those
designs. Every shell number is the fit check's (cad/robot/fitcheck/check.py LAYOUT and fit_env.py, 0 failing of 327),
imported, never copied:
  base   leg windows (the real legs' neck sweep, RN 8 + WR 0.9, pushed up past the rim, slid LSL off the pin),
         two front snap ribs
  body   two front snap fingers (SNT 0.8 x SNW 5, L RIMR - SNZ), the two eye cups (cad/eyes) in their bores
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
from build123d import (Torus, Shape, Box, Cylinder, Sphere, Pos, Rot, Solid, Shell, Face, Wire, Compound, Vector, Align,
                       export_step, export_stl, import_brep, export_brep, extrude, Plane, Polygon)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Pnt, gp_Dir
from scipy.spatial import ConvexHull, cKDTree
import fit_env as FE                    # S, P (motion lengths x S/0.60), PIV, A_ALL, inside()
from cad import design, fits as F
import timebudget as _tb
motion = FE.motion
class _Layout:
    """the fit check's numbers, read from check.py's source (importing it would run the 8-minute check): LAYOUT
    first, then each E("NAME", default) and the plain constants it uses."""
    FIXED = {"MANG", "TANG", "BSA", "KEELFIX", "HSZ", "N", "TI", "HNOTCH", "HOPEN", "DSCREW", "POSTSPINE", "LEGLEG",
             "LEGSONLY", "PSOLID", "SEATS", "FIG", "FIGLEG", "SNG", "WR", "LIFTC", "SPR", "HSINK2"}   # angles, flags, fits, bought spring
    WALLS = {"W", "WEB_T", "LIDT", "HNS", "SNAP_WALL"}                                         # walls / plates: fits.WALL_MIN
    DELETED = {"RELD", "BRELD", "PKR", "TAIL"}                                                  # 0.70 fit tweaks (phase 2 step 1)
    def __init__(self):
        import re, ast
        src = open(os.path.join(HERE, "fitcheck", "check.py")).read()
        blk = re.search(r"LAYOUT = dict\((.*?)\)\n", src, re.S).group(1)
        lay = {k: v for k, v in re.findall(r"(\w+)=([-\d.]+)", blk)}
        for m in re.finditer(r'E\("(\w+)",\s*([-\d.]+)\)', src): setattr(self, m.group(1), float(m.group(2)))
        for k in ("PINR", "W", "HUBCUT", "GW", "WEB_T"):
            setattr(self, k, float(re.search(rf"\b{k} = ([\d.]+)", src).group(1)))
        for k, v in lay.items(): setattr(self, k, float(v))
        for k in list(vars(self)):
            if k in self.FIXED: continue
            setattr(self, k, max(F.WALL_MIN, getattr(self, k)) if k in self.WALLS else getattr(self, k) * FE.K)
        for k in self.DELETED: delattr(self, k)
        self.TAIL_CUT = 1.5                # phase 3: the tube's mouth stops this much short of a wall's tail (tilt + axial drift put its rim 0.0-0.75 into the crank webs, n1 2026-11-27)
        self.TAIL = self.W - self.TAIL_CUT  # tube face XC - TAIL (was XC - W)
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
STRIP_X, STRIP_X2, STRIP_Y0, STRIP_Y1, STRIP_Z0, STRIP_Z1, STRIP_Z2 = (FE.K * v for v in (20.05, 19.25, 6.4, 12.8, 19.0, 23.65, 23.9))   # body strip under the cell holder, cut away
def wr_of(Lg): return WR
BRELD = F.LEG_PATH.side + 0.15   # body rim notch / eye-block pocket: the body inner face is pushed back to this from the legs' 24-pose sweep: LEG_PATH + 0.15 for the sample spacing and the coarse mesh (0.6 left 0.00-0.06 at legs 0/4; 0.75 and 0.85 gave an empty cutter outline)
PKT = FE.PKT                            # back-sheet pocket (depth, |x|, z0, z1): spec back_sheet_pocket, derived from the legs' sweep at S 1.0
SNX, SNW, SNT, SNZ, RIBD, SNG = CL.SNX, CL.SNW, CL.SNT, CL.SNZ, CL.RIBD, CL.SNG
PINR = CL.PINR                          # printed crank pin r (Ø3)
PIN_TRIM = 0.5                          # pin tip short of the legs' nominal bore floor by this (drive.py reads it: PIN_X1)
PIN_X1 = P["XC"] + CL.PINX - PIN_TRIM   # pin tip (|x|)
# leg end tube (option D): the bore is the tilted pin's ellipse, PINR / cos(tilt) + TURN; the wall is fits.WALL_MIN; per leg, set below
# (BORE_R, END_RS, TUBE_X1 after pin_swing); END_R is the largest, the envelope the checks box
# leg snap on the crank pin (option A, build-log N2 r00): a groove on the pin, a ring bead in the end tube's bore, an axial slit
# in the tube so it opens over the pin tip. The snap fit is fits.PRESS (assumed): coupon list, not printed now.
SNAP_NECK_R = 1.0 * FE.K                       # pin neck r in the groove (Ø2.0, brief: neck Ø >= 2.0)
SNAP_BW = 0.5 * FE.K                           # bead width (axial)
SNAP_WALL = F.WALL_MIN                         # solid end wall closing the tube beyond the bore floor: the neck rod runs into it (print 2026-11-24: the rod only butted the open rim, leg 3 snapped)
END_PAD = 0.05                                 # end wall starts this far past the bore floor (the bore cutter runs 0.02 past it; the wall must stay SNAP_WALL thick)
SLIT_END, SLIT_CHAMFER = 0.03, 0.5            # slit stops this far past the bore floor; 45 deg chamfer on its outer edges
SNAP_SLIT = 0.6 * FE.K                         # slit width (tangential)
def snap_bead_r(i):
    """bead inner r: the ring (circle of radius r, width SNAP_BW, plane normal to the tube's axis) sits tilted by the pin's swing on the
    neck: its edge corner is at distance r cos(tilt) - SNAP_BW / 2 sin(tilt) from the pin axis, which must be neck + TURN."""
    t = math.radians(PIN_TILT[i])
    return (SNAP_NECK_R + F.TURN.side + SNAP_BW / 2 * math.sin(t)) / math.cos(t)
SNAP_MARGIN = F.TURN.side + 0.05             # axial room each side of the bead's travel (TURN; 0.10 left crank x leg 0.06-0.09 over the poses; slide stays within RETAIN 1.25)
def snap_groove(i):
    """(x0, x1) of the pin groove (robot |x|, right side): the axial span the bead's inner edge sweeps where it is within the pin's
    shoulder radius (PINR), over the 24 poses (tilt of the tube on the pin and the leg's axial drift), plus SNAP_MARGIN a side."""
    P_, A0 = motion.neutral_leg(i, P, n=13)[:2]; A0 = np.asarray(A0, float); rb = snap_bead_r(i); lo = 1e9; hi = -1e9
    th = np.linspace(0, 2 * np.pi, 181)
    ring = np.array([[A0[0], A0[1] + r * np.cos(t), A0[2] + r * np.sin(t), 1.0] for r in np.linspace(rb, PINR + 0.5, 6) for t in th])     # the bead's face out to the shoulder radius: its tilted plane reaches furthest along x there
    for k in range(24):
        Q = (leg_frame(i, k) @ ring.T).T[:, :3]
        rho = np.hypot(Q[:, 1] - A_ALL[i, k][1], Q[:, 2] - A_ALL[i, k][2]); m = rho < PINR
        if m.any(): lo = min(lo, Q[m, 0].min() - SNAP_BW / 2); hi = max(hi, Q[m, 0].max() + SNAP_BW / 2)
    return round(float(lo - SNAP_MARGIN), 2), round(float(hi + SNAP_MARGIN), 2)
TAIL, HUBCUT = CL.TAIL, CL.HUBCUT       # tail past the pin (m21), real arm kept from HUBCUT past the pin
KEEL_BOSS_R = 2.75 + F.STEEL.side + F.WALL_MIN                       # keel boss radius: counterbore (M2 head 1.9 + STEEL) + 0.95 of wall
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
    # option D (phase 3 leg joint): the leg rides with its pin point on the crank pin, not with its pivot P fixed: translate by A_k - T A0
    # (<= 1.45 mm along the leg, foot height <= 0.3), so the bore axis stays on the pin and BORE_DRIFT is 0 (right-leg frame, then mirrored)
    T[:3, 3] += A - (T[:3, :3] @ np.asarray(A0, float) + T[:3, 3])
    if not right:
        Mx = np.diag([-1.0, 1, 1, 1]); T = Mx @ T @ Mx
    return T
JOINT_R = 2.35 * FE.K            # mm, the neck between the end tube and the arm (was P["r_inner"] 1.8: leg-3 broke there, print 2026-11-24)
JOINT_BLEND_DR, JOINT_BLEND_L = 1.0 * FE.K, 2.0 * FE.K     # mm, cone at the tube end of the neck: r +1 tapering over 2 mm
def _leg_right(i):
    from build123d import Cone
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
    arm = arm - hs - _along(Cylinder(60, HUBFLANGE_L, align=(Align.CENTER, Align.CENTER, Align.MIN)) - Cylinder(HUBFLANGE_R, HUBFLANGE_L, align=(Align.CENTER, Align.CENTER, Align.MIN)), A0 + HUBCUT * u, u)     # and the rim of the hub plate the cut left standing as a thin tab on the neck
    th = math.radians(CONE_FLARE[i]); c = CONE_AXIS[i]; c0 = float(c[0]); s_t = math.sqrt(1 - c0 * c0)    # bore and tube turned about the pin's swing cone: axis c (tilted towards +y), flare = cone half-angle + 1 deg
    END_R = END_RS[i]; BR = BORE_R[i]
    x0, xm, x1 = A0[0] - TAIL, A0[0], TUBE_X1[i]   # tail .. pin point .. bore floor (the tilted pin tip's corner + TURN); mouth and floor stay planes square to x
    x1p = x1 + END_PAD                                # the end wall's inner face
    xe = x1p + SNAP_WALL                              # the tube's closed end (at its lowest point)
    tn = math.tan(th); xt = min(flare_end(i), x1); ht = (xt - xm) / c0      # the flare stops where the pin tip's reach does (flare_end); a cylinder beyond it to the end
    ax = lambda x: A0 + (x - xm) / c0 * c             # the axis' point in the plane x
    LF = Plane(origin=tuple(A0), z_dir=tuple(c))      # local z along the tilted axis, h = distance from the pin point
    def slab(xa, xb): return Pos((xa + xb) / 2, A0[1], A0[2]) * Box(xb - xa, 60, 60)
    hlo = (x0 - xm) / c0 - 3.0
    def rev(r, hhi):
        """double cone (flare tn each side of the pin point, radius r there) about the axis, h from hlo to hhi; a cylinder beyond ht."""
        c1 = Pos(0, 0, hlo) * Cone(r - hlo * tn, r, -hlo, align=(Align.CENTER, Align.CENTER, Align.MIN))
        c2 = Cone(r, r + ht * tn, ht, align=(Align.CENTER, Align.CENTER, Align.MIN))
        c3 = Pos(0, 0, ht) * Cylinder(r + ht * tn, hhi - ht, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return LF * (c1 + c2 + c3)
    r1 = END_R + ht * tn                               # outer radius beyond the flare; the closed end is a flat wall (square to the axis) and a quarter round of radius SNAP_WALL, a revolve about the tilted axis
    rho = r1 - SNAP_WALL
    hc = (x1p + SNAP_WALL - A0[0] + rho * s_t) / c0 - SNAP_WALL      # round's centre plane: the end face's lowest point is SNAP_WALL past the floor plane
    tube = rev(END_R, hc)
    tube = tube + LF * (Pos(0, 0, hc - 0.5) * Cylinder(rho, SNAP_WALL + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
                        + ((Pos(0, 0, hc) * Torus(rho, SNAP_WALL)) & (Pos(0, 0, hc + SNAP_WALL / 2) * Box(4 * r1, 4 * r1, SNAP_WALL))))
    tube = tube & slab(x0, xe + 10)                    # mouth square to x
    # the mouth's outer edge is chamfered (leg 1 x transfer touched it, n1 2026-11-27)
    rf = END_R + (xm - x0) / c0 * tn; m0 = ax(x0)
    wedge = Pos(x0, m0[1], m0[2]) * Rot(0, 90, 0) * (Cylinder(rf + 1.5, FACE_CHAMFER + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                      - Cone(rf - FACE_CHAMFER, rf + 1.0, FACE_CHAMFER + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    tube = tube - wedge
    bore = rev(BR, (x1 - xm) / c0 + 3.0) & slab(x0 - 0.04, x1)       # ONE bore cutter: floor square to x, trimmed at the floor plane
    joint = _along(Cylinder(JOINT_R, HUBCUT - 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), A0 + 1.5 * u, u)
    joint = joint + _along(Cone(JOINT_R + JOINT_BLEND_DR, JOINT_R, JOINT_BLEND_L, align=(Align.CENTER, Align.CENTER, Align.MIN)), A0 + 1.5 * u, u)   # blends into the tube wall
    ball = Pos(*P_) * Sphere(PB)
    rb = snap_bead_r(i)
    ring = Pos(xm - SNAP_BW / 2, A0[1], A0[2]) * Rot(0, 90, 0) * (Cylinder(BR + 0.4, SNAP_BW, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                                  - Cylinder(rb, SNAP_BW, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    leg = fuse_all([blade, arm, tube, joint, ball]) - bore
    uh = u - np.dot(u, [1.0, 0, 0]) * np.array([1.0, 0, 0]); uh = uh / np.linalg.norm(uh)             # the arm's side of the tube
    if sorted(x.volume for x in leg.solids())[-2:-1] and sorted(x.volume for x in leg.solids())[-2] > 30:     # a piece bigger than the hub's 12 mm3 sliver
        # the arm leaves the tube's flare cone (leg 2/6: u mostly along x), so the joint never reaches the wall and the tube came off
        # (r00: «leg-2's tube detached»). A strut from the wall at the tube's mouth to the joint axis ties them.
        xw = xe - 0.3; rw = (rb + END_R) / 2 + (min(xw, xt) - xm) / c0 * tn + 0.2
        W_ = ax(xw) + rw * np.array([0, uh[1], uh[2]]) ; J_ = A0 + 6.0 * u
        v_ = J_ - W_; strut = _along(Cylinder(1.0 * FE.K, float(np.linalg.norm(v_)), align=(Align.CENTER, Align.CENTER, Align.MIN)), W_, v_)
        leg = fuse_all([leg, strut]) - bore
    leg = fuse_all([leg, ring])
    up_ = u - np.dot(u, [1.0, 0, 0]) * np.array([1.0, 0, 0]); up_ = -up_ / np.linalg.norm(up_)     # slit on the side away from the arm
    sx0 = x0 - 0.5                                    # the slit runs out through the mouth (from x0 + 0.2 it left a 0.2 mm membrane across the slit)
    rh = up_ - np.dot(up_, c) * c; rh = rh / np.linalg.norm(rh); th_ = np.cross(c, rh)       # the slit's radial and tangent directions about the tilted axis
    hs0 = (sx0 - xm) / c0 - 1.0
    slit = Plane(origin=tuple(A0), x_dir=tuple(rh), z_dir=tuple(c)) * (Pos(0, 0, hs0) * Box(END_R + 1.5 + ht * tn, SNAP_SLIT, (x1 + 1.0 - xm) / c0 - hs0, align=(Align.MIN, Align.CENTER, Align.MIN)))
    slit = slit & slab(sx0, x1 + SLIT_END)            # stops 0.03 past the floor plane: the end wall under it stays SNAP_WALL
    leg = leg - (slit & tube)
    # the slit's two outer edges: 0.5 x 45 deg chamfer, a square prism turned 45 deg along the outer generatrix at the slit's angle
    rr = lambda x: END_R + min(abs((x - xm) / c0), ht if x > xm else 1e9) * tn
    ch = None
    for xa_, xb_, ov in ((x0 - 0.6, xm, 0.02), (xm, xt, 0.02), (xt, x1 + SLIT_END, 0.0)):
        pa = ax(xa_) + rr(xa_) * rh; pb = ax(xb_) + rr(xb_) * rh; u_ = pb - pa; L_ = float(np.linalg.norm(u_)); u_ = u_ / L_
        t_ = np.cross(u_, rh); t_ /= np.linalg.norm(t_); sq = (SNAP_SLIT / 2 + SLIT_CHAMFER) * math.sqrt(2)
        pr = Plane(origin=tuple(pa), x_dir=tuple(t_), z_dir=tuple(u_)) * (Rot(0, 0, 45) * Box(sq, sq, L_ + ov, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        ch = pr if ch is None else ch + pr
    leg = leg - (ch & slab(x0 - 0.6, x1 + SLIT_END))
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
    key = ("leg18", i, CONE_TILT[i], CONE_FLARE[i], tuple(CONE_AXIS[i]), SLIT_END, SLIT_CHAMFER, flare_end(i), END_PAD, snap_bead_r(i), TUBE_X1[i], BORE_R[i], END_RS[i], SNAP_WALL, SNAP_NECK_R, SNAP_BW, SNAP_SLIT, FLARE_DEG[i], CL.PINX, S, HUBCUT, TAIL, PB, JOINT_R, JOINT_BLEND_DR, JOINT_BLEND_L, stamp("cad/legs/build.py", "cad/motion.py"), FE.D23, FE.D23C,
           FACE_CHAMFER, HUBFLANGE_L, HUBFLANGE_R, srch(_leg_right, _along))
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
FACE_CHAMFER = 0.6       # tube mouth outer edge 45 deg chamfer
HUBFLANGE_L, HUBFLANGE_R = 5.0, 6.0     # mm past HUBCUT, mm round the leg axis: jenscolt's hub-plate rim beyond HUBCUT is cut away outside this tube (it stood as a thin tab on the neck)
BORE_DRIFT = [0.0] * 4          # the leg rides on its pin (leg_frame): no axis drift to widen the bore by
PIN_TILT = [pin_swing(i) for i in range(4)]          # deg, the pin's largest tilt to the leg's x over the 24 poses
BORE_R = [PINR / math.cos(math.radians(t)) + F.TURN.side for t in PIN_TILT]     # the tilted pin cuts the bore's plane as an ellipse (semi-major PINR / cos)
END_R = None
def _tube_x1(i):
    """bore floor (robot |x|): the pin tip's far corner, tilted by the pin's swing, plus TURN."""
    A0 = np.asarray(motion.neutral_leg(i, P, n=13)[1], float); th = math.radians(PIN_TILT[i]); tip = PIN_X1 - A0[0]
    return float(A0[0] + tip * math.cos(th) + PINR * math.sin(th) + F.TURN.side)
TUBE_X1 = [_tube_x1(i) for i in range(4)]
BORE_PAD = 0.01                  # mm on the pin cone's bore radius (the cone fit's round-off)
def pin_cone(i):
    """the pin's swing cone in the leg frame (leg_frame over the 24 poses): smallest cone about an axis c enclosing the pin's direction;
    returns (c, half-angle deg, bore radius at the pin point so every pin surface point inside the tube clears it by TURN)."""
    from scipy.optimize import minimize
    A0 = np.asarray(motion.neutral_leg(i, P, n=13)[1], float); D = []; PTS = []; ph = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    for k in range(24):
        d = np.linalg.inv(leg_frame(i, k))[:3, :3] @ np.array([1.0, 0, 0]); d /= np.linalg.norm(d); D.append(d); A = A_ALL[i, k]
        e1 = np.cross(d, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
        for s_ in np.linspace(A0[0] - TAIL - 1.0 - A[0], PIN_X1 - A[0], 40):
            for t in ph: PTS.append(A0 + s_ * d + PINR * (math.cos(t) * e1 + math.sin(t) * e2))
    D = np.array(D); PTS = np.array(PTS)
    f = lambda v: max(math.degrees(math.acos(min(1, np.dot(dd, v / np.linalg.norm(v))))) for dd in D)
    c = np.r_[1.0, minimize(lambda q: f(np.array([1.0, q[0], q[1]])), [0.1, 0.0], method="Nelder-Mead").x]; c /= np.linalg.norm(c); a = f(c)
    q = PTS - A0; h = q @ c; rho = np.linalg.norm(q - np.outer(h, c), axis=1)
    ins = (q[:, 0] >= -TAIL) & (q[:, 0] <= TUBE_X1[i] - A0[0])
    return c, a, float((rho - np.abs(h) * math.tan(math.radians(a + 1.0)))[ins].max() + F.TURN.side)
_PC = [pin_cone(i) for i in range(4)]
CONE_AXIS = [pc[0] for pc in _PC]                                   # unit, +x, tilted towards +y in the leg frame
CONE_TILT = [round(math.degrees(math.acos(c[0])), 2) for c in CONE_AXIS]
CONE_FLARE = [round(pc[1] + 1.0, 2) for pc in _PC]                   # the cone's half-angle + 1 deg
BORE_R = [pc[2] + BORE_PAD for pc in _PC]                           # bore radius at the pin point, about the cone axis
END_RS = [BORE_R[i] + F.WALL_MIN / math.cos(math.radians(CONE_FLARE[i])) for i in range(4)]     # WALL_MIN measured normal to the flared cone
END_R = max(END_RS)
def flare_end(i):
    """x (leg frame) up to which the bore flares: the pin tip's farthest reach over the 24 poses (tip circle, leg frame) + TURN; beyond it
    the tube (to the bore floor) keeps the radius it has there: the floor is the leg's axial play, not the pin's."""
    P_, A0 = motion.neutral_leg(i, P, n=13)[:2]; A0 = np.asarray(A0, float); xt = 0.0
    ph = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    for k in range(24):
        Ti = np.linalg.inv(leg_frame(i, k)); A = A_ALL[i, k]
        pts = np.array([[PIN_X1, A[1] + PINR * np.cos(t), A[2] + PINR * np.sin(t), 1.0] for t in ph])
        xt = max(xt, float((pts @ Ti.T)[:, 0].max()))
    return round(xt + F.TURN.side, 2)

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
    clip = lambda m: Pos(0, cy - rb_in - 1.0, z0 - m) * Box(2 * (hx + m), 10.0, z1 - z0 + 2 * m, align=(Align.CENTER, Align.MIN, Align.MIN))
    ring = lambda r0, r1, m: (Pos(cx, cy, z0 - m) * (Cylinder(r1, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                                     - Cylinder(r0, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))))
    cut = ring(rb_in - dp, rb_in, 0.0) & clip(0.0)
    add = ring(rb_out - dp, rb_in - 0.05, w) & clip(w)
    return cut, add
def pocket_keepout():
    """the cup's volume grown by NEIGHBOUR: cut from the body so that its rear tab stays that far from the cup."""
    g = F.NEIGHBOUR.side; d = BASE_WALL / S; w = BASE_WALL; cx, cy = (BA.CX - ORIGIN[0]) * S, (BA.BACK_Y - ORIGIN[1]) * S
    rb_in, rb_out = (BA.BACK_R + d) * S, BA.BACK_R * S; dp, hx, z0, z1 = PKT; m = w + g
    clip = Pos(0, cy - rb_in - 1.0, z0 - m) * Box(2 * (hx + m), 10.0, z1 - z0 + 2 * m, align=(Align.CENTER, Align.MIN, Align.MIN))
    ring = (Pos(cx, cy, z0 - m) * (Cylinder(rb_in - 0.05, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                   - Cylinder(rb_out - dp - g, z1 - z0 + 2 * m, align=(Align.CENTER, Align.CENTER, Align.MIN))))
    return ring & clip
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
FING_Z0, FING_Z1, FING_IN = 24.5 * FE.K, 27.5 * FE.K, 1.2 * FE.K   # snap finger root: a block from z FING_Z0 to FING_Z1, FING_IN mm further out than the
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
PANEL_XW = 18.0 * FE.K                          # panel half-width: the arch (BO.CHIN[0] x S = 17.5) + 0.5, where the base's front wall meets the body rim (brief 2026-11-24: by |x| 18)
PANEL_M = 0.8 * FE.K                            # the panel's top follows the arch ellipse grown by this: it fuses into the wall round the arch (wall 3.2)
PANEL_RAY = 0.15                         # the outer face is the skin's y this far above the arch edge (step to the skin <= 0.4)
PANEL_BASE_TOP = tuple((FE.K * a, FE.K * b) for a, b in ((0, 12.96), (4, 13.22), (8, 14.00), (12, 15.35), (14, 16.27), (16, 16.80), (18, 17.01)))   # |x|, base front wall top z: measured on the base (robot frame, brief 2026-11-24); 18 = body rim RIMR
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
    # the region spans the strip's own y (it was a fixed y -15..-45 from S 0.70: at S 1.0 the skin is at -50..-55 and
    # the panel came out empty, mouth open again; Morante saw it in the viewer 2026-11-28)
    ry0, ry1 = float(yo.min()) - 1.0, float(yo.max()) + PANEL_T + 1.0
    reg = extrude(Plane.XZ.offset(-ry1) * Polygon(*([(x, bt(x)) for x in xs] + top), align=None), ry1 - ry0)
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
        + [cyl(x, y, DR.M3_HEAD_R + F.STEEL.side, zf - 1.0, zf + zh) for x, y, zh, _ in DR.KEEL_SCREWS] \
        + [cyl(x, y, DR.M3_HOLE_R, zf + zh - 0.5, DR.ZKEEL0 + 1.0) for x, y, zh, _ in DR.KEEL_SCREWS]
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
SW_SLOT_Y = 12.0 * FE.K                             # lever slot length along y (through the back wall)
SW_KEEP_REACH = 0.0                          # keeper ribs/top bar reach this far behind the switch's back face (the switch sits embedded in the wall: they end on that face, inside the skin)
W_KEEP = F.WALL_MIN                                 # keeper wall (loaded, rules 3.2)
def led_pos(sx):
    """LED sx (+-1) axis point on the big eye's bore floor, robot frame (check.py: ex, ey, ez)."""
    return sx * BO.EYE_DX * S, (BO.EYE_BORE_BACK - ORIGIN[1]) * S, (BO.EYE_Z - ORIGIN[2]) * S
LEDB0, LEDB1 = 0.3 * FE.K, 1.3 * FE.K  # LED through-bore: from 0.3 behind the bore floor to 1.3 past it (cavity face is 0.7 past, ray scan of body.stl)
LEDF = 0.7 * FE.K                                   # the bore floor's back (cavity) face, behind led_pos's y (ray scan of body.stl): the LED's flange stops on it
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
    key = (_file_key("cad/body/build.py", "cad/eyes/build.py", "cad/robot/power.py"), S, srch(body_static, pocket_keepout, body_skin, eye_cups, snap_geometry, finger_root, front_panel, led_pos, to_robot),
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
    adds = cups + [finger_root(f) for _, f, _ in snap_geometry()] + keeper
    b = b0.fuse(front_panel(b0), tol=0.005).fuse(*adds)          # the panel first, fuzzy 0.005: its face (0.15 off the skin) crosses the skin at the arch apex and left a 0.02 mm2 face the mesher could not triangulate
    tw, ty0, ty1, tz = BO.TAB; ty = (ty0 - ORIGIN[1]) * S; dp, hx, z0, z1 = PKT
    cuts = [Pos(0, ty - 1.0, z0 - 0.5) * Box(2 * hx + 1.0, dp + 1.0, z1 - z0 + 1.0, align=(Align.CENTER, Align.MIN, Align.MIN)), pocket_keepout()]
    for sx in (-1, 1):
        x, y, z = led_pos(sx); cuts.append(cylA((x, y - LEDB0, z), LED_R + F.TURN.side, LEDB1 + LEDB0))
        cuts.append(cylA(((BO.CX + sx * BO.SEYE_DX - ORIGIN[0]) * S, (BO.SEYE_BACK - ORIGIN[1]) * S - LEDB0, (BO.SEYE_Z - ORIGIN[2]) * S), BO.SEYE_BORE * S, LEDB1 + LEDB0))
    cuts.append(Pos(-(lx / 2 + SW_THROW / 2 + st), y1 - 0.5, zs - lz / 2 - st) * Box(lx + SW_THROW + 2 * st, SW_SLOT_Y, lz + 2 * st, align=MIN))
    r = F.LOCATOR.side
    # switch pocket opened 2.5 forward into the cavity: the leaning back wall left a wedge in front of it (z 29.6-31.2)
    # that blocked the switch 0.25 out and met the fingertip (verify 2026-11-27)
    cuts.append(Pos(-(bx / 2 + r), y1 - by - r - 2.5, zs - bz / 2 - r) * Box(bx + 2 * r, 2.5, bz + 2 * r, align=MIN))
    for part in (PW.holder(), PW.lid(), PW.cells(), PW.switch()):
        for so in part.solids():
            q = so.bounding_box(); cuts.append(Pos(q.min.X - r, q.min.Y - r, q.min.Z - r) * Box(q.size.X + 2 * r, q.size.Y + 2 * r, q.size.Z + 2 * r, align=MIN))
    cuts += [Pos(-STRIP_X, STRIP_Y0, STRIP_Z0) * Box(2 * STRIP_X, STRIP_Y1 - STRIP_Y0, STRIP_Z1 - STRIP_Z0, align=MIN),
             Pos(-STRIP_X2, STRIP_Y0 - 0.5, STRIP_Z0) * Box(2 * STRIP_X2, STRIP_Y1 - STRIP_Y0 + 0.5, STRIP_Z2 - STRIP_Z0, align=MIN)]
    b = b.cut(*cuts); export_brep(b, p)
    import cutters as CU
    m = CU.mesh_of(b, 0.05, 0.3); np.savez(p + ".npz", v=m.vertices, f=m.faces); return b, m
def body():
    """the body: its fixed features (body_static, cached) and the legs' designed notches and pockets (cutters.body_cutters:
    one cut). Then every leg is checked against it at its 24 poses and while the
    body is put on (cutters.body_gaps)."""
    import cutters as CU
    _T0[0] = time.time()
    b, bm = body_static(); tick("skin + fixed features")
    legs = {Lg: leg_mesh(Lg) for Lg in range(8)}
    lc = CU.body_cutters(bm, {Lg: leg_mesh(Lg, samples=True) for Lg in range(8)}, leg_frame, PIV,
                         BRELD, F.NEIGHBOUR.side + 0.1, KC, CL.LIFTD, RIMR, reach=30.0); tick(f"{len(lc)} leg cutters")
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
    b = one(unify(b, faces_only=True)); tick("unify")
    assert b.is_valid and len(b.solids()) == 1, f"body: valid {b.is_valid}, {len(b.solids())} solids"
    for Lg, what, g, at in CU.body_gaps(CU.mesh_of(b, 0.05, 0.3), legs, leg_frame, KC, CL.LIFTD):
        need = 0.2 if what == "poses" else 0.1
        print(f"    [body] leg {Lg} {what:8s} min gap {g:.2f} at {at}{'  FAIL' if g < need else ''}", flush=True)
    tick("leg gaps"); print(f"    [body] volume {b.volume:.1f} mm3, {len(b.faces())} faces, valid, 1 solid", flush=True)
    return b

PARTS = {"base": base, "body": body, **{f"leg-{Lg}": (lambda Lg=Lg: leg(Lg)) for Lg in range(8)}}
