# Print plates

Bambu Studio projects (.3mf), ready to print on the Bambu Lab P2S (0.4 mm nozzle, Textured PEI plate, Bambu PLA
Basic, 0.20 mm Standard). Open one in Bambu Studio, check it and send it: **Slice plate** → **Print plate**.

## Robot plates (S 1.0, one per colour)

The robot of [`cad/robot`](../cad/robot/) (S 1.0, branch `phase3-s1`) by filament colour: red body and legs, yellow inner
mechanisms, blue base. Every part is a separate object. Support is tree(auto), on the build plate only, standard
settings; the orientation of each part was chosen by slicing the candidates and keeping the least support.

| Plate | Parts (orientation `@rx,ry,rz`) | Time | PLA | Support |
|---|---|---|---|---|
| [`robot-red-body.3mf`](robot-red-body.3mf) | body, roof on the bed (`@180,0,0`), with the front panel | 3 h 20 min | 78.2 g | 6.7 g (9 %) |
| [`robot-red-legs-0-3.3mf`](robot-red-legs-0-3.3mf) | legs 0, 1 (`@90,0,0`), 2, 3 (`@-90,0,0`), lying on their side | 2 h 39 min | 48.4 g | 8.5 g (21 %) |
| [`robot-red-legs-4-7.3mf`](robot-red-legs-4-7.3mf) | legs 4-7, same orientations | 2 h 39 min | 48.5 g | 8.6 g (21 %) |
| [`robot-yellow-inner.3mf`](robot-yellow-inner.3mf) | spine (as modelled, slots up), cranks 1-4 (`@90,0,0`), idlers 1-3 and transfer (`@0,90,0`), journal cap, cell holder, lid (`@180,0,0`) | 1 h 18 min | 21.6 g | 2.6 g (13 %) |
| [`robot-yellow-motor.3mf`](robot-yellow-motor.3mf) | motor U (`@0,-90,0`), pinion (`@0,90,0`), transfer cheek (`@180,0,0`); print after the N10 arrives and coupons c2 / c10 are measured | 17 min | 4.8 g | 0 g (0 %) |
| [`robot-blue-base.3mf`](robot-blue-base.3mf) | base (`@-90,0,0`, on its side) | 1 h 10 min | 23.3 g | 5.3 g (30 %) |

The leg's end tube and the crank pin print with their axis horizontal (the leg and the crank lie on their side).

## Coupon plate

| Plate | Parts | Time | PLA | Support |
|---|---|---|---|---|
| [`coupons.3mf`](coupons.3mf) | the 12 fit coupons (c1-c12, c9 re-modelled) of [`cad/coupons`](../cad/coupons/) as modelled (no rotation, arranged by the tool): c1 / c7 tubes lie horizontal, c11 / c12 flat | 1 h 12 min | 26.6 g | 0.07 g (c5 only) |

Remake: `uv run python tools/bambu_plate.py print/coupons.3mf cad/coupons/out/c*-*.stl --standard`

## Standard settings

Every plate uses the same settings, so the measured fits in [`../cad/fits.py`](../cad/fits.py) stay valid from one
print to the next: P2S, 0.4 mm nozzle, Textured PEI plate, Bambu PLA Basic, **0.20 mm Standard**, supports
**tree(auto)**, **On build plate only**, X-Y hole and contour compensation left at 0.
[`bambu_plate.py --standard`](../tools/bambu_plate.py) adds them:

```bash
uv run python tools/bambu_plate.py print/<plate>.3mf <part>.stl[@rx,ry,rz][:x,y][xN] ... --standard
```

`@rx,ry,rz` turns a part into its print orientation, `:x,y` places it by hand on the bed (nothing is arranged),
`xN` repeats it. The tool writes the settings into the project as changed settings, so the GUI keeps them. A plate
that needs something else says so, with the reason. A plate is committed once, for the version that is printed.

## Earlier plates

Plates of the first design (before the looks-first redesign of 2026-11-17), kept in the
[archive](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/print) with their
commands and assembly notes. The [build log](../build-log/3-legs-and-drive.md) tells what each one taught.

| Plate | Parts | Time | PLA |
|---|---|---|---|
| [`test-leg-plate.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/test-leg-plate.3mf) | Test frame, one leg, fork, crankshaft, clearance block and pin | 1 h 28 min | 29.6 g |
| [`test-frame-v2.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/test-frame-v2.3mf) | Test frame v2 with the crankshaft keeper, fork and leg | 1 h 18 min | 25.6 g |
| [`gear-train-test.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/gear-train-test.3mf) | First gear train test: spine, 4 crankshafts, 3 idlers | 47 min | 16.5 g |
| [`gear-train-test-v2.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/gear-train-test-v2.3mf) | Gear train test v2: spine on a foot, cap, 4 crankshafts, 3 idlers | 1 h 19 min | 33.5 g |
| [`test-cap-v2.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/test-cap-v2.3mf) | The gear train test's cap on its own | 13 min | 6.7 g |
| [`base-v1.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/base-v1.3mf) | Base v1, its cap and the front block | 7 h 57 min | 140.4 g |
| [`legs-forks-v1.3mf`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/print/legs-forks-v1.3mf) | The 8 legs and 8 forks for base v1 | 2 h 30 min | 46.9 g |
