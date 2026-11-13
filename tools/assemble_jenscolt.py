#!/usr/bin/env python3
"""Join jenscolt's Spidey-Bot STLs into one assembled STL, for previews and as a size reference.

The original files place body, base, sensor and the front leg pair; eyes are off to the side and only one leg per
side is included. This script:
  - keeps body, base, sensor and the front legs where the author put them;
  - moves the big and small eye domes (2 of each) into their sockets, flat face back, dome forward (-Y);
  - adds the other 3 legs per side: rear leg mirrored front/back, two middle legs rotated about the body's vertical
    axis. THIS LAYOUT IS APPROXIMATE (not from the author), good enough for pictures, not for fitting parts.

Usage:
    python3 assemble_jenscolt.py CARCASS_DIR OUT.stl
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # stl_preview.py is next to it
from stl_preview import load  # noqa: E402

CENTER_X, CENTER_Y = 35.6, -3.0          # vertical axis of the body (mm), from the leg sockets
EYES = [(22.0, 91.0), (49.0, 91.0)]      # big eye socket centers (x, z)
SMALL_EYES = [(7.0, 100.0), (64.0, 100.0)]
EYE_BACK_Y, SMALL_EYE_BACK_Y = -50.0, -44.0
MIDDLE_LEG_ANGLES = (-24.3, -48.7)       # degrees, rotating the front leg toward the rear


def place(tris, x, z, back_y):
    v = tris.reshape(-1, 3)
    c = np.array([(v[:, 0].min() + v[:, 0].max()) / 2, v[:, 1].max(), (v[:, 2].min() + v[:, 2].max()) / 2])
    return tris + (np.array([x, back_y, z]) - c)


def rotate_z(tris, deg, side):
    a = np.radians(deg if side == "R" else -deg)
    rot = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    ctr = np.array([CENTER_X, CENTER_Y, 0])
    return (tris - ctr) @ rot.T + ctr


def mirror_y(tris):
    out = tris.copy()
    out[:, :, 1] = 2 * CENTER_Y - out[:, :, 1]
    return out[:, ::-1]  # keep outward normals


def save(path, tris):
    tris = tris.astype("<f4")
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(tris), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    rec["n"], rec["v"] = n, tris.reshape(-1, 9)
    with open(path, "wb") as f:
        f.write(b"Spidey-Bot by jenscolt, assembled preview".ljust(80, b" "))
        f.write(np.uint32(len(tris)).tobytes())
        f.write(rec.tobytes())


def main():
    d, out = sys.argv[1], sys.argv[2]
    part = lambda name: load(os.path.join(d, f"spideybot_{name}.stl"))  # noqa: E731
    parts = [part("body"), part("base"), part("sensor")]
    parts += [place(part("eye"), x, z, EYE_BACK_Y) for x, z in EYES]
    parts += [place(part("small_eye"), x, z, SMALL_EYE_BACK_Y) for x, z in SMALL_EYES]
    for side in ("L", "R"):
        leg = np.concatenate([part(f"{side}_leg1"), part(f"{side}_leg2")])
        parts += [leg, mirror_y(leg)]
        parts += [rotate_z(leg, a, side) for a in MIDDLE_LEG_ANGLES]
    save(out, np.concatenate(parts))


if __name__ == "__main__":
    main()
