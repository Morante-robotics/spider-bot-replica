"""Power parts' cad_verify spec, merged into verify.py by interior_verify.py (plan.json: cell-holder, cell-lid, ag13-cells,
ss12d00-switch, leds, jst-xh; contacts and the holder M3 as hardware). Nothing here moves: no poses_interior.
Entries naming a drive part (motor-u, journal-cap) are added only when drive_verify.py exists."""
import os, sys, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from cad import fits
from cad_verify import tool
import power as PW

DRIVE = importlib.util.find_spec("drive_verify") is not None
HW = {"ag13-cells": "6 x pila AG13 / LR44", "cell-springs": "3 x muelle conico 7 mm", "nickel-strip": "tira de niquel 0.3",
      "holder-screw": "M3×10 Allen", "ss12d00-switch": "interruptor SS12D00G3", "leds": "2 x LED 5 mm + resistencia",
      "jst-xh": "JST-XH 3 pines (pareja)"}
HW_EN = {"ag13-cells": "6 x AG13 / LR44 cell", "cell-springs": "3 x conical spring 7 mm", "nickel-strip": "nickel strip 0.3",
         "holder-screw": "M3×10 socket head", "ss12d00-switch": "SS12D00G3 switch", "leds": "2 x 5 mm LED + resistor",
         "jst-xh": "JST-XH 3-pin (pair)"}          # the English kit (tools/workshop_kit.py --lang en)
GLUED = ("leds", "jst-xh", "ss12d00-switch")          # held by a drop of glue (Morante 2026-11-23: lax on small non-critical fits): not retention-checked
PARTS = {"cell-holder": {"stl": "out/cell-holder.stl"}, "cell-lid": {"stl": "out/cell-lid.stl"},
         **{n: {"stl": f"out/{n}.stl", "hardware": True, "label": l, "label_en": HW_EN[n], **({"fixed": True} if n in GLUED else {})} for n, l in HW.items()}}
PAIR_GAP = {("ag13-cells", "cell-holder"): fits.STEEL.side - 0.01, ("cell-holder", "cell-springs"): fits.STEEL.side - 0.01,
            ("ag13-cells", "cell-lid"): fits.STEEL.side - 0.01,
            ("cell-holder", "nickel-strip"): fits.STEEL.side - 0.01, ("holder-screw", "journal-cap"): fits.STEEL.side - 0.01, ("cell-lid", "nickel-strip"): fits.STEEL.side - 0.01}   # bought parts in printed seats: STEEL a side is the design gap

RETAIN = {"cell-holder": {"spin": None, "slide": None, "play": 0.6},     # M3 through the tab into ear 2, post on the journal-cap (F)
          "cell-lid": {"spin": None, "slide": None, "play": 0.6},        # 4 snap lips (LOCATOR 0.2 a side), key in the back notch
          "ag13-cells": {"spin": [0, 1, 0], "slide": None, "play": 0.6},  # cradle (STEEL), lid, spring vs strip; free to spin on their axis
          "cell-springs": {"spin": [0, 1, 0], "slide": None, "play": 0.6},    # between the front wall and the cells
          "nickel-strip": {"spin": None, "slide": None, "play": 0.6},    # between the cells and the back wall
          "holder-screw": {"spin": [0, 0, 1], "slide": [0, 0, 1], "play": 0.6},   # threaded into drive block 2 / ear 2
          "ss12d00-switch": {"spin": None, "slide": None, "play": 0.6},  # lever slot + keeper in the body; glued (Morante 2026-11-23)
          "leds": {"spin": None, "slide": None, "play": 0.6},            # dome on the bore mouth (+y keeper: open decision)
          "jst-xh": {"spin": None, "slide": None, "play": 1.0}}          # on the lid, hangs on its wires (open decision)
ALLOWED_CONTACT = {("cell-lid", "cell-holder"): "lid plate rests on the wall tops; lips snap in the grooves (PRESS, coupon)",
                   ("cell-springs", "ag13-cells"): "spring pressed on the front cell (the contact)",
                   ("nickel-strip", "ag13-cells"): "strip on the back cells' + faces (the contact)",
                   ("holder-screw", "cell-holder"): "M3 head clamps the tab",
                   ("cell-lid", "jst-xh"): "the JST pair stands on the lid, glued (drop of glue)"}
JOINTS = {("cell-lid", "cell-holder"): {"fit": fits.PRESS, "why": "lid-on-holder: snap lips, LOCATOR 0.2 lips / 0.2 key (plan)"},
          ("ag13-cells", "cell-holder"): {"fit": fits.STEEL, "why": "cells in their cradles (bought part in a printed seat)"}}
if DRIVE:
    ALLOWED_CONTACT.update({("cell-holder", "motor-u"): "tab rests on the motor-u's ear 2 (plan holder-on-cap)",
                            ("cell-holder", "journal-cap"): "post on the cap top (plan holder-on-cap, F)",
                            ("holder-screw", "motor-u"): "M3 self-tapping into ear 2 (pilot 2.5, coupon c2)"})
    JOINTS[("holder-screw", "journal-cap")] = {"fit": fits.STEEL, "why": "M3 tip through the cap's hole"}

UP = [0, 0, 1]
import drive as _DR
_DY = _DR.UY1 + fits.NEIGHBOUR.side - (PW.HSYY - PW.TABHW) + 0.3         # tab's front edge clear of the U's +y wall
_DZ = 0.3                                                                   # tab 0.3 over ear 2, under the U floor (UZ0 - tab top 0.83)
HOLDER_PATH = [[0, 0, -30.0], [0, -_DY, 0], [0, 0, -_DZ]]   # lowered with its tab behind the U, slid toward -y under the U floor, set on ear 2
ASSEMBLY = [("cell-holder", HOLDER_PATH, {"step": 14, "note": "lowered with its tab behind the U, slid in under the U floor, set on ear 2 and the cap"}),
            ("holder-screw", UP, {"step": 14, "except": {"motor-u": "self-tapping M3 in its pilot Ø2.5 (plan m3-screws, assumed, coupon c2)"}}),   # M3 down through the tab and the U's key hole
            ("nickel-strip", UP, {"step": 19}),              # contact (wired) before the cells
            ("cell-springs", [[0, 0, -30.0], [0, -2.0, 0]], {"step": 19, "note": "dropped into the cradle, then pushed 2 mm into the front wall's socket (its top bridge is 0.2 over the cone)"}),
            ("ag13-cells", UP, {"step": 19}),                # + toward the strip
            ("cell-lid", UP, {"step": 20, "except": {"cell-holder": "the lid's snap lips flex into the holder's grooves (fits.PRESS, coupon c1)"}}),
            ("jst-xh", UP, {"step": 21}),
            ("leds", [[0, 0, 10.0], [0, -12.0, 0]], {"step": 22, "bench": ["body"], "note": "bench: into the body's eye bores from inside, before the body goes on"}),
            ("ss12d00-switch", [0, -1, 0], {"step": 23, "bench": ["body"], "note": "bench: lever out the back, in from the front against the keeper, a drop of glue (Morante 2026-11-23), before the body goes on"})]
ACCESS = [{"at": "holder-screw", "tool": tool("hex-key", [0, PW.HSYY, PW.BZ + PW.M3_HEAD_H], UP), "why": "2.5 mm hex key from above, through the U's key hole (motor not in yet)"},
          {"at": "nickel-strip", "tool": tool("finger", [0, PW.YBI - fits.STEEL.side - PW.STRIP_T / 2, PW.ZT - 0.25], UP, d=1.0, reach=30.0), "why": "tweezers tip (Ø1) on the strip's top edge, down into its slot"},
          {"at": "cell-springs", "tool": tool("finger", [0, PW.YFI + fits.STEEL.side + 3.0, PW.CZ + PW.SPR_R0], UP, d=3.0, reach=30.0), "why": "fingertip (Ø3) on the middle spring, pressed against the front wall"},
          {"at": "leds", "tool": tool("finger", [PW.led_axis(1)[0], PW.led_axis(1)[1] + PW.LED_H, PW.led_axis(1)[2]], [0, 1, 0], d=5.0, reach=30.0), "why": "fingertip on the LED's back, pushed forward into its bore"},
          {"at": "ss12d00-switch", "tool": tool("finger", [0, PW.SWY1 - PW.SW_BODY[1], PW.SWZ], [0, -1, 0], d=4.0, reach=15.0), "why": "fingertip on the switch body, pushed back until the lever stands out"},
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
           {"what": "tab hole Ø (M3 + STEEL)", "point": [0, PW.HSYY, PW.ZTB], "normal": [0, 0, 1],
            "from": [-PW.HOLE_R, PW.HSYY, PW.ZTB + 0.6], "to": [PW.HOLE_R, PW.HSYY, PW.ZTB + 0.6], "nominal": round(2 * PW.HOLE_R, 2), "tol": 0.1, "tool": "caliper"}]
