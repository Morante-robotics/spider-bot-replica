# Eyes datasheet

One revolved cup, three parameter sets: jenscolt's large eye, small eye and front sensor domes, each in its reference
frame (N1 form parts, not printed).

## Status (2026-11-20)

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| eye, small-eye, sensor | `build.py` (`cup()`, `CUPS`) | `spec.json` | `rounds.py check cad/eyes` |

## Structure and numbers

- Structure: revolved profile about +Y: flat apex (RF), elliptic dome of depth H up to the outer radius R, straight
  wall to length L, wall thickness W. 5 numbers + apex centre (3) per cup; 24 numbers in all plus S.
- Fidelity (p95 / max, mm, part to ref and ref to part): eye 0.64 / 0.71 and 0.40 / 0.48; small-eye 0.31 / 0.35 and
  0.19 / 0.23; sensor 0.29 / 0.33 and 0.18 / 0.22. Limits 1.0 / 2.5.
- STEP: a few KB each; build under 1 s per part.
- Simplified: the apex is flat and the dome an exact ellipse arc; reference relief under 0.3 mm is not modelled.
  Meshes are not watertight; the visible surface was modelled.

## Where to read, by task

| Task | Read | Section |
|---|---|---|
| Change a cup | `build.py` | `CUPS`, `cup()` |
| Why these numbers | `build.py` | docstring |

## Commands (from this folder)

```bash
(cd ../.. && uv run python tools/rounds.py validate cad/eyes)
../../.venv/bin/python build.py --sweep
(cd ../.. && uv run python tools/rounds.py check cad/eyes)
(cd ../.. && uv run python tools/rounds.py round cad/eyes 0)
```
