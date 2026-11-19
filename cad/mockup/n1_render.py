"""Four views of the N1 mock-up (3/4, front, side, from below-front), optionally next to a reference photo.
Called by n1.py --png; reuses n0_render's shading, views and colours."""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

import n0_render as r0  # noqa: E402
import n1  # noqa: E402

TXT = dict(es=dict(photo="juguete (referencia)", views=r0.TXT["es"]["views"],
                   title="Maqueta N1 al {s:.0%} de jenscolt: piezas reales simplificadas; base a {c:.0f} mm del suelo (media de una vuelta; postura {p})"),
           en=dict(photo="toy (reference)", views=r0.TXT["en"]["views"],
                   title="N1 mock-up at {s:.0%} of jenscolt: real parts, simplified; base {c:.0f} mm off the ground (mean over a turn; pose {p})"))
EYE = (0.93, 0.93, 0.90)


def cyl_tris(c, r, y0, y1, n=20):
    a = np.linspace(0, 2 * np.pi, n + 1)
    p0 = np.c_[c[0] + r * np.cos(a), np.full(n + 1, y0), c[1] + r * np.sin(a)]
    p1 = p0 + [0, y1 - y0, 0]
    t = []
    for i in range(n):
        t += [[p0[i], p1[i], p1[i + 1]], [p0[i], p1[i + 1], p0[i + 1]],
              [[c[0], y0, c[1]], p0[i + 1], p0[i]], [[c[0], y1, c[1]], p1[i], p1[i + 1]]]
    return np.array(t, float)


def scene(R, pose):
    st, legs, keep, bx = R["st"], R["legs"], R["keep"], R["bx"]
    posed = [n1.carry(l["loc"], l["g"])[pose] for l in legs]
    ground = min(W[:, 2].min() for W in posed)
    off = np.array([0, 0, -ground])
    items = [(st["body_v"][st["body_f"][keep["body"]]] + off, r0.COL["cuerpo"], 1.0),
             (st["base_v"][st["base_f"][keep["base"]]] + off, r0.COL["base"], 1.0),
             (st["eyes_v"][st["eyes_f"]] + off, EYE, 1.0)]
    for l, W in zip(legs, posed):
        items.append((W[l["F"]] + off, r0.COL["pata"], 1.0))
    for k, (lo, hi) in bx.items():
        c = r0.COL.get(k.split(" ")[0], r0.COL["engranajes"] if k.startswith("cig") else r0.COL["motor"])
        if k == "pilas":
            w, rr = (hi[0] - lo[0]) / 3, (hi[2] - lo[2]) / 2
            for j in range(3):
                items.append((cyl_tris((lo[0] + w * (j + .5), (lo[2] + hi[2]) / 2), rr, lo[1], hi[1]) + off, c, 1.0))
        else:
            items.append((r0.box_tris(lo, hi) + off, c, 1.0))
    allw = [n1.carry(l["samp"], l["g"]) for l in legs]
    clear = -np.mean([min(W[k, :, 2].min() for W in allw) for k in range(allw[0].shape[0])])
    return items, clear


def render(png, R, pose=0, photo=None, lang="es"):
    tx = TXT[lang]
    items, clear = scene(R, pose)
    allv = np.vstack([t.reshape(-1, 3) for t, _, _ in items])
    lo, hi = allv.min(0), allv.max(0)
    c, h = (lo + hi) / 2, (hi - lo).max() / 2 * 0.72
    ncol = 5 if photo else 4
    fig = plt.figure(figsize=(4.0 * ncol, 4.3))
    k0 = 0
    if photo:
        ax = fig.add_subplot(1, ncol, 1)
        ax.imshow(plt.imread(photo))
        ax.set_title(tx["photo"])
        ax.axis("off")
        k0 = 1
    for k, ((el, az), name) in enumerate(zip(r0.VIEWS, tx["views"])):
        ax = fig.add_subplot(1, ncol, k0 + k + 1, projection="3d")
        for tris, col, al in items:
            ax.add_collection3d(Poly3DCollection(tris, facecolors=r0.shade(tris, col, al), edgecolors="none"))
        g = np.array([[c[0] - h, c[1] - h, 0], [c[0] + h, c[1] - h, 0], [c[0] + h, c[1] + h, 0], [c[0] - h, c[1] + h, 0]])
        ax.plot(*np.r_[g, g[:1]].T, color="0.6", lw=0.8)
        ax.set_xlim(c[0] - h, c[0] + h); ax.set_ylim(c[1] - h, c[1] + h); ax.set_zlim(c[2] - h, c[2] + h)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(el, az)
        ax.set_proj_type("persp", focal_length=0.6)
        ax.axis("off")
        ax.set_title(name)
    fig.suptitle(tx["title"].format(s=R["p"]["S"], c=clear, p=pose), fontsize=11)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.0)
    fig.savefig(png, dpi=110)
    plt.close(fig)
