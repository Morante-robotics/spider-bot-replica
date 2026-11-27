# Spider-Bot · Hardware

The one shopping list for the robot (`cad/robot`, scale S 1.0, phase 3 design), counted from the code on 2026-11-28:
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
| M3 socket head screw (ISO 4762), 5 mm | 2 | 3 |
| M3 socket head screw, 10 mm | 2 | 3 |
| M3 button head screw (ISO 7380), 10 mm | 3 | 5 |
| M3 button head screw (ISO 7380), 16 mm | 1 | 2 |

From the Arduino kit, not ordered: 2 red or yellow 5 mm LEDs, their 2 resistors of 100–220 Ω and the hook-up wire
(spec m16 and m17). The robot uses no nuts or steel pins: every screw is M3 and self-tapping into a printed pilot.

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
| Socket head screw | M3 × 5 | 2 (keel, from below) | `drive.py` (`KEEL_LEN`, `KEEL_SCREWS`) | ? | To buy |
| Socket head screw | M3 × 10 | 2 (strap of the transfer cheek; cell holder to the drive unit) | `drive_verify.py` (`SCREWS["strap-screw"]`); `power.py` (`M3_L`) | ? | To buy |
| Button head screw | M3 × 10, ISO 7380 | 3 (idler axles 1, 2 and 3) | `drive_verify.py` (`SCREWS["axle-1"]` to `axle-3`, `BUTTON`) | ? | To buy |
| Button head screw | M3 × 16, ISO 7380 | 1 (transfer axle) | `drive_verify.py` (`SCREWS["transfer-pin"]`, `BUTTON`) | ? | To buy |

Socket head screws are ISO 4762 (head Ø5.5 × 3.0, 2.5 mm hex key); button heads are ISO 7380 (head Ø5.7 × 1.65, 2 mm hex
key), used where there is no room for a printed rim. All are self-tapping into PLA pilots of Ø2.5 (assumed; the coupon c2,
which Morante skipped, is replaced by the S 1.0 coupons in [Open items](build-log.md#open-items)). The robot has no nuts or
steel pins.

Rows of the old chassis designs (M3 screws and nuts, Ø3 steel pins, 2-pin JST, perfboard, printed battery
compartment, the test frame, gear train test and base v1 hardware) were removed: r00 does not use them. The archive
tags (`pre-redesign-2026-11-17`) keep them.

Tools in the workshop (for `ACCESS` in the CAD checks and the kit): screwdrivers, hex keys, pliers, caliper.
