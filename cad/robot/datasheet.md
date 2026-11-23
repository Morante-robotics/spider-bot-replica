# Robot datasheet

Numbers and paths that describe the robot's design as it stands. The story is in the build log
([Looks first](../../build-log/4-looks-first.md)); what is left is in [Open items](../../build-log.md#open-items).

## State 2026-11-23

N2 round r00 of `cad/robot` at scale 0.70. Heavy jobs run **in series, one at a time** (2 cores, 8 GB; every build
under a watchdog, e.g. 100 min / 5 GB).

**Done**

- Leg hold fixed with option A: a snap groove on the crank pins, a bead and a slit in the leg tubes (commit 77161ac).
  Leg RETAIN play 1.25 and crank 4 × leg 3/7 0.19 are accepted by Morante (`verify.py` PAIR_GAP).
- Interior assembly and access reworked: axle heads counterbored, web 0.1 thinner, leg paths along each pin's axis,
  holder path down-slide-down, switch and LEDs on the body's bench step, lid and switch snaps declared, key hole in
  the clamp plate, motor path 38 mm.
- The viewer draws the 8 real leg STLs.

**Check** `cad_verify verify.py --quick` (whole robot, about 1 min): **5 FAIL, motion all ok.**

**Next, in order**

1. One cad-fixer:
   - widen the base window cutters of legs 0 and 4 by about 0.6 mm (`shells.WR` for those two; no path or crank pose
     clears them, all 24 poses tested);
   - remove the body's inner wall strip under the cell holder (|x| < 20.05, y 6.4-12.8, z <= 23.65; it also touches
     the cells at x ±18, z 28);
   - shorten the switch access finger to a fingertip (about 15 mm, not 30);
   - fix the transfer + sleeve bench path (blocked 0.5 mm, never looked at).
2. One rebuild of base then body (about 70 min).
3. `--quick` with 0 FAIL.
4. `rounds.py round cad/robot 0` and the looks judge.
5. Morante's «se parece».

**Known issues**

- `fitcheck/check.py`, around line 260, misses `- ORIGIN[1]` for the battery box (the same bug was fixed in
  `power.py`).
- The leg snap's radial engagement is 0.08-0.18 mm (`fits.PRESS`); a coupon is planned in the robot batch.
- The r00 build-log entry is updated when r00 closes.
