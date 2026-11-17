"""Four views of the N0 mock-up (3/4, front, side, from below-front), optionally next to a reference photo.
Called by n0.py --png; plain grey shapes, Spanish labels for Morante."""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

VIEWS = [(20, -125), (4, -90), (4, 180), (-25, -110)]
TXT = dict(es=dict(views=("3/4", "de frente", "de lado", "desde abajo, de frente"), photo="juguete (referencia)",
                   title="Maqueta N0 al {s:.0%} de jenscolt: rodilla {k:.0f} mm sobre la base, base a {c:.0f} mm del suelo (media de una vuelta; postura {p})"),
           en=dict(views=("3/4", "front", "side", "from below, front"), photo="toy (reference)",
                   title="N0 mock-up at {s:.0%} of jenscolt: knee {k:.0f} mm above the base, base {c:.0f} mm off the ground (mean over a turn; pose {p})"))
LIGHT = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
COL = {"cuerpo": (0.78, 0.78, 0.80), "base": (0.45, 0.45, 0.47), "pata": (0.35, 0.36, 0.40), "motor": (0.16, 0.44, 0.69),
       "pilas": (0.83, 0.63, 0.09), "engranajes": (0.5, 0.5, 0.5), "interruptor": (0.23, 0.6, 0.23)}


def shade(tris, base, alpha=1.0):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    k = 0.45 + 0.55 * np.abs(n @ LIGHT)
    return np.c_[np.clip(np.outer(k, base), 0, 1), np.full(len(k), alpha)]


def tube(pts, rad, seg=10):
    """Triangles of a tube along pts with radii rad (spheres swept, end caps left open: N0)."""
    t = np.gradient(pts, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    a = np.cross(t, [0, 0, 1.0])
    a[np.linalg.norm(a, axis=1) < 1e-6] = [1, 0, 0]
    a /= np.linalg.norm(a, axis=1, keepdims=True)
    b = np.cross(t, a)
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    ring = pts[:, None] + rad[:, None, None] * (np.cos(ang)[None, :, None] * a[:, None] + np.sin(ang)[None, :, None] * b[:, None])
    tris = []
    for i in range(len(pts) - 1):
        for j in range(seg):
            k = (j + 1) % seg
            tris += [[ring[i, j], ring[i + 1, j], ring[i + 1, k]], [ring[i, j], ring[i + 1, k], ring[i, k]]]
    return np.array(tris)


def box_tris(lo, hi):
    c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return np.array([[c[a], c[b], c[d]] for a, b, d, _ in q] + [[c[a], c[d], c[e]] for a, _, d, e in q])


def scene(p, B, L, rad, ni, bx, pose):
    ground = (L[:, pose, -1, 2] - rad[-1]).min()
    off = np.array([0, 0, -ground])
    items = [(V[F] + off, COL[k], 1.0) for k, (V, F) in (("cuerpo", B["body"]), ("base", B["base"]))]
    for leg in L[:, pose, ni - 1:]:
        items.append((tube(leg, rad[ni - 1:]) + off, COL["pata"], 1.0))
    for k, (lo, hi) in bx.items():
        c = COL.get(k.split(" ")[0], COL["engranajes"] if k.startswith("cig") else COL["motor"])
        items.append((box_tris(lo, hi) + off, c, 1.0))
    return items, -(L[:, :, -1, 2] - rad[-1]).min(0).mean()          # base height, mean over the crank turn


def render(png, p, B, L, rad, ni, bx, pose=0, photo=None, lang="es"):
    tx = TXT[lang]
    items, clear = scene(p, B, L, rad, ni, bx, pose)
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
    for k, ((el, az), name) in enumerate(zip(VIEWS, tx["views"])):
        ax = fig.add_subplot(1, ncol, k0 + k + 1, projection="3d")
        for tris, col, al in items:
            ax.add_collection3d(Poly3DCollection(tris, facecolors=shade(tris, col, al), edgecolors="none"))
        g = np.array([[c[0] - h, c[1] - h, 0], [c[0] + h, c[1] - h, 0], [c[0] + h, c[1] + h, 0], [c[0] - h, c[1] + h, 0]])
        ax.plot(*np.r_[g, g[:1]].T, color="0.6", lw=0.8)                  # the ground, as an outline
        ax.set_xlim(c[0] - h, c[0] + h); ax.set_ylim(c[1] - h, c[1] + h); ax.set_zlim(c[2] - h, c[2] + h)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(el, az)
        ax.set_proj_type("persp", focal_length=0.6)
        ax.axis("off")
        ax.set_title(name)
    fig.suptitle(tx["title"].format(s=p["S"], k=p["knee_z"], c=clear, p=pose), fontsize=11)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.01, wspace=0.0)
    fig.savefig(png, dpi=110)
    plt.close(fig)
