# Spider-Bot · Hardware

Everything that is not printed: what each design uses and how many Morante has. Designs only use hardware listed
here (a new item is added here first, as «to buy»), and the workshop kit compares its parts list with the **Have**
column. At the end of the build this becomes the bill of materials.

**Have**: how many are in the workshop (`?` = not counted yet). **Used by**: the designs that need it, with the
count per robot or test.

| Item | Size | Have | Used by | Notes |
|---|---|---|---|---|
| Socket head screw | M3 × 10 | ? | [test frame v2](cad/test-frame/): 2 (fork swivel); [chassis Part B](cad/chassis/design-plan-b.md): 16 (forks) + 2 (front block) + 2 (holder cradle) + 1 (eyes board) + 1 (switch retainer) + 2 (body lug) + 2 (ballast lid, v0) + 2 (crank cover) = 28 | Nuts in the M3 nut row |
| Socket head screw | M3 × 12 | ? | [gear train test v2](cad/gear-train-test/): 3 (idler axles) + 2 (cap); [chassis Part A](cad/chassis/): 1 (cap front) + 1 (cap and clamp, shared) + 1 (clamp rear); chassis Part B: none (the body's rear screw is an M3×8, below) | |
| Socket head screw | M3 × 16 | ? | [test leg](build-log/3-legs-and-drive.md#test-leg-first-assembly-and-clearance-result) | |
| Nut | M3 | ? | gear train test v2: 3; test frame v2: 2; [chassis Part A](cad/chassis/): 4 (cap front, cap and clamp shared, clamp rear, pin keeper) + 4 (I7, module to chassis) | 5.5 mm across flats, 2.4 mm thick |
| Screw | M2 | ? | test leg, first assembly (instead of M3) | |
| Steel pin | Ø3 | ? | [base v1](cad/base/): idler axles; [chassis Part A](cad/chassis/): Ø3 × 10 × 3 (idler pins) | Length per design |
| Socket head screw | M3 × 6 | ? | [chassis Part B](cad/chassis/design-plan-b.md): 3 (I7: front, under the can, -X boss; nuts in the M3 nut row) | To buy |
| Socket head screw | M3 × 8 | ? | [chassis Part A](cad/chassis/): 1 (pin keeper; its nut in the M3 nut row); [chassis Part B](cad/chassis/design-plan-b.md): 1 (body rear screw, from below into the body lug) + 1 (I7, behind the can) | |
| Socket head screw | M3, length per nut | ? | [chassis](cad/chassis/README.md): 4 (I7, module to chassis from below; nuts in the M3 nut row). Stock lengths, never cut: the shell's counterbores are set so each tip ends between its nut's top and the hole's end (`shell.py`): M3×6 (front), M3×6 (under the can), M3×8 (behind the can), M3×6 (-X boss) | Counted in the M3 × 6 and M3 × 8 rows |
| Gear motor | N20, Pololu Micro Metal Gearmotor HP 6 V 380:1 ([#4794](https://www.pololu.com/product/4794)) | ? | [chassis](cad/chassis/design-plan.md) drive module: 1 | To buy once the whole robot passes in CAD and its mass confirms the [motor sizing](sim/motor-sizing-result.txt); measure it for the master model |
| Battery holder | 4 × AAA, switch and cover, about 64 × 49 × 16 mm | ? | [chassis](cad/chassis/design-plan.md): 1, in a cradle inside the body | To buy with the motor; size from a typical listing until then, measure the one bought |
| NiMH batteries | AAA | ? | Battery holder: 4 | To buy with the motor; the motor sizing's runtime assumes 800 mAh |
| LEDs | 3 mm or 5 mm, blue or white | ? | Eyes board: 2 | From the Arduino kit |
| Perfboard | | ? | Eyes board: 1, cut to fit a 50 × 22 × 10 mm pocket | |
| Mini slide switch | SPDT, panel, about 12 × 6 × 6 mm (e.g. SS12D00) | ? | [chassis](cad/chassis/design-plan.md): 1 (main switch, recessed at the rear) | To buy with the motor |
| 2-pin connector pair | JST-XH 2.54 mm, with leads | ? | [chassis](cad/chassis/design-plan.md): 2 (battery → chassis; switched power → eyes board) | To buy with the motor |
| Resistor | 100–220 Ω, ¼ W | ? | Eyes board: 2 (one per LED) | From the Arduino kit, or to buy |
| Ballast | Steel nuts or washers, about 110 g | ? | [chassis](cad/chassis/design-plan.md) v0 walk test: 1 set, in the ballast frame | Workshop stock or to buy; mass from [`cad/chassis/mass_estimate.py`](cad/chassis/mass_estimate.py), weighed on a kitchen scale |

Tools in the workshop (for `ACCESS` in the CAD checks and the kit): screwdrivers, hex keys, pliers, caliper.
