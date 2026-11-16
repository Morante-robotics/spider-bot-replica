# Chassis Part A (drive module and master model) · design review

Each answer with the number or the picture that shows it. Numbers from [`verify-result.txt`](verify-result.txt)
(full run, 36 steps of 10°, gears over one tooth in 1° steps, also with the motor lifted 0.2) and from
[`build.py`](build.py). Pictures: [`images/verify/`](images/verify/).

| Question | Answer and evidence |
|---|---|
| Fits: every face pair against `fits.py`, at the worst position | All clearances come from `fits.py`; none is typed in `build.py`. Measured: journals in Ø4.5 holes 0.25 a side (`TURN`); crank gear faces and webs to the walls 0.25 (`GEAR_THRUST_CRANK`, new, measured on gear train v2); idlers 1–2 and idler 3 v2 to the walls 0.45 (`GEAR_THRUST_IDLER`, new, measured; pocket 5.9 for the 5 mm idler); pins and screws in Ø3.3 holes 0.15 (`STEEL`); cap skirts and keeper edges 0.2 (`LOCATOR`). Assumed, each with its coupon: cap tongues 0.3 a side (`TONGUE`, K3), the clamp's cheeks on the gearbox flats and the can at its rear stop 0.2 (`MOTOR_SEAT`, K2), the clamp's gearbox pad 0.3 into the gearbox (`MOTOR_PRELOAD`, −0.3, K2: section 9 checks that the pad overlaps the gearbox), the +X wall's steps 0.5 a side (`WINDOW`), every gear tip 0.5 from its pocket (`GEAR_TIP`, idler 3 v2's flat floor and sides: K3), pinion D-bore at the shaft's size (`DSHAFT`, K1): section 9 of the result lists each assumed one as WARN «not measured yet». Worst positions: the cap at either skirt stop is in its own keep-out zone round the pinion (`pinion-cap`, clear); the motor lifted 0.2 against the clamp is in `GEAR_MOTION` (pinion × idler 3 v2: 0.10–0.18 mm, inside 0.08–0.5). Cap screw holes are Ø3.7 (`STEEL` + the skirts' 0.2 play) so the skirts, not the screws, locate the cap (first quick run: the shared screw overlapped the cap at its stop) |
| Strength: smallest section of every feature that takes force | Spine walls 2.5 (|x| 1.75–4.25), 2.55 round idler 3, 1.3 between the idler 3 pocket and the crank 3 and 4 slots (|x| 2.95–4.25: the webs ride on 4.25, the 5 mm idler needs 2.95; the WARN «upright feature 10 mm²» in section 6 is these two ribs, 8.8 mm tall across the layers: in rev 4 they were the gearbox's Y steps and took the motor torque, ≈ 20 N each at 190 N·mm, 10–18 MPa across the layers. Now the steps are 0.5 a side (`WINDOW`) and the clamp's cheeks (2.5 × 9 × 1.5 down the gearbox flats, 0.2 off them, `MOTOR_SEAT`) take the torque first: at 0.2 / 6 rad the gearbox's lower corner has moved 0.2 of the steps' 0.5, so the ribs stay out of the torque path; cheek ≈ 36 N, root moment ≈ 43 N·mm on 8.3 mm³ → ≈ 5 MPa across the clamp's layers). Pin blind ends 0.8 with a Ø2 push-out hole (only the finger's push). Gearbox pad 2.2 × 10.4 on the +X wall. Saddle 3.7 under the can's V, 2.1 under the gearbox's. Cap plate 5.05 (v2.1: 5.0), its -X bridge 3.5 × 5.05 at the window. Tongues 1.1 × 3.9 (test cap v2.1's section, measured). Clamp bar 8 × 3, 2.0 over the pinion relief (±4.5 mm, 1 mm deep); preload at the gearbox pad 0.3 mm (`MOTOR_PRELOAD`, assumed, K2): simply supported 49.6 mm between the screws, load 18 mm from the -X screw, EI 63 000 N·mm² → 8.7 N, 8 MPa in the bar. Keeper 2.0. Every nut has ≥ 1.0 mm round its pocket. Load along the layers: the module prints upside down, so the walls' layers are across Z; the journal load (Y) bends the walls about X near the hole, as in gear train v2 |
| Held: what stops each part in each direction (`RETAIN`) | Section 4: every non-fixed part held within its play. Crankshafts: slot bottom −Z, tongues +Z (0.25), webs ±X, slot ±Y (checked without the legs). Idlers: pin ±Y ±Z, walls ±X (0.45). Pinion: D-shaft ±Y ±Z and spin; +X gearbox face, −X the −X wall (0.8 each; the press holds it). N20: −Z pad and V; +Z the clamp's gearbox pad (0.3 preload, `MOTOR_PRELOAD`) and can pad (0.2); ±Y the clamp's cheeks 0.2 off the gearbox flats (`MOTOR_SEAT`: they take the torque), the +X wall's steps 0.5 a side (`WINDOW`, a backup out of the torque path) and the V; +X stop block 0.2; −X the preload's grip, then its pinion against the −X wall at 0.8 (no face of the gearbox can carry a −X stop: its corners are 7.81 from the axis, the pinion's tip circle + 0.8 is 7.8). Cap: screws, skirts, tongues. Clamp: 2 screws. Keeper: recess + 1 screw. Pins: blind end −X, keeper +X |
| Assembly: the steps as Morante's hands do them; how it comes apart | Section 5 and [`assembly-steps.png`](images/verify/assembly-steps.png): every part goes in along a straight line, in the order of README «Assembly». The pinion goes on **on the bench** (steps 20–23, drawn as Morante sees them: jig on the table, +X up, `STEP_VIEW`): the pinion slid into the press jig's pocket from its open side, the gauge fork dropped into its slot over the pinion, the motor pushed down into the jig's gearbox socket (squared) until the gearbox face stops on the fork, checked against the jig, pinion and fork only (the D-shaft left out: a zero-clearance press); step 23, only if the thumb is not enough, the press cup on the can's rear for a vise; then the fork lifts out and the motor slides out of the jig, and **one drop** of motor, shaft and pinion as one body (step 24), with crank 1 turned until the pinion meshes (idler 3, its gear partner, is not an obstacle). Section 8: every nut, pin and screw reachable (pliers for nuts, hex key for screws and to seat the pins, finger for the motor, a thumb tip on the can's rim below the terminals for the press, a finger for the cup). Apart: clamp screws (2) → motor lifts out with its pinion; front cap screw → cap; keeper screw → keeper; pins pushed out from −X with a 1.5 hex key through the Ø2 holes; idlers and crankshafts lift out. Nothing is glued or snapped |
| Seats: every part fully home (section at full depth) | The motor rests on the pad and the V (contact, allowed in the spec), so it is home by construction; the clamp's rear foot sits on the end wall and its −X foot on the cap (contact). Pins bottom in their blind holes (contact) and end flush with the recess floor, under the keeper. Sections `section-4.png` (motor axis) and `section-1.png` (gear plane) |
| Print: orientation, overhang, where support goes, can pliers reach it, why each cavity exists | Module upside down (deck-level top on the bed): every gear pocket is a teardrop with 50° flanks cut flat at the circle's bottom (Morante 2026-11-14, keel option b: bridges up to 10.7 mm under idler 3, ≈ 6–7 mm under the others, no support; lowest point z 42.77) and the saddle a 50° V (first version had round pockets 30 mm up inside the gear channel: base v1's trapped support). Remaining overhang 837 mm², 287 of it over the part itself (section 6; 672 in rev 4, the rest are the flat pocket bridges and the saddle's sloped underside): nut pocket roofs (5.8 mm bridges), the gearbox pad (10.4 mm bridge between the steps), the 1.25–1.65 mm ledges at the top of the thickened lower walls, the stop block's top under the terminals (6 × 9.6, support from the bed in the open motor space, reachable from ±Y, not a seat face). Journal holes Ø4.5 and pin holes Ø3.3 are small arcs. Cap upside down, clamp top down, keeper, pinion and idler flat, gauge fork flat, press jig on its −Z face with the open side up (pocket, slot, socket and the shaft tip's U all open upwards; rev 6.1's first try, −X face down, had 81 mm² over the part at the slot's ceiling), press cup top plate down: no overhangs. Cavities: gear pockets and channels (gears drop in), webs' channels (cranks drop in), pinion zone, motor seat, nut pockets and slots, keeper recess: each has a reason; none left from base v1. Integrity WARNs (section 1): 2.8 % of the module's surface (a sampled figure: 2.1–2.8 % between runs of the same geometry) and 1.3–1.5 % of the clamp's read thinner than 0.8 mm: knife edges where two teardrop pockets meet between neighbouring gears (y −34.9), at the push-out holes' rims and where the V saddle meets its sides (module), and where the clamp's arc pad meets its sides; none carries load. The gauge fork reads 87 % «thinner than 0.8» at 0.80 mm: it is the 0.8 gauge by design, loaded only in compression between the pinion and the gearbox face. Crankshafts and legs: reused unchanged, printed and working (their WARNs are their own designs') |
| Legs (LEG_PATH 0.8) | Every leg stays ≥ 1.0 mm from the module, cap, clamp, keeper and N20 over a full turn (no pair under 1 mm in section 2; the verifier searches 1 mm). There is no flange beside the motor, so nothing at deck level needed cutting back along leg 3R's path |
| Marks: which, where, visible in which step | 1–4 dice dots beside each journal slot on the +X wall (step 4, matching the crankshafts' web dots); FRONT arrow on the front block's +X face (whole-robot step); dot on idler 3 v2's +X face (step 2); dot over the pinion's D flat (step 6); dots on the cap's +X edge over each slot (step 5). Section 10: every gear has a mark or the reason it needs none (idlers 1–2: identical teeth) |
| Carry-over: what earlier versions had and whether it is still here | Gear train v2: wall gap 0.25 / 0.45 (now fits), 0.2 backlash (`CD_EXTRA`), gear offsets and idler phases, idler first layer 0.2 smaller. Test cap v2.1: tongues over the walls' outer part (`TONGUE_IN`/`OUT`), flat tongue ends, skirts with 0.4 lead-in, 5 mm plate, +X dots, crank gear keep-out zones with the cap's play. Test spine: dice dots by each slot. Base v1 faults fixed: cap fits from `fits.py`; every part held; pins reachable and pushed out; no closed recesses; marks present |

## As a stranger would see it

1. **The motor is not located in X by a face.** It is held by the clamp's preload (pad 0.3 into the gearbox,
   ≈ 9 N, `MOTOR_PRELOAD` assumed); if it is pushed, the pinion's face meets the −X wall or the gearbox meets the
   pinion at 0.8 mm. A −X face on the gearbox is impossible with this pinion (above); a +X stop block sits behind the
   can. K2 prints two clamps (0.2 clear and preloaded) with an X push-out test.
2. **The cap is held by two screws, not three.** There is no room for a third: behind crank 4 the deck ends (the
   carcass outline is 3 mm inside at y 31.75 on the body axis) and both sides of the motor are leg paths. The cap's
   rear part (crank 4) hangs on the −X bridge, screwed right next to it (shared screw at y 12.18), and the clamp
   presses the bridge too. K3 should include the bridge.
3. **The clamp bar is long (57.7 mm) and passes over the pinion's teeth.** Its underside is relieved 1 mm over
   the pinion (x ±4.5), so it is 1.8 mm above the teeth (0.8 keep-out + 1.0); the motor cannot lift with the preload,
   and the gears are also checked with it lifted 0.2 (GEAR_MOTION).
4. **Wires.** The terminals' wires leave on +Y over the can's stop block, under the clamp bar, between the can and
   the end wall (open above z 69); «+» (red, +Y) and «−» are sunk in the end wall's +X face (MARKS). Leg 3R passes
   2.9 mm from the motor's −Y side at z 72.8: no wire on −Y. Their path to the switch is Part B's (I12). The wire
   notch the review asked for is not modelled: the clamp nut's slot fills the end wall's +Y top (open item).
5. **The module's I7 nut traps are proposals.** Four M3 nuts from below (front block, two in the saddle at x 20 and
   32.5, −X boss), each ≥ 1.1 mm inside the shell's inner surface (section 12, i7-nut-1..4); screw lengths in the
   README's I7 table, set when Part B's floor is drawn. The deck lip is a `WINDOW` fit (88 mm outline: `LOCATOR` is
   for ≤ 40 mm). Service: legs off, robot on its back, 4 screws from below.
6. **The module is not all inside the shell.** Section 12 checks it against the carcass inset 2 mm below the deck,
   with three named, bounded exceptions: the keel (lowest z 42.77 ≥ 42.7, Morante's option b), the rear end (crank
   4's gear room ends at y 33.78, the shell's inner face is at 32.75: the module stays inside the carcass, ≥ 0.07,
   and Part B's bowl opens there) and the carcass's top under the head (y −47…−14, the deck replaces it): the module top stands at most 4.38 mm out of the carcass there (lowest carcass top under its top face 70.42, y ≈ −44, 0.25 mm ray grid; the reviewer's 70.3 at x 42 is under the pinion window, module top 61.2 there), the carcass top taken as the highest ray hit under z 80 below the module's top face (rev 6 kept the highest hit, the head at z 88–108, and bounded 1.56); the allowance box now reaches the module top (74.8), so the 72.3–74.8 band is checked too (`cad_verify` checks an allowance's box past the entry's `z` filter, test `test_allowance_is_checked_above_the_z_filter`).

## Pre-mortem

1. **The tongues or the D-bore are too tight** (assumed fits). Prevented by K3 and K1 before the module is printed;
   both values live in `fits.py`, one change and a rebuild.
2. **Support or sag in the upside-down print spoils the gearbox pad** (a 10.4 mm bridge that the motor rests on), so
   the pinion sits low and binds. The pad is checked with the depth gauge (`MEASURE`: 8.75 ± 0.1 from the top face);
   the backlash band has 0.1 mm of room; K2 prints the same pad.
3. **The thin ribs beside the crank 3 and 4 slots (1.3 mm) crack** when a crankshaft is pressed in or a leg jams.
   They carry the journal only near their root; the slots have 0.5 mm lead-ins so nothing is forced; if K3 shows a
   crack, the idler 3 pocket can narrow to 2.5 mm walls only below the journals.
4. **The 10.7 mm floor bridge under idler 3 sags** into the 0.5 mm `GEAR_TIP` room (it prints upside down, the
   floor is the last layers over the pocket) and the idler rubs. K3 now carries the idler 3 pocket printed upside
   down as the module: pass = idler 3 v2 turns by hand with no rub. If it rubs, `GEAR_TIP` under idler 3 grows (the
   floor stays at z ≥ 42.7: Morante's keel bound) or the floor gets two ribs across.
5. **The thin rear skin at y 34.73** (0.95 mm outside crank 4's gear room, nothing pushes on it) prints poorly or
   opens. It is not a seat or a load path; the crank's gear still stays in its room. Morante chose a 2 mm bump
   in Part B's shell over it (plan decision 13), so the skin is covered and no knock reaches it.
6. **The pinion ends off its 0.8 mm** (pressed crooked or not home). The press jig squares the pinion in its
   pocket and the motor in a gearbox socket (10.4 × 12.4, `MOTOR_SEAT`, 6 mm along the gearbox); the fork, measured
   before use (0.8 ± 0.05), ends the press on the gearbox face. **Bench check before the drop** (`MEASURE`): with
   the motor still in the jig the fork comes out snug and slides back in snug; after the drop the fork cannot reach
   the gap (the module's +X wall, the clamp and the cap are round it). K1 uses the same jig, fork and cup, so the
   method is proven before the motor's own pinion, and records «by thumb» or «needed the vise».

# Part B1 (the looks shell `chassis` and the `crank-cover`) · design review, interim

Numbers from [`verify-result-b1.txt`](verify-result-b1.txt) (`verify_b1.py`, full run, 36 steps of 10°) and from
`shell.py`'s output; pictures in [`images/verify-b1/`](images/verify-b1/). **Result: FAIL, 8 failures, all one
cause: the forks' Z float (below).** B1 is not finished: the switch retainer, the second lead clip and the lead
channel are not modelled (the switch pocket's layout clashes with the crank window, «As a stranger» 2).

| Question | Answer and evidence |
|---|---|
| Fits | Every clearance from `fits.py` (`shell.py` types none). Measured in section 2: cover screws, every fork nut and both cover nuts 0.15 (`STEEL`, nuts in pockets of `K.NUT_AF + 0.3`); cap, clamp, keeper, keeper screw, N20, motor leads to the shell 0.50 (`WINDOW`); forks to the shell 0.80 (`LEG_PATH` 0.8: pocket `FORK_GAP` = 0.8 + `FORK_ALLOW` 0.2); legs 4L/4R 0.89; crankshaft 4 0.80. The nut pockets now have a corner along their slot (`shell.nut_pocket`): base v1's hexagon put a flat across the slot's end, so 0.95 mm³ of a nut stood in the wall and a nut could not reach its screw's axis (probe: nut volume outside base v1's pocket 0.946 mm³, outside the new one 0.000); the allowed contacts that hid it are gone. Front block v2 to the shell: 0.000 mm³ overlap (it was 1188), the band cut round it by `front_block.clear_outline()` (stage `fb-clear`, keyed on the block's STL and `front_block.py`) |
| Strength | Bowl skin 1.6 (no load but the bosses), band skin 1.2, seat 2.0, slide lip 3.0 × 1.2. I7 bosses Ø9 up to the module's underside, ≥ 1.4 of boss over each head (`I7_UNDER_HEAD`). Every feature standing on the deck is rooted 0.5 into it (`DECK_ROOT`): cover post 2 and the right pad lip floated 0.09 over the deck (its top is 74.7 there, not 74.8) and were thrown away by export (467 mm³) |
| Held | Section 4: module, cap, clamp, train and crank cover held within their play. **FAIL: every fork moves 0.5+ in ±Z**: the pocket's Z gap is `FORK_GAP` 1.0 a side (the leg path's 0.8 + 0.2), the screws' tips slide in the fork's holes, so the fork floats 1.0 each way against `RETAIN` play 0.5. The spec is not loosened; the decision is in the report |
| Assembly | Section 5: every step passes. The module with its train and cap goes in from +Z (it was «blocked 1.25 mm out»: the module path was swept in 1 mm steps and a 0.23 mm skin at the module's rear end let slivers of the bump survive between the steps; now 0.2 mm steps). Then forks, legs, motor and pinion, clamp (the clamp notch in seat and lip), leads, crank cover and its 2 screws, the I7 screws from below |
| Access | Section 8: every fastener reachable (I7 from below with the robot on its back, cover screws from above, cover nuts with the pliers' nose on the bare shell, fork screws from the band top and from below) |
| Print | Shell band top on the bed: 16 383 mm² needs support, 7 261 mm² over the part itself (largest near the switch's lever slot, [69, 39.9]); three slivers of 0.4–0.6 mm² read as thin upright features (open). 3.6 % of the surface reads under 0.8 mm (mesh slivers from the carcass and the stepped path cut, none loaded). Crank cover printed upside down (top face and its arrow on the bed): 18 mm² over the bed; its rear lip (1.2 × 8.5 × 7.6) is the thin upright WARN, nothing pushes on it |
| Marks | FRONT arrow sunk 0.5 in the seat at x 26.2, y −41.5 (placed by `shell_marks()` on seat material clear of the front block and `DRIVE_CLEAR`: at CX it was cut in air). Fork numbers 1–4 dots beside each upper screw, every dot checked on the STL 0.5–0.6 deep (fork 4's row ran under the slide lip before). Cover: FRONT arrow on its top |
| Mass | Shell 69.6 g (56.16 cm³), crank cover 4.0 g: 73.6 g against the plan's 86 g for the shell. The front block cut took 2.2 g; nothing is dropped by export (0 mm³) |
| Carry-over | Base v1's fork mounts and band outline, its nut pocket corrected; Part A's I7 nuts and screw rule (stock M3×6 ×3, M3×8 ×1, every counterbore mouth open on the bowl's slope: ray probe) |

## As a stranger would see it (B1)

1. **The forks rattle 1 mm up and down.** The pocket's Z gap was raised to clear `LEG_PATH` everywhere; a fork only
   turns about Z, so its top and bottom faces need a turning fit, not the leg path's. This is the test frame's old
   failure («did not hold its fork»).
2. **The switch pocket has no full floor.** Its −X end (x 53.5–57) is over the crank window (x up to 57.02, y up to
   32.79), so the crank webs sweep under it; its +X end (x 66–68) is over the module. The floor is only x ≈ 57–66.
3. **Only one lead clip**, at (69.5, 24); no channel from the terminals to it.
4. **The front block nuts** slide in towards CX, into the module's space: they go in on the bare shell.
5. **`shell.py` is 740 lines** (over the 600 rule): split due (features vs pipeline).

## Pre-mortem (B1)

1. Forks rattle and the legs' gait wanders: fix the Z float before any print (report, option a).
2. The switch is pushed into the crank webs through its open floor: the switch layout decision first.
3. The 0.2 mm module path leaves a stepped surface at the module's rear end (45 pinch edges notched at r 0.1):
   cosmetic inside the bowl; K-coupon of the rear end if it prints badly.
4. The front block changes again: `fb-clear` re-keys on its STL, the shell rebuilds in ≈ 25 s.

## Friction clutch (2026-11-16, plan rev 2 approved)

| Question | Answer, with its number or picture |
|---|---|
| Brief → how met → how checked | Window 129–196 N·mm: set per unit with DIN 988 shims (lever test in `verify.py` MEASURE: 440–665 g at 30 mm). Notch x −3.3 to −5.4, r 5.5 (`build.py` `NOTCH_*`): `collar-clear` keep-out passes. Motor axis +0.1 (`robot.MOTOR_CD_EXTRA`): pinion × idler 3 v2 gap in section 3 (GEAR_MOTION, motor also lifted 0.2). I7 nut traps unchanged (`I7_NUTS` untouched). No clicker. Pinion face 4 mm (`R.PINION_FACE`); gearbox face kept at x 3.3 (`R.GEARBOX_X` now pinion + shoulder + 0.8). Cap, clamp top, front block and crank cover unchanged: `CLAMP_Z0` held at 79.85 (pinion tip 0.7 radial, 1.7 under the relief); shell.py and front_block.py not edited or rebuilt |
| Fits | Sleeve and collar D-bores `DSHAFT` (K1, assumed); pinion on sleeve `SLIP_BORE` 0.1 a side (new, assumed, CL1); collar to notch 1.0 radial and 0.8 to its end (`GEAR_AXIAL`); shoulder r 4.5 and wave washer r 4.0 inside the `idler3-ring` keep-out r 4.77 (\|x\| ≤ 2.95): idler 3 floated tip r 5.27 |
| Strength | Sleeve wall 1.0 (K1 tests 1 mm walls at 215 N·mm); collar 1.2 long on the D: pull-off ≥ 170 N is a K1 test, not a calculation; pinion 4 mm: Lewis ≈ 19 MPa worst (plan §3) |
| Held | Pinion, washer, shims spin on the shaft between the shoulder and the collar (RETAIN spin X); sleeve and collar held by their press, with the 0.8 gauge / notch end behind them (as the old pinion) |
| Assembly | One push in the press jig: collar (dot to the shaft's flat), shim, wave washer, pinion, sleeve, fork, motor (section 5). Service: collar prised off with two small screwdrivers, a new one pressed (0.1 g) |
| Print | Pinion and collar flat; sleeve shoulder down (D-bore vertical, no support) |
| Marks | Sleeve and collar: a dot over the D's flat; pinion none (either way round) |
| New WARNs (90 → 94) | +5, −1: `clutch-sleeve` 1.5 % and `clutch-collar` 1.9 % of the surface read under 0.8 mm (the D-bore's flat corners, lead-in rims and the dot; the walls are 1.0 and the collar 1.2 thick, none a knife edge that carries load); `clutch-sleeve × n20-shaft` and `clutch-collar × n20-shaft` `DSHAFT` assumed (K1); `pinion × clutch-sleeve` `SLIP_BORE` assumed (CL1); the old `pinion × n20-shaft` DSHAFT WARN is gone. The module's overhang went 837 → 848 mm²: the notch's arc is a roof when the module prints upside down, 11 mm² over the bed, none over the part (287 unchanged) |

Pre-mortem: (1) the collar's 1.2 mm press lets go under the spring and the slip creeps (K1 pull-off decides; fallback: collar longer into the notch's 0.8, or Loctite 638 on the tip); (2) PLA faces glaze or smear during a long stall (CL1-heat; kit rule «humming, legs stopped = switch off»); (3) the wave washer's rate is stiffer than 60 N/mm and one 0.1 shim jumps past the window (two washers in series; the seller's load table is checked before buying); (4) the collar's dot is set the wrong way and the press jams (the thumb test: if it does not go in by thumb, stop and re-align before the vise).
