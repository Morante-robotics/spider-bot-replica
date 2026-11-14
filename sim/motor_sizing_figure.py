#!/usr/bin/env python3
"""Two figures for the N20 choice, from motor_sizing.py's constants and its output (motor-sizing-result.txt):

  images/motor-sizing.png      the Pololu N20s with the 12 T pinion on idler 3 (reduction 1.0): margin at 4.0 V
                               against walking speed at 4.8 V, with the zone that passes shaded
  images/stall-protection.png  if a leg jams, the torque at which the weakest printed tooth in each path breaks
                               (estimate), against the gearbox's limit and the keep-the-D-pinion band

Break estimate (cad/chassis/design-plan.md, «Stall protection»): every mesh carries the same pitch-line force
F = T / (pinion pitch radius); a tooth breaks at F = SIGMA × contact width × module × Lewis Y.

    ../.venv/bin/python motor_sizing_figure.py            (run motor_sizing.py first)
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import motor_sizing as MS  # noqa: E402
from cad import design  # noqa: E402

C = design("crankshafts")
RESULT = os.path.join(HERE, "motor-sizing-result.txt")
CHOSEN = ("HP", 380)
SLOW_CMS = 1.8            # motor_sizing.py: under this at 4.8 V the verdict is «slow»
SIGMA = 50.0              # MPa, PLA tooth loaded along the layers (the coupons K6a/K6b replace it)
RULE_HI = 0.8             # keep the D pinion if every break ≤ 0.8 × the gearbox limit ...
RULE_LO = 1.5             # ... and ≥ 1.5 × the worst design torque at the motor
FONT = 12


def candidates():
    """Rows of section 6 with reduction 1.0: (family, ratio, margin 4.0 V, cm/s 4.8 V, verdict)."""
    rows = []
    for line in open(RESULT):
        m = re.match(r"\s+1\.0 (HP|MP|LP) 1:(\d+)\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+\d+\s+([\d.]+)\s+[\d.]+\s+[\d.]+"
                     r"\s+\d+\s+[\d.]+\s+(.+?)\s+\(", line)
        if m:
            rows.append((m[1], int(m[2]), float(m[4]), float(m[5]), m[6]))
    return rows


def worst_motor_torque():
    txt = open(RESULT).read()
    return float(re.search(r"Worst peak: (\d+) N·mm on the 12 T pinion", txt)[1])


def sizing_figure(out):
    rows = candidates()
    fig, ax = plt.subplots(figsize=(9, 6.5))
    xmax = max(r[3] for r in rows) + 0.4
    ymax = max(r[2] for r in rows) + 0.6
    ax.add_patch(plt.Rectangle((SLOW_CMS, 3.0), xmax - SLOW_CMS, ymax - 3.0, color="#2b9348", alpha=0.12, lw=0))
    ax.text(xmax - 0.05, ymax - 0.2, f"passes: margin ≥ 3 at 4.0 V,\nspeed ≥ {SLOW_CMS} cm/s at 4.8 V", ha="right",
            va="top", fontsize=FONT, color="#2b9348")
    ax.axhline(3.0, color="#2b9348", lw=1, ls="--")
    ax.axvline(SLOW_CMS, color="#2b9348", lw=1, ls="--")
    marker = {"HP": "o", "MP": "s", "LP": "^"}
    for fam, ratio, m40, cms, verdict in rows:
        chosen = (fam, ratio) == CHOSEN
        ax.plot(cms, m40, marker[fam], ms=12 if chosen else 8, color="#e63946" if chosen else "#457b9d",
                mec="black" if chosen else "none")
        ax.annotate(f"{fam} {ratio}:1", (cms, m40), xytext=(7, 4), textcoords="offset points",
                    fontsize=FONT if chosen else FONT - 2, fontweight="bold" if chosen else "normal")
    for fam in marker:
        ax.plot([], [], marker[fam], color="#457b9d", label=f"Pololu {fam} (6 V)")
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("Walking speed at 4.8 V (cm/s)", fontsize=FONT)
    ax.set_ylabel("Margin at 4.0 V (stall torque / worst load)", fontsize=FONT)
    ax.tick_params(labelsize=FONT - 1)
    ax.legend(loc="lower center", fontsize=FONT - 1)
    ax.set_title("N20 candidates, 12-tooth pinion on idler 3: chosen HP 380:1 (red)", fontsize=FONT + 1)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)
    return out


def stall_figure(out):
    r_pitch = C.MOD * MS.PINION_T / 2
    narrow, crank_face = C.GEAR_T - 0.4, C.GEAR_T     # idlers 1-2 face; crank gears' face
    brk = lambda width, Y: SIGMA * width * C.MOD * Y * r_pitch
    paths = [("Jam at crank 4 (rear legs)", brk(crank_face, MS.LEWIS_Y12), "crank 4 gear, 3 mm"),
             ("Jam at crank 3", brk(crank_face, MS.LEWIS_Y12), "crank 3 gear, 3 mm"),
             ("Jam at crank 2", brk(narrow, MS.LEWIS_Y12), "12 T, 2.6 mm contact"),
             ("Jam at crank 1 (front legs)", brk(narrow, MS.LEWIS_Y12), "12 T, 2.6 mm contact")]
    limit = MS.GEARBOX_MAX(CHOSEN[1]) * MS.NMM_PER_KGCM
    ts6 = MS.POLOLU[CHOSEN[0]]["t"][CHOSEN[1]][1] * MS.NMM_PER_KGCM
    stall = (ts6 * MS.V_FLAT / MS.V_RATED, ts6 * MS.V_FRESH / MS.V_RATED)
    design_t = worst_motor_torque()
    lo, hi = RULE_LO * design_t, RULE_HI * limit
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.axvspan(lo, hi, color="#2b9348", alpha=0.18)
    ax.axvspan(*stall, color="#e63946", alpha=0.12)
    ax.axvline(limit, color="#e63946", lw=2)
    ax.axvline(design_t, color="#555555", lw=1.5, ls="--")
    for k, (name, t, tooth) in enumerate(paths):
        ok = lo <= t <= hi
        ax.barh(k, t, color="#2b9348" if ok else "#f4a261", height=0.55)
        ax.text(t + 4, k, f"{t:.0f}  ({tooth})", va="center", fontsize=FONT - 1)
    ax.set_yticks(range(len(paths)), [p[0] for p in paths], fontsize=FONT - 1)
    ax.invert_yaxis()
    top = -0.75
    ax.text((lo + hi) / 2, top, f"keep the\nD pinion\n{lo:.0f}–{hi:.0f}", ha="center", va="bottom", fontsize=FONT - 1,
            color="#2b9348")
    ax.text(limit + 3, top, f"gearbox limit\n{limit:.0f}", va="bottom", fontsize=FONT - 1, color="#e63946")
    ax.text(sum(stall) / 2, top, f"motor stall\n{stall[0]:.0f}–{stall[1]:.0f}\n(4.0–5.6 V)", ha="center", va="bottom",
            fontsize=FONT - 1, color="#e63946")
    ax.text(design_t - 3, top, f"worst load\nwalking\n{design_t:.0f}", ha="right", va="bottom", fontsize=FONT - 1, color="#555555")
    ax.set_ylim(len(paths) - 0.5, -1.9)
    ax.set_xlim(0, stall[1] + 20)
    ax.set_xlabel("Torque at the motor (N·mm): estimated break of the weakest printed tooth", fontsize=FONT)
    ax.tick_params(axis="x", labelsize=FONT - 1)
    ax.set_title("If a leg jams, which printed tooth breaks first (estimate, before coupons K6a and K6b)",
                 fontsize=FONT + 1)
    fig.tight_layout()
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    for f in (sizing_figure(os.path.join(HERE, "images", "motor-sizing.png")),
              stall_figure(os.path.join(HERE, "images", "stall-protection.png"))):
        print(os.path.relpath(f, HERE))
