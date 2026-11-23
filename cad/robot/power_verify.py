"""Power parts' cad_verify spec, merged into verify.py by interior_verify.py (plan.json: cell-holder, cell-lid, ag13-cells,
ss12d00-switch, leds, jst-xh; contacts and the holder M2 as hardware). Nothing here moves: no poses_interior.
Entries naming a drive part (drive-unit, spine) are added only when drive_verify.py exists."""
import os, sys, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from cad import fits
from cad_verify import tool
import power as PW

DRIVE = importlib.util.find_spec("drive_verify") is not None
HW = {"ag13-cells": "6 x pila AG13 / LR44", "cell-springs": "3 x muelle conico 7 mm", "nickel-strip": "tira de niquel 0.3",
      "holder-screw": "M2x6 Allen", "ss12d00-switch": "interruptor SS12D00G3", "leds": "2 x LED 5 mm + resistencia",
      "jst-xh": "JST-XH 3 pines (pareja)"}
GLUED = ("leds", "jst-xh")          # held by a drop of glue (Morante 2026-11-23: lax on small non-critical fits): not retention-checked
PARTS = {"cell-holder": {"stl": "out/cell-holder.stl"}, "cell-lid": {"stl": "out/cell-lid.stl"},
         **{n: {"stl": f"out/{n}.stl", "hardware": True, "label": l, **({"fixed": True} if n in GLUED else {})} for n, l in HW.items()}}
PAIR_GAP = {("ag13-cells", "cell-holder"): fits.STEEL.side - 0.01, ("cell-holder", "cell-springs"): fits.STEEL.side - 0.01,
            ("ag13-cells", "cell-lid"): fits.STEEL.side - 0.01,
            ("cell-holder", "nickel-strip"): fits.STEEL.side - 0.01, ("cell-lid", "nickel-strip"): fits.STEEL.side - 0.01}   # bought parts in printed seats: STEEL a side is the design gap

RETAIN = {"cell-holder": {"spin": None, "slide": None, "play": 0.6},     # M2 through the tab, tongues in slot 4, post on the walls
          "cell-lid": {"spin": None, "slide": None, "play": 0.6},        # 4 snap lips (LOCATOR 0.2 a side), key in the back notch
          "ag13-cells": {"spin": [0, 1, 0], "slide": None, "play": 0.6},  # cradle (STEEL), lid, spring vs strip; free to spin on their axis
          "cell-springs": {"spin": [0, 1, 0], "slide": None, "play": 0.6},    # between the front wall and the cells
          "nickel-strip": {"spin": None, "slide": None, "play": 0.6},    # between the cells and the back wall
          "holder-screw": {"spin": [0, 0, 1], "slide": None, "play": 0.6},   # threaded into drive block 2 / ear 2
          "ss12d00-switch": {"spin": None, "slide": None, "play": 0.6},  # lever slot + keeper in the body (open decision)
          "leds": {"spin": None, "slide": None, "play": 0.6},            # dome on the bore mouth (+y keeper: open decision)
          "jst-xh": {"spin": None, "slide": None, "play": 1.0}}          # on the lid, hangs on its wires (open decision)
ALLOWED_CONTACT = {("cell-lid", "cell-holder"): "lid plate rests on the wall tops; lips snap in the grooves (PRESS, coupon)",
                   ("cell-springs", "ag13-cells"): "spring pressed on the front cell (the contact)",
                   ("nickel-strip", "ag13-cells"): "strip on the back cells' + faces (the contact)",
                   ("holder-screw", "cell-holder"): "M2 head clamps the tab",
                   ("cell-lid", "jst-xh"): "the JST pair stands on the lid, glued (drop of glue)"}
JOINTS = {("cell-lid", "cell-holder"): {"fit": fits.PRESS, "why": "lid-on-holder: snap lips, LOCATOR 0.2 lips / 0.2 key (plan)"},
          ("ag13-cells", "cell-holder"): {"fit": fits.STEEL, "why": "cells in their cradles (bought part in a printed seat)"}}
if DRIVE:
    ALLOWED_CONTACT.update({("cell-holder", "drive-unit"): "tab rests on drive ear 2 (plan holder-on-drive-block)",
                            ("cell-holder", "spine"): "post on the raised wall tops, tongues in slot 4 (plan)",
                            ("holder-screw", "drive-unit"): "M2 self-tapping into drive block 2 / ear 2 (pilot 1.6, coupon c2)"})
    JOINTS[("cell-holder", "crank-4")] = {"fit": fits.TURN, "why": "crank-in-spine: post-cap tongue over journal 4 (TURN)"}

UP = [0, 0, 1]
ASSEMBLY = [("cell-holder", UP, {"step": 10}),               # plan step 10, before the motor
            ("holder-screw", UP, {"step": 10}),              # M2 down through the tab, clamp empty
            ("nickel-strip", UP, {"step": 13}), ("cell-springs", UP, {"step": 13}),   # contacts (wired) before the cells
            ("ag13-cells", UP, {"step": 13}),                # + toward the strip
            ("cell-lid", UP, {"step": 14}),
            ("jst-xh", UP, {"step": 15}),
            ("leds", [0, 1, 0], {"step": 16}),               # into the body from inside
            ("ss12d00-switch", [0, -1, 0], {"step": 17})]    # lever out the back
ACCESS = [{"at": "holder-screw", "tool": tool("hex-key", [0, PW.HSYY, PW.BZ + PW.M2_HEAD_H], UP), "why": "1.5 mm hex key from above, clamp empty"},
          {"at": "ag13-cells", "tool": tool("finger", [0, PW.CYC, PW.ZT], UP, d=10.0, reach=30.0), "why": "cells pressed down against the spring"},
          {"at": "cell-lid", "tool": tool("finger", [0, PW.CY, PW.ZT + PW.LIDT], UP, reach=30.0), "why": "lid pressed shut; lifted by its back lips"},
          {"at": "jst-xh", "tool": tool("finger", [PW.CL.JX, PW.CL.JY, PW.JZ + PW.JST[2] / 2], UP, d=10.0, reach=30.0), "why": "latched by hand"}]
PRINT_ORIENT = {"cell-holder": np.array([[1.0, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]),  # on its back wall: cradles, tab,
                                                                       # post and tongues print vertical, no support under the post
                "cell-lid": np.diag([1.0, -1.0, -1.0, 1.0])}           # plate on the bed, lips up (180 deg about x)
MARKS = {"cell-lid": "keyed: back lips over the back wall, key in the back notch (goes on one way)",
         "ag13-cells": "+ face toward the nickel strip (back); '+' engraved on the holder's back wall"}
LABELS = {"es": {"cell-holder": "portapilas", "cell-lid": "tapa del portapilas", **{n: l for n, l in HW.items()}}}
MEASURE = [{"what": "cradle Ø (cell + 0.15 a side)", "point": [0, PW.CY, PW.CZ], "normal": [0, 1, 0],
            "from": [-PW.PD / 2, PW.CY, PW.CZ], "to": [PW.PD / 2, PW.CY, PW.CZ], "nominal": round(PW.PD, 2), "tol": 0.1, "tool": "caliper"},
           {"what": "tab hole Ø (M2 + STEEL)", "point": [0, PW.HSYY, PW.ZTB], "normal": [0, 0, 1],
            "from": [-PW.HOLE_R, PW.HSYY, PW.ZTB + 0.6], "to": [PW.HOLE_R, PW.HSYY, PW.ZTB + 0.6], "nominal": round(2 * PW.HOLE_R, 2), "tol": 0.1, "tool": "caliper"},
           {"what": "post-cap tongue width (slot 4 - TURN)", "point": [PW.D["wx1"], PW.OY4, PW.ZTG + 1], "normal": [1, 0, 0],
            "from": [PW.D["wx1"], PW.OY4 - PW.TG, PW.ZTG + 1], "to": [PW.D["wx1"], PW.OY4 + PW.TG, PW.ZTG + 1], "nominal": round(2 * PW.TG, 2), "tol": 0.1, "tool": "caliper"}]
