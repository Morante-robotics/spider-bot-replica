# body · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**jenscolt's body (the top shell) as one parametric build123d solid in jenscolt's frame: an outer skin lofted from 8 superellipse control sections up the vertical spine, a wall cut by an inner skin derived from the same table, and every visible detail a named feature placed on it; nothing moves.**

Level N1 · purpose: jenscolt's body (the top shell) rebuilt as parameters, every visible detail (eye sockets and rings, front grille, panels, rear features, rim); outer form and wall thickness as separate parameters, so scale and wall change independently. His inside is not kept beyond the shell wall. · pass: the default fidelity gate passes, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the mesh

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| body | the spider's top shell: skin, wall open at the rim, eye block with the two big eye bores and knurled rings, nose plate, two small eye tubes, chin arch and bridge, side scoops, side panel lines, rear lip, rear tab, two screw bosses | a separate jenscolt mesh (spideybot_body); N1 form part, not printed | 110 | not printed (N1 form part) |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | body | None | none |  | exported in jenscolt's frame |

## Alternatives

- **outer skin parameters**: a loft of 8 horizontal superellipse control sections (half-width, front / back half-lengths, front / back exponents) up the vertical spine x = CX, PCHIP-interpolated in z / a table of measured sections (a mesh copy) → **a loft of 8 horizontal superellipse control sections (half-width, front / back half-lengths, front / back exponents) up the vertical spine x = CX, PCHIP-interpolated in z**, 40 readable numbers that a person can change; a measured table cannot be edited
- **wall**: an OCCT offset of the lofted skin / an inner skin lofted from the same control table, each meridian eroded by the wall, cut from the outer one → **an inner skin lofted from the same control table, each meridian eroded by the wall, cut from the outer one**, the offset of the loft ran over 4 min without finishing; the inner loft takes under a second and keeps WALL one parameter

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| a1 | one valid closed build123d solid, exported by build.py to out/body.stl and out/body.step in jenscolt's frame at 100 % | measure |  | must |
| a2 | build.py --sweep rebuilds at S 0.65 and with the wall and the section scale at 0.8x and 1.2x, and prints FAIL for any variant that is not one valid closed solid | measure |  | must |
| a3 | fidelity of the body to spideybot_body.stl as a viewer above and around sees it: p95 ≤ 2.0 mm and max ≤ 4.0 mm both ways (the default) | measure |  | must |
| a4 | the visible details present as shape: big eye sockets with knurled rings, small eyes, nose plate, chin arch, side scoops, panel lines, rear lip and tab | visual |  | must |
| a5 | every shape parameter at the top of build.py with its source (a probe or a section); the shape comes from parameters, not from the mesh | morante |  | must |
| m1 | outer form and wall thickness separate parameters (wall as an inward offset of the skin) | measure |  | must |
| m2 | every visible detail a named feature placed on the skin: eye sockets and rings, front grille, panel lines, rear features | visual |  | must |
| n1 | not build.py reads a mesh: the reference meshes are read only by the gates and the designer's probes | measure |  | must |
| p1 | the default fidelity gate passes, the sweep's variants are valid solids, and the judge scores ≥ 0.70 against the mesh | morante |  | must |

## Diagram

<img src="SKIN_CTRL (8 sections, 40 numbers) --loft--> outer skin; same table eroded by WALL --loft--> inner skin; outer - inner = shell open at Z_RIM; + eye block, rings, nose, small eyes, bridge, scoops, rear lip, tab, bosses; - bores, chin arch, boss holes, panel lines" alt="Plan diagram">
