#!/usr/bin/env python3
"""Part E (the looks pass) plan figure, rev 2: a 4-view mock-up of the proposed looks robot, once per leg-shell option.

Rows: «thin» shells (rev 1, fixed per review objection 6) and «thick» shells (curved tall hoods on the arms, bulged
outer plates on the front and rear shins, middle shins as a narrow bulged plate). Columns: 3/4 front, front, side,
below-front (the 4 standard views of the pass). Left column: the reference photo when --photo is given (the photo is
private: the copies in images/ are rendered without it), and the design mass range per option.

Geometry (mock-up, not the model): chassis, crank cover, forks, legs and front block v2 from the built STLs (black);
the body is robot.carcass_proxy("body") cut by the dome plane (red below, blue above); the F1 face wall as two 1.2
plates over the front block's opening; the base skin as 2 mm slabs of the chassis hull's outer 1.2 mm, minus the front
block and body (+WINDOW) and the forks and legs swept at 30° steps (+LEG_PATH): a coarse copy of probe q2 (1 mm, 10°);
the leg shells from leg_shells() below (the same function the plan's sweep probe q3 uses).

    ../../.venv/bin/python plan_e_figure.py                       # images/plan-e.png
    ../../.venv/bin/python plan_e_figure.py --lang es             # images/plan-e-es.png
    ../../.venv/bin/python plan_e_figure.py --lang es --photo P --out X.png   # private copy beside the photo
    ../../.venv/bin/python plan_e_figure.py --lite                # one view per row, for trying a change
"""
import argparse
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import MultiPoint, MultiPolygon, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)
import figures as F  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from cad import design, fits, robot as R  # noqa: E402

L = design("legs")
COL = dict(black="#2b2b2b", red="#c0392b", blue="#2350b0", mark="#e67e22", grey="#9a9a9a")
# dome plane (design-plan-e.md rev 2, probe q1: body-v2 and dome each one piece): through (y -60, z 145), (y 65, z 135)
DOME = ((-60.0, 145.0), (65.0, 135.0))
# design mass ranges per leg option (design-plan-e.md rev 2 «Mass»), g
MASS = {"thin": (474.8, 483.4), "thick": (484.7, 494.3)}
VIEWS = [(22, -125), (3, -90), (3, 0), (-25, -110)]
WORDS = {
    "en": dict(title="Part E · the looks pass, rev 2: mock-up in the 4 standard views",
               views=["3/4 front", "front", "side", "below-front"], thin="«thin» leg shells", thick="«thick» leg shells",
               photo="reference photo\n(private: not in the repo)", mass="design mass (g), low – high",
               ceiling="ceiling 478 g", dome="blue dome", skin="black skin on the base", f1="face closed (F1)",
               shell="red leg shell"),
    "es": dict(title="Parte E · pasada de aspecto, rev 2: maqueta en las 4 vistas",
               views=["3/4 frontal", "frente", "lado", "desde abajo y delante"], thin="fundas de pata «finas»",
               thick="fundas de pata «gruesas»", photo="foto de referencia\n(privada: no va al repositorio)",
               mass="masa de diseño (g), mín – máx", ceiling="techo 478 g", dome="cúpula azul",
               skin="piel negra en la base", f1="frente cerrado (F1)", shell="funda roja de pata"),
}

# ---- leg shells (leg frame: legs/build.py leg(); arm along +x, y across, z up; shin frame SH: x along, z outward) ----
FIT, LP = fits.TURN.side, fits.LEG_PATH.side
TS, TT, TW = 0.8, 1.2, 1.2      # side skirt (nothing pushes), top / outer plate, hood wall
X0 = {"front": 16.0, "mid1": 16.0, "mid2": 16.0, "rear": 20.0}   # arm shell start (probe p2b: free from here)
FACING_END = 40.0               # middle arms: the facing skirt ends here (p2b: 44; q3: 0.4-0.8 left at 44)
FRONT_SKIRT_T = 5.0             # front shin: no +Y skirt (p2b: to 24; q3: meets the middle shin plate at 350°)
HOOD = {"thin": 0.0, "thick": 9.0}       # arch height over the arm top (thick: the photo's tall curved segment)
HOOD_ROOT = 4.0                 # thick hood over the first 8 mm (p1: 5-10 mm free at x 10-20)
BULGE = {"thin": 0.0, "thick": 4.0}      # outer bulge on the front and rear shins
BULGE_T0 = 12.0                 # bulge starts here on the shin (q3: from 5 it meets the middle arm's hood at 350°)
MID_BULGE = {"thin": 0.0, "thick": 1.5}  # middle shins: narrow plate (SHIN_W - 2 LEG_PATH), solid bulge (q3: 2.5 meets the front shin)
KIND = {"leg0": "front", "leg1": "mid1", "leg2": "mid2", "leg3": "rear"}


def _arch(w, h, z0, n=24):
    t = np.linspace(0, np.pi, n)
    return Polygon(np.column_stack([w / 2 * np.cos(t), z0 + h * np.sin(t)]))


def _extrude(poly, x0, x1, M=np.eye(4), grow=0.0):
    poly = poly.buffer(grow, join_style=2) if grow else poly
    out = []
    for p in getattr(poly, "geoms", [poly]):
        if p.area < 1e-3:
            continue
        m = trimesh.creation.extrude_polygon(p, (x1 - x0) + 2 * grow)
        T = np.array([[0, 0, 1, x0 - grow], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)   # (u,v,w) -> (x=w, y=u, z=v)
        m.apply_transform(T)
        m.apply_transform(M)
        out.append(m)
    return out


def shin_frame():
    P = L.P_
    b, s = np.radians(P["bend"]), np.radians(P["sweep"])
    d = np.array([np.cos(b), -np.sin(b) * np.sin(s), -np.sin(b) * np.cos(s)])
    n = np.cross(d, [0, 1, 0])
    n = n if n[0] > 0 else -n
    SH = np.eye(4)
    SH[:3, 0], SH[:3, 1], SH[:3, 2], SH[:3, 3] = d, np.cross(n, d), n, [P["L1"], L.SHIN_DY, 0]
    return SH


def leg_shells(kind, option, grow=0.0):
    """Red shell of one leg type ("front", "mid1", "mid2", "rear") for option "thin" or "thick", leg frame, as meshes
    (arm part, shin part; one printed part per leg). grow: every face pushed out by grow (sweep probe at LEG_PATH)."""
    L1, L2, LW, LH, SW, ADY = L.P_["L1"], L.P_["L2"], L.LEG_W, L.LEG_H, L.SHIN_W, L.ARM_DY
    out = []
    # arm: U channel over the bar (TURN fit), top plate; thick: hollow arch on top (open onto the plate)
    yl, yh = ADY - LW / 2 - FIT, ADY + LW / 2 + FIT
    inner = sbox(yl, -LH / 2, yh, LH / 2 + FIT)
    def arm_profile(skirt_lo, skirt_hi, hood):
        lo = yl - TS if skirt_lo else yl
        hi = yh + TS if skirt_hi else yh
        p = sbox(lo, -LH / 2 + 1.0, hi, LH / 2 + FIT + TT).difference(inner)
        if hood:
            c = (lo + hi) / 2
            a = _arch(hi - lo, hood, 0).buffer(0)
            hollow = _arch(hi - lo - 2 * TW, hood - TW, 0)
            from shapely import affinity
            a = affinity.translate(a.difference(hollow), c, LH / 2 + FIT + TT)
            p = p.union(a)
        return p
    x0, x1 = X0[kind], L1 - 3.0
    h = HOOD[option]
    cuts = [x0, x1] if not h else [x0, x0 + 8.0, x1]
    if kind in ("mid1", "mid2"):
        cuts = sorted(set(cuts + [FACING_END]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        lo_ok = not (kind == "mid2" and a >= FACING_END)
        hi_ok = not (kind == "mid1" and a >= FACING_END)
        hh = 0 if not h else (HOOD_ROOT if a < x0 + 8.0 else h)
        out += _extrude(arm_profile(lo_ok, hi_ok, hh), a, b, grow=grow)
    # shin: front / rear: U channel + outer plate (thick: hollow bulge); middle: narrow plate only (thick: solid bulge)
    SH = shin_frame()
    t0, t1 = 5.0, L2 - 8.0
    sl, sh = -SW / 2 - FIT, SW / 2 + FIT
    sin = sbox(sl, -LH / 2, sh, LH / 2 + FIT)
    from shapely import affinity
    if kind in ("front", "rear"):
        def shin_profile(skirt_hi, bulge=True):
            p = sbox(sl - TS, -LH / 2 + 1.0, sh + TS if skirt_hi else sh, LH / 2 + FIT + TT).difference(sin)
            bh = BULGE[option] if bulge else 0.0
            if bh:
                w = sh - sl + 2 * TS
                bulge = _arch(w, bh, 0).difference(_arch(w - 2 * TW, bh - TW, 0))
                p = p.union(affinity.translate(bulge, 0, LH / 2 + FIT + TT))
            return p
        if kind == "front":
            if FRONT_SKIRT_T > t0:
                out += _extrude(shin_profile(True), t0, FRONT_SKIRT_T, SH, grow)
            tb = max(FRONT_SKIRT_T, BULGE_T0 if BULGE[option] else t0)
            if tb > FRONT_SKIRT_T:
                out += _extrude(shin_profile(False, False), FRONT_SKIRT_T, tb, SH, grow)
            out += _extrude(shin_profile(False), tb, t1, SH, grow)
        else:
            out += _extrude(shin_profile(True), t0, t1, SH, grow)
    else:
        # both edges stop LEG_PATH inside the shin's faces; mid2's outer (+y) edge gets a skirt + lip (q3c: free over
        # the whole shin); mid1's outer (-y) edge is swept by the front shin over its whole length (q3c): plate only
        wf = SW / 2 - LP
        lo, hi = (-wf, wf) if kind == "mid1" else (-wf, sh + TS)
        p = sbox(lo, LH / 2 + FIT, hi, LH / 2 + FIT + TT)
        if kind == "mid2":
            p = p.union(sbox(sh, -LH / 2 + 1.0, sh + TS, LH / 2 + FIT + TT))
        if MID_BULGE[option]:
            p = p.union(affinity.translate(_arch(hi - lo, MID_BULGE[option], 0), (lo + hi) / 2, LH / 2 + FIT + TT))
        out += _extrude(p, t0, t1, SH, grow)
    return out


# ---- base skin (coarse copy of probe q2) ----
def base_skin(dz=2.0, step=30):
    ch, fb, body, cover = (load(n) for n in ("chassis", "front-block-v2", "body-v2", "crank-cover"))
    Z = list(np.arange(np.floor(ch.bounds[0][2]) + dz / 2, R.BAND_TOP, dz))
    def secs(m):
        return [unary_union(p.polygons_full) if p is not None and len(p.polygons_full) else Polygon()
                for p in m.section_multiplane([0, 0, 0], [0, 0, 1], Z)]
    S = [secs(m) for m in (ch, fb, body, cover)]
    mov = [[] for _ in Z]
    cache = {}
    for a in range(0, 360, step):
        for n, f, M in L.poses(np.radians(a)):
            if not (n.startswith("leg") or n.startswith("pivot")):
                continue
            m = cache.setdefault(f, trimesh.load(L.stl(f))).copy().apply_transform(M)
            lines, TT_, _ = trimesh.intersections.mesh_multiplane(m, [0, 0, 0], [0, 0, 1], Z)
            for i, seg in enumerate(lines):
                if len(seg):
                    p2 = seg.reshape(-1, 2)
                    pts = trimesh.transform_points(np.column_stack([p2, np.zeros(len(p2))]), TT_[i])[:, :2]
                    mov[i].append(MultiPoint([tuple(q) for q in pts]).convex_hull)
    meshes = []
    for i, z in enumerate(Z):
        c = S[0][i]
        if c.is_empty:
            continue
        H = MultiPolygon(list(getattr(c, "geoms", [c]))).convex_hull
        obs = unary_union([S[1][i].buffer(fits.WINDOW.side), S[2][i].buffer(fits.WINDOW.side),
                           S[3][i].buffer(fits.WINDOW.side), unary_union(mov[i]).buffer(LP)])
        skin = H.difference(H.buffer(-TT)).difference(obs).simplify(0.3)
        for p in getattr(skin, "geoms", [skin]):
            if p.area > 1.0:
                m = trimesh.creation.extrude_polygon(p, dz)
                m.apply_translation([0, 0, z - dz / 2])
                meshes.append(m)
    return trimesh.util.concatenate(meshes)


def load(n):
    return trimesh.load(os.path.join(HERE, "out", f"{n}.stl"))


def face_wall():
    """F1 mock-up: two 1.2 plates over the front block's opening (p3: seam 74.8 to 83.4 over |x-CX| <= 10.5; centre
    slot to z 102.5, 4-16 wide), set on the face's outer skin (y -58.3 at z 78, -60.5 at z 81-84)."""
    cx = R.CX
    out = []
    for lo, hi in (((cx - 10.5, -59.4, 74.8), (cx + 10.5, -58.2, 83.4)), ((cx - 8.0, -60.6, 82.0), (cx + 8.0, -59.4, 102.5))):
        lo, hi = np.array(lo), np.array(hi)
        m = trimesh.creation.box(hi - lo)
        m.apply_translation((lo + hi) / 2)
        out.append(m)
    return out


def scene(option, skin):
    body = R.carcass_proxy("body", lifted=True)
    (y0, z0), (y1, z1) = DOME
    nrm = np.array([0.0, -(z1 - z0) / (y1 - y0), 1.0])
    nrm /= np.linalg.norm(nrm)
    org = np.array([0.0, y0, z0])
    items = [{"mesh": load(n), "color": COL["black"]} for n in ("chassis", "crank-cover", "front-block-v2")]
    items += [{"mesh": skin, "color": COL["black"], "edges": False}]
    items += [{"mesh": m, "color": COL["black"]} for m in face_wall()]
    items += [{"mesh": trimesh.intersections.slice_mesh_plane(body, -nrm, org, cap=True), "color": COL["red"]},
              {"mesh": trimesh.intersections.slice_mesh_plane(body, nrm, org, cap=True), "color": COL["blue"]}]
    for n, f, M in L.poses(0.0):
        if n.startswith("leg"):
            items.append({"mesh": trimesh.load(L.stl(f)).apply_transform(M), "color": COL["black"]})
            items += [{"mesh": m.apply_transform(M), "color": COL["red"]} for m in leg_shells(KIND[n[:4]], option)]
        elif n.startswith("pivot"):
            items.append({"mesh": trimesh.load(L.stl(f)).apply_transform(M), "color": COL["black"]})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--photo", default=None, help="private reference photo: only for a copy outside the repo")
    ap.add_argument("--out", default=None)
    ap.add_argument("--lite", action="store_true")
    a = ap.parse_args()
    w = WORDS[a.lang]
    views = VIEWS[:1] if a.lite else VIEWS
    skin = base_skin()
    fig = plt.figure(figsize=(4.2 * (len(views) + 1), 9.2))
    for r, opt in enumerate(("thin", "thick")):
        items = scene(opt, skin)
        for c, v in enumerate(views):
            ax = fig.add_axes([(c + 1) / (len(views) + 1), 0.5 - r * 0.47, 1 / (len(views) + 1), 0.42])
            proj = F.draw(ax, items, view=v)
            ax.set_title(f"{w[opt]} · {w['views'][c]}", fontsize=F.FONT - 1)
            if c == 0:
                F.callout(ax, proj, [42.7, 10.0, 158.0], w["dome"], dx=-60, dy=-25, color=COL["blue"])
                F.callout(ax, proj, [62.0, -50.0, 66.0], w["skin"], dx=70, dy=-60, color="#1a1a1a")
                F.callout(ax, proj, [42.7, -60.0, 92.0], w["f1"], dx=40, dy=70, color="#1a1a1a")
                F.callout(ax, proj, [-40.0, -40.0, 72.0], w["shell"], dx=-10, dy=-70, color=COL["red"])
    px = fig.add_axes([0.0, 0.5, 1 / (len(views) + 1), 0.42])
    if a.photo:
        px.imshow(plt.imread(a.photo))
    else:
        px.text(0.5, 0.5, w["photo"], ha="center", va="center", fontsize=F.FONT, color=COL["grey"])
    px.axis("off")
    cx = fig.add_axes([0.05, 0.08, 0.6 / (len(views) + 1), 0.3])
    for i, opt in enumerate(("thin", "thick")):
        lo, hi = MASS[opt]
        cx.bar(i, hi - lo, bottom=lo, color=COL["red"] if i else "#e59866", edgecolor="#1a1a1a")
        f = (lambda g: f"{g:.1f}".replace(".", "," if a.lang == "es" else "."))
        cx.text(i, hi + 1, f"{f(lo)}–{f(hi)}", ha="center", fontsize=F.FONT - 2)
    cx.set_xticks([0, 1], [w["thin"].replace(" ", "\n", 1), w["thick"].replace(" ", "\n", 1)], fontsize=F.FONT - 2)
    cx.axhline(478, color="#c0392b", ls="--", lw=1.2)
    cx.text(-0.45, 478.6, w["ceiling"], color="#c0392b", fontsize=F.FONT - 2)
    cx.set_ylim(455, 500)
    cx.set_ylabel(w["mass"], fontsize=F.FONT - 2)
    cx.spines[["top", "right"]].set_visible(False)
    fig.suptitle(w["title"], fontsize=F.FONT + 3)
    out = a.out or os.path.join(HERE, "images", "plan-e" + ("-es" if a.lang == "es" else "") + ".png")
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
