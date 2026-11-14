#!/usr/bin/env python3
"""Gear train check in 2D (the gears' outlines in the YZ plane), finer than cad_verify's 3D steps.

For every meshing pair (crankshaft k or k + 1 with idler k), at every crank angle from 0 to 360° in --step degrees,
with every gear at its real angle (crankshaft gear offset - θ, idler phase + θ·12/n, from build.py):
  - overlap area of the two outlines (must be 0: no tooth in tooth)
  - circumferential backlash at the idler's pitch circle: the idler is turned forwards and backwards, the other gear
    held, until the teeth touch (bisection); backlash = (forward + backward free angle) × idler pitch radius
  - how far the idler sits from the middle of its free play (centred = the phases are as designed: a gear one tooth
    off would show here as no free play at all)
It also checks every idler against both neighbours at once (the v1 fault).

    python3 check_gear_train.py [--step 0.5]
"""
import argparse
import os
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import design  # noqa: E402

B = design("crankshafts")


def outline(teeth, ang, y, z):
    p = Polygon(B.gear_profile(teeth))
    return affinity.translate(affinity.rotate(p, ang, origin=(0, 0), use_radians=True), y, z)


def free(n, y, z, ang, other, sign, hi=0.2):
    """Largest rotation (rad) of the idler in direction sign before it touches `other`."""
    if outline(n, ang, y, z).intersection(other).area > 1e-7:
        return 0.0
    lo = 0.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if outline(n, ang + sign * mid, y, z).intersection(other).area > 1e-7:
            hi = mid
        else:
            lo = mid
    return lo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", type=float, default=0.5)
    args = ap.parse_args()
    sh, idl, off = B.shaft_yz(), B.idlers(), B.gear_offsets()
    print(f"crankshaft gear offsets: {', '.join(f'{np.degrees(a):.2f}°' for a in off)}")
    print(f"centre distance + {B.CD_EXTRA:.3f} mm per mesh, design backlash {B.BACKLASH} mm")
    ok = True
    for k, (y, z, n) in enumerate(idl):
        psi0 = B.idler_phase(k)
        cds = [np.hypot(y - sh[j][0], z - sh[j][1]) for j in (k, k + 1)]
        print(f"\nidler {k + 1}: {n} teeth at y {y:.2f}, z {z:.2f}; phase at crank 0: {np.degrees(psi0):.2f}°; "
              f"centre distances {cds[0]:.3f}, {cds[1]:.3f} mm (theory {B.MOD * (B.SHAFT_TEETH + n) / 2:.1f})")
        rp = B.MOD * n / 2
        res = {j: dict(area=0.0, bl=[], ctr=[]) for j in (k, k + 1)}
        both = []
        for t in np.arange(0, 360, args.step):
            th = np.radians(t)
            psi = psi0 + th * B.SHAFT_TEETH / n
            fwd_all, bwd_all = [], []
            for j in (k, k + 1):
                g = outline(B.SHAFT_TEETH, off[j] - th, *sh[j])
                a = outline(n, psi, y, z).intersection(g).area
                res[j]["area"] = max(res[j]["area"], a)
                f, b = free(n, y, z, psi, g, 1), free(n, y, z, psi, g, -1)
                fwd_all.append(f)
                bwd_all.append(b)
                res[j]["bl"].append((f + b) * rp)
                res[j]["ctr"].append((f - b) / 2 * rp)
            both.append(min(fwd_all) + min(bwd_all))
        for j, r in res.items():
            bl, c = np.array(r["bl"]), np.array(r["ctr"])
            bad = r["area"] > 1e-6 or bl.min() < 0.1 or bl.max() > 0.25
            ok &= not bad
            print(f"  with crankshaft {j + 1}: overlap {r['area']:.4f} mm²; backlash {bl.min():.3f}–{bl.max():.3f} mm "
                  f"(at the pitch circle); off-centre in its play {np.abs(c).max():.3f} mm  {'FAIL' if bad else 'ok'}")
        both = np.array(both) * rp
        ok &= both.min() > 0
        print(f"  both neighbours at once: free play {both.min():.3f}–{both.max():.3f} mm  "
              f"{'ok' if both.min() > 0 else 'FAIL: cannot mesh both'}")
    print("\ncheck_gear_train:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
