"""Views for the judge (spec.json views): the robot and jenscolt's assembled meshes in the same four views and framing
(tools/mesh_ref.py views). jenscolt's meshes are read here only, never by build.py or a gate.

    ../../.venv/bin/python views.py <out.png>        # the robot, framed on the reference
    ../../.venv/bin/python views.py --reference      # images/reference.png and out/reference.stl
Reference: jenscolt's meshes assembled by the archived tools/assemble_jenscolt.py (read from the git tag, not restored:
8 legs, eyes, small eyes, sensor), moved to the robot frame ((v - ORIGIN) x S).
"""
import os, sys, glob
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (ROOT + "/tools", ROOT, ROOT + "/cad"):
    if p not in sys.path: sys.path.insert(0, p)
import json, motion, mesh_ref
S = float(json.load(open(os.path.join(HERE, "spec.json")))["dims"]["S_start"]["value"])
REF = os.path.join(ROOT, "cad", "carcass-jenscolt")
OUT = os.path.join(HERE, "out")

def _archive():
    """the archived tools/assemble_jenscolt.py (git tag pre-redesign-2026-11-17), read from git, not restored."""
    import subprocess
    src = subprocess.run(["git", "show", "pre-redesign-2026-11-17:tools/assemble_jenscolt.py"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    src = src.replace("from stl_preview import load", "load = None")
    ns = {"__name__": "assemble_jenscolt", "__file__": os.path.join(ROOT, "tools", "assemble_jenscolt.py")}; exec(compile(src, "assemble_jenscolt.py", "exec"), ns)
    ns["load"] = lambda p: np.asarray(trimesh.load(p).triangles)
    return ns

def reference():
    A = _archive(); p0 = os.path.join(OUT, "jenscolt-assembled.stl")
    sys.argv_saved = sys.argv; sys.argv = ["x", REF, p0]
    try: A["main"]()
    finally: sys.argv = sys.argv_saved
    m = trimesh.load(p0); m.apply_translation(-motion.ORIGIN); m.apply_scale(S)
    p = os.path.join(OUT, "reference.stl"); m.export(p); return p

def robot():
    sys.path.insert(0, HERE); import verify as V
    ms = []
    T = V.poses(0)
    for n, d in V.PARTS.items():
        if "stl" not in d or d.get("bench"): continue
        m = trimesh.load(os.path.join(HERE, d["stl"]))
        if n in T: m.apply_transform(T[n])
        ms.append(m)
    p = os.path.join(OUT, "robot-view.stl"); trimesh.util.concatenate(ms).export(p); return p

if __name__ == "__main__":
    ref = reference()
    if "--reference" in sys.argv:
        os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
        mesh_ref.views(os.path.join(HERE, "images", "reference.png"), [ref])
    else:
        out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "images", "views.png")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        mesh_ref.views(out, [ref], [robot()])
