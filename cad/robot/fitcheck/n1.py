"""N1 whole-robot check: every part of verify.py at the 24 crank poses, manifold3d on the coarse STLs.
overlap mm = 2 V / A of the intersection (a slab's thickness); near = min_gap < 1 mm (tolerance)."""
import os, sys, time, json, itertools
import numpy as np, trimesh
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")); W = R + "/cad/robot"
for p in (R + "/tools", R, W): sys.path.insert(0, p)
os.chdir(W)
from manifold3d import Manifold, Mesh
import verify as V
t0 = time.time()
names = [n for n in V.PARTS if "mesh" in V.PARTS[n] or os.path.exists(V.PARTS[n].get("stl", ""))]
missing = [n for n in V.PARTS if n not in names]
mesh = {n: (V.PARTS[n]["mesh"] if "mesh" in V.PARTS[n] else trimesh.load(V.PARTS[n]["stl"], force="mesh")) for n in names}
def man(m, T):
    v = (np.c_[m.vertices, np.ones(len(m.vertices))] @ T.T)[:, :3]
    return Manifold(Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
worst = {}; near = {}
for k in range(24):
    P = V.poses(k); M = {n: man(mesh[n], np.asarray(P.get(n, np.eye(4)), float)) for n in names}
    B = {n: np.array(M[n].bounding_box()) for n in names}
    for a, b in itertools.combinations(names, 2):
        ba, bb = B[a], B[b]
        if (ba[:3] > bb[3:] + 1).any() or (bb[:3] > ba[3:] + 1).any(): continue
        x = M[a] ^ M[b]; vol = x.volume()
        if vol > 1e-3:
            t = 2 * vol / max(x.surface_area(), 1e-9)
            w = worst.setdefault((a, b), [0, 0, []]); w[2].append(k)
            if t > w[0]: w[0], w[1] = t, vol
        else:
            g = M[a].min_gap(M[b], 1.0)
            if g < 1.0:
                w = near.setdefault((a, b), [9, []]); w[1].append(k); w[0] = min(w[0], g)
allowed = set(getattr(V, "ALLOWED_CONTACT", {}).keys())
print(f"parts {len(names)} counted, missing STL: {missing}; {time.time() - t0:.1f} s")
print("OVERLAPS  part A | part B | worst mm (2V/A) | vol mm3 | poses | designed contact")
for (a, b), (t, vol, ks) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
    d = "yes" if (a, b) in allowed or (b, a) in allowed else ""
    print(f"  {a} | {b} | {t:.2f} | {vol:.1f} | {len(ks)}: {ks[0]}-{ks[-1]} | {d}")
print("NEAR (<1 mm, no overlap)  part A | part B | min gap | poses")
for (a, b), (g, ks) in sorted(near.items(), key=lambda kv: kv[1][0]):
    print(f"  {a} | {b} | {g:.2f} | {len(ks)}")
json.dump({"overlap": {f"{a}|{b}": v for (a, b), v in worst.items()}, "near": {f"{a}|{b}": v for (a, b), v in near.items()}},
          open(os.path.dirname(os.path.abspath(__file__)) + "/n1.json", "w"))
