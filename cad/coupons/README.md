# coupons: fits of the S 1.0 robot that were assumed or never printed

Built by `build.py` from the robot's constants (`cad/robot/drive.py`, `shells.py`, `cad/fits.py`); STL in `out/`.
Digits engraved on each coupon = step number (c6: notches on the left edge, 1-3; c4 / c5 blocks: steps run along the
row, 1-3 in order). Print all on one plate, 0.2 mm layers, PLA, no support. c1 / c7 print as the robot's legs and cranks do: pin and tube axis horizontal (the tubes lie on a flat foot, slit up, no support in the bore); c11 / c12 lie on their broad faces.

| Coupon | Fit | Steps | Morante measures | Robot constant it sets |
|---|---|---|---|---|
| c1-leg-snap | PRESS (leg snap) | bead radius per `shells.snap_bead_r` (tube 1-3: neck + TURN, leg 0/4, leg 3/7) on the real pin with its groove; bore = leg 0's BORE_R (a circle: the tilted-pin ellipse needs the leg's cone, not cut here), slit + 45 deg chamfers as the leg | tube pushed on the pin by hand: snaps over the tip? stays when pulled? comes off with a pull? | `shells.snap_bead_r`, `SNAP_BW`, `SNAP_SLIT`, `fits.PRESS` |
| c2-motor-seat | MOTOR_SEAT | 0.10 / 0.20 / 0.30 a side round 12 x 10 (U 1-3), plus a 12 x 10 stand-in | the real N10 (caliper first: 12 x 10?) drops in by hand, does not rattle | `fits.MOTOR_SEAT`, `drive.N10_W/H` |
| c3-gear-tip | GEAR_TIP | 0.25 / 0.40 / 0.50 round the tips (pockets 1-3), 2 gears 10 T, centre distance 10.10 | gear pair on two M3 screws turns freely by hand, tips not rubbing | `fits.GEAR_TIP` |
| c4-pilots | M3 pilot (M3_PILOT_R) | Ø2.4 / 2.5 / 2.6; depths 3.2 (keel), 4.0 (transfer pin), 2.0 through-wall on edge (axles) | M3 screw goes in with the key, holds a firm pull, does not split the block | `drive.M3_PILOT_R`, `KEEL_PILOT_OVER`, `KEEL_LEN` |
| c5-seats | button seat + socket counterbore (STEEL, FIRST_LAYER) | hole / head radius +0.05 / +0.15 / +0.25 | M3 button head sits flat on the plate; socket head drops into the bed-side counterbore | `fits.STEEL` use, `FIRST_LAYER`, `M3_HOLE_R`, `BTN_R` |
| c6-marks | engraved numbers 3 mm | depth 0.3 / 0.5 / 0.7 ("1234") | readable by eye at arm's length; the digit is not filled | `drive.MARK_DEPTH`, `MARK_FS` |
| c7-leg-turn | TURN (leg tube on the crank pin) | bore r = pin + 0.15 / 0.25 / 0.35 (tube 1-3) | tube turns and rocks on the pin; no slop that clicks | `fits.TURN` on the leg joint, `shells.BORE_R` |
| c8-neighbour | NEIGHBOUR | gap 0.05 / 0.10 / 0.15 (pairs 1-3) | two blocks separate by hand, not welded | `fits.NEIGHBOUR` |
| c9-leg-window | LEG_OPEN / LEG_PATH | slot 0.30 / 0.40 / 0.50 a side round a 4 mm strip | strip slides along its slot without rubbing | `fits.LEG_OPEN`, `LEG_PATH` |
| c10-dshaft | DSHAFT | D-bore radius -0.10 / 0 / +0.10 (gears 1-3) | presses on the motor's Ø3 D-shaft (needs the motor) | `fits.DSHAFT` |
| c11-snap | PRESS (body <-> base front snap) | rib depth RIBD -0.2 / 0 / +0.2 (ribs 1-3) on a wall piece, one finger piece (finger SNT x SNW, hook, root block, as `shells.snap_geometry` / `finger_root`, plus a hand grip) | finger piece pushed over each rib: snaps over it? stays when pulled? comes off with a pull, finger not cracked? | `shells.RIBD` (SNG, SNT, SNW stay), `fits.PRESS`, `fits.WINDOW` |
| c12-cell-lid | PRESS (cell lid <-> cell-holder lips) | lip bump 0.3 / 0.4 / 0.5 proud (engagement 0.1 / 0.2 / 0.3 past the LOCATOR gap; lids 1-3) in the holder wall's groove (one wall piece, `power.py`) | each lid lip pressed down inside the wall piece: clicks in? holds? pulls out without breaking the lip? | `power.BUMP`, `BUMP_H`, `LIP_T`, `LIP_L`, `GROOVE`, `fits.PRESS` |

Grams (PLA 1.24 g/cm3): c1 2.1, c2 3.4, c3 8.9, c4 3.7, c5 2.8, c6 2.1, c7 2.1, c8 2.4, c9 1.3, c10 2.2, c11 1.5, c12 0.9.
