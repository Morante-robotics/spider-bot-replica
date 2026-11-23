# robot · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**S 0.70 spider: base (ground), body snapped on (2 front fingers + rear tab), spine with open-top journal slots, 4 printed cranks capped by the drive unit (1-3) and the holder post (4), 3 idlers and transfer, N10 drive unit, 2S3P AG13 holder, 8 legs on crank pins; cranks 2/3 2.6 further apart (cad/robot/fitcheck/check.py: 0 failing of 319 with the real cad/legs parts, LEG_PATH 0.5).**

Level N2 · purpose: The whole looks Spider-Bot as one assembly: the parametric legs (8), eyes, base and body placed with cad/motion.py, and the drive fitted inside them: N10 gear motor, gear train to the crankshafts, 6 x AG13 wired 2S3P with contacts, slide switch, two 5 mm LED eye bores. The scale S is 0.70 (Morante, 2026-11-21: «Prueba 0.70»): every length in cad/motion.py P0 (approved at N0 at 0.60) times S/0.60, so the look is N0's; a larger S (0.75, 0.8) is an alternative put to Morante, not a limit. · pass: full cad_verify PASS with every part inside (no collision over the 24 poses, each part's assembly path) at the chosen S, and the judge >= 0.60 against jenscolt's model (his photos and his assembled meshes in the same views as the robot)

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| base | ground: bowl with 8 open-top leg windows sized from the real cad/legs neck sweep (NR 5.4, about Ø10.8), front snap ribs, back-sheet pocket, 1.2 pads where loaded (100 % of each window ring), front-window reliefs | the ground shell, prints in one piece | 14 | foot down |
| body | dome with the eye block (0.85 leg-arm pocket on its lower front corners), front snap fingers (0.8 x 5, L 8), rear snap tab, front panel closing the mouth at the front face (1.2 thick, x ±18, hides the snap fingers; no front sensor placed), inner pocket over the cell pack's lift path | lifts off for service | 16 | rim up (roof on the bed), fingers vertical |
| spine | two gear walls with open-top journal slots (TURN), idler-axle holes, keel seat; wall tops raised 0.8 under the holder post where idler 3's tip passes | carries the whole train as one unit | 3 | keel down, walls upright, slots up |
| crankshafts | 4 printed cranks with gears, webs and Ø3 pins | each turns in the spine | 3 | axis vertical, one piece; support marks sanded (sandpaper) |
| idlers | 3 idlers and the transfer compound, each GW - 0.4 wide, turning (TURN, Ø3.7 bore) on printed spacer sleeves Ø3.2 x 3.5 (M2-tapped bore Ø1.6, wall 0.8) clamped wall to wall by the M2 axle, so tightening does not pinch the walls | each turns on its axle | 1 | face down |
| drive-unit | N10 clamp, transfer cheek, 2 blocks + ears; wall-top cheeks whose tongues cap cranks 1-3; two lugs on its -x plate clamped by idler axles 1 and 2 (STEEL holes, 1.2 wall); ear 2 lowered to 1.0 tall (the holder tab and its M2 head sit under the N10 and the lower clamp) | motor comes out without the train | 2 | ear face down |
| pinion | 16 T m 0.6 pinion pressed on the N10's D-shaft (DSHAFT), meshes the transfer big gear | bought motor shaft; reprints alone | 0.2 | face down |
| legs | 8 legs, end tube on the pin, ball in the window | each rides its own pin | 8 | flat on its side |
| cell-holder | 3 x 2 AG13, spring, nickel strip, wire slot; the post (x ±4, y ±3 about the cells' centre) down to the wall tops, post-cap tongues cap crank 4; front tab (5.2 x 1.2) on drive ear 2 (lowered, under the N10 and its clamp) with the holder M2 (hole STEEL, head on the tab) down into drive block 2 / ear 2; front-bottom notch at drive block 2; 0.8 leg-arm pocket on its top edge | screwed to drive block 2, cells swap | 2 | floor down |
| cell-lid | closes the cells | opens for cell swap | 1 | flat |
| n10-motor | drive |  |  |  |
| m2-screws | M2 socket cap ISO 4762 (1.5 mm hex key), self-tapping in PLA (pilot Ø1.6, assumed, proven on coupon c2, the holder's too): 3 idler axles (1 and 2 through the drive unit's lugs), 2 keel, 1 holder |  |  |  |
| ag13-cells | power 2S3P |  |  |  |
| ss12d00-switch | power switch |  |  |  |
| leds | two 5 mm LEDs + resistors |  |  |  |
| jst-xh | 3-pin connector body/base |  |  |  |

## Joint table

| Joint | Parts | Type | Held | Fit | In from | Apart by |
|---|---|---|---|---|---|---|
| crank-in-spine | crankshafts ↔ spine | turn | +x gear face vs wall (THRUST) · -x web vs wall (THRUST) · +y slot face · -y slot face · +z cap tongue (drive unit 1-3, holder post 4) · -z slot bottom | fits.TURN | +z | lift the holder and the drive unit, lift each crank out of its slots |
| gear-mesh | idlers ↔ crankshafts | gear | +x wall · -x axle head · +y axle · -y axle · +z axle · -z axle | fits.GEAR_TIP | +z (idler drops in, then its M2 axle along +x) | pull the M2 axle along -x, lift the idler |
| leg-on-pin | legs ↔ crankshafts | turn | +x crank web · -x window · +y base window · -y body rim · +z window · -z window floor | fits.TURN | -z through its open-top window, then along the pin (x) | lift the body, slide the leg off its pin along x, lift it out |
| leg-path | legs ↔ base | clearance | +x window · -x window · +y window · -y body rim · +z window · -z window | fits.LEG_PATH | as leg-on-pin | as leg-on-pin |
| spine-on-keel | spine ↔ base | screw | +x keel · -x keel · +y keel · -y 2 M2 · +z keel · -z bowl floor | fits.STEEL | +z | undo 2 M2 from below |
| drive-on-spine | drive-unit ↔ spine | screw | +x lug face on the -x wall, axle heads · -x lugs clamped by idler axles 1 and 2 · +y tongues in slots 1-3 · -y tongues in slots 1-3 · +z idler axles 1 and 2 through the lugs · -z cheeks on the wall tops | fits.STEEL | +z (on the bench, before the idler axles) | undo idler axles 1 and 2 along -x (spine set out of the base), lift the drive unit |
| holder-on-drive-block | cell-holder ↔ drive-unit | screw | +x tab on drive ear 2, post tongues in slot 4 · -x tab on drive ear 2, post tongues in slot 4 · +y tongues in slot 4, M2 in the block · -y tongues in slot 4, M2 in the block · +z M2 (head on the tab) into drive block 2 / ear 2 · -z tab on the ear top, post on the wall tops | fits.STEEL | +z | slide the N10 out (-x), undo the M2 (from above), lift the holder |
| lid-on-holder | cell-lid ↔ cell-holder | snap | +x rim · -x rim · +y rim · -y snap · +z rim · -z holder wall | fits.PRESS | +z | lift by its tab |
| body-front-snaps | body ↔ base | snap | +x rim · -x front wall · +y rim · -y 2 hooks under ribs · +z rim · -z base ledge | fits.PRESS | +z | pull the body up (45 deg return faces) |
| body-rear-tab | body ↔ base | snap | +x tab · -x tab · +y tab · -y snap rib · +z back sheet · -z ledge | fits.PRESS | +z | pull up with the front |
| motor-in-clamp | n10-motor ↔ drive-unit | press | +x clamp · -x clamp · +y clamp · -y clamp · +z clamp · -z clamp | fits.MOTOR_SEAT | -x | slide out along -x |
| pinion-on-shaft | pinion ↔ n10-motor | press | +x press · -x press · +y D-shaft · -y D-shaft · +z D-shaft · -z D-shaft | fits.DSHAFT | -x | pull it off the shaft |
| spacer-on-axle | idlers ↔ spine | screw | +x wall · -x wall · +y M2 axle · -y M2 axle · +z M2 axle · -z M2 axle | fits.STEEL | +z (sleeve in the idler, then the M2 along +x) | pull the M2 along -x |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | base | None | hand |  | foot flat |
| 2 | spine | +z | hand | nothing (on the bench) | upright, slots up |
| 3 | crankshafts | +z | hand | spine | journals down in their 8 slots at the phase marks (pose KC) |
| 4 | idlers | +z | hand | crankshafts | each meshes both cranks |
| 5 | drive-unit | +z | hand | idlers | on the bench: tongues in slots 1-3, lugs flat on the -x wall over idler holes 1 and 2 |
| 6 | m2-screws | -x | 1.5 mm hex key | drive-unit | 3 idler axles in along +x (1 and 2 through the drive unit's lugs), train turns by hand |
| 7 | spine | +z | hand | base | spine set (with the drive unit) on the keel |
| 8 | m2-screws | -z | 1.5 mm hex key | spine | lay the base on its flank for the keel M2; crank 4 held in its slots by a rubber band over the walls until the holder caps it; 2 keel M2 tight |
| 9 | legs | +z | hand | spine | dropped through its window, slid onto its pin along x, ball in its seat |
| 10 | cell-holder | +z | 1.5 mm hex key | legs | before the motor (its tab and M2 head sit under the N10): post-cap tongues in crank 4's slots, tab on drive ear 2 (lowered to 1.0), M2 through the tab into block 2 tight, driven while the clamp is empty |
| 11 | pinion | -x | hand | cell-holder | on the bench: pressed on the N10 shaft to its stop, flat to the D |
| 12 | n10-motor | -x | hand | pinion | slid in along +x with its pinion over the holder tab, pinion meshes, flush; comes out along -x with the holder in place |
| 13 | ag13-cells | +z | hand | n10-motor | + toward the strip, each cell pressed against its spring as it goes down |
| 14 | cell-lid | +z | hand | ag13-cells | snaps shut |
| 15 | jst-xh | +z | hand | cell-lid | latched |
| 16 | leds | +y | hand | body | domes in the eye bores |
| 17 | ss12d00-switch | -y | hand | body | lever out the back |
| 18 | body | +z | hand | everything | body-on mark: crank pose 12 (best of 24 for the lift-off; the rim notch over the leg arms, 0.22 deep, is cut for it); two front clicks, rear tab seated, legs turn |

## Alternatives

- **crank 2/3 split**: ±1.3 about the midpoint / crank 2 +0.5, crank 3 +3.1 rearward (C +1.8) / crank 3 +2.6 only → **crank 2 +0.5, crank 3 +3.1 rearward (C +1.8)**, ±1.3 leaves leg ends 0/1 at −1.40; C +1.8 is the least shift with every leg pair ≥ 0.8; pivots P do not move, only the inner arms skew; chosen at LEG_PATH 0.8, now 0.5 (measured fork window), about 0.3 spare
- **body front hold**: 2 M2 from below at ±44° / 2 snap fingers at x ±6 under base ribs / 1 central snap → **2 snap fingers at x ±6 under base ribs**, screws boxed in by eye block and legs (Morante); two fingers stop roll, front wall straight there
- **front window relief**: pocket + outward bulge, 45° chamfer under it / through-notch (window grows) / larger S → **pocket + outward bulge, 45° chamfer under it; through only where the bulge would come within LEG_PATH of a leg**, spec rule: reshape locally, outward on the base first; S not wanted
- **crank retention**: two separate walls clamped by the idler axles + keel / open-top journal slots capped by drive-unit tongues (1-3) and the holder post (4) / spine split at the crank axis, screwed top half → **open-top journal slots capped by drive-unit tongues (1-3) and the holder post (4)**, a one-piece crank's webs stop a wall sliding on along x; the caps reuse the drive unit and holder (no new part)
- **front snap finger**: T 1.0, L 7.0, travel 0.6 (1.8 %) / T 0.8, L 8.0, travel 0.5, overlap 0.4 (0.9 %) → **T 0.8, L 8.0, travel 0.5, overlap 0.4 (0.9 %)**, ≤ 1.1 % across layers; fits.PRESS kept as assumed
- **cell holder vs drive block 2**: notch at PY 14.0 (front wall left 0.42) / PY +0.4 with a 0.38 notch and a body inner pocket / PY +0.8, no notch → **PY +0.4 with a 0.38 notch and a body inner pocket**, wall ≥ 0.8 by the spring seat; the body wall is 3.2, the pocket is inside it
- **leg arm vs eye block and cell holder**: local pocket PKR 0.85 from the arms' 24-pose sweep / move the eye block forward / larger S → **local pocket PKR 0.85 from the arms' 24-pose sweep**, spec rule m13: reshape the colliding part locally; the pockets are inside, under 0.9 deep, not visible

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| m1 | the parts are imported from cad/legs, cad/eyes, cad/base, cad/body; scale, crank and leg path from cad/motion.py, never copied | verify | motion | must |
| m2 | the parametric parts may be reshaped where the inside needs it (surfaces moved, stretched or opened), as long as the robot's look passes the judge | verify | integrity | must |
| m3 | every part, screw and contact is in the code that counts the fit; a fit that leaves something out is reported as partial. Wires take no volume (flexible, routed by hand); only a hole or slot where a wire must pass a wall between its two ends (Morante, 2026-11-21: «no consideres los cables ni el espacio que ocupan… si hay que conectar cables entre dos puntos que separa una pared, sí tienes que dejar un agujero o ranura para que pasen») | verify | access | must |
| m4 | assembly order and each part's path checked before the scale | verify | assembly | must |
| m5 | the motor's fit is a separate, screwed part (the motor is bought later and measured; a fix reprints grams) | verify | access | must |
| m6 | Morante can change the cells; the switch is reached from outside | verify | integrity | must |
| m7 | two 5 mm LED bores in the eyes, wired by Morante (no eyes board) | verify | integrity | must |
| m8 | the views command renders the robot and jenscolt's assembled meshes in the same views and framing, written as images/reference.png next to the photos | visual |  | must |
| m9 | fasteners: start with M2 self-tapping screws or snap fits; M3 where it solves a problem | verify | retention | must |
| m10 | margins, walls and clearances: the standard values of cad/fits.py; changed only where they cause a problem, and put to Morante | verify | joints | must |
| m11 | print support as little as possible; up to 20-30 % on a part is accepted when a valid solution needs it | verify | print | must |
| m12 | screwdriver access: where it blocks a solution, it is put to Morante before the solution is dropped | verify | access | must |
| m13 | when something collides: first layout; then the colliding part is reshaped locally to make room (a pocket, relief, notch or bulge), any bulge outward on the shell (base) or the body first; a larger S is not wanted and is only put to Morante when nothing else works (Morante, 2026-11-21: «cada vez que te encuentres con un problema de colisiones, modifica o deforma la pieza local para dar cabida a lo que falta… empiezas por fuera en la carcasa o en el cuerpo»; «no quiero aumentar la escala más») | verify | motion | must |
| m14 | views.py places jenscolt's meshes (body, base, eyes, sensor, 8 legs; leg placement as the archived tools/assemble_jenscolt.py) at the robot's S and frame, writes out/reference.stl, and renders robot and reference with tools/mesh_ref.py views; `views.py --reference` writes images/reference.png; meshes are read only here, never by build.py or a gate | visual |  | must |
| m15 | cell contacts: conical springs + nickel strip (to buy) | verify | integrity | must |
| m16 | eye LEDs: red or yellow from the Arduino kit, with their resistors placed and counted | verify | integrity | must |
| m17 | wiring through one 3-pin JST-XH (to buy); hook-up wire from the Arduino kit | verify | integrity | must |
| m18 | crank 4 and the rear legs clear the base's back sheet through a local pocket in it, 1.6 mm outward, x ±11, z 7-17, hidden behind the body's rear tab (notched to match); the back scoop itself is not moved (Morante, 2026-11-21: «Tu recomendación») | verify | motion | must |
| m19 | cranks 2 and 3 (and their mirror) 2.6 mm further apart along Y than motion.py's uniform DY, standard fits.LEG_PATH on every leg pair (no waiver); the middle legs open ~1.3 mm each, shown to Morante next to jenscolt before motion.py changes (Morante, 2026-11-21: «Ok», S 0.70 signed probe: leg ends 2/3 −2.55) | verify | motion | must |
| m20 | front leg windows of the base: a local relief where the leg arm passes (S 0.70 probe −0.76 at ±20.6, −16.9, 16.3) (Morante, 2026-11-21: «Ok») | verify | motion | must |
| m21 | leg-arm end tube tail shortened to ~0.7 mm where it meets its own crank web (Morante, 2026-11-21: «Ok») | verify | motion | must |
| m22 | body held at the front by snap fits (the front screws are boxed in by the eye block and the legs); screws only where they have driver access (Morante, 2026-11-21: «Ok») | verify | retention | must |
| n1 | a probe that leaves parts out reported as a fit | verify | integrity | must |
| n2 | jenscolt's inner posts in the body or base | verify | integrity | must |
| p1 | full cad_verify PASS with every part inside (no collision over the 24 poses, each part's assembly path) at the chosen S, and the judge >= 0.60 against jenscolt's model (his photos and his assembled meshes in the same views as the robot) | morante |  | must |
| q1 | front snaps click on and pull off by hand; legs walk a full turn | print |  | must |
| c1 | snap coupon, runs before the body and the base are printed (PRESS assumed): front-wall strip with rib + rim strip with fingers, rear-tab rib, real print orientations; clicks on, pulls off by hand | print |  | must |
| c2 | gear and slot coupon m 0.6 (c2 + c3 merged): wall-pair stub with open-top slots, cap tongue, a drive-unit lug, a crank and an idler (GW - 0.4 wide) on its spacer sleeve and a real M2 self-tapping axle (pilot Ø1.6, assumed); turns by hand, no skip, drops in, turns free, cap holds, lug clamped, tightening does not pinch; plus the holder tab (1.2 thick, hole STEEL) on a drive-ear stub over a block stub, real M2 into pilot Ø1.6 (assumed): holds, head clear | print |  | must |
| c4 | leg coupon: leg end bore on a printed Ø3 pin + window strip; slides on, ball seats, swings free; the pin is printed in the crank's real orientation (axis vertical) | print |  | must |

## Diagram

<img src="base > keel M2 > spine set (spine, cranks in open slots, idlers, drive-unit caps 1-3, 3 M2 axles: 1 and 2 through its lugs) > legs (window, pin) > cell-holder (post on the wall tops, tongues cap 4, tab M2 into drive block 2) > N10 + pinion > cells > lid; body snaps" alt="Plan diagram">
