#!/usr/bin/env python3
"""The three ways tried to drive the 8 toy legs from one motor, side by side (build log: Legs and drive).

Usage:
    python3 tools/drive_attempts_figure.py      # sim/images/drive-attempts.png

Uses the simulator (sim/toy_leg_3d.py) and its saved geometries: one crankshaft across the body
(toy_leg_3d_strict.json), two side crankshafts (toy_leg_3d_sides.json) and four lateral crankshafts, the
geometry used for the CAD (toy_leg_3d_rows_cad.json). Top row: from above; bottom row: from the side.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "sim")
sys.path.insert(0, SIM)
import toy_leg_3d as T  # noqa: E402

ATTEMPTS = [
    ("toy_leg_3d_strict.json", "shaft", "1 · One crankshaft across the body\n✗ the arms cut through the other legs' cranks"),
    ("toy_leg_3d_sides.json", "sides", "2 · Two crankshafts, front to back\n✗ fits, but the feet move sideways"),
    ("toy_leg_3d_rows_cad.json", "rows", "3 · Four crankshafts across the body\n✓ fits and walks forward"),
]


def main():
    results = []
    for name, axle, title in ATTEMPTS:
        s = next(s for s in json.load(open(os.path.join(SIM, name))) if s["axle"] == axle and s["slide"] == "crank")
        p = {k: s[k] for k in T.ranges(axle)}
        m, theta, legs, ground, support = T.measure(p, axle, "crank", steps=360, full=True, strict=True)
        results.append((title, m, theta, legs, ground, support))
    T.draw(results, png=os.path.join(SIM, "images", "drive-attempts.png"))


if __name__ == "__main__":
    main()
