"""N2 plan diagram: exploded view of the looks robot on N1's meshes plus boxes for the parts not modelled yet.
Not a check: positions are N0/N1's (cad/mockup), boxes are the plan's envelopes. Usage (repo root):
    uv run python cad/robot/plan_figure.py cad/robot/images/plan-exploded.png
"""
import os, sys
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "cad", "mockup"), os.path.join(ROOT, "tools")]
import n0, n1, figures as Fg  # noqa: E402

R = n1.run()
st, legs, bx = R["st"], R["legs"], R["bx"]
UP = dict(body=46, eyes=46, keeper=24, cells=34, drive=12, legs=0, base=0)    # exploded lift (mm)


def box(c, s, dz):
    m = trimesh.creation.box(extents=s); m.apply_translation(np.array(c, float) + [0, 0, dz]); return m


items, notes = [], []
add = lambda m, col, txt=None, at=None: (items.append(dict(mesh=m, color=col)), txt and notes.append((at, txt)))
body = trimesh.Trimesh(st["body_v"] + [0, 0, UP["body"]], st["body_f"])
add(body, "#c0392b", "1 body (dome + eyes, mesh)", body.vertices[body.vertices[:, 2].argmax()])
eyes = trimesh.Trimesh(st["eyes_v"] + [0, 0, UP["eyes"]], st["eyes_f"]); add(eyes, "#2e86c1")
base = trimesh.Trimesh(st["base_v"], st["base_f"])
add(base, "#7f8c8d", "2 base (bowl, ground part)", base.vertices[base.vertices[:, 1].argmin()])
for i, lg in enumerate(legs):
    W = n1.carry(lg["loc"], lg["g"])[0]
    m = trimesh.Trimesh(W, lg["F"]); add(m, "#e2b007", "leg ×8 (3 arm + 4 outer leg)" if i == 1 else None,
                                         m.vertices[m.vertices[:, 0].argmax()])
lo, hi = bx["engranajes"]; c, s = (lo + hi) / 2, hi - lo
add(box(c, s, UP["drive"]), "#27ae60", "5 spine + 6 cap + gears", c + [0, 0, UP["drive"] + s[2] / 2])
for k, (lo, hi) in bx.items():
    if k.startswith("cigüeñal"):
        add(box((lo + hi) / 2, hi - lo, UP["drive"]), "#16a085",
            "7 crankshaft ×4 (balls in the arms)" if k.endswith("1") else None, (lo + hi) / 2 + [0, 0, UP["drive"]])
# motor and cell holder: the best layout of `probes.py layouts` at S 0.65 (cad/robot/out/.cache/layouts_0.650.json)
import json
LAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", ".cache", "layouts_0.650.json")
best = max(json.load(open(LAY)), key=lambda r: r["least"])
for nm, lo, hi in best["boxes"]:
    lo, hi = np.array(lo), np.array(hi); c, s_ = (lo + hi) / 2, hi - lo
    if nm.startswith("holder"):
        add(box(c, s_, UP["cells"]), "#e67e22", "11 cell holder (3P pack ×2, on edge) + 12 lid" if nm.endswith("A") else None,
            c + [0, 0, UP["cells"] + s_[2] / 2])
    else:
        add(box(c, s_, UP["drive"]), "#8e44ad", "9 N10 motor + 10 clamp" if nm == "motor" else None,
            c + [0, 0, UP["drive"] + s_[2] / 2])
for sx in (1, -1):
    add(box([sx * 24, 1.5, 16.2], [6, 36, 2], UP["keeper"]), "#d35400",
        "13 pivot keeper ×2" if sx > 0 else None, np.array([sx * 24, 1.5, 17.2 + UP["keeper"]]))
lo, hi = bx["interruptor"]; add(box((lo + hi) / 2, hi - lo, UP["drive"]), "#4d4d4d", "SS12D00 switch + 14 retainer",
                                (lo + hi) / 2 + [0, 0, UP["drive"]])
add(box([0, -24, 28], [20, 2, 8], UP["body"]), "#2e86c1", "15 eyes board (perfboard, LEDs)",
    np.array([0, -24, 32 + UP["body"]]))
fig, ax = plt.subplots(figsize=(13, 10))
proj = Fg.draw(ax, items, view=(22, -62))
Fg.side_labels(ax, [(proj(np.atleast_2d(p))[0], t) for p, t in notes])
ax.set_title("Spider-Bot N2 plan: exploded view (N1 meshes; boxes = parts not modelled yet). Numbers = part list",
             fontsize=Fg.FONT + 2)
fig.savefig(sys.argv[1], dpi=110, bbox_inches="tight"); print("wrote", sys.argv[1])
