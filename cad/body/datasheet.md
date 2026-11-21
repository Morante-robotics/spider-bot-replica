# body datasheet

jenscolt's top shell (`cad/carcass-jenscolt/spideybot_body.stl`) rebuilt as one parametric build123d solid, in
jenscolt's frame at S = 1 (mm). The mesh is only the reference: `build.py` never reads it. Numbers live in
`build.py`'s parameter block, each with the probe it came from; this page does not copy them.

## Status (2026-11-20)

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| body | `build.py` | `spec.json` (N1, fidelity seen from above) | `rounds/_check/gates.json` |

## Structure

| Region | Model | Numbers |
|---|---|---|
| Outer skin | loft of 8 horizontal superellipse control sections up the vertical spine x = `CX` (`SKIN_CTRL`: z, half-width a, front / back half-lengths, front / back exponents), PCHIP-interpolated to 23 built sections | 40 (+ z of each) |
| Wall | inner skin lofted from the same table, each meridian (a, bf, bb) eroded by `WALL` in its own (r, z) plane, cut from the outer skin; open at `Z_RIM` | 1 (`WALL`) |
| Eye block | box behind the face (`BLOCK_*`), open under the eye axis behind `BLOCK_OPEN_Y`; side plates (`FRAME_*`) and chin bridge (`BRIDGE`) | 9 |
| Big eyes | bores (`EYE_*`), knurled rings (`RING_*`, 24 teeth) | 8 |
| Nose plate, small eyes | `NOSE`, `SEYE_*` | 10 |
| Chin arch | half-ellipse cut (`CHIN`) | 2 |
| Side scoops | crescent (`SCOOP`: two circles in (y, z)) of the skin widened by a proud depth, on each side | 7 |
| Side panel lines | band at `GROOVE_Y` minus the skin inset by `GROOVE_D` | 4 |
| Rear | lip on the top (`REAR_LIP`), wedge tab under the rim (`TAB`) | 8 |
| Screw bosses | tubes with holes through the top (`BOSS_*`) | 5 |

Mirror: every left/right feature is one definition placed at `CX ∓ dx`.

## Fidelity (`mesh_ref.py compare --view above`, default limits p95 3.3 / max 6.6 mm since 2026-11-21)

Morante, 2026-11-20, after seeing round r00: «A mí me vale el cuerpo como está, haz que pase a 0.69». The spec
held his own limits (p95 2.1 / max 6.0, dropped 2026-11-21: the default is now looser) and holds a judge pass
threshold of 0.69 (the rubric's is 0.70). Round r00:
part → ref p95 2.04 / max 5.1 mm (p99.9), ref → part p95 2.08 / max 5.6 mm: PASS; judge 0.69, passed. Skin alone:
within 0.1–0.3 mm median per section. Not modelled: the curved panel ridges on the dome and the chin grille (Open
items, if Morante wants them). Build 60–80 s, `--sweep` ≈ 6 min.

## Simplified, and why

- The curved panel lines on the top and the sides (≈ 1 mm deep, 1.5 wide) are left out; only the deep side line at
  y ≈ 0 is cut. They are the main thin dark lines left on the heat map.
- The eye block's inside is a box (the reference's frame of C-shaped arms is hidden except through the bores and the
  chin): what shows through the bores and the chin is approximated by two side plates and a bridge.
- The rings' knurl is 24 cubes, the scoops are a uniform 2.5 mm proud (the reference tapers from ≈ 4 at the front
  edge to flush), the tab's bottom is straight (the reference's is a shallow arc).
- The inner wall is a uniform erosion; the reference's wall thickens at the rim. It shows only through the rim
  opening at low angles and the bores.

## Build

STEP ≈ 10 MB (the knurl teeth), build ≈ 57 s (target 15 s: the knurl and the final fuse are the slow part).

## Commands (from this folder)

```bash
../../.venv/bin/python build.py            # out/body.stl + .step
../../.venv/bin/python build.py --bare     # skin and wall only
../../.venv/bin/python build.py --sweep    # S 0.65, wall and section scale 0.8x / 1.2x
(cd ../.. && uv run python tools/rounds.py check cad/body)
```
