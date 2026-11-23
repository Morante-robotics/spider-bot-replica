"""Interior of cad/robot (plan.json): merges the drive (drive.py) and the power parts (power.py), each written by its
own designer. A module that is missing is skipped and said. Each module exposes write_all() and PARTS {name: fn}."""
import importlib

MODULES = ("drive", "power")


def loaded():
    out = []
    for m in MODULES:
        try:
            out.append(importlib.import_module(m))
        except ImportError:
            print(f"{m}.py missing: skipped")
    return out


def write_all():
    for m in loaded():
        m.write_all()
