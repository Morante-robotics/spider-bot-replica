# Print plates

Bambu Studio projects (.3mf), ready to print on the Bambu Lab P2S (0.4 mm nozzle, Textured PEI plate, Bambu PLA
Basic, 0.20 mm Standard). Open one in Bambu Studio, check it and send it: **Slice plate** → **Print plate**.

| Plate | Parts | Time | PLA |
|---|---|---|---|
| [`test-leg-plate.3mf`](test-leg-plate.3mf) | [Test frame](../cad/drive/), middle leg (right), fork, crankshaft 2, [clearance block and pin](../cad/clearance-test/) | 1 h 28 min | 29.6 g |
| [`test-frame-v2.3mf`](test-frame-v2.3mf) | Test frame with the arms fixed and a keeper for the crankshaft, fork on M3 pins, and the leg, all with the clearances from the block (2026-11-11) | 1 h 18 min | 25.6 g |

## Test leg plate

One run with everything needed to turn one leg by hand and to learn which hole clearance this printer needs. The
other 21 parts of the drive wait for two things: the clearance result (if it is not 0.2 mm, they are rebuilt with
the right `CLR`) and the base, which holds the forks and the spine.

![Prepare](images/prepare.png)

![Preview with supports](images/preview-supports.png)

**Settings changed from the presets:** supports on, **tree(auto)**, **On build plate only**. Build-plate-only keeps
supports out of the holes and the leg's bore. Bambu Studio then warns about 2 regions of the leg it cannot support:
the top of the bore and the flared mouth inside the tube. Both are short bridges (3.8 mm) and print without support.

**How it was made** (to repeat it):

1. Lay out the parts in their print orientation, arrange them and slice with the CLI. The leg is laid on its flat
   side (rotated 90° about X); everything else stays as modelled:
   ```
   python3 tools/bambu_plate.py print/test-leg-plate.3mf cad/drive/test-frame.stl cad/drive/leg-middle-right.stl@90,0,0 \
       cad/drive/pivot.stl cad/drive/crankshaft-2.stl cad/clearance-test/clearance-block.stl cad/clearance-test/clearance-pin.stl \
       --set enable_support=1 "support_type=tree(auto)" support_on_build_plate_only=1 "curr_bed_type=Textured PEI Plate"
   ```
   The tool lists the `--set` overrides in the project as changed settings. Without that, the GUI opens the project
   with the plain system preset and drops them.
2. Open the .3mf in Bambu Studio and check **Process → Support**: **Enable support** ticked, **tree(auto)**, **On
   build plate only** ticked (checked on `test-frame-v2.3mf`: the GUI keeps them). **Slice plate**, check the preview,
   and save (⌘S).

**Hardware for the test:** 1 × M3×16 screw + nut (leg in the fork), 2 × M3×10 screws + 2 nuts (fork in the frame, from v2), 2 × M3×12 + 2 nuts (keeper, v2), and a few
spare M3 screws for the clearance block's bottom row and its 3 tap holes.

**After printing:** remove the supports. Then try the clearance block: the journal through the top holes, the
ball into the middle ones and an M3 screw through the bottom ones. The right clearance is the smallest one that
turns freely without wobbling. If it is not 0.2 mm, set `CLR` in [`cad/drive/build.py`](../cad/drive/build.py) and
rebuild before printing the rest.
