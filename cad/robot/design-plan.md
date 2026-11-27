# robot · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**Spider-Bot S 1.0, phase 3 simplify: N10 -> pinion 14 T -> transfer 17/13 T -> idler 2 -> 4 cranks (10 T, m 1.0) via 3 idlers; drive unit split into 3 flat screwed parts (journal-cap, motor-u, transfer-cheek), no sleeves, M3 only; grams = solid volume x 1.24 (100 % infill), from the S 1.0 STLs and boxes**

Level N2 · purpose: The whole looks Spider-Bot as one assembly: the parametric legs (8), eyes, base and body placed with cad/motion.py, and the drive fitted inside them: N10 gear motor, gear train to the crankshafts, 6 x AG13 wired 2S3P with contacts, slide switch, two 5 mm LED eye bores. The scale S is 1.0 (Morante, 2026-11-26: «S 1.0 máximo»): every length in cad/motion.py P0 (approved at N0 at 0.60) times S/0.60, so the look is N0's; printable minimums wall 2.0, gear module 1.0, M3. · pass: full cad_verify PASS with every part inside (no collision over the 24 poses, each part's assembly path) at the chosen S, and the judge >= 0.60 against jenscolt's model (his photos and his assembled meshes in the same views as the robot)

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| base | ground: bowl with 8 open-top leg windows, keel bosses, front snap ribs, back-sheet pocket (phase 2, unchanged) | the ground shell | 17.3 | foot down |
| body | shell snapped on the base, eye bores, switch window (unchanged) | the visible shell, lifts off for service | 128.1 | roof on the bed |
| legs | 8 legs from cad/legs on the crank pins (unchanged) | each leg swings on its own pin | 233.6 | the plater's (cad/legs) |
| spine | two 2.0 walls with 4 open-top journal slots, keel; idler holes: -x wall M3 pilot, +x wall STEEL (no thread, walls not squeezed) | ground of the gear train, screwed to the base keel | 4.1 | keel down, slots up |
| crankshafts | 4 cranks, 10 T m 1.0, journals Ø4.3, Ø3 pins (unchanged) | one per crank pair | 3.6 | the current orientation (phase 3 local work: support 137 mm² each) |
| idlers | 3 idlers 10 T, bore Ø3.3 on their M3 shank (B: no sleeves) | each turns on its own axle | 0.6 | face down |
| transfer | 13/17 T compound on a Ø3 steel pin (B: no sleeve), big gear outside the +x wall | turns between motor-u web and transfer-cheek | 1.7 | big gear face down |
| pinion | 14 T on the N10 D-shaft (DSHAFT) | pressed on the bought motor | 0.7 | face down |
| journal-cap | A/F: flat 2.0 plate over the wall tops above the idler tips, rails on the wall tops, 8 tongues in slots 1-4, transfer notch, lug on idler axle 3 | one flat cap for the 4 journals (F: also crank 4) | 2.9 | top face on the bed, no support |
| motor-u | A: -x web (lugs on idler axles 1, 2, ledge over the cap, transfer pin's -x end) + the N10 U along x (open +z) + ear 2 for the holder screw | carries the motor and the transfer's -x end; flat yz profile | 2.1 | -x face on the bed, U rises along +x, no support |
| transfer-cheek | A: +x cheek for the transfer pin + strap over the N10 U, 1 M3x10 into the -y ear | closes the U after the motor goes in | 0.9 | +x face on the bed, strap rises along -x, no support |
| cell-holder | 2S3P AG13 holder; F: no tongue over crank 4, post on the cap top, tab M3 into motor-u ear 2 | comes out without freeing crank 4 | 7.6 | floor down |
| cell-lid | snap lid (unchanged) | opens for the cells | 2.0 | plate down |
| n10-motor | N10 3 V gear motor (to buy; not measured) |  |  |  |
| m3-screws | ISO 4762 M3 self-tapping into Ø2.5 pilots: 2 x M3x6 (keel), 2 x M3x10 (strap 1, holder 1); ISO 7380 button head (Ø5.7 x 1.65, 2 mm hex key): 3 x M3x10 (idler axles 1-3) and 1 x M3x16 (transfer axle, listed as transfer-pin) |  |  |  |
| transfer-pin | M3 x 16 button head (ISO 7380, Morante 2026-11-27), the transfer's axle (screw, not a dowel); head on the motor-u web's -x face, thread in the web's Ø2.5 pilot, STEEL through the boss and the transfer; entered from -x |  |  |  |
| ag13-cells | 6 x AG13, springs and nickel strip |  |  |  |
| ss12d00-switch | slide switch |  |  |  |
| leds | 2 x 5 mm LED + resistors |  |  |  |
| jst-xh | 3-pin JST-XH pair |  |  |  |

## Joint table

| Joint | Parts | Type | Held | Fit | In from | Apart by |
|---|---|---|---|---|---|---|
| spine-on-keel | spine ↔ base | screwed | +x keel in the boss pocket · -x keel in the boss pocket · +y 2 M3x6 · -y 2 M3x6 · +z 2 M3x6 heads in the base bosses · -z keel on the boss tops | fits.STEEL | +z | 2 M3x6 out from below |
| crank-in-spine | crankshafts ↔ spine | turn | +x gear face vs wall (GEAR_THRUST_CRANK) · -x web vs wall · +y slot face · -y slot face · +z journal-cap tongues (slots 1-4, F) · -z slot bottom | fits.TURN | +z | lift the cap, lift each crank |
| idler-on-shank | idlers ↔ spine | turn | +x +x wall (GEAR_THRUST_IDLER 0.45) · -x -x wall · +y M3 shank · -y M3 shank · +z M3 shank · -z M3 shank | fits.STEEL | +z, then the screw along +x | screw out along -x, idler lifts |
| cap-on-spine | journal-cap ↔ spine | slide | +x tongues in the slot walls · -x lug 3 on the -x wall · +y tongues in slots 1-4 · -y tongues in slots 1-4 · +z idler-3 M3x10 button head on lug 3; motor-u ledge · -z rails on the wall tops | fits.TONGUE_SHORT | +z | axle 3 and motor-u off, lift |
| motor-u-on-spine | motor-u ↔ spine | screwed | +x web on the -x wall face · -x idler axle 1, 2 heads · +y M3 shanks 1, 2 · -y M3 shanks 1, 2 · +z M3 shanks 1, 2 · -z ledge on the cap | fits.STEEL | +z | 1 M3x10 out, lift |
| transfer-on-pin | transfer ↔ transfer-pin | turn | +x transfer-cheek (GEAR_AXIAL 0.8) · -x cap notch face (GEAR_AXIAL 0.8) · +y pin · -y pin · +z pin · -z pin | fits.STEEL | +z, pin along -x | M3x16 out |
| pin-in-cheeks | transfer-pin ↔ motor-u | slide | +x transfer-cheek face · -x M3x16 thread in its Ø2.5 pilot or its head · +y web hole · -y web hole · +z web hole · -z web hole | fits.STEEL | -x | cheek off, pull along +x |
| cheek-on-u | transfer-cheek ↔ motor-u | screwed | +x pin end in its hole · -x strap on the U ears · +y 1 M3x10 · -y 1 M3x10 · +z 1 M3x10 head · -z U ear tops | fits.STEEL | -z | 1 M3x10 out, lift |
| motor-in-u | n10-motor ↔ motor-u | clamp | +x gearbox face on the U end stop · -x strap press · +y U wall · -y U wall · +z strap · -z U floor | fits.MOTOR_SEAT | +z | strap off, lift |
| pinion-on-shaft | pinion ↔ n10-motor | press | +x shaft shoulder · -x press · +y D flat · -y D flat · +z D flat · -z D flat | fits.DSHAFT | -x | pull with pliers |
| holder-on-cap | cell-holder ↔ journal-cap | screwed | +x tab M3x10 · -x tab M3x10 · +y post on the cap · -y tab M3x10 · +z M3x10 head · -z post on the cap top, tab on ear 2 | fits.STEEL | +z | 1 M3x10 out, lift (crank 4 stays capped) |
| lid-on-holder | cell-lid ↔ cell-holder | snap | +x key · -x key · +y lips · -y lips · +z bumps in grooves · -z wall tops | fits.LOCATOR | +z | pull the back tab |
| legs-on-pins | legs ↔ crankshafts | turn | +x snap bead in the groove · -x web · +y pin · -y pin · +z pin, body rim · -z pin | fits.TURN | +z then -x along the pin | pull off along the pin |
| body-on-base | body ↔ base | snap | +x rim · -x rim · +y rear tab · -y front snaps · +z front snaps · -z ledge | fits.PRESS | +z | lift the front, unhook |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | base |  | hand | nothing | foot flat |
| 2 | spine | +z | hand | nothing (on the bench) | upright, slots up |
| 3 | crankshafts | +z | hand | spine | journals in their 8 slots at the phase marks |
| 4 | idlers | +z | hand | crankshafts | each meshes both cranks, held by hand at its hole |
| 5 | journal-cap | +z | hand | idlers | rails flat on the wall tops, 8 tongues in slots 1-4 |
| 6 | m3-screws | -x | 2 mm hex key | journal-cap | idler axle 3 (M3x10 button head, ISO 7380) through lug 3 and idler 3: cap held |
| 7 | transfer | +z | hand | m3-screws | small gear in the cap notch meshing idler 2 (before the motor-u: its U floor is over the transfer) |
| 8 | motor-u | +z | hand | transfer | ledge on the cap, web lugs over idler holes 1, 2, boss beside the transfer |
| 9 | m3-screws | -x | 2 mm hex key | motor-u | idler axles 1, 2 (M3x10 button head, ISO 7380): each idler turns free |
| 10 | transfer-pin | -x | 2 mm hex key | m3-screws | M3x16 button head (ISO 7380) from -x through the web, the boss and the transfer: it turns free |
| 11 | spine | +z | hand | base | spine set on the keel bosses |
| 12 | m3-screws | -z | 2.5 mm hex key | spine | 2 keel M3x6 from below, base on its flank |
| 13 | legs | +z | hand | spine | dropped through its window, slid onto its pin, bead clicks |
| 14 | cell-holder | +z | 2.5 mm hex key | legs | post on the cap, tab on ear 2, M3x10 through the U floor's key hole; no rubber band |
| 15 | pinion | -x | hand | n10-motor on the bench | pressed to its stop, flat to the D |
| 16 | n10-motor | +z | hand | cell-holder | drops into the U, pinion meshes the big transfer gear |
| 17 | transfer-cheek | -z | hand | n10-motor | over the pin end, strap on the motor |
| 18 | m3-screws | -z | 2.5 mm hex key | transfer-cheek | 1 strap M3x10: motor clamped, train turns by hand |
| 19 | ag13-cells | +z | hand | transfer-cheek | + toward the strip |
| 20 | cell-lid | +z | hand | ag13-cells | snaps shut |
| 21 | jst-xh | +z | hand | cell-lid | latched |
| 22 | leds | +y | hand | body | domes in the eye bores |
| 23 | ss12d00-switch | -y | hand | body | lever out the back |
| 24 | body | +z | hand | everything | body-on mark at crank pose 12; two front clicks |

## Alternatives

- **drive: transfer vs Direct 1 (comparison, probe p3plan/n1var.py, 24 poses)**: A+B+F with transfer / Direct 1: 10 T on idler 1 at 110°, face-mounted N10 → **A+B+F with transfer**, Direct 1 needs a ≥2.0 face plate + GEAR_AXIAL 0.8 between pinion and gearbox, pushing the N10 to x 4.9..25.9: N10↔body −0.79, plate↔body −0.50, N10↔leg-1 −0.12 (overlaps); A keeps the phase-2 envelope (cap↔transfer 0.24, a notch size)
- **comparison: printed parts / screws / steps**: A: 25 parts, 8 M3 (2 lengths) + 1 pin, 24 steps / Direct 1: 23 parts, 9 M3 + 2 M1.6 face screws (3 kinds), 22 steps → **A**, Direct 1 saves 2 parts and 2 steps but adds a screw kind on an unmeasured face
- **comparison: supported area**: A: drive 0 mm² (3 flat parts) vs 524 + 151 + sleeves now / Direct 1: 0 mm² on the drive → **A**, equal; cranks 137 mm² each remain in both
- **comparison: risks**: A: transfer centre distances through 3 screwed parts (STEEL 0.15 a side vs 0.27 before binding) / Direct 1: N10 face holes/spacing and shaft length assumed (2 x M1.6 at 9 mm, shaft ≥ 6.5 from the face), not bought, N1 fails by 0.8 → **A**, A's risk is a coupon; Direct 1's is a body change, which is frozen
- **idler and transfer axles (B)**: M3 shanks / Ø3 steel pins → **M3 shanks for the idlers and an M3x16 for the transfer**, fits.STEEL is measured for screw shanks as axles; each idler screw also holds the cap or the motor-u, threaded only in the -x wall so the walls are not squeezed; transfer span 18.7 needs 16 mm: M3x16, nothing to buy (Morante 2026-11-26: «Ok», 3 screw lengths)
- **motor U strap (A)**: strap on the transfer-cheek / separate strap part / strap on the motor-u → **strap on the transfer-cheek**, Morante's A; one part closes the U and caps the transfer pin
- **crank 4 cap (F)**: journal-cap tongues / holder tongues + rubber band → **journal-cap tongues**, Morante's F: the holder comes out without freeing crank 4

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
| m9 | fasteners: M3 everywhere (holes fits.STEEL on Ø3.3), or snap fits (datasheet robot «Phase 1 result», Morante 2026-11-26) | verify | joints | must |
| m10 | margins, walls and clearances: the standard values of cad/fits.py; changed only where they cause a problem, and put to Morante | verify | joints | must |
| m11 | print support as little as possible; up to 20-30 % on a part is accepted when a valid solution needs it | verify | print | must |
| m12 | screwdriver access: where it blocks a solution, it is put to Morante before the solution is dropped | verify | access | must |
| m13 | when something collides: first layout; then the colliding part is reshaped locally to make room (a pocket, relief, notch or bulge), any bulge outward on the shell (base) or the body first; a larger S is not wanted and is only put to Morante when nothing else works (Morante, 2026-11-21: «cada vez que te encuentres con un problema de colisiones, modifica o deforma la pieza local para dar cabida a lo que falta… empiezas por fuera en la carcasa o en el cuerpo»; «no quiero aumentar la escala más») | verify | motion | must |
| m14 | views.py places jenscolt's meshes (body, base, eyes, sensor, 8 legs; leg placement as the archived tools/assemble_jenscolt.py) at the robot's S and frame, writes out/reference.stl, and renders robot and reference with tools/mesh_ref.py views; `views.py --reference` writes images/reference.png; meshes are read only here, never by build.py or a gate | visual |  | must |
| m15 | cell contacts: conical springs + nickel strip (to buy) | verify | integrity | must |
| m16 | eye LEDs: red or yellow from the Arduino kit, with their resistors placed and counted | verify | integrity | must |
| m17 | wiring through one 3-pin JST-XH (to buy); hook-up wire from the Arduino kit | verify | integrity | must |
| m18 | body held at the front by snap fits (the front screws are boxed in by the eye block and the legs); screws only where they have driver access (Morante, 2026-11-21: «Ok») | verify | motion | must |
| m19 | cranks 2 and 3 (and their mirror) 2.6 mm further apart along Y than motion.py's uniform DY, standard fits.LEG_PATH on every leg pair (no waiver); the middle… | verify | motion | must |
| m20 | front leg windows of the base: a local relief where the leg arm passes (S 0.70 probe −0.76 at ±20.6, −16.9, 16.3) (Morante, 2026-11-21: «Ok») | verify | motion | must |
| m21 | leg-arm end tube tail shortened to ~0.7 mm where it meets its own crank web (Morante, 2026-11-21: «Ok») | verify | motion | must |
| m22 | body held at the front by snap fits (the front screws are boxed in by the eye block and the legs); screws only where they have driver access (Morante,… | verify | retention | must |
| n1 | a probe that leaves parts out reported as a fit | verify | integrity | must |
| n2 | jenscolt's inner posts in the body or base | verify | integrity | must |
| p1 | full cad_verify PASS with every part inside (no collision over the 24 poses, each part's assembly path) at the chosen S, and the judge >= 0.60 against jenscolt's model (his photos and his assembled meshes in the same views as the robot) | morante |  | must |
| q1 | front snaps click on and pull off by hand; legs walk a full turn | print |  | must |
| c1 | snap coupon, runs before the body and the base are printed (PRESS assumed): front-wall strip with rib + rim strip with fingers, rear-tab rib, real print… | print |  | must |
| c4 | leg coupon: leg end bore on a printed Ø3 pin + window strip; slides on, ball seats, swings free; the pin is printed in the crank's real orientation (axis… | print |  | must |
| c2 | gear and slot coupon m 1.0: wall-pair stub with open-top slots, cap tongues, an idler on its M3 shank (threads only in the -x wall): drops in, turns by hand | print |  | must |
| c5 | motor-u coupon: N10 in the U under the strap (MOTOR_SEAT 0.2), pinion meshes the transfer on its pin, turns by hand | print |  | must |
| s1 | A: journal-cap, motor-u and transfer-cheek print with no support (3 flat parts) | verify | print | must |
| s2 | B: no printed sleeves; idlers on M3 shanks, transfer on a Ø3 pin | verify | joints | must |
| s3 | F: crank 4 capped by the journal cap; the holder lifts out with crank 4 held | verify | retention | must |
| s4 | hardware labelled M3 (not M2), at most 2 screw lengths (M3x6, M3x10) | visual |  | must |
| s5 | N1: every pair at the 24 poses with no overlap (fitcheck/n1.py), drive pairs at their fits | verify | motion | must |

## Diagram

<img src="base > keel 2 M3x6 > spine set [spine, cranks, idlers, journal-cap (slots 1-4) + axle 3, motor-u + axles 1-2, transfer + pin] > legs > cell-holder (M3x10 into ear 2) > N10 + pinion > transfer-cheek (2 M3x10 strap) > cells > lid > body" alt="Plan diagram">
