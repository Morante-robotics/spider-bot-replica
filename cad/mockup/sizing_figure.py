# Usage (from the repo root): python cad/mockup/sizing_figure.py <out.png>
import sys, time; t=time.time()
import os; HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util, numpy as np, trimesh, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from scipy.spatial import ConvexHull
spec = importlib.util.spec_from_file_location("n0", HERE + "/sizing.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
J = "cad/carcass-jenscolt/spideybot_"
full = m.P  # body + base, the frame the sizing uses (legs come at the next N0 step)
s = 0.55
boxes = m.solve(s, [m.PACKS["6×AG13 (3S2P, 4,5 V)"], m.MOTORS["Ø6 planetario"], m.SWITCH])
names = ["engranajes", "6 pilas AG13", "motor Ø6", "interruptor"]; cols = ["#777", "#d4a017", "#2a6fb0", "#3a3"]
fig, axs = plt.subplots(1, 2, figsize=(13, 5.2))
for ax, (i, j, title) in zip(axs, [(0, 2, "de lado"), (0, 1, "desde arriba")]):
    for sc, col, lab in [(1.2, "#bbb", "cuerpo anterior (120 %)"), (s, "#c0392b", f"cuerpo nuevo ({s:.0%})")]:
        q = full[:, [i, j]] * sc
        h = ConvexHull(q); ax.add_patch(Polygon(q[h.vertices], closed=True, fc=col, ec="none", alpha=0.35 if sc > 1 else 0.55, label=lab))
    off = -((m.V0[:, i].min() + m.V0[:, i].max()) / 2) * 0
    for (b0, b1), nm, c in zip(boxes, names, cols):
        ax.add_patch(Rectangle((b0[i], b0[j]), b1[i] - b0[i], b1[j] - b0[j], fc=c, ec="k", lw=0.6, label=nm))
    ax.add_patch(Rectangle((-50, 0 if j == 2 else -30), 100, 100 if j == 2 else 60, fill=False, ls="--", ec="k", lw=1.2, label="minirrobot ≈ 10 × 10 × 6 cm"))
    ax.set_aspect("equal"); ax.autoscale(); ax.set_title(title); ax.set_xlabel("mm")
axs[0].legend(loc="upper left", fontsize=8, frameon=False, bbox_to_anchor=(0, 1.0))
fig.suptitle(f"Maqueta N0: el robot más pequeño que aloja 6 pilas AG13, un motor Ø6 y los engranajes ({s:.0%}, ≈ {224*s:.0f} mm)")
fig.tight_layout(); fig.savefig(sys.argv[1], dpi=90)
print(f"{time.time()-t:.1f} s")
