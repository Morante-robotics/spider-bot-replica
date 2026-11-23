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

**Done 2026-11-23 (afternoon, uncommitted)**

- Leg 4 window WR + 0.6 (`WR_EXTRA`); leg 0's front relief and bulge also follow its 30 mm down move (`PATH_RELIEF`, `path_samples`).
- Body: the inner wall strip under the cell holder cut (`STRIP_*`): the body + switch + LEDs bench path now clears.
- Drive unit: cheek rails notched over the transfer (`NOTCH_HW`), tongue 2 cut back to the notch edge (3.00 → 1.56 mm, Morante's choice); the transfer's bench path clears, crank 2 retention ok. The hub cannot be shortened: it is the only link between the transfer's two gears.
- `fitcheck/check.py` switch y: `- ORIGIN[1]` added.
- `unify()` in shells.py: base clean() left it invalid and clean() also alters its input; the base uses faces-only unify (valid, watertight STL); the keel stage is keyed on it.
- Stage times (2 cores, cold stages): base ≈ 50 min, leg 0 bulge + relief ≈ 19 min of it; body 58 min (rim cuts 846 s, lift cuts 884 s, power 591 s, stop posts 318 s). Speed tips (clean=False etc.) measured: tenths of a second, not worth it.

**Check** `cad_verify verify.py --quick` after the rebuild: **5 FAIL**:

1. base × leg-1 gap 0.00 at pose 0 (was 0.89), also as a LEG_OPEN joint FAIL: probably leg 0's path bulge (`path=pth` on the bulge carve) grew into leg 1's sweep. Check the bulge first.
2. leg-0 and leg-4 now pass the down move but block on move 2 (the slide along the pin) at 2.00 / 3.25 mm.
3. ss12d00-switch: the fingertip tool still hits the body (14 mm³): the reach 30 → 15 in power_verify.py did not change it; find which ACCESS entry verify.py uses and what the tool hits.

**Next, in order**

1. Diagnose 1–3 with probes on the built STLs (seconds each), then one cad-fixer for the three.
2. Rebuild only the stages they touch (one heavy job, watchdog script as in this step), `--quick` with 0 FAIL.
3. `rounds.py round cad/robot 0` and the looks judge, then Morante's «se parece».
4. Optimizer on the stage times above (leg 0 bulge, body rim and lift cuts).

**Known issues**

- The leg snap's radial engagement is 0.08-0.18 mm (`fits.PRESS`); a coupon is planned in the robot batch.
- The r00 build-log entry is updated when r00 closes.
