#!/usr/bin/env python3
"""Figures for the Onshape tutorial (onshape.md): the test-frame parts with the edges and points to click for each
mate marked, and an animation of what the finished assembly should do.

Usage:
    python3 onshape_figures.py          # PNGs and GIF into images/onshape/

Reads the STLs written by the build.py of ../legs, ../crankshafts and this folder (run those first). Flat-shaded painter's renderer with Pillow.
Needs numpy, Pillow and build123d (for build.py's parameters and kinematics).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from cad import common as K, design  # noqa: E402
from stl_preview import load  # noqa: E402

L = design("legs")
C = design("crankshafts")

OUT = os.path.join(HERE, "images", "onshape")
SS = 2                                     # supersampling
LIGHT = np.array([0.4, -0.7, 0.6]) / np.linalg.norm([0.4, -0.7, 0.6])
COL = {"frame": (150, 150, 160), "crank": (52, 120, 200), "leg": (192, 57, 43), "pivot": (230, 160, 30),
       "slider": (40, 170, 90), "ghost": (215, 215, 220)}
MARK = (220, 0, 140)
FONT = "/System/Library/Fonts/Helvetica.ttc"

i_leg = 1                                  # right middle leg, crankshaft 2
P = [x for x in K.sim.pivots() if x[0] == "R" and x[1] == i_leg][0][2]
Y_SH, Z_SH = C.shaft_yz()[i_leg]
WIN_X, WIN_Y, WIN_Z, YH = L.yoke_size()
INFO = L.leg(i_leg)[1]


def mesh(name):
    return load(L.stl(name))


def tf(tris, R, t):
    return tris @ np.asarray(R).T + np.asarray(t)


def pose(theta):
    """Transforms (R, t) of crankshaft, leg and pivot at crank angle theta, and the ball centre / bore axis."""
    l = L.legs_at(theta)[i_leg]
    R_leg = L.leg_frame(l["u"])
    return dict(crank=(K.rot_x(-theta), [K.CX, Y_SH, Z_SH]), leg=(R_leg, l["P"]),
                pivot=(K.rot_z(np.arctan2(l["u"][1], l["u"][0])), l["P"]), A=l["A"], u=l["u"], F=l["F"])


def camera(azim, elev):
    a, e = np.radians(azim), np.radians(elev)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return rx @ rz                         # looks along +Y after rotation: screen x = X, up = Z, depth = Y


def render(parts, azim, elev, center, span, size=(700, 520), marks=(), labels=(), title=None):
    """parts: [(tris, rgb)]; marks: [(kind, data)] with kind 'circle' (c, axis, r), 'dot' (p), 'line' (p0, p1);
    labels: [(text, p3d, (dx, dy))] text placed at an offset (px) from the projected point, with a leader line."""
    W, H = size[0] * SS, size[1] * SS
    M = camera(azim, elev)
    scale = min(W, H) / span
    c = M @ np.asarray(center, float)

    def proj(p):
        v = np.asarray(p, float) @ M.T
        return np.stack([(v[..., 0] - c[0]) * scale + W / 2, H / 2 - (v[..., 2] - c[2]) * scale], -1), v[..., 1]

    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    allt, cols = [], []
    for tris, rgb in parts:
        if len(tris):
            allt.append(tris)
            cols.append(np.repeat([rgb], len(tris), 0))
    tris, cols = np.concatenate(allt), np.concatenate(cols)
    v = tris @ M.T
    n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.35 + 0.65 * np.abs(n @ (M @ LIGHT))
    xy, depth = proj(tris)
    for k in np.argsort(-depth.mean(1)):
        col = tuple((cols[k] * shade[k]).astype(int))
        d.polygon([tuple(p) for p in xy[k]], fill=col, outline=col)
    lw = 4 * SS // 2
    for kind, data in marks:
        if kind == "circle":
            cc, axis, r = data
            ax = K.unit(axis)
            e1 = K.unit(np.cross(ax, [0, 0, 1]) if abs(ax[2]) < 0.9 else np.cross(ax, [1, 0, 0]))
            e2 = np.cross(ax, e1)
            t = np.linspace(0, 2 * np.pi, 60)
            pts = np.asarray(cc) + r * (np.outer(np.cos(t), e1) + np.outer(np.sin(t), e2))
            p2, _ = proj(pts)
            d.line([tuple(p) for p in p2], fill=MARK, width=lw)
            q, _ = proj(cc)
            d.ellipse([q[0] - 3 * SS, q[1] - 3 * SS, q[0] + 3 * SS, q[1] + 3 * SS], fill=MARK)
        elif kind == "dot":
            q, _ = proj(data)
            rr = 7 * SS
            d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=MARK, width=lw)
            d.ellipse([q[0] - 2.5 * SS, q[1] - 2.5 * SS, q[0] + 2.5 * SS, q[1] + 2.5 * SS], fill=MARK)
        elif kind == "line":
            p2, _ = proj(np.array(data))
            d.line([tuple(p) for p in p2], fill=MARK, width=lw)
    font = ImageFont.truetype(FONT, 17 * SS)
    for text, p3, (dx, dy) in labels:
        q, _ = proj(p3)
        tx, ty = q[0] + dx * SS, q[1] + dy * SS
        d.line([tuple(q), (tx, ty)], fill=(60, 60, 60), width=SS)
        bb = d.textbbox((tx, ty), text, font=font, anchor="mm")
        d.rectangle([bb[0] - 4 * SS, bb[1] - 3 * SS, bb[2] + 4 * SS, bb[3] + 3 * SS], fill=(255, 255, 255),
                    outline=(60, 60, 60), width=SS)
        d.text((tx, ty), text, fill=(20, 20, 20), font=font, anchor="mm")
    if title:
        d.text((16 * SS, 14 * SS), title, fill=(20, 20, 20), font=ImageFont.truetype(FONT, 20 * SS))
    return img.resize(size, Image.LANCZOS)


def row(imgs, path):
    w = sum(i.width for i in imgs) + 10 * (len(imgs) - 1)
    out = Image.new("RGB", (w, max(i.height for i in imgs)), (255, 255, 255))
    x = 0
    for im in imgs:
        out.paste(im, (x, 0))
        x += im.width + 10
    out.save(path, optimize=True)
    print(path)


def keep(tris, test):
    """Triangles whose centroid passes test(centroid) (to cut away a wall that hides the edge)."""
    return tris[np.array([test(c) for c in tris.mean(1)])]


def cut_near(tris, center, azim, elev, keep_gap=0.0):
    """Drop the triangles on the camera's side of a plane through center, to see inside."""
    toward = camera(azim, elev).T @ np.array([0, -1.0, 0])
    return tris[(tris.mean(1) - np.asarray(center)) @ toward < keep_gap]


def main():
    os.makedirs(OUT, exist_ok=True)
    frame, crank, leg, pivot = mesh("test-frame"), mesh("crankshaft-2"), mesh("leg-middle-right"), mesh("pivot")
    th0 = np.radians(30)
    ps = pose(th0)
    crank_w, leg_w, piv_w = tf(crank, *ps["crank"]), tf(leg, *ps["leg"]), tf(pivot, *ps["pivot"])
    sl_c = ps["A"]
    slider = slider_mesh(sl_c, ps["u"])
    all_parts = [(frame, COL["frame"]), (crank_w, COL["crank"]), (piv_w, COL["pivot"]), (leg_w, COL["leg"])]

    # 0 · overview: names of the parts
    mid = (np.array(P) + np.array([K.CX, Y_SH, Z_SH])) / 2 + [20, 0, -15]
    ov = render(all_parts, -35, 22, mid, 150, size=(900, 620), labels=[
        ("Test frame (test-frame)", [K.CX + 20, Y_SH - 14, 38], (-90, 120)),
        ("Crankshaft (crankshaft-2)", [K.CX, Y_SH, Z_SH + 6], (-60, -90)),
        ("Fork (pivot)", list(np.array(P) + [0, 0, YH / 2]), (40, -100)),
        ("Leg (leg-middle-right)", list(ps["F"] + [0, 0, 8]), (-10, -110)),
        ("Ball", list(sl_c), (60, -60)),
    ])
    ov.save(os.path.join(OUT, "0-parts.png"), optimize=True)

    # 1 · crankshaft journal in the frame (revolute)
    jr = C.JOURNAL / 2
    a = render([(crank, COL["crank"])], -25, 25, [3, 0, 0], 30,
               marks=[("circle", ([C.GEAR_T / 2, 0, 0], [1, 0, 0], jr))],
               labels=[("Journal edge at the gear face", [C.GEAR_T / 2, 0, jr], (-20, -120))],
               title="A · Crankshaft")
    fr_cut = keep(frame, lambda c: K.CX + 0.5 < c[0] < K.CX + 10)
    ce = [K.CX + C.WALL_IN, Y_SH, Z_SH]
    bb = render([(fr_cut, COL["frame"])], 60, 20, [K.CX + 3, Y_SH, Z_SH - 6], 46,
                marks=[("circle", (ce, [1, 0, 0], (C.JOURNAL + K.CLR) / 2))],
                labels=[("Hole edge on the inner face", list(np.array(ce) + [0, 0, 2.1]), (-60, -110))],
                title="B · Test frame (near wall hidden)")
    c = render([(frame, COL["frame"]), (crank_w, COL["crank"])], -35, 25, [K.CX, Y_SH, Z_SH - 4], 50,
               title="Result")
    row([a, bb, c], os.path.join(OUT, "1-crankshaft-frame.png"))

    # 2 · fork in the upper arm (revolute)
    tap = K.TAP / 2
    a = render([(pivot, COL["pivot"])], -40, 35, [0, 0, 4], 34,
               marks=[("circle", ([0, 0, YH / 2], [0, 0, 1], tap))],
               labels=[("Edge of the top hole", [0, 0, YH / 2], (40, -130))], title="A · Fork")
    z_arm = P[2] + YH / 2 + 0.4
    ce = [P[0], P[1], z_arm]
    bb = render([(frame, COL["frame"])], -40, -35, [P[0], P[1] + 6, z_arm], 40,
                marks=[("circle", (ce, [0, 0, 1], (K.SCREW + K.CLR) / 2))],
                labels=[("Hole edge, underside of the arm", ce, (-20, 150))],
                title="B · Test frame, seen from below")
    c = render([(frame, COL["frame"]), (piv_w, COL["pivot"])], -40, 20, list(P), 50, title="Result")
    row([a, bb, c], os.path.join(OUT, "2-fork-frame.png"))

    # 3 · leg in the fork (revolute)
    hy = L.LEG_W / 2
    a = render([(leg, COL["leg"])], -150, 20, [-2, 0, 0], 60,
               marks=[("circle", ([0, hy, 0], [0, 1, 0], (K.SCREW + K.CLR) / 2))],
               labels=[("Hole edge on the side face", [0, hy, 0], (-60, -150))], title="A · Leg")
    piv_cut = keep(pivot, lambda c: c[1] > 0)
    ce = [0, WIN_Y / 2, 0]
    bb = render([(piv_cut, COL["pivot"])], -150, 15, [0, 2, 0], 34,
                marks=[("circle", (ce, [0, 1, 0], (K.SCREW + K.CLR) / 2))],
                labels=[("Hole edge on the inner face", ce, (-40, -150))],
                title="B · Fork (near wall hidden)")
    c = render([(piv_w, COL["pivot"]), (leg_w, COL["leg"])], -40, 20, list(np.array(P) - 12 * ps["u"]), 60,
               title="Result")
    row([a, bb, c], os.path.join(OUT, "3-leg-fork.png"))

    # 4 · ball (crankshaft) to slider centre
    ball = [K.P_["XC"], K.P_["r"], 0]       # crankshaft-2, right crank at its printed phase (pi): pin at +Y
    a = render([(crank, COL["crank"])], 35, 20, [6, 1, 0], 38, marks=[("dot", ball)],
               labels=[("Centre of the ball on the +X side", ball, (-40, -150))], title="A · Crankshaft")
    sl0 = slider_mesh([0, 0, 0], [0, 0, 1])
    bb = render([(sl0, COL["slider"])], -40, 20, [0, 0, 0], 12, marks=[("dot", [0, 0, 0])],
                labels=[("Midpoint of the axis", [0, 0, 0], (80, -150))], title="B · Slider")
    row([a, bb], os.path.join(OUT, "4-ball-slider.png"))

    # 5 · slider axis along the bore (slider)
    x_b = -(INFO["mouth"] + INFO["bottom"]) / 2
    leg_cut = cut_near(leg, [x_b, 0, 0], 160, 15)
    a = render([(leg_cut, COL["leg"])], 160, 15, [x_b + 4, 0, 0], 30,
               marks=[("line", [[-INFO["mouth"] - 3, 0, 0], [-INFO["bottom"] + 3, 0, 0]]), ("dot", [x_b, 0, 0])],
               labels=[("Axis of the bore in the tube", [x_b, 0, 0], (40, -150))],
               title="A · Leg (cut in half)")
    bb = render([(sl0, COL["slider"])], -40, 20, [0, 0, 0], 12,
                marks=[("line", [[0, 0, -3], [0, 0, 3]]), ("dot", [0, 0, 0])],
                labels=[("Same point: its Z axis", [0, 0, 0], (80, -150))], title="B · Slider")
    c = render([(leg_cut, COL["leg"]), (slider_mesh([x_b, 0, 0], [1, 0, 0]), COL["slider"])], 160, 15,
               [x_b + 4, 0, 0], 30,
               title="Result (leg cut in half)")
    row([a, bb, c], os.path.join(OUT, "5-slider-leg.png"))

    # 6 · animation: what the finished assembly does, with the foot path
    feet = np.array([pose(t)["F"] for t in np.linspace(0, 2 * np.pi, 72)])
    frames = []
    for t in np.linspace(0, 2 * np.pi, 36, endpoint=False):
        q = pose(t)
        parts = [(frame, COL["frame"]), (tf(crank, *q["crank"]), COL["crank"]), (tf(pivot, *q["pivot"]), COL["pivot"]),
                 (tf(leg, *q["leg"]), COL["leg"])]
        marks = [("line", list(feet)), ("dot", q["F"])]
        whole = render(parts, -35, 15, mid, 150, size=(560, 420), marks=marks, title="Animated")
        zoom = render(parts[-1:], -90, 5, feet.mean(0), 34, size=(420, 420), marks=marks,
                      title="The foot, seen from outside")
        both = Image.new("RGB", (990, 420), (255, 255, 255))
        both.paste(whole, (0, 0))
        both.paste(zoom, (570, 0))
        frames.append(both.convert("P", palette=Image.ADAPTIVE))
    gif = os.path.join(OUT, "6-animation.gif")
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
    print(gif)


def slider_mesh(c, axis, r=1.5, h=4.0, n=32):
    ax = K.unit(axis)
    e1 = K.unit(np.cross(ax, [0, 0, 1]) if abs(ax[2]) < 0.9 else np.cross(ax, [1, 0, 0]))
    e2 = np.cross(ax, e1)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = r * (np.outer(np.cos(t), e1) + np.outer(np.sin(t), e2))
    lo, hi = np.asarray(c) + ring - ax * h / 2, np.asarray(c) + ring + ax * h / 2
    tris = []
    for k in range(n):
        j = (k + 1) % n
        tris += [[lo[k], lo[j], hi[j]], [lo[k], hi[j], hi[k]],
                 [np.asarray(c) - ax * h / 2, lo[j], lo[k]], [np.asarray(c) + ax * h / 2, hi[k], hi[j]]]
    return np.array(tris)


if __name__ == "__main__":
    main()
