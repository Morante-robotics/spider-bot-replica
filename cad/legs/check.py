#!/usr/bin/env python3
"""Collision check of the Spider-Bot legs and drive over a full crank turn.

Loads the STL parts written by the build.py of legs, crankshafts, gear-train-test (its spine stands in for the
robot's) and test-frame, places them with the simulator's kinematics every few degrees (poses() in build.py, the same
placement as build.py --assembly) and reports every pair of parts that overlaps, with the volume. Pairs that touch on
purpose are skipped: meshing gears. Pins are not modelled, so a leg must stay clear of its own pivot and the ball
clear of its bore: any overlap there is a real fault. The test frame is checked with its middle leg, pivot and
crankshaft 2.

Usage:
    python3 check.py              # every 10°
    python3 check.py --step 5

Needs trimesh and manifold3d (pip install trimesh manifold3d).
"""
import argparse
import itertools
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import design  # noqa: E402

L = design("legs")


def skip(a, b):
    gears = lambda n: n.startswith("idler") or n.startswith("crankshaft")
    return gears(a) and gears(b)


def overlap(m1, m2):
    if not (np.all(m1.bounds[0] <= m2.bounds[1]) and np.all(m2.bounds[0] <= m1.bounds[1])):
        return 0.0
    r = trimesh.boolean.intersection([m1, m2], engine="manifold")
    return r.volume if r is not None and len(r.faces) else 0.0


def neighbours(n1, n2):
    """Pairs whose gap is worth measuring: a leg against the next leg on its side, its own pivot and crankshaft, and
    any crankshaft against the spine."""
    def leg(n):
        return (int(n[3]), n[4]) if n.startswith("leg") else None
    a, b = leg(n1), leg(n2)
    if a and b:
        return a[1] == b[1] and abs(a[0] - b[0]) == 1
    if a or b:
        i, s = a or b
        other = n2 if a else n1
        return other in (f"pivot{i}{s}", f"crankshaft{i}")
    return {n1[:5], n2[:5]} == {"crank", "spine"}


def gap(m1, m2, n=1200):
    """Smallest distance (mm) between the surfaces of two meshes that do not overlap, sampled."""
    if np.any(m1.bounds[0] > m2.bounds[1] + 3) or np.any(m2.bounds[0] > m1.bounds[1] + 3):
        return np.inf
    p1 = m1.sample(n)
    p2 = m2.sample(n)
    d1 = trimesh.proximity.closest_point(m2, p1)[1].min()
    d2 = trimesh.proximity.closest_point(m1, p2)[1].min()
    return min(d1, d2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", type=float, default=10)
    ap.add_argument("--min", type=float, default=0.01, help="smallest overlap reported (mm³)")
    ap.add_argument("--gaps", action="store_true", help="also measure the smallest gap between parts that do not "
                    "overlap (slower); reports pairs closer than 1 mm")
    args = ap.parse_args()
    cache = {}

    def mesh(f, M):
        if f not in cache:
            cache[f] = trimesh.load(L.stl(f))
        m = cache[f].copy()
        m.apply_transform(M)
        return m

    worst, gaps = {}, {}
    for a in np.arange(0, 360, args.step):
        th = np.radians(a)
        ps = L.poses(th)
        ms = {n: mesh(f, M) for n, f, M in ps}
        for n1, n2 in itertools.combinations(ms, 2):
            if skip(n1, n2):
                continue
            v = overlap(ms[n1], ms[n2])
            if v > args.min and v > worst.get((n1, n2), (0, 0))[0]:
                worst[(n1, n2)] = (v, a)
            elif args.gaps and v <= args.min and neighbours(n1, n2):
                g = gap(ms[n1], ms[n2])
                if g < gaps.get((n1, n2), (np.inf, 0))[0]:
                    gaps[(n1, n2)] = (g, a)
        print(f"{a:g}°", end=" ", flush=True)
        # test frame: right middle leg, its pivot, crankshaft 2 and the frame (robot coordinates)
        tf = {n: ms[n] for n in ("leg1R", "pivot1R", "crankshaft1")}
        tf["test-frame"] = mesh("test-frame", np.eye(4))
        tf["keeper"] = mesh("test-frame-keeper", np.eye(4))
        for n1, n2 in itertools.combinations(tf, 2):
            v = overlap(tf[n1], tf[n2])
            key = ("frame:" + n1, n2)
            if v > args.min and v > worst.get(key, (0, 0))[0]:
                worst[key] = (v, a)
            elif args.gaps and v <= args.min and {n1, n2} & {"test-frame", "keeper"}:
                g = gap(tf[n1], tf[n2])
                if g < gaps.get(key, (np.inf, 0))[0]:
                    gaps[key] = (g, a)
    if not worst:
        print(f"no overlaps over a full turn (every {args.step:g}°)")
    if args.gaps:
        close = sorted(((g, a, k) for k, (g, a) in gaps.items() if g < 1.0))
        print(f"{len(close)} pairs closer than 1 mm" + (":" if close else ""))
        for g, a, (n1, n2) in close:
            print(f"{n1:18s} × {n2:18s} gap {g:5.2f} mm (closest at {a:g}°)")
    for (n1, n2), (v, a) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
        print(f"{n1:18s} × {n2:18s} {v:8.2f} mm³ (worst at {a:g}°)")


if __name__ == "__main__":
    main()
