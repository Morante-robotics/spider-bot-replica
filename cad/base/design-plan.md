# base · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**jenscolt's base as one parametric bowl: skin, wall, rim and the front leg windows; his inside is left out (N2 puts our mechanism there).**

Level N1 · purpose: jenscolt's base as parameters: only the outer bowl, its rim and the leg notches (Morante, 2026-11-20); his inside (posts, motor and light mounts, static-leg tabs) is left out, our mechanism goes there at N2. Reference: the derived bowl (derive_bowl.py). · pass: the default fidelity gate passes, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the mesh

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| base | the bowl the body and mechanism sit in, ground part | the only part of this design | 9 | bowl up, foot on the bed |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | base | None | hand |  | stands on its foot, open side up |

## Alternatives

- **how the wall is made**: outer loft minus inner loft / outer and inner skins sewn with a top ring → **outer and inner skins sewn with a top ring**, the cut of two near-parallel lofts took 40 s and came out invalid; the sewn shell builds in 6 s

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| a1 | the bowl is within the default fidelity limits of the reference both ways | measure |  | must |
| a2 | every sweep variant (S 0.65, wall and section 0.8x / 1.2x) is one valid closed solid | measure |  | must |
| a3 | build.py reads no mesh | measure |  | must |
| a4 | the bowl, its rim and the front windows look like jenscolt's base | visual |  | must |
| m1 | bowl skin and wall thickness separate parameters | visual |  | must |
| m2 | the rim notches (leg windows) as named features, one parameter set mirrored left/right | visual |  | must |
| n1 | not: build.py reads a mesh: the reference meshes are read only by the gates and the designer's probes | visual |  | must |
| p1 | the default fidelity gate passes, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the mesh | morante |  | must |
