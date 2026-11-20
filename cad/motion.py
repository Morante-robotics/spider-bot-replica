"""The approved motion of the looks Spider-Bot: where the 8 legs sit, their shape in the neutral pose and how they move
over one crank turn. No mesh is read here.

These are the numbers Morante approved with the N0 mock-up (build log, «N0 mock-up»; the mock-up itself, which drew
jenscolt's body around them, is archived at the tag n2-on-meshes-2026-11-20). The legs design (`cad/legs/build.py
--edit`) bends its parts onto this path; the N2 design takes its scale, crank and leg path from here, never a copy.

Motion: the toy leg of sim/toy_leg_3d.py, "rows" axle, slide at the crank: four lateral crankshafts, one per pair of
notches; the leg turns about its pivot P (gimbal, sideways axis kept level) as its inner end follows the crank pin.
The leg's shape is given in the neutral pose (crank level) and carried rigidly in the leg's frame (u = P − A, side,
up).

Frame: mm, z up, forward = −Y, +X = robot's right (cad/README.md); origin on the body axis, z = 0 at the base's
bottom, at scale P0["S"].
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sim"))
import toy_leg_3d as TL  # noqa: E402  (notches, centre, gait groups: one source)

K120 = 1 / 1.2                                         # sim coordinates are jenscolt at 120 %
POSES = 24

# Every number in mm at the robot's scale; the leg sizes are jenscolt's × S unless noted.
P0 = dict(
    S=0.60,          # robot scale vs jenscolt, as approved at N0 (the N2 scale is decided again: build log)
    # crank (toy_leg_3d_rows_cad.json[0] × 0.5 = 60 % of jenscolt, rounded)
    r=2.0,           # crank throw
    XC=6.0,          # crank pins this far either side of the body axis
    H=-3.0,          # crankshafts this far below the notches (the base's bowl is narrow below)
    DY=-2.4,         # crankshafts shifted along Y from their notch pair
    # leg shape in the neutral pose (crank level), measured from the body axis in the notch's direction
    angles=(-45, -15, 15, 45),   # right legs front to rear: direction from the body axis, degrees from +X
    knee_r=44.0,     # knee: horizontal distance from the body axis (jenscolt ≈ 63 × S = 38)
    knee_z=46.0,     # knee: height above the base's bottom (dome top ≈ 49)
    foot_r=68.0,     # foot: horizontal distance from the body axis (jenscolt ≈ 83 × S = 50)
    foot_z=-8.0,     # foot: height above the base's bottom (< 0: the body stands clear of the ground)
    elbow=1.0,       # upper leg: 0 = straight from the pivot to the knee, 1 = out level first, then up
    up_arch=0.0,     # upper leg's bend raised by this much
    blade_top=6.0,   # blade goes on past the knee by this much (jenscolt ≈ 10 × S)
    blade_bow=4.0,   # blade bows outward by this much at its middle
    r_upper=4.0,     # upper leg radius at the knee (jenscolt leg2 ≈ Ø14 shaft × S)
    r_root=3.0,      # upper leg radius at the pivot (the middle notches are only ≈ 8 mm apart at 60 %)
    r_blade=6.0,     # blade radius at its thickest (jenscolt leg1 ≈ 23 × 10, a capsule of the same bulk)
    r_inner=1.5,     # inner arm radius
)

# The body's origin in the simulator's frame (jenscolt at 120 %): its axis, at the base's bottom.
ORIGIN = np.array([TL.CENTER[0] * K120, TL.CENTER[1] * K120, TL.BASE_BOTTOM * K120])


def to_frame(xyz, p=P0):
    """A point in jenscolt's frame at 100 % into the robot's frame at scale p["S"]."""
    return (np.asarray(xyz, float) - ORIGIN) * p["S"]


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def frame(u):
    """Leg frame for inner-arm directions u (N, 3): u, side (level), up."""
    side = unit(np.cross(np.array([0, 0, 1.0]), u))
    up = np.cross(side, u)
    return np.stack([u, side, up], -2)                 # (N, 3, 3), rows = axes


def bezier(a, c, b, n):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b


def pivot(i, p=P0):
    """Right leg i (front to rear): its pivot P in the base rim and its crank centre O (crank level: A0 = O + r·(−Y))."""
    x, y = TL.NOTCHES_RIGHT[i]
    P = to_frame((x * K120, y * K120, TL.NOTCH_Z * K120), p)
    O = np.array([p["XC"], P[1] + p["DY"], P[2] + p["H"]])
    return P, O


def leg_shape(P, A0, ang, p=P0, n=10):
    """Points (M, 3) and radii (M,) of one right leg in the neutral pose; A0 = crank pin at the level crank.
    Returns also the number of inner-arm points: inner arm, then upper leg (n points, P .. K), then blade (n + 4)."""
    rd = np.array([np.cos(ang), np.sin(ang), 0])
    K = np.array([p["knee_r"] * rd[0], p["knee_r"] * rd[1], p["knee_z"]])
    F = np.array([p["foot_r"] * rd[0], p["foot_r"] * rd[1], p["foot_z"]])
    inner = np.linspace(A0 - 2 * unit(P - A0), P, 6)[:-1]             # inner arm, a little past the pin
    e = p["elbow"]                                                    # 0: straight up to the knee, 1: out, then up
    C = np.r_[P[:2] + e * (K[:2] - P[:2]), P[2] + (1 - e) * (K[2] - P[2]) + p["up_arch"]]
    upper = bezier(P, C, K, n)
    kd = unit(K - F)
    top = K + p["blade_top"] * kd
    bmid = (top + F) / 2 + p["blade_bow"] * rd
    blade = bezier(top, 2 * bmid - (top + F) / 2, F, n + 4)
    t = np.linspace(0, 1, n + 4)
    rb = 2.0 + (p["r_blade"] - 2.0) * np.sin(np.pi * np.clip(t * 1.25, 0, 1)) ** 0.7
    rb[0] = max(rb[0], 2.5)
    pts = np.vstack([inner, upper, blade])
    rad = np.concatenate([np.full(len(inner), p["r_inner"]),
                          np.linspace(p["r_root"], p["r_upper"], n), rb])
    return pts, rad, len(inner)


def neutral_leg(i, p=P0, n=10):
    """Right leg i in the neutral pose: P, A0, its direction angle (rad), and leg_shape's points, radii, n_inner."""
    P, O = pivot(i, p)
    A0 = O + p["r"] * np.array([0, -1.0, 0])
    ang = np.radians(p["angles"][i])
    return (P, A0, ang) + leg_shape(P, A0, ang, p, n)


def legs(p=P0, poses=POSES):
    """Leg tubes over the crank turn: pts (8, poses, M, 3), radii (M,), n_inner, pivots (8, 3), crank pins (8, poses, 3).
    Legs 0-3 right front to rear, 4-7 left (mirrored in x)."""
    th = np.linspace(0, 2 * np.pi, poses, endpoint=False)
    allp, A_all, piv = [], [], []
    for side, sx in (("R", 1), ("L", -1)):
        for i in range(len(TL.NOTCHES_RIGHT)):
            P, O = pivot(i, p)
            ph = np.pi * TL.GROUP[side][i]
            A = O + p["r"] * (np.cos(th + ph)[:, None] * [0, -1, 0] + np.sin(th + ph)[:, None] * [0, 0, 1])
            _, A0, _, pts, rad, ni = neutral_leg(i, p)
            R0 = frame(unit(P - A0)[None])[0]
            loc = (pts - P) @ R0.T                                     # shape in the neutral leg frame
            R = frame(unit(P - A))                                     # (poses, 3, 3)
            W = P + np.einsum("mk,nkj->nmj", loc, R)
            if sx < 0:
                W, A, P = W * [-1, 1, 1], A * [-1, 1, 1], P * [-1, 1, 1]
            allp.append(W)
            A_all.append(A)
            piv.append(P)
    return np.array(allp), rad, ni, np.array(piv), np.array(A_all)
