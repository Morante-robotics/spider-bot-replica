# Spider-Bot · Looks first

Part of the [build log](../build-log.md): its [contents](../build-log.md#contents), [open items](../build-log.md#open-items) and [glossary](../build-log.md#glossary).

## Looks first

The second design, started on 2026-11-17 after the first ([Legs and drive](3-legs-and-drive.md)) drifted away from the
toy: the specification is now the toy and jenscolt's model, and the mechanism is fitted inside the looking parts. It
went through a mock-up in simple shapes (N0), the real parts as light meshes (N1), and a first print-detail attempt
that did not fit at 65 % (N2 rev 5). Meshes then proved a dead end, so every part was rebuilt as parameters and only
those measure. Round r00 of N2 designed the inside (drive and power); the shells then took an hour to build, so their
leg clearances were redesigned as simple shapes and every build and check came under 40 s, with 0 failures. Then the unused front sensor was removed and the mouth closed with a front panel, and the robot was split into one print plate per colour for a first test batch. That batch failed as a robot: the parts print, but the mechanism is too fine for the printer at this size. Morante then asked for a top-down redesign in three phases: the size (S 1.0, set by the smallest features the printer made well), whether the whole mechanism turns at that size (it does, with no large layout move), and what to simplify (a 3-part flat drive unit, M3 screws only, engraved marks, and a new leg ↔ crank joint). The design now passes the full check; nothing has been printed at S 1.0 yet. Older
entries are shortened to their summary; the full text is in git (links).

### Redesign: looks first

**Phase 3 · Mechanisms · 2026-11-17** · Status: ✅ done; carried out by the entries below

> **In short.** The robot had drifted away from the toy: the dome sat on a tall black base with the gear box under it,
> and the legs hung like stilts. Every design change also took days, because the checks chased under a millimetre and
> a degree on shapes that were not yet decided. So the design restarts looks-first, with three levels of detail so a
> change costs seconds, and the size is worked out again from the smallest motor and the button cells that can feed
> it. A coarse estimate puts the scale at 60 to 80 %, not 120 %. The next step is to measure the original toy.

<img src="https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/images/plan-e.png?raw=true" alt="Part E mock-up of the robot, archived">

*Fig. 1 · The archived Part E mock-up. Look at the tall black base under the dome and at the thin legs: this is what
the redesign leaves behind.*

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#redesign-looks-first) (archived text, with steps, figures and data).

### N0 mock-up: the looks robot in simple shapes

**Phase 3 · Mechanisms · 2026-11-18** · Status: ✅ N0 look approved, N1 next

> **In short.** The first level of the redesign is built: a mock-up of the whole robot in simple shapes, with
> jenscolt's body and base at 60 %, eight legs shaped like his, the toy leg's motion, and the motor, six button cells
> and switch inside. One run draws four views and checks 24 crank poses in about 2 seconds. Every check is inside the
> 5 mm tolerance of this level, and the robot reads as the toy: the legs are thick and curved, the body sits low.
> Next is N1, the real looking parts as light meshes.

<img src="https://github.com/Morante-robotics/spider-bot-replica/blob/n2-on-meshes-2026-11-20/cad/mockup/images/n0-mockup.png?raw=true" alt="The N0 mock-up from four views: three-quarter, front, side and from below">

*Fig. 1 · The mock-up, default parameters, crank pose 0. Look at the thick legs rising level from the base and then
bending up to the knee, the blade coming down to the foot, and the base standing clear of the ground. The grey frame
is the ground plane.*

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#n0-mock-up-the-looks-robot-in-simple-shapes) (archived text, with steps, figures and data).

### N1 form: the real looking parts as light meshes

**Phase 3 · Mechanisms · 2026-11-19** · Status: ✅ N1 look approved, N2 next

> **In short.** The second level of the redesign is built: jenscolt's real body, eyes, base and legs at 60 %, simplified
> to light meshes, moving on the N0 motion with the motor, cells and switch inside. The legs are his own, stretched to
> reach N0's knee path, and each leg root has a window in the body and base. The 24-pose check passes within 1 mm
> (the legs graze the base by 0.4 mm), a run takes about 10 seconds, and Morante compared the views with his photo of
> the toy and approved the look. Next is N2, the print detail.

<img src="https://github.com/Morante-robotics/spider-bot-replica/blob/n2-on-meshes-2026-11-20/cad/mockup/images/n1-mockup.png?raw=true" alt="The N1 mock-up from four views: three-quarter, front, side and from below">

*Fig. 1 · The N1 mock-up, crank pose 0. Look at the real dome with its two eyes, two small eyes and front dome, at
the thick curved legs that now have jenscolt's shape, and at the base standing 12 mm off the ground. The windows are
hidden behind the legs. The grey frame is the ground plane.*

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#n1-form-the-real-looking-parts-as-light-meshes) (archived text, with steps, figures and data).

### N2 rev 5: the inside does not fit at 65 %

**Phase 3 · Mechanisms · 2026-11-19** · Status: ↩️ restarted from scratch ([Only the parametric parts measure](#only-the-parametric-parts-measure))

> **In short.** The N2 robot now runs on the design-rounds harness, and its plan was laid out again inside the
> unchanged look at 65 %. Nine layouts were tried and none fits: the best has its tightest pair 1.75 mm too close, and
> with real shapes instead of boxes 20 pairs still overlap. A sweep for the one scale at which everything fits and can
> be assembled found a second problem at 65 %: the motor sits over the spine cap, so the cap, its screws and the
> crankshafts cannot go in after it. Scale does not fix that, so N2 is paused until Morante decides how to change
> the assembly order.

<img src="https://github.com/Morante-robotics/spider-bot-replica/blob/n2-on-meshes-2026-11-20/cad/robot/images/plan-exploded.png?raw=true" alt="Exploded view of the N2 plan, rev 5: body, eyes, base, motor, gears, cell holders, switch and legs, with numbered labels (Spanish)">

*Fig. 1 · The plan, rev 5, exploded (labels in Spanish). Coloured blocks are parts not yet modelled; the grey bowl is
the base and the yellow shapes the legs. Look at the purple and green blocks crowded between the crankshafts and the
dome: that is where the fit fails.*

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#n2-rev-5-the-inside-does-not-fit-at-65-) (archived text, with steps, figures and data).

### Meshes become parameters

**Phase 3 · Mechanisms · 2026-11-20** · Status: ✅ parts converted

> **In short.** Building on jenscolt's STL meshes stopped working: the legs came out warped, the body is 102k
> triangles, a STEP sewn from a mesh weighs 50–180 MB, and scale and wall thickness cannot be changed apart.
> Morante decided to stay on build123d and convert every mesh into parameters once, keeping the meshes only as
> references. A new tool measures how far a rebuild is from its reference, and the eyes, base, body and legs are
> converted and pass (0.92, 0.83, 0.69, 0.89). N1 has to be rebuilt on these parts next.

<img src="../cad/carcass-jenscolt/images/conversions-vs-reference.png" width="640" alt="Four rows, each with jenscolt's mesh in grey on the left and the parametric rebuild in colour on the right: body, base, leg, eyes">

*Fig. 1 · Reference (grey) and rebuild (colour) of the body, the base seen from below, one leg (blade and arm) and the
three eyes, same view for both. The reference's scribbles and spikes are mesh noise; the rebuild is smooth. Look at the
body: the rebuild has the eye barrels, side scoop and rear lip but not the curved panel lines on top.*

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#meshes-become-parameters) (archived text, with steps, figures and data).

### Only the parametric parts measure

**Phase 3 · Mechanisms · 2026-11-20** · Status: ✅ done; N2 continues in [N2 round r00](#n2-round-r00-the-inside-and-the-leg-hold)

> **In short.** After the conversion, the N0 and N1 mock-ups and every N2 fit probe still measured jenscolt's
> meshes. They were removed, and N2 starts again from scratch on the four parametric parts; the approved motion
> (scale, crank, leg path) moved to a small module that reads no mesh. Checks now refuse an STL older than the model
> it was exported from, the fidelity limit grows with the part's size, and a part departs from a rule only through an
> exception Morante approves. Under the new limit the eyes and the leg blade pass; the leg arm and the base do not yet.

[Full entry](https://github.com/Morante-robotics/spider-bot-replica/blob/14d512996da3c506c01acb43c4fcb56bd19c3970/build-log/3-legs-and-drive.md#only-the-parametric-parts-measure) (archived text, with steps, figures and data).

### N2 round r00: the inside and the leg hold

**Phase 3 · Mechanisms · 2026-11-23** · Status: ✅ r00 is the robot, printing next

> **In short.** The robot's shells had taken 71 minutes to build and its fit check 19, and the design was stuck on
> tolerances of a few tenths of a millimetre in places that are not critical. Morante asked to relax them; with that,
> the inside (drive and power) was designed for the first time and the whole-robot check came out with 0 failing and
> 4 at tolerance of 318. The smoke check found one real fault: with the body on, a leg could slide outward along its
> crank pin and come off; a snap groove on the pin fixed it. The full `cad_verify` of the whole robot then passed
> with 0 failing, the looks judge gave 0.66 (threshold 0.6) and Morante said «se parece»: r00 is the robot, with no
> refine round, and he goes straight to printing it.

Context: the robot is `cad/robot/` at scale 0.70 (see [Open items](../build-log.md#open-items)). Each part is built
from parameters, and the shells (base, body, legs) are carved by the legs' sweeps, which is hundreds of solid
operations; the fit check then tests every pair of parts over 24 crank poses. Before this entry the inside did not
exist, so the smoke check could only say «not held».

#### Steps

1. **Relaxed two checks** (Morante: «se laxó con tolerancias muy pequeñas en sitios no críticos para poder avanzar»).
   A new fit `LEG_OPEN` (0.4 mm) is used for the leg's neck in the open-top window of all 8 legs: leg 3 measured 0.41
   against the 0.5 of `LEG_PATH`, and the leg is located by its pin, the window only clears it. In `cad_verify`, a
   zero-area face on a mesh that is otherwise watertight is a warning, not a failure.
2. **Shells made cheaper to rebuild.** Every stage (base, body, legs) has its own cache key made from its source, so
   an edit to the body leaves the base and the legs warm (a warm re-export takes 40 s, a rebuild 35 minutes).
   The leg bores are widened by the drift of each leg over the 24 poses (0.12 / 0.07 / 0.09 / 0.17 mm), the base
   keel has screw bosses with counterbores, and the body has 5 mm LED bores at the big eyes (the small eyes' bores
   are vented), a switch slot with its keeper (throw 1.5 mm, a standard value: the SS12D00 datasheet has to
   confirm it) and the power pockets. A bug where `clean()` changed its input and left an invalid body is fixed. The
   body is now 35.3 cm³ (≈ 44 g), one valid solid.
3. **Designed the inside**, in two modules that each have their own check, merged by `interior.py`:
   - **Drive** (`drive.py`): the spine (1.4 g), the four cranks with the legs' pins (0.33 g each), idlers 1–3,
     sleeves, the 15/20-tooth transfer gear, the drive unit (1.8 g), the pinion (0.22 g), the N10 motor as a box and
     the M2 screws.
   - **Power** (`power.py`): the cell holder (4.1 g), 2 × 3 AG13 cells with springs and locating rings, a nickel
     strip, a lid with snap lips and a key pocket, the SS12D00 switch, the LEDs at the big eyes, the resistors
     upright and the JST connector glued.
4. **Hardware changed** (see [`hardware.md`](../hardware.md)): the holder screw is M2 × 6 (was × 8), the keel
   screws M2 × 4 (was × 6), all with flush heads, and a transfer axle M2 × 12 was added, which the plan's count did
   not have.
5. **Ran the checks.** `verify.py` merges the gears, the pair gaps and the keep-out zones of both modules and orders
   the assembly by the plan's steps (interior up to step 9, legs, holder, motor, cells, lid, body). The
   whole-robot fit check (`check.py`, 19 min on a shared CPU) gives 0 failing and 4 at tolerance of 318. The smoke
   check fails on the leg hold (below) and has 4 hairlines, «gap 0.20 < 0.2», accepted under the relaxed rules.

#### Result

<img src="images/leg-x-hold-pin.png" alt="Three views of the real CAD: the robot without its body with one leg in orange, the leg's tube on its crank pin, and the leg slid off the pin">

*Fig. 1 · The leg hold. Left: the robot without the body, crankshafts in blue and one leg in orange. Middle: the
leg's tube seated on its crank pin, as it should be. Right: the same tube slid 6 mm outward and off the pin, which
nothing stops once the body is on. Real CAD, rendered from the exported parts.*

The four at tolerance are paths and fits within 0.1 mm of their limit: the drive unit's assembly path against the
spine (0.01), idler axles 1 and 2 against the drive unit (0.0 each) and the cells' path past the nickel strip (0.0).

**The leg hold.** With the body on, a leg slides outward along its crank pin by up to 6.25 mm (leg 1) while the pin
engages only 3.7 mm. The leg's window in the body is the union of its 24 poses, so it leaves 1.5–6 mm of slack.
Two fixes were tried and failed: a collar on the pin's tip cannot fit, because the leg's own arm lies on the pin's
axis past the tube, and a post on the body also failed. Separately, leg 2's end tube is detached in
its STL (joint radius 1.75 against a bore of 1.84): a model bug to fix whichever option is chosen.

#### Decisions

- Tolerances relaxed in places that are not critical, to keep moving (Morante, 2026-11-23).
- Options for the leg hold (the fix chosen afterwards is option A, commit
  [77161ac](https://github.com/Morante-robotics/spider-bot-replica/commit/77161ac)):
  - **A (recommended):** a snap groove on the pin (Ø3 → Ø2.3, 0.8 wide at x = 7) with a bead in the leg's bore and
    a slit, tried first on a 3 g coupon.
  - **B:** a pin 1 mm longer; it does not solve leg 1.
  - **C:** a tab on the body; it depends on the pose and rebuilds body and base.

#### Close of round r00

`rounds.py status cad/robot`, 2026-11-23:

| Round | Gates | Score | Passed | Caps |
|---|---|---|---|---|
| r00 | PASS | 0.66 | yes | none |

- **Gates:** `cad_verify` of the whole robot, 0 FAIL (`verify-result.txt`). Two bookkeeping fixes: its section keys
  are now the heading's first word («assembly order» became «assembly»), and plan m13 reads the «motion» check. Plan
  m14 stays «failed» only because the judge cannot see code; checked by hand, the meshes are read only by `views.py`.
- **Looks judge:** 0.66 against 0.6, passed, so no refine round was asked.
- **Morante:** «se parece». r00 is the robot.
- **Coupons skipped:** Morante prints the whole robot instead of the coupons. The leg snap is tested on the first
  plate (the base and one leg) before the other seven legs are printed.
- **Shopping list:** [`hardware.md`](../hardware.md) now counts every bought item from the code (motor, 6 cells,
  3 springs, nickel strip, switch, JST-XH 3-pin, 2 LEDs with resistors and 7 M2 screws in four lengths).

#### Next

Print the robot: see [Print plates by colour](#print-plates-by-colour).

[↑ Contents](../build-log.md#contents)

### Fast shells: clearances designed, not computed

**Phase 3 · Mechanisms · 2026-11-23** · Status: ✅ every build and check under 40 s, whole-robot check 0 FAIL

> **In short.** The base took 28 minutes to build and the body about an hour, because the room each leg needs was
> computed: hundreds of convex hulls around sampled leg points, cut one by one from curved skins. Each leg's room is
> now one simple prism whose outline is measured from the leg's motion, and each shell is one fuse and one cut. The
> base builds in 22 s, the body in 28 s and the check of the whole robot runs in 37 s with 0 failures (5 before).
> Morante chose the shapes on three comparison sheets.

Context: Morante set the rule that any build or check over 40 s is a bug (aim for 10 s). The causes were measured in
the previous session (base 1669 s, body ≈ 3500 s, `body.step` 152 MB); this entry is the fix.

#### Steps

1. **A window from the motion.** For each leg, the base wall points that the leg comes within its clearance of
   (WR 0.9 mm, at its 24 crank poses and along the slide onto its pin) are seen along the wall's normal; their lowest
   point per 0.25 mm column is the window's floor, open to the top. The outline, buffered and simplified, has 11–13
   straight sides and is cut through the wall as one prism ([`cutters.py`](../cad/robot/cutters.py)). Wall left
   between two windows narrower than 4 nozzle lines joins the first window. Prototyped on meshes (seconds per try),
   then built in OpenCascade.
2. **The body the same way.** A notch from the rim for each leg (its 24 poses, and the body pressed on from above at
   crank pose 12), and a shallow pocket where a leg nears a face below the rim (the rear tab, legs 3 and 7). What does
   not depend on the legs (shell, eye cups, snap fingers, switch keeper, bores, pockets round the power parts as
   boxes) is one cached stage. The x-stop posts were found once and frozen.
3. **Proof on meshes, inside the build.** Every leg is checked against the built shell at every pose and along its
   path with manifold3d (a few seconds). This replaced a volume check around every boolean.
4. **The checks.** `cad_verify` remembers the legs' frames (11 000 calls had rebuilt each leg's shape: 9 s), measures
   joints with one gap query, advances assembly paths by the free gap, runs retention and print in a second process,
   and lets an assembly step set the crank pose it is done at.
5. **Removed**: the hull and offset code of `shells.py` (768 → 450 lines), the stage-cache tool, 1.6 GB of caches.

#### Result

| What | Before | After |
|---|---|---|
| Base build | 1669 s | 22 s |
| Body build | ≈ 3500 s | 28 s (40 s when its fixed stage is rebuilt) |
| Whole robot, each part | — | ≤ 26 s (80 s for all 34 parts) |
| `cad_verify verify.py --quick` | 70 s, 5 FAIL | 37–40 s, 0 FAIL |

<img src="images/speed-1-windows.png" alt="Base from four sides and a close-up: jenscolt's reference, the base with computed windows, the base with designed windows" width="720">

*Fig. 1 · Decision 1, the base windows: reference, computed (before), designed (accepted). The floors stay at the
same height; the thin posts the old pads left above the rim are gone.*

<img src="images/speed-2-front.png" alt="Front of the base: reference, the old relief and bulge, the smooth wall; and the front arms at their closest pose" width="720">

*Fig. 2 · Decision 2, the front of legs 0 and 4: the relief and bulge are dropped; the arms clear the smooth wall by
0.40 mm (bottom row).*

<img src="images/speed-3-body.png" alt="Body from six sides: reference, the version in the viewer, the body with designed notches" width="720">

*Fig. 3 · Decision 3, the body: a notch at the rim for each leg, a shallow pocket on the rear tab, the x-stop posts.
The middle column is the body as the viewer had it, before its rim cuts.*

#### Decisions

- Windows as designed; smooth base front, no relief («Lisa»); body notches, tab pocket and frozen posts (Morante).
- No 1.2 mm pads round the windows: open-top windows carry no load (the leg is held by its pin). With a 1.2 mm wall
  the front arms came within 0.14 mm.
- Legs 1, 2, 4–7 go on with the crank at pose 0; after half a turn, legs 0 and 3 and the body.
- Legs 0 and 7 may slide 1.65 mm towards their crank at pose 0 (Morante: «Aceptar 1,6 mm hacia dentro»).
- The back pocket is a cup (the bare sheet came loose), and the switch keeper's bar no longer overhangs the switch.
- Carving on meshes (STL only) was not needed: the STEP for Onshape is kept.

#### Next

Round r00: the looks judge and Morante's «se parece»; the half turn in the workshop kit.

[↑ Contents](../build-log.md#contents)

### Front sensor removed, mouth closed

**Phase 3 · Mechanisms · 2026-11-24** · Status: ✅ done, before plating

> **In short.** jenscolt's front «sensor» (a ball on a stem hanging in the mouth) does nothing in the toy, so it is
> no longer placed. The mouth is now closed at the front face by a 1.2 mm panel flush with the body's skin, which also
> hides the body's two front snap fingers. Body valid, whole-robot check still PASS, 0 FAIL.

Morante, looking at the robot before plating: «elimina ese palo y la bola, que no sirven para nada». The two vertical
columns he saw in the mouth are the body's two front snap fingers (x ±6, 0.8 × 5 mm, flexing length 8 mm) under ribs
on the base's front wall. With the rear tab they are the only retention of the body ([decision m22](#n2-round-r00-the-inside-and-the-leg-hold)), so
they stay, but behind a cover.

#### Result

<img src="images/mouth-closed.png" alt="Front of the robot before and after">

*Fig. 1 · Left: before, with the stem and ball and the open mouth. Right: after (closer view), the panel closes the
front down to the base. The two views are at different zoom.*

- `eye_cups()` no longer places the sensor and `body_static()` no longer adds its stem (`cad/robot/shells.py`);
  `cad/eyes` still builds the sensor as a converted part, it is just not placed.
- `front_panel()` (same file) is fused into the body: 1.2 mm thick (the minimum loaded wall, rules 3.2), x ±18, z ≈ 13.2–27.3, its outer
  face the skin's front swept down, flush round the chin arch and covering the arch and the slit below it, down to
  0.2 mm above the base's front top (the same seam as between body and base). The snap fingers keep their flexing
  length free (about 1.7 mm of room in front of them).
- Body: 1 valid solid, 35 416 mm³ (35 002 before). Leg gaps ≥ 0.53 mm over 24 poses, lift ≥ 0.55 mm. A ray scan from
  the front finds no ray through the panel, only the 0.2 mm seam at its bottom edge.
- Full check: PASS, 0 FAIL, 95 WARN (the same rows as before), [`verify-result.txt`](../cad/robot/verify-result.txt).

#### Decisions

- **Close at the front, not inside.** A first try cut the chin arch as a 1.4 mm recess closed behind it. Morante:
  «No está bien. Tiene que cerrar por delante no por dentro». The panel version: «Me gusta».
- `cad/body/build.py` is unchanged (its chin arch cut stays): the panel is a feature of the robot frame.

[↑ Contents](../build-log.md#contents)

### Print plates by colour

**Phase 5 · Final build · 2026-11-24** · Status: ✅ plates made; batch 1 was printed, see [Batch 1 result](#batch-1-result-the-mechanism-is-not-printable-at-this-size)

> **In short.** The robot is printed in three colours, so the parts are split into one plate per colour: red for the
> body and the eight legs, yellow for the inner mechanisms, blue for the base. Every part is its own object, so
> Morante chooses in Bambu Studio which ones to print. The first batch is the test: the blue and yellow plates whole
> and only leg 4 from the red one, to see that the leg snaps onto its crank pin and that the M2 screws bite in
> their pilot holes. The rest of the red plate follows when leg 4 works.

Morante's rule: carcass and legs red, base blue, inner mechanisms yellow. The plates are made with
[`tools/bambu_plate.py`](../tools/bambu_plate.py) with the repo's standard settings ([`print/README.md`](../print/README.md)).
Support is tree(auto), on the build plate only.

#### Result

<table>
<tr>
<td width="33%"><img src="../print/images/robot-red.png" alt="Red plate: body and eight legs"></td>
<td width="33%"><img src="../print/images/robot-yellow-inner.png" alt="Yellow plate: 17 inner parts"></td>
<td width="33%"><img src="../print/images/robot-blue-base.png" alt="Blue plate: the base"></td>
</tr>
<tr>
<td><em>Fig. 1a · Red: the body and legs 0 to 7 (leg 3 is the second piece of the top row).</em></td>
<td><em>Fig. 1b · Yellow: the 17 inner parts, each labelled.</em></td>
<td><em>Fig. 1c · Blue: the base, foot down.</em></td>
</tr>
</table>

*Previews are labelled by part and drawn in green; the colours are chosen in Bambu Studio.*

| Plate | Parts | Time | PLA | Support |
|---|---|---|---|---|
| [`robot-red.3mf`](../print/robot-red.3mf) | body and legs 0–7 (legs 4–7 mirrored) | 5 h 25 min | 86.81 g | 13.35 g (18 %) |
| [`robot-yellow-inner.3mf`](../print/robot-yellow-inner.3mf) | spine, cranks 1–4, idlers 1–3, sleeves 1–3, transfer gear and sleeve, drive unit, pinion, cell holder, cell lid | 1 h 16 min | 14.27 g | 4.17 g (41 %) |
| [`robot-blue-base.3mf`](../print/robot-blue-base.3mf) | base, foot down | 52 min | 8.02 g | 4.24 g (112 %, outside the bowl) |

Leg 3 alone is 26 min 33 s and 6.48 g; Bambu Studio names it `leg-3-7.stl` (a suffix from the tool). Support over
30 % of the part's weight is on the base, the cranks (about 140 %), the drive unit (66 %), the transfer gear (46 %)
and the spine (30 %).

#### Decisions

- **Support marks stay.** Morante: «Me vale así». The marks are on non-functional faces and get sanded.
- **No pre-print review.** Morante: «No sé para qué sirve esta revisión. Lo tengo que imprimir igual, diga lo que
  diga el revisor, ¿no?». Right: the first batch is itself the test, so the review is dropped.
- **Batch 1** (≈ 2 h 35 min): blue plate, yellow plate and leg 3 from the red one. Check the crank pins, snap bead and
  collar for support residue, the bore of leg 3 for roundness, and that sleeves and idlers stuck to the bed.
- **Batch 2** (≈ 5 h): the rest of the red plate, after leg 3 snaps well.
- **Kits in the repo.** Morante liked the workshop kit enough to keep it: «quiero que a partir de ahora los kits
  formen parte del repo». From now on every kit is made in English in [`kits/`](../kits/README.md), one folder per
  step, served by GitHub Pages. This step's kit: [`kits/01-batch-1-test-leg`](https://github.com/Morante-robotics/spider-bot-replica/tree/batch-1-kit-2026-11-24/kits/01-batch-1-test-leg)
  (archived at tag `batch-1-kit-2026-11-24` after the batch failed): the two batches, 37 assembly steps with a
  picture each, what to measure and what to film.

### Batch 1 result: the mechanism is not printable at this size

**Phase 5 · Final build · 2026-11-24** · Status: ❌ batch 1 failed as a robot; answered by the [top-down redesign](#top-down-redesign-phase-1-size-s-10)

> **In short.** Morante printed batch 1 (the blue base, the yellow inner plate and leg 3) at scale 0.70 and tried to
> assemble it. Two parts broke while he removed the support, and after two fixes the assembly still failed on five
> counts: no marks can be seen, the parts are tiny, they snap when touched, no gear turns and no screw or pin goes
> through its hole. Almost every size the design asks for is within one or two lines of the 0.4 mm nozzle, and the
> fits for it were assumed, never printed on a test piece. The next step is open: Morante chooses how to make the
> mechanism printable.

Batch 1 was the first print of the whole-robot design, and the test of fits that the ready-to-print check had marked
«assumed»: the D-shaft bore, the gear tip room, the leg path, the motor seat and the press fits. The plan was to
print it as the coupon for all of them at once. It did, and the answer is in this entry. The kit that guided the
assembly is [`kits/01-batch-1-test-leg`](https://github.com/Morante-robotics/spider-bot-replica/tree/batch-1-kit-2026-11-24/kits/01-batch-1-test-leg) (archived).

#### What broke while printing

- **The drive unit** broke while the support was being removed: its plates were 1.2 mm. Fixed in `7c37dfb`: plates
  2.0 mm, and the part printed turned -90°, which cuts its support from 66 % to 34 %.
- **Leg 3** snapped at the joint between its pin tube and the arm. First fix (`7c37dfb`): the joint Ø3.6 became Ø4.7.
  Then Morante saw light between the rod and the tube in Bambu Studio: the rod only butted against the tube's open rim,
  and the thinnest plane through the junction was 1.9 mm². Second fix (`1fb1b20`): the tube is closed at its tip and
  the rod fused to it, 17.3 mm² (the rod's own section). A new check, `cad_verify` 9b `SECTION_MIN`, fails all 8 legs
  of the old design and passes the new one; the full verify of the robot passes.

#### Morante's result

Morante, 2026-11-24, assembling what he could (the original Spanish and a translation):

- «No se ve ninguna marca impresa en ninguna pieza así que no sé cómo montarlas.» · No printed mark can be seen on
  any part, so I do not know how to assemble them.
- «Las piezas son tan pequeñas, que por la resolución de la impresora salen las cosas mal.» · The parts are so small
  that, because of the printer's resolution, things come out wrong.
- «Las piezas son tan finas y endebles que se rompen con tocarlas (como las orejeras que se me han roto y he tenido que
  imprimir de nuevo).» · The parts are so thin and weak that they break just by touching them (like the ears that broke
  and I had to print again).
- «No gira ningún engranaje porque rozan.» · No gear turns because they rub.
- «No cabe ningún tornillo ni pasador por agujeros.» · No screw or pin fits through any hole.

<table>
<tr>
<td width="50%"><img src="images/batch1-result-1.jpg" width="440" alt="The yellow inner parts assembled on the spine, seen from above"></td>
<td width="50%"><img src="images/batch1-result-2.jpg" width="400" alt="The inner assembly held between two fingers, the cranks with their axles, and a loose gear"></td>
</tr>
<tr>
<td><em>Fig. 1a · The inner assembly on the spine. The gears are there, but they do not turn.</em></td>
<td><em>Fig. 1b · The same from the cranks' end, with a loose gear on the mat. The parts are small next to a fingertip.</em></td>
</tr>
<tr>
<td width="50%"><img src="images/batch1-result-3.jpg" width="440" alt="The blue base held between two fingers, thin and flexible"></td>
<td width="50%"><img src="images/batch1-result-4.jpg" width="440" alt="Two yellow sleeves on a ruler, each about 3 mm"></td>
</tr>
<tr>
<td><em>Fig. 1c · The blue base: a thin, flexible shell.</em></td>
<td><em>Fig. 1d · Two sleeves on a ruler (cm), each about 3 mm. The idlers turn on these.</em></td>
</tr>
</table>

#### Why: the sizes against the printer

From the design numbers (not yet measured on a printed part): the marks are dots Ø0.7 mm and 0.35 mm deep at 1.0 mm
pitch (`common.dice` and `Sphere(0.35)` in `drive.py`), under one 0.4 mm line, so they do not print. The gears are
module 0.6 with 12, 15, 16 and 20 teeth, a tooth about 0.94 mm thick at the pitch circle, and a tip room of 0.4 mm
(`GEAR_TIP`, «assumed», never printed on a coupon). The walls are 1.2 mm (three lines) and the drive unit's ear 2 was
1.0 mm high. The M2 holes are Ø2.3 mm and the self-tapping pilots Ø1.6 mm, both «assumed»: `STEEL` was measured only
on M3 in Ø3.3, and the X-Y hole compensation was never calibrated (an open item).

<img src="images/batch1-limits.png" alt="Bars of the designed sizes against one line, two lines and one layer">

*Fig. 2 · Sizes the design asks of the printer, against one 0.4 mm line, two lines and one 0.2 mm layer. Red: under
two lines; orange: under three. The marks and the gear tip room are the clearest misses.*

What it proves: the failures are not a handful of bugs but a size problem. The two breaks were fixed, but the marks,
the gears and the holes are the design at 0.70 scale meeting a 0.4 mm nozzle. It also shows that the ready-to-print
gate was right to call the assumed fits risky: batch 1 was their coupon, and they all failed together, so the
result does not say which of them would have worked alone.

#### Decisions

- **Batch 2 (the rest of the red plate) is not printed.** There is no point printing seven more legs of a mechanism
  that does not turn.
- **Cold leg build.** A leg built from nothing takes over 40 s under load (`CAD_BUDGET`); it is now an open item.

#### Next

Morante chose how to make it printable: a top-down redesign in three phases, starting with [phase 1](#top-down-redesign-phase-1-size-s-10).

[↑ Contents](../build-log.md#contents)

### Top-down redesign, phase 1: size S 1.0

**Phase 5 · Final build · 2026-11-26** · Status: ✅ target scale S 1.0 chosen

> **In short.** After batch 1 failed, two attempts to thicken the mechanism in place and to bisect a scale part by part
> gave no number. Morante stopped them and asked for a top-down approach in three phases: first how big the robot
> must be, then where everything goes, then what can be simplified. Phase 1 measured the smallest feature the printer
> made well, per type, and scaled the robot to reach them: pure scaling needs S 1.17, and Morante capped it at **S 1.0**
> (225 mm across the legs, jenscolt's own size). At 1.0 the gears keep their pitch diameters with fewer teeth at module
> 1.0, and the walls need only +0.3 mm in place.

Morante's reason for stopping the probes: «falta razonamiento espacial y te centras en solucionar problemas pequeños
antes de saber qué tenemos que hacer. Yo quiero una aproximación Top-down» (spatial reasoning is missing and the work
sits on small problems before knowing what has to be done; he wants a top-down approach). Scale S is the fraction of
jenscolt's size; the batch 1 robot was S 0.70. No phase starts before the one above is validated.

#### Steps

1. List the smallest printed feature of each type, only from what was printed and measured (archive tag
   `pre-redesign-2026-11-17`).
2. Measure the ray thickness of every printed STL at 0.70 to see which parts are thin.
3. Compare three scales (0.70, 1.0, 1.17) with the bought parts (motor, cells) and one smallest part of each type
   at true size; Morante picks the target.

#### Result

| Feature | At S 0.70 | Measured minimum | Factor | Source |
|---|---|---|---|---|
| gear module | 0.6 | 1.0 | ×1.67 | gear train v2 turned at module 1 (2026-11-12) |
| wall / plate | 1.2 (spine 0.56, drive unit 0.29, idler rims 0.98) | 2.0 | ×1.67 | fork side wall, test leg v2 (`measurements.csv`, 2026-11-11) |
| crank journal | Ø3 | Ø4 (`TURN` 0.25) | ×1.33 | crankshaft journal 4.0 printed 3.9–4.0 |
| screw | M2 (Ø2.3 holes, never measured) | M3, `STEEL` on Ø3.3 | ×1.5 | clearance test, M3 column (2026-11-11) |
| mark | dots Ø0.7 × 0.35 | engraved numbers ≈ 3 mm | new type | not measured: the one assumption |

- Legs and body are near the minimum already (legs p10 ≈ 2.0 mm, thin only at spots). What is thin is the mechanism
  (gears, cranks, idlers, spine, sleeves: median ≈ 1.0, module 0.6) and the base bowl (0.7 everywhere).
- The crank spacing is set by the legs, so the gear train's size follows the robot's S. Pure scaling reaches every
  minimum only at S 1.17–1.2: 271 mm across the legs, weight ×5, motor torque ×8.6 against 0.70.
- Morante, verbatim: «S 1.0 máximo». At S 1.0 (×1.43 from 0.70) the gears keep their pitch diameters with fewer
  teeth at module 1.0: crank and idlers 12 → 10 T, pinion 16 → 14, transfer 20/15 → 17/13 (crank:motor ratio 1.07, or
  0.99 with a 13 T pinion). Walls scale to 1.71 and need +0.3 mm in place to reach 2.0; journals Ø4.3 and M3 holes
  pass by scaling.
- Below 1.0 the crank gear falls to 9 T and the walls need ≥ 0.45 mm more, so 1.0 is also the floor.
- Cost against 0.70: 225 mm across the legs, weight ×2.9, crank torque ×4.2. The motor (not bought, torque never
  measured) and the cells are sized in phase 2.

#### Decisions

- **Target S 1.0** (Morante's cap). It does not promise a fit: phase 2 checks that.
- **Printable minimums become a gate:** `cad_verify` check 13 (module, walls, marks read from the meshes; spec
  `MINIMUMS`, `GEAR_GEOM`, `MARK_GEOM`). The 0.70 design fails it 28 times. A deliberately thin feature is declared
  as an `except` box with its reason.

[↑ Contents](../build-log.md#contents)

### Top-down redesign, phase 2: the whole mechanism turns at S 1.0

**Phase 5 · Final build · 2026-11-26** · Status: ✅ the mechanism turns, no layout move needed; overlaps left are phase 3's

> **In short.** The whole robot was rebuilt at S 1.0 with the minimums, deleting every fit tweak made at 0.70, and
> checked over the 24 crank poses at 1 mm resolution. No leg overlaps a shell or another leg, and every remaining
> overlap is at most 0.40 mm. No large layout move was needed: the motor even has 22 mm free along −x. The remaining
> small overlaps and gaps are phase 3's.

#### Steps

1. Scale the robot to S 1.0, apply the minimums and delete the fit tweaks made at 0.70 (D23/D23C, arm pockets,
   reliefs, x-stop posts, spacings).
2. Re-derive the approved concepts at 1.0 (below).
3. Run the whole-robot N1 check, `cad/robot/fitcheck/n1.py`: 41 parts, 24 poses, 18 s.

<img src="../cad/robot/images/phase2/top.png" alt="Top view of the robot with the swept volume of legs, cranks and gears over 24 poses">

*Fig. 1 · From above, cut at the motor axis. Light blue: where the legs go over a whole turn; the black outline is
the base and body. Notice that the motor (green), the cells and holder (purple) and the gears (orange) sit inside the
shells, clear of the leg sweep.*

<img src="../cad/robot/images/phase2/side.png" alt="Side view of the same sweep, with the motor above the gear train">

*Fig. 2 · The same from the side, cut at x = 0. The motor (green) is the top gear's neighbour; the cranks and gears
turn in the lower half, the cells and the switch toward the front (+y).*

#### Result

| Check | Result |
|---|---|
| Whole mechanism, 24 poses | no shell ↔ leg or leg ↔ leg overlap |
| Remaining overlaps | all ≤ 0.40 mm: legs 3/7 against crank 4, legs against the crank 1/2 webs and the M3 axle heads |
| All 10 gears | module 1.0 (check 13) |
| Mass | ≈ 225 g printed, ≈ 255 g with hardware |
| Crank throw | 3.3 mm: lifting the whole weight needs ≈ 0.09 kg·cm |
| Body build | 41–47 s cold (over the 40 s rule) |
| Count going into phase 3 | 27 printed parts, 14 hardware entries, 37 assembly steps |

- Re-derived at 1.0 (concepts Morante approved at 0.70): crank 2/3 spread 4.3 + shift 2.8 (legs 1↔2 and 5↔6 0.55;
  legs 0↔1 and 4↔5 0.37), body leg cutters (BRELD 0.65, 12 cutters), back-sheet cup [3.0, |x| 17.2, z 10.0–23.7] with
  the body tab keep-out.
- Leg ↔ shell gaps 0.01–0.32 (no overlap) and the base's front-window relief (not restored) go to phase 3.
- Room: the motor has 22 mm free along −x and 17 mm above, so an N20 would fit without moving anything.
- The motor bought must give ≥ ≈ 0.3 kg·cm at 3 V (the N10's torque has never been measured): the seller's datasheet
  comes before buying.

#### Decisions

- **No large layout move.** The approach worked as intended: the size decision made the room; no sub-millimetre
  relief was needed to get a turning mechanism.
- The N1 check's sub-0.2 mm numbers are noise at its 1 mm resolution and are not acted on.

Branch `phase2-s1` (`808cf15`, `51a83ce`, `dbee8af`). The figures are projections of the exported STLs.

[↑ Contents](../build-log.md#contents)

### Top-down redesign, phase 3: simplify, and the leg joint

**Phase 5 · Final build · 2026-11-28** · Status: 🔄 design done and checked (full `cad_verify` PASS, 0 FAIL); coupons, plates and the hardware order next

> **In short.** Phase 3 cut the mechanism down to what a 0.4 mm nozzle prints well: the drive unit is three flat parts
> with no support, the printed sleeves are gone, all screws are M3, and the crank marks are engraved numbers 1–4.
> The leg ↔ crank joint was the one real problem left: Morante parked it, reopened it, and picked option D, where
> the leg's end tube follows the pin's real swing cone. The robot now passes the full check (0 FAIL, 91 WARN). Nothing
> has been printed at S 1.0: the 3 mm numbers and the M3 pilots in PLA are still assumptions, so coupons come before
> the plates.

Phase 3 is the simplification phase: count parts, screws, assembly steps and supported parts, propose what can go,
Morante picks, and only then the local work (fits, retention, marks, the check, coupons).

#### Steps

1. **Count at S 1.0:** 27 printed parts (10 gears in 9), 14 hardware entries, 37 assembly entries (17 plan steps, 11
   on the bench); 18 of 27 parts need support.
2. **Proposals, Morante picks A + B + F.** **A**: the drive unit as 3 flat parts screwed with M3 (motor U closed by a
   strap on the same part as the transfer axle; one flat journal cap; the transfer cheek). **B**: idlers and transfer
   on M3 shanks, no printed sleeves. **F**: A's journal cap also caps crank 4, so the cell holder loses its tongue
   over journal 4 and the holder comes out without freeing crank 4. Declined: C (one-way keys) and D (motor held by
   the base: pinion centre distance on two parts). Also applied: M2 labels → M3, at most two screw lengths.
3. **Direct drive (no transfer) was scanned** (pinion 10–30 T on any idler or crank, every 5°, 24 poses): the best,
   «Direct 1», has the pinion on idler 1 and clears the body by 0.47 mm, but only if the gearbox face holds the
   motor. Morante: «Lanza con la variante directa incluida»; the plan compared both, and A + B + F with the transfer
   is the design that stays.
4. **Hardware:** ISO 7380 M3 button heads on axles 1–3 and the transfer axle (M3 × 16), because there is no room for
   thin printed rims (Morante: buy them). Motor: N10 07 type, 100:1.
5. **Marks:** engraved numbers 1–4 on the +x web hub of each crank, 3 mm high and 0.5 mm deep.
6. **Smaller fixes** (committed on the branch): spine keel pilots stop at z 8.2 and the keel screws go from M3×6 to
   M3×5; nickel strip inside the holder's walls; lid lips 3.06 wide between the spring seats; switch pocket opened
   2.5 mm forward; `BODY_TOP` 80.5; transfer-cheek strap ends squared (`STRAP_TIP_W` 2.4, was a 50° wedge with wall 0).
7. **The checks ask their pair's fit:** leg ↔ own crank at `fits.TURN`, leg ↔ every other part at `LEG_PATH` 0.5,
   legs in `MINIMUMS` at `WALL_MIN` (only the end tube asked). That check run gave 30 FAIL, all on the legs.

#### The leg ↔ crank joint

The leg's end tube had walls of 1.7–1.9 mm (< 2.0) and, after a first fix, a 4.3 mm grip on its pin. Pure ×1.43
scaling would have given ×1.43 more gap everywhere (Morante's point); the gain went to the 2.0 walls, a 6.3 mm grip,
the bore drift added outside and the M3 heads. The one real contact left was the closed tube ends of legs 0↔1 and
4↔5 (overlap 0.06), because the leg leans 12.5–17.9° on its pin and the tube flares.

- Options seen: (A) as it was, the snap that broke; (B) a tube centred on the pin point plus a Ø2 × 8 steel cross pin
  in a groove of the printed pin (groove neck Ø2.9: coupon risk); (C) a steel Ø3 pin, slimmer tube, but no retention
  without opening the tube end. Two earlier attempts at fixing A (archived at tag [`leg-joint-A-attempts-2026-11-27`](https://github.com/Morante-robotics/spider-bot-replica/tree/leg-joint-A-attempts-2026-11-27)) made it worse
  (27 FAIL against 20).
- Morante, 2026-11-27: «Deje este tema para resolverlo más adelante y vamos a seguir abordando otras cosas que haya
  pendiente». It was parked, then reopened by him, who **picked option D**: the leg rides with its pin point on the
  crank pin (foot moves ≤ 1.43 mm along the leg, ≤ 0.23 high), the bore follows the tilted pin's ellipse, and the neck
  tab was removed. That gave 17 FAIL (30 before).
- Then the tube was fitted **about the pin's real swing cone** (Morante's pick): measured over the 24 poses, the pin
  tilts only towards +y, so the old symmetric 13.9° double cone made the end up to 1.1 mm fatter. Cone tilt
  6.44/5.49/5.52/7.96° for leg classes 0/4, 1/5, 2/6, 3/7; outer wall = bore + `WALL_MIN`/cos; rounded end revolved
  about the tilted axis; slit edges chamfered 0.5 × 45°; groove margin `TURN` + 0.05; body notch grown 0.35.
- Option A′ (a rigid carry with 2.0 walls) failed at the 1 mm check (tube ↔ tube −0.04, base −0.15 to −0.23) and was
  dropped.

#### Result

Full `cad_verify` on branch `phase3-s1`: **PASS, 0 FAIL, 91 WARN** (`cad/robot/verify-result.txt`).

| Gap or check | Value |
|---|---|
| base ↔ legs | ≥ 0.49 (legs 3/7); legs 0/4 0.26 → 1.3 |
| legs ↔ transfer, body | ≥ 0.60 |
| leg ↔ crank (`TURN`) | 0.25–0.26 |
| retention | 36 held |
| tube wall across slit chamfers | ≥ 2.0 |

- Lessons from this phase: `verify.py` imported a second, unscaled `cad.motion`, so its boxes for legs 1, 2, 5, 6 sat
  off the tube (leg 2 by 5 mm) and it now uses the shells' own module; stale STLs in `out/` gave false wall FAILs, so
  rebuild everything (`build.py`) after switching branches; deleting a recess that a comment explained brought back
  the base FAIL it was made for.
- Interior WARNs located and read as noise: spine (keel pilot chord), cranks (engraving floor), journal cap (sloped
  face); the motor-u has a 1.24 mm floor under a blind hole (0.2 %), not identified.
- Not done: printed mass in grams (the check prints volumes only); the full check takes ≈ 95 s (over 60).
- The whole-robot viewer is at S 1.0 but still shows the legs from before option D; it is regenerated at the step's
  close.

#### Decisions

- **A + B + F, M3 only, ISO 7380 button heads** where there is no room for a thin printed rim.
- **Option D with the pin's swing cone** for the leg ↔ crank joint.
- **Motor: N10 07 type 100:1**, hardware counts in [`hardware.md`](../hardware.md).

#### Next

Nothing has been printed at S 1.0 yet, and two sizes are assumptions: the 3 mm engraved numbers and the M3
self-tapping pilots (Ø2.5) in PLA. The order is: (1) coupons for those two (`measurements.csv`, then `cad/fits.py` by
the designer); (2) print plates and the pre-print review; (3) the workshop kit; (4) one hardware order, after checking
that the seller's datasheet gives ≥ ≈ 0.3 kg·cm at 3 V. The items are rows in Open items.

[↑ Contents](../build-log.md#contents)
