"""cad_verify spec for <design>: every part, one fixed. Fields: see the docstring of tools/cad_verify.py.

The demo (a block in a window) FAILS retention on purpose: a part that only sits in an opening is not held (base v1
front block, 2026-11-13). A real design gives it a stop: a cap, a pin, a screw.

    python3 ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import design, fits  # noqa: E402
B = design(os.path.basename(HERE))                # this folder's build.py (cad/__init__.py)
from cad_verify import rod, tool  # noqa: E402,F401

STEP = int(os.environ.get("VERIFY_STEP", 10))
PARTS = {"frame": {"stl": "out/frame.stl", "fixed": True},
         "example": {"stl": "out/example.stl"}}
#        "pin1": {"mesh": rod(3.0, 20, [x, y, z], [1, 0, 0]), "hardware": True, "label": "pasador Ø3×20"}
MOTION = [0]                                       # e.g. list(range(0, 360, STEP))


def poses(t):
    return {}                                      # part -> 4x4 matrix at motion step t


RETAIN = {"example": {"play": 0.5}}                # every part but the fixed one
JOINTS = {("example", "frame"): {"fit": fits.WINDOW, "why": "block in its window"}}
MARKS = {}                                         # every gear and "phased" part: what and where
ASSEMBLY = [("frame", None), ("example", [0, 0, 1])]
ACCESS = []                                        # one tool(...) per fastener in ASSEMBLY
PRINT_ORIENT = {}
SECTIONS = []                                      # through every joint
LABELS = {"es": {"frame": "marco", "example": "bloque"}}
MEASURE = []                                       # what Morante checks with the caliper after printing
