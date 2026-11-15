#!/usr/bin/env python3
"""Build-log figures for the chassis Part A (the drive module), made from the CAD with the house style of
tools/figures.py. Every number written on a figure is read from build.py, ../robot.py or verify.py.

    images/part-a-in-robot.png     the module and the motor in the carcass, cut away along the body axis
    images/part-a-keel.png         side section at the gear plane: the carcass, the module, the keel before and after
    images/part-a-rear.png         the module's rear end against the carcass's rear face, and the 2 mm bump of Part B
    images/part-a-exploded.png     every part and fastener of the module, numbered by its assembly step
    images/part-a-bench-press.png  the pinion pressed on the motor on the bench, then the motor dropped in

The keel «before» (rev 4) is not kept as a model: it is redrawn here from the same gear pockets left pointed (50°
teardrops with 2 mm walls, as rev 4 had them) instead of cut flat; its lowest point is printed with the figure.

    ../../.venv/bin/python part_a_figures.py
"""
import os
import sys
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from shapely.geometry import Polygon as SPoly, box as sbox  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)
import figures as F  # noqa: E402
from cad import design, robot as R  # noqa: E402
from cad_verify import load_spec, steps  # noqa: E402

B = design("chassis")
IMG = os.path.join(HERE, "images")
BEIGE, BEIGE_EDGE = "#e8e0d2", "#8a7b62"
RED = "#c0392b"
BLUE = "#2e86c1"

EN = {"drive-module": "drive module", "cap": "cap", "motor-clamp": "motor clamp", "pinion": "pinion, 12 teeth",
      "idler-3-v2": "idler 3 v2 (5 mm)", "pin-keeper": "pin keeper", "n20": "N20 motor",
      "n20-shaft": "motor shaft", "keeper-screw": "M3 × 8 (keeper)", "keeper-nut": "M3 nut (keeper)",
      "cap-screw": "M3 × 12 (cap, front)", "cap-nut": "M3 nut (cap, front)",
      "shared-screw": "M3 × 12 (cap and clamp)", "shared-nut": "M3 nut (cap and clamp)",
      "clamp-screw": "M3 × 12 (clamp, rear)", "clamp-nut": "M3 nut (clamp, rear)",
      "gauge-fork": "gauge fork (0.8 mm)", "press-jig": "press jig", "press-cup": "press cup",
      **{f"crankshaft-{i + 1}": f"crankshaft {i + 1}" for i in range(4)},
      **{f"idler-{k + 1}": f"idler {k + 1}" for k in range(2)},
      **{f"pin-{k + 1}": f"pin {k + 1}, Ø3 × {B.PIN_L:g} steel" for k in range(3)}}


def load():
    spec = load_spec(os.path.join(HERE, "verify.py"))
    meshes = {n: p["mesh"] if "mesh" in p else trimesh.load(os.path.join(HERE, p["stl"]), force="mesh")
              for n, p in spec.PARTS.items()}
    return spec, meshes


def module_only(spec):
    """The spec without the reference bodies (legs, holder, eyes board): the module's own assembly, English labels."""
    s = types.SimpleNamespace(**{k: getattr(spec, k) for k in dir(spec) if not k.startswith("__")})
    s.ASSEMBLY = [e for e in spec.ASSEMBLY if not (isinstance(e[0], str) and
                                                    (e[0].startswith("leg-") or e[0] in ("holder", "eyes-board")))]
    s.LABELS = {"en": EN}
    return s


def save(fig, name):
    p = os.path.join(IMG, name)
    fig.savefig(p, dpi=110, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(p)


# ---------------------------------------------------------------- 1. the module in the robot
def in_robot(spec, meshes):
    s = module_only(spec)
    tri = F._placed(s, meshes, bench=False)
    col = F.colours(s)
    shell = R.carcass("base")
    far = trimesh.intersections.slice_mesh_plane(shell, plane_normal=[-1, 0, 0], plane_origin=[R.CX - 8.0, 0, 0],
                                                 cap=True)
    show = ["drive-module", "cap", "motor-clamp", "n20", "pinion", "idler-3-v2", "pin-keeper",
            *[f"crankshaft-{i + 1}" for i in range(4)], "shared-screw", "clamp-screw", "cap-screw"]
    items = [{"mesh": far, "color": BEIGE}] + [{"mesh": tri[n], "color": col[n]} for n in show]
    fig, ax = plt.subplots(figsize=(12, 7.5))
    view = (18, 12)
    proj = F.draw(ax, items, view)
    g = R.GROUND_Z
    y0, y1 = ax.get_xlim()
    a, b = proj([[R.CX, -75, g]])[0], proj([[R.CX, 50, g]])[0]
    ax.plot([a[0], b[0]], [a[1], b[1]], color="#333333", lw=2.5)
    ax.annotate("table", xy=b, xytext=(-40, 6), textcoords="offset points", fontsize=F.FONT, color="#333333")
    lo = proj([[R.CX, 0, g]])[0]
    ax.set_ylim(min(ax.get_ylim()[0], lo[1] - 8), ax.get_ylim()[1])
    pts = [(proj(tri["drive-module"].bounds.mean(axis=0) + [0, -30, 0])[0], "drive module"),
           (proj(tri["cap"].bounds.mean(axis=0) + [0, -20, 2])[0], "cap"),
           (proj(tri["motor-clamp"].bounds.mean(axis=0) + [8, 0, 2])[0], "motor clamp"),
           (proj([R.CX + 20.0, R.MOTOR_AXIS[1] + R.N20_W / 2, R.MOTOR_AXIS[2]])[0], "N20 motor (catalogue size)"),
           (proj(tri["pin-keeper"].bounds.mean(axis=0) + [0, -12, 0])[0], "pin keeper"),
           (proj(tri["crankshaft-1"].bounds.mean(axis=0))[0], "crankshaft 1 (front)"),
           (proj(tri["crankshaft-4"].bounds.mean(axis=0))[0], "crankshaft 4 (rear)"),
           (proj([R.CX - 8, -40, 100])[0], "carcass (far half)")]
    F.side_labels(ax, pts)
    ax.set_title("The drive module in the robot, seen from the right with the near half of the carcass cut away\n"
                 "front of the robot to the left; legs not drawn", fontsize=F.FONT + 2)
    save(fig, "part-a-in-robot.png")


# ---------------------------------------------------------------- 2. keel before and after
def _outline(ax, poly, **kw):
    for g in getattr(poly, "geoms", [poly]):
        ax.plot(*g.exterior.xy, **kw)


def keel(spec, meshes):
    x0 = R.CX
    plane = dict(plane_origin=[x0, 0, 0], plane_normal=[1, 0, 0])
    fig, ax = plt.subplots(figsize=(12, 7))

    def fill(mesh, fc, ec, alpha=1.0, z=1):
        s = mesh.section(**plane)
        for path in s.discrete:
            ax.fill(path[:, 1], path[:, 2], fc=fc, ec=ec, lw=1.0, alpha=alpha, zorder=z)

    shell = R.carcass("base")
    fill(shell, BEIGE, BEIGE_EDGE, z=1)
    carcass_bottom = float(shell.section(**plane).vertices[:, 2].min())
    mod = trimesh.load(os.path.join(HERE, "out", "drive-module.stl"))
    fill(mod, RED, "#7b241c", alpha=0.9, z=3)
    # rev 4: the same pockets left pointed (teardrops, flanks at SELF_SUPPORT) with KEEL walls round them; drawn is
    # the material it had below today's module (hatched): what rev 5 cut away
    rev4 = unary_union([SPoly(B.teardrop(y, z, r + B.GEAR_ROOM)).buffer(B.KEEL, 16) for y, z, r, _ in B.gears()])
    rev4 = rev4.intersection(sbox(B.Y0, 0, B.Y1, B.TOP))
    low4 = rev4.bounds[1]
    now = SPoly(B.profile()).buffer(0.01)
    gone = rev4.difference(now)
    for g_ in getattr(gone, "geoms", [gone]):
        if g_.area > 1.0:
            ax.fill(*g_.exterior.xy, fc="#f5c6c0", ec=RED, ls="--", lw=1.4, hatch="///", zorder=4)
    g = R.GROUND_Z
    v1 = spec.KEEP_IN["carcass-shell"]["allow"]["keel"]["min_z"]
    ax.axhline(g, color="#333333", lw=2.5)
    ax.text(30, g + 1.0, "table (feet)", fontsize=F.FONT, color="#333333")
    for z, txt, c, ls, va in [
            (carcass_bottom, f"carcass bottom, z {carcass_bottom:.1f}", BEIGE_EDGE, ":", "bottom"),
            (B.KEEL_Z, f"module now, lowest z {B.KEEL_Z:.2f} (base v1's keel: {v1:g})", RED, "-", "top"),
            (low4, f"rev 4 (hatched), lowest z {low4:.1f}", RED, "--", "top")]:
        ax.axhline(z, color=c, lw=1.0, ls=ls, zorder=2)
        ax.text(36, z + (0.5 if va == "bottom" else -0.5), txt, fontsize=F.FONT - 1, color=c, va=va, ha="left")
    for y, z, txt in [(-66, carcass_bottom, f"{carcass_bottom - g:.0f} mm\nunder the carcass"),
                      (-14, B.KEEL_Z, f"{B.KEEL_Z - g:.1f} mm\nnow"),
                      (14, low4, f"{low4 - g:.1f} mm\nrev 4")]:
        ax.annotate("", xy=(y, g), xytext=(y, z), arrowprops=dict(arrowstyle="<|-|>", color="#333333", lw=1.4))
        ax.text(y + 1.5, (g + z) / 2, txt, fontsize=F.FONT, va="center")
    ax.set_xlim(-80, 95)
    ax.set_ylim(g - 4, 112)
    ax.set_aspect("equal")
    ax.set_xlabel("front (−Y) to rear (+Y), mm")
    ax.set_ylabel("height, mm")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.set_title("Side section through the gear plane: carcass (beige), drive module (red)\n"
                 "hatched: what rev 4's pointed gear pockets added below the carcass; rev 5 cut them flat",
                 fontsize=F.FONT + 1)
    save(fig, "part-a-keel.png")
    return carcass_bottom, low4


# ---------------------------------------------------------------- 3. rear end
def rear(spec, meshes):
    x0 = R.CX
    plane = dict(plane_origin=[x0, 0, 0], plane_normal=[1, 0, 0])
    fig, ax = plt.subplots(figsize=(8, 7))
    shell = R.carcass("base")
    for path in shell.section(**plane).discrete:
        ax.fill(path[:, 1], path[:, 2], fc=BEIGE, ec=BEIGE_EDGE, lw=1.0, zorder=1)
    mod = trimesh.load(os.path.join(HERE, "out", "drive-module.stl"))
    for path in mod.section(**plane).discrete:
        ax.fill(path[:, 1], path[:, 2], fc=RED, ec="#7b241c", lw=1.0, alpha=0.9, zorder=3)
    y4, z4 = R.SHAFTS[3]
    room = B.TIP_SH + B.GEAR_ROOM
    t = np.linspace(0, 2 * np.pi, 100)
    ax.plot(y4 + room * np.cos(t), z4 + room * np.sin(t), color="#555555", lw=1, ls=":", zorder=4)
    ax.plot(y4 + B.TIP_SH * np.cos(t), z4 + B.TIP_SH * np.sin(t), color="#555555", lw=1.2, zorder=4)
    ax.text(y4, z4, "crank 4\ngear", ha="center", va="center", fontsize=F.FONT - 1, zorder=5)
    # the 2 mm bump of Part B's shell over the rear end (decision 13): drawn as its outline, not modelled yet
    bz = (57.0, B.TOP)
    ax.plot([B.Y1, B.Y1 + 2.0, B.Y1 + 2.0, B.Y1], [bz[0], bz[0], bz[1], bz[1]], color=BLUE, lw=2, ls="--", zorder=6)
    ax.annotate("Part B: shell bulges about 2 mm here\nand covers the module's rear end",
                xy=(B.Y1 + 2.0, (bz[0] + bz[1]) / 2), xytext=(B.Y1 + 5, 84), fontsize=F.FONT, color=BLUE,
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.9))
    sec = shell.section(**plane).vertices
    face = float(sec[(sec[:, 2] > 57.0) & (sec[:, 2] < B.TOP)][:, 1].max())
    ax.annotate(f"module's rear wall, y {B.Y1:.2f}\n(carcass rear face, y {face:.2f})",
                xy=(B.Y1, 66), xytext=(B.Y1 + 5, 48), fontsize=F.FONT, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.9))
    ax.set_xlim(5, 60)
    ax.set_ylim(40, 95)
    ax.set_aspect("equal")
    ax.set_xlabel("towards the rear (+Y), mm")
    ax.set_ylabel("height, mm")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.set_title("Rear end, side section through the gear plane", fontsize=F.FONT + 1)
    save(fig, "part-a-rear.png")


# ---------------------------------------------------------------- 4. exploded view
def exploded(spec, meshes):
    s = module_only(spec)
    seq = F.exploded_steps(steps(s))
    tri, col = F._placed(s, meshes, bench=False), F.colours(s)
    lo = np.min([tri[n].bounds[0] for _, names, _, _ in seq for n in names], axis=0)
    hi = np.max([tri[n].bounds[1] for _, names, _, _ in seq for n in names], axis=0)
    gap = 0.25 * float((hi - lo).max())
    items, anchors = [], []
    for k, names, d, nums in seq:
        for n, num in zip(names, nums):
            m = tri[n].copy()
            if d is not None:
                m.apply_translation(d * gap * (1 + 0.08 * k))
            items.append({"mesh": m, "color": col[n]})
            anchors.append((num, n, m.bounds.mean(axis=0)))
    fig, ax = plt.subplots(figsize=(12, 9))
    proj = F.draw(ax, items, (25, -60))
    F.side_labels(ax, [(proj(p)[0], f"{num}  {EN.get(n, n)}") for num, n, p in anchors])
    bench = [i + 1 for i, st in enumerate(steps(s)) if st["bench"] is not None]
    ax.set_title("Drive module, exploded: each part pulled out the way it goes in, numbered by its step\n"
                 f"(steps {bench[0]}–{bench[-1]} are done on the bench, before the motor goes in)", fontsize=F.FONT + 1)
    save(fig, "part-a-exploded.png")


# ---------------------------------------------------------------- 5. bench press and drop
BENCH_TITLES = {
    "pinion": "1 · pinion into the jig's pocket,\ndot up",
    "gauge-fork": "2 · gauge fork (0.8 mm) down\ninto its slot, flat on the pinion",
    "n20 + n20-shaft": "3 · motor pushed down by its can until\nthe gearbox stops on the fork",
    "press-cup": "4 · only if the thumb is not enough:\npress cup on the can, then a vise",
    "n20 + n20-shaft + pinion": "5 · fork out, motor out of the jig;\nmotor and pinion lowered in as one",
    "motor-clamp": "6 · clamp on, 2 × M3 × 12",
}


def bench_press(spec, meshes):
    s = module_only(spec)
    ctx = F._context(s, meshes)
    keys = [" + ".join(st["names"]) for st in ctx["seq"]]
    fig, axes = plt.subplots(2, 3, figsize=(15, 10.5))
    for ax, key in zip(axes.flat, BENCH_TITLES):
        k = keys.index(key)
        F._step_panel(ax, s, ctx, k, "en", number=False)
        ax.set_title(BENCH_TITLES[key], fontsize=F.FONT + 2, pad=6)
    fig.suptitle("Pressing the pinion on the motor's shaft on the bench (1–4), then the motor goes in (5–6)",
                 fontsize=F.FONT + 3)
    fig.tight_layout()
    save(fig, "part-a-bench-press.png")


def main():
    spec, meshes = load()
    in_robot(spec, meshes)
    keel(spec, meshes)
    rear(spec, meshes)
    exploded(spec, meshes)
    bench_press(spec, meshes)


if __name__ == "__main__":
    main()
