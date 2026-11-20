# legs · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**jenscolt's leg, left and right, as two parametric build123d solids per side: leg-blade (L_leg1) and leg-arm (L_leg2), the right ones (leg-blade-r, leg-arm-r) the same model mirrored about x = 35.45 by a side parameter; the blade's skin from a 5-point spine and 6 control sections (50 numbers), the arm's neck lofted along its own 5-point spine with the hub rigid at its start, so both bend onto N0's leg path by their spines alone (--edit, and leg() for N1); nothing moves.**

Level N1 · purpose: jenscolt's leg (left and right) as parameters: the blade's skin from a spine and a few control sections, so it bends onto N0's leg path by its spine alone; the right leg is the left one mirrored. Pilot (2026-11-20) adopted as the method; fidelity at the default. · pass: leg-blade within the default fidelity (tools/mesh_ref.py) of L_leg1 both ways with its skin from ≤ 60 numbers; build.py --edit bends it onto N0's right-front blade curve (spine within 0.5 mm of it) and makes the length +10 % and bow +3 mm variants, every one a valid closed solid; the judge scores ≥ 0.70 against the mesh render

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| leg-blade | the leg's outer blade: a skin lofted along a 5-point spine from 6 control sections with rounded ends, the arm's socket, the side seam grooves and the eye boss carried in the spine's frame | a separate jenscolt mesh (L_leg1); N1 form part, not printed | 19 | not printed (N1 form part) |
| leg-arm | the leg's arm: hub plate with axle hole, ring and gears (rigid at the spine's start, the crank pin), a ringed neck lofted along a 5-point spine (pin, neck root, pivot, middle, knee) flaring into the top block, the ringed tab tube and the static-leg tab | a separate jenscolt mesh (L_leg2); N1 form part, not printed | 7 | not printed (N1 form part) |
| leg-blade-r | the right leg's blade: leg-blade mirrored about x = 35.45 (side 'R'), never a second model | a separate jenscolt mesh (R_leg1); N1 form part, not printed | 19 | not printed (N1 form part) |
| leg-arm-r | the right leg's arm: leg-arm mirrored about x = 35.45 (side 'R'), never a second model | a separate jenscolt mesh (R_leg2); N1 form part, not printed | 7 | not printed (N1 form part) |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | leg-arm | None | none |  | exported in jenscolt's frame |
| 2 | leg-blade | +z | none |  | the arm's top block sits in the blade's socket, both in jenscolt's frame |
| 3 | leg-arm-r | None | none |  | exported in jenscolt's frame, mirror of leg-arm |
| 4 | leg-blade-r | +z | none |  | the right arm's top block sits in the right blade's socket |

## Alternatives

- **blade skin parameters**: a spine (cubic spline through 5 points) + K control sections, a cubic spline through each number along it / v1's 26 planar sections on a straight axis (≈ 270 numbers) / one section swept along the spine with width / thickness laws (polynomials) → **a spine (cubic spline through 5 points) + K control sections, a cubic spline through each number along it**, ≤ 60 readable numbers (spine points, widths, thicknesses, roundness) that bend with the spine; v1's table cannot bend and a single swept section loses the tip and the ridge's change along the blade
- **where the features go on a new spine**: carried in the spine's frame at the same arc-length fraction (n1 warp's convention) / rigid at the same distance from the top end → **carried in the spine's frame at the same arc-length fraction (n1 warp's convention)**, the sections sit at arc-length fractions too, so socket and eye stay on the skin when the length changes (at a fixed distance the eye floated off the stretched N0 blade)
- **arm body**: hub rigid at the start of a 5-point spine, neck lofted along it, rings / flare / block / boss placed by z of the original spine mapped knot to knot / v1: 2.5D plate + neck loft on horizontal stations (cannot bend) / one loft along a branched spine → **hub rigid at the start of a 5-point spine, neck lofted along it, rings / flare / block / boss placed by z of the original spine mapped knot to knot**, N1 lays the arm on N0's inner arm + upper path (crank pin -> pivot -> knee) by its spine alone; mapping knot to knot keeps the pivot on N0's pivot (n1's breakpoints); the hub's flat faces stay exact at 45 degrees
- **right leg**: side parameter: the left model mirrored about x = 35.45 (or, on given spines, about the leg plane) / a second model with its own numbers → **side parameter: the left model mirrored about x = 35.45 (or, on given spines, about the leg plane)**, jenscolt's R meshes are the L ones mirrored about x = 35.45 to 0.0000 mm (probe); one model keeps both sides equal under every edit

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| a1 | four parts, leg-blade (jenscolt L_leg1), leg-arm (L_leg2), leg-blade-r (R_leg1), leg-arm-r (R_leg2), each one valid closed build123d solid, exported by build.py to out/leg-blade.*, out/leg-arm.*, out/leg-blade-r.*, out/leg-arm-r.* (STL and STEP) in jenscolt's own frame at 100 % | measure |  | must |
| a2 | every shape parameter at the top of build.py with its source (a mesh_ref section or measurement); the shape comes from parameters, not from the mesh | morante |  | must |
| a3 | build.py --sweep rebuilds both sides at S 0.65 and the left parts with blade thickness and arm section scale at 0.8x and 1.2x, and prints FAIL for any variant that is not one valid closed solid | measure |  | must |
| a4 | the arm's visible details (hub hole, gear relief, the rings, the static-leg tab) present as shape; fine relief may be simplified if fidelity still passes | visual |  | must |
| a5 | fidelity of leg-blade to L_leg1 within the default (tools/mesh_ref.py) both ways, its skin from ≤ 60 numbers | measure |  | must |
| a6 | fidelity of leg-arm to L_leg2 within the default (tools/mesh_ref.py) both ways | measure |  | must |
| a7 | leg-blade's skin from BLADE_SPINE (≤ 5 points) and BLADE_CTRL (≤ 8 sections), ≤ 60 numbers in all; build.py prints FAIL past any limit | measure |  | must |
| a8 | build.py --edit: (a) the blade on N0's right-front blade curve at its S, spine within 0.5 mm of it, (b) length +10 %, (c) bow +3 mm, (d) the arm on N0's right-front inner arm + upper leg curve at its S; each one valid closed solid in out/edit-*.stl, and images/edit-demo.png; FAIL printed otherwise | measure |  | must |
| a9 | socket, eye and seam grooves carried in the blade spine's frame, the arm's hub, rings, flare and block in the arm spine's frame, so they follow a bend (edit-demo.png) | visual |  | must |
| a10 | datasheet.md: blade p95 / max with 4, 6, 8 control sections and v1's 26, measured with tools/mesh_ref.py compare; the fewest that pass are used | morante |  | must |
| a11 | fidelity of leg-blade-r to R_leg1 within the default both ways | measure |  | must |
| a12 | fidelity of leg-arm-r to R_leg2 within the default both ways | measure |  | must |
| a13 | the arm's neck lofted along ARM_SPINE (≤ 5 points), the hub rigid at its start, rings / flare / block / boss at positions mapped along it; --edit (d) lays it on N0's inner arm + upper curve as one valid solid | measure |  | must |
| a14 | leg(side, blade_spine, arm_spine, S, across) -> (blade, arm) solids in build.py, a pure memoised function of its inputs, documented in datasheet.md for N1 | morante |  | must |
| n1 | not build.py never reads an STL or uses trimesh: the meshes are read only by the gates and by the designer's probes (scratchpad) | measure |  | must |
| n2 | not no warp or morph of mesh vertices | measure |  | must |
| m1 | leg-blade's skin from a spine curve (BLADE_SPINE, ≤ 5 control points) and ≤ 8 control sections interpolated along it (≤ 60 numbers in all for the skin); the seam grooves, socket and eye placed relative to the spine so they follow a bend | measure |  | must |
| m2 | leg-arm's neck on a spine of ≤ 5 points (hub, gears and tab rigid at its start), so it bends onto N0's inner and upper leg path; same fidelity gate (Morante, 2026-11-20: N1 bends both parts) | measure |  | must |
| m3 | build.py --edit writes out/edit-*.stl and images/edit-demo.png: (a) the blade bent onto N0's right-front blade curve (cad/mockup/n0.py leg_shape with P0, imported, never copied) in N0's frame at its S, (b) length +10 %, (c) bow +3 mm; prints FAIL for any variant that is not one valid closed solid or, for (a), whose spine is more than 0.5 mm from N0's curve | measure |  | must |
| m4 | build.py --sweep as in v1 (S 0.65, thickness and arm section 0.8x / 1.2x) | measure |  | must |
| m5 | a fidelity-vs-sections table in datasheet.md: blade p95/max with 4, 6, 8 control sections (and v1's 26), so Morante sees the trade-off | morante |  | must |
| m6 | the right leg (leg-blade-r, leg-arm-r) from the same model by a mirror parameter, never a second model; its fidelity against jenscolt's R_leg1 / R_leg2 | measure |  | must |
| p1 | leg-blade within the default fidelity (tools/mesh_ref.py) of L_leg1 both ways with its skin from ≤ 60 numbers; build.py --edit bends it onto N0's right-front blade curve (spine within 0.5 mm of it) and makes the length +10 % and bow +3 mm variants, every one a valid closed solid; the judge scores ≥ 0.70 against the mesh render | morante |  | must |

## Diagram

<img src="BLADE_SPINE (5 pts) + BLADE_CTRL (6 sections) --loft--> leg-blade skin; socket, eye, grooves carried in the spine's frame; ARM_SPINE (5 pts: pin, root, pivot, middle, knee): hub rigid at the pin, neck lofted along it, rings / flare / block carried; leg(side, blade_spine, arm_spine, S) -> (blade, arm); side R = mirror (x = 35.45)" alt="Plan diagram">
