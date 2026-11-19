# Robot (N2) · plan

Status: **PLAN rev 4 (2026-11-19), waiting for Morante's open questions.** B3 shows that the inside does **not** fit
as fixed (below; probe bugs fixed 2026-11-19: the old −6.02 was not trustworthy, now −3.40 with the packs separated); the questions at the end are about that. Nothing modelled. Every number names its probe in
`probes.py` (repo root, `uv run python cad/robot/probes.py <name>`): `arms pivot neck crown cell pins` (≈ 20 s),
`layouts4 3.0` (≈ 70 s, one run per body wall), `motoronly` (≈ 2 min, both walls), `figure <png>`. `slice` waits for
the N2 meshes. Envelopes: bare part + walls (1.2 loaded, 0.8 elsewhere) + fits from `cad/fits.py` + contacts.

## Brief

- **Purpose.** N2 = the print detail of the looks robot approved at N1 (jenscolt body + eyes + base, his legs on
  N0's path, high knees) at **S 0.65**. The look does not change; the mechanism fits inside it.
- **Pass criterion.** It walks on its 8 legs: one N10, 6 × AG13 (2S3P, 3 V), switch, two LED eyes on a perfboard, no
  microcontroller. Every part prints with ≤ 10 % support, none on a functional face.
- **Motion.** N10 along Y → 10T pinion → 20T crown → 10T spur → transfer idler → spur strip along Y → 4 lateral
  crankshafts (r, XC, H of `n0.P0` scaled by S/0.60; **crank Y offsets `probes.CRANK_DY_65` = 0 / 0 / +2.0 / 0 mm at
  S 0.65**, frozen, `arms`) → each leg turns about a Ø2 steel pin in a notch of the base rim (yaw + pitch, no roll;
  the Ø2 crank ball slides in a Ø2.5 bore at the arm's end). Gait groups half a turn apart (`sim/toy_leg_3d.GROUP`).
- **Frame.** z = 0 at the base's bottom, origin on the body axis, forward −Y, +X right.
- **Bought parts are all «datasheet, measure on arrival»**; nothing is bought until the robot is final. N10 fits to
  add as `DSHAFT_N10`, `MOTOR_SEAT_N10`, `MOTOR_PRELOAD_N10` (assumed → coupons K1, K2).

## Fixed by Morante (2026-11-19)

S 0.65 · D1b motor along Y, crown at the front · H3e cells (two 3P packs on edge, one either side of the motor) ·
D2e Ø2 steel pin in notches in the base (no rails) · D5a m0.6, 0.4 nozzle · D7a eyes in the body colour, LED dome as
the pupil · D4a 3 mm wall, jenscolt's inner posts dropped · defaults D3a, D6a, D9a.
**Morante, 2026-11-19:** no eyes board in the design: the body only has the eye bores for the 5 mm LEDs from the
Arduino kit; he wires them himself (parts 15, the ledge, its screw and joint go). **Scale ceiling S 0.70**: a fit
problem is solved by placing things differently, never by a larger robot.

## Review items (`plan-review.md` rev 2)

| # | Answer | Probe |
|---|---|---|
| B1 | Crown pair defined (below): 10T x +0.42 pinion → 20T crown (axis X) + 10T spur on one part → 12T idler → crank 1. **crank:motor 1:2** (0.50). Crown on a Ø3 steel pin in the spine, printed face up. Coupon K3b | `crown`, `layouts4` |
| B2 | Rim at S 0.65: 1-2 +3.23, 2-3 +1.35, 3-4 +9.00, front of leg 1 10.7, rear of leg 4 3.1 → M3 lands (nut land 8.2) only in front of leg 1 and at 3-4. Keeper: one per side with those 2 screws + 2 hooks under a rim lip (default) or one per leg pair; pin Ø2 × 8 in a blind seat on a step, 2.0 proud for service | `pivot` |
| B3 | All boxes added. **Does not fit on D4a**: the motor group alone with the B3 boxes is already < 0 (−1.76: transfer idler ↔ arms; crown ↔ arms −1.51, motor ↔ arms −1.46, crown ↔ eyes board −1.39; no room for a front body boss in the skirt band); with the H3e packs (mirrored pair, one each side) the search ends at −3.40 (holder A ↔ switch), −2.74 with the lid screw in the hook. D4b gives the same pairs (they are not at the body wall): D4b does not help, S 0.67 not run | `layouts4`, `motoronly` |
| B4 | `arms`, `pivot` take S; at S 0.65, Ø2: offsets frozen **0 / 0 / +2.0 / 0 mm** (pairs +0.96 / +0.93 / +3.21, margin ≥ 0.2 kept by 0.73). Neck Ø1.6: breaks at ≈ 3.5 N at the ball, walking ≈ 0.49 N (×7) | `arms`, `neck` |
| 4 | Base rim-up vs rim-down: both kept, numbers below (D8) | `slice` (N2) |
| 8 | Negative contact: ring 1.5 high = spring working height, spring free 3.0 (contact guaranteed); 3P bus and series link drawn below | `cell` |

## Crown pair (B1, `probes.py crown`)

| Gear | Teeth, shift | Axis, place (best layout, `layouts4`) | Print |
|---|---|---|---|
| pinion (part 9) | 10T m0.6, x +0.42, tip Ø7.7, face 3 | N10 shaft, axis Y, centre y −16.5 z 23.0 | flat, D-bore up (K1) |
| crown (part 16) | 20T face gear, R0 6.0, teeth R 5.4–6.9 (2.5 m face), height 1.35, top land 0.51 at R0 (1.3 lines) | axis X at the motor's height: centre y −22.5 z 23.0, pitch plane x −3.25 | **face up**, disc on the bed, no support; 0.12 mm layers on the teeth (11 layers, not 7) |
| spur on the crown part | 10T x +0.42, at x 0, nested inside the crown's tooth ring (hub Ø8 < R 5.4) | same axis | on the same part, above the crown face |
| transfer idler (part 17) | 12T, x −0.42 (zero-sum) | Ø3 steel pin, y −21.9 z 16.4, meshes the spur and **crank 1**; in-plane clearance +0.33 to the pinion, motor and other strip gears | flat |

Shaft and bearing: the crown part turns on a Ø3 steel pin (TURN in the part, STEEL pressed in the walls) between two
spine walls at x −7.25 and +3.15, part of the spine's front tower that also carries the motor seat. Direction: all four
cranks turn the same way (one idler each); one transfer idler makes crank 1 turn like the crown spur. If the robot
walks backwards, swap the two motor wires (no part changes). The pinion's face clears the spur's tips by 0.65 along Y
(GEAR_TIP 0.5). Face-gear tooth limits (R 5.4–6.9) are assumed, not computed: K3b decides them.

## Inside fit (B3, `probes.py layouts4 3.0` and `motoronly`)

Boxes now in `eval_layout` / `search_b3`: motor + seat + clamp; **clamp ears** 2 × M3 (head 3.0 above, nut below);
**motor terminals** (3 mm) and a **wire box** behind them (solder joints, series link, leads to the switch); pinion,
crown part with its walls, transfer idler; packs H3e **+ inner tongue** (2 + 2 × TONGUE) **+ rear lid-screw boss**
(6.2) with its **M3 head** on the lid and **nut lug** under; **eyes board** (perfboard 1.6 + resistors 2.5, ledge 1.2)
behind **2 LEDs** on the eye axes (5 mm; 3 mm re-checked on the same layout) and its **M3 head**; **2 body bosses** on
the skirt band at x 0 (nut pocket 8.2); **switch** + retainer boss + tabs at the rear; **2 JST-XH pairs** placed last in
the room left. jenscolt's inner posts (body-to-base columns and the eye backing) are replaced by the 2 body bosses and
the eye-board ledge: no other boss.

Probe fixes (2026-11-19): (1) the old «−9.00 motor crown ↔ shell» was the coarse pick of a tie (every place scored −8
from the two identical bosses, the first one won, and the exact check then found it outside the shell); `motoronly` now
ranks coarse and re-checks the 12 best places exactly. (2) `place()` did not keep a placed boss out of the next one's
way (no room in the band = its room cannot get worse), so both bosses landed on the same box; now a placed box is
excluded, the rear boss stays on the axis in the skirt band (z 9–13), the front boss is off the axis; with no room
anywhere in the band both take the best room found (±0.3), front preferred. (3) Packs are searched as a mirrored pair
(A at x < 0, B = A mirrored), hill-climb on A (10 steps of 0.5); they no longer cluster. Motor x is fixed (strip plane
x 0), so the motor group is searched over y, z only.

Result (D4a, body wall 3 mm, 5 mm LEDs):

```
motoronly (motor group + B3 boxes, no cells):   least -1.76 (transfer idler <-> arms) at motor y -1.0 z 22.0;
                                                crown <-> arms -1.51, motor <-> arms -1.46, crown <-> eyes board -1.39,
                                                motor wires <-> switch -1.04. Bosses distinct: rear on the axis
                                                (y 21.9-30.1), front off the axis (x -24..-15.8, y 6.4-14.6, no room
                                                in the band: it falls at the best room found, not at the front).
                                                D4b 1.6: same least -1.76, same pair
R0 layouts4 (bugs fixed, nothing else):         least -3.40 (holder A <-> switch); holder A <-> shell -3.28,
                                                holder B <-> shell -3.22, holder A/B <-> eyes board -3.09,
                                                clamp ear L <-> holder A -2.76. motor y -1.0 z 22.0 (crown centre
                                                y -23.5 z 23.0), packs x -22.3..-9.4 and 9.4..22.3, y -25..23,
                                                z 22.5-37.5. 3 mm LEDs: -3.40, same pair
R1 + (c) eyes board flat above the LEDs:        least -3.40 (holder A <-> switch), unchanged; the eyes board is no
                                                longer binding (board <-> shell -2.63, next to holder A <-> shell
                                                -3.28, B <-> shell -3.22, ear L <-> holder A -2.76). Same motor and
                                                packs. Board z 38.0-42.1, y -24.6..-13.6
R2 + (d) lid screw in the hook (packs 41.8):    least -2.74 (holder A <-> shell); holder B <-> shell -2.69, eyes
                                                board <-> shell -2.63, holder A <-> switch -2.40, nut lugs <-> shell
                                                -2.28. motor y -1.0 z 21.0, packs x -23.3..-10.4 / 10.4..23.3,
                                                y -18.4..23.4, z 22-37. 3 mm LEDs: -3.08 (eyes screw <-> shell)
```

Notes: R1 and R2 are R0 plus the change, cumulative. Flat eyes board modelled as 25 × 11 × 4.1 above the LED flange
tops (+0.4), M3 head on top; the hook is modelled as no 6.2 end boss (pack 41.8 long), lid screw head and nut lug
kept at the pack's rear end inside its footprint. The pack hill-climb is local (greedy, 10 steps): the least can still
move by a few tenths with another start. No run reaches 0: the binds are now the packs against the shell and the
switch, not the motor group.

**Wall and scale sweep (coordinator, 2026-11-19; `search_b3(S, wall, eyes="flat", hook=True)`, i.e. R2):**

```
motor group alone, S 0.65, 3.0:  least -1.76 (idler <-> arms); crown <-> arms -1.51, motor <-> arms -1.46
R2 S 0.65 wall 1.6:              least -1.77 (idler <-> arms); holder A/B <-> shell -1.77 / -1.75
R2 S 0.67 wall 3.0:              least -2.39 (eyes board <-> shell); holders <-> shell -1.58, idler <-> arms -1.55
R2 S 0.70 wall 3.0:              least -1.99 (eyes board <-> shell); crown <-> arms -1.50, motor <-> arms -1.46
R2 S 0.75 / 0.80:                not run: `train()` finds no idler for the wider crank spacing (best = None)
```

Reading: scale gains ≈ 0.15 mm per +1 % S on the shell pairs, and almost nothing on motor group <-> arms (−1.76 at
0.65, −1.50 at 0.70): the gear teeth, motor and idlers do not scale, the arms' sweep does. The thin wall fixes the
packs (−1.75 → only the motor group binds). The D1b + crown layout does not fit by scale alone.

Without the eyes board (Morante's decision, same R2 search): S 0.65 wall 3.0 −2.74 (holder A ↔ shell), wall 1.6
−1.77 (idler ↔ arms); S 0.70 wall 3.0 −1.27 (idler ↔ arms; rear body boss ↔ shell −1.17, crown ↔ shell −1.03),
wall 1.6 −1.27 (same). The remaining bind is the D1b drive path (transfer idler and crown) against the arms' sweep.

Reading: rev 3's +0.99 left out about 1 cm³ of parts. What binds is the front: the crown pair must sit at the motor's
height (a face gear meshes at its axis height) and the motor cannot go below the strip top (z 15.4), so the crown
(Ø14.8 with walls, z 15.6–30.4) and the eyes board (z 28–40, y −22.6…−18.5) share the space behind the eyes; the
packs, now 48 × 12.9 with their screw boss and tongue, no longer fit beside the motor and its clamp ears. This is a
decision for Morante (questions 1–2), not a fix by loosening envelopes.

## Pivot retention (B2, `probes.py pivot`, S 0.65, Ø2)

- Rim left between swept blocks (LEG_PATH 0.8 each side): 1-2 **+3.23**, 2-3 **+1.35**, 3-4 **+9.00**; rim past
  leg 1 **10.7**, past leg 4 **3.1**. An M3 with its nut needs 8.2 (nut 5.5 AF + 2 × STEEL + 2 × 1.2): lands only
  **in front of leg 1** and **between 3 and 4**.
- **Keeper (a), default: one per side**, 2.4 thick, 2 × M3 down into nuts in the base (front land, 3-4 land), and
  **2 hooks** (2 mm tongues) that slide 3 mm along Y under a lip on the rim's outer face at the 1-2 segment and behind
  leg 4, so no span lifts. **(b) One keeper per leg pair** (1-2: screw in front of leg 1 + hook at 1-2; 3-4: screw at
  3-4 + hook behind leg 4): one pair serviced alone, 4 parts and 4 screws instead of 2 and 2.
- **Pin Ø2 × 8** (stock length; `pivot`): blind seat 1.2 deep (Ø2.30, STEEL) in a 2.0 notch floor, sitting on a step
  with a Ø1.5 push-out hole below; stack 4.8; play 0.5 (WINDOW); keeper pocket 1.5 deep (0.9 of keeper left above).
  Held down by the step, up by the keeper. Service: keeper off → pin stands **2.0** above the stack → pliers, or push
  it up from below through the Ø1.5 hole with the 1.5 hex key.
- Flare ±10° (pitch ±6.3 / 5.4 / 5.4 / 7.7°), block 4.7 × 5.7, flat-face edge travel 0.32 ≤ 0.5, crowned R ≈ 9.

## Crank ball (B4, `probes.py arms neck`)

Ø2 ball, end tube Ø4.1; ball swivel off the crank axis ≤ 18.5 / 15.8 / 13.7 / 22.7°, the bore mouth (0.5 × 45°)
passes 44°. Neck Ø1.6 (4 lines), lever 3.1 (ball to web face), section 0.27 mm³ after the 0.3 bed flat, crank printed
lying down so the neck lies in the bed plane and bends along its lines: ≈ 3.5 N at break vs ≈ 0.49 N walking (×7). A
jammed leg at stall (40 N·mm assumed → 37 N) breaks a neck first: the 0.4 g crankshaft is the fuse.

## Cells (item 8, `probes.py cell`)

```
        pack A (x < 0)                 motor            pack B (x > 0)        same STL, both with plates toward +X
  outer wall      inner wall                       inner wall      outer wall
  [- spring]x3 ... [+ plate]x3  ==== series link ==== [- spring]x3 ... [+ plate]x3
     bus A-                bus A+   (behind the motor,   bus B-              bus B+
       |                             in the wire box)                          |
       +--- JST 1 ---------------------- motor (-)          switch --- motor (+), JST 2 --- eyes board
```

- **Negative contact:** conical spring Ø5 (< cap Ø7.6–8.9), free 3.0, solid ≤ 0.8 (to buy, datasheet), in a Ø6
  pocket; a printed ring from Ø8 to the bay wall stands **1.5** proud of the spring seat: the can's shoulder sits on
  the ring, the spring is held at ≤ 1.5 against the cap (+ the cap's proud height). Ring height = working height <
  free height: contact always; the can rim never reaches the spring.
- **3P bus:** per wall, one tinned wire along Y in the top corner of the bays (2.6 mm of room between bay circle and box
  corner), through a 1.2 notch at the top of each 0.8 bay wall, soldered to the 3 spring tails (−) or 3 plate tabs
  (+). No envelope change. **Series link** A+ → B− across behind the motor in the wire box (y +3…+6 behind the
  terminals).

## Part list

| # | Part | Why separate | Est. g | Print orientation |
|---|---|---|---|---|
| 1 | body (dome, eyes, eye-board ledge, 2 bosses, skirt slots open at the bottom) | Looks part, off for cells | 22.6 (slicer, D4a) | D8 |
| 2 | base (bowl, 8 notches with Ø2 seats and push-out holes, rim lip, nut lands, body lugs) | Ground part | 11.7 (voxel) | D8 (item 4) |
| 3 | leg-arm ×8 (eye + bar + Ø4.1 end with Ø2.5 bore, key tongue) | Flat, no support | 0.4 each (box) | Flat, bore along the bed |
| 4 | leg ×8 (outer leg, eye with key groove) | Looks part | 1.8 each × 1.27 (S 0.65) | On its side |
| 5 | spine (strip walls, idler bores, front tower: crown walls, motor seat; 2 lugs) | Drive frame | 4 (box) | Walls up |
| 6 | spine cap (journal tongues, idler pin heads) | Closes the slots | 1.5 (box) | Flat |
| 7 | crankshaft ×4 (10T x +0.42, 2 webs, 2 Ø2 balls on Ø1.6 necks, 180°) | Moving | 0.4 each | Lying down, 0.3 flat |
| 8 | strip idler ×3 (13T / 13T / 15T, x −0.42, Ø3 pins) | Moving | 0.2 each | Flat |
| 9 | pinion 10T x +0.42, D-bore | On the N10 shaft | 0.1 | Flat |
| 10 | motor clamp (2 × M3) | Fix likely | 1 (box) | Flat |
| 11 | cell pack ×2 (3P on edge, same STL) | Cells replaceable | 2 each (box) | Open side up |
| 12 | pack lid ×2 (1 × M3 + hook) | Access | 0.5 each | Flat |
| 13 | pivot keeper ×2 (default a) or ×4 (b) | Holds the pins | 1 each | Flat, hooks up |
| 14 | switch retainer | Holds the SS12D00 | 0.5 | Flat |
| 15 | eyes board (perfboard, 2 LEDs, 2 resistors) | Bought + soldered | — | — |
| 16 | crown part (20T crown + 10T spur) | Turns the drive 90° | 0.6 (box) | Face up |
| 17 | transfer idler 12T | Crown spur → crank 1 | 0.1 | Flat |

## Joint table

| Joint | Type | Holds it ±X / ±Y / ±Z | Fit | In from | Apart by | Onshape |
|---|---|---|---|---|---|---|
| base → ground | — | — | — | — | — | Fixed |
| spine → base | 2 × M3 from below, nuts in lugs; locating pins | pins / pins / screws | LOCATOR 0.2 | down | 2 screws | Fastened |
| crankshaft → spine | journals in slots, cap tongues; webs on the walls | walls (GEAR_THRUST_CRANK) / slots / floor + cap | TURN, TONGUE_SHORT | down | cap off, lift | Revolute (X) |
| strip idlers, transfer idler → spine | on Ø3 pins between walls | walls / pin / pin | STEEL in walls, TURN in gear, GEAR_THRUST_IDLER | down | cap off | Revolute (X) |
| crown part → spine tower | on a Ø3 pin between 2 walls | walls (GEAR_THRUST_IDLER) / pin / pin | STEEL, TURN | down, then pin along X | pin out | Revolute (X) |
| pinion ↔ crown | face gear 10:20 | — | GEAR_BACKLASH, GEAR_TIP (assumed for face gears, K3b) | — | — | Gear relation |
| spur meshes | m0.6, x ±0.42 | — | GEAR_BACKLASH, GEAR_TIP | — | — | Gear relation |
| pinion → N10 shaft | D-bore press | D-flat / press / press | DSHAFT_N10 (assumed, K1) | along shaft | pull | Fastened |
| N10 → seat | seat + clamp, 2 × M3 | seat / seat + clamp / clamp | MOTOR_SEAT_N10, MOTOR_PRELOAD_N10 (assumed, K2) | into seat | clamp off | Fastened |
| arm ↔ crank ball | Ø2 ball slides ≤ 1.0 and swivels ≤ 23° in a Ø2.5 bore open inboard | bore (the pivot holds the leg) | TURN | leg slides in along its arm | slide out | Ball + Slider via dummy body |
| leg ↔ arm | key tongue along the eye block, both on the pin | key / key / keeper + floor | PRESS 0.0 key (assumed, K4) | leg onto arm, down | lift | Fastened |
| leg + arm → base | Ø2 pin, flare ±10°, crowned faces | pin / pin / floor + keeper (0.5 play) | STEEL; LEG_PATH 0.8 | down into the notch | keeper off, pin out | Revolute (Z) + Revolute (pitch) |
| pin → base | blind seat on a step + keeper above | seat / seat / step + keeper | STEEL | down | keeper off, pliers or push from below | Fastened |
| keeper → base | 2 × M3 + 2 hooks under the rim lip | lip / hooks + screws / screws + lip | LOCATOR 0.2, hooks WINDOW 0.5 | hooks along +Y 3 mm, then screws | screws, slide back | Fastened |
| pack → motor seat | tongue along Y + lid screw into a nut in the seat lug | tongue / screw / tongue | TONGUE 0.3, LOCATOR 0.2 | slide along Y | screw | Fastened |
| cells → pack | ring + spring (−), plate (+) | bay / spring / lid | WINDOW 0.5 round each cell | down | lid off | Fastened |
| lid → pack | hook + 1 × M3 (same screw as the pack) | hook / hook / screw | LOCATOR 0.2 | hook then down | screw | Fastened |
| switch → base | slot + retainer, 1 × M3 | slot / slot / retainer | WINDOW 0.5 | from inside | retainer | Fastened |
| eyes board → body | ledge + 1 × M3 | ledge / ledge / screw | WINDOW 0.5 | inside the dome | screw | Fastened |
| body → base | skirt lip inside the rim, 2 × M3 up through base lugs into nuts in the body bosses | lip / lip / screws | WINDOW 0.5 | down over the placed legs | 2 screws, JST 2 | Fastened |

## Assembly sequence (two hands, no jig)

| Step | Part or fastener | From | Hands / tool | In place | How you know it is right |
|---|---|---|---|---|---|
| 1 | spine on the bench: strip idlers and transfer idler on Ø3 pins; crown part on its Ø3 pin; pinion pressed on the N10 | above / side | hands; pliers with shaft support | — | pinion flush with the shaft mark; crown turns |
| 2 | N10 into the seat, pinion into the crown; clamp, 2 × M3 | above | hex key | 1 | crown turns by the motor shaft, no skip |
| 3 | spine → base, 2 × M3 + nuts | above / below | hex key, finger on the nut | base | no rock |
| 4 | crankshafts 1–4 into the slots | above | one hand | 3 | phase marks on the idler marks (§3.7) |
| 5 | spine cap | above | hex key | 4 | train turns by the motor shaft |
| 6 | arm into its leg (key); leg lowered into its notch 3 mm outboard and slid in along the arm onto the ball | above, then inward | one hand on the leg, the other turns the crank to its mark | 5 | eye holes over the Ø2 seat; path clear (`asm`, to rerun at S 0.65 on the N2 meshes) |
| 7 | Ø2 × 8 pin down through both eyes into its seat | above | fingers | 6 | pin top 2.0 above the stack (gauge: flush with a 2 mm step on the keeper) |
| 8 | keeper per side: hooks slid +Y 3 mm under the rim lip, 2 × M3 | side / above | hex key | 7 | legs swing, no roll, pins cannot lift |
| 9 | switch + retainer, M3 | inside, rear | hex key | base | lever through the skirt slot |
| 10 | packs slid onto the seat tongues; wiring: buses, series link, JST 1, switch, motor | above | iron | 9 | 3.0 V across the JST |
| 11 | 6 × AG13, lids + M3 (one per pack) | above | hex key | 10 | + mark on each bay |
| 12 | eyes board into the body, M3; JST 2 | inside the dome | hex key | body | LEDs in the eye bores |
| 13 | body down over the legs, JST 2 plugged first, 2 × M3 up from below | above / below | hands, hex key | all | lip seated all round |

Service: cells = 13 → 11 backwards. A leg = keeper (2 screws, outside the skirt), pin, leg out along its arm; body
stays on. A crankshaft = body, its 2 legs, cap.

## Decisions (every candidate kept, default marked)

- **D8 support / item 4 base orientation** (`slice`, voxel upper bounds, redone on the N2 meshes): **rim-up** 6.9 g
  support (59 %) in the bowl; notch floors (the legs' Z faces) print facing up, no bridge. **Rim-down** 8.7 g (72 %);
  the notch floors are 4.7 mm bridges on a loaded face. Default rim-up, support blocked on the outside looks faces;
  body open side down, 6.9 g (30 %) inside the crown and under the eyes. Settled with the slicer on the N2 meshes.
- **D2 keeper:** (a) one per side, 2 screws + 2 hooks (**default**); (b) one per leg pair.
- **LED size** (D7a): 5 mm (in hand, Arduino kit) vs 3 mm (to buy): side by side on the N2 render; B3 numbers above.
- **Inside fit** (questions below).

## Coupons (one batch after the whole robot passes `cad_verify`)

| # | What | Pass test |
|---|---|---|
| K1 | 3 pinions, D-bore −0.1 / 0 / +0.1 | pressed by hand + pliers, no slip |
| K2 | motor seat + clamp, 0.2 clear and −0.3 preload | motor does not move along its axis |
| K3 | spine stub, crankshafts 2–3 lying down, their idler, m0.6 x ±0.42 | turns by hand, no skip under a finger brake |
| K3b | spine front tower: crown part (face up, 0.12 layers) on its Ø3 pin, transfer idler, a printed 10T pinion on a Ø3 D-pin (crown teeth R 5.4–6.9, two face widths) | pinion turned by hand drives the crown spur with no skip or bind; teeth intact after 100 turns under a finger brake |
| K4 | base rim segment, legs 2–3 roots (arm + leg keyed), Ø2 pins in their seats, keeper with hook and screw | swing ±8° yaw, ±10° pitch, no roll, no bind; pin pulls out with pliers |
| K5 | crank ball Ø2 on a Ø1.6 neck in a Ø2.5 arm bore | slides 1 mm, swivels ±23° |
| K6 | one bay of 2 cells + ring + spring + plate | 3.0 V; cell out with a fingernail |
| K7 | skirt arc with the merged 2-3 slot + rim arc | body drops on over two legs and lifts off |

## Diagrams

`images/plan-exploded.png` (`plan_figure.py`, labels in Spanish): N1 meshes at S 0.65 + every `layouts4` box of the
best D4a layout (including the overlaps the probe reports). `images/plan-windows.png` (`probes.py figure`): right
side, legs off, N1 windows vs rev 4 notches with Ø2 pins.

## Open questions for Morante (batched)

1. **The inside does not fit (B3).** Options, each with its cost: **(a) S 0.67** (+3 % every length, shells ×1.06,
   legs ×1.09; one more `layouts4` run); **(b) D4b 1.6 mm body wall** (no gain on the binding pairs, `motoronly`);
   **(c) eyes board lying flat above the LEDs** (leads bent 90°: frees z 28–38 behind the eyes for the crown);
   **(d) pack lid screw moved into the lid hook** (no 6.2 boss: packs 41.8 long again). Also **(e) front body boss off the axis** (beside the crown tower). Default: **(c) + (d) + (e) on D4a,
   one `layouts4` run; S 0.67 only if still < 0**; (a) changes the look size again.
2. **Pack mounting:** tongue on the motor seat (+2.6 width, default) vs packs clipped to the body (out with the body).
3. **Keeper:** one per side (default) or one per leg pair.
4. **LEDs:** 5 mm (default, in hand) or 3 mm.
5. **Base print:** rim-up (default) or rim-down.
