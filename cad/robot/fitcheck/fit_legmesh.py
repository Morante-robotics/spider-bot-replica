"""The real parametric legs (cad/legs leg()) bent onto motion.py's neutral leg at the robot's S (fit_env.P), as
meshes in the neutral frame, written to .cache/ (fit_legs.py builds it when missing or older than cad/legs/build.py).
Poses: rigid carry as motion.legs does (P + ((v-P) @ R0.T) @ R_k)."""
import os, sys, time, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fit_env import *
sys.path.insert(0, ROOT + "/cad/legs"); import build as LB
from build123d import Shape
def tri(shape, tol=0.25):
    V, Fc = shape.tessellate(tol, 0.4); V = np.array([[v.X, v.Y, v.Z] for v in V]); return trimesh.Trimesh(V, np.array(Fc), process=False)
def build(i, n_end=1):
    P_, A0, ang, pts, rad, ni = motion.neutral_leg(i, P, n=13)
    rd = np.array([np.cos(ang), np.sin(ang), 0.0]); across = np.cross([0, 0, 1.0], rd)
    bl = pts[ni + 13:][::-1]; bsp = [tuple(bl[round(j * 16 / 4)]) for j in range(5)]
    _, A0b, _, pts2, _, _ = motion.neutral_leg(i, P, n=201)
    up = pts2[ni:ni + 201]; sp0 = LB.arm_spine_local(); f = sp0.knots[1] / sp0.knots[2]
    asp = [A0, A0 + f * (P_ - A0), P_, up[100], up[-1]]
    blade, arm = LB.leg("L", bsp, asp, S, tuple(across))
    return tri(blade), tri(arm), P_, A0
def mesh_path():
    return os.path.join(CACHE, f"legs_mesh_{stamp('cad/legs/build.py', 'cad/motion.py', 'cad/common.py')}_{S}.npz")
def write():
    t = time.time(); m = {}
    for i in range(4):
        b, a, P_, A0 = build(i); print(i, "blade", len(b.faces), round(b.volume/1000, 2), "arm", len(a.faces), round(a.volume/1000, 2), "t", round(time.time()-t, 1), flush=True)
        m[f"b{i}"] = b.vertices; m[f"bf{i}"] = b.faces; m[f"a{i}"] = a.vertices; m[f"af{i}"] = a.faces; m[f"P{i}"] = P_; m[f"A{i}"] = A0
    np.savez(mesh_path(), **m)
if __name__ == "__main__":
    write()
