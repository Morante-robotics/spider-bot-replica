# Chassis datasheet

The one page an agent reads first. It points into the long files at the section a task needs and never repeats a
number that has a home in code: datums and interfaces in [`../robot.py`](../robot.py) (`python3 ../robot.py` prints
them), clearances in [`../fits.py`](../fits.py), part parameters at the top of each build file.

## Status (2026-11-16)

| Part | Built by | Spec | Last full check |
|---|---|---|---|
| A: drive module, cap, motor clamp, pinion, idler 3 v2, pin keeper, bench tools | `build.py` | `verify.py` | `verify-result.txt`: PASS, 39 warnings |
| B1: shell `chassis`, `crank-cover` | `shell.py` (stages cached in `out/.cache/`) | `verify_b1.py` (interim) | `verify-result-b1.txt`: PASS, 88 warnings |
| Front block v2 | `front_block.py` | `verify_fb.py` (interim) | `verify-result-fb.txt`: PASS, 42 warnings |
| B rest (body v2, cradle, ballast frame, eyes pocket), C, D | not started | | |

The three specs merge into `verify.py` in Part C (the whole-robot check); until then `verify_b1.py` and `verify_fb.py`
import Part A's spec and add their parts.

## Where to read, by task

| Task | Read | Section |
|---|---|---|
| Part A part or fit | `README.md` | Parts, Hardware, I7 table |
| Part A decision or joint | `design-plan.md` | `grep -n '^## '` |
| Shell, band, lips, bosses, crank cover | `design-plan-b.md` | Part list, Joint table, Fits, Assembly sequence |
| Shell mass | `design-plan-b.md` | Shell mass |
| Open questions | `design-plan-b.md` | Open questions for Morante |
| Front block | `front_block.py` docstring | |
| Interfaces I1–I12 | `../robot.py` | `INTERFACES` |

Figure and probe scripts (`plan_figure.py`, `plan_b_figure.py`, `plan_b_rear_section.py`, `part_a_figures.py`,
`mass_estimate.py`) are run only at the end of an approved step; no need to read them for a change.

## Light geometry

- The body's scan is 102k triangles: never cut or check against `R.carcass("body")`. Use `R.carcass_proxy("body")`
  (31k, within 0.2 mm, cached) or `R.carcass_envelope(...)` (boxes per 2 mm slab). The base scan (7.5k) is light;
  its proxy is 4k.
- `shell.py --lite` (or `SHELL_LITE=1`) while trying a fix; the full build once at the end.
- STLs are exported coarse while iterating; `build.py --fine` (or `CAD_FINE=1`) for the STL that is printed.

## Commands (from this folder)

```bash
../../.venv/bin/python build.py --part cap                                        # one Part A part
../../.venv/bin/python ../../tools/cad_verify.py verify.py --smoke --only cap      # after every fix (seconds)
VERIFY_STEP=30 ../../.venv/bin/python ../../tools/cad_verify.py verify.py --quick --only cap   # a moving part changed
../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify  # once, at the end
SHELL_LITE=1 ../../.venv/bin/python shell.py                                      # B1 while trying a fix
```
