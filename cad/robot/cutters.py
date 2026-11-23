"""Designed cutters of the shells (speed plan, phase A; Morante 2026-11-23): each leg window is a few-sided prism whose
outline is measured from the legs' motion, never a hull of sampled points cut in OpenCascade.

How a window is made (numbers below):
  1. the wall samples (0.4 mm apart, both faces of the wall) that leg Lg comes within WR + SLACK of, over the
     24 crank poses and its assembly slide along the pin (at its assembly pose ASM_POSE), within RN + 4 of its pivot;
  2. seen along the wall's outward normal n there (horizontal): the lowest such sample per COL column is the window's
     floor; the window is open to the top (ZTOP);
  3. buffered SLACK2 + SMOOTH and simplified SMOOTH: 11-13 straight sides; extruded through the wall band only.
Between two neighbouring windows, wall left narrower than MINW (4 nozzle lines) is added to the first window's outline
(a separate prism there cost 7.7 s of OpenCascade: it cuts thin spikes of the BSpline skin). No pads round the windows:
open-top windows carry no load (the leg is held by its pin), and their booleans on the BSpline skin cost 12 s.

Everything here is numpy, shapely and trimesh (milliseconds to a few seconds); shells.base() turns the prisms into
OpenCascade solids and cuts them in one boolean. leg_gaps() is the check: every leg at every pose and along its
assembly path against the built base, with manifold3d (a few seconds).
"""
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from trimesh.remesh import subdivide_to_size

SLACK = 0.05        # mm on top of WR when picking wall samples near the sweep (with SMOOTH: gaps 0.94-1.16 for WR 0.9)
SLACK2 = 0.12       # outline buffer for the 0.4 mm wall sampling
SMOOTH = 0.25       # outline grown and simplified by this: 11-13 sides per window
COL = 0.25          # floor columns along the wall
MINW = 1.6          # wall between two windows narrower than this is cut (4 lines of a 0.4 nozzle)
LEG_STEP = 0.8      # leg surface samples at most this far apart
WALL_STEP = 0.4     # wall surface samples
SLIDE_N = 8         # samples along the assembly slide
LEG_DROP = 30.0     # verify.py: each leg is lowered this far beside its pin, then slid in along it
LEG_SLIDE = {k: 6.6 for k in range(8)}          # shells.CL.LSL; legs 5 and 6 start 10 mm out (drive unit's lug)
LEG_SLIDE.update({5: 10.0, 6: 10.0})
ASM_POSE = {k: 0 for k in range(8)}             # crank pose each leg is put on at: legs 0 and 3 after half a turn (pose 12):
ASM_POSE.update({0: 12, 3: 12})                 # leg 0 has no front relief (Morante 2026-11-23 «Lisa»), leg 3 grazes the back
                                                # pocket's side at pose 0; at 12 they clear 1.32 / 1.33
PAIRS = ((0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7))


def mesh_of(shape, tol=0.05, ang=0.3):
    """OpenCascade shape -> welded trimesh (tessellate() repeats each face's vertices: unwelded, it is not a manifold)."""
    v, f = shape.tessellate(tol, ang)
    m = trimesh.Trimesh(np.array([[p.X, p.Y, p.Z] for p in v]), np.array(f), process=False)
    m.merge_vertices(digits_vertex=6); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    return m


def frame_of(n):
    """(t, z, n): n the horizontal outward normal, z up, t = z x n (the window's 2D axes are t, z)."""
    n = np.array([n[0], n[1], 0.0]); n /= np.linalg.norm(n); z = np.array([0, 0, 1.0])
    return np.cross(z, n), z, n


class Windows:
    """leg windows of a base: base0 (trimesh, the base before windows), legs {Lg: trimesh in the neutral pose}, frames(Lg, k) -> 4x4, piv (8, 3), crank pins A (8, 24, 3), wr(Lg), rn, ztop."""

    def __init__(self, base0, legs, frames, piv, A, wr, rn, ztop, samples=None):
        self.base0, self.legs, self.frames, self.piv, self.A, self.wr, self.rn, self.ztop = base0, legs, frames, piv, A, wr, rn, ztop
        self.samples = samples or {}
        self.wall = self._near(base0)
        self.hits = {Lg: self._hits(Lg) for Lg in range(8)}
        for i, j in PAIRS: self._narrow(i, j)

    def _near(self, m):
        """surface samples WALL_STEP apart of the faces of m within rn + 6 of a pivot (the rest of the bowl is never cut)."""
        c = m.triangles_center; keep = np.zeros(len(c), bool)
        for p in self.piv: keep |= np.linalg.norm(c - p, axis=1) <= self.rn + 6
        return subdivide_to_size(m.vertices, m.faces[keep], max_edge=WALL_STEP)[0]

    def u(self, Lg, k):
        u = self.piv[Lg] - self.A[Lg, k]; return u / np.linalg.norm(u)

    def _cloud(self, Lg):
        """the leg's samples within rn + 4 of its pivot (the pivot is fixed by the frames: the filter holds at every pose)
        at the 24 poses and along the slide of its assembly path."""
        V = self.samples.get(Lg)
        if V is None: m = self.legs[Lg]; V = subdivide_to_size(m.vertices, m.faces, max_edge=LEG_STEP)[0]
        V = V[np.linalg.norm(V - self.piv[Lg], axis=1) <= self.rn + 4]
        at = lambda k: V @ self.frames(Lg, k)[:3, :3].T + self.frames(Lg, k)[:3, 3]
        k0 = ASM_POSE[Lg]; q0 = at(k0); u = self.u(Lg, k0)
        return np.vstack([at(k) for k in range(24)] + [q0 + s * u for s in np.linspace(0, LEG_SLIDE[Lg], SLIDE_N)])

    def _hits(self, Lg):
        """wall samples within wr + SLACK of the leg's sweep, and the mean outward normal of the wall there."""
        C = cKDTree(self._cloud(Lg)); w = self.wall[np.linalg.norm(self.wall - self.piv[Lg], axis=1) <= self.rn + 4]
        R = w[np.isfinite(C.query(w, distance_upper_bound=self.wr(Lg) + SLACK)[0])]
        _, _, fi = trimesh.proximity.closest_point(self.base0, R[::max(1, len(R) // 300)])
        nn = self.base0.face_normals[fi]; c = self.base0.triangles_center[fi]
        nn = nn * np.sign((nn[:, :2] * c[:, :2]).sum(1))[:, None]                  # outward (the bowl is round the z axis)
        return R, nn.mean(0)

    def outline(self, R, fr):
        t, z, _ = fr; tz = np.c_[R @ t, R @ z]; cb = np.floor(tz[:, 0] / COL).astype(int); lo = {}
        for c, zz in zip(cb, tz[:, 1]): lo[c] = min(lo.get(c, 1e9), zz)
        cs = sorted(lo); env = [(c * COL, lo[c]) for c in cs] + [((cs[-1] + 1) * COL, lo[cs[-1]])]
        p = Polygon([(env[0][0], self.ztop)] + env + [(env[-1][0], self.ztop)]).buffer(SLACK2 + SMOOTH, quad_segs=2).simplify(SMOOTH)
        return p if p.geom_type == "Polygon" else max(p.geoms, key=lambda g: g.area)

    def _narrow(self, i, j):
        """wall between windows i and j narrower than MINW, seen along their mean normal (closing of the two outlines):
        its wall samples join window i's, so window i's floor takes the narrow wall down to where it is MINW wide."""
        import shapely
        (Ri, ni), (Rj, nj) = self.hits[i], self.hits[j]; fr = frame_of(ni / np.linalg.norm(ni) + nj / np.linalg.norm(nj))
        U = self.outline(Ri, fr).union(self.outline(Rj, fr))
        F = U.buffer(MINW / 2, quad_segs=3).buffer(-MINW / 2, quad_segs=3).difference(U)
        if F.is_empty: return
        d = np.r_[Ri @ fr[2], Rj @ fr[2]]; w = self.wall
        w = w[(w @ fr[2] >= d.min() - 1.0) & (w @ fr[2] <= d.max() + 1.0)]
        w = w[shapely.contains_xy(F.buffer(0.1), w @ fr[0], w @ fr[1])]
        if len(w): self.hits[i] = (np.vstack([Ri, w]), ni)

    def window(self, Lg):
        """(outline, frame, (d0, d1)): the prism is outline x [d0, d1] along n."""
        R, n = self.hits[Lg]; fr = frame_of(n); d = R @ fr[2]
        return self.outline(R, fr), fr, (d.min() - 1.0, d.max() + 1.0)


def ccw(poly):
    xy = np.array(poly.exterior.coords)[:-1]; return xy if poly.exterior.is_ccw else xy[::-1]


def leg_gaps(base, legs, frames, piv, A, need=0.4):
    """every leg against the base (trimesh) at the 24 poses and along its assembly path (slide, then the drop) at its
    ASM_POSE: [(leg, 'poses' | 'path', min gap, where)], gaps capped at 2 mm. manifold3d, a few seconds."""
    from manifold3d import Manifold, Mesh
    def M(m):
        x = Manifold(Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
        if x.status().name != "NoError" or x.volume() <= 0: raise ValueError(f"leg_gaps: mesh is not a closed manifold ({x.status()})")
        return x
    b = M(base); rows = []
    for Lg in range(8):
        lm = M(legs[Lg]); k0 = ASM_POSE[Lg]; u = piv[Lg] - A[Lg, k0]; u /= np.linalg.norm(u)
        g = min((b.min_gap(lm.transform(frames(Lg, k)[:3, :]), 2.0), k) for k in range(24)); rows.append((Lg, "poses", *g))
        path = [s * u for s in np.linspace(0, LEG_SLIDE[Lg], 12)] + [LEG_SLIDE[Lg] * u + [0, 0, dz] for dz in np.arange(0.5, LEG_DROP + 0.1, 1.0)]
        best = (9.0, None)
        for o in path:
            T = frames(Lg, k0).copy(); T[:3, 3] += o; gg = b.min_gap(lm.transform(T[:3, :]), 2.0)
            if gg < best[0]: best = (gg, tuple(np.round(o, 1)))
        rows.append((Lg, f"path@k{k0}", *best))
    return rows
