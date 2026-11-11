#!/usr/bin/env python3
"""Pictures of base v1 for the README and the build log.

  images/base-v1.png    the base from above and from below, with the cap
  images/section-leg.png  cut through a middle leg: body, band, base, fork, swivel screws, leg and crankshaft
  images/section-spine.png  cut along the spine: gears, keel and the cap's tongues
  images/band.png       the robot before and after: the body lifted on the band

Usage:
    python3 figures.py

Needs matplotlib, trimesh, shapely.
"""
import os
import sys

import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = os.path.join(HERE, "..", "drive")
sys.path.insert(0, DRIVE)
import build as D  # noqa: E402
import check as DC  # noqa: E402

sys.path.insert(0, HERE)
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("basebuild", os.path.join(HERE, "build.py"))
BB = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BB)

IMG = os.path.join(HERE, "images")
GREY, BLUE, RED, GREEN, BLACK = "#9a9a9a", "#2e86c1", "#c0392b", "#27ae60", "#222222"


def load(n, folder=HERE):
    return trimesh.load(os.path.join(folder, n + ".stl"))


def draw3d(ax, items, elev, azim, lim=None):
    light = np.array([0.4, -0.6, 0.7])
    light /= np.linalg.norm(light)
    allb = []
    for m, col in items:
        sh = 0.35 + 0.65 * np.abs(m.face_normals @ light)
        f = np.array(matplotlib.colors.to_rgb(col))[None] * sh[:, None]
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=f, edgecolors="none"))
        allb.append(m.bounds)
    b = np.array(allb)
    lo, hi = b[:, 0].min(0), b[:, 1].max(0)
    mid, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(mid[0] - r, mid[0] + r)
    ax.set_ylim(mid[1] - r, mid[1] + r)
    ax.set_zlim(mid[2] - r, mid[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev, azim)
    ax.set_axis_off()


def section(ax, m, P, h, n, **kw):
    s = m.section(plane_origin=P, plane_normal=n)
    if s is None:
        return
    for e in s.discrete:
        xy = np.c_[(e - P) @ h, e[:, 2]]
        if kw.get("fill"):
            ax.fill(xy[:, 0], xy[:, 1], color=kw["color"], alpha=kw.get("alpha", 1), lw=0)
        else:
            ax.plot(xy[:, 0], xy[:, 1], color=kw["color"], lw=kw.get("lw", 1), ls=kw.get("ls", "-"))


def fig_base():
    base, cap = load("base-v1"), load("cap")
    fig = plt.figure(figsize=(14, 7), dpi=100)
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    draw3d(ax, [(base, GREY), (cap, BLUE)], 50, -60)
    ax.set_title("From above: band, fork pockets, deck and cap (blue)", fontsize=12)
    ax = fig.add_subplot(1, 2, 2, projection="3d")
    draw3d(ax, [(base, GREY)], -35, -60)
    ax.set_title("From below: bowl, keel and the bosses under the forks", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, "base-v1.png"))
    plt.close(fig)


def fig_section_leg():
    """Vertical cut through the right middle leg (i = 1), along the leg."""
    base, cap, body = load("base-v1"), load("cap"), load("body-lifted")
    old_body = load("spideybot_body", os.path.join(HERE, "..", "carcass-120"))
    old_base = load("spideybot_base", os.path.join(HERE, "..", "carcass-120"))
    th = np.radians(np.arange(0, 360, 5))
    tilt = np.array([-np.degrees(np.arcsin(D.legs_at(t)[1]["u"][2])) for t in th])
    t_hi, t_lo = th[tilt.argmax()], th[tilt.argmin()]
    l = D.legs_at(t_hi)[1]
    P = l["P"]
    h = np.array([l["u"][0], l["u"][1], 0])
    h /= np.linalg.norm(h)
    n = np.cross([0, 0, 1], h)
    fig, axs = plt.subplots(1, 2, figsize=(16, 7.5), dpi=100)
    for k, ax in enumerate(axs):
        if k == 0:
            section(ax, old_base, P, h, n, fill=True, color=GREY)
            section(ax, old_body, P, h, n, fill=True, color=RED, alpha=0.5)
            ax.set_title("Before: the fork's top half inside the body", fontsize=13)
        else:
            section(ax, base, P, h, n, fill=True, color=GREY)
            section(ax, cap, P, h, n, fill=True, color=BLUE)
            section(ax, body, P, h, n, fill=True, color=RED, alpha=0.5)
            ax.set_title(f"Base v1: body {BB.LIFT:g} mm higher on the band", fontsize=13)
        for t, ls in ((t_hi, "-"), (t_lo, "--")):
            for nm, f, M in DC.poses(t):
                if nm in ("leg1R", "pivot1R", "crankshaft1"):
                    m = load(f, DRIVE)
                    m.apply_transform(M)
                    col = BLACK if nm.startswith("leg") else GREEN if nm.startswith("pivot") else BLUE
                    if nm.startswith("crank") and ls == "--":
                        continue
                    section(ax, m, P, h, n, color=col, lw=1.3, ls=ls)
        if k == 1:
            for z0, z1 in ((BB.FORK_TOP - BB.SCREW_IN, BB.TOP), (BB.FORK_BOT - BB.FORK_GAP - 6.4 - 3, BB.FORK_BOT + BB.SCREW_IN)):
                ax.plot([0, 0], [z0, z1], color="#8e44ad", lw=3)
            ax.text(1.2, BB.TOP - 3, "M3×10, head in the band's top", fontsize=9, color="#8e44ad")
            ax.text(1.2, BB.FORK_BOT - 9, "M3×10 from below,\nnut in the boss", fontsize=9, color="#8e44ad")
            ax.axhline(BB.TOP, color=RED, lw=0.6, ls=":")
        ax.axhline(BB.SEAM, color="k", lw=0.6, ls=":")
        ax.text(-58, BB.SEAM + 0.6, "old seam", fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-60, 25)
        ax.set_ylim(40, 105)
        ax.set_xlabel("mm outwards from the pivot, along the leg")
        ax.grid(alpha=0.25)
    axs[0].text(-58, 103, "red: body   grey: base   black: leg (highest and lowest)   green: fork   blue: crankshaft / cap",
                fontsize=9, va="top")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, "section-leg.png"))
    plt.close(fig)


def fig_section_spine():
    base, cap = load("base-v1"), load("cap")
    P = np.array([D.CX, 0, 0])
    h = np.array([0, 1.0, 0])
    n = np.array([1.0, 0, 0])
    fig, ax = plt.subplots(figsize=(13, 5.5), dpi=100)
    for x, lw in ((D.CX, 0), (D.CX + (D.WALL_IN + D.WALL_OUT) / 2, 1)):
        pass
    section(ax, base, P, h, n, fill=True, color=GREY)
    Pw = np.array([D.CX + (D.WALL_IN + D.WALL_OUT) / 2, 0, 0])
    section(ax, base, Pw, h, n, color="#555555", lw=0.8)
    section(ax, cap, Pw, h, n, fill=True, color=BLUE, alpha=0.7)
    for nm, f, M in DC.poses(0):
        if nm.startswith(("crankshaft", "idler")):
            m = load(f, DRIVE)
            m.apply_transform(M)
            section(ax, m, P, h, n, color=RED, lw=1)
    ax.set_aspect("equal")
    ax.set_xlabel("y (mm, front ← → rear)")
    ax.set_ylabel("z (mm)")
    ax.set_title("Along the spine: the gears in the bowl (grey), the keel under them and the cap (blue) with its "
                 "tongues down the journal slots (dark outline: the spine wall)", fontsize=11)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, "section-spine.png"))
    plt.close(fig)


def fig_band():
    """Side view before and after (silhouettes from the side)."""
    old = [load("spideybot_base", os.path.join(HERE, "..", "carcass-120")),
           load("spideybot_body", os.path.join(HERE, "..", "carcass-120"))]
    new = [load("base-v1"), load("body-lifted")]
    fig = plt.figure(figsize=(14, 6.5), dpi=100)
    for k, (items, title) in enumerate(((old, "Carcass as downloaded (120 %)"),
                                        (new, f"Base v1 and the body {BB.LIFT:g} mm higher"))):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        draw3d(ax, [(items[0], GREY), (items[1], RED)], 8, -20)
        ax.set_zlim(40, 170)
        ax.set_title(title, fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, "band.png"))
    plt.close(fig)


def main():
    os.makedirs(IMG, exist_ok=True)
    fig_section_leg()
    fig_section_spine()
    fig_base()
    fig_band()
    print("written to", IMG)


if __name__ == "__main__":
    main()
