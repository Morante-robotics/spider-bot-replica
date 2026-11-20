# legs

jenscolt's leg (blade `L_leg1`, arm `L_leg2`; the right ones `R_leg1`, `R_leg2` the same model mirrored) as parametric
build123d code instead of meshes. Both parts lie on spines, so N1 bends them onto the approved leg path ([`../motion.py`](../motion.py)) with `leg()`. Level N1 (form only, not printed).

**License:** derived from jenscolt's [Spidey-Bot](https://www.thingiverse.com/thing:5196618), so [CC BY-NC-SA](../carcass-jenscolt/LICENSE.txt): non-commercial, share-alike, with credit to jenscolt; unlike the rest of the repo (see [`carcass-jenscolt/README.md`](../carcass-jenscolt/README.md)).

- `spec.json`: the request (the coordinator's). `plan.json` → `design-plan.md`: the plan.
- `build.py`: the four parts into `out/` in jenscolt's frame; `--sweep` checks the parameter variants; `--edit` bends the blade (N0's leg curve, +10 % length, +3 mm bow) and the arm (N0's inner arm + upper leg) into `out/edit-*.stl` and `images/edit-demo.png`; `--part` one part; `leg(side, blade_spine, arm_spine, S)` is N1's entry point (datasheet.md).
- `datasheet.md`: numbers, fidelity, simplifications.

```bash
../../.venv/bin/python build.py [--sweep] [--edit] [--part leg-arm] [--fine]
uv run python tools/rounds.py check cad/legs      # from the repo root: build + fidelity gates
```
