# Robot (N2) datasheet

The one page an agent reads first: status, where each topic lives, the commands. It points at numbers in code and
never copies them. Updated by whoever changes the design, in the same change.

## Status (2026-11-19, PLAN rev 4, waiting for Morante's open questions)

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| all (17 in the part list) | not modelled: PLAN rev 4 (answers `plan-review.md` rev 2 B1–B4, items 4 and 8), waiting for Morante's open questions; B3 inside fit < 0 | — | — |

`build.py`, `verify.py`, `README.md`, `design-review.md` are unfilled copies of `../_template/`.

## Where to read, by task

| Task | Read | Section |
|---|---|---|
| The approved look and motion (scale, leg path, crank, inner boxes) | `../mockup/n0.py` `P0`, `../mockup/n1.py` `P1`, `P0_N1` | parameters at the top |
| Why the look is fixed | `../../build-log/3-legs-and-drive.md` | «N0 mock-up», «N1 form», Decisions |
| Parts, joints, assembly, alternatives, coupons, open decisions | `design-plan.md` | each heading |
| Probe numbers (inside fit, arms, pivots, gears, cells, pins, support grams) | `probes.py` (each prints its result); used in `design-plan.md` | «Review items», «Inside fit», «Support from the slicer» |
| Crank offsets per crank (arm clearance) | `probes.py` `CRANK_DY_65` (rev 4, frozen, mm at S 0.65, no rescale); `CRANK_DY` (rev 2, Ø3, mm at S 0.60) and `CRANK_DY_D2` (rev 3) are history | — |
| Crown pair, transfer idler | `probes.py` `CROWN`, `crown_drive` | `design-plan.md` «Crown pair» |
| Inside fit with every box (B3) | `probes.py` `search_b3`, `fixed_boxes`, `h3e_boxes`; `layouts4`, `motoronly` | `design-plan.md` «Inside fit» |
| Fits | `../fits.py`; to add at N2 as assumed: `DSHAFT_N10`, `MOTOR_SEAT_N10`, `MOTOR_PRELOAD_N10` (K1, K2), face-gear backlash (K3b) | — |
| Bought parts | `../../hardware.md` (N10, AG13 numbers: datasheet, measure on arrival) | — |
| Leg motion and gait groups | `../../sim/toy_leg_3d.py` | `NOTCHES_RIGHT`, `GROUP` |
| Plan figures | `plan_figure.py` → `images/plan-exploded.png`; `probes.py figure` → `images/plan-windows.png` | — |

## Commands (from the repo root)

```bash
uv run python cad/robot/plan_figure.py cad/robot/images/plan-exploded.png    # plan diagram (≈ 15 s)
uv run python cad/robot/probes.py                 # quick probes: gear cell pins pivot arms neck crown asm (≈ 20 s)
uv run python cad/robot/probes.py layouts4 3.0    # B3 inside fit, one body wall (≈ 70 s)
uv run python cad/robot/probes.py motoronly       # B3 bound: motor group without cells, D4a and D4b (≈ 2 min)
uv run python cad/robot/probes.py slice           # slicer support grams, body/base candidates (≈ 4 min)
uv run python cad/robot/probes.py figure cad/robot/images/plan-windows.png
```
