# Spider-Bot · AI log

Where AI (Claude) helped with the build, what it was asked, and what was checked by hand. Rules: every AI suggestion
needs a measurable test; designs are checked in Onshape (animation) before printing; soldering, batteries and
assembly are done by me.

| Date | Phase | Task | AI did | Checked by |
|---|---|---|---|---|
| 2026-11-08 | 2 · CAD | Carcass base model | Searched for faithful models and compared licenses; measured the 9 STLs and checked them for mesh errors; wrote [`tools/stl_preview.py`](tools/stl_preview.py) and [`tools/stl_turntable.py`](tools/stl_turntable.py) for the previews | Opened in Bambu Studio: imports, same mesh errors reported |
