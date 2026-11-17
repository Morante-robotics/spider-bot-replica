"""House style for the capstones' diagrams: one look for every figure, made from the CAD meshes.

Every diagram (assembly steps, exploded views, measurement drawings) is drawn with these functions, so they all look
alike: the same colour for the same kind of part in every figure, parts already in place in light grey, the part
that moves in colour with an arrow, black outlines where faces meet (like a hand-drawn assembly sheet), large labels.

Why not matplotlib's 3D axes: they sort each part as one block, so a part behind another is often drawn on top of it
(the «diagram looks wrong» of the gear train test, 2026-11-12). Here every triangle of every part is projected and
sorted by depth together, back faces are dropped, and outlines are drawn only where the camera can see them.

    from figures import assembly_steps, exploded, measure_sheet
    assembly_steps(spec, meshes, "images/assembly-steps.png", lang="es")

Functions:
    draw(ax, items, view)          the renderer: items = [{"mesh": trimesh, "color": c, "alpha": 1}]
    assembly_steps(spec, meshes, out, lang)   one panel per ASSEMBLY step on one sheet, numbered, words for direction
    step_pictures(spec, meshes, outdir, lang) the same, one large picture per step (for the phone)
    exploded(spec, meshes, out, lang)         every part pulled out along its way in, numbered and named
    measure_sheet(spec, meshes, out, lang)    one panel per MEASURE entry: section, dimension line, nominal ± tol
Spec fields used besides cad_verify's: LABELS = {"es": {"idler1": "engranaje loco 1"}, "en": {...}},
VIEW = (elev, azim), STEP_VIEW = {"part": (elev, azim)}, MEASURE = [{"what": "tongue width", "point": p, "normal": n,
"from": p1, "to": p2, "nominal": 2.0, "tol": 0.1, "tool": "caliper"}], PARTS[...]["label"] = "M3×12 socket head".
"""
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

PALETTE = ["#c0392b", "#2e86c1", "#e2b007", "#27ae60", "#8e44ad", "#e67e22", "#16a085", "#d35400", "#7f8c8d"]
PLACED = "#d5d5d5"       # parts already in place
HARDWARE = "#4d4d4d"     # screws, pins, nuts
TOOL = (0.85, 0.1, 0.1, 0.25)
FONT = 12                # labels; titles FONT + 2
plt.rcParams.update({"font.size": FONT, "font.family": "DejaVu Sans"})

WORDS = {
    "en": {"in": "in from", "+Z": "above", "-Z": "below", "+X": "the +X side", "-X": "the −X side",
           "+Y": "the +Y side", "-Y": "the −Y side", "first": "start with", "step": "Step",
           "bench": "on the bench"},
    "es": {"in": "entra desde", "+Z": "arriba", "-Z": "abajo", "+X": "el lado +X", "-X": "el lado −X",
           "+Y": "el lado +Y", "-Y": "el lado −Y", "first": "base de partida", "step": "Paso",
           "bench": "en la mesa"},
}


# ---------------------------------------------------------------- names and colours

def kind(name):
    """'crankshaft3' -> 'crankshaft', 'leg-front-left' -> 'leg': parts of one kind share a colour."""
    return re.sub(r"[-_ ]?\d+$", "", name).split("-")[0]


def label(spec, name, lang):
    return getattr(spec, "LABELS", {}).get(lang, {}).get(name, name)


def colours(spec):
    kinds, out = [], {}
    for n, p in spec.PARTS.items():
        if p.get("hardware"):
            out[n] = HARDWARE
            continue
        k = kind(n)
        if k not in kinds:
            kinds.append(k)
        out[n] = PALETTE[kinds.index(k) % len(PALETTE)]
    return out


def direction_words(d, lang):
    d = np.asarray(d, float)
    i = int(np.argmax(np.abs(d)))
    key = ("+" if d[i] > 0 else "-") + "XYZ"[i]
    w = WORDS[lang]
    return f"{w['in']} {w[key]}"


BENCH_WORDS = {
    "en": {"up": "up", "down": "down", "toward": "towards you", "away": "away from you", "left": "to the left",
           "right": "to the right"},
    "es": {"up": "hacia arriba", "down": "hacia abajo", "toward": "hacia ti", "away": "hacia el fondo",
           "left": "hacia la izquierda", "right": "hacia la derecha"},
}
_OPP = {"up": "down", "down": "up", "toward": "away", "away": "toward", "left": "right", "right": "left"}


def bench_words(d, spec, lang):
    """A bench step's move as seen on the bench, or None (no pose given: use direction_words).
    spec.BENCH_POSE (optional) says where each model axis points on the bench: {"+X": "up", "+Z": "toward", ...} with
    up / down / toward (you) / away / left / right; the opposite axis is derived. A part that comes in from d moves
    along -d, so «in from +X» with +X up reads «hacia abajo»."""
    pose = dict(getattr(spec, "BENCH_POSE", None) or {})
    for k, v in list(pose.items()):
        pose.setdefault(("-" if k[0] == "+" else "+") + k[1:], _OPP[v])
    d = np.asarray(d, float)
    i = int(np.argmax(np.abs(d)))
    move = ("-" if d[i] > 0 else "+") + "XYZ"[i]      # the part moves opposite to the side it comes from
    return BENCH_WORDS[lang][pose[move]] if move in pose else None


def step_words(st, spec, lang):
    """How a step reads in its title and in the kit: first step, a path, or a direction (bench steps as on the bench)."""
    d = st["d"]
    if d is None:
        return WORDS[lang]["first"]
    if st.get("path"):
        how = path_words(st["path"], lang)
    else:
        how = (bench_words(d, spec, lang) if st["bench"] is not None else None) or direction_words(d, lang)
    return f"{WORDS[lang]['bench']}: {how}" if st["bench"] is not None else how


def path_words(path, lang):
    """The moves of an ASSEMBLY path in order: «down 30 mm, then +Y 4 mm»."""
    from cad_verify import move_words
    return (", then " if lang == "en" else ", luego ").join(move_words(m) for m in path)


# ---------------------------------------------------------------- the renderer

def simplify(mesh, cell=0.2):
    """Lighter mesh for drawing only (vertex clustering on a grid of `cell` mm); never for checks."""
    if len(mesh.faces) < 20000:
        return mesh
    v = np.round(mesh.vertices / cell) * cell
    m = trimesh.Trimesh(v, mesh.faces, process=True)
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    return m


def camera(elev, azim):
    e, a = np.radians(elev), np.radians(azim)
    toward = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])   # from the scene to the eye
    right = np.array([-np.sin(a), np.cos(a), 0.0])
    up = np.cross(toward, right)
    return np.vstack([right, up, toward])


def draw(ax, items, view=(25, -60), edge_angle=30.0, light=(0.3, 0.4, 1.0)):
    """Draw meshes with correct depth order and visible outlines. Returns proj(points) -> 2D for annotations."""
    R = camera(*view)
    toward = R[2]
    L = np.asarray(light, float) @ R
    L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for it in items:
        m = it["mesh"]
        alpha = it.get("alpha", 1.0)
        n = m.face_normals
        front = n @ toward > 0
        tri = m.triangles[front]
        p = tri @ R.T
        shade = 0.55 + 0.45 * np.clip((n[front] @ R.T) @ L, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(it["color"]))
        c = np.clip(rgb[None, :] * shade[:, None] + (1 - shade[:, None]) * 0.15, 0, 1)
        polys.append(p[:, :, :2])
        cols.append(np.hstack([c, np.full((len(c), 1), alpha)]))
        depth.append(p[:, :, 2].mean(axis=1))
    # outlines (sharp edges and silhouettes) go into the same depth sort as the faces, a little nearer the eye than
    # the faces they border: faces in front of an edge cover it, so hidden edges vanish without any ray casting
    segs, sdepth = [], []
    for it in items:
        if not it.get("edges", True):
            continue
        m = it["mesh"]
        fa, ea = m.face_adjacency, m.face_adjacency_edges
        f = m.face_normals[fa] @ toward
        keep = (m.face_adjacency_angles > np.radians(edge_angle)) & ((f[:, 0] > 0) | (f[:, 1] > 0))
        keep |= (f[:, 0] > 0) != (f[:, 1] > 0)
        e = m.vertices[ea[keep]] @ R.T
        segs.append(e[:, :, :2])
        sdepth.append(e[:, :, 2].max(axis=1) + 0.3)
    P, C, D = np.concatenate(polys), np.concatenate(cols), np.concatenate(depth)
    n_face = len(P)
    allp = P.reshape(-1, 2)
    shapes = list(P)
    ec, fc, lw = list(C), list(C), [0.25] * n_face
    if segs:
        S = np.concatenate(segs)
        shapes += list(S)
        D = np.concatenate([D, np.concatenate(sdepth)])
        ec += [(0.1, 0.1, 0.1, 1.0)] * len(S)
        fc += [(0, 0, 0, 0)] * len(S)
        lw += [0.7] * len(S)
    order = np.argsort(D, kind="stable")
    ax.add_collection(PolyCollection([shapes[i] for i in order], facecolors=np.array(fc)[order],
                                     edgecolors=np.array(ec)[order], linewidths=np.array(lw)[order], closed=False))
    lo, hi = allp.min(axis=0), allp.max(axis=0)
    pad = 0.06 * (hi - lo).max()
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_aspect("equal")
    ax.set_axis_off()
    return lambda pts: (np.atleast_2d(pts) @ R.T)[:, :2]


def callout(ax, proj, p3, text, dx=30, dy=30, color="#1a1a1a"):
    xy = proj(p3)[0]
    ax.annotate(text, xy=xy, xytext=(dx, dy), textcoords="offset points", fontsize=FONT, color=color,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.8),
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8))


def side_labels(ax, points, color="#1a1a1a"):
    """Labels in two tidy columns left and right of the drawing, each with a leader line to its point, never on top
    of each other: points = [(xy, text)] in the drawing's 2D coordinates."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    w = x1 - x0
    cx = np.median([p[0] for p, _ in points])
    for side, sel in ((-1, [q for q in points if q[0][0] < cx]), (1, [q for q in points if q[0][0] >= cx])):
        sel = sorted(sel, key=lambda q: -q[0][1])
        if not sel:
            continue
        ys = np.linspace(y1, y0, len(sel) + 2)[1:-1]
        xt = x0 - 0.08 * w if side < 0 else x1 + 0.08 * w
        for (p, text), y in zip(sel, ys):
            ax.annotate(text, xy=p, xytext=(xt, y), textcoords="data", fontsize=FONT, color=color,
                        ha="right" if side < 0 else "left", va="center",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.8),
                        arrowprops=dict(arrowstyle="-", color=color, lw=0.7, shrinkA=0, shrinkB=2))
            ax.plot(*p, "o", color=color, ms=3)


def move_arrow(ax, proj, p_from, p_to, color):
    a, b = proj(p_from)[0], proj(p_to)[0]
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5, mutation_scale=22))


def badge(ax, n):
    ax.text(0.02, 0.98, str(n), transform=ax.transAxes, fontsize=FONT + 8, fontweight="bold", va="top",
            ha="left", color="white", bbox=dict(boxstyle="circle,pad=0.3", fc="#1a1a1a"))


# ---------------------------------------------------------------- figures from a cad_verify spec

def _placed(spec, meshes, bench=True):
    from cad_verify import placed
    motion = list(getattr(spec, "MOTION", [0]))
    out = {}
    for n, m in placed(spec, meshes, motion[0], bench=bench).items():
        mm = m.to_mesh()
        out[n] = simplify(trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=True))
    return out


def _context(spec, meshes):
    from cad_verify import access_step, steps
    tri, col = _placed(spec, meshes), colours(spec)
    seq = steps(spec)
    tools = {}
    for a in getattr(spec, "ACCESS", []):
        k = access_step(seq, a["at"])
        if k is not None:
            tools.setdefault(k, []).append(a["tool"])
    lo = np.min([t.bounds[0] for t in tri.values()], axis=0)
    hi = np.max([t.bounds[1] for t in tri.values()], axis=0)
    return dict(tri=tri, col=col, tools=tools, seq=seq, lift=max(15.0, 0.25 * float((hi - lo).max())))


def _step_panel(ax, spec, ctx, k, lang, number=True):
    """Step k: on the bench, only its bench parts (grey) and the moving body; in the machine, every part placed by
    the machine steps before it. A tuple of parts moves as one body, each in its colour, one arrow."""
    from cad_verify import before_step
    seq = ctx["seq"]
    st = seq[k]
    names, d = st["names"], st["d"]
    tri, col = ctx["tri"], ctx["col"]
    views = getattr(spec, "STEP_VIEW", {})
    view = views.get(names if len(names) > 1 else names[0],
                     next((views[n] for n in names if n in views), getattr(spec, "VIEW", (25, -60))))
    there = before_step(spec, seq, k)
    items = [{"mesh": tri[p], "color": PLACED} for p in there]
    lift = ctx["lift"]
    if st["bench"] is not None:          # a small sub-assembly: lift it by its own size
        b = [tri[p].bounds for p in list(there) + list(names)]
        lift = max(8.0, 0.6 * float((np.max([x[1] for x in b], axis=0) - np.min([x[0] for x in b], axis=0)).max()))
    moving = []
    for n in names:
        m = tri[n].copy()
        if d is not None:
            m.apply_translation(d * lift)
        moving.append(m)
        items.append({"mesh": m, "color": col[n]})
    for tm in ctx["tools"].get(k, []):
        items.append({"mesh": tm, "color": TOOL[:3], "alpha": TOOL[3], "edges": False})
    proj = draw(ax, items, view)
    if d is not None:
        c0 = np.mean([m.bounds.mean(axis=0) for m in moving], axis=0)
        move_arrow(ax, proj, c0, c0 - d * lift * 0.8, col[names[0]])   # a path: only its last move is drawn
    if number:
        badge(ax, k + 1)
    how = step_words(st, spec, lang)
    ax.set_title(f"{' + '.join(label(spec, n, lang) for n in names)}\n{how}", fontsize=FONT + 2, pad=4)


def assembly_steps(spec, meshes, out, lang="en", cols=3, panel=5.0):
    """One panel per ASSEMBLY step: what is already in place (grey), the part going in (colour, lifted out along its
    direction, arrow), the finger or tool that reaches it (red), and a title in words."""
    from cad_verify import steps
    seq = steps(spec)
    if not seq:
        return None
    ctx = _context(spec, meshes)
    rows = -(-len(seq) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(panel * cols, panel * rows), squeeze=False)
    for k in range(len(seq)):
        _step_panel(axes[k // cols][k % cols], spec, ctx, k, lang)
    for k in range(len(seq), rows * cols):
        axes[k // cols][k % cols].set_axis_off()
    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor="white")
    plt.close(fig)
    return out


def step_pictures(spec, meshes, outdir, lang="es", size=6.5, prefix="paso"):
    """One large picture per ASSEMBLY step (for a phone): <outdir>/<prefix>-01.png, ..."""
    from cad_verify import steps
    seq = steps(spec)
    if not seq:
        return []
    ctx, paths = _context(spec, meshes), []
    for k in range(len(seq)):
        fig, ax = plt.subplots(figsize=(size, size))
        _step_panel(ax, spec, ctx, k, lang)
        fig.tight_layout()
        p = os.path.join(outdir, f"{prefix}-{k + 1:02d}.png")
        fig.savefig(p, dpi=110, facecolor="white")
        plt.close(fig)
        paths.append(p)
    return paths


def _letters(j):
    """a, b, ... z, then aa, ab ...: a sub-assembly's member letters (the chassis module group has 23 members)."""
    s = ""
    j += 1
    while j:
        j, r = divmod(j - 1, 26)
        s = chr(97 + r) + s
    return s


def exploded_steps(seq):
    """The machine steps of steps(spec) for the exploded view: [(k, names, d, numbers)], k counting the machine steps
    from 0 (the pull-out distance), numbers the step numbers as in assembly-steps.png (bench steps keep theirs, so
    the numbers skip them), a sub-assembly's members as 22a, 22b..."""
    out = []
    for i, st in enumerate(seq):
        if st["bench"] is not None:
            continue
        names = st["names"]
        nums = [f"{i + 1}" if len(names) == 1 else f"{i + 1}{_letters(j)}" for j in range(len(names))]
        out.append((len(out), names, st["d"], nums))
    return out


def exploded(spec, meshes, out, lang="en", view=None, size=(11, 8)):
    """Every part pulled out along the direction it goes in, by its step number, each named with a callout. Bench
    steps are left out (their jigs are not in the machine) but keep their numbers; a sub-assembly moves as one body,
    its members numbered 22a, 22b..."""
    from cad_verify import steps
    seq = exploded_steps(steps(spec))
    tri, col = _placed(spec, meshes, bench=False), colours(spec)
    lo = np.min([t.bounds[0] for t in tri.values()], axis=0)
    hi = np.max([t.bounds[1] for t in tri.values()], axis=0)
    gap = 0.12 * float((hi - lo).max())
    items, anchors = [], []
    for k, names, d, nums in seq:
        for n, num in zip(names, nums):
            m = tri[n].copy()
            if d is not None:
                m.apply_translation(d * gap * (1 + 0.15 * k))
            items.append({"mesh": m, "color": col[n]})
            anchors.append((num, n, m.bounds.mean(axis=0)))
    fig, ax = plt.subplots(figsize=size)
    proj = draw(ax, items, view or getattr(spec, "VIEW", (25, -60)))
    side_labels(ax, [(proj(p)[0], f"{num}  {label(spec, n, lang)}") for num, n, p in anchors])
    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor="white")
    plt.close(fig)
    return out


def measure_sheet(spec, meshes, out, lang="en", cols=2):
    """One panel per MEASURE entry: the section through the part, a red dimension line, nominal ± tolerance."""
    items = getattr(spec, "MEASURE", [])
    if not items:
        return None
    tri, col = _placed(spec, meshes), colours(spec)
    cols = min(cols, len(items))
    rows = -(-len(items) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(6.5 * cols, 6.5 * rows), squeeze=False)
    txt = {"en": ("expected", "with the"), "es": ("debe dar", "con el")}[lang]
    tools = {"en": {}, "es": {"caliper": "calibre", "ruler": "regla"}}[lang]
    for k, mz in enumerate(items):
        ax = axes[k // cols][k % cols]
        o, nrm = np.asarray(mz["point"], float), np.asarray(mz["normal"], float)
        nrm /= np.linalg.norm(nrm)
        to2d = trimesh.geometry.plane_transform(origin=o, normal=nrm)
        for n, t in tri.items():
            s = t.section(plane_origin=o, plane_normal=nrm)
            if s is None:
                continue
            p2, _ = s.to_2D(to_2D=to2d)
            for poly in p2.polygons_full:
                ax.fill(*poly.exterior.xy, color=col[n], alpha=0.85, ec="#1a1a1a", lw=0.6)
                for h in poly.interiors:
                    ax.fill(*h.xy, color="white", ec="#1a1a1a", lw=0.6)
        a, b = (trimesh.transform_points([np.asarray(mz[q], float)], to2d)[0][:2] for q in ("from", "to"))
        # zoom on the measured feature, with enough around it to recognise where it is
        mid, span = (a + b) / 2, float(np.linalg.norm(b - a))
        half = max(3.0 * span, 10.0)
        ax.set_xlim(mid[0] - half, mid[0] + half)
        ax.set_ylim(mid[1] - half, mid[1] + half)
        # dimension line drawn beside the feature (extension lines), value written past its end
        u = (b - a) / max(span, 1e-9)
        nrm2 = np.array([-u[1], u[0]])
        off = nrm2 * 0.35 * half
        ax.plot(*np.array([a, a + off * 1.1]).T, color="#c0392b", lw=0.8)
        ax.plot(*np.array([b, b + off * 1.1]).T, color="#c0392b", lw=0.8)
        ax.annotate("", xy=b + off, xytext=a + off,
                    arrowprops=dict(arrowstyle="<|-|>", color="#c0392b", lw=2, mutation_scale=18, shrinkA=0, shrinkB=0))
        tool = tools.get(mz.get("tool", "caliper"), mz.get("tool", "caliper"))
        ax.annotate(f"{mz['nominal']:g} ± {mz.get('tol', 0.1):g} mm", xy=mid + off, xytext=mid + off * 1.6,
                    color="#c0392b", fontsize=FONT + 4, fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c0392b", lw=1))
        ax.set_title(f"{k + 1}. {mz.get('what_' + lang, mz['what'])}\n{txt[0]} {mz['nominal']:g} mm, {txt[1]} {tool}",
                     fontsize=FONT + 1)
        ax.set_aspect("equal")
        ax.set_axis_off()
    for k in range(len(items), rows * cols):
        axes[k // cols][k % cols].set_axis_off()
    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    import argparse
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cad_verify import load_spec
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("outdir")
    ap.add_argument("--lang", default="en", choices=sorted(WORDS))
    args = ap.parse_args()
    spec = load_spec(args.spec)
    base = os.path.dirname(os.path.abspath(args.spec))
    meshes = {n: p["mesh"] if "mesh" in p else trimesh.load(os.path.join(base, p["stl"]), force="mesh")
              for n, p in spec.PARTS.items()}
    os.makedirs(args.outdir, exist_ok=True)
    sfx = "" if args.lang == "en" else f"-{args.lang}"
    for f in (assembly_steps(spec, meshes, os.path.join(args.outdir, f"assembly-steps{sfx}.png"), args.lang),
              exploded(spec, meshes, os.path.join(args.outdir, f"exploded{sfx}.png"), args.lang),
              measure_sheet(spec, meshes, os.path.join(args.outdir, f"measure{sfx}.png"), args.lang)):
        if f:
            print(f)
