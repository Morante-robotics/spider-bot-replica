"""Failure figure for base v1's cap: the cap as designed beside the printed one, its broken tongues circled.

Left: cap.stl from cad/base/, drawn upside down (as printed, tongues up) with tools/figures.py; the tongue count and
sizes in the labels are measured from the mesh. Right: Morante's photo of the printed cap (images/base-v1-print-4.jpg)
with the remaining tongues and the scars of the broken ones circled; the circle positions are pixel coordinates in
that photo.

    python3 cad/base/cap_failure_figure.py       # writes images/base-v1-cap-failure.png
"""
import os
import sys

import numpy as np
import trimesh
from matplotlib.patches import Ellipse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import figures  # noqa: E402
from figures import plt  # noqa: E402

PHOTO = os.path.join(ROOT, "images", "base-v1-print-4.jpg")
OUT = os.path.join(ROOT, "images", "base-v1-cap-failure.png")
PHOTO_CROP = (180, 820, 1080, 1600)            # the cap in the photo (left, top, right, bottom), px
KEPT = (365, 1385, 150, 120)                   # the tongues still on the plate: centre x, y, width, height (px)
SCARS = (740, 1080, 360, 210)                  # the pale marks where the other tongues broke off


def cap_mesh():
    for rel in ("cad/base/out/cap.stl",):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            return trimesh.load(p)
    sys.exit("cap.stl not found in cad/base/")


def tongues(cap):
    """Tongues = the pieces of a cut halfway down below the plate; their count and size come from the mesh."""
    z0, z1 = cap.bounds[:, 2]
    zs = np.linspace(z0, z1, 200)
    areas = []
    for z in zs:
        s = cap.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        areas.append(0 if s is None else s.to_2D()[0].area)
    plate_z = zs[int(np.argmax(np.array(areas) > 0.5 * max(areas)))]   # where the plate starts
    s, _ = cap.section(plane_origin=[0, 0, (z0 + plate_z) / 2], plane_normal=[0, 0, 1]).to_2D()
    sizes = sorted(tuple(np.ptp(np.array(p.bounds).reshape(2, 2), axis=0).round(1)) for p in s.polygons_full)
    return len(sizes), sizes[0], plate_z - z0


def main():
    cap = cap_mesh()
    n, (w, l), h = tongues(cap)
    cap.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))   # tongues up, as printed

    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw={"width_ratios": [1.15, 1]})
    proj = figures.draw(a, [{"mesh": cap, "color": figures.PALETTE[1]}], view=(32, -55))
    top = cap.bounds[1, 2]
    v = cap.vertices[cap.vertices[:, 2] > top - 0.2]
    tip = v[np.argmax(v[:, 1])]
    a.annotate(f"{n} tongues, {min(w, l):.1f} × {max(w, l):.1f} mm,\n{h:.1f} mm tall", proj(tip[None])[0],
               (0.02, 0.88), textcoords="axes fraction", fontsize=figures.FONT + 1, va="top",
               arrowprops={"arrowstyle": "-|>", "color": "#1a1a1a", "lw": 1.5})
    a.set_title("As designed: cap.stl, tongues up", fontsize=figures.FONT + 2, pad=12)
    a.axis("off")

    im = Image.open(PHOTO)
    x0, y0, x1, y1 = PHOTO_CROP
    b.imshow(im.crop(PHOTO_CROP))
    red = "#d62728"
    box = {"boxstyle": "round,pad=0.3", "fc": "white", "ec": red}
    for (cx, cy, ew, eh), text, xy_text, side in ((KEPT, "2 tongues left", (560, 720), 1),
                                                  (SCARS, f"{n - 2} broke off:\npale scars\nwhere they stood",
                                                   (20, 330), -1)):
        b.add_patch(Ellipse((cx - x0, cy - y0), ew, eh, fill=False, ec="white", lw=5))
        b.add_patch(Ellipse((cx - x0, cy - y0), ew, eh, fill=False, ec=red, lw=3))
        b.annotate(text, (cx - x0 + side * ew / 2, cy - y0), xy_text, color=red, fontsize=figures.FONT + 1,
                   fontweight="bold", bbox=box, arrowprops={"arrowstyle": "-|>", "color": red, "lw": 2})
    b.set_title("As printed (2026-11-13), after fitting", fontsize=figures.FONT + 2)
    b.axis("off")
    fig.tight_layout()
    fig.savefig(OUT, dpi=110, facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
