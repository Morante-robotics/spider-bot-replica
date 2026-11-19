# Robot (N2) datasheet

The one page an agent reads first: status, where each topic lives, the commands. It points at numbers in code and
never copies them. Updated by whoever changes the design, in the same change.

## Status (2026-11-19, PLAN rev 5, does not fit at S 0.65: PAUSED for Morante's decision)

**Resume here.** Read the build-log entry «N2 rev 5: the inside does not fit at 65 %» (`../../build-log/3-legs-and-drive.md`)
and the N2 row of Open items. Best layout F2s-sw: −1.75 with boxes, −1.74 with real shapes (`probes.py real F2s-sw 3.0`),
20 pairs overlap. Morante asked for the definitive scale at which everything fits and can be assembled, never grown
later. `probes.py sweep <S…>` counts every part, screw, pin, contact and wire with a +1.0 mm margin, assembly paths
and Ø6 × 30 tool access. Only S 0.65 was measured (−5.25). Its assembly order fails: the motor sits over the strip, so
the spine cap, its screws and the crankshafts cannot go in from +z after it. That needs a layout or order fix before
the sweep (≈ 1.5–2 h as a batch) can give a number, which then needs an independent audit of `sweep_boxes_<S>.txt`.
The cells as one block of 2 × 3 (Morante) are layout `L5["F2s-1b"]`. Nothing runs; no rounds yet.

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| all (`plan.json`, 16 printed parts + hardware) | not modelled: PLAN rev 5 (no eyes board, switch under the base pressed into a floor pocket from inside: no cover, no screw, `plan.json` → `design-plan.md`, validate PASS). Inside fit **< 0 with every box placed**: best F2s-sw −1.75 at D4a, strip gear counted against the arms (−1.64 crown↔shell with it exempt; `probes.py layouts5 F2s-sw 3.0`). With real shapes on that layout (`probes.py real`): least −1.74 (strip gear 2↔arms), 20 pairs still overlap, does not fit | — | — |

`build.py`, `verify.py`, `README.md`, `design-review.md` are unfilled copies of `../_template/`. `views.py` draws the
N1 meshes for now (r00 task 1: the N2 STLs).

## Where to read, by task

| Task | Read | Section |
|---|---|---|
| The approved look and motion (scale, leg path, crank, inner boxes) | `../mockup/n0.py` `P0`, `../mockup/n1.py` `P1`, `P0_N1` | parameters at the top |
| Why the look is fixed | `../../build-log/3-legs-and-drive.md` | «N0 mock-up», «N1 form», Decisions |
| Parts, joints, assembly, alternatives, open decisions | `plan.json` (source), `design-plan.md` (generated) | each heading |
| Probe numbers (inside fit, arms, pivots, gears, cells, pins, support grams) | `probes.py` (each prints its result); used in `design-plan.md` | «Review items», «Inside fit», «Support from the slicer» |
| Crank offsets per crank (arm clearance) | `probes.py` `CRANK_DY_65` (rev 4, frozen, mm at S 0.65, no rescale); `CRANK_DY` (rev 2, Ø3, mm at S 0.60) and `CRANK_DY_D2` (rev 3) are history | — |
| Crown pair, transfer idler | `probes.py` `CROWN`, `crown_drive` | `design-plan.md` «Crown pair» |
| Inside fit with every box (B5, rev 5) | `probes.py` `L5` (candidates), `search_b5`, `_drive5`, `_chain`, `pack_boxes`; results in `out/.cache/layouts5_<name>_<wall>.json` | `plan.json` alternatives, open questions |
| Inside fit, rev 4 (history) | `probes.py` `search_b3`, `layouts4`, `motoronly` | — |
| Fits | `../fits.py`; to add at N2 as assumed: `DSHAFT_N10`, `MOTOR_SEAT_N10`, `MOTOR_PRELOAD_N10` (K1, K2), face-gear backlash (K3b) | — |
| Bought parts | `../../hardware.md` (N10, AG13 numbers: datasheet, measure on arrival) | — |
| Leg motion and gait groups | `../../sim/toy_leg_3d.py` | `NOTCHES_RIGHT`, `GROUP` |
| Plan figures | `plan_figure.py` → `images/plan-exploded.png`; `probes.py figure` → `images/plan-windows.png` | — |

## Commands (from the repo root)

```bash
uv run python cad/robot/plan_figure.py cad/robot/images/plan-exploded.png [F2s 3.0]   # plan diagram (≈ 15 s)
uv run python cad/robot/probes.py layouts5 F2s 3.0   # one rev 5 candidate at one body wall (≈ 1-3 min)
uv run python cad/robot/probes.py layouts5 table     # every rev 5 result found in the cache
uv run python cad/robot/probes.py real F2s-sw 3.0     # cached layout re-measured with real shapes (manifold3d, ≈ 2.5 min)
uv run python cad/robot/probes.py sweep 0.65 0.70 …  # smallest S: F2s-1b re-searched per S, every box, gaps ≥ 1.0, paths, tools, train (→ out/.cache/sweep_<S>.json, sweep_boxes_<S>.txt)
uv run python tools/rounds.py validate cad/robot     # plan.json → design-plan.md
uv run python cad/robot/probes.py                 # quick probes: gear cell pins pivot arms neck crown asm (≈ 20 s)
uv run python cad/robot/probes.py layouts4 3.0    # B3 inside fit, one body wall (≈ 70 s)
uv run python cad/robot/probes.py motoronly       # B3 bound: motor group without cells, D4a and D4b (≈ 2 min)
uv run python cad/robot/probes.py slice           # slicer support grams, body/base candidates (≈ 4 min)
uv run python cad/robot/probes.py figure cad/robot/images/plan-windows.png
```
