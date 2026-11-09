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

1. **3D model of the toy leg** (new `sim/toy_leg_3d.py`, or extend `sim/legs.py`). Inputs: crank pin radius and
   the plane it turns in, pivot position on the body edge (start from the 8 notches in the base rim of
   [cad/carcass-120/](cad/carcass-120/), at z ≈ 60 mm in the original files, 72 mm at 120 %), the leg's inner arm
   length, bend and outer length. Measure the same numbers as above: stride per half turn, body bob, step height,
   crank radius, footprint. Suggested targets (to confirm): step height ≥ 10 mm, stride ≥ 25 mm, bob ≤ 3 mm, crank
   axle about 55 mm above the ground, robot footprint within about 270 × 185 mm (the 120 % carcass with legs).
   Re-tick «Tengo la trayectoria del pie simulada y la pata elegida con datos» in Plan and Seguimiento when done.
2. **How 8 legs share one motor:** watch 2–3 «walking spider toy teardown» videos (phase 3 study item) and choose
   the crank layout (one crankshaft per side, or a central disc with pins), with the N20 and the 4×AAA holder
   inside the body ([cad/layout/](cad/layout/)).
3. **CAD, by Claude in code** (Python + build123d, agreed 2026-11-09 and written in the Plan): leg, crank pins /
   crankshaft, pivot and a test frame, parametric from the simulator's numbers; check in Python that nothing
   collides over a full crank turn; export STEP (for Onshape) and STL (for Bambu Studio) to `cad/toy-leg/` with a
   README. Shafts 3 mm; hole clearance as a parameter (+0.2 mm by default until the phase 2 clearance test).
4. **Onshape, by Santi:** import the STEP files, assemble and animate. Suggested mates: revolute for the crank,
   cylindrical (slides and turns) for the leg in its pivot sleeve, ball or revolute where the leg sits on the crank
   pin. Check the animated foot path against the simulator.
5. Print one leg with its pivot and turn it by hand.
