# Spider-Bot · Build log

Every step of the build in order, written so that it can be repeated: what was done, with what, the result, and what
went wrong. Newest entries at the bottom.

| Date | Phase | Step |
|---|---|---|
| 2026-10 | 0 · Workshop | [Printer calibration](#printer-calibration) |
| 2026-11-08 | 2 · CAD | [Carcass base model](#carcass-base-model) |
| 2026-11-09 | 2 · CAD | [Motor, battery holder and print scale](#motor-battery-holder-and-print-scale) |

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

- Repair the meshes before cutting or drilling them (booleans fail on non-manifold meshes).
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
