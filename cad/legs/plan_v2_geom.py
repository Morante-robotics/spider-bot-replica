#!/usr/bin/env python3
"""Legs v2 plan: candidate leg geometry (mock-up meshes, not the model), shared by the plan figure and its probes.

Every candidate keeps the mechanism of today's legs (build.py): pivot P on the rim, fork, inner tube on the crank's
ball, rigid leg. What changes is the leg outside the fork (x > X_CUT in the leg frame: P at the origin, X along the
leg outward, Z up, Y = Z × X; see build.py leg_frame()):

  today   the built out/leg-*-right.stl (5 × 6 bar, straight arm and shin)
  A       one-piece arched leg, same feet: arm rises to a high knee, shin down to today's foot; thin across (5 mm,
          the middle shins' 0.8 gap), deep in the leg's plane (the face the photo shows)
  B       as A, thick across (8 mm), with room made by spreading the feet: per-leg sweep (front and middle-1 forward,
          middle-2 and rear back); same pivots, forks, crankshafts; foot height kept by L2 / cos(sweep)
  C       today's leg + a screwed-on shell (hollow hood 1.2 wall over the bar, 0.2 gap): straight, 7.8 across
  B'      as B, 5 mm across (today's) from the fork out along the straight root, widening to 8 by the knee
  B2      (B'' in the plan) as B', also 5 across at the knee: 8 only along the shin (B's middle knees touched)
  D       as B's section, room made by moving the middle forks 5 mm apart on the rim (crank centres kept: DY per leg)
  rev 3 (Morante 2026-11-17: the shin's bed face >= RAISE above the bed all along, foot included):
  B3      B2 (B'') with the shin raised: front and middle-1 feet swept forward (-Y) print on their +Y face (bed = +1)
  Bs      small sweep +5/+5/-5/-5, shin 6.5 across, raised; front and middle-1 print on +Y
  Bb      sweep +2/+2/-8/-8, shin 7 across, raised; every leg prints on -Y as today (no leg flipped)

Inner part (tube, bar through the fork, boss) is today's built mesh cut at X_CUT, for every option.
"""
import functools
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import common as K, design  # noqa: E402

L = design("legs")
sim, P_ = K.sim, K.P_
NAMES = ["front", "middle", "middle", "rear"]

X_CUT = 7.0          # today's leg kept inside this (tube, fork bar, boss: the mechanism)
KNEE = (42.0, 30.0)  # arched options: knee (x, z) in the leg frame; z 30 puts it at world z ~ 105-115
FEMUR_H = (6.0, 14.0)   # depth in the leg's plane, at the root (today's LEG_H) and at the knee
ROOT_X = 18.0        # the upper segment stays today's straight 6-deep bar from the fork out to here, then rises
                     # (probe g1, 2026-11-17: rising from x 5.5 touched the body and forks; plan E's shells were clear
                     # from x 16-20)
SHIN_H = (14.0, 7.0)    # at the knee and at the foot
KNEE_R = 8.0         # round knee boss (black in the photo)
FOOT_R = 2.25        # today's foot sphere (Ø4.5): the shin's tip must clear the bed by RAISE too
OPTIONS = {
    "A": dict(w=5.0, sweep=[0, 0, 0, 0], dpiv=[0, 0, 0, 0]),
    "B": dict(w=8.0, sweep=[14, 10, -10, -14], dpiv=[0, 0, 0, 0]),
    "B'": dict(w=8.0, w_root=5.0, sweep=[14, 10, -10, -14], dpiv=[0, 0, 0, 0]),   # B, 5 across near the fork
    "B2": dict(w=8.0, w_root=5.0, w_knee=5.0, sweep=[14, 10, -10, -14], dpiv=[0, 0, 0, 0]),  # B', knee 5 too
    "C": dict(w=7.8),
    "D": dict(w=8.0, sweep=[0, 0, 0, 0], dpiv=[0, -5.0, 5.0, 0]),
    "B3": dict(w=8.0, w_root=5.0, w_knee=5.0, sweep=[14, 10, -10, -14], dpiv=[0, 0, 0, 0], raise_=1.0),
    "Bs": dict(w=6.5, w_root=5.0, w_knee=5.0, sweep=[5, 5, -5, -5], dpiv=[0, 0, 0, 0], raise_=1.0),
    "Bb": dict(w=7.0, w_root=5.0, w_knee=5.0, sweep=[2, 2, -8, -8], dpiv=[0, 0, 0, 0], raise_=1.0),
}


def bed_side(i, opt):
    """-1: the leg prints on its -Y face (today's); +1: on its +Y face (a foot swept forward, -Y, would go under the
    -Y bed). Only options with raise_ choose; the others print on -Y."""
    o = OPTIONS[opt]
    if "raise_" not in o:
        return -1
    yf = foot(o["sweep"][i])[1] + L.ARM_DY
    return -1 if yf - FOOT_R >= -L.TUBE_W / 2 + o["raise_"] else 1


def pivots(dpiv=(0, 0, 0, 0)):
    """Right-side (i, P, rhat, O): D moves P along Y (the rim) and keeps O (the crankshafts)."""
    out = []
    for side, i, P, rhat in sim.pivots():
        if side != "R":
            continue
        O = sim.crank_centre(P_, "rows", i, P, rhat)
        P2 = P + np.array([0, dpiv[i], 0])
        out.append((i, P2, K.unit(P2 - [K.CX, sim.CENTER[1], P2[2]]), O))
    return out


def poses(theta, dpiv=(0, 0, 0, 0)):
    """Right legs at crank angle theta: (i, 4x4 leg matrix, 4x4 fork matrix)."""
    out = []
    for i, P, rhat, O in pivots(dpiv):
        ph = np.pi * sim.GROUP["R"][i]
        s = sim.solve_leg(P_, "rows", "crank", P, rhat, np.array([theta + ph]), O)
        u = s["u"][0]
        Ml, My = np.eye(4), np.eye(4)
        Ml[:3, :3], Ml[:3, 3] = L.leg_frame(u), P
        My[:3, :3], My[:3, 3] = K.rot_z(np.arctan2(u[1], u[0])), P
        out.append((i, Ml, My))
    return out


def foot(sweep_deg):
    """Foot in the leg frame for a sweep (deg); L2 stretched so the foot stays at today's height."""
    b, s0, s = np.radians(P_["bend"]), np.radians(P_["sweep"]), np.radians(P_["sweep"] + sweep_deg)
    L2 = P_["L2"] * np.cos(s0) / np.cos(s)
    return np.array([P_["L1"] + L2 * np.cos(b), -L2 * np.sin(b) * np.sin(s), -L2 * np.sin(b) * np.cos(s)])


def bezier(p0, c, p1, n):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


def sweep_tube(path, w, h, flat_y=None):
    """Octagon section (w across along Y, h in the leg's plane) swept along path; flat_y: -Y face at this y (the face
    on the bed when printed), else centred."""
    path = np.asarray(path, float)
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    ring = []
    for k, (p, t) in enumerate(zip(path, tang)):
        y = np.array([0, 1.0, 0])
        nrm = np.cross(t, y)
        nrm /= np.linalg.norm(nrm)
        y = np.cross(nrm, t)
        ww, hh = w[k] / 2, h[k] / 2
        c = 0.3 * min(ww, hh)
        sec = [(-ww, -hh + c), (-ww, hh - c), (-ww + c, hh), (ww - c, hh), (ww, hh - c), (ww, -hh + c),
               (ww - c, -hh), (-ww + c, -hh)]
        if flat_y is None:
            off = 0.0
        elif np.ndim(flat_y) == 0:
            off = flat_y + ww                             # flat_y: -Y face's offset from the path
        else:
            fy, sd = flat_y[k]                            # per point (offset, side): side -1 -Y face, +1 +Y face
            off = fy + ww if sd < 0 else fy - ww
        ring.append([p + (a + off) * y + b * nrm for a, b in sec])
    V = np.array(ring).reshape(-1, 3)
    n, m = len(path), 8
    F = []
    for k in range(n - 1):
        for j in range(m):
            a, b = k * m + j, k * m + (j + 1) % m
            F += [[a, b, b + m], [a, b + m, a + m]]
    V = np.vstack([V, path[0], path[-1]])
    for j in range(m):
        F.append([n * m, (j + 1) % m, j])
        F.append([n * m + 1, (n - 1) * m + j, (n - 1) * m + (j + 1) % m])
    t = trimesh.Trimesh(V, np.array(F), process=True)
    trimesh.repair.fix_normals(t)
    return t


@functools.lru_cache(maxsize=None)
def today(i):
    return trimesh.load(L.stl(f"leg-{NAMES[i]}-right"))


@functools.lru_cache(maxsize=None)
def inner(i):
    return trimesh.intersections.slice_mesh_plane(today(i), [-1, 0, 0], [X_CUT, 0, 0], cap=True)


def arched(i, opt):
    """Outer leg of an arched option, in the leg frame (A, B, D). Returns (mesh, foot)."""
    o = OPTIONS[opt]
    F = foot(o["sweep"][i])
    w = o["w"]
    kx, kz = KNEE
    p0 = np.array([X_CUT - 1.5, L.ARM_DY, 0.0])
    kn = np.array([kx, L.ARM_DY, kz])
    r0 = np.array([ROOT_X, L.ARM_DY, 0.0])
    straight = np.linspace(p0, r0, 8)[:-1]                      # today's bar, unchanged height, out to ROOT_X
    rise = bezier(r0, np.array([ROOT_X + (kx - ROOT_X) * 0.35, L.ARM_DY, kz * 0.9]), kn, 20)
    fem = np.vstack([straight, rise])
    sh = bezier(kn, np.array([kx + 12, (kn[1] + F[1]) / 2, kz * 0.1]), F + [0, L.ARM_DY, 0], 28)
    n1, n2 = len(fem), len(sh)
    hf = np.concatenate([np.full(len(straight), FEMUR_H[0]), np.linspace(*FEMUR_H, len(rise))])
    wr = o.get("w_root", w)                                     # width across at the root (B': 5, as today)
    wk = o.get("w_knee", w)                                     # across at the knee (B2: 5, the middle knees met)
    wf = np.concatenate([np.full(len(straight), wr), np.linspace(wr, wk, len(rise))])
    hs = np.linspace(*SHIN_H, n2)
    ws = np.linspace(w, max(4.5, w - 2.0), n2) if wk == w else \
        np.interp(np.linspace(0, 1, n2), [0, 0.4, 1], [wk, w, max(4.5, w - 2.0)])   # B2: 8 only along the shin
    flat = -L.TUBE_W / 2
    off = flat - L.ARM_DY          # -Y face flush with the tube's (the face on the bed), relative to the path
    rz = o.get("raise_")
    if rz is None:
        parts = [sweep_tube(fem, wf, hf, off), sweep_tube(sh, ws, hs, off)]
        ky = flat + wk / 2
    else:                          # rev 3: shin's bed face >= rz above the bed all along, foot sphere included
        sd = bed_side(i, opt)
        bed = sd * L.TUBE_W / 2    # the bed plane in the leg frame
        if sd > 0:                 # +Y face down: the femur's +Y face flush with the tube's, clear of the fork window
            keep = fem[:, 0] > X_CUT - 0.5
            fem = np.vstack([[X_CUT - 0.5, L.ARM_DY, 0.0], fem[keep]])
            hf, wf = np.concatenate([hf[:1], hf[keep]]), np.concatenate([wf[:1], wf[keep]])
        t = np.linspace(0, 1, n2)
        yf = F[1] + L.ARM_DY
        face = (bed - sd * rz) + t * ((min(bed - rz, yf + FOOT_R) if sd > 0 else max(bed + rz, yf - FOOT_R))
                                      - (bed - sd * rz))
        parts = [sweep_tube(fem, wf, hf, [(bed - L.ARM_DY, sd)] * len(fem)),
                 sweep_tube(sh, ws, hs, [(face[k] - sh[k, 1], sd) for k in range(n2)])]
        ky = bed - sd * wk / 2
    knee = trimesh.creation.cylinder(radius=KNEE_R, height=wk, sections=32)
    knee.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    knee.apply_translation([kn[0], ky, kn[2]])
    parts.append(knee)
    return trimesh.util.concatenate(parts), F, (trimesh.util.concatenate(parts[:2]), knee)


def shell_c(i):
    """C: hollow hood over today's bar (arm and shin), outer 7.8 across, 1.2 wall, 0.2 gap. Mesh = the shell's outer
    envelope minus nothing (mass counts the walls only, see probe)."""
    b, s = np.radians(P_["bend"]), np.radians(P_["sweep"])
    Kn = np.array([P_["L1"], L.ARM_DY, 0])
    F = foot(0) + [0, L.ARM_DY, 0]
    arm = np.linspace([X_CUT + 9.0, L.ARM_DY, 0], Kn, 12)
    shin = np.linspace(Kn, F - (F - Kn) / np.linalg.norm(F - Kn) * 6, 14)
    g = 2 * (1.2 + 0.2)
    return trimesh.util.concatenate([sweep_tube(arm, np.full(12, L.LEG_W + g), np.full(12, L.LEG_H + g)),
                                     sweep_tube(shin, np.full(14, L.SHIN_W + g), np.full(14, L.LEG_H + g))])


def leg_mesh(i, opt):
    """Whole right leg i for an option, in the leg frame."""
    if opt == "today":
        return today(i)
    if opt == "C":
        return trimesh.util.concatenate([today(i), shell_c(i)])
    return trimesh.util.concatenate([inner(i), arched(i, opt)[0]])


def outer_mesh(i, opt):
    """Only the new part (what the probes check against everything)."""
    if opt == "today":
        return trimesh.intersections.slice_mesh_plane(today(i), [1, 0, 0], [X_CUT, 0, 0], cap=True)
    if opt == "C":
        return shell_c(i)
    return arched(i, opt)[0]
