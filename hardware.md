# Spider-Bot · Hardware

The one shopping list for the N2 robot (`cad/robot`, round r00, scale 0.70), counted from the code on 2026-11-23:
everything that is not printed. Designs only use hardware listed here (a new item is added here first, as «To
buy»), and the workshop kit compares its parts list with the **Have** column. At the end of the build this
becomes the bill of materials.

## Order

What to order: the count the robot uses and the count to order (screws +50 %, cells ×2).

| Item | Uses | Order |
|---|---|---|
| N10 gear motor, 3 V, **07 type, 100:1** (low-current core), metal gearbox, Ø3 shaft | 1 | 2 |
| AG13 / LR44 alkaline cells, Ø11.6 × 5.4 | 6 | 12 |
| Conical springs, Ø7 at the base and Ø4 at the tip, 2.0 mm compressed | 3 | 6 |
| Nickel strip, 0.3 mm thick (one 37 × 5.5 mm piece) | 1 piece | a strip of about 10 cm |
| JST-XH 3-pin connector, male and female pair with leads | 1 pair | 2 pairs |
| SS12D00 slide switch (SPDT, panel) | 1 | 2 |
| M2 socket head screw (ISO 4762), 4 mm | 2 | 3 |
| M2 socket head screw, 5 mm | 1 | 2 |
| M2 socket head screw, 6 mm | 3 | 5 |
| M2 socket head screw, 12 mm | 1 | 2 |

From the Arduino kit, not ordered: 2 red or yellow 5 mm LEDs, their 2 resistors of 100–220 Ω and the hook-up wire
(spec m16 and m17). The robot uses no M3 screws, nuts or steel pins.

## Table

**Have**: how many are in the workshop (`?` = not counted yet). **Source**: «To buy», or «Arduino kit» if it is
already in the kit. **Where used**: the file that holds the count.

| Item | Size | Count | Where used | Have | Source |
|---|---|---|---|---|---|
| Gear motor | N10, 3 V, **07 type, 100:1** (Morante, 2026-11-27), metal gearbox, Ø3 × 10 shaft (D-cut and body size to measure on arrival; modelled 12 × 10 × 21 mm). Seller's datasheet at 3 V: no load 95 rpm ≤ 0.05 A, rated 63 rpm 0.2 kg·cm ≤ 0.11 A, stall ≥ 0.4 kg·cm ≤ 0.25 A. Picked over the 92 type (0.42 A rated) because the AG13 cells are rated for mA-level drain (VARTA V13GA: 130 mAh at 6.8 kΩ): at the robot's ≈ 0.09 kg·cm it draws ≈ 0.1 A (≈ 33 mA a cell) at ≈ 70 rpm, estimated, not measured. The crank turns ≈ 1:1 with the shaft | 1 | `drive.py` (`N10_W/H/L`, `RATIO`), `drive_verify.py` (`n10-motor`) | ? | To buy |
| Button cells | AG13 / LR44 alkaline, Ø11.6 × 5.4 mm | 6 (3 stacks of 2) | `power.py` (`cells`, `XS`) | ? | To buy |
| Conical spring | Ø7 → Ø4, 2.0 mm compressed | 3 | `power.py` (`springs`, `SPR_R0`, `SPR_R1`) | ? | To buy |
| Nickel strip | 0.3 thick, 37 wide, 5.5 long (cut piece) | 1 | `power.py` (`strip`, `STRIP_T`, `NSX`) | ? | To buy |
| Slide switch | SS12D00, SPDT, body 8.6 × 3.5 × 3.6, lever 1.5 × 3.0 × 1.5 | 1 | `power.py` (`switch`), part `ss12d00-switch` | ? | To buy |
| Connector pair | JST-XH 3-pin, 2.5 mm pitch, with leads; mated 9.9 × 5.8 × 11.5 | 1 | `power.py` (`jst`) | ? | To buy |
| LED | 5 mm (Ø5, flange Ø5.8), red or yellow (spec m16) | 2 (the big eyes) | `power.py` (`leds`) | ? | Arduino kit |
| Resistor | 100–220 Ω, ¼ W, Ø2.3 × 6.5 | 2 (one per LED) | `power.py` (`leds`, `RES_*`) | ? | Arduino kit |
| Hook-up wire | thin, a few short leads (switch, LEDs, JST) | not counted (wires take no volume, spec m3) | spec m17 | ? | Arduino kit |
| Socket head screw | M2 × 4 | 2 (keel, from below) | `drive.py` (`KEEL_LEN`, `KEEL_SCREWS`) | ? | To buy |
| Socket head screw | M2 × 5 | 1 (idler axle 3) | `drive_verify.py` (`SCREWS["axle-3"]`) | ? | To buy |
| Socket head screw | M2 × 6 | 3 (idler axles 1 and 2; cell holder to the drive unit) | `drive_verify.py` (`axle-1`, `axle-2`); `power.py` (`M2_L`) | ? | To buy |
| Socket head screw | M2 × 12 | 1 (transfer axle) | `drive_verify.py` (`SCREWS["axle-t"]`) | ? | To buy |

All M2 screws are ISO 4762 (head Ø3.8 × 2.0, 1.5 mm hex key), self-tapping into PLA pilots of Ø1.6 (assumed; proven
on the coupon c2, which Morante skipped: the first plate tests it). The robot has no M3 screws, nuts or steel pins.

Rows of the old chassis designs (M3 screws and nuts, Ø3 steel pins, 2-pin JST, perfboard, printed battery
compartment, the test frame, gear train test and base v1 hardware) were removed: r00 does not use them. The archive
tags (`pre-redesign-2026-11-17`) keep them.

Tools in the workshop (for `ACCESS` in the CAD checks and the kit): screwdrivers, hex keys, pliers, caliper.
