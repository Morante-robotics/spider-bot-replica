#!/usr/bin/env python3
"""Lay out STL parts on one Bambu Studio plate, slice it, and save a ready-to-print project (.3mf).

Each part is given as  path.stl[@rx,ry,rz][xN]: rotated about X, then Y, then Z (degrees) into its print orientation,
dropped onto the bed, and repeated N times. Bambu Studio's CLI then arranges the plate and slices it with the
system presets below, flattened (the CLI does not follow "inherits"), plus the overrides in --set.

Usage:
    python3 bambu_plate.py OUT.3mf part1.stl@90,0,0 part2.stl x2 ... [--set enable_support=1 ...]

Needs numpy and trimesh, and Bambu Studio in /Applications.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
import trimesh

BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
SYSTEM = os.path.expanduser("~/Library/Application Support/BambuStudio/system/BBL")
MACHINE = "Bambu Lab P2S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL P2S"
FILAMENT = "Bambu PLA Basic @BBL P2S"


def flat(kind, name):
    """System preset with its whole 'inherits' chain merged in (child wins)."""
    d = json.load(open(os.path.join(SYSTEM, kind, f"{name}.json")))
    parent = d.pop("inherits", None)
    base = flat(kind, parent) if parent else {}
    base.update(d)
    return base


def parse(spec):
    reps = 1
    if "x" in spec.rsplit(".stl", 1)[-1]:
        spec, n = spec.rsplit("x", 1)
        reps = int(n)
    path, _, rot = spec.partition("@")
    angles = [float(a) for a in rot.split(",")] if rot else [0, 0, 0]
    return path, angles, reps


def orient(path, angles, out):
    m = trimesh.load(path)
    for ax, a in zip(np.eye(3), angles):
        if a:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a), ax))
    m.apply_translation(-m.bounds[0])                    # corner on the origin, bottom on the bed
    m.export(out)
    return m.extents


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--set", nargs="*", default=[], help="process overrides, key=value")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp()
    stls = []
    for spec in a.parts:
        path, angles, reps = parse(spec)
        name = os.path.splitext(os.path.basename(path))[0]
        dst = os.path.join(tmp, f"{name}.stl")
        ext = orient(path, angles, dst)
        print(f"{name:20s} × {reps}  {ext[0]:6.1f} × {ext[1]:6.1f} × {ext[2]:6.1f} mm")
        stls += [dst] * reps

    machine, process, filament = flat("machine", MACHINE), flat("process", PROCESS), flat("filament", FILAMENT)
    for kv in a.set:
        k, v = kv.split("=", 1)
        process[k] = v
    for d, n in ((machine, MACHINE), (process, PROCESS), (filament, FILAMENT)):
        d["name"], d["from"] = n, "system"
    files = []
    for kind, d in (("machine", machine), ("process", process), ("filament", filament)):
        f = os.path.join(tmp, f"{kind}.json")
        json.dump(d, open(f, "w"), indent=1)
        files.append(f)

    out = os.path.abspath(a.out)
    cmd = [BAMBU, "--arrange", "1", "--orient", "0", "--load-settings", f"{files[0]};{files[1]}",
           "--load-filaments", files[2], "--slice", "1", "--export-3mf", out, *stls]
    r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"Bambu Studio failed ({r.returncode})")
    shutil.rmtree(tmp)
    mark_changed(out, [kv.split("=", 1)[0] for kv in a.set])
    print("wrote", out)


def mark_changed(path, keys):
    """List the overridden keys in the project's 'different_settings_to_system', as the GUI does when it saves:
    without it, the GUI opens the project with the plain system process and drops the overrides."""
    import zipfile
    name = "Metadata/project_settings.config"
    with zipfile.ZipFile(path) as z:
        items = {i: z.read(i) for i in z.namelist()}
    cfg = json.loads(items[name])
    diff = cfg.get("different_settings_to_system") or ["", "", ""]
    diff[0] = ";".join(sorted(set(filter(None, diff[0].split(";") + keys))))
    cfg["different_settings_to_system"] = diff
    items[name] = json.dumps(cfg, indent=4).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for i, data in items.items():
            z.writestr(i, data)


if __name__ == "__main__":
    main()
