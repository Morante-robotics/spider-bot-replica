# base datasheet

N1 conversion of cad/carcass-jenscolt/spideybot_base_bowl.stl (derived reference: jenscolt's bowl without his inside). Parameters and their sources: top of build.py.

## Status (2026-11-20, refine round r01)

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| base | build.py (mesh-to-cad, r01 rebuild of the skin) | spec.json | gates PASS (source, build + sweep, fidelity-base), 2026-11-20 |

## Structure

| Part | Structure | Numbers | STEP | Build |
|---|---|---|---|---|
| base | skin: plan superellipses (exponent N_FOOT 1.6 at the foot to N_TOP 2.0 at the ledge) whose half-widths follow two smooth meridian curves w(z) = W (1 - ((ZE - z)/H)^P)^(1/P), one across x, one along y (front = back); 14 loft stations are sampled from those numbers. Band: the ledge section grown by LEDGE, straight up. Wall: the same table shrunk by WALL, cut from the outer skin (no offset, no sewn faces). Rim: one ear per side wall, a side-view polyline RIM_EAR beyond EAR_DX. Back: vertical cylinder scoop with its wall kept as the back sheet. Front leg windows: arch + walled pocket (cheek face, flat front face, floor) + post, one parameter set mirrored. Wall windows (4 angles) and rim slot: one list, mirrored. All cutters in one boolean. | 51 (17 skin/band/wall) | 2.9 MB | 13 s |

## Fidelity (mesh_ref.py compare --view below; 2026-11-20, r01)

Limits: this design's own, p95 ≤ 1.8 / max ≤ 3.1 mm, an exception Morante approved on 2026-11-20 (`spec.json` →
`exceptions`); the size-relative default would be 1.01 / 2.02 mm.

| Part | part to ref max (p99.9) / p95 | ref to part max (p99.9) / p95 |
|---|---|---|
| base | 3.09 / 1.79 | 2.00 / 0.83 |

Where the remaining error is: the band and ears above the ledge (z 60-66, 1.5-2.5 mm): the reference flares from r 49.1 at z 60 to 50.6 at z 62 and its ear is 1.0-1.3 mm thick, ours has a step (LEDGE) and an ear LEDGE + WALL/2 = 1.9 mm thick so it stays joined to the bowl wall for every wall in the sweep; the x meridian (rms 0.86, max 2.1) rounds off the reference's foot bulge at z 42.

## Named features (one parameter set, mirrored about the plane x = CX)

| Feature | Parameters | Source |
|---|---|---|
| front leg window | WIN_FLOOR_Z, WIN_ARCH_R, WIN_BACK_Y (arch, symmetric by construction); SIDE_Y, SIDE_DX, SIDE_LEAN, SIDE_Z (the walled pocket beside it, the side wedge); POST_DX, POST_TOP (the post between arch and cheek) | probe2.py front depth map, cheek.py |
| wall windows | WWIN_ALPHA (4 angles), WWIN_W, WWIN_Z0, WWIN_Z1 | win.py (left/right means) |
| rim slot | RIM_SLOT_ALPHA, RIM_SLOT_W, RIM_SLOT_DEPTH | win.py |
| rim ear | RIM_Z, EAR_DX, RIM_EAR | rays.py |

Every one is built once in `bowl()` inside `for sx in (-1, 1)` (or is symmetric): the left and right windows, pockets, wall windows and slots share one parameter set.

## Simplified

- The reference's wall windows are not quite mirrored (+x 58.6 / 81.6 / 99.3 / 132.6 deg, -x 58.9 / 87.1 / 103.2 / 135.2): one mirrored list of the means (up to 2.8 deg, 2.4 mm, off).
- The rim ledge is a step, not the reference's 2 mm flare.

## Edits

Every number is a named parameter; --sweep rebuilds S 0.65, wall 0.8x/1.2x, section scale 0.8x/1.2x (plan positions of the cutters follow the section scale): all one valid solid.

## Commands

```bash
../../.venv/bin/python build.py --sweep
(cd ../.. && uv run python tools/rounds.py check cad/base)
(cd ../.. && uv run python tools/rounds.py validate cad/base)
```
