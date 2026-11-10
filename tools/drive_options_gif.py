#!/usr/bin/env python3
"""Animated sketch of the three drive options compared before choosing (build log: Four lateral crankshafts).

Top row: side view of the right middle leg (forward = left). A and B come from the simulator
(../sim/toy_leg_3d_rows_cad.json; B with a 6 mm crank instead of 3.9): crank, pivot, knee and foot seen from the side,
the foot loop (lift, forward, plant, push) and the body bobbing as the robot walks. C, the cam toy, is a sketch: the
simulator cannot represent it. A cam only lifts the leg, so the foot moves up and down, and it walks by the leg leaning
back and scraping the floor. Bottom row: top view of the parts each option needs (a sketch).

Usage:
    python3 drive_options_gif.py ../images/drive-options.gif

Needs numpy, matplotlib and pillow.
"""
import argparse
import json
import os
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import toy_leg_3d as sim  # noqa: E402

LEG, CRANK, GEAR, GREY = "#534AB7", "#D85A30", "#1D9E75", "#888780"
OPTIONS = [
    dict(title="A · four shafts, 3 mm bob (chosen)", sub="stride 10 mm · bob 4.6 mm", r=None, kind="crank"),
    dict(title="B · four shafts, 6 mm bob", sub="stride 15 mm · bob 6.8 mm", r=6.0, kind="crank"),
    dict(title="C · cam toy", sub="pushes by friction, no loop", r=7, kind="cam"),
]


def rot(v, a):
    c, s = np.cos(a), np.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def leg(o, th):
    """Joint points of one leg (2D side view, y up) at crank angle th."""
    P, O = np.array([10.0, 70]), np.array([-30.0, 58])
    if o["kind"] == "crank":
        A = O + o["r"] * np.array([np.cos(th), np.sin(th)])
        u = (P - A) / np.linalg.norm(P - A)
        K = P + 38 * u
        F = K + 80 * rot(u, -1.25)
        return dict(O=O, A=A, P=P, K=K, F=F)
    lift = o["r"] * (0.5 + 0.5 * np.cos(th))
    ang = -0.12 - lift * 0.025
    u = np.array([np.cos(ang), np.sin(ang)])
    A, K = P - 34 * u, P + 38 * u
    F = K + 80 * rot(u, -1.45)
    return dict(O=A - [0, 9], A=A, P=P, K=K, F=F)


def simulated(r, frames):
    """Right middle leg seen from the side (x = Y, forward to the left; y = height above the ground under the robot)
    at each crank angle, from the simulator."""
    g = json.load(open(os.path.join(HERE, "..", "sim", "toy_leg_3d_rows_cad.json")))[0]
    p = {k: g[k] for k in sim.ranges("rows")}
    if r:
        p["r"] = r
    th, legs = sim.simulate(p, "rows", "crank", steps=frames)
    zmin = np.stack([l["F"][:, 2] for l in legs]).min(axis=0)       # the robot stands on its lowest foot
    l = legs[1]
    return {k: np.column_stack([l[k][:, 1], l[k][:, 2] - zmin]) for k in ("O", "A", "P", "K", "F")}


def top_view(ax, kind):
    ax.add_patch(FancyBboxPatch((-55, -75), 110, 150, boxstyle="round,pad=0,rounding_size=10", fc="none",
                                ec=GREY, lw=0.8))
    rows = [-55, -23, 7, 57]
    if kind == "crank":
        for y in rows:
            ax.plot([-50, 50], [y, y], color=GREY, lw=1.5)
            for s in (-1, 1):
                ax.add_patch(Rectangle((s * 12 - 3, y - 5), 6, 10, color=CRANK))
                ax.plot([s * 55, s * 95], [y, y + (y - 0) * 0.25], color=LEG, lw=2.5)
            ax.add_patch(Circle((30, y), 7, fc="none", ec=GEAR, lw=1.3))
        for a, b in zip(rows, rows[1:]):
            ax.add_patch(Circle((38, (a + b) / 2), 5, fc="none", ec=GEAR, lw=1.3, ls="--"))
        ax.text(0, -92, "4 shafts · 8 cranks · 8 pivots · ~8 gears", ha="center", fontsize=8)
    else:
        ax.plot([-50, 50], [0, 0], color=GREY, lw=1.5)
        for dx in (-14, 14):
            ax.add_patch(Ellipse((dx, 0), 12, 18, fc="none", ec=CRANK, lw=1.5))
        for y in rows:
            for s in (-1, 1):
                ax.plot([s * 55, s * 95], [y, y + y * 0.25], color=LEG, lw=2.5)
                ax.plot([s * 55, s * 22], [y, y * 0.3], color=LEG, lw=1, alpha=0.6)
        ax.add_patch(Circle((30, 0), 7, fc="none", ec=GEAR, lw=1.3))
        ax.text(0, -92, "1 shaft · 2 cams · 8 hinges · 2 gears", ha="center", fontsize=8)
    ax.add_patch(Rectangle((-20, 20), 30, 12, fc="none", ec=GREY, lw=0.8))
    ax.text(-5, 26, "N20", ha="center", va="center", fontsize=7)
    ax.set_xlim(-110, 110)
    ax.set_ylim(-100, 85)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--frames", type=int, default=40)
    args = ap.parse_args()

    sims = [simulated(o["r"], args.frames) if o["kind"] == "crank" else None for o in OPTIONS]
    cam = np.array([leg(OPTIONS[2], t)["F"] for t in np.linspace(0, 2 * np.pi, 90)])
    cam_off = -cam[:, 1].min()

    fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.6), gridspec_kw=dict(height_ratios=[1.1, 1]))
    for ax, o in zip(axs[1], OPTIONS):
        top_view(ax, o["kind"])
    fig.text(0.5, 0.965, "Side view of the right middle leg (forward ←) · A and B simulated, C sketched",
             ha="center", fontsize=9, color="#555")
    fig.text(0.5, 0.47, "Top view: the parts to print and assemble", ha="center", fontsize=9, color="#555")

    def frame(k):
        th = 2 * np.pi * k / args.frames
        for ax, o, S in zip(axs[0], OPTIONS, sims):
            ax.clear()
            ax.axhline(0, color=GREY, lw=1)
            if S is not None:                  # simulated: everything relative to the ground under the robot
                body = S["P"][k, 1] - 72 + 45.6          # base bottom is 26.4 mm under the rim
                ax.add_patch(FancyBboxPatch((-55, body), 104, 30, boxstyle="round,pad=0,rounding_size=6",
                                            fc="#F1EFE8", ec=GREY, lw=0.6))
                ax.plot(S["F"][:, 0], S["F"][:, 1] - (S["P"][:, 1] - S["P"][k, 1]), color=CRANK, lw=1,
                        ls="--", alpha=0.8)              # foot loop relative to the body, drawn at today's height
                r = np.linalg.norm(S["A"][0] - S["O"][0])
                ax.add_patch(Circle(S["O"][k], r + 2, fc="none", ec=CRANK, lw=1))
                ax.plot(*zip(S["O"][k], S["A"][k]), color=CRANK, lw=2.5)
                ax.plot(*zip(S["A"][k], S["P"][k], S["K"][k], S["F"][k]), color=LEG, lw=3, solid_joinstyle="round")
                ax.add_patch(Circle(S["P"][k], 2.5, fc="white", ec="black", lw=0.8, zorder=5))
                ax.set_xlim(-75, 70)
            else:
                sh = lambda p: (p[0], p[1] + cam_off)
                ax.add_patch(FancyBboxPatch((-75, 54 + cam_off), 90, 36, boxstyle="round,pad=0,rounding_size=6",
                                            fc="#F1EFE8", ec=GREY, lw=0.6))
                ax.plot(cam[:, 0], cam[:, 1] + cam_off, color=CRANK, lw=1, ls="--", alpha=0.8)
                L = leg(o, th)
                ax.add_patch(Ellipse(sh(L["O"]), 18, 12, angle=np.degrees(th), fc="none", ec=CRANK, lw=1.5))
                ax.plot(*zip(*[sh(L[n]) for n in "APKF"]), color=LEG, lw=3, solid_joinstyle="round")
                ax.add_patch(Circle(sh(L["P"]), 2.5, fc="white", ec="black", lw=0.8, zorder=5))
                ax.set_xlim(-85, 125)
            ax.set_ylim(-8, 110)
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(f"{o['title']}\n{o['sub']}", fontsize=9)

    plt.tight_layout(rect=(0, 0, 1, 0.95))
    FuncAnimation(fig, frame, frames=args.frames).save(args.out, writer=PillowWriter(fps=14), dpi=70)
    frame(0)
    fig.savefig(args.out.rsplit(".", 1)[0] + ".png", dpi=80)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
