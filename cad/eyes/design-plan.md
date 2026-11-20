# eyes · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**jenscolt's three dome cups (large eye, small eye, front sensor) as one revolved parametric cup with three parameter sets, each in its reference frame; nothing moves.**

Level N1 · purpose: jenscolt's eye domes as parameters: the large eye, the small eye and the front sensor (cups made of primitives), in their reference frames · pass: the default fidelity gate passes for each part, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the meshes

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| eye | the large eye dome (spideybot_eye.stl): a hollow cup, apex at low Y, open at high Y | a separate jenscolt mesh, far from the others; N1 form part, not printed | 19 | not printed (N1 form part) |
| small-eye | the small eye dome (spideybot_small_eye.stl), same cup with its own numbers | a separate jenscolt mesh, far from the others; N1 form part, not printed | 1 | not printed (N1 form part) |
| sensor | the front sensor dome (spideybot_sensor.stl), same cup with its own numbers | a separate jenscolt mesh, far from the others; N1 form part, not printed | 1 | not printed (N1 form part) |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | eye | None | none |  | exported in jenscolt's frame |
| 2 | small-eye | None | none |  | exported in jenscolt's frame |
| 3 | sensor | None | none |  | exported in jenscolt's frame |

## Alternatives

- **cup profile**: revolved profile: flat apex, elliptic dome, straight wall / sphere cap minus an inner sphere → **revolved profile: flat apex, elliptic dome, straight wall**, the meshes have a flat apex and a straight wall that a sphere cap cannot give; 5 numbers per cup

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| a1 | each part is within p95 1.0 mm and max 2.5 mm of its reference, both ways | measure |  | must |
| a2 | the small eye is within the same fidelity | measure |  | must |
| a3 | the sensor is within the same fidelity | measure |  | must |
| a4 | every sweep variant is one valid closed solid | measure |  | must |
| a5 | build.py reads no mesh | measure |  | must |
| m1 | one parametric cup (radius, depth, wall, rim) used by all three parts, each with its own numbers | measure |  | must |
| n1 | not: build.py reads a mesh: the reference meshes are read only by the gates and the designer's probes | measure |  | must |
| p1 | the default fidelity gate passes for each part, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the meshes | morante |  | must |
