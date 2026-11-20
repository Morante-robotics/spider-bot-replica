# Spider-Bot CAD

Every part of the robot is modelled in code ([build123d](https://github.com/gumyr/build123d)), one folder per
design. No printed part is a mesh: a part that exists only as a mesh (a downloaded model, a scan) is first converted
to parameters (see «From a mesh»), and the mesh stays only as its reference. This page holds the rules every design follows, so a new one starts from the same layout,
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
| Fidelity to a reference mesh | p95 ≤ 1 % and max ≤ 2 % of the reference's largest extent, never below 0.5 / 1.0 mm (max checked on the 99.9th percentile: one stray sample does not decide), both ways, at the reference's scale: [`mesh_ref.py`](../tools/mesh_ref.py) `limits()` (Morante, 2026-11-20). Other limits for one part only as an approved exception (`rounds.py except`, «From a mesh») |
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

Geometry stays light: no cut or check runs against a reference mesh (jenscolt's body is 102k triangles); checks
read the parametric parts' coarse STL, cached, or boxes. That STL is the model's own export, so `cad_verify` (and
everything that loads parts through it) fails before any check when an STL is older than its `build.py` or the shared
`common.py`, `fits.py`, `motion.py`: rebuild first. The approved motion (scale, crank, leg path) is
[`motion.py`](motion.py); every design imports it, never a copy. Shared stage caching for mesh builds:
[`tools/stage_cache.py`](../tools/stage_cache.py). A spec may name each interface's parts in `GROUPS`, so
`--only <group>` checks one interface instead of the whole robot.

## From a mesh

A part that exists only as a mesh is converted once, by the `mesh-to-cad` agent, into a design folder like any
other: the reference mesh is measured, never read by `build.py`.

1. The request, with Morante (what to keep, what to leave out, how much detail):
   `uv run python tools/rounds.py init cad/<design> --level N1 --purpose "..." --mesh <part>=<ref.stl> [--mesh ...]
   [--edit] --rounds 1`. It writes the gates every conversion runs and the reference picture:
   - `source`: `build.py` reads no mesh (`mesh_ref.py source`);
   - `build`: `build.py --sweep` rebuilds at S 0.65 and with every wall and section scale at 0.8× and 1.2×, each one
     valid closed solid;
   - `edit` (`--edit`, organic parts): `build.py --edit` moves the spine (a target curve, length +10 %, bow +3 mm);
   - `fidelity-<part>`: `mesh_ref.py compare` against its reference at the default limits (relative to its size),
     with a heat map in
     `images/fidelity-<part>.png`. When the reference's inside is not kept (jenscolt's body), the coordinator adds
     `--view above` (or `below`): only what a viewer outside sees counts, on both meshes.
2. The structure: primitives by their named dimensions; organic skins as a loft of ≤ 8 control sections along a
   spine of ≤ 5 points (≤ ~60 numbers per skin); shell walls as an offset, separate from the outer form; every
   detail placed in its host's frame, so it follows an edit; left and right as one model and a mirror.
3. Rounds as for any design: r00, the blind judge on `mesh_ref.py views` (the design and the reference in the same
   four views and framing), the refine rounds Morante asked for, then his «se parece».
4. **Exceptions, per part, only with Morante's approval.** When a part cannot meet a rule within the agent's budget,
   the agent stops and asks for one (`EXCEPTION_REQUEST`: the rule, by how much, the heat map, its proposal). Three
   kinds exist: the part's own fidelity limits, the design's own judge threshold, a detail of the reference left
   out. Never more parameters or more time. Each is recorded with his reason by
   `uv run python tools/rounds.py except cad/<design> <part> --reason "..." [--p95 MM] [--max MM] [--judge 0.69] [--drop "..."]`
   in `spec.json` `exceptions` (the only change to `spec.json` after `init`); `validate` refuses own limits or a
   lower threshold without one, and the judge's brief lists the details left out so it does not count them.

[`legs/`](legs/) is the worked example: jenscolt's leg as a 5-point spine and 6 sections (50 numbers for the
blade's skin, ≈ 270 as a table of sections), bent onto the N0 leg path by its spine alone.

```bash
uv run python tools/mesh_ref.py info <ref.stl>                         # size, triangles, watertight
uv run python tools/mesh_ref.py sections <ref.stl> --axis z --n 12     # the sections to model from
uv run python tools/mesh_ref.py compare cad/<design>/out/<part>.stl <ref.stl> --png heat.png   # limits from its size
uv run python tools/mesh_ref.py views out.png --ref <ref.stl> --parts cad/<design>/out/<part>.stl
```

## Assembly steps

An `ASSEMBLY` step in `verify.py` is `(part, side)` (the part comes in straight, from that side) or `(part, path)`:
a list of moves in mm, in the order the part moves going in, e.g. `("body", [[0, 0, -30], [0, 4, 0]])` = lowered
30 mm, then slid 4 mm along +Y into place. The check starts at the place minus all the moves and sweeps each move
against the parts already in; it reports «goes in: down 30 mm, then +Y 4 mm» or «blocked on move 2 at 1.75 mm».

## What is printed and kept in git

- STL and STEP of a part are committed when that version is printed, and at milestones.
- A print plate (`../print/*.3mf`) is committed once, for the version that was printed; a re-slice of the same
  parts does not get a new commit, since the README's command rebuilds it. Plates of milestones also go into the
  GitHub release.
- Generated helper meshes (assemblies, lifted bodies) are not committed: the script that writes them is.
