# Robot datasheet

Numbers and paths that describe the robot's design as it stands. The story is in the build log
([Looks first](../../build-log/4-looks-first.md)); what is left is in [Open items](../../build-log.md#open-items).

## State 2026-11-23

N2 round r00 of `cad/robot` at scale 0.70. **Full `verify.py` of the whole robot: PASS, 0 FAIL, in ≈ 80 s (+ 15 s renders; `verify-result.txt`).** `--quick`
(PARTIAL: retention at the first step only): 37–39 s.

**Speed plan done (night 2026-11-23, branch `speed/designed-cutters`).** Any build or check over 40 s is a bug
(Morante); `build.py` runs under the `tools/timebudget.py` watchdog (`CAD_BUDGET`, default 40 s).

| What | Before | Now |
|---|---|---|
| base build | 1669 s | 22 s (skin cached; 28 s cold) |
| body build | ≈ 3500 s | 28 s (fixed stage cached; 40 s when cad/body, cad/eyes or power.py change) |
| `cad_verify verify.py --quick`, whole robot | 70 s, 5 FAIL | 37 s, 0 FAIL |
| `cad_verify verify.py` (full), whole robot | not run | ≈ 80 s, 0 FAIL (retention 45 s: over the 40 s rule, open) |
| body.step | 152 MB | a few MB |

How (rules in `cad/README.md` «Time budget»):
- **Designed cutters** (`cutters.py`): each leg's base window is one few-sided prism, its outline the wall samples the
  leg comes within WR of (24 poses and its assembly slide), seen along the wall normal, open to the top; wall left
  narrower than 4 lines between two windows joins the first one. The body has a notch from the rim per leg (24 poses
  and the body put on at pose 12) and a shallow pocket where a leg nears a face below the rim (the rear tab, legs 3/7).
  One fuse and one cut per shell; `leg_gaps` / `body_gaps` (manifold3d) check every leg inside the build.
- Morante's decisions (comparison sheets): windows as designed (1); **smooth base front, no relief** for legs 0/4,
  the arms clear it by 0.40 (2); body notches, tab pocket and frozen x-stop posts (3).
- **No 1.2 pads** round the windows: open-top windows carry no load (the leg is held by its pin); wall 0.84.
- **Back pocket is a cup** (side walls of the wall's thickness): the bare sheet moved 1.6 out came loose.
- **Assembly**: legs 1, 2, 4–7 at crank pose 0, then half a turn (pose 12) for legs 0 and 3 and the body
  (`cutters.ASM_POSE`; `cad_verify` takes `"at"` per ASSEMBLY step).
- **Leg play**: the corner legs 0, 3, 4, 7 slide up to 1.40–1.50 mm towards their crank (0/7 near pose 0, 4 at pose
  10, 3 at pose 12; measured at all 24 poses: only the groove stops them): accepted by Morante (`RETAIN` play 1.65);
  outward every leg stays ≤ 1.15 mm. The full check's retention samples poses 0, 8, 16 only.
- **x-stop posts frozen** (`XS_POSTS`: legs 0 and 3, and mirrors; none fits 1 and 2); `xstop_post` is re-run by hand
  only if the legs or the body wall move (60–100 s a leg).
- Switch keeper's top bar no longer overhangs the switch (the fingertip touched it). Power pockets are the parts'
  bounding boxes + LOCATOR, not offsets.
- `fitcheck/check.py` (19 min) is the pre-CAD planner, not a gate.

**Body front, 2026-11-24.** jenscolt's front sensor (ball on a stem) is not placed (`eye_cups()`, `body_static()` in
`shells.py`; `cad/eyes` still builds it). `front_panel()` closes the mouth at the front face: 1.2 mm (`PANEL_T`), x ±18,
z ≈ 13.2–27.3, flush with the skin, 0.2 mm above the base's front top (`PANEL_GAP` = `fits.LOCATOR`); it hides the two
front snap fingers (x ±6, 0.8 x 5, flex L 8) with ≈ 1.7 mm free in front of them. Body: 1 valid solid, 35 416 mm³;
leg gaps ≥ 0.53, lift ≥ 0.55; full check PASS, 0 FAIL, 95 WARN. `cad/body/build.py` unchanged.

**Next**
1. `rounds.py round cad/robot 0`, the looks judge, Morante's «se parece».
2. Workshop kit: the crank half-turn before legs 0 and 3 and the body; the glued switch.

**Known issues**

- The leg snap's radial engagement is 0.08-0.18 mm (`fits.PRESS`); a coupon is planned in the robot batch.
- The r00 build-log entry is updated when r00 closes.
