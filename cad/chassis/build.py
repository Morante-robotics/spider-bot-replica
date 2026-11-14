#!/usr/bin/env python3
"""<Design>: <one line>.

Parts: <name>  <what it is>

Coordinates as in ../README.md (mm, Z up, forward = -Y, +X = right). Every part is exported to out/ as STEP and STL
in its own print frame.

Usage:
    python3 build.py               # every part
    python3 build.py --part <name> # one part (faster while iterating)
"""
import argparse
import os
import sys

from build123d import Box, export_step, export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import fits  # noqa: E402,F401   another design's numbers: from cad import design; C = design("crankshafts")

OUT = os.path.join(HERE, "out")

# ---- parameters: every number named, with its source
EXAMPLE_W = 10.0                       # <source: file + parameter, or measurement>
SLOT_W = EXAMPLE_W + 2 * fits.WINDOW.side   # never type a clearance: take it from fits.py


def frame():
    return Box(30, 30, 5) - Box(SLOT_W, SLOT_W, 10)


def example():
    return Box(EXAMPLE_W, EXAMPLE_W, 5)


PARTS = {"frame": frame, "example": example}   # name -> function that builds it


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append", choices=sorted(PARTS), help="build only this part (repeatable)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for name in args.part or PARTS:
        shape = PARTS[name]()
        export_step(shape, os.path.join(OUT, f"{name}.step"))
        export_stl(shape, os.path.join(OUT, f"{name}.stl"), tolerance=0.02, angular_tolerance=0.15)
        print(name)


if __name__ == "__main__":
    main()
