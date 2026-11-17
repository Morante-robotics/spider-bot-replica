# Spider-Bot · Hardware

Everything that is not printed: what each design uses and how many Morante has. Designs only use hardware listed
here (a new item is added here first, as «to buy»), and the workshop kit compares its parts list with the **Have**
column. At the end of the build this becomes the bill of materials.

**Have**: how many are in the workshop (`?` = not counted yet). **Used by**: the designs that need it, with the
count per robot or test.

| Item | Size | Have | Used by | Notes |
|---|---|---|---|---|
| Socket head screw | M3 × 10 | ? | [test frame v2](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/test-frame): 2 (fork swivel); [chassis Part B](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/design-plan-b.md): 16 (forks) + 2 (front block) + 2 (holder cradle) + 1 (eyes board) + 1 (switch retainer) + 2 (body lug) + 2 (crank cover) = 26 | Nuts in the M3 nut row |
| Socket head screw | M3 × 12 | ? | [gear train test v2](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/gear-train-test): 3 (idler axles) + 2 (cap); [chassis Part A](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/chassis): 1 (cap front) + 1 (cap and clamp, shared) + 1 (clamp rear); chassis Part B: none (the body's rear screw is an M3×8, below) | |
| Socket head screw | M3 × 16 | ? | [test leg](build-log/3-legs-and-drive.md#test-leg-first-assembly-and-clearance-result) | |
| Nut | M3 | ? | gear train test v2: 3; test frame v2: 2; [chassis Part A](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/chassis): 4 (cap front, cap and clamp shared, clamp rear, pin keeper) + 4 (I7, module to chassis) | 5.5 mm across flats, 2.4 mm thick |
| Screw | M2 | ? | test leg, first assembly (instead of M3) | |
| Steel pin | Ø3 | ? | [base v1](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/base): idler axles; [chassis Part A](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/chassis): Ø3 × 10 × 3 (idler pins) | Length per design |
| Socket head screw | M3 × 6 | ? | [chassis Part B](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/design-plan-b.md): 3 (I7: front, under the can, -X boss; nuts in the M3 nut row) | To buy |
| Socket head screw | M3 × 8 | ? | [chassis Part A](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17/cad/chassis): 1 (pin keeper; its nut in the M3 nut row); [chassis Part B](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/design-plan-b.md): 1 (body rear screw, from below into the body lug) + 1 (I7, behind the can) | |
| Socket head screw | M3, length per nut | ? | [chassis](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/README.md): 4 (I7, module to chassis from below; nuts in the M3 nut row). Stock lengths, never cut: the shell's counterbores are set so each tip ends between its nut's top and the hole's end (`shell.py`): M3×6 (front), M3×6 (under the can), M3×8 (behind the can), M3×6 (-X boss) | Counted in the M3 × 6 and M3 × 8 rows |
| Gear motor | N10, 3 V, metal gearbox, 3 mm D-shaft; ratio for ≈ 100–150 rpm at 3 V | ? | Redesign (looks first): 1, at ≈ 60 % scale | To buy; chosen 2026-11-17 over a Ø6 mm planetary for its strength and D-shaft. Measure it for the mock-up |
| Battery compartment | Printed, for 6 × AG13 wired 2S3P (3 V), with spring contacts | — | Redesign: 1 | Contacts to choose at N1 |
| Button cells | AG13 / LR44 alkaline, Ø11.6 × 5.4 mm | ? | Battery compartment: 6 | The original Mini Spider-Bot uses 6 × AG13 |
| LEDs | 3 mm or 5 mm, blue or white | ? | Eyes board: 2 | From the Arduino kit |
| Perfboard | | ? | Eyes board: 1, cut to fit a 50 × 22 × 10 mm pocket | |
| Mini slide switch | SPDT, panel, about 12 × 6 × 6 mm (e.g. SS12D00) | ? | [chassis](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/design-plan.md): 1 (main switch, recessed at the rear) | To buy with the motor |
| 2-pin connector pair | JST-XH 2.54 mm, with leads | ? | [chassis](https://github.com/Morante-robotics/spider-bot-replica/blob/pre-redesign-2026-11-17/cad/chassis/design-plan.md): 2 (battery → chassis; switched power → eyes board) | To buy with the motor |
| Resistor | 100–220 Ω, ¼ W | ? | Eyes board: 2 (one per LED) | From the Arduino kit, or to buy |

Tools in the workshop (for `ACCESS` in the CAD checks and the kit): screwdrivers, hex keys, pliers, caliper.
