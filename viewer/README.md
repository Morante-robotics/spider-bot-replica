# Whole-robot viewer

A 3D view of the whole robot as it stands today: the shells, the 8 legs over the 24 crank poses, the interior and
the open problems of the fit check, each marked where it happens.

**Open it:** online at **https://morante-robotics.github.io/spider-bot-replica/**, or double-click
[`index.html`](index.html) in a clone. It works from disk in Safari, Firefox and Chrome, with no server. Everything it needs is in this folder. Only the fonts come from Google Fonts, and without a connection the
page uses the system fonts.

## What it shows

| In the viewer | Where it comes from | State |
|---|---|---|
| Base and body | `cad/base/out/base.stl`, `cad/body/out/body.stl`, moved into the robot frame at S | As those designs are; the plan's windows, pockets and tabs are cut by `cad/robot/shells.py`, which does not build yet |
| Legs | The 8 printed legs, `cad/robot/out/leg-0..7.stl` (end tube with the snap bead, root ball), carried per crank pose by `shells.leg_frame` as `cad/robot/verify.py` does | Real parts |
| Cranks | Journals, webs and pins from `cad/robot/fitcheck/check.py`, per pose | Plan |
| Interior | The boxes and cylinders `check.py` samples each part from (one node per part; a convex hull where a part is not made of whole primitives) | Plan, not modelled yet |
| Open problems | Every row of `cad/robot/fitcheck/out/rows.json` under its need by more than 0.05 mm: FAIL in red, at tolerance in amber. The point is where one part sits deepest in the other; for an assembly path, a red ghost shows the part where it fails | From the last fit check run |

## Update it

After a fit check run or a changed part:

```bash
.venv/bin/python viewer/src/export.py
```

It runs the parts half of `check.py` (≈ 10 s with its caches, none of the pair checks) and rewrites
`robot-data.js` and `index.html`. When only `src/page.html` changed, `--page` rewrites `index.html` alone. Commit
the regenerated files with the change that caused them. A push to `main` that touches `viewer/` publishes it again
on GitHub Pages (`.github/workflows/viewer.yml`, a minute or two).

A new problem without plain words in `src/page.html` (`TEXT`) is shown with its part names; add its title and
description there.

## Files

| File | What it is |
|---|---|
| `index.html` | The page to open (generated: edit `src/page.html`) |
| `robot-data.js` | The robot as a GLB (base64) and the poses and conflicts as JSON, both as globals (generated) |
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
home view's height (72 frames, 5° apart) while the crank advances one pose per frame (three walking cycles),
each frame saved from the canvas on the page's background colour (640 × 440). The frames become the GIF with
ffmpeg (12 fps, 480 px wide, 128 colours). Make it again when the robot changes enough to look different.
