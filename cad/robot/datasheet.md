# Robot datasheet

Numbers and paths that describe the robot's design as it stands. The story is in the build log
([Looks first](../../build-log/4-looks-first.md)); what is left is in [Open items](../../build-log.md#open-items).

## State 2026-11-26, top-down plan (start here)

Batch 1 failed because the mechanism is too small to print at S 0.70 (faults below, 2026-11-24). Two probe agents then
tried to thicken in place and bisect a scale part by part (≈ 270k tokens, FAIL: no number). Morante stopped that:
«falta razonamiento espacial y te centras en solucionar problemas pequeños antes de saber qué tenemos que hacer. Yo
quiero una aproximación Top-down». The work goes in three phases, each closed by his call on a picture; no phase starts
before the one above is validated, and no local fix is worked before phase 3.

**Phase 1, size: how much must the robot grow?** (coordinator, no agent)
1. Printable minimum per feature type, only from what was printed and measured (archive tag `pre-redesign-2026-11-17`):

   | Feature | Now (S 0.70) | Measured minimum | Factor | Source |
   |---|---|---|---|---|
   | gear module | 0.6 | 1.0 | ×1.67 | gear train v2 turned at module 1 (2026-11-12) |
   | wall / plate | 1.2 (spine 0.56, drive unit 0.29, idler rims 0.98) | 2.0 | ×1.67 | fork side wall, test leg v2 (measurements.csv 2026-11-11) |
   | crank journal | Ø3 | Ø4, `TURN` 0.25 | ×1.33 | crankshaft journal 4.0 printed 3.9–4.0 |
   | screw | M2 (Ø2.3 holes, never measured) | M3, `STEEL` on Ø3.3 | ×1.5 | clearance test, M3 column (2026-11-11) |
   | mark | dots Ø0.7 × 0.35 | engraved numbers ≈ 3 mm | new type | not measured: the only assumption |

2. Split what scales (printed parts) from what does not (N10 motor, AG13 cells, switch, screws, fit clearances
   0.1–0.4 mm): a larger S gives the bought parts room.
3. Range of S (fraction of jenscolt's size): pure scaling to the minimums gives 0.70 × 1.67 ≈ **1.17**; scaling less
   and thickening in place, the scale probe pointed at ≈ 1.0–1.05 (crank 4 against the back shell was its only
   scale-bound gap). Estimate to be confirmed by this phase, not a result.
4. Morante: the robot at 0.70, 1.0 and 1.17 next to jenscolt, with the motor, the cells and one smallest part of each
   type at true size. He picks the target S (± 0.05). It does not yet promise a fit: phase 2 checks that.

**Phase 2, motion: where does everything go so the whole mechanism turns?**
1. Scale the whole robot to the chosen S and apply the minimums; every fit tweak made at 0.70 is deleted (D23/D23C,
   arm pockets, reliefs, x-stop posts, spacings).
2. Spatial reasoning before modelling: side and top sections with the swept volume of each moving part over a turn
   (legs, cranks, gears) and where the motor and cells go.
3. Collisions are solved by large layout moves (motor place, crank spread, gear train route), not sub-mm reliefs.
4. Done when the whole mechanism runs the 24 poses with no collision, every part counted, at N1 (1 mm).
5. Morante: animation and sections. Agent: `cad-designer` · opus for the layout PLAN (≈ 200k), one N1 check.

**Phase 3, simplify: what can go, and how?**
1. Count parts, screws, assembly steps, supported parts.
2. Proposals with their gain, e.g. fewer gears, merged parts, and the two already approved (2026-11-26):
   **A** drive unit as 3 flat parts screwed with M3 (motor U closed by a strap on the same part as the transfer axle;
   one flat journal cap; the transfer cheek), **B** idlers and transfer on steel pins or M3 shanks, no printed sleeves.
   Declined: C (one-way keys), D (motor held by the base: pinion centre distance on two parts).
3. Morante picks. Only then the local work: fits, retention, marks, the N2 `cad_verify`, coupons, the print.

**Kept from earlier work:** `cad_verify` check **13 minimums** (commit `69c342b`; spec `MINIMUMS`, `GEAR_GEOM`,
`MARK_GEOM`): module, walls and marks read from the meshes; the 0.70 design fails it 28 times. It is phase 1's measure
of «now» and phase 3's gate. A design must declare `GEAR_GEOM` for every gear, export each engraving's cutter as
`out/<part>-marks.stl` into `MARK_GEOM`, and give a deliberately thin feature as a `MINIMUMS["except"]` box with its
reason. Morante's answer «1.a» (module 1.0 at 9 T) stands as the minimum; tooth counts, the leg end tubes («2.a») and
the motor place are re-derived in phase 2. The scale probe's scripts and box list (`probe2.py`, `boxes.csv`,
`out_<S>.json`) are in the session scratchpad of 2026-11-26 (may be cleared); its partial results are not a size.
`plan.json` / `design-plan.md` are still the 0.70 design's; phase 2 rewrites them.

## State 2026-11-24

Batch 1 (blue base, yellow inner plate, leg-3) was printed and assembled: **it fails as a robot**
([Batch 1 result](../../build-log/4-looks-first.md#batch-1-result-the-mechanism-is-not-printable-at-this-size)).
Before that, two fixes went in: drive unit plates 2.0 mm (`DU_W`), printed −90° about X (`7c37dfb`); leg tube
closed at its tip with the Ø4.7 rod fused to it (`SNAP_WALL`, `JOINT_R`) and the `SECTION_MIN` check 9b in
`cad_verify` (`1fb1b20`). Full `verify.py`: PASS, 0 FAIL.

Morante's five faults, each with the design number behind it:

| Fault | Design number | Status of the fit |
|---|---|---|
| No mark can be seen | dots `Sphere(0.35)` at 1.0 pitch (`common.dice`): Ø0.7 × 0.35 deep, under one 0.4 line | — |
| Parts come out wrong | gears module `M = 0.6` (12/15/16/20 teeth): tooth ≈ 0.94 mm, two lines | — |
| Parts snap when touched | walls `W = 1.2` (3 lines); drive unit ear 2 `EARH2` 1.0 high (the «orejeras») | — |
| No gear turns | `GEAR_TIP` 0.4 radial | assumed, never on a coupon |
| No screw or pin goes in | M2 holes Ø2.3 (`STEEL` 0.15, measured on M3/Ø3.3 only), pilots Ø1.6; X-Y hole compensation never calibrated | assumed |

**Decision asked 2026-11-24 (answered 2026-11-26, above):** how to make the mechanism printable. Options, none
dropped: (1) **calibration coupons first**, recommended and needed by every other option: one
plate ≈ 20–30 min with M2 holes and pilots in 0.1 steps, pin/sleeve fits, gear pairs at module 0.6/0.8/1.0 and two
tip clearances, mark samples (dots and engraved numbers of several sizes), walls 1.2/1.6/2.0; the measured values go
into `cad/fits.py`; (2) a larger scale (no number until code counts every part); (3) same
scale with printable minimums (module ≥ 0.8, walls 1.6–2.0, big numbers as marks), likely does not fit inside;
(4) a 0.2 mm nozzle for the P2S (a purchase, 2–3× slower, not stronger); (5) a simpler mechanism (fewer, larger
parts, e.g. one crankshaft + side bars). Whatever he picks, the faults above become `cad_verify` checks (smallest
printed feature, gear module, mark size) so a design cannot pass with them again.


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

**Walking direction, 2026-11-24.** The robot walks forward (−y) with the crank pose falling (k 23, 22, …): with k rising, the feet in stance move toward −y and the robot walks backward (Morante saw it in the viewer). The viewer's Walk and the GIF run the poses backward; the motor's polarity in the kit must turn the cranks that way.

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
