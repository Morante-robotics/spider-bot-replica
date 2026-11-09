# Spider-Bot · Build log

Every step of the build in order, written so that it can be repeated: what was done, with what, the result, and what
went wrong. Newest entries at the bottom.

| Date | Phase | Step |
|---|---|---|
| 2026-10 | 0 · Workshop | [Printer calibration](#printer-calibration) |
| 2026-11-08 | 2 · CAD | [Carcass base model](#carcass-base-model) |
| 2026-11-09 | 2 · CAD | [Motor, battery holder and print scale](#motor-battery-holder-and-print-scale) |
| 2026-11-09 | 2 · CAD | [Mesh repair](#mesh-repair) |
| 2026-11-09 | 3 · Mechanisms | [Leg simulator and comparison](#leg-simulator-and-comparison) |
| 2026-11-09 | 3 · Mechanisms | [Toy leg in 3D](#toy-leg-in-3d) |
| 2026-11-09 | 3 · Mechanisms | [Toy leg on one crankshaft](#toy-leg-on-one-crankshaft) |

## Printer calibration

**Phase 0 · Workshop · 2026-10**

Bambu Lab P2S Combo (with AMS) running its automatic calibration before the first print. All Spider-Bot parts are
printed in PLA.

https://github.com/user-attachments/assets/948dd098-af7a-4972-a0bd-290c17e0126f

## Carcass base model

**Phase 2 · CAD · 2026-11-08**

**Goal:** start the carcass from an existing faithful model instead of modelling it from scratch.

**Source:** [Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), the most faithful replica found
(CC BY-NC-SA). Others looked at: a stylised low-poly game asset on Sketchfab (CC BY-ND, so no modified versions
can be published; reference only) and the MyMiniFactory «Spider BOT» (an unrelated sci-fi miniature).

**Steps:**

1. On the Thingiverse page, **Download all files** (zip with 9 STLs, photos, README and license). Scripted downloads get
   HTTP 403.
2. Check every STL is valid and measure it: [`tools/stl_preview.py`](tools/stl_preview.py) prints the size of each part
   and renders the previews.
3. The files place body, base, sensor and only the front leg pair; the eyes are off to the side. Join everything into
   one assembled STL: `python3 tools/assemble_jenscolt.py cad/carcass-jenscolt spideybot_assembled.stl`. It moves the
   4 eye domes into their sockets and adds the other 3 legs per side (rear mirrored, middle two rotated). The leg
   layout is approximate, read off the author's photos: fine for pictures, not for fitting parts.
4. Open the assembled STL in Bambu Studio to check it imports.
5. Files, sizes and previews: [cad/carcass-jenscolt/](cad/carcass-jenscolt/).

**Result:** 9 binary STLs. The body is a hollow shell 96 × 110 × 66 mm. The base has posts and mounts inside. The
legs are static display parts. Print 4 of each leg file per side (8 legs) and 2 of each eye. Assembled, the robot
measures 224 × 154 × 118 mm.

![Assembled carcass turntable](cad/carcass-jenscolt/images/assembled-turntable.gif)

![Carcass parts](cad/carcass-jenscolt/images/parts.png)

Bambu Studio imports the assembly, but reports mesh errors (non-manifold edges and reversed faces); every file has some.

![Bambu Studio import](cad/carcass-jenscolt/images/bambu-studio-import.png)

**Decisions:**

- Carcass = jenscolt's meshes, edited in Bambu Studio (cuts, holes). Mechanism = new parametric parts in Onshape, with
  the body STL imported only as a size reference.
- The walking legs are designed new; jenscolt's legs give their outer look.

**Open:**

- ~~Repair the meshes before cutting or drilling them.~~ Done in [Mesh repair](#mesh-repair).
- ~~Print scale.~~ Decided in the next step: 120 %.

## Motor, battery holder and print scale

**Phase 2 · CAD · 2026-11-09**

**Goal:** choose the motor and the battery holder, and find the print scale at which both fit inside the carcass.

**Steps:**

1. Collect the outer sizes from shop data sheets (largest listed value, rounded up):

   | Part | Size (mm) | Notes |
   |---|---|---|
   | N20 gear motor | 37 × 12 × 10 | 12 × 10 cross-section for every gear ratio; length includes the 10 mm shaft |
   | 4×AA holder, switch + cover (flat) | 70.5 × 68 × 20 | Parts Express, The Pi Hut, Abra, DFRobot listings |
   | 4×AAA holder, switch + cover | 64 × 49 × 16 | Typical listing; check the drawing of the one bought |
   | 3×AA / 2×AA holder, switch | ~62 × 50 × 18 / ~60 × 34 × 18 | Typical listings |
   | 4×AA holder, 2×2 stacked | 58 × 32 × 31 | No switch or cover |

2. Measure the free space inside the body and try each part in it:
   ```
   python3 tools/fit_check.py cad/carcass-jenscolt --scale 1.0 --min-scale \
       --box "4×AA flat, switch + cover" 70.5 68 20 --box "4×AAA holder, switch + cover" 64 49 16 ...
   ```
   [`tools/fit_check.py`](tools/fit_check.py) slices the body every 1 mm from the top of the base upwards, keeps the
   inside of the wall behind the eye block, and looks for a spot where the box lies flat (0° or 90°). The author's
   screw bosses and base posts are ignored: the inside is redesigned. The base is a near-solid bowl; hollowing it
   does not help, it is too shallow at the edges.
3. Repeat at the chosen scale with 2 mm clearance per side (holder sizes vary about ±0.5 mm between makers, and the
   wires need room): `--scale 1.2 --clearance 2`.

**Result:** at 100 % the free space is a horseshoe about 71 × 62 mm. The N20 fits with room to spare. The 4×AA flat
holder needs 137 %. With 2 mm clearance the 4×AAA holder needs 118 %; at 120 % it fits.

![What fits at 100 %](cad/layout/images/fit-100.png)

![4×AAA holder and N20 at 120 %](cad/layout/images/fit-120.png)

**Decisions:**

- **Motor: N20 gear motor.** The ratio is picked in phase 4 from the measured load; all ratios have the same size.
- **Batteries: 4×AAA NiMH** in a holder with switch and cover. Same 4.8 V as 4×AA, so motor and eyes behave the same;
  less capacity (about 800–1000 mAh against 2000–2500 mAh). 2×AA was ruled out: 2.4 V (about 2.2 V under load)
  gives a 6 V N20 about 40 % of its speed and torque, and blue or white LEDs (about 3 V) do not light.
- **Print scale: 120 %.** Robot about 269 × 185 × 142 mm. 110 % fits the holder with no clearance at all.

**Open:**

- Check the drawing of the holder actually bought against 64 × 49 × 16 mm (+2 mm).
- Battery life on 4×AAA: measured in phase 4.
- Room for the leg mechanism next to the holder: laid out in Onshape (phase 3).

## Mesh repair

**Phase 2 · CAD · 2026-11-09**

**Goal:** make the carcass meshes watertight (closed, no non-manifold edges) without changing their shape, so that
cuts and holes in Bambu Studio work, and scale them to the chosen 120 %.

**What was wrong:** every file has duplicate triangles (zero-thickness walls), zero-area triangles, tiny gaps
between triangles, and in the body 10 edges where two surfaces touch ("pinched" edges). Bambu Studio's CLI
(`BambuStudio --info part.stl`) reports `manifold = no` for body, eyes and sensor.

**Steps:**

1. Repair and scale the 5 carcass parts:
   ```
   python3 tools/repair_stl.py cad/carcass-120 --scale 1.2 cad/carcass-jenscolt/spideybot_{body,base,eye,small_eye,sensor}.stl
   ```
   [`tools/repair_stl.py`](tools/repair_stl.py) merges vertices closer than 0.1 µm, drops zero-area and duplicate
   triangles, closes small holes, and at pinched edges splits the vertices and moves each copy 0.01 mm into its own
   side. It then reads every file back, as a slicer would, and measures the largest distance to the original.
2. Check with Bambu Studio's own mesh check: `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --info
   cad/carcass-120/spideybot_body.stl` → `manifold = yes` for all 5 files.

**Result** (deviation measured at 100 %, before scaling):

| File | Before: open / non-manifold edges | Fixed | After: open / non-manifold edges | Watertight | Max deviation (mm, at 100 %) |
|---|---|---|---|---|---|
| `spideybot_body.stl` | 0 / 55 | 228 degenerate, 7 duplicate triangles, 10 pinched edges split (surface moved 0.01 mm) | 0 / 0 | yes | 0.010 |
| `spideybot_base.stl` | 0 / 4 | 6 degenerate, 0 duplicate triangles | 0 / 0 | yes | 0.000 |
| `spideybot_eye.stl` | 0 / 3 | 0 degenerate, 3 duplicate triangles | 0 / 0 | yes | 0.000 |
| `spideybot_small_eye.stl` | 0 / 3 | 5 degenerate, 3 duplicate triangles, 3 open edges closed | 0 / 0 | yes | 0.000 |
| `spideybot_sensor.stl` | 0 / 3 | 2 degenerate, 3 duplicate triangles | 0 / 0 | yes | 0.000 |

Bambu Studio: `manifold = yes` for all 5 (before: body 9 non-manifold edges, eye, small eye and sensor 3 each).
Imported in the Bambu Studio window, the body shows no errors (compare the red errors in
[Carcass base model](#carcass-base-model)):

![Repaired body in Bambu Studio](cad/carcass-120/images/bambu-studio-import.png)

![Repaired parts at 120 %](cad/carcass-120/images/parts.png)

**Decisions:**

- **No automatic rebuild (MeshFix).** Tried first: it closes everything, but on a leg it cut off a 1.5 mm relief.
  Only fixes that keep the surface within 0.01 mm are used.
- **Legs not repaired.** Their pinched edges need the shape changed to close. They are not printed (the walking
  legs are designed new) and stay as a reference in [cad/carcass-jenscolt/](cad/carcass-jenscolt/).
- Repaired files live at 120 %, the print scale, so measurements taken from them are the real ones.

**Open:**

- Cuts in Bambu Studio: battery hatch in the base, motor and shaft openings (after the mechanism layout).

## Leg simulator and comparison

**Phase 3 · Mechanisms · 2026-11-09**

**Goal:** simulate the foot path of three candidate legs driven by one crank and choose one with numbers: toy
(crank + sliding leg), Klann and Jansen.

**Steps:**

1. Bar lengths: Klann from his patent as redrawn by [DIY Walkers](https://www.diywalkers.com/klann-linkage-optimizer.html)
   (crank = 3, frame pivots at (7.4, 16.9) and (3.4, 8.03) with the crank at (10, 10), knee bent 30°, upper bar
   bent 12.8°); Jansen's "holy numbers" (crank = 15); the toy leg from a random search (4000 tries) for the longest
   stride with less than 3 mm of body bob, so it is compared at its best.
2. Run the simulator: `python3 sim/legs.py --png sim/images/foot-paths.png --gif sim/images/legs.gif`.
   [`sim/legs.py`](sim/legs.py) turns the crank in 0.5° steps, solves each joint as the crossing of two circles
   (keeping the linkage on the same branch), and scales every leg so the crank axle is 55 mm above the ground
   (the body bottom is about 46 mm up at 120 %).
3. Measure over the half turn each leg carries the body. The gait is two groups of four legs with cranks 180°
   apart, so every leg must hold the body for half a turn, starting from its lowest point.

**Result:**

| Leg | Stride per half turn (mm) | Body bob while walking (mm) | Step height (mm) | Foot slips back on the ground | Foot speed peak / median | Crank radius (mm) | Leg size W × H (mm) | Moving parts per leg | Pin joints per leg |
|---|---|---|---|---|---|---|---|---|---|
| toy (crank + sliding leg) | 29 | 2.5 | 5 | yes | 1.4 | 7.7 | 55 × 63 | 1 | 2 |
| Klann | 60 | 3.7 | 28 | yes | 1.3 | 14.4 | 100 × 114 | 4 | 6 |
| Jansen | 38 | 1.1 | 13 | no | 1.2 | 9.0 | 73 × 75 | 7 | 10 |

Klann's driving four-bar (frame O-P2, crank, bar A-M, rocker M-P2): s + l = 9.88774, p + q = 10.19: crank-rocker — its crank turns fully.

![Foot paths](sim/images/foot-paths.png)

![Legs animated](sim/images/legs.gif)

- **Toy:** one part per leg, but in this flat (2D) model the foot barely lifts (5 mm) and drags back. Real toy
  spiders work in 3D (the foot also swings sideways and up), which this simulator does not model, so these numbers
  under-rate it.
- **Klann:** longest stride (60 mm) and highest step (28 mm). The leg arches above the body like a spider's.
  4 parts per leg, a bigger crank (14 mm), the body bobs 3.7 mm, and the foot slows at both ends of the step.
  Sensitive to dimensions: rounding the bars to 0.5 mm changes the foot path a lot.
- **Jansen:** the smoothest (1.1 mm bob, even speed) but 7 parts and 10 pins per leg (56 parts for 8 legs), and it
  does not look like a spider leg.

**Decision: toy leg** (crank + one bent leg that slides and swivels in a pivot on the body edge). Simplest for a
first robot: 1 part per leg (8 legs + cranks, against 32 parts for Klann), not sensitive to small dimension
errors, a small crank (about 7 mm, so less torque), and probably how the original toy walks.

How this was decided: Klann was picked first from the table above, then dropped the same day. The toy leg had been
ruled out on the 2D model only, which does not represent it; it was not offered as an option. Klann's real-size
bars can be regenerated with `sim/legs.py` if needed.

**How the toy leg works:** each leg is one rigid bent part. Its inner end sits on a crank pin that turns in a
circle; further out it passes through a pivot on the body edge that lets it slide and swivel (a sleeve on a swivel,
or a ball joint). When the crank pin goes up, the foot goes down (lever), and when the pin goes in, the leg slides
in: the foot traces a loop. Gait as planned: two groups of four legs (left 1 and 3 + right 2 and 4, against the
other four) on crank pins 180° apart.

**Open (next session):**

1. ~~**3D model of the toy leg**~~ Done in [Toy leg in 3D](#toy-leg-in-3d). (new `sim/toy_leg_3d.py`, or extend `sim/legs.py`). Inputs: crank pin radius and
   the plane it turns in, pivot position on the body edge (start from the 8 notches in the base rim of
   [cad/carcass-120/](cad/carcass-120/), at z ≈ 60 mm in the original files, 72 mm at 120 %), the leg's inner arm
   length, bend and outer length. Measure the same numbers as above: stride per half turn, body bob, step height,
   crank radius, footprint. Suggested targets (to confirm): step height ≥ 10 mm, stride ≥ 25 mm, bob ≤ 3 mm, crank
   axle about 55 mm above the ground, robot footprint within about 270 × 185 mm (the 120 % carcass with legs).
   Re-tick «Tengo la trayectoria del pie simulada y la pata elegida con datos» in Plan and Seguimiento when done.
2. ~~**How 8 legs share one motor:** watch 2–3 «walking spider toy teardown» videos (phase 3 study item) and choose
   the crank layout (one crankshaft per side, or a central disc with pins), with the N20 and the 4×AAA holder
   inside the body ([cad/layout/](cad/layout/)).~~ Decided: one lateral crankshaft, see
   [Toy leg on one crankshaft](#toy-leg-on-one-crankshaft). The teardown videos are still on the study list.
3. **CAD, by Claude in code** (Python + build123d, agreed 2026-11-09 and written in the Plan): leg, crank pins /
   crankshaft, pivot and a test frame, parametric from the simulator's numbers; check in Python that nothing
   collides over a full crank turn; export STEP (for Onshape) and STL (for Bambu Studio) to `cad/toy-leg/` with a
   README. Shafts 3 mm; hole clearance as a parameter (+0.2 mm by default until the phase 2 clearance test).
4. **Onshape, by Santi:** import the STEP files, assemble and animate. Suggested mates: revolute for the crank,
   cylindrical (slides and turns) for the leg in its pivot sleeve, ball or revolute where the leg sits on the crank
   pin. Check the animated foot path against the simulator.
5. Print one leg with its pivot and turn it by hand.

## Toy leg in 3D

**Phase 3 · Mechanisms · 2026-11-09**

**Goal:** model the chosen toy leg in 3D on the whole robot (8 legs in the base notches, two gait groups) and get the
same numbers as the 2D comparison, for every way of building it, each at its best.

**Steps:**

1. Find the leg pivots: the base rim has 8 notches, 4 per side, about 10 × 5 mm, at z 70–74 mm
   ([cad/carcass-120/](cad/carcass-120/) coordinates: z = height above the ground of jenscolt's assembly, forward =
   −Y). Right-side centres, front to rear: (89.5, −32.2), (95.9, −12.6), (96.1, 2.9), (82.6, 31.1); the left ones are
   their mirror about x = 42.7 (the body axis). Measured by slicing `spideybot_base.stl` at z = 71 and 73 and
   subtracting the slice from its convex hull.
2. Model one leg ([`sim/toy_leg_3d.py`](sim/toy_leg_3d.py)): crank pin A turns about a crank centre O placed D mm
   inward from the pivot P and H mm above it; the inner arm runs along the line A → P; past the knee the shin bends
   down (bend angle) and leans forward or back (sweep). The leg keeps its sideways axis horizontal (a gimbal at P).
   Two joint types:
   - **slides at crank:** the leg turns about a fixed point at P, and the crank pin slides in a bore or slot at the
     leg's inner end;
   - **slides at body:** the leg sits on the crank pin and slides through a sleeve at P (the 2D model).

   Three crank axle directions: **lateral** (X, across the body), **vertical** (Z) and **longitudinal** (Y, the
   walking direction). Same leg part on all 8 notches (mirrored on the left); cranks 180° apart for the two groups
   (left 1 and 3 + right 2 and 4, against the other four). How one motor drives the 8 cranks is not modelled (next step).
3. Walk the robot over one crank turn: the body stays level and stands on its lowest feet (those within 2 mm of the
   lowest, as it tilts onto them) and moves by what the lowest foot moves.
4. For each of the 6 combinations, search the geometry (3000 random tries + 750 refinement steps, crank radius
   3–12 mm, D 8–40 mm, H −20 to +8 mm, arm 5–70 mm, bend 30–150°, sweep ±45°, shin 30–120 mm) for the longest
   stride within the targets: step height ≥ 10 mm, bob ≤ 3 mm, ground clearance under the base 20–60 mm, ≥ 3 mm
   between neighbouring legs, knee and foot ≥ 5 mm outside the body, body centre inside the supporting feet, footprint
   ≤ 270 × 185 mm, little foot slip:
   ```
   python3 sim/toy_leg_3d.py --search 3000 --only lateral/crank --json lateral-crank.json   # one per combination
   python3 sim/toy_leg_3d.py --params sim/toy_leg_3d.json --png sim/images/toy-3d-comparison.png --gif sim/images/toy-3d.gif
   ```
   The 6 best geometries are in [`sim/toy_leg_3d.json`](sim/toy_leg_3d.json). The 6 searches ran in parallel, about
   10 minutes in all.

**Result:**

| Crank axle | Slides at | Stride per half turn (mm) | Body bob (mm) | Step height (mm) | Feet slip (mm per leg per turn) | Stable all turn (margin mm) | Gap between legs (mm) | Clearance under base (mm) | Footprint X × Y (mm) | Crank radius (mm) |
|---|---|---|---|---|---|---|---|---|---|---|
| lateral | crank | 26 | 3.1 | 12 | 39 | yes (15) | 8.0 | 49 | 190 × 133 | 10.0 |
| lateral | body | 11 | 3.8 | 10 | 15 | yes (21) | 15.5 | 48 | 222 × 133 | 3.3 |
| vertical | crank | 39 | 0.7 | 7 | 29 | yes (13) | 2.9 | 24 | 268 × 184 | 10.1 |
| vertical | body | 34 | 0.7 | 6 | 22 | yes (12) | 4.0 | 20 | 265 × 176 | 4.1 |
| longitudinal | crank | 13 | 3.1 | 10 | 39 | yes (6) | 15.5 | 21 | 171 × 133 | 9.1 |
| longitudinal | body | 8 | 4.5 | 10 | 16 | yes (14) | 15.5 | 29 | 249 × 150 | 3.0 |

Knee and foot stay outside the body in all six. Feet slip = how far, on average, each foot slides on the ground per
turn against the foot carrying the body (it includes touching down and lifting off).

| Crank axle / slides at | Geometry (mm, °) | Crank axle above ground (mm) | Slide travel (mm) | Pivot swing yaw / pitch | Leg to crank pin angle |
|---|---|---|---|---|---|
| lateral / crank | r 10.0, D 34.8, H −12.9, arm 23.1, bend 107, sweep 4, shin 79.3 | 62 | 13.9 | 32° / 29° | 7–35° |
| lateral / body | r 3.3, D 30.5, H −7.2, arm 58.7, bend 85, sweep 4, shin 79.7 | 67 | 4.4 | 12° / 12° | 10–22° |
| vertical / crank | r 10.1, D 38.2, H −6.0, arm 45.5, bend 71, sweep 21, shin 66.8 | 44 | 20.0 | 31° / 5° | 78–83° |
| vertical / body | r 4.1, D 17.6, H −2.6, arm 62.4, bend 72, sweep 22, shin 61.4 | 44 | 8.1 | 27° / 4° | 79–83° |
| longitudinal / crank | r 9.1, D 30.8, H −9.3, arm 17.2, bend 104, sweep 22, shin 52.6 | 38 | 18.1 | 6° / 33° | 77–83° |
| longitudinal / body | r 3.0, D 37.0, H −7.7, arm 52.6, bend 63, sweep 27, shin 78.8 | 48 | 6.0 | 2° / 9° | 80–81° |

![Toy leg in 3D, best geometry of each combination](sim/images/toy-3d-comparison.png)

![Toy leg in 3D, animated](sim/images/toy-3d.gif)

- **Lateral axle, slides at crank** is the only one close to every target (bob 3.1 against 3). The crank pin points
  along the leg (7–35°), so it can slide straight into a bore in the leg's inner end: probably the classic toy. The
  feet slip the most (39 mm per leg per turn), and the 8 cranks sit near the body centre, where the battery holder
  goes.
- **Vertical axle** gives the longest, smoothest stride (34–39 mm, 0.7 mm bob) but a low step (6–7 mm): it only
  lifts the feet by tilting the leg. Its legs come within 2.9 mm of each other (slides at crank), and the left cranks
  must turn the other way (a gear pair).
- **Longitudinal axle** is the weakest: the crank moves the inner end sideways, which hardly makes a stride.
- **Slides at body** gives shorter strides with a lateral axle (11 mm) but less slip.
- Limits of the model: the body stays level (a real one tilts onto 3 feet), legs are lines (no thickness, so 3 mm
  gaps are tight), and nothing is checked against the carcass interior, the battery holder or the motor yet.

**Decision:** taken in [Toy leg on one crankshaft](#toy-leg-on-one-crankshaft): lateral axle sliding at the crank. Before that it was pending (Santi), together with the crank layout: lateral axle sliding at the crank (meets the targets,
the classic toy) or vertical axle (longer stride, low step).

**Open:**

- ~~Choose the variant above~~ Lateral, on one crankshaft: [Toy leg on one crankshaft](#toy-leg-on-one-crankshaft). Then steps 2–5 of [Leg simulator and comparison](#leg-simulator-and-comparison) → Open:
  crank layout for 8 legs with the N20 and the 4×AAA holder, CAD in build123d, Onshape, print one leg.
- Check that the notches (10 × 5 mm) let the leg swing as far as the table says, or widen them in the base.

## Toy leg on one crankshaft

**Phase 3 · Mechanisms · 2026-11-09**

**Goal:** check whether the lateral toy leg keeps its numbers when one motor drives it. In
[Toy leg in 3D](#toy-leg-in-3d) every leg had its own crank, and the 4 crank centres of each side ended up 5–9 mm
apart with 10 mm cranks, so they would hit each other.

**Steps:**

1. Add a **shaft** mode to [`sim/toy_leg_3d.py`](sim/toy_leg_3d.py): one lateral crankshaft for all 8 legs at
   y = Y0, z = 72 + H. The 4 cranks of each side sit along it from XIN to XIN + 3 × PITCH mm from the body axis
   (PITCH ≥ 8 mm: crank web plus leg end), in any of the 24 orders, and mirrored on the left. The two gait groups
   are pins 180° apart on the same shaft, and both sides turn the same way.
2. Keep the crankshaft below the battery holder and inside the base. The holder (64 × 49 × 16 mm) sits above the
   rim and fills almost the whole body ([cad/layout/](cad/layout/)), so the crank discs (radius r + 2 mm for the pin
   head) must stay below z 73 and inside the base's outer outline shrunk by a 2 mm wall, checked on slices of
   `spideybot_base.stl` every 1 mm. The base bowl is near solid, so it will need hollowing there.
3. `--strict` rules, used for this step: legs are 5 mm thick, so 6 mm between centre lines for **every pair** of
   legs on a side, including the inner arms inside the body (before, only neighbours and only outside the body).
   Footprint at least 240 × 165 mm, close to the original's look (jenscolt's assembly at 120 %: 269 × 185).
4. Search 3000 random tries + 750 refinement steps: shaft sliding at crank (3 seeds), shaft sliding at body, and,
   as a reference, the per-leg lateral cranks under the same rules:
   ```
   python3 sim/toy_leg_3d.py --strict --search 3000 --seed 3 --only shaft/crank --json shaft-crank.json
   python3 sim/toy_leg_3d.py --params sim/toy_leg_3d_strict.json --png sim/images/toy-3d-strict.png --gif sim/images/toy-3d-strict.gif
   ```
   The best results are in [`sim/toy_leg_3d_strict.json`](sim/toy_leg_3d_strict.json). The 5 searches ran in
   parallel, about 15 minutes in all.

**Result:**

| Cranks | Slides at | Stride per half turn (mm) | Body bob (mm) | Step height (mm) | Feet slip (mm per leg per turn) | Stable all turn (margin mm) | Gap between legs (mm) | Clearance under base (mm) | Footprint X × Y (mm) | Crank radius (mm) |
|---|---|---|---|---|---|---|---|---|---|---|
| one per leg (lateral), reference | crank | 15 | 5.3 | 12 | 18 | yes (7) | 1.0 | 49 | 261 × 166 | 3.0 |
| one crankshaft | crank | 14 | 4.2 | 10 | 17 | yes (5) | 2.2 | 40 | 241 × 165 | 5.1 |
| one crankshaft | body | 6 | 2.9 | 6 | 6 | yes (15) | 1.4 | 24 | 243 × 175 | 3.1 |

The other two crankshaft seeds gave strides of 9 and 7 mm. Best crankshaft geometry (sliding at crank): r 5.1,
Y0 −12.9, H −6.4 (crank axle 60 mm above the ground), cranks at 6, 16, 26 and 36 mm from the body axis (front leg
innermost), arm 67.4, bend 114°, sweep −15°, shin 77.1 mm. Slide 10 mm, pivot swing 15° each way, crank pin 2–17°
off the leg's axis. The crank discs fit inside the base.

![Toy leg on one crankshaft](sim/images/toy-3d-strict.png)

![Toy leg on one crankshaft, animated](sim/images/toy-3d-strict.gif)

- With realistic clearance between legs, **no layout meets the targets**, not even one crank per leg. Stride halves
  (26 → 14–15 mm) and bob rises to 4–5 mm.
- The cause, measured: every closest pair is two **inner arms inside the body**. Coming in from notches 10–15 mm
  apart toward the cranks, almost in the same plane, they meet. No variant gets the 6 mm.
- The one crankshaft costs almost nothing against one crank per leg (14 against 15 mm). The inner arms are the
  limit, not the shaft.
- Limits: the footprint minimum twisted the legs (rear legs stretched about 100 mm back, see the top view), so it
  probably costs stride too. Left and right legs are not checked against each other, and the inner arms of the two
  sides come close in the middle.

**Decision: lateral toy leg on one crankshaft, sliding at the crank** (best geometry above, in
[`sim/toy_leg_3d_strict.json`](sim/toy_leg_3d_strict.json)). It accepts 14 mm per half turn and 4.2 mm of bob: a
slower walk, but the simplest drive. One shaft across the body turns both sides the same way, and the N20 drives it
with spur gears. Pivots at different heights were offered and not picked.

**Open:**

- How the N20 drives the shaft: gear ratio and where the motor sits (phase 4 picks the ratio).
- CAD in build123d (step 3 of [Leg simulator and comparison](#leg-simulator-and-comparison) → Open), starting from
  this geometry. Real leg thickness, the inner arms (2.2 mm between centre lines here) and left against right legs
  are checked there, in the collision check over a full turn.
- Hollow the base for the crankshaft, and cut the pivot windows: 15° of swing each way.
