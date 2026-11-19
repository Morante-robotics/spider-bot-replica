# Robot (N2) · PLAN gate review, rev 1

Verdict: **CHANGES** (design-reviewer, 2026-11-19). Rev 2 of `design-plan.md` answers every item below; D1–D9 go
to Morante only after items 1–3 and 7 are re-probed.

1. **The inside does not fit; the shortfall is ≈ 3–5 mm, not ≈ 1 mm.** The probe (pr5) used bare boxes: motor
   24×10×12 (z 16–28), cells 36×12.6×13 (z 28.5–41.5). Add clamp walls and fit, holder floor/lid/end walls and
   contacts, LEG_PATH 0.8 on the arms, real arm thickness (N1 arms are thinned ×0.15–0.20). The 9 mm gear box
   (`cad/mockup/n0.py` boxes) leaves out the idler over the 7.7 mm pair 2–3: with m0.6 10T cranks and a 12T idler,
   its tip reaches z ≈ 19.8, under the motor (bottom z 16, y −1..9). D1a is not 1:1: 12T → idler → 10T turns the
   crank 1.2× the motor. Fix: rerun pr5 with real envelopes for D1a/b/c, idlers at their real positions.
2. **Middle arm ends collide.** Cranks 2–3 are 7.7 mm apart and half a turn apart (`sim/toy_leg_3d.py` GROUP),
   so same-side ball centres come within 7.7 − 2·2 = 3.7 mm. A Ø3 ball needs a Ø3.5 bore + 0.8 walls → arm end
   ≥ Ø5.1: overlap ≈ 1.4 mm before LEG_PATH. Fix: probe arm ↔ arm with real ends; candidates: different XC per
   crank, staggered ends.
3. **Pivot joint cannot pitch as drawn.** Arm eye and leg eye stacked, each with its own flare: two waists, no tilt.
   Notch floor and keeper bind (edge travel ≈ 2.85·tan 8° = 0.4 mm a side). The two PRESS pegs carry the leg's whole
   pitch moment over ~1.5 mm. Default D2a (Ø3, block 5.7) leaves 1.23 mm between swept roots; with LEG_PATH 0.8 per
   notch there is no rim left between notches 2–3; pr2's windows used the 4.7 block (Ø2 pin). Fix: one flare across
   the stack, crowned eye faces, a key along the whole block; add a **Ø2 steel pin** candidate to D2.
4. **Fix-prone notches live in the looks base.** The 8 notches, flares and pin bores are unproven (K4) and break
   «fix-prone parts separate». Printed rim-down, the notch floors (the legs' Z bearing face) are bridges. Fix: add a
   candidate of 2 pivot rails, one per side, screwed into the base, floors up (also covers D8b).
5. **Crankshaft printed axis-vertical puts support on functional faces** (bottom ball on the bed, webs and ball
   undersides overhang, layers across the crank pins). v2 printed crankshafts lying down. The 10T crank gear is under
   v2's 12T limit (needs a modified tooth shape). At m0.6 the tooth tip is ≈ 0.4 mm, one line of a 0.4 nozzle;
   GEAR_BACKLASH 0.20 was measured at module 1. Fix: state orientation and the undercut / profile-shift plan; K3
   prints the real crankshaft. Add a D5 candidate: m0.6 with a 0.2 mm nozzle for the gear parts (a purchase).
6. **Assembly and service steps are not real yet.**
   - Step 3: two hands hold two swivelling arms while journals, both eyes and the phase mark line up at once, and
     crank 3 goes down 3.7 mm from crank 2's arms. Needs a jig or another order.
   - The body goes on after the legs, so its skirt windows must be open at the bottom; not stated, and at legs 2–3
     the lip between the two slots disappears.
   - Leg service needs the body off if the keeper is under the skirt.
   - Pins «Ø3 × 6» look short: floor + 2 eyes + keeper ≥ 7.4 (v2 idler pins were × 10).
   - Ball-in-bore plus closed loop has no clean Onshape mate: name the mate combination, check degrees of freedom.
7. **D8 is not ripe.** pr4 measures overhang area, not support grams. D4 at 1.6 mm roughly doubles the support
   share. With the open side down, the eyes overhang outward on looks faces. Get slicer grams per orientation and per
   D4 option first.
8. **Cell holder does not fit its box.** The 12.6 mm stack axis leaves 1.8 mm for both contacts and no walls; real
   ≈ +4 mm in Y and +3 mm in Z (feeds item 1). The negative contact must be smaller than the cell's negative cap, or
   it touches the positive can rim and shorts the cell. D9 lacks bought candidates: ready 2 × LR44 holders, bent
   brass strip.
9. **Window claim (≈ 10 mm) cannot be checked**: the probes were left in a scratchpad. The method is plausible
   (≈ 5 + 2·1.4 swing + 1.6 ≈ 9.4 mm) but uses the 4.7 block, and N1 recorded 20 × 12. Fix: put the probes in
   `cad/robot/probes.py` and render the windows and the rebuilt rim for Morante (the visible rim changes).

**D7 (eyes; Morante has no translucent PLA).** Candidates: eyes coloured in the body with a Ø3 through-bore so the
LED's clear dome is the pupil (reviewer's default); a 2-layer (0.4 mm) yellow skin over the LED after a glow coupon
in his 4 colours; buy a translucent or white spool; separate clear lenses. Colour is AMS-painted in Bambu Studio:
give the slicer's purge grams for the painted body.

**Checked and fine:** N1 look kept (same meshes, S 0.60); colour never a split reason; every joint's fit from
`fits.py`, assumed ones to coupons K1–K7; joint table has an Onshape column; N10 and AG13 numbers flagged as
datasheet; D3 and D6 have fair candidates; spine, clamp, holder and keepers are separate screwed parts; phase marks
and gear offsets carried over from v2.

# Robot (N2) · PLAN gate review, rev 2 (of design-plan rev 2/3)

Verdict: **CHANGES** (design-reviewer, 2026-11-19). Rev 3 is good enough to start N2 modelling of body, base, legs,
spine and gears once B1–B4 are settled; each costs a print if wrong. Ran `probes.py pivot arms`; not `inside`,
`inside65`, `layouts`, `slice`.

| # | Verdict | Evidence |
|---|---|---|
| 1 | Partly | +0.99 is a real hill-climbed search (motor 26.8×12.8×14.8, holder 41.8/10.3/15.0 per pack, arms with LEG_PATH, crank sweeps, strip) but is the max of a climb with face samples good to ±0.3 (`box_pts`): no slack; envelope leaves things out (B3) |
| 2 | Partly | Ø2 balls with `CRANK_DY_D2` (0,0,2,0): pairs +0.47/+0.63/+2.35, spacing 9.8/9.8/12.1, pass ≥ 0 with 0.2 margin; probe at `p_at(0.60)`, not rerun at 0.65. Strength of a printed Ø2 ball on a neck, crank lying down, not stated |
| 3 | Partly | Rim 2-3 +0.87 (Ø2) is the wall left after two LEG_PATH 0.8: ≈ 2 lines, at S 0.60. Flare ±10°, crowned faces, edge travel 0.32 < 0.5: answered. Keeper screws do not fit (B2) |
| 4 | Not (rails declined) | Notch floors are the legs' Z bearing faces. D8 default (b) «rim ring = rails extended» contradicts the decision. Rim-up: 59 % support in the bowl; rim-down: floors are a 4.7 mm bridge on a loaded face. K4 proves a rim segment, not a printed base |
| 5 | Partly | Lying down, 0.3 flat: sound. 10T x +0.42 vs 0.41 undercut limit: 0.01 margin. Tip land 0.37 < one 0.4 line. K3 covers spur teeth only (B1) |
| 6 | Partly | Order credible; pin sequence unclear (B2); step 12 relies on K7 only |
| 7 | Answered | Numbers given; D8 open on purpose; D4b 14 g not trusted |
| 8 | Partly | Holder envelope honest. Negative-contact short unclear: «1.8 mm ring» vs 1.5 mm compressed spring (ring taller than spring = no contact). 3P parallel bus through 0.8 walls and the series link between packs across the motor not drawn. K6 tests one bay |
| 9 | Partly | Probes in `probes.py`; windows figure still missing (the visible rim changes) |

**B1. Crown and 10T pinion undefined.** `d1b` is a box (x ±7.1, y 10, z −7.1…+2): which strip gear it meshes, its
shaft and bearing, how a face gear prints; m0.6 face teeth with profile shift and GEAR_BACKLASH unproven, K3 spur only.
Add a crown coupon K3b and a crown bearing in the spine; state the crank:motor ratio direction.

**B2. Pivot hardware not buildable as written.** Keeper «2 × M3 per side» needs screw lands; free rim +2.45 at 1-2,
+0.87 at 2-3 (room only at 3-4 and the ends). A ≈ 40 mm thin keeper screwed at its ends lifts at legs 1-2: one keeper
per leg pair, or end screws plus a rim lip. Step 6 «pin 1 mm proud below the floor» with the keeper above the stack
(7.7 = floor + 4.8 + keeper): pin not retained from below; a smooth Ø2 pin needs a head or pull notch for service.
State the retention.

**B3. +0.99 omits:** eyes board + LEDs + perfboard at the front (where the crown is; the figure shows the holder under
the eyes); switch, JST, wires; motor terminals (24 mm body is datasheet); M3 heads and nuts of clamp and holder lid;
the two body bosses and the eye-board ledge; the bosses jenscolt's removed posts provided. Add these boxes to
`eval_layout`, run `layouts` once for H3e on D4a. Below 0 → fallback D4b (+1.64, limited by crown↔holder) or S 0.67:
Morante's call.

**B4.** `pivot` and `arms` at S 0.60: rerun at `p_at(0.65)` with the Ø2 offsets before freezing crank Y values; the
0.2 margin is thin.

**Stale text.** design-plan status line («rev 2 … waiting for D1–D9»); review-items rows 1–4 (S 0.62/0.65 «to run»,
Ø3 offsets, «Ø3 does not fit», rails «only fit»); «Inside fit» S 0.60 block, D1a/c idler numbers, «Next probe» line;
part list 5 (idler bores), 7 (estimate), 8 (Ø3 pins, sizes), 9 (12T pinion → 10T crown pinion), 13 (keeper or rail);
assembly 5 (`asm` +3.15 at old S/DY), 6 (Ø3 or Ø2, «1 mm proud»); joint table (idler Ø3 × 6, pinion → N10, STEEL Ø3,
«Revolute (pitch)»); decisions D1 text, D2 «default rails», D8 (a)+(b), D9 pins to buy, «Next: reviewer»; coupons K5
(→ Ø2 in Ø2.5) and K4 «rail (or rim)», crown coupon missing; diagrams «rev 2 envelopes»; datasheet.md status, Fits
row, crank offsets (two sets now); `probes.py` `CRANK_DY` comment (rescaled by S/0.6 in `_ctx`).

**Open for Morante.** (1) If B3 boxes push room below 0: D4b 1.6 mm wall or S 0.67. (2) Base print rim-up (≈ 59 %
support in the bowl) or rim-down (bridges on the Z faces). (3) Keeper per leg pair, or long with end screws.
(4) 5 mm vs 3 mm LEDs side by side.

**Checked and fine:** N10 fits named, flagged assumed; walls and fits from `fits.py`; flare, crowned faces, key along
the block; assembly order plausible; H3e and motor↔holder spacing in the probes.
