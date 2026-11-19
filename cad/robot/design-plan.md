# Robot (N2) · plan

Status: **PLAN, rev 2 (2026-11-19), answers `plan-review.md` items 1–9 and D7; waiting for Morante's D1–D9.**
Nothing modelled yet. Every number names its probe in `probes.py` (repo root:
`uv run python cad/robot/probes.py [inside arms pivot gear cell pins asm]`, ≈ 1 min with the N1 cache;
`… probes.py slice` ≈ 4 min; `… probes.py figure cad/robot/images/plan-windows.png`). Envelopes are real: bare
part + walls (1.2 loaded, 0.8 elsewhere) + fits from `fits.py` + contacts; arm ends Ø3.5 bore + 0.8 walls.

## Brief

- **Purpose.** N2 = the print detail of the one looks robot approved at N1 (jenscolt body + eyes + base at S = 0.60,
  his legs warped onto N0's path, high knees). The look does not change; the mechanism fits inside it.
- **Pass criterion.** It walks on its 8 legs: one N10, 6 × AG13 (2S3P, 3 V), switch, two LED eyes on a hand-soldered
  perfboard, no microcontroller. Every part prints with ≤ 10 % support, none on a functional face.
- **Motion.** N10 → spur strip along Y → 4 lateral crankshafts (r = 2, XC = 6, H = −3 from `n0.P0`; **rev 2: per-crank
  Y offsets** `probes.CRANK_DY` = −1.5 / −0.5 / +2.5 / 0 from DY −2.4, item 2) → each leg turns about its pivot P in the
  base rim (yaw + pitch, no roll; the crank ball slides in a bore at the arm's end). Gait groups half a turn apart
  (`sim/toy_leg_3d.GROUP`, unchanged).
- **Frame.** N0/N1's: z = 0 at the base's bottom, origin on the body axis, forward −Y, +X right.
- **Every motor and cell number is «datasheet, measure on arrival».** Fits only from `cad/fits.py`; the N10 fits are
  added as `DSHAFT_N10`, `MOTOR_SEAT_N10`, `MOTOR_PRELOAD_N10` (assumed → coupons K1, K2).

## Review items (rev 1 → rev 2)

| # | Answer | Probe |
|---|---|---|
| 1 | Real envelopes: motor + seat + clamp 26.8 × 12.8 × 14.8 (rev 1: 24 × 10 × 12), holder 41.8 × 15.7 × 15.0 (rev 1: 36 × 12.6 × 13), idlers placed by the gear geometry (above or below the strip, whichever is free), arms with Ø5.1 ends + LEG_PATH. S 0.60: none fits (D1a motor outside the shell, D1b −3.95, see «Inside fit»); S 0.62/0.65 still to run. True ratios: D1a 1.20 (12T → idler → 10T), D1b 0.50, D1c 0.10 | `inside` |
| 2 | Arm ends collide as N1 (pairs 1-2 −0.62, 2-3 −2.67 mm; and crank gears 2-3 only 7.8 apart, tips 7.45: they rub). XC stagger makes it worse (−2.82); Ø2 balls alone not enough (2-3 −1.58). **Per-crank Y offsets** (−1.5, −0.5, +2.5, 0) give +0.51 / +0.71 / +0.60 with Ø3 balls, crank spacings 10.8 / 10.8 / 11.6; arm yaw changes ≤ 6.9°, taken by the arm-leg key so the outer leg keeps its N1 angle; swing p-p 12.5 / 10.9 / 11.0 / 15.9° (N1 12.9 / 10.9 / 10.9 / 15.9) | `arms` |
| 3 | One flare across the arm + leg stack (4.8 high), ±10° (pitch ±7.7° at leg 4 + 2°); eye faces crowned R ≈ 11 mm (Ø3) / 9 (Ø2); flat-face edge travel 0.39 / 0.32 < WINDOW 0.5 play; key: tongue along the whole block (6.7 / 5.7 long), not 2 pegs. Rim left 2-3: Ø3 −0.23 (does not fit), Ø2 pin / M2 +0.87 | `pivot` |
| 4 | Pivot rails added as D2-R: 2 printed rails (one per side, 4 notches each) screwed under the base rim, notch floors printed facing up (no bridges); the base keeps one window per side. Rim between notches 2-3 on the rail = same +0.87 (Ø2) / −0.23 (Ø3); a rail tooth of 0.87 is printable (2 lines) but not loaded-wall; Ø2 + rail is the only fit at 2-3 | `pivot` |
| 5 | Crankshaft printed **lying down** (as v2), throws in the bed plane, a 0.3 mm flat on the bed side of journals, webs and balls; layers along the crank pins. 10T: x = +0.42 (no undercut needs x ≥ 0.41), tip height 0.8 m → tip land 0.37 mm at m0.6 (0.9 line of 0.4; 1.9 lines of a 0.2 nozzle), 0.50 at m0.8. Idlers take −0.42 (centres unchanged). GEAR_BACKLASH 0.20 is module-1: K3 proves it at m0.6 | `gear` |
| 6 | New order (below): crankshafts in first, each leg goes in alone, one hand, along its arm onto the ball (path clear +3.15 mm to the placed arms); no jig. Skirt slots open at the bottom (figure); 2-3 slots merge into one. Keeper outside the skirt → leg service without the body off. Pins Ø3 × 9 / Ø2 × 9 (stack 7.7 + 1 proud); idler pins Ø3 × 6. Onshape: see «Onshape» | `asm`, `pins` |
| 7 | Slicer grams, below. Over 10 % in every orientation tried: D8 stays open with numbers | `slice` |
| 8 | Holder 41.8 × 15.7 × 15.0 (walls 1.2/0.8, WINDOW 0.5, spring 1.5 + plate 0.5); negative spring coil Ø5 inside the cap Ø8 (datasheet), behind a 1.8 mm ring so the can rim cannot touch it. D9 adds bought 2 × LR44 holders and bent brass strip | `cell` |
| 9 | Probes in `probes.py`; windows and rim figure (`probes.py figure`) not kept: triangle removal on the N1 mesh made it unreadable; redrawn from the N2 parts | `figure` |

## Inside fit (item 1, `probes.py inside`)

S 0.60, crank offsets `CRANK_DY`, body wall 3 mm (D4b adds ≤ 1.4 on body faces only), holder D9a above the motor:

```
    S 0.60 D1a crank/motor 1.20: least -9.00  motor↔shell -9.00 arms↔motor -3.35 cranks↔motor -4.55 strip +9.00 holder↔shell -0.27 (motor axis y -14 z 16, holder floor z 23.9)
    S 0.60 D1b crank/motor 0.50: least -3.95  motor↔shell -1.33 arms↔motor -3.35 cranks↔motor -3.60 strip -3.95 holder↔shell -0.27 (motor axis y -4 z 18, holder floor z 25.9)
    S 0.60 D1c crank/motor 0.10: least -9.00  motor↔shell -9.00 arms↔motor -2.75 cranks↔motor -0.60 strip +9.00 holder↔shell -0.27 (motor axis y -16 z 17, holder floor z 24.6)
    S 0.60: strip top z 14.6; idler 1-2 12T down z 6.4, idler 2-3 12T down z 6.4, idler 3-4 13T down z 6.5
    size: S 0.62 = +3.3 % every length, shell grams ×1.068, solid legs ×1.103; S 0.65 = +8.3 %, ×1.174, ×1.271
```

Reading: **nothing fits at S 0.60 with real envelopes.** D1a with the gearbox face on the spine wall (pinion in the
gear plane, the only way it meshes) puts the motor 3.4–30.2 mm from the axis: outside the shell on the left. D1b
misses by ≈ 4 mm (motor over the strip top z 14.6, arms, crank sweeps). D1c with the motor in line behind the strip leaves the shell at the rear. The idlers all fit **below** the strip (z 6.4,
12–13T), so the reviewer's idler-under-the-motor clash is gone in every option. **S 0.62 / 0.65 not run yet**
(`probes.pr_inside(scales=(0.62, 0.65))`, ≈ 6 min: the N1 meshes rebuild at each S); their size and gram effect is
above (D1). Next probe before D1: S 0.62/0.65 and D4b, motor between the cell holder and the crown (holder lower).

**Rev 3 (S 0.65 fixed, Ø2 balls, in progress, 2026-11-19).** `probes.py layouts` (drive × holder × D4 search,
min-filtered room grids then exact KD + 0.5 mm hill-climb) and `probes.py inside65` (rev 2 search, grid then exact
top 6). D4b = outer skin − 1.6 (voxel-labelled outer samples), not a +1.4 constant. Finding: the rev 2 «holder↔shell
−0.2 at every S» is jenscolt's **inner features** (posts and housings inside the dome, e.g. samples at (2.5, −17.7,
27.4) and a column at (21.5, 9.6, 23–36)), not the dome: every holder shape, even a 15 × 42 × 10 pack, binds at
−0.25 on them. **D4a now = outer skin − 3.0** (inner posts dropped), same construction as D4b. Result at S 0.65 (`inside65`): D1b
motor↔shell −1.47 (D4a) / −1.44 (D4b); D1a −3.22 / −1.82, D1c leaves the shell at both walls. `layouts` (80 rows):
only **D1b along Y + H3e (two 3P packs on edge, rows along Y)** fits: D4a +0.99 (holder↔shell), D4b +1.64 (motor
crown↔holder); next, H3 flat on D4b +0.01; every other holder < 0 (H1z −0.26, H1r −0.34, H3x −0.07 on D4b). S 0.62:
H3e D4a +0.20, D4b +0.87 (H3 flat D4b −0.73). Figure `images/plan-exploded.png` shows the S 0.65 D4a H3e layout.

## Support from the slicer (item 7, `probes.py slice`; 0.20 Standard, tree auto, build plate only)

| Part, orientation | Part g | Support g | Support % | Note |
|---|---|---|---|---|
| body D4a 3 mm (jenscolt mesh), open side down | 22.6 | 6.9 | 30 | real mesh; support inside the crown and under the eyes |
| body D4b 1.6 mm, open side down / up | — | 14.0 / 8.3 | — | **not valid**: the voxel-thinned mesh came out heavier than D4a (staircase faces); needs the N2 mesh |
| base bowl 1.2 (voxel-hollowed), rim up / rim down | 11.7 / 12.1 | 6.9 / 8.7 | 59 / 72 | upper bound: voxel steps overhang; real mesh at N2 |

AMS purge for the painted body: the CLI cannot paint; at Bambu's default flush (≈ 0.3 g a change, to confirm when the
plater paints it) the eyes span ≈ 60 layers of two colours → ≈ 18 g purge + prime tower, more than the body. D7
weighs this.

## Part list

| # | Part | Why separate | Est. g | Print orientation |
|---|---|---|---|---|
| 1 | body (dome, eyes per D7, front dome, eye-board ledge, 2 bosses, skirt slots open at the bottom) | Looks part, removable for cells | 22.6 (slicer, D4a) | Open side down (D8) |
| 2 | base (bowl, notches or rail windows, bosses) | Ground part; looks | 11.7 (slicer, voxel) | D8 |
| 3 | leg-arm ×8 (eye + bar + Ø5.1 ball end, key tongue) | Prints flat, no support; arm angle per crank (item 2) | 0.4 each (box) | Flat, bore along the bed (teardrop) |
| 4 | leg ×8 (outer leg, eye with key groove) | Looks part | 1.8 each (N1 pr3) | On its side; support under the knee arch |
| 5 | spine (walls, idler bores, motor seat, 2 lugs) | Drive frame, screwed: a gear fix reprints grams | 3 (box) | Walls up, slots open up |
| 6 | spine cap (journal tongues, idler pin heads, clamp) | Closes the slots (v2) | 1.5 (box) | Flat |
| 7 | crankshaft ×4 (10T x +0.42, 2 webs, 2 balls 180°) | Moving | 0.4 each | **Lying down**, 0.3 flat (item 5) |
| 8 | idler ×4 (sizes per crank spacing, x −0.42, Ø3 pins) | Moving | 0.2 each | Flat |
| 9 | pinion (12T, D-bore) | On the N10 shaft | 0.1 | Flat |
| 10 | motor clamp | Fix likely | 1 (box) | Flat |
| 11 | cell holder 2S3P (D9) | Cells replaceable | 4 (box) | Open side up |
| 12 | cell lid (1 screw) | Access | 1 (box) | Flat |
| 13 | pivot keeper ×2 (outside the skirt line) or pivot rail ×2 (D2-R) | Holds the pins; fix likely | 1 each | Flat / rail floors up |
| 14 | switch retainer | Holds the SS12D00 | 0.5 | Flat |
| 15 | eyes board (perfboard, 2 LEDs, 2 resistors) | Bought + soldered | — | — |

## Joint table (Onshape mate in the last column)

| Joint | Type | Holds it ±X / ±Y / ±Z | Fit | In from | Apart by | Onshape |
|---|---|---|---|---|---|---|
| base → ground | — | — | — | — | — | Fixed |
| spine → base | 2 × M3 from below, nuts in lugs; locating pins | pins / pins / screws | LOCATOR 0.2 | down | 2 screws | Fastened |
| crankshaft → spine | journals in slots, cap tongues; webs on the walls | walls (GEAR_THRUST_CRANK) / slots / floor + cap | TURN, TONGUE_SHORT | down | cap off, lift | Revolute (X) |
| idler → spine | on Ø3 × 6 pin between walls | walls / pin / pin | STEEL on pin, TURN, GEAR_THRUST_IDLER | down | cap off | Revolute (X) |
| gear meshes | spur m0.6 (D5), x ±0.42 | — | GEAR_BACKLASH, GEAR_TIP | — | — | Gear relation |
| pinion → N10 shaft | D-bore press | D-flat / press / press | DSHAFT_N10 (assumed, K1) | along shaft | pull | Fastened |
| N10 → spine | seat + clamp, 2 × M3 | seat / seat + clamp / clamp | MOTOR_SEAT_N10, MOTOR_PRELOAD_N10 (assumed, K2) | into seat | clamp off | Fastened |
| arm ↔ crank ball | Ø3 ball slides ≤ 1.0 and swivels in a Ø3.5 bore open inboard | bore (pivot holds the leg) | TURN | leg slides in along its arm | slide out | see «Onshape» |
| leg ↔ arm | key tongue along the whole eye block, both on the pivot pin | key / key / keeper + floor | PRESS 0.0 key (assumed, K4) | leg onto arm, down | lift | Fastened |
| leg + arm → base (pivot) | vertical pin, one flare ±10° across the stack, crowned faces | pin / pin / floor + keeper (0.5 play) | STEEL at the waist; LEG_PATH 0.8 round the block | down into the open notch | keeper, pin out | Revolute (Z) + Revolute (pitch axis), no roll |
| keeper → base (or rail → base) | 2 × M3 per side, from outside, below the skirt | rim / rim / screws | LOCATOR 0.2 | from the side | screws | Fastened |
| cell holder → base | 2 × M3 | bosses / bosses / screws | LOCATOR 0.2 | down | screws | Fastened |
| cells → holder | spring (−, Ø5 < cap Ø8) and plate (+) | bay / springs / lid | WINDOW 0.5 round each cell | down | lid off | Fastened |
| lid → holder | 1 × M3 + hook | hook / hook / screw | LOCATOR 0.2 | hook then down | screw | Fastened |
| switch → base | slot + retainer, 1 × M3 | slot / slot / retainer | WINDOW 0.5 | from inside | retainer | Fastened |
| eyes board → body | ledge + 1 × M3 | ledge / ledge / screw | WINDOW 0.5 | inside the dome | screw | Fastened |
| body → base | skirt lip inside the rim, slots open down, 2 × M3 from below | lip / lip / screws | WINDOW 0.5 | down over the placed legs | 2 screws, unplug JST | Fastened |

**Onshape (item 6).** Per leg: pivot = Revolute (Z) on the pin to a dummy yaw frame + Revolute about the leg's level
side axis (pitch); no roll. Ball in bore = a point on a line, which Onshape has no single mate for, so a dummy
«slider» body sits at the ball centre: **Ball** mate crank ball ↔ slider (−3 DOF) + **Slider** mate slider ↔ arm
bore axis (−5 DOF), on a body that adds 6: net −2. DOF per leg loop: crank 1 + leg 2 − 2 = 1 = the crank angle,
driven by the crankshaft's Revolute (over a turn the slide is ≤ 1.0 mm, `pr1`). Checked by turning the crank at N2.

## Assembly sequence (two hands, no jig)

| Step | Part or fastener | From | Hands / tool | In place | How you know it is right |
|---|---|---|---|---|---|
| 1 | spine on the bench: idlers on Ø3 × 6 pins, pinion pressed on the N10, N10 in its seat | above | hands; pliers with shaft support | — | pinion flush with the shaft mark |
| 2 | spine → base, 2 × M3 + nuts | above / below | hex key, finger on the nut | base | no rock |
| 3 | crankshafts 1–4 dropped into the slots, alone (no arms yet) | above | one hand | 2 | gear phase marks on the idler marks (§3.7) |
| 4 | spine cap + motor clamp, 2 × M3 | above | hex key | 3 | train turns by the pinion |
| 5 | arm into its leg (key), then the leg lowered into its open notch 3 mm outboard and slid in along the arm onto the ball | above, then inward | one hand holds the leg, the other turns the crank to its mark | 4 | eye holes in line with the notch hole; path clear +3.15 mm (`asm`) |
| 6 | pivot pin Ø3 × 9 (or Ø2 × 9) through the eyes | above | fingers | 5 | 1 mm proud below the floor |
| 7 | keeper (or rail) per side, 2 × M3 | from the side | hex key | 6 | legs swing, no roll |
| 8 | switch + retainer, M3 | inside, rear | hex key | base | lever reachable |
| 9 | cell holder 2 × M3; wiring cells → switch → motor + JST | above | hex key, iron | 8 | — |
| 10 | 6 × AG13, lid, M3 | above | screwdriver | 9 | + mark on each bay |
| 11 | eyes board into the body, M3 | inside the dome | hex key | body | LEDs in the eye bores |
| 12 | body down over the legs (slots open at the bottom), JST first, 2 × M3 from below | above / below | hands, hex key | all | lip seated all round |

Service: cells = 12 → 10 backwards. A leg = keeper (2 screws, outside the skirt), pin, lift the leg, slide out along
its arm: body stays on. A crankshaft = body, its 2 legs, cap.

## Decisions for Morante (batched; every candidate kept, default marked)

**Chosen by Morante, 2026-11-19:** S **0.65**; D1 **(b)** motor along Y with the crown at the front, cells as
**H3e** (two 3P packs on edge, one either side of the motor; +0.99 mm least room on D4a); D2 **(e) Ø2 steel pin**
in **notches in the base** (not rails: K4 proves the notch on a rim segment before the base is printed); D5 **(a)**
m0.6 with the 0.4 nozzle; D7 **(a)** eyes in the body colour with a Ø3 through-bore, the LED's dome as the pupil. LED size open: the main eye is Ø11.4 at S 0.65, so the 5 mm LEDs Morante already has (Arduino kit) fit with a Ø5 bore; 3 mm LEDs (to buy) give a smaller pupil. Shown side by side on the N2 render, his call.
Defaults kept: D3 (a), D4 (a) 3 mm, D6 (a), D9 (a). D8 is settled with the slicer on the N2 meshes. Next: a
design-reviewer pass on the rev 2/3 diff, then N2 modelling.

- **D1 motor.** (a) N10 along X left of the spine, pinion 12T → crank 10T direct or via one idler, ratio 1.20
  (default only if a larger S makes it fit; at S 0.60 its motor leaves the shell); (b) along Y, crown 10T → 20T, ratio 0.50; (c) along Y, worm → 10T
  wheels, ratio 0.10 (N10 10× faster, ≈ 40 % efficiency). Plus **S**: 0.60 / 0.62 / 0.65 (+3.3 % / +8.3 % every
  length, shells ×1.07 / ×1.17, solid legs ×1.11 / ×1.27); the look otherwise unchanged.
- **D2 pivot.** (a) Ø3 steel pin (rim 2-3 −0.23: does not fit); (b) M2 screw (+0.87; M2 in `hardware.md`);
  (e) **Ø2 steel pin (+0.87; to buy) — default**; (c) printed ball + cross pin (K4b); (d) yoke per leg. Each in the
  base rim notches or on **D2-R pivot rails** (2 screwed rails, floors up; **default rails**: the fix-prone part
  reprints in grams and the floors are not bridges).
- **D3 leg split.** (a) arm + outer leg keyed (**default**; also absorbs item 2's arm angles); (b) one piece on its
  side; (c) one piece upright.
- **D4 body wall.** (a) jenscolt's 3 mm (22.6 g sliced) (**default** until D4b is sliced on the N2 mesh); (b) 1.6 mm,
  same outside (+1.4 mm room inside, grams at N2).
- **D5 gears.** (a) m0.6, x ±0.42, 0.4 nozzle, tip land 0.37 (**default**, K3); (b) m0.6 with a 0.2 nozzle for the
  gear parts (to buy; 1.9 lines on the tip); (c) m0.8 (land 0.50; idlers and tips larger).
- **D6 switch.** (a) rear, lever through the skirt (**default**); (b) under the base.
- **D7 eyes** (no translucent PLA). (a) eyes in the body colour with a Ø3 through-bore, the LED's clear dome is the
  pupil (**default**: no purge for the eyes if they stay body colour); (b) 0.4 mm yellow skin over the LED after a
  glow coupon K8 in his 4 colours; (c) buy a white or translucent spool; (d) separate clear lenses (bought).
  Painting eyes in another colour costs ≈ 18 g purge (estimate above).
- **D8 support on body and base.** All sliced options exceed 10 % (body 30 %, base 59–72 % upper bound). (a) accept
  support inside the crown and inside the bowl only (no looks face), by a slicer support blocker on the outside;
  (b) split the base into bowl + rim ring (rim ring = the rails of D2-R extended), (c) body printed open side up
  (to slice on the N2 mesh). **Default (a)+(b)**; settled with the slicer on the N2 meshes.
- **D9 cells.** (a) printed holder + nickel spring/plate pairs (**default**; to buy); (b) 3 bought 2 × LR44 holders
  wired in parallel (size from the listing, measure); (c) printed holder with bent brass strip contacts (16.3 mm
  stack, no springs). Pins to buy: 8 × Ø2 × 9 (D2e) or 8 × Ø3 × 9, 4 × Ø3 × 6.

## Coupons (one batch after the whole robot passes `cad_verify`)

| # | What | Pass test |
|---|---|---|
| K1 | 3 pinions, D-bore −0.1 / 0 / +0.1 | pressed by hand + pliers, no slip |
| K2 | motor seat + clamp, 0.2 clear and −0.3 preload | motor does not move along its axis |
| K3 | spine stub, the real crankshafts 2–3 printed lying down, their idler, m0.6 x ±0.42 | turns by hand, no skip under a finger brake |
| K4 | rail (or rim) segment, legs 2–3 roots (arm + leg keyed), pins, keeper | swing ±8° yaw, ±10° pitch, no roll, no bind |
| K4b | same with the ball + cross pin (D2c) | same |
| K5 | crank ball Ø3 in a Ø3.5 arm bore | slides 1 mm, swivels ±20° |
| K6 | one bay of 2 cells + contacts | 3.0 V; cell out with a fingernail |
| K7 | skirt arc with the merged 2-3 slot + rim arc | body drops on over two legs and lifts off |
| K8 | (D7b) 0.4 mm skins in red, blue, black, yellow over a lit LED | the eye reads lit in daylight |

## Diagrams

`images/plan-exploded.png` (`plan_figure.py`): N1 meshes + boxes, numbered as the part list (rev 2 envelopes).
The windows and rim figure (`probes.py figure`) is redrawn from the N2 parts; the rev 2 one was unreadable.
