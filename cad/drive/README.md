# Legs and drive

The 8 legs, their pivots and the drive that turns them, modelled in code with build123d from the simulator's
geometry ([`sim/toy_leg_3d_rows_cad.json`](../../sim/toy_leg_3d_rows_cad.json), first entry). Four lateral
crankshafts drive the legs, one per pair of legs, linked by idler gears so all four turn the same way. Each leg slides
on its crank pin. How and why: [build log](../../build-log.md#legs-and-drive-in-cad).

```
python3 build.py --assembly 0   # every part (STEP + STL) and the assembled drive at crank angle 0°
python3 check.py --gaps         # collision and gap check over a full turn (about 9 minutes)
```

Needs Python 3.12 with build123d, numpy, trimesh and manifold3d. All sizes come from parameters at the top of
[`build.py`](build.py).

![Parts](images/parts.png)

![Assembly, crank angle 0°](images/assembly.gif)

| File | What | X × Y × Z (mm) | Print |
|---|---|---|---|
| `leg-front-right.stl` / `-left` | Front leg | 93.6 × 7.6 × 67.6 | 1 + 1 |
| `leg-middle-right.stl` / `-left` | Middle legs (2nd and 3rd) | 99.7 × 7.6 × 67.6 | 2 + 2 |
| `leg-rear-right.stl` / `-left` | Rear leg | 87.3 × 7.6 × 67.6 | 1 + 1 |
| `pivot.stl` | Fork that holds a leg at the rim | 10.6 × 10.0 × 22.0 | 8 |
| `crankshaft-1.stl` … `-4.stl` | One piece: 12-tooth gear, two journals, two cranks with balls (front to rear). Each is different: its gear is turned on the shaft by its own offset, and 1–4 dots on the +X web say which it is. Crankshaft 4's crank webs are 1.5 mm thick instead of 2, to keep them clear of the rear legs | 27.6 × 14.0 × 14.0 | 1 each |
| `idler-1.stl`, `-2`, `-3` | Idler gears, 12, 12 and 20 teeth | up to 22.0 × 22.0 × 2.6 | 1 each |
| `spine.stl` | Gear train test: two walls on a foot that carry the 4 crankshafts and the idler axles, an M3 nut slot at each end, dots by each slot. The robot's spine is built into [base v1](../base/) | 30.0 × 97.3 × 32.5 | 1 |
| `test-cap.stl` | Gear train test: cap whose tongues hold the crankshafts down in their slots, as base v1's cap does; four skirts at the ends centre it on the walls, and the tongues cover only the outer part of each wall, clear of the gears (print upside down) | 20.0 × 97.3 × 11.7 | 1 |
| `test-frame.stl` | Desk stand for one middle leg, its pivot and crankshaft 2, turned by hand | 75.4 × 35.5 × 80.1 | 1 |
| `test-frame-keeper.stl` | Cap that holds crankshaft 2 in the test frame (print upside down) | 8.5 × 28.0 × 9.0 | 1 |
| `assembly-0.stl` | Whole drive at crank angle 0°, for reference only | 218.0 × 87.5 × 71.3 | — |

STEP files with the same names are for Onshape (how to assemble and animate them: [onshape.md](onshape.md); the test-frame assembly: [Onshape](https://cad.onshape.com/documents/07632681db3e0a6b5b785746/w/6c5d5bb7bfec5781a6827599/e/c59459f0a1ed69675318d6bb)). Bambu Studio `--info` reports `manifold = yes` for all of them.

**How it fits together:**

- **Leg:** the inner end is a tube (flat sides, 5.6 × 7.6 mm) with a Ø3.8 mm bore. The ball on the crank pin
  (Ø3.6) slides 1.8–2.5 mm in it and lets the leg tilt. At the rim the leg goes through the pivot fork on an M3 screw,
  so it can tilt up and down (6–23°). The fork swings left and right (±6°) on two M3 screws driven into its top and
  bottom, which turn in the rim (or the test frame). The leg does not roll about its own axis.
- **Gait:** the two cranks on a crankshaft sit 180° apart. Neighbouring crankshafts are printed 180° apart too, so
  left legs 1 and 3 + right legs 2 and 4 move against the other four. Assemble with every crank level (crank
  angle 0°) and the dots on +X, the side of the right legs: a shaft one tooth off has its cranks 30° from level.
- **Gears:** module 1, 20° pressure angle, 3 mm wide (idlers 2.6 mm). The crankshaft gears all have 12 teeth, so the
  four turn at the same speed. The idlers sit below the line of shafts, each 0.275 mm further from its crankshafts
  than in theory, for about 0.2 mm of backlash (`BACKLASH`). Each crankshaft's gear offset (`gear_offsets()`) lets
  every idler mesh with both of its neighbours. The motor's drive is designed in phase 4.

**Hardware:** for the whole robot, 8 × M3×16 screws + nylon lock nuts (leg pivots; the fork is 10.0 mm across, so M3×12
leaves no room for the nut), 16 × M3×10 screws + nuts (forks, as pins: they go in [base v1](../base/)), 3 × 3 mm steel pins 9 mm long (idlers). For the test frame:
1 × M3×16 + nylon lock nut, 2 × M3×10 + 2 nuts (fork), 2 × M3×12 + 2 nuts (keeper).

**Assembling the test frame:**

![Test frame screws](images/test-frame-screws.png)

1. Leg in the fork: put the leg's boss in the fork's window, and an M3×16 through the fork's side hole, the leg
   and the other side. Nut on the end, snug but not tight: if it squeezes the fork's walls onto the leg, the leg
   cannot tilt. A nylon lock nut keeps it there. The window is 1 mm wider than the leg: if the leg slides along
   the screw, put an M3 washer on each side of it where they fit (the middle legs pass 0.7 mm apart).
2. Fork in the frame: the fork goes between the frame's two arms. An M3×10 down through the upper arm's hole,
   with a nut on it under the arm, tightened against the arm; its tip goes 3 mm into the blind hole on top of the
   fork. The same from below through the lower arm. The two screws are fixed to the frame and the fork turns on
   their tips.
3. Crankshaft last: guide the ball into the mouth of the leg's tube while lowering the journals into the slots.
4. Keeper: slide an M3 nut into each end block's slot from outside, put the keeper on top with its tongues down the
   slots, and drive two M3×12 down through it into the nuts.

Figure: [`screws_figure.py`](screws_figure.py).

**Print** (PLA, 0.2 mm layers):

| Part | Lay it | Supports |
|---|---|---|
| Legs | On their −Y face (rotate 90° about X): arm, boss, knee and shin are offset so their −Y face is flush with the tube's, and the leg lies flat (the shin rises 3 mm towards the foot) | Tree, on the build plate only, under the shin |
| Crankshafts | Axis horizontal, so the ball stubs are not split by layer lines | Tree |
| Pivot, spine | As modelled (Z up) | None |
| Test cap | Upside down, tongues up | None |
| Idlers | Flat | None |
| Test frame | Plate on the bed | Tree, under the pivot arms |

**Clearances** (on the diameter, from the [clearance test](../clearance-test/)): 0.5 mm for a printed part turning
or sliding in a printed hole (`CLR`: journals, the ball in the bore), 0.3 mm for a steel screw or pin (`CLR_STEEL`).
The fork's window is 1.0 mm wider than the leg (0.5 mm a side; 0.2 mm a side was too tight on one print).

**Check over a full turn** ([`check.py`](check.py), every 30°): it lists any overlap between two parts and every pair
closer than 1 mm. Latest result: [`check-result.txt`](check-result.txt).

**Gear train check** ([`verify_gear_train.py`](verify_gear_train.py), a spec for the shared
[`tools/cad_verify.py`](../../../tools/cad_verify.py)): the gear train test with every gear turning at its real
angle, the cap shifted to either side, keep-out zones around the gear faces, and what holds each part. Latest result: [`verify-gear-train.txt`](verify-gear-train.txt); pictures in
`images/verify/`. [`check_gear_train.py`](check_gear_train.py) checks every mesh in 2D every 1° ([`check-gear-train.txt`](check-gear-train.txt)).
[`gear_phase_figure.py`](gear_phase_figure.py) draws each idler between its two crankshafts, v1 and v2.
[`assembly_figure.py`](assembly_figure.py) draws the test's assembly diagram (`--lang es` for Spanish).

What is still to do on the drive: [Open items](../../build-log.md#open-items) in the build log.
