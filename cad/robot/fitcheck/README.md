# Whole-robot fit check

The check that answers «does everything fit inside the looks robot, and can it be assembled?» while the robot is
still a plan. It does not need the parts modelled in build123d. It samples every part, screw, contact and resistor as
a point cloud. It reads the body and base cavities from their own build modules' section functions and the real
`cad/legs` parts over 24 crank poses. Every gap is signed against its clearance in [`../../fits.py`](../../fits.py).
It found the layout of round r00. Now that the parts are modelled, it is **not a gate**: the full `cad_verify` of
the real parts ([`../verify.py`](../verify.py)) is. Run it again only to try a new layout before modelling it.

```bash
uv run python cad/robot/fitcheck/check.py > cad/robot/fitcheck/out/report.txt    # ≈ 19 min
```

Progress goes to stderr. The report lists the least margins first, then `FAILING: n AT TOLERANCE …: m of N checks`.
`out/rows.json` has every row. With `FIG=1`, `out/window_old_vs_new.png` compares the leg windows. Point clouds are cached in
`.cache/`, keyed by their inputs and by the modification time of the modules they come from. `out/` and `.cache/` are
not in git.

| File | What it is |
|---|---|
| `check.py` | Builds every part and runs every pair, lift-off, assembly path and driver line. `need()` says which clearance each pair needs; `LAYOUT` holds the layout knobs chosen so far (each can be overridden from the environment) |
| `fit_env.py` | The robot's scale (from `../spec.json`), motion parameters, and the inner surfaces of the body and base in the robot frame |
| `fit_legs.py`, `fit_legmesh.py` | The real `cad/legs` arm and blade, bent onto `cad/motion.py`'s neutral leg at S and carried per pose |
| `fit_samplers.py` | Samplers: cylinders along any axis, swept discs |
| `n1.py` | Whole-robot overlap check on the built coarse STLs (`out/*.stl`): every part pair at the 24 crank poses, worst overlap thickness (2 V / A) and gaps under 1 mm; ≈ 18 s, `../../.venv/bin/python n1.py` |

## Which clearance a pair needs

| Pair | Needs | Fit |
|---|---|---|
| A moving leg and anything | 0.5 | `LEG_PATH` |
| A gear and a fixed part (radial) | 0.4 | `GEAR_TIP` |
| The crankshafts and anything | 0.25 | `TURN` |
| A part and the body or base shell (large parts) | 0.2 | `LOCATOR` |
| A bought part (motor, cell, screw) and a printed one | 0.15 | `STEEL` |
| Bendable leads, wires and springs among bought parts | 0 (no overlap) | — |
| Two fixed printed parts side by side | 0.1 | `NEIGHBOUR` |
| A part along its assembly path | 0.1 | `NEIGHBOUR` (its running fit is checked in place) |
| Designed contacts (a part in its seat, a joint) | Their own fit | Declared in `check.py` |

A gap less than 0.1 mm under its need is reported «at tolerance»: that is the sampling noise, not a failure.
Wires take no volume (`../spec.json`). Only a hole or a slot is needed where a wire passes a wall.
