# Drive torque limiter (friction clutch): plan

Status: **PLAN rev 2, approved** (Morante, 2026-11-16, with the answers at the end; rev 1 got CHANGES, 8 objections). The clicker is not built. Morante chose a friction clutch over a PTC fuse. It replaces the
«teeth break first» protection (F3, [`design-plan.md`](design-plan.md#stall-protection-decided-f3-d-bore-pinion));
its fallback F2b is the starting point of candidate A. Nothing modelled; no `.py` file changed.
Diagram: [`images/clutch-plan.png`](images/clutch-plan.png) (Spanish: `images/clutch-plan-es.png`).
Probes (scratchpad, real STLs from `out/`, never the carcass): `probe_room.py` (free radius round the N20 axis),
`probe_notch.py` (module material round a -X notch), `probe_clutch.py` (window, capacities, mass).

## Rev 2: what changed (objection → answer; probe `probe_rev2.py` in the scratchpad, real STLs, motor model of `motor_sizing.motor_point`)

1. **Sustained slip.** Slip at 159 N·mm costs 0.67 W at 4.8 V (0.86 W at 5.6 V; shaft 40 rpm, motor 534 mA). Bulk pinion 25→60 °C in ≈ 47 s (PLA only), 52 s with the steel spring as the -X face, 63 s with two Ø9×1 steel washers: **steel faces buy ≈ 15 s, not safety**; what matters is stopping the slip. Ways compared (§1b): PTC fuse rejected by numbers (slip 498–569 mA is only 2.1 × the walking mean 237 mA; a PTC's trip/hold is ≈ 2.0, so it either trips walking on a warm day or never at slip); thermal cut-off (no room near the clutch, senses the motor not the faces); hand-reset breakaway (zero heat, but a new mechanism with no room found); **audible clicker** (recommended) + rule in the kit. -X face is now steel (the wave spring bears on the pinion); two steel washers do not fit the shaft (§3b). New test CL1-heat: crank blocked, 60 s at 4.8 V.
2. **Adjustment.** Steel shims DIN 988 3×6 in 0.1 steps (stock) replace 0.2 printed shims; spring rate ≤ 60 N/mm required (10 %/step; 0.05 creep → 5 %), two wave springs in series if one is stiffer. μ spread ±29 % means each unit is set by measure-shim-measure. Window bounds are now a choice for Morante (Q2): ±8 % (146–172) is tighter than one 0.1 step at 60 N/mm can hit reliably.
3. **Collar.** Bayonet dropped. Collar has a D-bore pressed on the **steel shaft tip** (`DSHAFT`, the same press as the sleeve): it cannot twist; shims are D-bore-free steel between steel spring and keyed collar. K1 adds an axial pull-off test (≥ 170 N = 2 × 85). F2b's M2 set screw does not fit the 2.1 mm left (§3b).
4. **Pinion centring.** New slip bore 0.1 a side (a new fit kind, measured on CL1) instead of TURN 0.25: backlash worst −0.018; plus the motor axis moved out 0.1 (interface I6, `CD_EXTRA`): worst **+0.054** (= today), largest +0.346. CL1 carries an idler-3 tooth segment at that centre distance: 3 turns, no bind.
5. **Spring vs idler 3 floated.** Idler 3's tip is at r 5.27 over |x| ≤ 2.95 (floated by 0.45). Spring now DIN 137 B **M3** (Ø3.2 × 8): r 4.0, 1.27 radial (≥ 0.5); shoulder Ø9.0: 0.77; KEEP_OUT ring r 4.77, |x| ≤ 2.95.
6. **Nut-trap wall.** Notch ends at x −5.4 (wall ≥ 1.25 to the I7 pocket by `probe_notch.py`), collar ends at −4.6 (0.8 `GEAR_AXIAL`).
7. **Hand assembly.** No push-and-turn: the collar is pressed in the press jig with the fork in (jig pocket widened to Ø9.5 for the shoulder), like the sleeve. K1 pass raised to 215 N·mm (440 g on 50 mm) on 1 mm-wall sleeves pressed on the real shaft.
8. **Fair comparison.** O-rings (C) bought with the spring; CL3 runs. B's CL2: 60 s motor run (≈ 2000 clicks), not 200. A's wear claim withdrawn (unproven for PLA; CL1-heat decides).

## 1. Slip torque (at the N20 output shaft, where the clutch sits)

| Quantity | N·mm | Source |
|---|---|---|
| Worst walking torque at the motor shaft, 463 g | 113 | `sim/motor_sizing.py` §6 (worst split, ground μ 0.6, joints, η 0.5, R 1.0) |
| Same at 466 g (design) / 478 g (ceiling) | 114 / 117 | `probe_clutch.py`, scaled ∝ mass |
| **Lower bound** = 1.25 × 117 | **146** | Slipping while walking only stops the robot (no damage), so 1.25 over an already-worst case, not the 1.5 used for teeth |
| Gearbox: Pololu max instantaneous output torque, HP 380:1 | 245 (2.5 kg·cm) | Pololu micro metal gearmotor datasheet; `motor_sizing.py` `GEARBOX_MAX`. Stall is 360 / 431 / 503 at 4.0 / 4.8 / 5.6 V (§5): a jam without a limiter exceeds it |
| 0.8 × 245 (the rule Morante set for F3) | 196 | design-plan.md, Stall protection |
| Weakest printed tooth in any jam path (estimate, 2.6 mm contact) | ≈ 191 | design-plan.md table; coupons K6a/K6b measure it |
| **Upper bound** = min(196, 0.9 × weakest tooth) | **172** (estimate) | `probe_clutch.py` |
| **Slip target** | **Q2 (Morante)**: 159 ± 8 % (146–172) · 171 ± 15 % (146–196) · 150 ± 14 % (129–172) · 162 ± 21 % (129–196) | `probe_rev2.py` §2 |

At slip the motor sees ≤ 172 < its stall at 4.0 V (360): the clutch always slips before the motor stalls, and,
being after the gearbox, it also caps the rotor's inertia spike at a sudden jam (a PTC fuse does not).

## 2. Placement

Every jam path is pinion → idler 3 → … (README, Stall protection table). `probe_room.py`: round the N20 axis the
free radius is 5.27 inside |x| < 2.5 (idler 3's tip), so ≤ 4.77 with `GEAR_TIP` 0.5; the gearbox face is at
x +3.3 and the -X wall at x -3.3 has only the shaft's U-slot (r 2.3). Room today: **Ø9.5 × 5 mm, the pinion itself.**

| Place | Protects | Room | Verdict |
|---|---|---|---|
| **Motor shaft / pinion** | Gearbox and every printed tooth, one clutch | Ø9.5 × 5 today; + x -3.3…-5.8 at r ≤ 5.5 with a U-notch in the -X wall | **Chosen** |
| Idler 3 (or 1, 2) | Nothing by itself: an idler's teeth pass torque straight from one mesh to the next; a clutch needs the idler split into two gears in two planes, which moves the pinion (interface I6) | none | Rejected (cannot work without moving the motor) |
| Crankshaft gear (gear ↔ crank) | Only that crank; four clutches needed, each in a 12 T, 3 mm gear (Ø14) | crankshafts reused unchanged | Rejected (4 × parts and calibrations; changes 4 reused parts) |

## 3. Candidates at the motor shaft (`probe_clutch.py`)

| | A Spring-loaded friction disc | B Printed flexure detent (clicks) | C O-ring friction hub |
|---|---|---|---|
| Layout | Sleeve (D-bore, pressed) with a +X shoulder; pinion (4 mm face) turns on the sleeve; spring + shim + collar locked on the sleeve's -X end, in the notch | 3 curved arms inside the pinion (r 2.3–3.9, 0.8 thick, 5 tall) click into notches of the tooth ring | 1–2 O-rings 5 × 1 in grooves of the pinion bore, squeezed on a Ø5 hub |
| Reaches 159? | Yes: 2 faces, r_eff 3.74, clamp 47–85 N for μ 0.45–0.25 | Only with a 0.4 bump: 165 N·mm at 70 MPa arm stress (PLA yields ≈ 50–60); 0.25 bump: 103 at 44 MPa. In a notch disc: 28–47 | 2 rings at high squeeze: 118–188; 1 ring: 20–94. Squeeze force very uncertain |
| Set to slip torque | Printed shims (0.2 steps) under the spring, on the bench; force loop closed in the sleeve (no thrust on the gearbox) | Only by reprinting (arm thickness, bump height) | Only by reprinting (groove depth) |
| Wear | Faces glaze (μ drops, slip drops = safe side); spring keeps the force as PLA creeps or wears | Bump and arm tips wear; arms fatigue at every click near yield | Rubber heats and abrades while slipping; slip rises if PLA creeps less than rubber relaxes: unpredictable |
| Hardware | 1 spring (to buy, §6) | none | 2 O-rings 5 × 1 NBR (to buy) |
| Module change | U-notch r 5.5 in the -X wall (§5) | none | none |
| Pinion face | 5 → 4 mm (Lewis ≈ 19 MPa worst, `motor_sizing` scaled; under 20) | 5 mm | ≈ 4 mm (two grooves) |
| Mass | +0.2 g printed + spring ≈ 0.2 g → 466.5 g, margin 3.07 (ceiling 478 unchanged) | ≈ 0 | ≈ +0.1 g |

**Recommended: A rev 2 (steel spring face, keyed pressed collar, 0.1 steel shims) + audible clicker.** Not on wear
(unproven for PLA, obj. 8): A is the only candidate set per unit after printing, which the ±29 % μ spread needs.
B and C stay fair candidates with their coupons in the same batch (CL2, CL3); any that passes CL1's tests in the
chosen window and the 60 s run is offered to Morante.

### 1b. Stopping sustained slip (no microcontroller; `probe_rev2.py` §1)

| Way | Stops slip? | Cost, room | Verdict |
|---|---|---|---|
| Nothing; the user sees the legs stop and switches off | Only if someone is there; ≈ 47 s to 60 °C bulk | 0 | Not enough alone |
| PTC fuse in the motor lead | No reliable separation: slip 498–569 mA vs walking mean 237 mA (2.1×) vs PTC trip/hold ≈ 2.0; trip at 2.1 × hold takes minutes; hold derates warm | ≈ 1 part, purchase | Rejected (numbers) |
| Thermal cut-off (bimetal 60 °C) | Senses the motor can, not the faces; slow | no room at the clutch | Rejected |
| Hand-reset breakaway (pops to free-wheel) | Yes, zero heat | new mechanism; no room found in Ø9.5 × 4 | Kept as a fallback if CL1-heat fails |
| **Audible clicker**: a printed flexure tooth on the keyed collar rides 6 bumps on the pinion's -X rim; clicks only while slipping (≈ 4 clicks/s at 40 rpm) | Makes a jam heard; the kit rule: «clicking = switch off» | printed, 0 g; adds ≈ 5–10 % torque ripple, measured on CL1 | **Recommended**, with the steel -X face |

### 3b. Stack along the shaft (x from the body axis; room `probe_rev2.py` §4)

| Item | x | r out | Clearance |
|---|---|---|---|
| Gauge gap (fork 0.8) | +3.3 → +2.5 | | `GEAR_AXIAL` |
| Sleeve shoulder, PLA | +2.5 → +1.5 | 4.5 | 0.77 to idler 3 floated (r 5.27, \|x\| ≤ 2.95) ≥ `GEAR_TIP` 0.5 |
| Pinion 12 T, 4 mm, slip bore 0.1 on the Ø5 sleeve (1 mm wall) | +1.5 → −2.5 | tip 7 | overlap with idler 3 ≥ 3.55 at either float |
| Wave spring DIN 137 B M3, steel, on the bare shaft (sleeve ends at −2.3) | −2.5 → −3.3 | 4.0 | 1.27 to idler 3 |
| Steel shims DIN 988 3 × 6, 0–0.3 | −3.3 → −3.6 | 3.0 | |
| Collar, D-bore pressed on the steel tip, clicker tooth | −3.4 → −4.6 | 4.5 | notch r 5.5 (1.0), notch end −5.4 (0.8 axial) |
| -X wall notch U r 5.5 open at +Z | −3.3 → −5.4 | | I7 nut wall ≥ 1.2 |

Two steel washers (Ø9 × 1) or an M2 set-screw collar (≥ 3 mm wide) need ≥ 1 mm more shaft than the 2.1 mm left
between the pinion and −4.6; they come back only if the I7 nut trap moves (Q1).

## 4. Coupons (listed now, cut and handed over only with the whole-robot batch)

| Coupon | What | g | Pass test |
|---|---|---|---|
| CL1 (A) | Sleeve and collar pressed on the **real N20 shaft** in the press jig, 4 mm pinion with a 30 mm lever, bought spring and shims, clicker; an idler-3 tooth segment at the plan's centre distance | ≈ 5 | Slips in the chosen window on 3 trials; after 50 slips each way the collar has not moved (pen mark); after 24 h clamped; 3 turns against the segment, no bind |
| CL1-heat (A) | CL1 on the motor, crank blocked | – | 60 s at 4.8 V: no fusing or smear, breakaway re-measured in the window; clicks heard. If it fails, the time it lasted / 2 goes in the kit rule and the breakaway fallback is drawn |
| CL2 (B) | Detent hub, arms 0.8 / 1.0, bumps 0.25 / 0.4 | ≈ 2 | Same lever test; then the 60 s motor run (≈ 2000 clicks), re-measure, no crack |
| CL3 (C) | Hub + pinion bore, grooves 15 / 20 / 25 % squeeze, bought O-rings | ≈ 2 | Same lever test and 60 s run |
| K1 (changed) | 1 mm-wall sleeves (not 5 mm discs) and collars on the real shaft | 1.5 + jig | Holds 215 N·mm (440 g on 50 mm) without turning; collar pull-off ≥ 170 N (a 17 kg luggage scale or water jugs); fork still fits after 24 h |
| K6a/b (existing) | Tooth break | | Sets the 172 upper bound |

## 5. Joint table (A rev 2)

| Joint | Type | Held ±X / ±Y / ±Z | Fit (`fits.py`) | In / out |
|---|---|---|---|---|
| Sleeve ↔ N20 D-shaft | Press | Press; torque by the D; +X load (clamp) by the press, K1 pull-off | `DSHAFT` (K1) | Pressed in the jig to the 0.8 fork; pulled with the jig |
| Pinion ↔ sleeve | Slip bearing + friction | +X shoulder, −X spring; radial sleeve | new «slip bore» 0.1 (CL1) | Slid on from −X |
| Spring + shims ↔ shaft | Free on the steel shaft | between pinion and collar | DIN 988 bore | Slid on |
| Collar ↔ shaft tip | Press, D-keyed | Press ±X (pull-off ≥ 170 N), D for torque | `DSHAFT` | Pressed in the jig, fork in (no load on the gearbox's bearing beyond today's); pulled with the jig to change shims |
| Clutch ↔ module | Spinning, no contact | — | `GEAR_TIP`, `GEAR_AXIAL`; KEEP_OUT r 4.77 \|x\| ≤ 2.95 | Drops with the motor |

Assembly (bench, replaces README step 6): fork in; sleeve pressed; pinion (dot towards the gearbox), spring, shims
slid on; collar pressed with the jig's Ø9.5 pocket (fork still in); lever test with the bottle, add or take a shim
(collar pulled with the jig). Service: motor out as today, collar pulled in the jig.

## 6. Open questions for Morante (batched)

1. **Module change**: −X wall notch U r 5.5, x −3.3 to −5.4, and the motor axis 0.1 further from idler 3 (I6). Option: also move the −X I7 nut trap ≥ 1 mm to fit two steel washers. Default: notch + 0.1 yes, nut trap stays.
2. **Slip window**: upper 172 (0.9 × weakest tooth, nothing breaks) or 196 (0.8 × gearbox, accept reprinting a gear); lower 1.25 × or 1.1 × walking (1.1 = may stop on a rough floor, no damage). Four windows in §1; no default chosen for him.
3. **Pinion face 5 → 4 mm** (I6). Default: yes.
4. **Clicker + kit rule** «if it clicks, switch off». Default: yes.

## 7. Purchases (with the motor, stock sizes; nothing before the robot passes in CAD)

Wave spring DIN 137 B M3 stainless (pack of 10; load table checked, ≤ 60 N/mm); shim washers DIN 988 3 × 6 × 0.1 / 0.2 / 0.3 (one assortment); O-rings 5 × 1 NBR 70 (pack, for CL3). No PTC, no set screw.

## Morante's answers (2026-11-16)

| Question | Answer |
|---|---|
| Slip window | **129–196 N·mm** (±21 %): easiest to set; accepts a reprinted gear in the worst case and a stop on rough floors |
| Module change | **Notch (x −3.3 to −5.4) and motor axis +0.1 mm**; the I7 nut trap stays (steel washer on one face only) |
| Clicker and kit rule | **No clicker** |
| Pinion face | **4 mm** |
