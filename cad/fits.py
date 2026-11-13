"""Measured fits for the Spider-Bot's printed parts: the one place where clearances live.

Every `build.py` takes its clearances from here instead of typing a number, and every `verify_*.py` spec declares
its joints with these fits (`JOINTS` in `tools/cad_verify.py`), so the verifier fails any joint that is tighter than
what was measured on a real print. Base v1 (2026-11-13) failed because its cap had 0.3 mm a side typed by hand,
below the measured 0.5: that cannot happen again if the number comes from here.

The measurements behind each fit are in ../measurements.csv (one row per caliper reading or fit trial).
A fit is measured when a printed part showed it works (or showed the next smaller value fails). A fit marked
`assumed` has not been printed yet: a design that uses one needs a coupon first (cad-designer agent, «Coupons»).
When a print gives a new value, change it here, say where it was measured, and rebuild every design that uses it.

All values for Bambu PLA Basic, 0.4 mm nozzle, 0.20 mm layers, on the P2S, with the default X-Y compensation (0).

    import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # from cad/<design>/
    import fits
    bore = fits.bore(4.0, fits.TURN)          # Ø4 journal → Ø4.5 hole
    window = leg_w + 2 * fits.WINDOW.side     # 0.5 mm a side
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Fit:
    what: str          # which kind of joint this is
    side: float        # least gap on each side, in mm, with both parts at their nominal (centred) positions
    status: str        # "measured" or "assumed" (needs a coupon before a big part)
    source: str        # where it was measured, or why it is assumed

    @property
    def diametral(self):
        return 2 * self.side


TURN = Fit("printed part turning or sliding in a printed hole (journal, ball in its bore)", 0.25, "measured",
           "clearance block, 2026-11-11: +0.4 mm on the diameter turned roughly, +0.5 used since; test leg v2 and "
           "gear train v2 turned freely with it")
STEEL = Fit("steel pin or screw in a printed hole (axle, pivot, screw shank)", 0.15, "measured",
            "clearance block, 2026-11-11 (M3 into Ø3.3); test leg v2 and gear train v2")
WINDOW = Fit("printed part in a printed window, slot or opening (tongue, lid, cap, block, leg in its fork)", 0.5,
             "measured",
             "fork window 0.5 a side, test leg v2, 2026-11-11. Failed below it: base v1 cap 0.3 a side and its "
             "tongues 0.15 a side did not go in, 2026-11-13")
LOCATOR = Fit("short printed skirt or lip that centres a small part on another (≤ 40 mm long)", 0.2, "measured",
              "test cap v2.1 skirts, 2026-11-12: went on and the train turned. Not valid for long or large parts: "
              "use WINDOW there")
GEAR_AXIAL = Fit("spinning gear face to a stationary printed face, at the worst position of every loose part", 0.8,
                 "measured", "test cap v2.1, 2026-11-12 (0.25 mm jammed the train, v2 cap)")
LEG_PATH = Fit("moving leg to anything it sweeps past", 0.8, "assumed", "base v1 LEG_CLR, not printed yet")
PRESS = Fit("printed press fit or snap", 0.0, "assumed", "never printed: prove on a coupon")

# gears: backlash at the pitch circle, per mesh (gear train test v2, 2026-11-12: turned with 0.20)
GEAR_BACKLASH = 0.20
# first layers come out wider (elephant's foot): add this to a fit that sits on the bed, or chamfer the edge 0.4 mm
FIRST_LAYER = 0.2      # assumed (agent rule), not measured

ALL = {name: value for name, value in globals().items() if isinstance(value, Fit)}


def bore(d, fit):
    """Hole diameter for a part of diameter d with this fit."""
    return d + fit.diametral


def report():
    """One line per fit, for a design review or a figure."""
    return "\n".join(f"{n:11s} {f.side:.2f} mm a side  {f.status:8s}  {f.what}" for n, f in ALL.items())


if __name__ == "__main__":
    print(report())
