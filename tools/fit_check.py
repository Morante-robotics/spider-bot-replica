#!/usr/bin/env python3
"""Check whether boxes (battery holder, motor) fit inside the jenscolt Spider-Bot body, and at what scale.

The body is sliced every 1 mm above the top of the base (z = 62.5 mm in the original files). The free space at
each height is the inside of the body wall, minus the face block at the front (y < -20). The author's small screw
bosses and the posts on the base are ignored: the inside of the carcass is redesigned anyway. A box fits when its
footprint is inside the free space at every height it occupies, lying flat on the base, rotated 0 or 90 degrees.

Usage:
    python3 fit_check.py CARCASS_DIR --scale 1.2 --box "4xAAA holder" 64 49 16 --box N20 37 12 10 \
        [--clearance 2] [--png out.png] [--min-scale]

Needs numpy, matplotlib, trimesh and shapely (pip install numpy matplotlib trimesh shapely networkx scipy).
The meshes are not watertight, so the free space is built from the cross-sections, not from an inside test.
"""
import argparse
import os

import matplotlib
import numpy as np
import trimesh
from shapely.geometry import MultiPoint, Polygon, box
from shapely.ops import unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

FLOOR = 62.5      # top of the base, original files (mm)
FACE_Y = -19.5    # back face of the eye block, original files (mm)


class Cavity:
    def __init__(self, carcass_dir):
        self.body = trimesh.load(os.path.join(carcass_dir, "spideybot_body.stl"))
        self.cache = {}

    def at(self, z):
        """Free space (shapely polygon) at height z, original scale."""
        z = round(z, 2)
        if z in self.cache:
            return self.cache[z]
        sec = self.body.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        cav = Polygon()
        if sec is not None:
            path, tf = sec.to_2D()
            polys = []
            def to3d(ring):
                pts = np.array(ring.coords)
                return (np.c_[pts, np.zeros(len(pts)), np.ones(len(pts))] @ tf.T)[:, :2]

            for p in path.polygons_full:  # keep holes: where the wall closes into a ring, the hole is the cavity
                polys.append(Polygon(to3d(p.exterior), [to3d(h) for h in p.interiors]).buffer(0))
            # wall ring is open at the front, so: hull of the section minus the wall material
            hull = MultiPoint([c for p in polys for c in p.exterior.coords]).convex_hull
            cav = hull.difference(unary_union([p for p in polys if p.area > 100]))
            if cav.geom_type == "MultiPolygon":
                cav = max(cav.geoms, key=lambda g: g.area)
            cav = cav.intersection(box(-1e3, FACE_Y, 1e3, 1e3))
        self.cache[z] = cav
        return cav

    def column(self, height):
        """Free space common to every slice from the floor up to floor + height (original scale)."""
        out = None
        for z in np.arange(FLOOR, FLOOR + height + 0.01, 1.0):
            c = self.at(z)
            out = c if out is None else out.intersection(c)
        return out

    def place(self, L, W, H, scale, step=0.5):
        """Lower-left corner (x, y, dx, dy) in scaled mm of a free spot for an L x W x H box, or None."""
        L, W, H = L / scale, W / scale, H / scale
        col = self.column(H)
        if col is None or col.is_empty:
            return None
        x0, y0, x1, y1 = col.bounds
        cx, cy = col.centroid.x, col.centroid.y
        spots = []
        for a, b in ((L, W), (W, L)):
            for x in np.arange(x0, x1 - a + 0.01, step):
                for y in np.arange(y0, y1 - b + 0.01, step):
                    if col.contains(box(x, y, x + a, y + b)):
                        spots.append(((x + a / 2 - cx) ** 2 + (y + b / 2 - cy) ** 2, x, y, a, b))
        if not spots:
            return None
        _, x, y, a, b = min(spots)  # most central spot
        return x * scale, y * scale, a * scale, b * scale


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carcass_dir")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--box", nargs=4, action="append", metavar=("NAME", "L", "W", "H"), required=True)
    ap.add_argument("--clearance", type=float, default=0.0, help="mm added on each side (and on top)")
    ap.add_argument("--min-scale", action="store_true", help="also print the smallest scale (1 %% steps) that fits")
    ap.add_argument("--png")
    args = ap.parse_args()

    cav = Cavity(args.carcass_dir)
    c = args.clearance
    rows = []
    for name, L, W, H in args.box:
        L, W, H = float(L), float(W), float(H)
        Lc, Wc, Hc = L + 2 * c, W + 2 * c, H + c
        spot = cav.place(Lc, Wc, Hc, args.scale)
        line = f"{name}: {L:g} x {W:g} x {H:g} mm, clearance {c:g} mm, scale {args.scale:.0%}: "
        line += "FITS" if spot else "does NOT fit"
        if args.min_scale:
            s = next((s / 100 for s in range(80, 201) if cav.place(Lc, Wc, Hc, s / 100, step=1.0)), None)
            line += f" | smallest scale that fits: {s:.0%}" if s else " | does not fit up to 200 %"
        print(line)
        rows.append((name, L, W, H, Hc, spot))

    if args.png:
        n = len(rows)
        fig, axs = plt.subplots(1, n, figsize=(5.2 * n, 5.4), squeeze=False)
        s = args.scale
        for ax, (name, L, W, H, Hc, spot) in zip(axs[0], rows):
            col = cav.column(Hc / s)
            for g in (col.geoms if col.geom_type == "MultiPolygon" else [col]):
                x, y = g.exterior.xy
                x, y = np.array(x) * s, np.array(y) * s
                ax.fill(x, y, color="#ddd")
                ax.plot(x, y, "k", lw=0.8)
            if spot:
                x, y, a, b = spot
                ax.add_patch(Rectangle((x, y), a, b, fill=False, ec="#7f8c8d", lw=1, ls="--"))
                ax.add_patch(Rectangle((x + c, y + c), a - 2 * c, b - 2 * c, fill=False, ec="#27ae60", lw=2.2))
            ok = "fits" if spot else "does NOT fit"
            ax.set_title(f"{name}\n{L:g} × {W:g} × {H:g} mm — {ok}", fontsize=11)
            ax.set_aspect("equal")
            ax.grid(alpha=0.3)
            ax.set_xlabel("x (mm)")
            ax.text(0.02, 0.02, f"grey = free space inside the body, {s:.0%} scale,\n"
                    f"from the base up to {Hc:g} mm; dashed = {c:g} mm clearance",
                    transform=ax.transAxes, fontsize=8)
        axs[0][0].set_ylabel("y (mm) — front (eyes) is down")
        plt.tight_layout()
        plt.savefig(args.png, dpi=90)
        print(f"wrote {args.png}")


if __name__ == "__main__":
    main()
