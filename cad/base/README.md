# base

jenscolt's base reduced to its outer bowl, rim and front leg windows, as parameters (N1 conversion; his posts, mounts and tabs are left out). [`../robot/`](../robot/) scales it to 70 % and adds the leg windows, the snap ribs and the pockets the mechanism needs: that is the printed base.

**License:** derived from jenscolt's [Spidey-Bot](https://www.thingiverse.com/thing:5196618), so [CC BY-NC-SA](../carcass-jenscolt/LICENSE.txt): non-commercial, share-alike, with credit to jenscolt; unlike the rest of the repo (see [`carcass-jenscolt/README.md`](../carcass-jenscolt/README.md)).

## Parts

| File (`out/`) | What it is | Size (mm) | Quantity |
|---|---|---|---|
| `base.stl`, `base.step` | hollow bowl, open on top, 1.2 mm wall | 101 x 88 x 35 | 1 |

Hardware: none.

## Rebuild and check

`../../.venv/bin/python build.py --sweep`, then `uv run python tools/rounds.py check cad/base` from the repo root. See [the CAD rules](../README.md#from-a-mesh).
