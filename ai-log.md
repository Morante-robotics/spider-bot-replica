# Spider-Bot · AI log

Where AI (Claude) helped with the build, what it was asked, and what was checked by hand. Rules: every AI suggestion
needs a measurable test; designs are checked in Onshape (animation) before printing; soldering, batteries and
assembly are done by me.

| Date | Phase | Task | AI did | Checked by |
|---|---|---|---|---|
| 2026-11-08 | 2 · CAD | Carcass base model | Searched for faithful models and compared licenses; measured the 9 STLs and checked them for mesh errors; wrote [`tools/stl_preview.py`](tools/stl_preview.py) and [`tools/stl_turntable.py`](tools/stl_turntable.py) for the previews; [`tools/assemble_jenscolt.py`](tools/assemble_jenscolt.py) to assemble the full robot (eye sockets measured from the mesh, leg layout approximate) | Opened in Bambu Studio: imports, same mesh errors reported. Leg count (8) from the author's photos; exact leg layout not checked |
| 2026-11-09 | 2 · CAD | Motor, battery holder and print scale | Collected motor and holder sizes from shop listings; worked out voltage for 2×AA / 4×AAA against the N20 and the LEDs; wrote [`tools/fit_check.py`](tools/fit_check.py) to find the free space in the body and the smallest scale for each part | Pending: holder drawing checked when bought; fit checked again in Onshape with the mechanism |
| 2026-11-09 | 2 · CAD | Mesh repair | Diagnosed the mesh errors; wrote [`tools/repair_stl.py`](tools/repair_stl.py); rejected MeshFix after measuring it removed a 1.5 mm relief | Bambu Studio `--info`: `manifold = yes` for the 5 repaired parts; max deviation from the original 0.01 mm |
| 2026-11-09 | 3 · Mechanisms | Leg simulator and comparison | Found Klann's patent bar lengths and Jansen's numbers; wrote [`sim/legs.py`](sim/legs.py) (circle-intersection solver, Grashof check, gait metrics); random search for the toy leg; caught and fixed two errors of its own (Jansen triangle sides swapped; toy stance measured off the ground) | Klann and Jansen foot paths match the published shapes (DIY Walkers). Pending: animated leg in Onshape and a printed leg turned by hand |
