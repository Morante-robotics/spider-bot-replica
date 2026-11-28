"""cad_verify spec for the coupons: every coupon is its own printed test piece, none touches another.

They are `bench` parts (a jig used on the bench, not in the machine): only integrity (closed solid, walls, bed) and the
print check apply. No motion, joints or retention exist between coupons; the fits they prove are in README.md's table.

    ../../.venv/bin/python ../../tools/cad_verify.py verify.py --smoke
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from cad import design  # noqa: E402
B = design(os.path.basename(HERE))

NAMES = list(B.PARTS)
# loose pieces per coupon (a pin plate + 3 tubes, a stand-in + 3 U's, one gear pair + the plate...): bodies is that count, on purpose
BODIES = {"c1-leg-snap": 4, "c2-motor-seat": 4, "c3-gear-tip": 3, "c4-pilots": 2, "c5-seats": 2, "c6-marks": 3,
          "c7-leg-turn": 4, "c8-neighbour": 6, "c9-leg-window": 2, "c10-dshaft": 3, "c11-snap": 2, "c12-cell-lid": 4}
PARTS = {n: {"stl": f"out/{n}.stl", "bench": True, "bodies": BODIES[n]} for n in NAMES}
PARTS[NAMES[0]]["fixed"] = True
MOTION = [0]


def poses(t):
    return {}


ASSEMBLY = []
RETAIN = {}
JOINTS = {}
MARKS = {}
ACCESS = []
PRINT_ORIENT = {}
SECTIONS = []
LABELS = {"es": {"c1-leg-snap": "cupón enganche pierna", "c2-motor-seat": "cupón asiento motor",
                 "c3-gear-tip": "cupón punta de engranaje", "c4-pilots": "cupón pilotos M3",
                 "c5-seats": "cupón asientos de cabeza", "c6-marks": "cupón números grabados",
                 "c7-leg-turn": "cupón giro pierna-pin", "c8-neighbour": "cupón vecinos",
                 "c9-leg-window": "cupón ventana de pierna", "c10-dshaft": "cupón eje en D", "c11-snap": "cupón enganche cuerpo-base",
                 "c12-cell-lid": "cupón tapa de pilas"}}
MEASURE = []
