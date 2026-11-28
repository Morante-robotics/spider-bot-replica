# Robot datasheet

The robot as it stands (branch `phase3-s1`): status, where each topic lives, the commands. Every number is read from
the file named next to it. How it got here: [Top-down redesign, phases 1–3](../../build-log/4-looks-first.md#top-down-redesign-phase-1-size-s-10) and
[the leg ↔ crank joint](../../build-log/4-looks-first.md#top-down-redesign-phase-3-simplify-and-the-leg-joint). What is left: [Open items](../../build-log.md#open-items).

## 0. Where we stopped (2026-11-28, start here)

Pipeline step 10–11 (plates and pre-print review). Done on 2026-11-28 (commit `f523368` and the working tree after it):

- Mouth closed again: at S 1.0 `front_panel()`'s clip box was still the S 0.70 one and the panel came out empty; the
  box now follows the skin. New `cad_verify` check **14 closed** (`CLOSED` in `verify.py`: body + base over the mouth;
  seams under `COARSE` are not holes): FAILs on the open body, PASS now.
- Full check after it: **PASS, 0 FAIL, 92 WARN**, only with `--jobs 1` (the default second process does not finish:
  «retention, print … did not finish»).
- Coupons (`cad/coupons/`, 12): c1/c7 lying like the legs, c9 0.40/0.50/0.60, c11 body–base snap, c12 lid lips (its
  bump was extruded the wrong way, fixed in `_prism_x`). A c13 for the body–base rim was built and dropped: the joint
  is the snap (c11) with the rim resting on the ledge, so c13 only repeated c8.
- Plates (`print/README.md`): coupons; red body, red legs 0–3, red legs 4–7; yellow inner; **yellow motor** (pinion,
  motor-u, transfer-cheek: printed only after the N10 arrives and c2/c10 are measured); blue base. The 0.70 red plate
  is gone.
- Pre-print review: **CHANGES**. Done: keel screw M3×5 in `plan.json`, c9 steps, yellow split. Left, both need a
  design change:
  1. **Spine**: 3 upright stubs ≈ 2.0 × 2.2 mm, 10.8 mm tall (verify «upright feature thinner than Ø4», z 15–25.8 at
     [±3.4, 28.4], [−3.4, −31.3]) break along the layers. Lying on a side (`@0,±90,0`) puts 42 % support on the
     journal slots' inner walls, so the orientation stays slots-up and the stubs must grow (Ø4-equivalent) or go.
  2. **Base** (`@−90,0,0`, 30 % support): the support touches the front snap ribs, the rim/ledge the body rests on and
     the back-sheet cup; the other orientations put it in the keel boss pockets.

  Next: one measure-only probe for both (what each stub holds and how far it can grow over the 24 poses; which rib face
  is the hook's catch face; ledge = resting contact?), ranked options with renders, Morante picks once, one fixer,
  rebuild, full check (`--jobs 1`), re-slice yellow inner and base. A first probe was stopped before it returned.
- Workshop kit `kits/02-s1-coupons-and-plates/`: written, not sent to Morante. Before sending: Spanish words
  (probetas, pata, pasador: not «cupones», «pierna», «pin»), 12 coupons without c13, c9 steps, the yellow split, the
  spine and base changes, the screws the coupons need (from the order), total 11 h 19 for the robot plates.
- Not written yet: the build-log entry for 2026-11-28 (mouth, check 14, coupons, plates, review).

## 1. Scale and minimums

Scale **S 1.0** (`spec.json` `S_start`; Morante: «S 1.0 máximo»): jenscolt's size (225 mm across the legs, not in code). Below 1.0 the
crank gear falls under 9 T. Printable minimums, measured on prints (`fits.py`, `measurements.csv`), checked by
`cad_verify` check 13 (`MINIMUMS`, `GEAR_GEOM`, `MARK_GEOM` in `verify.py`):

| Feature | Minimum | Where |
|---|---|---|
| gear module | 1.0 | `fits.MODULE_MIN` |
| wall / plate | 2.0 | `fits.WALL_MIN`, `drive.DU_W` |
| crank journal / turning fit | Ø4 journal, `TURN` 0.25 a side | `fits.TURN` |
| screw | M3 in Ø3.3 holes, `STEEL` 0.15 a side | `fits.STEEL` |
| mark | engraved number, 3 mm | `MINIMUMS["mark"]` |

Other fits: `LEG_PATH` 0.5 (moving leg to anything), `LEG_OPEN` 0.4, `WINDOW` 0.5, `GEAR_AXIAL` 0.8; `PRESS` (snap)
and `GEAR_TIP` are still `assumed` (never on a coupon).

## 2. Parts

- **Gears** (`drive.py`): module 1.0; crank and idlers 10 T, pinion 14 T, transfer 17 / 13 T. The crank turns 1.07 per
  pinion turn (`RATIO`). Pitch diameters are the S 0.70 ones (comment in `drive.py`).
- **Motor**: N10 07 type, 100:1, 3 V, Ø3 shaft (`hardware.md`; modelled 12 × 10 × 21 mm, `N10_*`). Torque need ≈ 0.09 kg·cm
  at the cranks (estimate in `hardware.md`; the seller's rated 0.2 kg·cm; not measured).
- **Drive unit** A + B + F: `journal-cap` (flat, also caps crank 4), `motor-u` (U closed by a strap), `transfer-cheek`;
  idlers and transfer on M3 shanks, no sleeves; the cell holder comes out without freeing crank 4.
- **Screws** (`hardware.md`): 2 × M3×5 (keel, `KEEL_LEN`), 2 × M3×10 (strap, holder), 3 × M3×10 and 1 × M3×16 ISO 7380
  button heads (axles 1–3, transfer axle). No nuts, no steel pins.
- **Counts** (`plan.json`): 13 printed rows (8 legs, 4 cranks, 3 idlers inside them), 7 hardware rows, 24 assembly steps.
  Mass: `plan.json` grams (solid volume × 1.24, 100 % infill) add to ≈ 405 g printed, of which legs 234, body 128.
- Marks: crank numbers 1–4 engraved on the +x web hub.

## 3. Leg ↔ crank joint (option D, as built)

The leg rides with its pin point on the crank pin (`leg_frame`); its end tube follows the pin's real swing cone
(`pin_cone(i)` in `shells.py`, fitted over the 24 poses; the pin tilts only towards +y).

- `CONE_TILT` 6.44 / 5.49 / 5.52 / 7.96° and `CONE_FLARE` 7.46 / 6.51 / 6.52 / 8.98° (swing + 1°) for leg classes
  0/4, 1/5, 2/6, 3/7; `BORE_R` 2.416 / 2.412 / 2.412 / 2.422; outer wall = bore + `WALL_MIN`/cos(flare).
- Closed end revolved about the tilted axis, `END_PAD` 0.05, slit stops `SLIT_END` 0.03 past the floor, slit edges
  chamfered 0.5 × 45° (`SLIT_CHAMFER`); snap groove margin `SNAP_MARGIN` = `TURN` + 0.05; body notch `NOTCH_GROW` 0.35
  (`cutters.py`), body rim `BRELD` 0.65; hub-plate rim kept to `HUBFLANGE_L/R` 5 / 6.
- Gaps (last full check): base ≥ 0.49, legs / transfer / body ≥ 0.60, `TURN` 0.25–0.26; 36 retention rows ok.
- Deliberately thin spots are `MINIMUMS["except"]` boxes in `verify.py` with measured walls: tube mouth and slit
  chamfers (exact BREP wall ≥ 1.98), snap bead. Only the end tube is asked for 2.0; the rest of the leg is jenscolt's looks.

## 4. Assembly

`cutters.ASM_POSE`: legs 1, 2, 4–7 go on at crank pose 0; then the cranks turn half a turn (pose 12) for legs 0 and 3
and the body (`"at"` in the `cad_verify` ASSEMBLY step). Forward is −y: the robot walks forward with the crank pose
falling (k 23, 22, …; the cranks turn −15° a pose, `crank_angle`), so the motor's leads must turn the cranks that way.

## 5. Check

Last full `cad_verify` (`verify-result.txt`, 2026-11-28, `--jobs 1`): **PASS, 0 FAIL, 92 WARN** (listed there).
Run from `cad/robot/` with `../../.venv/bin/python`:

| Command | What | Time last recorded |
|---|---|---|
| `build.py` | every part into `out/` (watchdog `CAD_BUDGET`) | 41–47 s cold (2026-11-26, before D) |
| `../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify` | full; add `--jobs 1` (the second process does not finish) | ≈ 4 min with `--jobs 1` (2026-11-28) |
| same with `--smoke [--only <part>]` | rest pose only | seconds (not timed) |
| same with `--quick --jobs 1` | no wall check, retention at the first step | not timed |
| `fitcheck/n1.py` | whole robot, 24 poses at 1 mm (41 parts) | 18 s (2026-11-26) |

A build or check over 60 s is a bug (`tools/timebudget.py`, `CAD_BUDGET` default 60, commit 3794e1a; `cad/README.md` «Time budget» still says 40): the full check is over it.
`fitcheck/check.py` (19 min) is the old layout planner, not a gate.

## 6. Lessons that still hold

- Rebuild `out/` (`build.py`) after switching branches and before any check: stale STLs gave false FAILs.
- One motion module: import `SH.motion` / `FE.motion`, never `cad.motion` (a second copy that fit_env had not scaled).
- Read a feature's comment before deleting it (the `END_REL` recess brought back the FAIL it was made for).
- Each check asks its pair's own fit (leg ↔ crank `TURN`, leg ↔ other `LEG_PATH`, base `LEG_OPEN`), not a blanket 0.2.

## 7. Open

- Grams: the check prints volumes only; `plan.json` grams are from volumes × 1.24 and nothing was weighed.
- Still saying M2: `cad/robot/README.md` (70 %, sleeves,
  «M2 screws»); comments and names in `shells.py`, `drive.py`,
  `power.py`. `hardware.md`, `drive_verify.py` and
  `power_verify.py` are M3 (`hardware.md` as edited in the working tree, not yet committed).
- `cad/README.md` «Time budget» says 40 s; the rule and `timebudget.py` are 60 s.
- Optimizer proposals awaiting Morante: the fork failure in `--quick`, a stale-STL guard, one motion import.
- On coupons, not printed yet: `PRESS` (c1, c11, c12), `GEAR_TIP` (c3), `DSHAFT` and `MOTOR_SEAT` (c10, c2: need the motor, not bought).
