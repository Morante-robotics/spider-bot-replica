# body

jenscolt's top shell as one parametric build123d solid: a skin lofted from 8 control sections with the wall as a
separate inward offset, the eye sockets with their knurled rings, the nose plate and small eyes, the chin arch, the
side scoops and panel line, the rear lip and tab, and the screw bosses. `build.py` never reads a mesh; the shell
mesh is only the reference it is measured against. Level N1 (form): [`../robot/`](../robot/) scales it to 70 %
and adds the leg notches, the front panel and the snap fingers: that is the printed body.

**License:** derived from jenscolt's [Spidey-Bot](https://www.thingiverse.com/thing:5196618), so [CC BY-NC-SA](../carcass-jenscolt/LICENSE.txt): non-commercial, share-alike, with credit to jenscolt; unlike the rest of the repo (see [`carcass-jenscolt/README.md`](../carcass-jenscolt/README.md)).

## Parts

| File (`out/`) | What it is | Size (mm) | Quantity |
|---|---|---|---|
| `body.stl`, `body.step` | the top shell, open underneath, in jenscolt's frame at 100 % | 96.0 x 110.5 x 66.1 | 1 |

Hardware: none.

- `spec.json`: the request. `plan.json` gives `design-plan.md`. `datasheet.md`: structure, fidelity, what is left out.
- `build.py`: the part into `out/`; `--sweep` checks the variants (S 0.65, wall and section scale 0.8x and 1.2x).

## Rebuild and check

`../../.venv/bin/python build.py --sweep`, then `uv run python tools/rounds.py check cad/body` from the repo root.
See [the CAD rules](../README.md#from-a-mesh).
