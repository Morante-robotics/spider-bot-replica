#!/usr/bin/env python3
"""How much filament a sliced Bambu Studio project spends on support, per part and in total.

Reads the G-code inside a sliced .3mf (Metadata/plate_N.gcode), adds up the extrusion of each feature (outer wall,
sparse infill, support, ...) and of each object, and prints grams of part and of support. Use it to compare print
orientations: slice each candidate, run this, keep the one with the least support.

Usage:
    python3 tools/print_report.py plate.3mf [--plate 1] [--json out.json]
"""
import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

SUPPORT = ("Support", "Support interface", "Support transition")


def report(path, plate=1):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        gname = f"Metadata/plate_{plate}.gcode"
        if gname not in names:
            raise SystemExit(f"{path}: no {gname} (is the project sliced?)")
        gcode = z.read(gname).decode(errors="replace")
        objects = {}
        if "Metadata/slice_info.config" in names:
            root = ET.fromstring(z.read("Metadata/slice_info.config"))
            for o in root.iter("object"):
                objects[o.get("identify_id")] = o.get("name")
    dia, dens = 1.75, 1.24
    m = re.search(r"; filament_diameter[:=]\s*([\d.]+)", gcode)
    dia = float(m.group(1)) if m else dia
    m = re.search(r"; filament_density[:=]\s*([\d.]+)", gcode)
    dens = float(m.group(1)) if m else dens
    g_per_mm = math.pi * (dia / 2) ** 2 * dens / 1000
    m = re.search(r"total estimated time:\s*(.+)", gcode)
    time = m.group(1).strip() if m else "?"

    feat, obj = "none", "none"
    by_feat = defaultdict(float)
    by_obj = defaultdict(lambda: defaultdict(float))
    relative = True
    e_re = re.compile(r"\bE(-?[\d.]+)")
    for line in gcode.splitlines():
        if line.startswith(";"):
            if line.startswith("; FEATURE: "):
                feat = line[11:].strip()
            elif line.startswith("; start printing object, unique label id: "):
                obj = line.rsplit(":", 1)[1].strip()
            elif line.startswith("; stop printing object"):
                obj = "none"
            continue
        if line.startswith("M82"):
            relative = False
        elif line.startswith("M83"):
            relative = True
        if not (line.startswith("G1 ") or line.startswith("G2 ") or line.startswith("G3 ")):
            continue
        m = e_re.search(line)
        if not m or not relative:
            continue
        if " X" not in line and " Y" not in line:     # un-retract after a retraction: no material laid down
            continue
        e = float(m.group(1))
        if e <= 0:
            continue
        by_feat[feat] += e
        by_obj[obj]["support" if feat in SUPPORT else "part"] += e

    grams = {k: v * g_per_mm for k, v in by_feat.items()}
    support = sum(v for k, v in grams.items() if k in SUPPORT)
    total = sum(grams.values())
    parts = []
    for oid, d in by_obj.items():
        if oid == "none":
            continue
        p, s = d["part"] * g_per_mm, d["support"] * g_per_mm
        parts.append({"object": objects.get(oid, oid), "part_g": round(p, 2), "support_g": round(s, 2),
                      "support_pct": round(100 * s / p, 1) if p else 0.0})
    loose = by_obj.get("none", {})
    return {"file": path, "plate": plate, "time": time, "total_g": round(total, 2), "support_g": round(support, 2),
            "support_pct_of_parts": round(100 * support / (total - support), 1) if total > support else 0.0,
            "support_outside_objects_g": round(loose.get("support", 0) * g_per_mm, 2),
            "features_g": {k: round(v, 2) for k, v in sorted(grams.items(), key=lambda x: -x[1])},
            "objects": sorted(parts, key=lambda x: -x["support_g"])}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--plate", type=int, default=1)
    ap.add_argument("--json")
    a = ap.parse_args()
    r = report(a.project, a.plate)
    print(f"{r['file']} plate {r['plate']}: {r['total_g']} g, {r['time']}")
    print(f"  support {r['support_g']} g = {r['support_pct_of_parts']} % of the parts' weight"
          + (f" ({r['support_outside_objects_g']} g not tied to one object)" if r["support_outside_objects_g"] else ""))
    for o in r["objects"]:
        print(f"  {o['object']:30s} part {o['part_g']:8.2f} g   support {o['support_g']:7.2f} g ({o['support_pct']} %)")
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
