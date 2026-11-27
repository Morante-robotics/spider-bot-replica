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

**Phase 1 result (closed 2026-11-26): S = 1.0.** Measured (ray thickness, every printed STL at 0.70): legs and body
are near the minimum already (legs p10 ≈ 2.0, thin only at spots); the mechanism (gears, cranks, idlers, spine,
sleeves, median ≈ 1.0, module 0.6) and the base bowl (0.7 everywhere) are what is thin. The crank spacing is set by the
legs, so the gear train's size follows the robot's S. Pure scaling reaches every minimum only at S 1.17–1.2 (271 mm
across the legs, weight ×5, motor torque ×8.6 vs 0.70). Morante, verbatim: «S 1.0 máximo». At S 1.0 (×1.43 from 0.70)
the minimum is reached without moving the gears: **same pitch diameters, fewer teeth at module 1.0** (crank and idlers
12 → 10 T, pinion 16 → 14, transfer 20/15 → 17/13; crank:motor ratio 1.07, or 0.99 with a 13 T pinion); walls scale to
1.71 and need **+0.3 mm in place** to reach 2.0; journals Ø4.3 and M3 holes pass by scaling. Below 1.0 the crank gear
falls to 9 T and the walls need ≥ 0.45 mm more, so 1.0 is also the floor. Costs vs 0.70: 225 mm across the legs
(jenscolt's own size), weight ×2.9, crank torque ×4.2: the motor (N10 not bought, torque never measured) and cells are
sized in phase 2. Figure: session scratchpad `p1/escala.png`, script `p1/fig.py`; wall table `p1/walls.py`.

**Phase 2, motion: where does everything go so the whole mechanism turns?**
1. Scale the whole robot to S 1.0 and apply the minimums; every fit tweak made at 0.70 is deleted (D23/D23C,
   arm pockets, reliefs, x-stop posts, spacings).
2. Spatial reasoning before modelling: side and top sections with the swept volume of each moving part over a turn
   (legs, cranks, gears) and where the motor and cells go.
3. Collisions are solved by large layout moves (motor place, crank spread, gear train route), not sub-mm reliefs.
4. Done when the whole mechanism runs the 24 poses with no collision, every part counted, at N1 (1 mm).
5. Morante: animation and sections. Agent: `cad-designer` · opus for the layout PLAN (≈ 200k), one N1 check.

**Phase 2 result (closed 2026-11-26, branch `phase2-s1`: `808cf15`, `51a83ce`, `dbee8af`).** The robot builds at S 1.0
with the minimums (all 10 gears module 1.0 by check 13). Whole-robot N1 check `cad/robot/fitcheck/n1.py` (41 parts,
24 poses, 18 s): no shell↔leg or leg↔leg overlap; every remaining overlap ≤ 0.40 mm (legs 3/7 vs crank-4, legs vs
crank-1/2 webs and M3 axle heads), all phase 3. No large layout move was needed. Re-derived at 1.0 (concepts Morante
approved at 0.70): crank 2/3 spread 4.3 + shift 2.8 (legs 1↔2, 5↔6 0.55; legs 0↔1, 4↔5 0.37), body leg cutters
(BRELD 0.65, 12 cutters), back-sheet cup [3.0, |x| 17.2, z 10.0–23.7] with the body tab keep-out. Leg↔shell gaps
0.01–0.32 (no overlap) and the base front-window relief (not restored) are phase 3. Room: the motor has 22 mm free
along −x and 17 mm above (an N20 fits without moving anything). Mass ≈ 225 g printed, ≈ 255 g with hardware; crank
throw 3.3 mm, so lifting the whole weight needs ≈ 0.09 kg·cm: the motor bought must give ≥ ≈ 0.3 kg·cm at 3 V (N10's
torque never measured; seller's datasheet before buying). Body build 41–47 s cold (over 40 s). Count for phase 3: 27
printed parts, 14 hardware entries, 37 assembly steps. Sections: `cad/robot/images/phase2/` (not committed).

**Leg ↔ crank joint reopened by Morante (2026-11-27, second session): measure only, see «Next» below.** Branch `phase3-s1`.
Morante, 2026-11-27: «Deje este tema para resolverlo más adelante y vamos a seguir abordando otras cosas que haya
pendiente». Do not reopen the joint unless he does.

*Parked: leg ↔ crank joint.* The one real problem is the leg's end tube: walls 1.7–1.9 (< 2.0) and, after the first
fixer, a 4.3 mm grip on its pin. Measured on the fine meshes (cad-designer, 2026-11-27): pure ×1.43 scaling would have
given ×1.43 more gap everywhere (Morante's point); it was spent on the 2.0 walls, the 6.3 mm grip, the bore drift
added outside and the M3 heads. The only real contact left is the closed tube ends of legs 0↔1 and 4↔5 (overlap 0.06):
the leg leans 12.5–17.9° on its pin, so the tube flares and its closed end is the widest part. Base, cranks and
transfer meet their fits; several checks ask more than the fit (pin in bore and mouth ↔ web at 0.2 instead of the
TURN contact; leg pairs at 0.2 instead of LEG_PATH 0.5; check 13's per-part share let the 1.7 walls pass). The
N1 check's sub-0.2 mm numbers are noise at its 1 mm level. Options seen: (A) as now, snap that broke; (B, designer's
pick) tube centred on the pin point (end radius −0.9, ≈ 1.5 to the next leg) + Ø2×8 steel cross pin in a groove of the
printed pin (groove neck Ø2.9: coupon risk); (C) steel Ø3 pin, slimmer tube, but no retention without opening the
tube end. *Two fixers' attempts, committed on branch `phase3-leg-joint-wip` (4320b72), not on phase3-s1* (cutters.py, drive.py, fit_env.py, shells.py): legs out
XC_OUT 1.5, H_UP 0, full pin (PIN_TRIM 0, PIN_CH 0.6), TAIL = W, recess deleted, `leg_end_r` with BORE_DRIFT, base
window over the tube end (`Windows(tube, wt)`, MINW = WALL_MIN), elliptic neck JOINT_DH, SNAP_END_X 0.4, TB_CH 1.0,
BRELD +0.25; `--quick` 27 FAIL with it (20 before), legs 0/5 retention and leg-0 path worse. Kept or dropped when the
joint is reopened.

*Done 2026-11-27, not about the joint:* crank marks = engraved numbers 1–4, 3 mm × 0.5 deep on the +x web hub;
spine keel pilots stop at z 8.2 (2.16 mm left), keel screws M3×6 → **M3×5**; nickel strip inside the holder's walls
(NSX 18.84); lid lips 3.06 wide, between the spring seats (the lid is held); switch pocket opened 2.5 mm forward
(the leaning back wall's wedge); `BODY_TOP` 80.5 (the roof tool started inside the shell). Full `cad_verify` on a
clean rebuild: **10 FAIL, all on the legs** (body/transfer gaps 0.04–0.17 < 0.2, legs 0, 1, 5, 6, 7 not held, leg-0
path), i.e. the parked joint. Before this, `out/` mixed the joint branch's legs and base with this branch's parts:
rebuild everything (`build.py`) after switching branches.
*Done 2026-11-27 (second session), not the joint:* checks ask their pair's fit (`verify.py` end block): leg ↔ own crank a JOINTS row at fits.TURN (crank-4 / legs 3, 7 keep the accepted 0.18); leg ↔ every other part LEG_PATH 0.5 (base stays LEG_OPEN); legs in MINIMUMS at WALL_MIN, only the end tube asked (except boxes = the complement of a tube box; the rest is jenscolt's looks). `wall_frac` stays 0.01 (0 failed every edge and tip). Transfer-cheek strap ends square, `STRAP_TIP_W` 2.4 (was a 50° wedge, wall 0.00). Base: one solid. Motor picked: N10 07 type 100:1 (`hardware.md`). **Full check: 30 FAIL, all the legs** — (i) leg ↔ crank TURN 0.20–0.22 on legs 0, 1, 2, 4, 5, 6; (ii) LEG_PATH 0.5: body ↔ legs 0.04–0.46 (legs 0, 1, 2, 3, 4, 6, 7), leg-1 ↔ transfer 0.13, legs 0↔1 and 4↔5 0.36; (iii) tube walls 1.65–1.82, slit / bead edges near 0 (8 legs); (iv) legs 0, 1, 5, 6, 7 not held, leg-0 cannot go in. Interior WARNs located: spine (keel pilot chord), cranks (engraving floor), journal cap (sloped face): noise; motor-u 1.24 floor under a blind hole, 0.2 %, not identified. Full check now 95 s (over 60).
*Joint decided (2026-11-27, Morante): option D*, on branch `phase3-legjoint-D` (worktree `~/Repositories/spider-bot-replica-D`, HEAD 976a41c, not pushed): the leg rides with its pin point on the crank pin (`leg_frame` translated by A_k − T·A0: foot ≤ 1.43 mm along the leg, ≤ 0.23 high), BORE_DRIFT 0, bore with the tilted pin's ellipse term, floor at the tilted pin-tip corner + TURN (tube 1.3 shorter), legs RETAIN play 1.0, and the neck tab removed (`HUBFLANGE_L/R`: the rim of jenscolt's hub plate that HUBCUT left standing; it caused no FAIL, checked on D and on phase3-s1). **Full check 17 FAIL** (30 on phase3-s1): retention and assembly 0, leg-0 goes in, tube↔tube 0.60, leg-1↔transfer 0.59, base windows ≥ 0.60. Option A′ (rigid carry, walls 2.0, rounded end; branch `phase3-legjoint-A2`, worktree `-A2`, 31cf95b) fails at N1: tube↔tube −0.04, transfer 0.00, base −0.15 to −0.23: dropped.
*Done 2026-11-27 (third session): D finished and merged.* Full cad_verify **PASS, 0 FAIL, 91 WARN**. Leg tube about the pin's real swing cone (Morante's pick; measured: the pin tilts only towards +y, so the old symmetric 13.9° double cone made the tube up to 1.1 mm fatter at the end): `pin_cone(i)` fits the cone over the 24 poses, CONE_TILT 6.44/5.49/5.52/7.96° (leg classes 0/4, 1/5, 2/6, 3/7), CONE_FLARE 7.46/6.51/6.52/8.98° (swing + 1°), BORE_R 2.416/2.412/2.412/2.422, outer = bore + WALL_MIN/cos; one trimmed bore cutter, rounded end revolved about the tilted axis, END_PAD 0.05, slit to x1 + 0.03, slit edges 0.5 × 45° (SLIT_CHAMFER); groove SNAP_MARGIN = TURN + 0.05 (bead ↔ groove edge was 0.2257 on exact BREP); body notch NOTCH_GROW 0.35. Gaps: base ≥ 0.49 (legs 3/7; 0/4 0.26 → 1.3), legs/transfer/body ≥ 0.60, TURN 0.25–0.26, retention 36 ok. Except boxes carry measured walls (STEP_X 2.6: 1.98 on exact BREP; slit chamfers: wall across ≥ 2.0). cad_verify wall check: samples within the coarse chord deviation (0.05) under `wall` are a WARN. Lessons: (a) verify.py imported `cad.motion`, a second module copy that fit_env had not scaled, so its boxes for legs 1, 2, 5, 6 sat off the tube (leg 2 by 5 mm): use `SH.motion`; (b) stale `out/` STLs (legs 3, 7) gave false wall FAILs: rebuild before a check; (c) deleting the END_REL recess (this plan's own step) brought back the base FAIL it was made for: read a feature's comment before deleting it. Not done: grams (check prints volumes only: legs 2/6 23.5 cm³, 3/7 23.1 cm³). Scratch worktrees -A2 / -S1tab (branches `phase3-legjoint-A2`, `phase3-s1-notab`) still to remove: scratch only (S1tab = the neck-tab cut, already in D; A2 = dropped A′).
*Done in phase 3 so far (2026-11-26/27), committed on the branch:* plan.json rewritten for S 1.0 (A + B + F, validate
PASS, 24 steps); drive unit split into journal-cap 2.7 g, motor-u 3.4 g, transfer-cheek 1.3 g, flat, no support;
sleeves gone; idlers and transfer on M3 shanks; **ISO 7380 M3 button heads** on axles 1–3 and the transfer axle M3×16
(Morante: no thin rims, buy them); 1 strap screw; screws 2 × M3×6, 5 × M3×10, 1 × M3×16; transfer before motor-u;
spine set lowered 1 mm forward then slid back (crank-4 vs the base's rear lip). hardware.md still lists M2: the
documenter updates it with the button heads at the step's close.

**Phase 3 step 1 result (2026-11-26).** Count at S 1.0: 27 printed parts (10 gears in 9), 14 hardware entries (7
screws in 4 lengths, M3 in the geometry but still labelled «M2» in `drive_verify.py` / `power_verify.py` and the kit),
37 assembly entries (17 plan steps, 11 on the bench), 18 of 27 parts supported (drive unit 524 mm², cranks 137 mm²
each ≈ 140 % of their weight, transfer 151, spine 226, holder 461; legs' orientation the plater's). Morante picked
**A + B + F**: **F** = A's flat journal cap also caps crank 4, the cell holder loses its tongue over journal 4 (no
rubber band at step 7; the holder comes out without freeing crank 4). Applied without asking: M2 labels → M3, at most
2 screw lengths. **Direct drive (no transfer)** scanned (pinion 10–30 T on any idler or crank, every 5°, motor ±x, 24
poses, 0.25 mm grid): the bare N10 clears ≤ 0.75 mm everywhere, a 2 mm clamp fits nowhere. Best: **Direct 1**, 10 T
on idler 1 at 110° (motor centre y −22.8, z 32.0, motor on +x, same speed as now): bare motor 0.47 to the body, 0.62
to leg-1, 0.84 to the spine; it only works with the motor held by its gearbox face. Morante: «Lanza con la variante
directa incluida»: the PLAN compares A + B + F with the transfer against Direct 1 with a face mount.

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
