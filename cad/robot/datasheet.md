# Robot datasheet

Numbers and paths that describe the robot's design as it stands. The story is in the build log
([Looks first](../../build-log/4-looks-first.md)); what is left is in [Open items](../../build-log.md#open-items).

## State 2026-11-26 (start here)

**Morante's decision (2026-11-26), answering the open decision of 2026-11-24:** make the mechanism printable by
**thickening its parts in place (same layout), plus simplifications A and B**. No calibration coupons: the measured
values of the first design (archive tag `pre-redesign-2026-11-17`: clearance test, test leg v2, gear train v2) are
used instead. **Re-laying the inside is the last option; a larger scale only after this, if it does not fit, and
only his call.** Option C (one-way keys) and D (motor held by the base) were declined: D would make the pinion's
centre distance depend on two parts; its gain (no slide-in pinion grooves) goes into A.

| | Change | Source of the number |
|---|---|---|
| Thicken | walls and plates 1.2 → **2.0** | fork side wall 2.0, test leg v2 (measurements.csv 2026-11-11) |
| | gears module 0.6 → **1.0**, idler teeth re-derived by `_zfor` | gear train v2 turned at module 1 (2026-11-12); its tip room and backlash from the archive tag's `cad/gear-train-test/` |
| | crank journals Ø3 → **Ø4**, `TURN` 0.25 | crankshaft journal 4.0 printed 3.9–4.0; `TURN` measured |
| | M2 → **M3** everywhere (holes `STEEL` on Ø3.3) | clearance test, M3 column (2026-11-11); M3 self-tap pilots from the same block, else `assumed` |
| | marks: dots → **engraved numbers ≈ 3 mm high** | not measured; the only new assumption |
| A | drive unit split into **3 flat parts screwed with M3**: (1) motor U open on top, closed by a flat strap with 2 M3, on the same part as the transfer axle (centre distance on one part; motor and pinion go in from above, no pinion grooves); (2) one flat cap over the journal slots (replaces tongues, blocks, ears); (3) the transfer cheek. Each prints flat, no support | Morante: the central part is hard to print and assemble |
| B | idlers and transfer turn on **steel pins or M3 shanks**: no printed sleeves (sleeve-1..3, transfer-sleeve go) | `STEEL` measured on M3 |

Rules for this step: crank centres, leg motion (`cad/motion.py`) and the carcass stay; legs and shells change only
where the bigger gears or pins need it, and the looks judge then says if they still pass. When something collides,
report «cabe sin X» with the gap, never a scale number. A new mechanism layout is a PLAN: `cad-designer` (Opus),
then the design-reviewer's PLAN gate, then Morante with the diagram before any code.

**Next session, in order:**
1. ~~Coordinator, no agent: minimum checks~~ **done 2026-11-26**: `cad_verify` check **13 minimums** (spec
   `MINIMUMS`, `GEAR_GEOM`, `MARK_GEOM`; `drive_verify.py` lists the drive's printed parts). All read from the meshes:
   module from each gear's section (teeth counted, tip radius), walls by ray thickness outside the teeth and the
   marks' cuts (FAIL over 1 % of the surface under 2.0), each mark cutter cut from its part with every body ≥ 3 mm
   long. Current design: 28 FAIL, all here (module 0.60 on all 10 gears, dots 0.9–1.1 mm, walls: spine 0.56,
   drive unit 0.29, idler rims 0.98, sleeves 0.80); synthetic plan sizes (module 1.0, 2.0 plate with M3 holes, digit
   3 × 0.6) pass (`tools/tests/test_cad_verify.py`, 74 passed). The plan's design must declare `GEAR_GEOM` for every
   gear, export each engraving's cutter as `out/<part>-marks.stl` into `MARK_GEOM` (None with the MARKS reason when a
   part needs no mark), and give any deliberately thin feature (a flexing snap) as a `MINIMUMS["except"]` box with
   its reason.
2. `cad-designer` · opus (≈ 200–400k, 20–30 min): `plan.json` for the change above, `rounds.py validate` PASS, PLAN
   with the collision list. 3. `design-reviewer` PLAN gate. 4. Morante: diagram, acceptance table, questions.

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
