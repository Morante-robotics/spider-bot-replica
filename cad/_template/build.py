#!/usr/bin/env python3
"""<Design>: <one line>.

Parts: <name>  <what it is>

Coordinates as in ../README.md (mm, Z up, forward = -Y, +X = right). Every part is exported to out/ as STEP and STL
in its own print frame.

Usage:
    ../../.venv/bin/python build.py               # every part (coarse STL; --fine for the printed one)
    ../../.venv/bin/python build.py --part <name> # one part (faster while iterating)
Each part has its own CAD_BUDGET (tools/timebudget.py, default 40 s): past it the build names the stage and exits 3.
"""
import os
import sys

from build123d import Box

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timebudget  # noqa: E402
from cad import common, fits  # noqa: E402,F401   another design's numbers: from cad import design; C = design("crankshafts")

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
    args = common.part_args(__doc__, PARTS)     # --part, --fine, and the time-budget watchdog
    for name in args.part or PARTS:
        timebudget.reset(name)                  # each part its own budget; a slow stage: with timebudget.stage("..."):
        common.export(name, PARTS[name](), OUT, fine=args.fine)   # prints its size


if __name__ == "__main__":
    main()
