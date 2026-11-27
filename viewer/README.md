# Whole-robot viewer

A 3D view of the whole robot as the round r00 builds it: every part from its real STL, the moving parts placed per crank pose as `cad/robot/verify.py` places them, and the warnings of cad_verify's report, each marked where it happens. The page is in Spanish.

**Open it:** online at **https://morante-robotics.github.io/spider-bot-replica/**, or double-click
[`index.html`](index.html) in a clone. It works from disk in Safari, Firefox and Chrome, with no server. Everything it needs is in this folder. Only the fonts come from Google Fonts, and without a connection the
page uses the system fonts.

## What it shows

| In the viewer | Where it comes from | State |
|---|---|---|
| Shells: base (blue), body (red) | `cad/robot/out/base.stl`, `body.stl` | Real parts |
| Legs: the 8 legs | `out/leg-0..7.stl`, carried per pose by `verify.poses(k)` | Real parts |
| Drive: spine, 4 cranks, 3 idlers, transfer, pinion, journal cap, motor U, transfer cheek | `out/*.stl`; cranks, idlers, transfer and pinion move per pose | Real parts, one colour each |
| Power: cell holder, cell lid | `out/cell-holder.stl`, `cell-lid.stl` | Real parts |
| Bought (green): N10 motor, AG13 cells, springs, nickel strip, JST-XH, switch, LEDs, screws and axles | `out/*.stl` of the bought parts; the motor and the screws as the spec models them | Real or as modelled in the spec |
| Warnings | The FAIL rows and the fit-relevant WARN rows of `cad/robot/verify-result.txt` (coarse gaps, joints «not measured yet»). The pin is where the two parts come closest at pose 0 | From the last cad_verify run (S 1.0, 2026-11-27: 10 FAIL, all on the legs' joint, parked) |

The part list has a toggle per group (show, hide, open the list) and a checkbox per part. «See inside» hides the shells; «See-through shells» keeps them as ghosts. The fit check's rows are no longer shown: it is the pre-CAD planner, not a gate.

## Update it

After a new build or a new cad_verify run (`verify-result.txt` is read as it stands):

```bash
.venv/bin/python viewer/src/export.py
```

It imports `cad/robot/verify.py` (PARTS and `poses(k)`, nothing copied), reads the cached STLs and the report, and rewrites `robot-data.js` and `index.html` (≈ 5 s, ≈ 3 MB). Labels are in English (the public repo); `LABELS["es"]` stays for the workshop kit. It runs no check. When only `src/page.html` changed, `--page` rewrites `index.html` alone. Commit the regenerated files with the change that caused them. A push to `main` that touches `viewer/` publishes it again on GitHub Pages (`.github/workflows/viewer.yml`, a minute or two).

A warning without plain words is shown with its part names; add its Spanish title and description to `words()` in `src/page.html`.

## Files

| File | What it is |
|---|---|
| `index.html` | The page to open (generated: edit `src/page.html`) |
| `robot-data.js` | The robot as a GLB (base64) and the poses and warnings as JSON, both as globals (generated) |
| `turntable.gif` | The preview at the top of the repo's README: one turn of the camera while the legs walk (see below) |
| `three-r147.js` | three.js r147 with OrbitControls, GLTFLoader, RoomEnvironment and BufferGeometryUtils (MIT) |
| `src/page.html` | The page itself: layout, texts, colours, the 3D scene |
| `src/export.py` | Writes `robot-data.js` and `index.html` |
| `src/vendor.sh` | Downloads `three-r147.js` again |

three.js r147 is the last release with classic scripts. Pages that load ES modules do not open from `file://` in
Firefox and Chrome. The page turns on r147's physical lights and sRGB colours, so it looks as it would with a
current release.

## The preview GIF

`turntable.gif` is made from the viewer itself: with the page open, the camera goes once round the robot at the
home view's height, 1.25 × the home distance, with the sun turning with it (72 frames, 5° apart) while the crank steps one pose per frame in the walking direction, 23, 22, … (three walking cycles; the poses run backward: as k rises the robot would walk backward),
each frame saved from the canvas on the page's background colour (640 × 440). The frames become the GIF with
ffmpeg (12 fps, 480 px wide, 128 colours). Make it again when the robot changes enough to look different.
