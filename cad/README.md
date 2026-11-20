# Spider-Bot CAD

Every part of the robot is modelled in code ([build123d](https://github.com/gumyr/build123d)) or kept as a mesh,
one folder per design. This page holds the rules every design follows, so a new one starts from the same layout,
the same axes and the same clearances. Set up the Python environment once from the repo root with `uv sync`.

## Conventions

| What | Rule |
|---|---|
| Units | Millimetres, degrees in arguments, radians inside the maths |
| Axes | As the carcass ([carcass-120](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/carcass-120)) and the [simulator](../sim/): **Z up**, **forward = −Y**, **+X = the robot's right** (the right legs' side) |
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
| `datasheet.md` | The one page read first: status, where each topic lives (file and section), the commands |
| `README.md` | What the design is, its parts and hardware, how to print and assemble it (no status: that is in the build log) |
| `spec.json` | The request: level (N0/N1/N2), purpose, pass criterion, must-haves, dimensions with their sources, references, gates, views, judge, how many refine rounds. Written once (`rounds.py init`) |
| `plan.json` | The plan: parts, joints, assembly, alternatives, acceptance items, open questions. Written before modelling, checked by `rounds.py validate` |
| `design-plan.md` | The plan as tables, generated from `plan.json` by `validate` (never edited by hand) |
| `rounds/rNN/` | One round: the source snapshot, gates, views, the judge's brief and answer, the score. Local, not in git |
| `build.py` | The parametric model. Parameters at the top, each with its source; `--part <name>` rebuilds one part |
| `out/` | STEP (for Onshape) and STL (for printing) of every part, written by `build.py` |
| `verify.py` | The [`cad_verify`](../tools/cad_verify.py) spec: every part, motion, joints with their fits, marks, assembly, access, measurements |
| `verify-result.txt` | The last full verification (`PASS`, not `PARTIAL`) |
| `design-review.md` | Fits, strength, retention, assembly, seats, print, marks, carry-over, pre-mortem: each with the number or picture that shows it |
| `images/` | Figures made by scripts (`verify/` from `cad_verify --render`, others from [`tools/figures.py`](../tools/figures.py)) |

## Rounds

A design is worked in rounds, a method adapted from
[3dcodeverse's harness](https://github.com/gaoypeng/3dcodeverse/tree/main/harness) (Apache-2.0):
[`tools/rounds.py`](../tools/rounds.py) runs it, from the repo root.

1. **Request** (`init`) and **plan** (`plan.json`, then `validate` until `PASS`). The validator catches, in
   code, what a review round used to: a part never assembled, a joint held by «gravity», a fit that is not in
   `fits.py`, a placeholder, a must-have with no acceptance item. A plan that changes after it validated is a
   re-plan: the rounds start over.
2. **Round 0**: the code is written from the plan, `check` runs every gate (`cad_verify` at N2, the level's own
   check at N0 and N1) until no `FAIL`, then `round WS 0` snapshots the source, renders the views and writes the
   judge's brief.
3. **Blind judge**: a fresh agent that never sees the code reads only the brief and the pictures (the design next to
   the reference, the toy), scores the rubric's criteria ([`tools/rubrics/looks.json`](../tools/rubrics/looks.json))
   and answers each acceptance item. `score WS 0` turns that into a number with explicit caps (a gate `FAIL` caps it
   at 0.60, an unverified must item at 0.60–1.00) and one improvement list, gate failures first.
4. **Refine rounds**: exactly as many as were asked for in `spec.json`. Each one makes the last score's
   improvement list and nothing else, then packs and scores again. Rounds stop when they are done, when the score
   passes with nothing left to improve, or when it fell two rounds running; the deliverable is the best round
   (`best` restores its source).

```bash
uv run python tools/rounds.py validate cad/<design>
uv run python tools/rounds.py check cad/<design>
uv run python tools/rounds.py round cad/<design> 0      # prints the JUDGE INSTRUCTION
uv run python tools/rounds.py score cad/<design> 0
uv run python tools/rounds.py status cad/<design>
uv run python tools/rounds.py ready cad/<design> --kit <kit.html>   # N2: the ready-to-print checklist
```

Reference images are private (a product photo): `spec.json` names them as `{refs}/<file>` and `CAD_REFS` points at
the folder that holds them, outside the repo.

Commands, from the design folder:

```bash
../../.venv/bin/python build.py                     # every part into out/ (coarse STL; --fine for the printed one)
../../.venv/bin/python ../../tools/cad_verify.py verify.py --smoke --only <part>   # after every fix: seconds
VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify.py --quick --only <part>   # a moving part changed
../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify   # once, at the end
../../.venv/bin/python ../../tools/figures.py verify.py images --lang es
```

Designs that use another design's parameters import its `build.py` as a module (one source per number), never
copy a value: with the repo root on `sys.path`, `from cad import design` and `C = design("crankshafts")`
([`__init__.py`](__init__.py)); a design loads its own `build.py` the same way. What several designs share (the
simulator's geometry, hardware sizes, build123d helpers) is in [`common.py`](common.py). The robot master model,
[`robot.py`](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/robot.py), holds the datums, the carcass envelope, the interfaces between designs and the bought parts'
sizes (catalogue values until they are measured): a design takes these numbers from it, never a copy.

Geometry stays light: no cut or check runs against the carcass body's scan (102k triangles); `robot.carcass_proxy()`
(within 0.2 mm, cached) or `robot.carcass_envelope()` (boxes) take its place. Shared stage caching for mesh builds:
[`tools/stage_cache.py`](../tools/stage_cache.py). A spec may name each interface's parts in `GROUPS`, so
`--only <group>` checks one interface instead of the whole robot.

## Assembly steps

An `ASSEMBLY` step in `verify.py` is `(part, side)` (the part comes in straight, from that side) or `(part, path)`:
a list of moves in mm, in the order the part moves going in, e.g. `("body", [[0, 0, -30], [0, 4, 0]])` = lowered
30 mm, then slid 4 mm along +Y into place. The check starts at the place minus all the moves and sweeps each move
against the parts already in; it reports «goes in: down 30 mm, then +Y 4 mm» or «blocked on move 2 at 1.75 mm».

## What is printed and kept in git

- STL and STEP of a part are committed when that version is printed, and at milestones.
- Mesh parts (`body-v2`, `front-block-v2`: the STEP is the STL sewn face by face, minutes and 50-180 MB) write their
  STEP only with `--step`: pass it before an Onshape upload or a milestone, never in the inner loop.
- A print plate (`../print/*.3mf`) is committed once, for the version that was printed; a re-slice of the same
  parts does not get a new commit, since the README's command rebuilds it. Plates of milestones also go into the
  GitHub release.
- Generated helper meshes (assemblies, lifted bodies) are not committed: the script that writes them is.
