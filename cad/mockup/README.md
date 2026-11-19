# N0 mock-up

The whole robot in simple shapes, checked and drawn in seconds. Part of the looks-first redesign described in the
[build log](../../build-log/3-legs-and-drive.md#n0-mock-up-the-looks-robot-in-simple-shapes).

| File | What |
|---|---|
| `sizing.py` | Smallest scale of jenscolt's body that holds the motor, the cells and the switch |
| `sizing_figure.py` | Draws the sizing result |
| `n0.py` | The mock-up: parameters `P0`, the checks over 24 crank poses, the timing; `--png` draws four views |
| `n0_render.py` | The four-view drawing used by `n0.py` |
| `n1.py` | N1: jenscolt's real body, base, eyes and legs at 60 % (clustered to ≤ 25k triangles), legs warped onto N0's path, one window per leg root, checks over 24 poses (≈ 10 s); `--png` draws four views |
| `n1_render.py` | The four-view drawing used by `n1.py` |
| `images/` | The mock-up's figure |

Run from the repository root: `uv run python cad/mockup/n0.py` (checks) or `uv run python cad/mockup/n0.py --png out.png --lang en`.
The first run builds a distance field of the body in `.cache/` (not in git). The body model is third party
(CC BY-NC-SA, see [`../carcass-jenscolt/`](../carcass-jenscolt/)).

N1: `uv run python cad/mockup/n1.py [--png out.png --lang en]`. The first run caches the clustered meshes in `.cache/` (not in git). The legs, body and base are third party too (CC BY-NC-SA).
