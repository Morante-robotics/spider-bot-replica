#!/usr/bin/env python3
"""3D model of the toy leg on the whole robot: 8 legs, one crank per leg, two gait groups.

The toy leg is one rigid bent part. Its inner arm runs along the line from the crank pin A through a pivot P in a
notch of the base rim; past P it bends down (shin) to the foot F. Two ways to build the joints:
  - slide at body ("body"): the leg is fixed to the crank pin (ball joint) and slides through a sleeve at P;
    knee K = A + L1·u;
  - slide at crank ("crank"): the leg turns about a fixed point at P (gimbal) and the crank pin slides in a bore or
    slot at the leg's inner end; knee K = P + L1·u.
u = unit(P - A). The leg does not roll about its own axis: the gimbal at P keeps its sideways axis horizontal.
Shin direction d = cos(bend)·u + sin(bend)·(cos(sweep)·down + sin(sweep)·forward), so bend 90°, sweep 0° = straight
down, sweep > 0 = shin leaning forward.

Each crank turns about an axle through O = P - D·r + H·z (r = horizontal direction from the body centre to the
notch), in one of three directions: "lateral" (world X), "vertical" (Z) or "longitudinal" (Y, the walking
direction). How the 8 cranks are driven by one motor is not modelled here (next step).

All 8 legs are the same part (mirrored on the left). Gait: left 1 and 3 + right 2 and 4 against the other four,
cranks 180° apart. Quasi-static walk over one crank turn: the body is level and stands on its lowest feet; it moves
by what the lowest foot moves. Measured: stride per half turn, body bob, step height, feet slipping against each
other, static stability (body centre inside the supporting feet), gap between neighbouring legs, ground clearance
under the base, footprint, slide travel, pivot swing and pin tilt.

Coordinates as in cad/carcass-120/ (mm, 120 % scale): z up, ground of jenscolt's assembly at z = 0, forward = -Y.

Usage:
    python3 toy_leg_3d.py --search 20000 --json toy_leg.json          # search every axle × joint type
    python3 toy_leg_3d.py --params toy_leg.json --png a.png --gif b.gif  # measure and draw one geometry

Needs numpy and matplotlib (pillow for the GIF).
"""
import argparse
import json

import numpy as np

STEPS = 360
CENTER = np.array([42.72, -3.6])        # vertical axis of the body (cad/carcass-120 coordinates)
BASE_BOTTOM = 45.6                       # z of the base's lowest point
NOTCH_Z = 72.0                           # notches in the base rim span z 70-74
# Right-side notch centres, front to rear, measured on spideybot_base.stl (convex hull minus the rim slice at
# z = 71 and 73); the left ones are their mirror about x = CENTER[0].
NOTCHES_RIGHT = [(89.5, -32.2), (95.9, -12.6), (96.1, 2.9), (82.6, 31.1)]
GROUP = {"R": [0, 1, 0, 1], "L": [1, 0, 1, 0]}      # crank phase group (×180°) of legs 1-4, front to rear
CARCASS_XY = (121.4, 132.6)               # widest of base and body, X × Y (mm)

# targets (suggested in the build log, to confirm)
TARGETS = dict(lift=10.0, stride=25.0, bob=3.0, clearance=20.0, clearance_max=60.0, gap=3.0, width=270.0, length=185.0)
# --strict (shared crankshaft run): legs 5 mm thick, so 6 mm between centre lines, and a footprint close to the
# original's look (jenscolt's assembly at 120 %: 269 × 185 mm)
STRICT = dict(gap=6.0, width_min=240.0, length_min=165.0)

RANGES = dict(r=(3, 12), D=(8, 40), H=(-20, 8), L1=(5, 70), bend=(30, 150), sweep=(-45, 45), L2=(30, 120))
# "shaft": one lateral crankshaft for all 8 legs at y = Y0, z = NOTCH_Z + H; the 4 cranks of each side sit along it
# from XIN to XIN + 3·PITCH mm from the body axis, in one of the 24 orders (ORDER); left side mirrored.
SHAFT_RANGES = dict(r=(3, 12), Y0=(-25, 15), H=(-22, 0), XIN=(6, 25), PITCH=(8, 14), ORDER=(0, 23.999),
                    L1=(5, 70), bend=(30, 150), sweep=(-45, 45), L2=(30, 120))
# "sides": two longitudinal crankshafts (along Y), one per side, XS mm from the body axis at z = NOTCH_Z + H; each
# leg's crank sits on its side's shaft level with its notch, shifted DY mm along the shaft. The two shafts turn
# opposite ways (a spur gear pair), so the left side is the mirror image of the right.
SIDES_RANGES = dict(r=(3, 12), XS=(10, 50), H=(-22, 0), DY=(-10, 10),
                    L1=(5, 70), bend=(30, 150), sweep=(-45, 45), L2=(30, 120))
# "rows": four lateral crankshafts (along X), one per pair of legs, each level with its pair of notches (shifted DY
# mm along Y) at z = NOTCH_Z + H, with the left and right cranks XC mm either side of the body axis. Idler gears
# between neighbouring shafts make all four turn the same way.
# Buildable limits (CAD, 2026-11-09): XC >= 12 leaves room between a shaft's two cranks for a gear and two bearing
# walls; H <= -8 puts the shafts 8 mm under the rim so a module-1 gear fits under the battery holder (z 73).
ROWS_RANGES = dict(r=(3, 12), XC=(12, 45), H=(-22, -8), DY=(-10, 10),
                   L1=(5, 70), bend=(30, 150), sweep=(-45, 45), L2=(30, 120))
AXLES = ("lateral", "vertical", "longitudinal", "shaft", "sides", "rows")
SHAFTS = ("shaft", "sides", "rows")
SLIDES = ("crank", "body")


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def pivots():
    """(side, index, P xyz, outward unit r) for the 8 legs."""
    out = []
    for side, sx in (("R", 1), ("L", -1)):
        for i, (x, y) in enumerate(NOTCHES_RIGHT):
            px = CENTER[0] + sx * (x - CENTER[0])
            P = np.array([px, y, NOTCH_Z])
            r = np.array([px - CENTER[0], y - CENTER[1], 0.0])
            out.append((side, i, P, r / np.linalg.norm(r)))
    return out


def axle_basis(axle):
    """Axle direction and two in-plane unit vectors (the crank turns from e1 towards e2)."""
    X, Y, Z = np.eye(3)
    return {"lateral": (X, -Y, Z), "vertical": (Z, X, -Y), "longitudinal": (Y, X, Z), "shaft": (X, -Y, Z), "sides": (Y, X, Z), "rows": (X, -Y, Z)}[axle]


def ranges(axle):
    return {"shaft": SHAFT_RANGES, "sides": SIDES_RANGES, "rows": ROWS_RANGES}.get(axle, RANGES)


def crank_centre(p, axle, i, P, rhat):
    """Crank centre of right-side leg i (front to rear)."""
    if axle == "rows":
        return np.array([CENTER[0] + p["XC"], P[1] + p["DY"], NOTCH_Z + p["H"]])
    if axle == "sides":
        return np.array([CENTER[0] + p["XS"], P[1] + p["DY"], NOTCH_Z + p["H"]])
    if axle != "shaft":
        return P - p["D"] * rhat + np.array([0, 0, p["H"]])
    import itertools
    slot = list(itertools.permutations(range(4)))[int(p["ORDER"])][i]
    return np.array([CENTER[0] + p["XIN"] + p["PITCH"] * slot, p["Y0"], NOTCH_Z + p["H"]])


def solve_leg(p, axle, slide, P, rhat, theta, O):
    """Joint positions of one right-side leg for crank angles theta (array). Returns dict of (N, 3) arrays."""
    a, e1, e2 = axle_basis(axle)
    A = O + p["r"] * (np.cos(theta)[:, None] * e1 + np.sin(theta)[:, None] * e2)
    u = unit(P - A)
    fwd = unit(np.cross(np.array([0, 0, 1.0]), u))
    fwd = np.where((fwd[:, 1:2] > 0), -fwd, fwd)          # sideways axis of the leg, pointing forward (-Y)
    down = unit(np.cross(u, fwd))
    down = np.where(down[:, 2:3] > 0, -down, down)
    K = (A if slide == "body" else P) + p["L1"] * u
    b, s = np.radians(p["bend"]), np.radians(p["sweep"])
    d = np.cos(b) * u + np.sin(b) * (np.cos(s) * down + np.sin(s) * fwd)
    F = K + p["L2"] * d
    N = len(theta)
    return dict(O=np.tile(O, (N, 1)), A=A, P=np.tile(P, (N, 1)), K=K, F=F, u=u, a=a)


def mirror(pts):
    q = pts.copy()
    q[..., 0] = 2 * CENTER[0] - q[..., 0]
    return q


def simulate(p, axle, slide, steps=STEPS):
    """All 8 legs over one crank turn. Left legs are mirror images; with a vertical or longitudinal axle their cranks
    then turn the other way (reported, a gear pair does it)."""
    theta = np.linspace(0, 2 * np.pi, steps, endpoint=False)
    legs = []
    for side, i, P, rhat in pivots():
        ph = np.pi * GROUP[side][i]
        if side == "R":
            s = solve_leg(p, axle, slide, P, rhat, theta + ph, crank_centre(p, axle, i, P, rhat))
        else:   # mirrored part on a mirrored pivot; same physical motion of A in Y-Z for a lateral axle
            Pm, rm = mirror(P), rhat * np.array([-1, 1, 1])
            s = solve_leg(p, axle, slide, Pm, rm, theta + ph, crank_centre(p, axle, i, Pm, rm))
            s = {k: (mirror(v) if k not in ("u", "a") else v * np.array([-1, 1, 1])) for k, v in s.items()}
        s["side"], s["i"] = side, i
        # inner end E of the leg: just past the crank pin (slides at crank) or at the pin (slides at body)
        AP = np.linalg.norm(s["P"] - s["A"], axis=1)
        s["inner"] = AP.max() + 3 if slide == "crank" else 0.0
        s["E"] = s["P"] - s["inner"] * s["u"] if slide == "crank" else s["A"]
        legs.append(s)
    return theta, legs


def seg_dist(p1, q1, p2, q2):
    """Smallest distance between segments p1-q1 and p2-q2 (arrays of (N, 3)), sampled."""
    t = np.linspace(0, 1, 9)
    a = p1[:, None, :] + (q1 - p1)[:, None, :] * t[None, :, None]
    b = p2[:, None, :] + (q2 - p2)[:, None, :] * t[None, :, None]
    return np.linalg.norm(a[:, :, None, :] - b[:, None, :, :], axis=-1).min(axis=(1, 2))


_BASE = None


def base_slices():
    """Outer outline of the base every 1 mm from z 46 to 74, shrunk by a 2 mm wall (for the crankshaft check)."""
    global _BASE
    if _BASE is None:
        import os
        import trimesh
        from shapely.geometry import Polygon
        here = os.path.dirname(os.path.abspath(__file__))
        b = trimesh.load(os.path.join(here, "..", "cad", "carcass-120", "spideybot_base.stl"))
        _BASE = {}
        for z in range(47, 75):
            sec = b.section([0, 0, 1], [0, 0, z])
            if sec is not None:
                outer = max((Polygon(e) for e in sec.discrete if len(e) > 3), key=lambda q: q.area)
                _BASE[z] = outer.buffer(-2)
    return _BASE


def shaft_fit(p, legs):
    """How far (mm, summed) the crank discs (radius r + 2 for the pin head) stick out of the base (2 mm wall) or
    above z 73, where the battery holder starts."""
    from shapely.geometry import Point
    sl, out = base_slices(), 0.0
    R = p["r"] + 2
    for l in legs:
        O = l["O"][0]
        e = np.abs(l["a"])
        e1 = np.array([0, 1.0, 0]) if e[0] > 0.5 else np.array([1.0, 0, 0])    # horizontal, across the shaft
        for t in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            q = O + R * (np.cos(t) * e1 + np.sin(t) * np.array([0, 0, 1.0]))
            z = q[2]
            out += max(0, z - 73)
            zi = int(round(z))
            if zi not in sl:
                out += abs(z - np.clip(z, 47, 74)) + 2
                continue
            pt = Point(q[0], q[1])
            if not sl[zi].contains(pt):
                out += sl[zi].exterior.distance(pt)
    return out


LEG_HALF = 2.5      # half the leg thickness (5 mm legs)
PLAY = 1.0          # free space wanted between a leg and the crankshaft parts
SHAFT_R = 1.5       # 3 mm shaft
WEB = 4.0           # half width (along X) of one crank: web + pin head


def crank_clear(p, legs):
    """Smallest free space (mm) between any leg's inner arm E-P and the crankshaft parts it does not ride on: the
    other 7 cranks (discs of radius r + 2, WEB mm either side of their centre) and the bare 3 mm shaft. Negative =
    the arm cuts through them."""
    t = np.linspace(0, 1, 25)
    worst = np.inf
    if "XS" in p:
        shafts = [[l for l in legs if l["side"] == sd] for sd in "RL"]
    elif "XC" in p:
        shafts = [[l for l in legs if l["i"] == i] for i in range(4)]
    else:
        shafts = [legs]
    for shaft in shafts:                               # cranks on one shaft: centres on one line along axis a
        a = np.abs(shaft[0]["a"])
        O = np.array([l["O"][0] for l in shaft])
        o0 = O[0]
        cs = (O - o0) @ a                              # crank positions along the shaft
        lo, hi = cs.min() - WEB, cs.max() + WEB
        for l in legs:
            mine = [k for k, q in enumerate(shaft) if q is l]
            pts = l["E"][:, None, :] + (l["P"] - l["E"])[:, None, :] * t[None, :, None]   # (N, 25, 3)
            v = pts - o0
            x = v @ a
            d = np.linalg.norm(v - x[..., None] * a, axis=-1)
            own = np.abs(x - cs[mine[0]]) <= WEB if mine else np.zeros_like(x, bool)
            need = np.where((x >= lo) & (x <= hi) & ~own, SHAFT_R, -np.inf)
            for k in range(len(shaft)):
                if not mine or k != mine[0]:
                    need = np.where(np.abs(x - cs[k]) <= WEB, p["r"] + 2, need)
            free = d - need - LEG_HALF
            if np.isfinite(need).any():
                worst = min(worst, free[np.isfinite(need)].min())
    return worst


def measure(p, axle, slide, steps=STEPS, full=False, strict=False):
    theta, legs = simulate(p, axle, slide, steps)
    F = np.stack([l["F"] for l in legs])                  # (8, N, 3)
    zmin = F[:, :, 2].min(axis=0)                          # lowest foot at each crank angle
    ground = zmin.min()
    bob = np.ptp(zmin)
    support = F[:, :, 2] <= zmin[None, :] + 2.0            # feet carrying the body (within 2 mm of the lowest: it tilts onto them)
    lowest = F[:, :, 2].argmin(axis=0)
    n = F.shape[1]
    nxt = (np.arange(n) + 1) % n
    dF = F[:, nxt, :2] - F[:, :, :2]                       # foot motion relative to the body, per step
    ref = dF[lowest, np.arange(n)]                         # the body moves by minus the lowest foot's motion
    travel = -ref[:, 1].sum()                              # forward (-Y) body travel per turn
    stride = travel / 2
    slip = (np.linalg.norm(dF - ref[None], axis=-1) * support).sum() / 8   # mm of foot sliding per leg per turn
    sideways = abs(ref[:, 0].sum())                        # body drifts sideways per turn (should be ~0)
    lift = (F[:, :, 2].max(axis=1) - F[:, :, 2].min(axis=1)).min()
    # static stability: body centre inside the polygon of the supporting feet, smallest margin over the turn
    margin = np.inf
    for k in range(0, n, max(1, n // 120)):
        pts = F[support[:, k], k, :2]
        margin = min(margin, hull_margin(pts, CENTER))
    # gaps between legs on each side: neighbours only (outer arm P-K and shin K-F); with --strict every pair, and
    # the inner arm E-P too (inside the body the legs cross over the crankshaft)
    gap = np.inf
    for side in "RL":
        sl = [l for l in legs if l["side"] == side]
        segs = (("E", "P"), ("P", "K"), ("K", "F")) if strict else (("P", "K"), ("K", "F"))
        pairs = [(a, b) for j, a in enumerate(sl) for b in sl[j + 1:]] if strict else list(zip(sl, sl[1:]))
        for l1, l2 in pairs:
            for a1, b1 in segs:
                for a2, b2 in segs:
                    gap = min(gap, seg_dist(l1[a1], l1[b1], l2[a2], l2[b2]).min())
    # knee and foot must stay outside the body: further from the body axis than the pivot, by at least 5 mm
    reach = np.inf
    for l in legs:
        rp = np.linalg.norm(l["P"][0, :2] - CENTER)
        for k in ("K", "F"):
            reach = min(reach, (np.linalg.norm(l[k][:, :2] - CENTER, axis=1) - rp).min())
    allpts = np.concatenate([np.concatenate([l["K"], l["F"]]) for l in legs])
    width = max(np.ptp(allpts[:, 0]), CARCASS_XY[0])
    length = max(np.ptp(allpts[:, 1]), CARCASS_XY[1])
    m = dict(stride=stride, bob=bob, reach=reach, lift=lift, slip=slip, sideways=sideways, margin=margin, gap=gap,
             clearance=BASE_BOTTOM - ground, width=width, length=length, crank=p["r"],
             crank_axle_height=NOTCH_Z + p["H"] - ground, strict=strict,
             shaft_out=shaft_fit(p, legs) if axle in SHAFTS else 0.0,
             crank_clear=crank_clear(p, legs) if axle in SHAFTS else np.inf)
    if full:
        l0 = legs[1]                                      # right middle-front leg
        AP = np.linalg.norm(l0["P"] - l0["A"], axis=1)
        u = l0["u"]
        yaw = np.degrees(np.arctan2(u[:, 1], u[:, 0]))
        pitch = np.degrees(np.arcsin(u[:, 2]))
        tilt = np.degrees(np.arccos(np.clip(np.abs(u @ l0["a"]), 0, 1)))   # angle between leg and crank pin axis
        slide_travel = max(np.ptp(np.linalg.norm(l["P"] - l["A"], axis=1)) for l in legs)
        m.update(slide_travel=slide_travel, pivot_yaw=np.ptp(yaw), pivot_pitch=np.ptp(pitch),
                 pin_angle=(tilt.min(), tilt.max()), A_to_P=(AP.min(), AP.max()),
                 inner=[l["inner"] for l in legs[:4]], crank_x=[l["O"][0, 0] for l in legs[:4]],
                 crank_y=[l["O"][0, 1] for l in legs[:4]],
                 left_turns_other_way=axle not in ("lateral", "shaft", "rows"))
        return m, theta, legs, ground, support
    return m


def hull_margin(pts, c):
    """Signed distance from c to the edge of the convex hull of pts (positive inside); -50 if < 3 points."""
    if len(pts) < 3:
        return -50.0
    from scipy.spatial import ConvexHull
    try:
        h = ConvexHull(pts)
    except Exception:
        return -50.0
    # each facet: normal·x + offset <= 0 inside
    d = -(h.equations[:, :2] @ c + h.equations[:, 2])
    return d.min()


def score(m):
    t = dict(TARGETS, **STRICT) if m["strict"] else TARGETS
    pen = (max(0, m["bob"] - t["bob"]) * 4 + max(0, t["lift"] - m["lift"]) * 2
           + max(0, t["clearance"] - m["clearance"]) + max(0, m["clearance"] - t["clearance_max"]) + max(0, t["gap"] - m["gap"]) * 10 + max(0, 5 - m["reach"]) * 3
           + max(0, m["width"] - t["width"]) + max(0, m["length"] - t["length"])
           + max(0, 5 - m["margin"]) * 3 + m["slip"] * 0.5 + m["sideways"]
           + m["shaft_out"] * 3 + (max(0, PLAY - m["crank_clear"]) * 10 if m["strict"] else 0) + max(0, t.get("width_min", 0) - m["width"]) * 0.5
           + max(0, t.get("length_min", 0) - m["length"]) * 0.5)
    return m["stride"] - pen


def random_params(rng, axle="lateral"):
    return {k: float(rng.uniform(*v)) for k, v in ranges(axle).items()}


def search(axle, slide, tries, rng, strict=False):
    best = None
    R = ranges(axle)
    for _ in range(tries):
        p = random_params(rng, axle)
        try:
            m = measure(p, axle, slide, steps=120, strict=strict)
        except Exception:
            continue
        if not np.isfinite(score(m)):
            continue
        if best is None or score(m) > best[0]:
            best = (score(m), p)
    # local refinement around the best
    sc, p = best
    step = {k: (v[1] - v[0]) * 0.08 for k, v in R.items()}
    for it in range(tries // 4):
        q = {k: float(np.clip(p[k] + rng.normal(0, step[k]), *R[k])) for k in p}
        m = measure(q, axle, slide, steps=120, strict=strict)
        s = score(m)
        if np.isfinite(s) and s > sc:
            sc, p = s, q
        if it % 500 == 499:
            step = {k: v * 0.7 for k, v in step.items()}
    return p


def row(axle, slide, m):
    ok = lambda b: "yes" if b else "no"
    return (f"| {axle} | {slide} | {m['stride']:.0f} | {m['bob']:.1f} | {m['lift']:.0f} | {m['slip']:.0f} "
            f"| {ok(m['margin'] > 0)} ({m['margin']:.0f}) | {m['gap']:.1f} | {m['clearance']:.0f} "
            f"| {m['width']:.0f} × {m['length']:.0f} | {ok(m['reach'] >= 5)} | {m['crank']:.1f} |")


HEADER = ("| Crank axle | Slides at | Stride per half turn (mm) | Body bob (mm) | Step height (mm) "
          "| Feet slip (mm per leg per turn) | Stable all turn (margin mm) | Gap between legs (mm) "
          "| Clearance under base (mm) | Footprint X × Y (mm) | Knee and foot outside the body | Crank radius (mm) |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|---|")


def draw(results, png=None, gif=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(results)
    colors = {"R": "#c0392b", "L": "#2471a3"}

    def frame(fig, axs, k):
        for col, (title, m, theta, legs, ground, support) in zip(axs.T, results):
            for ax, (i, j, lab) in zip(col, ((0, 1, "top (X, Y) · forward ↑"), (1, 2, "side (Y, Z) · forward ←"))):
                ax.clear()
                ax.axhline(ground, color="#888", lw=1) if i == 1 else None
                ax.add_patch(plt.Rectangle((CENTER[0] - 60.7, -60) if i == 0 else (-60, BASE_BOTTOM),
                                           121.4 if i == 0 else 103.6, 104 if i == 0 else 26.4,
                                           fc="#ddd", ec="#aaa", zorder=0))
                for l in legs:
                    c = colors[l["side"]]
                    F = l["F"]
                    ax.plot(F[:, i], F[:, j], color=c, lw=0.8, alpha=0.5)
                    q = k % len(theta)
                    pts = np.array([l["O"][q], l["A"][q], l["E"][q], l["P"][q], l["K"][q], l["F"][q]])
                    ax.plot(pts[:2, i], pts[:2, j], "-", color="#555", lw=1.5)
                    ax.plot(pts[2:, i], pts[2:, j], "-o", color=c, lw=2, ms=2)
                    ax.plot(*pts[1, [i, j]], "o", color="#555", ms=3)
                ax.set_aspect("equal")
                if i == 0:
                    ax.invert_yaxis()
                    ax.set_title(title, fontsize=9)
                else:
                    ax.invert_xaxis()
                ax.set_xlabel(lab, fontsize=8)
                ax.grid(alpha=0.25)
                ax.tick_params(labelsize=7)

    fig, axs = plt.subplots(2, n, figsize=(4.2 * n, 8), squeeze=False)
    if png:
        frame(fig, axs, 0)
        plt.tight_layout()
        fig.savefig(png, dpi=80)
        print(f"wrote {png}")
    if gif:
        from matplotlib.animation import FuncAnimation, PillowWriter
        frames = 36
        nst = len(results[0][2])
        anim = FuncAnimation(fig, lambda f: frame(fig, axs, f * nst // frames), frames=frames)
        plt.tight_layout()
        anim.save(gif, writer=PillowWriter(fps=12), dpi=55)
        print(f"wrote {gif}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search", type=int, help="random tries per axle × slide combination")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--params", help="JSON from --json: measure these instead of searching")
    ap.add_argument("--strict", action="store_true", help="6 mm between legs (all pairs, inner arms too), a "
                    "footprint of at least 240 × 165 mm and, on a crankshaft, 1 mm between every inner arm and the "
                    "cranks and shaft it does not ride on")
    ap.add_argument("--only", help="search one combination, e.g. vertical/crank")
    ap.add_argument("--json", help="write the best geometry of every combination here")
    ap.add_argument("--png")
    ap.add_argument("--gif")
    args = ap.parse_args()

    if args.params:
        sets = json.load(open(args.params))
    else:
        rng = np.random.default_rng(args.seed)
        sets = []
        combos = [tuple(args.only.split("/"))] if args.only else [(a, s) for a in AXLES for s in SLIDES]
        for axle, slide in combos:
            p = search(axle, slide, args.search or 4000, rng, args.strict)
            sets.append(dict(axle=axle, slide=slide, strict=args.strict, **{k: round(v, 2) for k, v in p.items()}))
            print(f"searched {axle} / {slide}", flush=True)
        if args.json:
            json.dump(sets, open(args.json, "w"), indent=1)
            print(f"wrote {args.json}")

    print("\n" + HEADER)
    results = []
    for s in sets:
        p = {k: s[k] for k in ranges(s["axle"])}
        m, theta, legs, ground, support = measure(p, s["axle"], s["slide"], steps=360, full=True,
                                                  strict=s.get("strict", False))
        print(row(s["axle"], s["slide"], m))
        results.append((s, m, theta, legs, ground, support))
    print()
    for s, m, *_ in results:
        geo = ", ".join(f"{k} {s[k]:g}" for k in ranges(s["axle"]))
        print(f"{s['axle']} / {s['slide']}: {geo} | crank axle {m['crank_axle_height']:.0f} mm above ground, "
              f"A-P {m['A_to_P'][0]:.0f}-{m['A_to_P'][1]:.0f} mm, slide {m['slide_travel']:.1f} mm, pivot swing "
              f"yaw {m['pivot_yaw']:.0f}° pitch {m['pivot_pitch']:.0f}°, leg-to-pin angle {m['pin_angle'][0]:.0f}-"
              f"{m['pin_angle'][1]:.0f}°, body drifts sideways {m['sideways']:.1f} mm/turn"
              + (", left cranks turn the other way" if m["left_turns_other_way"] else "")
              + f", inner arm past P (R1-R4) {' / '.join(f'{l:.0f}' for l in m['inner'])} mm"
              + (f", cranks stick out of the base {m['shaft_out']:.1f} mm, free space arm to crankshaft "
                 f"{m['crank_clear']:.1f} mm, crank centres x "
                 f"{' / '.join(f'{x:.1f}' for x in m['crank_x'])} y {' / '.join(f'{y:.1f}' for y in m['crank_y'])}"
                 if s["axle"] in SHAFTS else ""))
    if args.png or args.gif:
        draw([(f"{s['axle']} axle, slides at {s['slide']}\nstride {m['stride']:.0f} · step {m['lift']:.0f} · "
               f"bob {m['bob']:.1f} mm", m, th, lg, gr, sp) for s, m, th, lg, gr, sp in results],
             args.png, args.gif)


if __name__ == "__main__":
    main()
