# Legs and drive · Onshape assembly

How to assemble the [STEP files](README.md) in Onshape with mates and animate them, so you can see a leg walk and
compare its foot path with the simulator. Part 1 (one leg on the test frame) is the one that matters. Part 2 (the
gear train) is optional.

Free Onshape account. Documents on the free plan are public, which is fine here because the files are public anyway.

## Part 1 · One leg on the test frame

The same parts you will print and turn by hand: `test-frame`, `crankshaft-2`, `leg-middle-right`, `pivot`.

### 1. Import

1. **Create → Document**, name it `Spider-Bot drive`.
2. Click **+** (bottom left) → **Import**, and pick `test-frame.step`, `crankshaft-2.step`, `leg-middle-right.step`
   and `pivot.step`. Each one becomes a Part Studio tab. STEP carries millimetres, so nothing needs scaling.
   Import from inside the document, not from the Documents page: there, every file becomes a document of its own.
   If an options dialog comes up, leave *Orient imported models with Y Axis Up*, *Create a composite part* and
   *Join adjacent surfaces* unticked, because the files are Z up and each one is a single solid.

The test frame is exported in robot coordinates (mm, z up, forward = −Y). The other three are each in their own
frame. Keep this in mind: once the frame is fixed at the origin, every number you measure is a robot coordinate.

### 2. The slider (a helper part)

Onshape has no mate for "ball slides inside a bore and can tilt". You build it from two mates and a small helper
part: crankshaft → **Ball** → slider → **Slider** → leg.

1. **+ → Create Part Studio**, rename it `slider`.
2. **Sketch** on the Top plane: a circle at the origin, Ø3 mm.
3. **Extrude**, *Symmetric*, 4 mm. Its axis is Z and its centre is the origin.

You can hide it in the assembly later. It stands for the part of the crank ball that is inside the bore.

### 3. Assembly

1. **+ → Create Assembly**.
2. **Insert** the test frame. Close the dialog *without clicking in the view*, so it lands on the origin with its
   own coordinates. Right-click it → **Fix**.
3. Insert the crankshaft, the leg, the pivot and the slider. Drop them anywhere near the frame.

### 4. Mates

To add a mate, pick its type in the toolbar, then hover over an edge or face of each part and click the inferred
point (the mate connector). **Offset** and **Flip primary axis** are in the mate dialog. If a part lands the wrong
way round, flip. If it ends up pointing the wrong way, **Reorient secondary axis**.

| # | Mate | Part A: connector | Part B: connector | Offset |
|---|---|---|---|---|
| 1 | **Revolute** | Crankshaft: circular edge where the journal (Ø4) leaves the gear face | Test frame: the journal hole's edge on the *inner* face of the wall on the same side | 0.25 mm along Z, gear between the walls |
| 2 | **Revolute** | Pivot (fork): edge of the blind hole on its top face | Test frame: edge of the hole on the *underside* of the upper arm | 0.4 mm |
| 3 | **Revolute** | Leg: edge of the M3 hole on a side face of the boss | Pivot: edge of the cross hole on the *inner* face of the fork wall on the same side | 0.2 mm |
| 4 | **Ball** | Crankshaft: centre of the ball on the leg's side (+X) | Slider: midpoint of its axis | — |
| 5 | **Slider** | Slider: same connector (Z along its axis) | Leg: any point on the axis of the bore in the inner tube | — |

Check after mate 1: the crankshaft axis should be at y = −17.4, z = 63.9 (use **Measure** between the journal edge
and the origin). After mate 3 the leg should go through the fork with the tube on the crankshaft's side.

Mates 4 and 5 close the loop. If Onshape says the loop cannot be solved, the ball is too far from the bore. Turn the
crankshaft by dragging it until the ball sits near the tube's mouth, then add the mate again. If the leg snaps to
the wrong side (tube pointing outwards), drag it back, or flip mate 3.

The leg should now have exactly one free motion: dragging the crankshaft moves everything.

### 5. Animate

Right-click mate 1 in the Mates list → **Animate**: 0° to 360°, about 60 steps, **Play** (loop on). You should see
the following:

- The fork swings a few degrees left and right (±6°) and the leg tilts up and down in it (6–23°).
- The ball slides in and out of the bore by about 1.7 mm and never leaves it.
- The foot draws a closed loop.

### 6. Compare with the simulator

Put a **Mate connector** on the leg at the centre of the foot (hover over the round foot face and take its centre).
Then **Measure** between that connector and the assembly origin to get the foot's x, y, z. Turn the crankshaft
(drag it, or edit mate 1's value) so the crank pin on the leg's side points each way in turn, and write down the
foot position each time:

| Crank pin on the leg's side points | Foot x | Foot y | Foot z |
|---|---|---|---|
| Back (+Y) | 148.7 | −8.3 | 20.4 |
| Down | 152.3 | −2.8 | 25.2 |
| Forward (−Y) | 146.7 | 1.4 | 20.2 |
| Up | 143.0 | −3.9 | 15.7 |

These are the simulator's numbers (`sim/toy_leg_3d_rows_cad.json`). Over the whole turn the foot moves 9.8 mm along Y
(the stride) and 9.5 mm up and down: on the stand the foot never touches anything, so this is the full loop, not
the 4.6 mm bob of the walking robot. A difference of a few tenths of a millimetre comes from picking the pin
direction by eye. More than 1 mm means a mate is off: check the offsets.

## Part 2 · The gear train (optional)

Four crankshafts linked by three idlers. In Onshape you do not need gear teeth to mesh: a **Gear relation** couples
two revolute mates.

1. Import `spine.step` (robot coordinates: insert it at the origin and **Fix**), `crankshaft-1` … `-4` and
   `idler-1` … `-3`.
2. A **Revolute** for each crankshaft, as mate 1 above: the journal edge on the gear face against the inner face of
   a spine wall, 0.25 mm offset. Front to rear: crankshaft 1 in the frontmost slot (most negative Y).
3. A **Revolute** for each idler: the edge of its bore against the edge of the pin hole on a wall's inner face,
   0.45 mm offset. Idler 1 (11 teeth) goes between crankshafts 1 and 2, idler 2 (10) between 2 and 3, idler 3 (20)
   between 3 and 4.
4. **Before adding any relation, set the phases.** Turn each crankshaft until its right crank pin (+X side) points
   like this. The pins point opposite ways on neighbouring shafts, as in [the assembly image](images/assembly.gif):

   | Crankshaft | 1 | 2 | 3 | 4 |
   |---|---|---|---|---|
   | Right pin points | Forward (−Y) | Back (+Y) | Forward (−Y) | Back (+Y) |

   Turn each idler until its teeth sit between the teeth of its neighbours.
5. **Gear relation** between each crankshaft's revolute and the neighbouring idler's revolute, with the ratio set to
   the two tooth counts (12 and 11, 12 and 10, 12 and 20) and **Reverse direction** on, because meshed gears turn
   opposite ways. Each idler joins two crankshafts, so add 6 relations in all. Check the direction: all four
   crankshafts must turn the same way. If an idler spins too fast or too slow against its neighbours, swap the ratio.
6. Animate crankshaft 1's revolute. All four shafts must turn together, and their pins must stay 180° apart from the
   neighbours'.

## When you are done

Tell Claude, with the document's link. Claude takes the screenshots and the animation video of the Onshape window,
adds the link to the [README](README.md) and writes the result into the [build log](../../build-log.md), including
whatever did not match the table in step 6.
