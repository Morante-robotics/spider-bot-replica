"""The real cad/legs parts (fit_legmesh.py: leg() bent on motion's neutral leg at the robot's S) as surface samples,
carried rigidly per pose exactly as motion.legs does: V' = P + (V - P) @ R0.T @ R_k (right legs; left = mirror in x)."""
import os, numpy as np, trimesh
from trimesh.remesh import subdivide_to_size
import fit_legmesh
def samp(V, Fc, edge):
    v, f = subdivide_to_size(V, Fc, max_edge=edge); return np.asarray(v)
def load(motion, PIV, A_ALL, cut=11.5, edge_arm=0.5, edge_blade=0.8):
    mp = fit_legmesh.mesh_path()
    if not os.path.exists(mp): fit_legmesh.write()
    ck = mp.replace(".npz", f"_pts_{edge_arm}_{edge_blade}.npz")
    z = np.load(mp)
    if os.path.exists(ck): c = np.load(ck)
    else:
        c = {}
        for i in range(4):
            c[f"a{i}"] = samp(z[f"a{i}"], z[f"af{i}"], edge_arm); c[f"b{i}"] = samp(z[f"b{i}"], z[f"bf{i}"], edge_blade)
        np.savez(ck, **c)
    N = []
    for i in range(4):
        Pn, A0 = z[f"P{i}"], z[f"A{i}"]; u0 = (Pn - A0) / np.linalg.norm(Pn - A0); R0 = motion.frame(u0[None])[0]
        a = c[f"a{i}"]; s = (a - A0) @ u0; sP = np.linalg.norm(Pn - A0)
        arm = a[s >= cut]; s = s[s >= cut]
        N.append(dict(P=Pn, R0=R0, inn=arm[s <= sP + 4.0], out=np.vstack([arm[s > sP + 4.0], c[f"b{i}"]]), sP=sP))
    def pose(Lg, k, full):
        n = N[Lg % 4]; right = Lg < 4; A = A_ALL[Lg, k] * ([1, 1, 1] if right else [-1, 1, 1])
        u = (n["P"] - A) / np.linalg.norm(n["P"] - A); Rk = motion.frame(u[None])[0]; M = n["R0"].T @ Rk
        V = n["inn"] if not full else np.vstack([n["inn"], n["out"]])
        W = n["P"] + (V - n["P"]) @ M
        return W if right else W * [-1, 1, 1]
    return pose
