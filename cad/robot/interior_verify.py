"""Interior spec merged into verify.py: drive_verify.py and power_verify.py, each written by its own designer.
Each may define PARTS, poses_interior(t), RETAIN, JOINTS, MARKS, ASSEMBLY, ACCESS, PRINT_ORIENT, LABELS, MEASURE,
ALLOWED_CONTACT, MINIMUMS, GEAR_GEOM, MARK_GEOM. Missing modules are skipped."""
import importlib

PARTS, RETAIN, JOINTS, MARKS, PRINT_ORIENT, ALLOWED_CONTACT = {}, {}, {}, {}, {}, {}
LABELS, MEASURE, ACCESS, ASSEMBLY, GEARS = {"es": {}}, [], [], [], []
PAIR_GAP, KEEP_OUT, MARK_GEOM = {}, {}, {}
GEAR_GEOM, MINIMUMS = [], None
_MODS = []
for _m in ("drive_verify", "power_verify"):
    try:
        _MODS.append(importlib.import_module(_m))
    except ImportError:
        pass
for _v in _MODS:
    for _d, _n in ((PARTS, "PARTS"), (RETAIN, "RETAIN"), (JOINTS, "JOINTS"), (MARKS, "MARKS"),
                   (PRINT_ORIENT, "PRINT_ORIENT"), (ALLOWED_CONTACT, "ALLOWED_CONTACT"),
                   (PAIR_GAP, "PAIR_GAP"), (KEEP_OUT, "KEEP_OUT"), (MARK_GEOM, "MARK_GEOM")):
        _d.update(getattr(_v, _n, {}))
    LABELS["es"].update(getattr(_v, "LABELS", {}).get("es", {}))
    MEASURE += getattr(_v, "MEASURE", []); ACCESS += getattr(_v, "ACCESS", []); ASSEMBLY += getattr(_v, "ASSEMBLY", []); GEARS += getattr(_v, "GEARS", [])
    GEAR_GEOM += getattr(_v, "GEAR_GEOM", [])
    if getattr(_v, "MINIMUMS", None):                # one MINIMUMS for the interior: the parts lists joined
        MINIMUMS = dict(_v.MINIMUMS, parts=(MINIMUMS or {}).get("parts", []) + list(_v.MINIMUMS["parts"]))


def poses_interior(t):
    out = {}
    for v in _MODS:
        if hasattr(v, "poses_interior"):
            out.update(v.poses_interior(t))
    return out


ASSEMBLY.sort(key=lambda e: (e[2] if len(e) > 2 else {}).get("step", 99))   # plan.json step numbers (stable within a step)
LEGS_AFTER_STEP = 12                                 # plan step 13 (legs) goes between ASSEMBLY steps <= 12 (spine set and keel screws) and the holder (14)
