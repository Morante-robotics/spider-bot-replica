# Leg simulator

[`legs.py`](legs.py) simulates three walking legs driven by one crank (toy crank + sliding leg, Klann, Jansen),
scaled so the crank axle is 55 mm above the ground, and prints the numbers used to choose one. It also checks the
Grashof condition of a four-bar. It is 2D: the toy leg (the one chosen) moves in 3D, so its numbers here
under-rate it; the 3D model is [`toy_leg_3d.py`](toy_leg_3d.py), below. How it was used and the results: [build log](../build-log.md#leg-simulator-and-comparison).

```
python3 legs.py --png images/foot-paths.png --gif images/legs.gif   # --hip 60 for another axle height
```

Needs numpy, matplotlib and pillow.

![Foot paths](images/foot-paths.png)

![Legs animated](images/legs.gif)

## Toy leg in 3D

[`toy_leg_3d.py`](toy_leg_3d.py) models the toy leg on the whole robot: 8 legs in the base rim notches of the 120 %
carcass, two gait groups, a quasi-static walk over one crank turn. It compares 3 crank axle directions × 2 joint types
(the leg slides at the crank pin or at the body pivot), each searched for its best geometry, and measures stride, bob,
step height, foot slip, stability, gap between legs, ground clearance and footprint. Best geometries:
[`toy_leg_3d.json`](toy_leg_3d.json). Results: [build log](../build-log.md#toy-leg-in-3d).

`--strict` adds 6 mm between every pair of legs (inner arms too) and a minimum footprint; `--only shaft/crank` puts
all 8 cranks on one lateral crankshaft inside the base (needs trimesh and shapely to read the base). Results:
[toy_leg_3d_strict.json](toy_leg_3d_strict.json), [build log](../build-log.md#toy-leg-on-one-crankshaft).

```
python3 toy_leg_3d.py --search 3000 --only lateral/crank --json lateral-crank.json   # search one combination
python3 toy_leg_3d.py --params toy_leg_3d.json --png images/toy-3d-comparison.png --gif images/toy-3d.gif
```

Needs numpy, scipy, matplotlib and pillow (plus trimesh and shapely for `shaft`).

![Toy leg in 3D](images/toy-3d-comparison.png)

![Toy leg in 3D, animated](images/toy-3d.gif)
