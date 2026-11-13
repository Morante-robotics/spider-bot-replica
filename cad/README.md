# Spider-Bot CAD

Every part of the robot is modelled in code ([build123d](https://github.com/gumyr/build123d)) or kept as a mesh,
one folder per design. This page holds the rules every design follows, so a new one starts from the same layout,
the same axes and the same clearances. Set up the Python environment once from the repo root with `uv sync`.

## Conventions

| What | Rule |
|---|---|
| Units | Millimetres, degrees in arguments, radians inside the maths |
| Axes | As the carcass ([carcass-120](carcass-120/)) and the [simulator](../sim/): **Z up**, **forward = −Y**, **+X = the robot's right** (the right legs' side) |
| Origin | The carcass's origin at 120 %; every design places its parts in this frame (`poses()` in its spec), and exports each part in its own print frame |
| Crank angle | 0° = every crank level; it turns positive about +X |
| Left and right | Seen from behind the robot, looking forward: as the robot's own right and left |
| Clearances | Only from [`fits.py`](fits.py): measured on real prints, never typed in a design |
| Names | Parts in kebab-case (`leg-front-left`), numbered front to rear (`crankshaft-1` is the front one); versions as `-v2`, never «new» or «final» |

## A design folder

Copy [`_template/`](_template/) to start one. Every design has the same files, so anyone (and every agent) knows
what to run and where the result is:

| File | What it is |
|---|---|
| `README.md` | What the design is, its parts and hardware, how to print and assemble it (no status: that is in the build log) |
| `design-plan.md` | Part list, joint table, assembly sequence, alternatives, diagram: written before modelling |
| `build.py` | The parametric model. Parameters at the top, each with its source; `--part <name>` rebuilds one part |
| `out/` | STEP (for Onshape) and STL (for printing) of every part, written by `build.py` |
| `verify.py` | The [`cad_verify`](../tools/cad_verify.py) spec: every part, motion, joints with their fits, marks, assembly, access, measurements |
| `verify-result.txt` | The last full verification (`PASS`, not `PARTIAL`) |
| `design-review.md` | Fits, strength, retention, assembly, seats, print, marks, carry-over, pre-mortem: each with the number or picture that shows it |
| `images/` | Figures made by scripts (`verify/` from `cad_verify --render`, others from [`tools/figures.py`](../tools/figures.py)) |

Commands, from the design folder:

```bash
../../.venv/bin/python build.py                     # every part into out/
VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify.py --quick --only <part>   # while iterating
../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify
../../.venv/bin/python ../../tools/figures.py verify.py images --lang es
```

Designs that use another design's parameters import its `build.py` as a module (one source per number), never
copy a value. The folders made before this layout ([drive](drive/), [base](base/)) still have their own names
(`check.py`, `verify_gear_train.py`); each moves to this layout the next time it changes.

## What is printed and kept in git

- STL and STEP of a part are committed when that version is printed, and at milestones.
- A print plate (`../print/*.3mf`) is committed once, for the version that was printed; a re-slice of the same
  parts does not get a new commit, since the README's command rebuilds it. Plates of milestones also go into the
  GitHub release.
- Generated helper meshes (assemblies, lifted bodies) are not committed: the script that writes them is.
