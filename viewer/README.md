# Whole-robot viewer

A 3D view of the whole robot as it stands today: the shells, the 8 legs over the 24 crank poses, the interior and
the open problems of the fit check, each marked where it happens.

**Open it:** double-click [`index.html`](index.html). It works from disk in Safari, Firefox and Chrome, with no
server. Everything it needs is in this folder. Only the fonts come from Google Fonts, and without a connection the
page uses the system fonts. The same page is published as the claude.ai artifact *Spider-Bot Replica Viewer*.

## What it shows

| In the viewer | Where it comes from | State |
|---|---|---|
| Base and body | `cad/base/out/base.stl`, `cad/body/out/body.stl`, moved into the robot frame at S | As those designs are; the plan's windows, pockets and tabs are cut by `cad/robot/shells.py`, which does not build yet |
| Legs | The real `cad/legs` arm and blade (the fit check's mesh cache), carried per crank pose as `cad/motion.py` does; end tube and root ball as in the fit check | Real parts |
| Cranks | Journals, webs and pins from `cad/robot/fitcheck/check.py`, per pose | Plan |
| Interior | The boxes and cylinders `check.py` samples each part from (one node per part; a convex hull where a part is not made of whole primitives) | Plan, not modelled yet |
| Open problems | Every row of `cad/robot/fitcheck/out/rows.json` under its need by more than 0.05 mm: FAIL in red, at tolerance in amber. The point is where one part sits deepest in the other; for an assembly path, a red ghost shows the part where it fails | From the last fit check run |

## Update it

After a fit check run or a changed part:

```bash
.venv/bin/python viewer/src/export.py
```

It runs the parts half of `check.py` (≈ 10 s with its caches, none of the pair checks) and rewrites
`robot-data.js` and `index.html`. When only `src/page.html` changed, `--page` rewrites `index.html` alone. Then
publish the artifact again (page `src/page.html`, with `robot-data.js` and `three-r147.js` beside it).

A new problem without plain words in `src/page.html` (`TEXT`) is shown with its part names; add its title and
description there.

## Files

| File | What it is |
|---|---|
| `index.html` | The page to open (generated: edit `src/page.html`) |
| `robot-data.js` | The robot as a GLB (base64) and the poses and conflicts as JSON, both as globals (generated) |
| `three-r147.js` | three.js r147 with OrbitControls, GLTFLoader, RoomEnvironment and BufferGeometryUtils (MIT) |
| `src/page.html` | The page itself: layout, texts, colours, the 3D scene |
| `src/export.py` | Writes `robot-data.js` and `index.html` |
| `src/vendor.sh` | Downloads `three-r147.js` again |

three.js r147 is the last release with classic scripts. Pages that load ES modules do not open from `file://` in
Firefox and Chrome. The page turns on r147's physical lights and sRGB colours, so it looks as it would with a
current release.
