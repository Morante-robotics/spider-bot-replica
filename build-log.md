# Spider-Bot · Build log

The story of the build, step by step, written so that anyone can follow it and repeat it. Every entry opens with a
short **In short** box; read only those boxes and you have the whole story. Below each box come the steps, the
results with their figures, and the decisions taken. Commands and full data tables are folded under
**How to reproduce**. Entries are grouped by topic, oldest first; what is left to do and a glossary are at the
end.

<table>
<tr>
<td width="50%"><img src="cad/carcass-jenscolt/images/jenscolt-photo-1.jpg" alt="Spidey-Bot by jenscolt, three-quarter view"></td>
<td width="50%"><img src="cad/carcass-jenscolt/images/jenscolt-photo-2.jpg" alt="Spidey-Bot by jenscolt, eyes lit"></td>
</tr>
<tr>
<td colspan="2"><em>The goal. <a href="https://www.thingiverse.com/thing:5196618">Spidey-Bot by jenscolt</a>, the static
display model this replica starts from (photos: jenscolt, CC BY-NC-SA). Ours keeps its look, and adds legs that
walk, driven by one motor, and lit eyes.</em></td>
</tr>
</table>

## Contents

The robot's story in three parts, then what is left to do and a glossary.

1. **[Workshop](build-log/1-workshop.md#workshop)**: getting the printer ready.
   - [Printer calibration](build-log/1-workshop.md#printer-calibration) · 2026-10 · ✅ done
   - [First print: purge waste bin](build-log/1-workshop.md#first-print-purge-waste-bin) · 2026-11-09 · ✅ done
2. **[Carcass](build-log/2-carcass.md#carcass)**: the robot's outer shell, and what has to fit inside it.
   - [Carcass base model](build-log/2-carcass.md#carcass-base-model) · 2026-11-08 · ✅ done
   - [Motor, battery holder and print scale](build-log/2-carcass.md#motor-battery-holder-and-print-scale) · 2026-11-09 · ✅ 120 %
   - [Mesh repair](build-log/2-carcass.md#mesh-repair) · 2026-11-09 · ✅ done
3. **[Legs and drive](build-log/3-legs-and-drive.md#legs-and-drive)**: how one motor moves eight legs.
   - [Leg simulator and comparison](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) · 2026-11-09 · ✅ toy leg chosen
   - [Toy leg in 3D](build-log/3-legs-and-drive.md#toy-leg-in-3d) · 2026-11-09 · ✅ lateral axle
   - [Toy leg on one crankshaft](build-log/3-legs-and-drive.md#toy-leg-on-one-crankshaft) · 2026-11-09 · ↩️ reversed
   - [Crankshaft against real parts](build-log/3-legs-and-drive.md#crankshaft-against-real-parts) · 2026-11-09 · ❌ one crankshaft ruled out
   - [Two side crankshafts](build-log/3-legs-and-drive.md#two-side-crankshafts) · 2026-11-09 · ❌ ruled out
   - [Four lateral crankshafts](build-log/3-legs-and-drive.md#four-lateral-crankshafts) · 2026-11-09 · ✅ chosen
   - [Legs and drive in CAD](build-log/3-legs-and-drive.md#legs-and-drive-in-cad) · 2026-11-10 · ✅ done
   - [Onshape assembly](build-log/3-legs-and-drive.md#onshape-assembly) · 2026-11-10 · ✅ done
   - [Clearance test and test leg print plate](build-log/3-legs-and-drive.md#clearance-test-and-test-leg-print-plate) · 2026-11-10 · ✅ printed
   - [Test leg: first assembly and clearance result](build-log/3-legs-and-drive.md#test-leg-first-assembly-and-clearance-result) · 2026-11-11 · ✅ v2 designed
   - [Test leg v2: turning by hand](build-log/3-legs-and-drive.md#test-leg-v2-turning-by-hand) · 2026-11-11 · ✅ the leg turns
   - [Base v1 in CAD](build-log/3-legs-and-drive.md#base-v1-in-cad) · 2026-11-11 · ✅ printed, faults found
   - [Gear train test](build-log/3-legs-and-drive.md#gear-train-test) · 2026-11-11 · ✅ faults found
   - [Gear train v2 in CAD](build-log/3-legs-and-drive.md#gear-train-v2-in-cad) · 2026-11-11 · ✅ printed
   - [Gear train test v2: the cap](build-log/3-legs-and-drive.md#gear-train-test-v2-the-cap) · 2026-11-12 · ✅ the train turns
   - [Base v1: print and first fitting](build-log/3-legs-and-drive.md#base-v1-print-and-first-fitting) · 2026-11-13 · ✅ faults found
   - [Whole robot first: motor sizing and chassis plan](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) · 2026-11-14 · ✅ plan approved
   - [Chassis Part A: master model and drive module](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) · 2026-11-15 · ✅ modelled and checked
   - [Chassis Part B1, Part C check and the friction clutch](build-log/3-legs-and-drive.md#chassis-part-b1-part-c-check-and-the-friction-clutch) · 2026-11-16 · ✅ chassis checked, clutch modelled
   - [Chassis Part D: the weight review](build-log/3-legs-and-drive.md#chassis-part-d-the-weight-review) · 2026-11-17 · ✅ 459 g, looks parts next
   - [Chassis Part B2: the looks parts](build-log/3-legs-and-drive.md#chassis-part-b2-the-looks-parts) · 2026-11-17 · 🔄 whole robot passes in CAD; buying next
   - [Chassis Part E: the looks pass, planned and paused](build-log/3-legs-and-drive.md#chassis-part-e-the-looks-pass-planned-and-paused) · 2026-11-17 · 🔄 paused until the legs are rethought
   - [Legs v2: three plan rounds, paused](build-log/3-legs-and-drive.md#legs-v2-three-plan-rounds-paused) · 2026-11-17 · 🔄 paused, mass audit first
   - [Redesign: looks first](build-log/3-legs-and-drive.md#redesign-looks-first) · 2026-11-17 · 🔄 in progress
   - [N0 mock-up: the looks robot in simple shapes](build-log/3-legs-and-drive.md#n0-mock-up-the-looks-robot-in-simple-shapes) · 2026-11-18 · ✅ N0 look approved, N1 next
   - [N1 form: the real looking parts as light meshes](build-log/3-legs-and-drive.md#n1-form-the-real-looking-parts-as-light-meshes) · 2026-11-19 · ✅ N1 look approved, N2 next
   - [N2 rev 5: the inside does not fit at 65 %](build-log/3-legs-and-drive.md#n2-rev-5-the-inside-does-not-fit-at-65-) · 2026-11-19 · ↩️ restarted from scratch
   - [Meshes become parameters](build-log/3-legs-and-drive.md#meshes-become-parameters) · 2026-11-20 · ✅ parts converted
   - [Only the parametric parts measure](build-log/3-legs-and-drive.md#only-the-parametric-parts-measure) · 2026-11-20 · 🔄 N2 restarts on the parametric parts
4. **[Open items](#open-items)**: everything still to do.
5. **[Glossary](#glossary)**: the terms used in the entries.

Status: ✅ done · 🔄 in progress · ❌ ruled out · ↩️ reversed by a later entry.

## Open items

Everything still to do on the build, in one place. Each row links to the entry where it came up; when an item is
done, its row is removed and the entry that closes it says so. Plan-level tasks (study, purchases) are tracked
outside the repo.

Since 2026-11-17 the robot is redesigned **looks-first**: the toy (and jenscolt's model, legs included) is the
specification, only parts with their final looks are modelled, and the mechanism is fitted inside them. Sizing runs
from the bottom up: a smaller motor, the button cells that can feed it, and a robot as small as they allow. Work goes
through three levels of detail: a quick mock-up of the whole robot in simple shapes (seconds per change), the real
looking parts as light meshes with a motion check (minutes), and the print detail (fits, screws, the full check)
once, before printing. Everything before the redesign is in the
[archive tag](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17).

| Pending | Came up in | Phase |
|---|---|---|
| **First:** N2 round r00 of `cad/robot` at S 0.70, **in series, one heavy job at a time** (the Mac has 2 cores and 8 GB: two agents in parallel swapped it to a load of 22 and turned an 8-min fit check into 27–37 min). **State 2026-11-22 (session closed by Morante, nothing committed):** (1) The r00 interior designer found three holes in the old «0 failing of 327» before modelling: the 2 drive-unit M2 and the holder M2 only bit their own blocks/post (nothing held the drive unit or the holder), and the holder head sat 1.25 mm inside a cell (the check compared surface points only). (2) Re-plan (local, Morante's rules), `plan.json` validate PASS, `design-plan.md` regenerated: drive unit held by two lugs on idler axles 1+2 (its 2 M2 dropped; idler axles go in after it, on the bench); cell holder keeps its post and is screwed through a front tab into drive block 2 / ear 2; printed idler spacer sleeves Ø3.2 × 3.5; M2 pilot Ø1.6 assumed (coupon c2); pinion added as a printed part. (3) `fitcheck/` now tests solid-in-solid for hardware pairs and along assembly paths (`PSOLID`, `SOLIDS`/`EXTRA_SOLIDS` in `fit_samplers.py`; `POSTSPINE=1` restores the rejected post-in-spine geometry for comparison, not run yet). Result then: 3 failing of 320 (holder screw head 1.21 into the N10; the holder's +z path 2.79 into the N10, its tab lay under the motor; the cells' path through the springs), plus one the check did not see: the holder tab inside the drive unit's lower clamp (0.5 × 1.2 mm; printed pairs are compared by surface points only). **Fixed 2026-11-22 (local, coordinator):** drive ear 2 lowered to 1.0 (`EARH2`), so the tab and the M2 head sit under the N10 (0.20, needs 0.15) and the clamp (0.19); the holder and its M2 go in **before** the N10, which slides in over the tab and comes out along −x with the holder in place; the cells sit against the strip (spring compressed to SPR, they were centred) and the springs yield on the cells' path. `plan.json` updated, validate PASS. Fit check (19 min, alone): **0 failing, 4 at tolerance of 318**. Open: a solid test for printed pairs, so an overlap like the tab's is caught. The viewer is one fit check behind until the next ENTRY. (4) Shells: `cad/robot/shells.py`, `build.py`, `verify.py`, `views.py` written, never smoke-checked. `images/reference.png` written from the archive tag's `assemble_jenscolt.py`. The base build did not finish in 91 min. **2026-11-22, base build (Morante: A, then B, then C):** diagnosis: every boolean costs ~4 s + 0.02 s per tool face where the tool's planar faces meet the base's BSpline skin; a Compound of overlapping tools gave an invalid result. Done in `shells.py`: support-plane cutters (never smaller than the grown hull, ≤ 0.08 mm larger), per-leg cached cutters and stages, local-box booleans (A), relief cell 3 → 6 mm (B: pocket up to 0.4 mm and bulge up to 1.6 mm larger at a few points, bbox unchanged); in `cad/base/build.py` the 14 loft sections share one knot vector (C: skin poles 175×16 → 35×16, shape within 0.061 mm, base gates PASS). Cold 15.8 → 10.5 min, warm 7 s. **But** those results were wrong while «1 valid solid» (window of leg 2 not cut, leg 1 partly, pads of legs 0–2 partial). Now every cut and fuse is checked by volume (`checked()` in `shells.py`: removed = vol(part ∩ tool), 3 % or 5 mm³, GProp being ~1 % noisy on the skin). It found and fixed: the back-sheet pocket was never cut (its clip box was at y 52–82, the sheet is at y 22–26); a fuzzy value 1e-4 made OCC return 0 mm³ for window 1 (fuzzy 0 is right); two nested local pieces gave an inside-out one. Mirroring one half is not possible: the left legs run 12 poses out of phase, so each window's slide-off direction differs from its mirror's by design. Result: **every op matches its volume; base 3.50 cm³, 1 solid, valid**; cold 22.5 min (the checks triple the booleans), warm seconds (cached). Still open: the STL export fails («could not make it watertight»): 28 non-manifold edges near the windows/relief (regions touching along a line) and 40 open edges on the floor near (4, −3, 1); and the cold time (ideas: op on the whole base at fuzzy 0 first, local piece only on a mismatch; fuse each side's 4 windows into one tool: fusing two takes 0.4 s, cutting with it is exact). Then: build all shells and `cad_verify --smoke`. The leg end tube runs along the pin (x) with a double-cone flared bore (`FLARE_DEG` = pin swing + 1°); legs fused (`one()`). Not done: rear-tab snap rib, MEASURE, smoke. (5) `interior.py` / `interior_verify.py` do not exist yet. (6) The viewer [`viewer/`](viewer/) is current with this fit check (regenerated 03:11, after the 02:25 run; committed in `8c1ccf9`, `95d3f8d`); the `capstone-documenter` regenerates it in each ENTRY. Order for the next session: (a) base STL export (the 28 non-manifold + 40 open edges; locate them on the cached base BREP, `out/.cache/base_*.brep`) and the cold time (target ≤ 5 min; any edit to `shells.py` invalidates every cache, since the keys stamp the whole file) → (b) build all shells and `cad_verify verify.py --smoke` → (c) rerun the fit check alone (cad/base's skin changed ≤ 0.061 mm) and regenerate the viewer → (d) one designer models the interior from plan.json → `rounds.py check`, `round cad/robot 0`, the looks judge. Nothing of 2026-11-22 is committed: `check.py`, `plan.json`, `design-plan.md`, `cad/base/build.py`, this file, and the untracked `cad/robot/` shells files. Spent ≈ 520k tokens this session | [Only the parametric parts measure](build-log/3-legs-and-drive.md#only-the-parametric-parts-measure) | 3 |
| Body: the curved top panels and the chin grille, if Morante wants them later (a build takes 60–80 s) | [Meshes become parameters](build-log/3-legs-and-drive.md#meshes-become-parameters) | 3 |
| Buy the N10 (3 V, ≈ 100–150 rpm) and 6 × AG13, and measure it (body, shaft, mounting) to replace the mock-up's box at N2. Chosen bottom-up from the original Mini Spider-Bot (≈ 10 cm, 6 × AG13, walks on legs): the body held them at ≈ 60 % on jenscolt's mesh ([`sizing.py`](https://github.com/Morante-robotics/spider-bot-replica/blob/n2-on-meshes-2026-11-20/cad/mockup/sizing.py)); N2 sizes again | Redesign, looks first | 3 |
| Print detail, one batch of coupons, the workshop kit and the one robot | Redesign, looks first | 4 |
| Import the parts into Onshape as STEP and assemble them with mates | [Onshape assembly](build-log/3-legs-and-drive.md#onshape-assembly) | 3 |
| Count the hardware in the workshop (the **Have** column) | [Hardware](hardware.md) | 3 |
| Calibrate X-Y hole and contour compensation and save the standard settings as a Bambu Studio preset | [Standard settings](print/README.md#standard-settings) | 2 |
| Measure battery life | [Motor, battery holder…](build-log/2-carcass.md#motor-battery-holder-and-print-scale) | 4 |

[↑ Contents](#contents)

## Glossary

Terms used in the entries, in the order they first appear, with a link to that entry.

| Term | Meaning | First in |
|---|---|---|
| **STL / STEP** | 3D file formats: STL is a triangle mesh (for printing), STEP is exact geometry (for CAD). | [Carcass base model](build-log/2-carcass.md#carcass-base-model) |
| **Bambu Studio** | The printer's slicer: it turns a 3D model into printer instructions. | [Carcass base model](build-log/2-carcass.md#carcass-base-model) |
| **Clearance** | Free space left around a part: how much bigger a hole or a space is than the part in it. | [Motor, battery holder…](build-log/2-carcass.md#motor-battery-holder-and-print-scale) |
| **Watertight (manifold)** | A mesh with no holes or loose edges, which slicers and CAD tools need. | [Mesh repair](build-log/2-carcass.md#mesh-repair) |
| **Crank** | An arm fixed to a turning shaft; its far end goes round in a circle. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Crank pin** | The pin (here a small ball) at the end of the crank, where the leg is attached. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Stride** | How far the robot moves forward per half turn of the crank. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Bob** | How much the body goes up and down while walking. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Step height** | How high a foot lifts off the ground. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Gait groups** | The legs move in two groups of four (left 1 and 3 + right 2 and 4, and the other four), half a turn apart. | [Leg simulator…](build-log/3-legs-and-drive.md#leg-simulator-and-comparison) |
| **Crankshaft** | One shaft with one or more cranks on it, so one motor turns them all. | [Toy leg on one crankshaft](build-log/3-legs-and-drive.md#toy-leg-on-one-crankshaft) |
| **Idler** | A gear between two others, so they turn the same way. | [Four lateral crankshafts](build-log/3-legs-and-drive.md#four-lateral-crankshafts) |
| **build123d** | A Python library for CAD: parts are written as code. | [Legs and drive in CAD](build-log/3-legs-and-drive.md#legs-and-drive-in-cad) |
| **Journal** | The round part of a shaft that turns inside a hole (its bearing). | [Legs and drive in CAD](build-log/3-legs-and-drive.md#legs-and-drive-in-cad) |
| **Fork (pivot)** | The small block on the body's edge that the leg passes through. It swivels, and the leg tilts in it. | [Legs and drive in CAD](build-log/3-legs-and-drive.md#legs-and-drive-in-cad) |
| **Onshape** | CAD in the browser, used to assemble the parts and animate them. | [Onshape assembly](build-log/3-legs-and-drive.md#onshape-assembly) |
| **Band** | The ring added between the base and the body, 18.7 mm tall, that holds the forks' upper screws. | [Base v1 in CAD](build-log/3-legs-and-drive.md#base-v1-in-cad) |
| **Backlash** | The small play between meshing teeth. Without it, printed gears bind. | [Gear train test](build-log/3-legs-and-drive.md#gear-train-test) |
| **Keel** | A narrow ridge under the bowl that covers the gears where they go lower than the bowl. | [Base v1 in CAD](build-log/3-legs-and-drive.md#base-v1-in-cad) |
| **Keeper** | A cover that holds the crankshaft down in its slots. | [Test leg…](build-log/3-legs-and-drive.md#test-leg-first-assembly-and-clearance-result) |
| **Gear offset** | The angle a gear is turned on its own shaft, relative to the cranks. | [Gear train v2 in CAD](build-log/3-legs-and-drive.md#gear-train-v2-in-cad) |
| **Margin (motor)** | How many times the motor's stall torque exceeds the worst torque it has to give; 3 or more here. | [Whole robot first…](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) |
| **Stall torque** | The torque at which a motor stops turning. | [Whole robot first…](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) |
| **Pinion** | The small gear on the motor's shaft. | [Whole robot first…](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) |
| **Coupon** | A small test piece cut from a part's design, printed to test one fit before the whole part. | [Whole robot first…](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) |
| **v0** | The plan's first working chassis with its motor, walking with ballast in place of the body. Dropped on 2026-11-16: the looks robot is the only one printed. | [Whole robot first…](build-log/3-legs-and-drive.md#whole-robot-first-motor-sizing-and-chassis-plan) |
| **Master model** | One file with the robot's reference heights, the joints between its designs and the sizes of the bought parts; every design takes its shared numbers from it. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **Drive module** | The gearbox that carries the crankshafts, the idlers and the motor, assembled on the bench and screwed into the chassis as one piece. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **D-shaft** | A motor shaft with one flat side, so a part pressed on it cannot turn. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **Jig** | A tool made for one job that holds parts in the right place while they are put together. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **Gauge** | A piece of a known thickness used to set or check a gap. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **Keep-in check** | A check that every part stays inside an envelope (here the carcass, less its wall), except where a named exception says how far it may stand out. | [Chassis Part A](build-log/3-legs-and-drive.md#chassis-part-a-master-model-and-drive-module) |
| **Friction clutch** | A joint that transmits torque by friction and slips when the torque is too high, so a jam cannot break a gear. | [Part B1 and the clutch](build-log/3-legs-and-drive.md#chassis-part-b1-part-c-check-and-the-friction-clutch) |
| **Wave washer** | A thin steel ring bent in waves, used as a spring that presses with a steady force. | [Part B1 and the clutch](build-log/3-legs-and-drive.md#chassis-part-b1-part-c-check-and-the-friction-clutch) |
| **Shim** | A very thin flat washer added or taken away to set a gap or a spring's force. | [Part B1 and the clutch](build-log/3-legs-and-drive.md#chassis-part-b1-part-c-check-and-the-friction-clutch) |
| **Mock-up (N0)** | The whole robot drawn and checked in simple shapes (tubes and boxes), so a change costs seconds. | [N0 mock-up](build-log/3-legs-and-drive.md#n0-mock-up-the-looks-robot-in-simple-shapes) |
| **N1 form** | The real looking parts (body, base, eyes, legs) as light meshes of at most 25k triangles, checked over 24 crank poses. | [N1 form](build-log/3-legs-and-drive.md#n1-form-the-real-looking-parts-as-light-meshes) |
| **Window** | The opening cut in the body and base where a leg root passes, sized by the root's swing over a turn. | [N1 form](build-log/3-legs-and-drive.md#n1-form-the-real-looking-parts-as-light-meshes) |
| **Reference mesh** | A downloaded STL kept only to measure a parametric rebuild against; no printed part is a mesh. | [Meshes become parameters](build-log/3-legs-and-drive.md#meshes-become-parameters) |
| **Spine and sections** | A part's skin described by a curve of 5 points (spine) and a few cross-sections along it; changing the spine bends the part. | [Meshes become parameters](build-log/3-legs-and-drive.md#meshes-become-parameters) |
| **Fidelity (p95, max)** | How far a rebuild's surface is from its reference, both ways: 95 % of points within p95, the max on the 99.9th percentile. | [Meshes become parameters](build-log/3-legs-and-drive.md#meshes-become-parameters) |

[↑ Contents](#contents)
