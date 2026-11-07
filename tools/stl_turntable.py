#!/usr/bin/env python3
"""Render a turntable animation (GIF) of one or more binary STL files shown together.

Usage:
    python3 stl_turntable.py OUT.gif part1.stl [part2.stl ...] [--frames 36] [--elev 20] [--size 480]

Needs numpy, matplotlib and Pillow (pip install numpy matplotlib pillow).
"""
import argparse
import io

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

from stl_preview import draw, load  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("stls", nargs="+")
    p.add_argument("--frames", type=int, default=36)
    p.add_argument("--elev", type=float, default=20)
    p.add_argument("--size", type=int, default=480)
    a = p.parse_args()

    tris = np.concatenate([load(s) for s in a.stls])
    frames = []
    for i in range(a.frames):
        fig = plt.figure(figsize=(a.size / 100, a.size / 100), dpi=100)
        ax = fig.add_subplot(projection="3d")
        draw(ax, tris, a.elev, -60 + 360 * i / a.frames)
        plt.subplots_adjust(0, 0, 1, 1)
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        frames.append(Image.open(buf).convert("P", palette=Image.ADAPTIVE, colors=64))
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)


if __name__ == "__main__":
    main()
