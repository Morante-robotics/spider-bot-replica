#!/usr/bin/env python3
"""Size the N20 gear motor of the Spider-Bot from the robot's mass and the simulator's leg kinematics.

The plan's formulas, each number printed:
  crank torque  ≈ force lifting/pushing the legs × crank radius, here by virtual work over one crank turn;
  motor torque  = crank torque / (reduction × efficiency), efficiency 0.5 for printed gears (0.7 best case);
  working torque ≤ 1/3 of the motor's stall torque (margin ≥ 3), checked at 4.8 V and at 4.0 V (flat NiMH);
  runtime (h)   ≈ mAh × 0.8 / mean mA.

Steps: 1 mass (from the STLs and the printed plates), 2 worst crank torque over a turn, 3 target crank speed,
4 where the motor meshes with the gear train and whether its body fits, 5 N20 tables (Pololu, measured at 6 V)
scaled to 4.8 / 4.0 V, 6 ratios that meet speed and margin, current and runtime.

Load model (quasi-static, as the simulator's walk): the body is level and stands on its support feet (within 2 mm
of the lowest, the simulator's rule). In the body frame each foot F_i moves by dF_i/dθ; the ground pushes it with
R_i = (f_i, N_i). Virtual work on a frictionless massless leg pivoted at P: τ_i = −R_i · dF_i/dθ. The lowest foot
grips; the other support feet slip on the ground (friction μ_g N_i against their slip), so the cranks pay
  vertical: −Σ N_i dFz_i/dθ (lifting the body: the bob)   +   slip: μ_g Σ N_i |dF_i − dF_lowest|/dθ.
How the weight splits over 3-5 feet is statically indeterminate, so two cases: "even" (least squares with the
centre of mass on the body axis) and "worst" (the split, with the centre of mass anywhere in a ±5 mm box, that needs
the most torque: a linear program). On top, the printed joints' friction (ball in the leg's bore, the leg's M3
pivot screws, the crankshaft journals) from the leg's statics, and lifting the legs' own weight. Each leg's torque is
counted per crankshaft (its two legs share one printed part) and only when positive (no energy given back through
the printed gears).

Usage:  uv run python sim/motor_sizing.py > sim/motor-sizing-result.txt
"""
import json
import os
import sys

import warnings

import numpy as np
from scipy.optimize import linprog, nnls

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import toy_leg_3d as sim  # noqa: E402

G = 9.81
KGCM = 0.0980665     # N·m per kg·cm
NMM_PER_KGCM = 98.0665

# --- 1 · mass ----------------------------------------------------------------------------------------------------
PLA = 1.24           # g/cm³
WALL_CM = 0.084      # 2 wall loops (0.42 mm) a side, Bambu 0.20 mm Standard, counted over the mesh's whole surface
INFILL = 0.15        # sparse infill of the rest (Standard preset)


def printed_g(vol_cm3, area_cm2):
    """Printed mass of a closed mesh: a skin WALL_CM thick over its whole area, the rest at INFILL."""
    shell = min(vol_cm3, area_cm2 * WALL_CM)
    return PLA * (shell + (vol_cm3 - shell) * INFILL)


def mesh(path):
    import trimesh
    m = trimesh.load(os.path.join(ROOT, path))
    return m.volume / 1000, m.area / 100


def mass_table():
    rows = []
    v, a = mesh("cad/base/out/base-v1.stl")
    est = printed_g(v, a)
    rows.append(("Base v1 (print report, part only)", 82.3,
                 f"measured; check of the shell model: {v:.1f} cm³, {a:.0f} cm² → {est:.1f} g ({est / 82.3 - 1:+.0%})"))
    rows.append(("Front block (print report)", 23.4, "measured"))
    rows.append(("Cap (print report)", 5.8, "measured"))
    v, a = mesh("cad/carcass-120/spideybot_body.stl")
    rows.append(("Body, carcass at 120 % (shell model)", printed_g(v, a),
                 f"{v:.0f} cm³, {a:.0f} cm², mean wall {20 * v / a:.1f} mm: 0.84 mm skin + 15 % infill"))
    eyes = sum(printed_g(*mesh(f"cad/carcass-120/spideybot_{n}.stl")) * k
               for n, k in (("eye", 2), ("small_eye", 2), ("sensor", 1)))
    rows.append(("Eyes and sensor, printed", eyes, "shell model"))
    rows.append(("8 legs + 8 forks (legs-forks-v1 plate)", 46.9, "measured plate, incl. ~2 g support"))
    v = sum(mesh(f"cad/crankshafts/out/{n}.stl")[0] for n in
            ("crankshaft-1", "crankshaft-2", "crankshaft-3", "crankshaft-4", "idler-1", "idler-2", "idler-3"))
    rows.append(("4 crankshafts + 3 idlers", v * PLA, f"{v:.2f} cm³, solid"))
    rows.append(("Motor mount, motor gear (printed, guess)", 4.0, "guess"))
    rows.append(("4 × AAA NiMH", 4 * 12.0, "~12 g each"))
    rows.append(("4×AAA holder, switch, cover", 20.0, "typical, empty"))
    rows.append(("N20 gear motor", 10.0, ""))
    rows.append(("Screws, nuts, pins", 8 * (1.2 + 0.4) + 19 * (0.9 + 0.25) + 3 * 0.5,
                 "8 M3×16 + lock nuts, 19 M3×10 + nuts, 3 Ø3 pins"))
    rows.append(("Wiring", 5.0, "guess"))
    rows.append(("Eyes board (perfboard, LEDs, resistors)", 5.0, "guess"))
    return rows


MARGIN = 0.15        # on the total: base v2, glue, a heavier holder, a different infill


# --- 2 · crank torque ---------------------------------------------------------------------------------------------
STEPS = 720
SUPPORT_MM = 2.0     # support feet: within this of the lowest (the simulator's rule)
COM_BOX = 5.0        # worst case: centre of mass anywhere within ±5 mm (x and y) of the body axis
MU_GROUND = (0.4, 0.6)  # PLA foot on a desk (laminate/wood) ... a grippy or rough surface
MU_PLA = 0.35        # printed on printed, dry: ball in the leg's bore, journals in the spine
MU_STEEL = 0.25      # M3 screw in PLA: the leg's pivot and the fork's swivel
BALL_R = 1.8         # ball on the crank pin (cad/crankshafts BALL / 2)
JOURNAL_R = 2.0      # crankshaft journal (JOURNAL / 2)
SCREW_R = 1.5        # M3 pivot screws
LEG_G = 5.9          # one leg + its fork (46.9 g plate / 8), weight taken at the knee


def kinematics():
    geo = json.load(open(os.path.join(HERE, "toy_leg_3d_rows_cad.json")))[0]
    p = {k: geo[k] for k in sim.ranges("rows")}
    theta, legs = sim.simulate(p, "rows", "crank", steps=STEPS)
    m = sim.measure(p, "rows", "crank", steps=STEPS, strict=True)
    d = lambda x: (np.roll(x, -1, axis=0) - np.roll(x, 1, axis=0)) / (2 * (theta[1] - theta[0]))   # per rad
    for l in legs:
        l["dF"] = d(l["F"])
        l["dK"] = d(l["K"])
        AP = np.linalg.norm(l["P"] - l["A"], axis=1)
        l["dAP"] = d(AP[:, None])[:, 0]
        u = l["u"]
        l["dyaw"] = d(np.unwrap(np.arctan2(u[:, 1], u[:, 0]))[:, None])[:, 0]
        l["dpitch"] = d(np.arcsin(u[:, 2])[:, None])[:, 0]
    return p, m, theta, legs


def joint_friction(l, k, R):
    """Crank torque (N·mm per rad) lost in leg l's printed joints at step k when the ground pushes its foot with R
    (N). Statics of the leg: the crank pin pushes across the bore (F_A ⟂ u), the gimbal at P takes the rest and no
    moment about its two axes (vertical swivel, horizontal pivot screw)."""
    u, P, A, F = l["u"][k], l["P"][k], l["A"][k], l["F"][k]
    z = np.array([0, 0, 1.0])
    fwd = np.cross(z, u)
    fwd /= np.linalg.norm(fwd)
    e1, e2 = fwd, np.cross(u, fwd)
    MR = np.cross(F - P, R)
    rA = A - P
    Mat = np.array([[np.cross(rA, e) @ ax for e in (e1, e2)] for ax in (z, fwd)])
    try:
        a, b = np.linalg.solve(Mat, -np.array([MR @ z, MR @ fwd]))
    except np.linalg.LinAlgError:
        return 0.0
    FA = np.hypot(a, b)
    FP = np.linalg.norm(-R - (a * e1 + b * e2))
    return (MU_PLA * FA * (abs(l["dAP"][k]) + BALL_R + JOURNAL_R)
            + MU_STEEL * FP * SCREW_R * (abs(l["dyaw"][k]) + abs(l["dpitch"][k])))


def crank_torque(legs, W, mu_g, case):
    """Total crank torque (N·mm, all 8 legs, at the crankshafts' common speed) over the turn, and its parts."""
    F = np.stack([l["F"] for l in legs])                    # (8, N, 3)
    dF = np.stack([l["dF"] for l in legs])
    n = F.shape[1]
    out = dict(lift=np.zeros(n), slip=np.zeros(n), joints=np.zeros(n), legs=np.zeros(n), total=np.zeros(n),
               per_leg=np.zeros(n), feet=np.zeros(n, int))
    for k in range(n):
        z = F[:, k, 2]
        sup = np.where(z <= z.min() + SUPPORT_MM)[0]
        low = int(z.argmin())
        slip = np.linalg.norm(dF[sup, k, :2] - dF[low, k, :2], axis=1)
        c_lift = -dF[sup, k, 2]
        c = c_lift + mu_g * slip
        xy = F[sup, k, :2] - sim.CENTER
        if case == "even":
            A = np.vstack([np.ones(len(sup)), xy.T])
            Aa = np.vstack([1e3 * A, np.eye(len(sup)) * 1e-3])
            N, _ = nnls(Aa, np.concatenate([1e3 * np.array([W, 0, 0]), np.zeros(len(sup))]))
        else:   # most torque any split can need: max Σ c N, Σ N = W, |Σ N (xy − c)| ≤ W·COM_BOX, N ≥ 0
            r = linprog(-c, A_eq=[np.ones(len(sup))], b_eq=[W],
                        A_ub=np.vstack([xy.T, -xy.T]), b_ub=[W * COM_BOX] * 4, bounds=(0, None))
            N = r.x if r.success else np.full(len(sup), W / len(sup))
        per_leg = np.zeros(8)
        f_low = np.zeros(2)
        for j, i in enumerate(sup):
            per_leg[i] += N[j] * c[j]
            out["lift"][k] += N[j] * c_lift[j]
            out["slip"][k] += N[j] * mu_g * slip[j]
            if i != low and slip[j] > 1e-9:
                f = -mu_g * N[j] * (dF[i, k, :2] - dF[low, k, :2]) / slip[j]
                f_low -= f
                R = np.array([f[0], f[1], N[j]])
            else:
                R = None
            if R is not None:
                jf = joint_friction(legs[i], k, R)
                per_leg[i] += jf
                out["joints"][k] += jf
        jl = sup[list(sup).index(low)] if low in sup else low
        Nlow = N[list(sup).index(low)]
        jf = joint_friction(legs[jl], k, np.array([f_low[0], f_low[1], Nlow]))
        per_leg[jl] += jf
        out["joints"][k] += jf
        for i, l in enumerate(legs):                         # lifting each leg's own weight (taken at the knee)
            t = LEG_G / 1000 * G * l["dK"][k, 2]
            per_leg[i] += t
            out["legs"][k] += t
        out["per_leg"][k] = np.clip(per_leg, 0, None).sum()  # most cautious: no leg helps another
        shaft = per_leg[:4] + per_leg[4:]                     # legs R_i and L_i share one printed crankshaft
        out["total"][k] = np.clip(shaft, 0, None).sum()       # nothing given back through the gears
        out["feet"][k] = len(sup)
    return out


# --- 3 · speed ------------------------------------------------------------------------------------------------------
SPEED_CMS = (2.0, 3.0, 5.0)   # slow / target / fast walk for a desk toy this size (cm/s)

# --- 4 · gear train and where the motor goes ----------------------------------------------------------------------
EFF = (0.5, 0.7)     # printed spur train, design / best
PINION_T = 12        # fewest teeth without undercut (cad/crankshafts IDLER_MIN_TEETH)
GEARBOX_FACE = 0.5   # gap from the spine wall's outer face to the N20's gearbox face (mm)
N20_BODY = 26.0      # gearbox 9 + motor 15 + end cap and tabs ~2 (mm), no encoder, ratios up to 380:1
N20_ACROSS_Y, N20_ACROSS_Z = 10.0, 12.0     # gearbox cross-section 12 × 10, laid with 10 across Y (the narrow way)
LEG_HALF = 3.8       # half the leg's tube height (7.6): the biggest half-size of a leg's inner arm
DECK_UNDER = 72.8    # base v1: underside of the deck; the battery holder sits on its top (z 74.8)
BASE_BOTTOM = sim.BASE_BOTTOM
# Reductions to compare (crank rpm = motor output rpm / R). R = 0.6: the motor's own 20-tooth gear in idler 3's
# place; R = 1: a 12-tooth pinion on any gear of the train (idlers do not change the ratio); 1.5 and 2: one extra
# compound stage (12:18, 12:24), for which no room was found under the deck.
REDUCTIONS = {0.6: "20 T motor gear on idler 3's axle", 1.0: "12 T pinion on the train",
              1.5: "extra stage 12:18", 2.0: "extra stage 12:24"}


def arm_clearance(legs, lo, hi):
    """Least gap (mm) over a turn from any leg's inner arm (E-P, LEG_HALF thick) to the box lo-hi."""
    worst = np.inf
    t = np.linspace(0, 1, 40)
    for l in legs:
        pts = l["E"][:, None, :] + (l["P"] - l["E"])[:, None, :] * t[None, :, None]
        d = np.linalg.norm(np.maximum(0, np.maximum(lo - pts, pts - hi)), axis=-1)
        worst = min(worst, d.min() - LEG_HALF)
    return worst


def motor_box(y, z, C):
    x0 = sim.CENTER[0] + C.WALL_OUT + GEARBOX_FACE
    return (np.array([x0, y - N20_ACROSS_Y / 2, z - N20_ACROSS_Z / 2]),
            np.array([x0 + N20_BODY, y + N20_ACROSS_Y / 2, z + N20_ACROSS_Z / 2]))


def base_overlap(lo, hi):
    import trimesh
    b = trimesh.load(os.path.join(ROOT, "cad/base/out/base-v1.stl"))
    return trimesh.creation.box(bounds=[lo, hi]).intersection(b).volume / 1000


def layouts(legs, ground):
    from cad import design
    C = design("crankshafts")
    y3, z3, n3 = C.idlers()[2]
    out = []
    # A: the motor's gear replaces idler 3, motor in the only gap between the legs' arms under the deck
    out.append(("A", f"{n3} T motor gear in idler 3's place (y {y3:.1f}, z {z3:.1f}), N20 along +X under the deck",
                PINION_T / n3, y3, z3))
    # B: a 12-tooth pinion meshing idler 3 from straight below (outside the bowl: a pod under the belly)
    zb = z3 - C.MOD * (n3 + PINION_T) / 2 - C.CD_EXTRA
    out.append(("B", f"12 T pinion under idler 3 (y {y3:.1f}, z {zb:.1f}), N20 along +X in a pod under the base",
                1.0, y3, zb))
    # B2: the same with idler 3 made 17 T (the fewest that reach both shafts with a 12 T neighbour): it moves up
    sh = C.shaft_yz()
    half = (sh[3][0] - sh[2][0]) / 2
    n = 17
    cd = C.MOD * (C.SHAFT_TEETH + n) / 2 + C.CD_EXTRA
    zi = sh[2][1] - np.sqrt(cd ** 2 - half ** 2)
    zb2 = zi - C.MOD * (n + PINION_T) / 2 - C.CD_EXTRA
    out.append(("B2", f"as B with idler 3 made {n} T (moves up to z {zi:.1f}): pinion at z {zb2:.1f}", 1.0, y3, zb2))
    rows = []
    for key, what, R, y, z in out:
        lo, hi = motor_box(y, z, C)
        rows.append((key, what, R, lo, hi, arm_clearance(legs, lo, hi), base_overlap(lo, hi), hi[2], lo[2]))
    return C, rows


def corridors(legs, C, z=60.0, step=1.0):
    """Y ranges where an N20 along +X (centre at height z) clears every leg's inner arm under the deck."""
    free, cur = [], None
    for y in np.arange(-65, 55 + step, step):
        lo, hi = motor_box(y, z, C)
        ok = arm_clearance(legs, lo, hi) >= 0
        if ok and cur is None:
            cur = y
        if not ok and cur is not None:
            free.append((cur, y - step))
            cur = None
    if cur is not None:
        free.append((cur, y))
    return free


# --- 5 · motors (Pololu micro metal gearmotors, 6 V, https://www.pololu.com/category/60/micro-metal-gearmotors)
# ratio: (no-load rpm, extrapolated stall torque kg·cm) at 6 V. Free-run / stall current per family.
POLOLU = {
    "HP": dict(I0=0.10, Is=1.6, t={100: (310, 1.7), 150: (210, 2.4), 210: (150, 3.0), 250: (120, 3.4),
                                    298: (100, 4.0), 380: (84, 5.5), 1000: (31, 12.0)}),
    "MP": dict(I0=0.07, Is=0.67, t={100: (220, .94), 150: (150, 1.3), 210: (100, 1.7), 250: (88, 2.2),
                                     298: (73, 2.4), 380: (57, 3.6), 1000: (22, 6.7)}),
    "LP": dict(I0=0.04, Is=0.36, t={100: (130, .74), 150: (90, 1.1), 210: (65, 1.6), 250: (54, 1.7),
                                     298: (45, 2.0), 380: (36, 2.9), 1000: (13, 5.5)}),
}
GEARBOX_MAX = lambda ratio: 2.5 if ratio >= 380 else 2.0   # Pololu: max instantaneous output torque (kg·cm)
# Generic N20 6 V listings: the Aslong GA12-N20 table (3000, 1500, 750, 500, 300, 150, 100, 71, 60, 50, 39, 15 rpm
# for 1:10 ... 1:1000) runs a ~15000 rpm motor: LP/MP class. Sellers whose 1:298 is "100 rpm" run an HP-class motor.
GENERIC_15K = {100: 150, 150: 100, 210: 71, 250: 60, 298: 50, 380: 39, 1000: 15}
GENERIC_30K = {100: 300, 150: 200, 210: 150, 250: 120, 298: 100, 380: 80, 1000: 30}
V_RATED = 6.0
V_NOM, V_FLAT, V_FRESH = 4.8, 4.0, 5.6
R_SUPPLY = 0.3       # Ω: 4 AAA NiMH (~50 mΩ each) + switch and wires
MAH = 800
EYES_MA = 20         # 2-4 LEDs from 4.8 V through resistors
LEWIS_Y12, LEWIS_Y17, LEWIS_Y20 = 0.245, 0.302, 0.320    # Lewis form factors, 20° full depth


def motor_point(fam, ratio, V, T_out_kgcm):
    """Speed (rpm), current (A) and stall torque (kg·cm) of a Pololu motor on a battery at V (through R_SUPPLY)
    under output torque T: linear brushed-DC model scaled from 6 V (no-load speed and stall torque ∝ voltage)."""
    f = POLOLU[fam]
    w0, Ts = f["t"][ratio]
    I = f["I0"]
    for _ in range(30):
        Vm = V - I * R_SUPPLY
        Ts_v = Ts * Vm / V_RATED
        I = f["I0"] + (f["Is"] * Vm / V_RATED - f["I0"]) * min(T_out_kgcm / Ts_v, 1)
    return w0 * Vm / V_RATED * max(0, 1 - T_out_kgcm / Ts_v), I, Ts_v


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # trimesh: centre of mass of a 0-volume cut
    print("SPIDER-BOT · N20 GEAR MOTOR SIZING  (sim/motor_sizing.py)\n")

    # 1 · mass
    print("1 · ROBOT MASS")
    rows = mass_table()
    for name, g, note in rows:
        print(f"  {name:<44s} {g:6.1f} g   {note}")
    tot = sum(g for _, g, _ in rows)
    M = tot * (1 + MARGIN)
    W = M / 1000 * G
    print(f"  {'Sum':<44s} {tot:6.1f} g")
    print(f"  Design mass, +{MARGIN:.0%} margin: {M:.0f} g  → weight W = {W:.2f} N\n")

    # 2 · crank torque
    p, m, theta, legs = kinematics()
    print("2 · CRANK TORQUE OVER ONE TURN (all 8 legs, at the crankshafts' common speed)")
    print(f"  Geometry: sim/toy_leg_3d_rows_cad.json [0]: crank r {p['r']} mm; stride {m['stride']:.2f} mm per half "
          f"turn, bob {m['bob']:.2f} mm, step {m['lift']:.1f} mm, feet slip {m['slip']:.1f} mm/leg/turn")
    lever = max(np.abs(l["dF"][:, 2]).max() for l in legs)
    print(f"  Foot vertical speed per crank radian: up to {lever:.1f} mm/rad (crank pin {p['r']} mm/rad: the leg "
          f"multiplies it {lever / p['r']:.1f} ×)")
    print(f"  Plain estimate: W × bob × 2 steps per turn = {W:.2f} × {m['bob']:.2f} × 2 = {W * m['bob'] * 2:.0f} N·mm "
          f"of lift work per turn → mean {W * m['bob'] * 2 / (2 * np.pi):.1f} N·mm, before peaks and friction")
    print(f"  Assumptions: support feet within {SUPPORT_MM} mm of the lowest; μ joints PLA/PLA {MU_PLA}, screw/PLA "
          f"{MU_STEEL}; ground μ {MU_GROUND}; centre of mass ±{COM_BOX} mm; each crankshaft's net torque counted "
          f"only when positive")
    res = {}
    for case in ("even", "worst"):
        for mu in MU_GROUND:
            r = crank_torque(legs, W, mu, case)
            res[(case, mu)] = r
            k = r["total"].argmax()
            print(f"  {case:>5s} split, μ_ground {mu}: peak {r['total'][k]:5.1f} N·mm at {np.degrees(theta[k]):5.1f}° "
                  f"(lift {r['lift'][k]:.1f} + ground slip {r['slip'][k]:.1f} + joints {r['joints'][k]:.1f} + legs' "
                  f"weight {r['legs'][k]:.1f}), mean {r['total'].mean():4.1f}; no leg helping another: peak "
                  f"{r['per_leg'].max():.1f}, mean {r['per_leg'].mean():.1f}")
    worst = res[("worst", MU_GROUND[1])]
    T_c = worst["total"].max()
    T_c_typ = res[("even", MU_GROUND[0])]["total"].max()
    mean_lo, mean_hi = res[("even", MU_GROUND[0])]["total"].mean(), worst["total"].mean()
    print(f"  → Worst crank torque T_c = {T_c:.0f} N·mm = {T_c / NMM_PER_KGCM:.2f} kg·cm (a {T_c / p['r']:.1f} N push on "
          f"the {p['r']} mm crank); typical peak {T_c_typ:.0f} N·mm")
    print(f"  → Mean crank torque {mean_lo:.0f} (even split, μ {MU_GROUND[0]}) to {mean_hi:.0f} N·mm (worst split, "
          f"μ {MU_GROUND[1]})\n")

    # 3 · speed
    print("3 · TARGET CRANK SPEED")
    per_turn = 2 * m["stride"]
    print(f"  Stride {m['stride']:.2f} mm per half turn → {per_turn:.1f} mm per crank turn")
    for v in SPEED_CMS:
        print(f"  {v:.0f} cm/s → {v * 10 / per_turn * 60:4.0f} rpm at the crank")
    print("  Range for a desk toy this size: 2-5 cm/s; aim ~3 cm/s at 4.8 V, not under ~1.5 cm/s at 4.0 V\n")

    # 4 · gear train and motor position
    print("4 · GEAR TRAIN AND WHERE THE MOTOR MESHES")
    C, lay = layouts(legs, m)
    sh = C.shaft_yz()
    print(f"  Crankshaft gears: {C.SHAFT_TEETH} T, module {C.MOD}, axes y {', '.join(f'{y:.1f}' for y, _ in sh)} at "
          f"z {sh[0][1]:.1f} (tips to z {sh[0][1] + C.MOD * (C.SHAFT_TEETH / 2 + 1):.1f}); deck underside z "
          f"{DECK_UNDER}, battery holder on the deck from z 74.8; base bottom z {BASE_BOTTOM}, ground z "
          f"{BASE_BOTTOM - m['clearance']:.1f}")
    print("  Idlers (y, z, teeth): " + ", ".join(f"({y:.1f}, {z:.1f}, {n})" for y, z, n in C.idlers()))
    print(f"  Idlers only reverse direction: crank rpm = rpm of the motor's gear × its teeth / {C.SHAFT_TEETH}")
    print(f"  The N20 lies along X (its shaft parallel to the crankshafts), gearbox face {GEARBOX_FACE} mm outside the "
          f"spine wall, body x {C.WALL_OUT + GEARBOX_FACE:.1f}..{C.WALL_OUT + GEARBOX_FACE + N20_BODY:.1f} mm from the "
          f"axis, {N20_ACROSS_Y:.0f} mm across Y × {N20_ACROSS_Z:.0f} mm tall")
    free = corridors(legs, C)
    print("  Under the deck (motor centre z 60) the legs' inner arms leave it room only at y " +
          ", ".join(f"{a:.0f}..{b:.0f}" for a, b in free) + " (centre); y < -50 and y > 39 run out of the bowl")
    for key, what, R, lo, hi, clr, ov, top, bot in lay:
        print(f"  {key}: {what}")
        print(f"     reduction R = {R:.2f}; box y {lo[1]:.1f}..{hi[1]:.1f}, z {bot:.1f}..{top:.1f}; leg arms "
              f"{clr:+.1f} mm; deck {DECK_UNDER - top:+.1f} mm; below base bottom {max(0, BASE_BOTTOM - bot):.1f} mm "
              f"(ground clearance left {bot - (BASE_BOTTOM - m['clearance']):.0f} mm); overlaps base v1's solid "
              f"{ov:.2f} cm³")
    print("  No place was found for a 12 T pinion in the gap between the arms: meshing idler 3 puts it above the deck,"
          " and a pinion with two 12 T idlers to crankshafts 3 and 4 clashes with idler 2 or the deck. An extra"
          " compound stage (24 T, Ø26) has no room under the deck either.")
    print(f"  Output shaft: ≥ {C.WALL_OUT + GEARBOX_FACE + C.GEAR_T / 2:.1f} mm through the wall to the far face of "
          "the gear; a 9-10 mm D-shaft also reaches the far wall (bearing hole)\n")

    # 5 · motor tables
    print("5 · N20 DATA (Pololu micro metal gearmotors, rated 6 V; no-load speed and stall torque ∝ V)")
    print(f"  {'family':<7}{'ratio':>6}{'rpm@6':>7}{'@4.8':>6}{'@4.0':>6}{'Ts@6':>7}{'@4.8':>6}{'@4.0':>6} kg·cm"
          f"   generic 6 V label (15k / 30k motor)")
    for fam, f in POLOLU.items():
        for ratio, (w0, Ts) in f["t"].items():
            print(f"  {fam:<7}{ratio:>6}{w0:>7.0f}{w0 * .8:>6.0f}{w0 * 4 / 6:>6.0f}{Ts:>7.2f}{Ts * .8:>6.2f}"
                  f"{Ts * 4 / 6:>6.2f}         {GENERIC_15K[ratio]} / {GENERIC_30K[ratio]} rpm")
    print("  Gearbox: keep output torque under 2.0 kg·cm (2.5 for 380:1 and 1000:1), Pololu's instantaneous limit\n")

    # 6 · candidates
    print("6 · MOTOR TORQUE AND CANDIDATES")
    for R in REDUCTIONS:
        print(f"  R {R:.1f} ({REDUCTIONS[R]}): motor torque = T_c / (R × eff) = {T_c:.0f} / ({R} × {EFF[0]}) = "
              f"{T_c / (R * EFF[0]):.0f} N·mm = {T_c / (R * EFF[0]) / NMM_PER_KGCM:.2f} kg·cm (eff {EFF[1]}: "
              f"{T_c / (R * EFF[1]) / NMM_PER_KGCM:.2f}); stall needed at 4.0 V ≥ "
              f"{3 * T_c / (R * EFF[0]) / NMM_PER_KGCM:.2f} kg·cm")
    print(f"\n  Margin = stall at that voltage / worst peak motor torque (eff {EFF[0]}); speed at the mean worst-case "
          f"torque; current at 4.8 V incl. {EYES_MA} mA eyes; runtime = {MAH} × 0.8 / mA")
    print(f"  {'R':>4} {'motor':<9}{'mrg 4.8':>8}{'mrg 4.0':>8}{'mrg mean 4.0':>13}{'crank rpm':>10}{'cm/s 4.8':>9}"
          f"{'4.0':>6}{'5.6':>6}{'mA':>6}{'h':>5}  verdict")
    passing = []
    for R in REDUCTIONS:
        Tm = T_c / (R * EFF[0]) / NMM_PER_KGCM
        Tmean = mean_hi / (R * EFF[0]) / NMM_PER_KGCM
        Tmean_lo = mean_lo / (R * EFF[0]) / NMM_PER_KGCM
        for fam, f in POLOLU.items():
            for ratio in f["t"]:
                r48, I48, Ts48 = motor_point(fam, ratio, V_NOM, Tmean)
                r40, _, Ts40 = motor_point(fam, ratio, V_FLAT, Tmean)
                r56, _, _ = motor_point(fam, ratio, V_FRESH, Tmean)
                _, I_lo, _ = motor_point(fam, ratio, V_NOM, Tmean_lo)
                cms = lambda rpm: rpm / R * per_turn / 600
                m48, m40 = Ts48 / Tm, Ts40 / Tm
                if m40 < 3:
                    verdict = "margin < 3"
                elif Tm > GEARBOX_MAX(ratio):
                    verdict = "gearbox"
                elif cms(r48) < 1.8:
                    verdict = "slow"
                elif cms(r56) > 5.5:
                    verdict = "fast"
                else:
                    verdict = "PASS"
                    passing.append((R, fam, ratio))
                if m40 < 1.5 or cms(r48) < 0.5:
                    continue        # hopeless rows left out
                mA_hi, mA_lo = I48 * 1000 + EYES_MA, I_lo * 1000 + EYES_MA
                print(f"  {R:>4.1f} {fam + ' 1:' + str(ratio):<9}{m48:>8.1f}{m40:>8.1f}{Ts40 / Tmean:>13.1f}"
                      f"{r48 / R:>10.0f}{cms(r48):>9.1f}{cms(r40):>6.1f}{cms(r56):>6.1f}{mA_hi:>6.0f}"
                      f"{MAH * 0.8 / mA_hi:>5.1f}  {verdict}  (typical load: {mA_lo:.0f} mA, "
                      f"{MAH * 0.8 / mA_lo:.1f} h)")
    print("\n  PASS: " + (", ".join(f"R {R} {f} 1:{r}" for R, f, r in passing) or "none"))

    # tooth load at the pinion (R = 1)
    Tp = T_c / EFF[0]
    Ft = Tp / (C.MOD * PINION_T / 2)
    Ft_typ = T_c_typ / EFF[1] / (C.MOD * PINION_T / 2)
    print(f"\n  Teeth at the motor's mesh (it carries the whole train). Worst peak: {Tp:.0f} N·mm on the 12 T pinion → "
          f"{Ft:.0f} N at the pitch circle (typical {Ft_typ:.0f} N). Lewis bending σ = F / (face × m × Y):")
    for name, face, Y in (("12 T pinion, 3 mm face", C.GEAR_T, LEWIS_Y12), ("12 T pinion, 5 mm face", 5.0, LEWIS_Y12),
                          ("idler 3, 20 T, 2.6 mm face", C.GEAR_T - 0.4, LEWIS_Y20),
                          ("idler 3, 17 T, 2.6 mm face", C.GEAR_T - 0.4, LEWIS_Y17)):
        print(f"    {name:<28s} {Ft / (face * C.MOD * Y):4.0f} MPa worst, {Ft_typ / (face * C.MOD * Y):4.0f} typical")
    print("    (printed PLA tooth, loaded along the layers: ~50 MPa tensile; aim under ~20 MPa)")


if __name__ == "__main__":
    main()
