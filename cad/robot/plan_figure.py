"""N2 plan diagram (rev 4): exploded view of the looks robot on N1's meshes at S 0.65 plus boxes for the parts not
modelled yet, placed by `probes.py layouts4` (cad/robot/out/.cache/layouts4_0.650.json). Labels in Spanish (for
Morante). Not a check: boxes are the plan's envelopes. Usage (repo root):
    uv run python cad/robot/plan_figure.py cad/robot/images/plan-exploded.png
"""
import os, sys, json
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "cad", "mockup"), os.path.join(ROOT, "tools")]
import n1, figures as Fg  # noqa: E402
import probes as P  # noqa: E402

R = n1.run(P.p_at(P.S_FIX))
st, legs = R["st"], R["legs"]
UP = dict(body=50, eyes=50, keeper=26, cells=36, drive=14, legs=0, base=0)    # exploded lift (mm)
LAY = json.load(open(os.path.join(HERE, "out", ".cache", f"layouts4_{P.S_FIX:.3f}.json")))
best = max(LAY, key=lambda r: r["least"])


def box(lo, hi, dz):
    lo, hi = np.array(lo, float), np.array(hi, float)
    m = trimesh.creation.box(extents=hi - lo)
    m.apply_translation((lo + hi) / 2 + [0, 0, dz])
    return m


items, notes = [], []


def add(m, col, txt=None, at=None):
    items.append(dict(mesh=m, color=col))
    if txt:
        notes.append((at, txt))


body = trimesh.Trimesh(st["body_v"] + [0, 0, UP["body"]], st["body_f"])
add(body, "#c0392b", "1 cuerpo (cúpula, ojos del color del cuerpo)", body.vertices[body.vertices[:, 2].argmax()])
add(trimesh.Trimesh(st["eyes_v"] + [0, 0, UP["eyes"]], st["eyes_f"]), "#2e86c1")
base = trimesh.Trimesh(st["base_v"], st["base_f"])
add(base, "#7f8c8d", "2 base (pieza fija, muescas de las patas)", base.vertices[base.vertices[:, 1].argmin()])
for i, lg in enumerate(legs):
    W = n1.carry(lg["loc"], lg["g"])[0]
    m = trimesh.Trimesh(W, lg["F"])
    add(m, "#e2b007", "3 brazo + 4 pata (×8)" if i == 1 else None, m.vertices[m.vertices[:, 0].argmax()])
c = P._ctx(P.S_FIX, P.BALL_D2, P.CRANK_DY_65)
lo, hi = c["strip"]
add(box(lo, hi, UP["drive"]), "#27ae60", "5 espina + 6 tapa + 8 engranajes locos", (lo + hi) / 2 + [0, 0, UP["drive"] + 8])
for k, (lo, hi) in enumerate(c["sweeps"][:4]):
    add(box(lo, hi, UP["drive"]), "#16a085", "7 cigüeñal ×4 (bolas Ø2 en los brazos)" if k == 0 else None,
        (lo + hi) / 2 + [0, 0, UP["drive"]])
TXT = {"motor": ("#8e44ad", "drive", "9 motor N10 + 10 abrazadera (2 × M3)"),
       "motor crown": ("#9b59b6", "drive", "16 corona 20T + piñón recto 10T (una pieza)"),
       "motor idler": ("#a569bd", "drive", "17 loco de transmisión a la tira"),
       "holderA": ("#e67e22", "cells", "11 portapilas: 2 paquetes 3P de canto + 12 tapas"),
       "eyes board": ("#2e86c1", "body", "15 placa de ojos (2 LED de 5 mm, resistencias)"),
       "switch": ("#4d4d4d", "drive", "interruptor SS12D00 + 14 retén"),
       "bossF body": ("#c0392b", "body", "tetones del cuerpo (2 × M3 desde abajo)"),
       "jst1": ("#34495e", "cells", "2 conectores JST-XH")}
for nm, lo, hi in best["boxes"]:
    key = nm if nm in TXT else None
    grp = nm.split()[0]
    col, up, txt = TXT.get(nm, (None, None, None))
    if col is None:
        col = {"motor": "#8e44ad", "holderA": "#e67e22", "holderB": "#e67e22", "LEDL": "#5dade2",
               "LEDR": "#5dade2", "eyes": "#2e86c1", "bossF": "#c0392b", "bossR": "#c0392b",
               "jst2": "#34495e"}.get(grp, "#95a5a6")
        up = {"holderA": "cells", "holderB": "cells", "LEDL": "body", "LEDR": "body", "eyes": "body",
              "bossF": "body", "bossR": "body", "jst2": "cells"}.get(grp, "drive")
    if "column" in nm:
        up = "base"
    dz = UP[up]
    m = box(lo, hi, dz)
    add(m, col, txt, (np.array(lo) + np.array(hi)) / 2 + [0, 0, dz + (np.array(hi) - np.array(lo))[2] / 2])
for sx in (1, -1):
    Lg = [L for L in c["L"] if L["side"] == ("R" if sx > 0 else "L")]
    ys = [L["P"][1] for L in Lg]
    x = np.mean([L["P"][0] for L in Lg])
    z = Lg[0]["P"][2] + 2.4 + P.F.WINDOW.side
    add(box([x - 3, min(ys) - 6, z], [x + 3, max(ys) + 3, z + 2.4], UP["keeper"]), "#d35400",
        "13 retén de los pasadores ×2 (2 × M3 + gancho bajo el labio del borde)" if sx > 0 else None,
        np.array([x, np.mean(ys), z + 2.4 + UP["keeper"]]))
fig, ax = plt.subplots(figsize=(13, 10))
proj = Fg.draw(ax, items, view=(22, -62))
Fg.side_labels(ax, [(proj(np.atleast_2d(p))[0], t) for p, t in notes])
ax.set_title(f"Spider-Bot N2, plan rev 4: vista despiezada (escala 0,65; cajas = piezas aún sin modelar; "
             f"holgura mínima {best['least']:+.2f} mm). Números = lista de piezas", fontsize=Fg.FONT + 1)
fig.savefig(sys.argv[1], dpi=110, bbox_inches="tight")
print("wrote", sys.argv[1])
