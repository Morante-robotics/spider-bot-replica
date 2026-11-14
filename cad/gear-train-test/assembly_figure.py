"""Assembly diagram of the gear train test v2 (print/gear-train-test-v2.3mf), from the same parts and poses as
verify.py:

  left   exploded view: every part pulled out along the direction it goes in, numbered by assembly step
  right  seen from +X (the side with the dots) at crank angle 0: every crank level, the dots per shaft, front/rear

    python3 assembly_figure.py            # images/gear-train-test-v2-assembly.png (English)
    python3 assembly_figure.py --lang es  # images/gear-train-test-v2-assembly-es.png (Spanish)
"""
import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify as V  # noqa: E402  (this design's cad_verify spec)

TXT = {
    "en": dict(spine="spine", cap="cap", cs="crankshaft {i}", idler="idler {k} ({n} T)", idlers="idlers (12 T front, 20 T rear)", axle="M3×12 + nut",
               capscrew="M3×12", nut="M3 nut in the slot",
               t1="Exploded view: numbers are the assembly steps", t2="Seen from +X (the side with the dots), crank angle 0°",
               level="every crank level; arrows: the +X crank of each shaft", front="front", rear="rear", dots="{i} dot{s}", plusx="+X: dots, screw heads",
               minusx="−X: axle nuts"),
    "es": dict(spine="espina", cap="tapa", cs="cigüeñal {i}", idler="engranaje loco {k} ({n} dientes)",
               idlers="engranajes locos (12 dientes delante, 20 detrás)",
               axle="M3×12 + tuerca", capscrew="M3×12", nut="tuerca M3 en la ranura",
               t1="Vista despiezada: los números son los pasos de montaje",
               t2="Vista desde +X (el lado de los puntos), manivelas a 0°",
               level="todas las manivelas horizontales; flechas: la manivela del lado +X", front="delante", rear="detrás", dots="{i} punto{s}",
               plusx="+X: puntos, cabezas de tornillo", minusx="−X: tuercas de los ejes"),
}
COL = {"spine": "#b8b8b8", "cap": "#8fb3d9", "crankshaft": "#c0392b", "idler": "#f1c40f", "hw": "#555555"}


def tri(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)


def placed():
    from cad_verify import placed as P, to_manifold  # noqa: F401
    meshes = {}
    for n, p in V.PARTS.items():
        meshes[n] = p["mesh"] if "mesh" in p else trimesh.load(os.path.join(HERE, p["stl"]), force="mesh")
    return {n: tri(m) for n, m in P(V, meshes, V.MOTION[0]).items()}


def kind(n):
    for k in ("crankshaft", "idler", "spine", "cap"):
        if n.startswith(k) and not n.startswith("capscrew"):
            return k
    return "hw"


def shade(t, color):
    light = np.array([0.4, -0.5, 0.75])
    light /= np.linalg.norm(light)
    f = 0.45 + 0.55 * np.clip(t.face_normals @ light, 0, 1)
    c = np.array(matplotlib.colors.to_rgb(color))
    return np.clip(np.outer(f, c), 0, 1)


def main():
    from matplotlib.collections import PolyCollection
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=TXT)
    lang = ap.parse_args().lang
    T = TXT[lang]
    ms = placed()
    # exploded offsets: along the direction each part goes in (ASSEMBLY), so the picture reads as the steps
    off = {"cap": [0, 0, 92], **{f"capscrew{j + 1}": [0, 0, 116] for j in range(2)}}
    for k in range(3):
        off[f"idler{k + 1}"] = [0, 0, 24]
        off[f"axle{k + 1}"] = [26, 0, 0]
        off[f"axlenut{k + 1}"] = [-20, 0, 0]
    for i in range(4):
        off[f"crankshaft{i + 1}"] = [0, 0, 56]

    fig = plt.figure(figsize=(18, 9))
    ax = fig.add_subplot(1, 2, 1)
    # own orthographic projection with a global painter's sort (matplotlib's 3D axes sort per collection and draw
    # parts through each other)
    az, el = np.radians(28), np.radians(24)
    view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])   # towards the viewer
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    P = np.vstack([right, up])
    polys, cols, depth, labels = [], [], [], []
    sb = ms["spine"].bounds
    proj = lambda p: P @ np.asarray(p, float)
    for n, t in ms.items():
        t = t.copy()
        t.apply_translation(off.get(n, [0, 0, 0]))
        front = t.face_normals @ view > 0
        tr = t.triangles[front]
        polys.append(tr @ P.T)
        cols.append(shade(t, COL[kind(n)])[front])
        depth.append(tr.mean(axis=1) @ view)
        c = t.bounds.mean(axis=0)
        if n in ("crankshaft1", "crankshaft4"):
            labels.append((c, f"4 · {T['cs'].format(i=int(n[-1]))}", (-70 if n[-1] == "1" else 60, 25)))
        elif n == "idler1":
            labels.append((c, f"2 · {T['idlers']}", (-110, 10)))
        elif n == "axle1":
            labels.append((c, f"3 · {T['axle']}", (70, -20)))
        elif n == "cap":
            labels.append((c, f"6 · {T['cap']}", (-80, 30)))
        elif n == "capscrew2":
            labels.append((c, f"6 · {T['capscrew']}", (50, 10)))
        elif n == "spine":
            labels.append(([c[0], sb[0][1] + 3, sb[0][2] + 6], f"1 · {T['nut']}", (-70, -40)))
            labels.append(([c[0], sb[1][1] - 3, sb[0][2] + 6], f"1 · {T['nut']}", (60, -40)))
            labels.append(([sb[1][0], c[1], sb[0][2]], T["spine"], (40, -60)))
    polys, cols, depth = np.concatenate(polys), np.concatenate(cols), np.concatenate(depth)
    o = np.argsort(depth)
    ax.add_collection(PolyCollection(polys[o], facecolors=cols[o], edgecolors=cols[o], linewidths=0.2))
    lo2, hi2 = polys.reshape(-1, 2).min(axis=0), polys.reshape(-1, 2).max(axis=0)
    ax.set_xlim(lo2[0] - 25, hi2[0] + 25), ax.set_ylim(lo2[1] - 15, hi2[1] + 10)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(T["t1"], fontsize=13)
    for p, s_, d in labels:
        ax.annotate(s_, tuple(proj(p)), xytext=d, textcoords="offset points", fontsize=9, ha="center", zorder=20,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.6"),
                    arrowprops=dict(arrowstyle="-", color="0.3", lw=0.8))

    # right: seen from +X (looking towards -X, Z up): -Y runs to the right. Crank angle 0
    bx = fig.add_subplot(1, 2, 2)
    order = ["spine", "idler1", "idler2", "idler3", "crankshaft1", "crankshaft2", "crankshaft3", "crankshaft4"]
    for n in order:
        t = ms[n]
        f = t.triangles[:, :, 1:] * [-1, 1]
        vis = t.face_normals[:, 0] > 0 if n == "spine" else np.ones(len(f), bool)
        bx.add_collection(PolyCollection(f[vis], facecolors=COL[kind(n)], edgecolors="none",
                                         alpha=0.35 if n == "spine" else 1.0))
    rr = V.C.P_["r"]
    for i, (y, z) in enumerate(V.SH):
        u = -y
        ph = V.C.shaft_phases(i)[0]                 # the +X (right) crank
        du, dz = rr * np.cos(ph), rr * np.sin(ph)  # pin offset (-Y is +u)
        bx.annotate("", (u + 2.6 * du, z + 2.6 * dz), (u, z),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=2.2, mutation_scale=14))
        bx.plot(u, z, "o", color="black", ms=4)
        bx.annotate(f"{T['cs'].format(i=i + 1)}\n{T['dots'].format(i=i + 1, s='' if i == 0 else 's')}",
                    (u, z + 7), (u, z + 19), ha="center", fontsize=9.5, arrowprops=dict(arrowstyle="-", color="0.5"))
    for k, (y, z, n) in enumerate(V.IDL):
        bx.annotate(T["idler"].format(k=k + 1, n=n), (-y, z - 4), (-y, z - 18 - 7 * (k % 2)), ha="center",
                    fontsize=9, arrowprops=dict(arrowstyle="-", color="0.5"))
    umin, umax = -sb[1][1], -sb[0][1]
    zb = sb[0][2]
    bx.annotate("", (umax + 2, zb - 22), (umax - 22, zb - 22), arrowprops=dict(arrowstyle="->", lw=1.5))
    bx.text(umax - 24, zb - 22, T["front"], ha="right", va="center", fontsize=11)
    bx.text((umin + umax) / 2, V.SH[0][1] + 31, T["level"], ha="center", fontsize=11, style="italic")
    bx.text(umin, zb - 12, f"{T['plusx']}\n{T['minusx']}", ha="left", va="center", fontsize=9, color="0.3")
    bx.set_xlim(umin - 6, umax + 6)
    bx.set_ylim(zb - 28, V.SH[0][1] + 36)
    bx.set_aspect("equal")
    bx.set_axis_off()
    bx.set_title(T["t2"], fontsize=13)
    out = os.path.join(HERE, "images", "gear-train-test-v2-assembly" + ("" if lang == "en" else f"-{lang}") + ".png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
