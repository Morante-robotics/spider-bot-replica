#!/usr/bin/env python3
"""Render a turntable animation (GIF) of one or more binary STL files shown together.

Usage:
    python3 stl_turntable.py OUT.gif part1.stl [part2.stl ...] [--frames 36] [--elev 20] [--size 520]

Flat-shaded painter's renderer with Pillow: seconds per frame even for 400k triangles.
Needs numpy and Pillow (pip install numpy pillow).
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw

from stl_preview import load

COLOR = np.array([192, 57, 43])  # same red as stl_preview.py
LIGHT = np.array([0.4, -0.7, 0.6]) / np.linalg.norm([0.4, -0.7, 0.6])


def frame(tris, azim, elev, size):
    a, e = np.radians(azim), np.radians(elev)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    v = tris @ (rx @ rz).T  # camera looks along +Y: screen x = X, screen up = Z, depth = Y
    n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.3 + 0.7 * np.abs(n @ LIGHT)
    colors = (COLOR * shade[:, None]).astype(int)
    pts = np.stack([v[:, :, 0] + size / 2, size / 2 - v[:, :, 2]], axis=2)
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    for i in np.argsort(-v[:, :, 1].mean(1)):  # far to near
        draw.polygon([tuple(q) for q in pts[i]], fill=tuple(colors[i]))
    return img.convert("P", palette=Image.ADAPTIVE, colors=64)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("stls", nargs="+")
    p.add_argument("--frames", type=int, default=36)
    p.add_argument("--elev", type=float, default=20)
    p.add_argument("--size", type=int, default=520)
    a = p.parse_args()

    tris = np.concatenate([load(s) for s in a.stls])
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    tris = (tris - (lo + hi) / 2) * (0.9 * a.size / np.linalg.norm(hi - lo))
    frames = [frame(tris, -60 + 360 * i / a.frames, a.elev, a.size) for i in range(a.frames)]
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)


if __name__ == "__main__":
    main()
