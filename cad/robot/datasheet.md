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

**Done 2026-11-23 (afternoon, commit 7ad2b9b)**

- Leg 4 window WR + 0.6 (`WR_EXTRA`); leg 0's front relief and bulge also follow its 30 mm down move (`PATH_RELIEF`, `path_samples`).
- Body: the inner wall strip under the cell holder cut (`STRIP_*`): the body + switch + LEDs bench path now clears.
- Drive unit: cheek rails notched over the transfer (`NOTCH_HW`), tongue 2 cut back to the notch edge (3.00 → 1.56 mm, Morante's choice); the transfer's bench path clears, crank 2 retention ok. The hub cannot be shortened: it is the only link between the transfer's two gears.
- `fitcheck/check.py` switch y: `- ORIGIN[1]`; `unify()` faces-only for the base.

**Evening 2026-11-23 (uncommitted, unverified)**

The 5 FAIL of `verify.py --quick` were diagnosed with probes (seconds each):
1. base × leg-1 gap 0.00: leg 0's bulge, grown along its path, put 3.04 mm³ into leg 1's window (box 3 × 2 × 2.5 at
   (35.0, -10.25, 16.3); `base_win` had 0 there).
2. legs 0 / 4 block on the slide along the pin: only the base, 0.01 mm³ at (15, -24, 10–12) and < 0.005 mm³ at
   (-28.5, -14.6, 11.2); `path_samples` covered the down move, not the slide.
3. Switch: the body boxed it in (floor, top bar, ribs and a rigid 1.2 mm front plate): it could not go in. **Morante:
   «Con pegamento»**: front plate removed, switch pushed in from the front and glued, like the LEDs and JST.

A cad-fixer edited `shells.py` (bulge carved for leg 1, slide samples for legs 0/4, keeper plate removed) and
`power_verify.py` (switch in GLUED); the base was rebuilt (1669 s), the body build was stopped. Not checked: the next
step replaces these cutters anyway (below). The switch decision stays.

**Speed (Morante, 2026-11-23): any build or check over 40 s is a bug; aim for 10 s.** Measured cause: the shells'
clearances are hundreds of convex hulls of sampled leg points cut in OpenCascade (base 1669 s: leg 0 and 4 hulls,
bulges and reliefs ≈ 22 min; body ≈ 3500 s: rim 846 s, lift 884 s, power 551 s, posts 318 s; body.step 152 MB).
Probes (2 cores, 8 GB): the base skin builds in 6.2 s; the same skin with 10 designed cutters (a slot per leg, two
pockets) cuts in **3.2 s** in OpenCascade; manifold3d cuts the skin with finished cutters in 0.3–0.6 s but chokes on
the same hundreds of hulls (50–190 s); `min_gap` of 8 legs × 24 poses against the base takes 4.2 s; a band-limited
hull shortcut failed (14–16 mm³ left at the pivot blocks).

Phase 0 of the speed plan (time budget) was started and stopped half way, untested: `tools/timebudget.py` (watchdog,
`CAD_BUDGET` default 40 s, exit 3; stage times to `out/build-times.csv`), hooks in `tools/stage_cache.py` and
`shells.py cached()`, lazy build123d import in `cad/common.py` (`part_args` starts the watchdog).

**Next, in order** (no cold base or body build before step 2: they take 30–60 min)

1. Finish Phase 0: test a warm `build.py --part`, a dummy stage killed at `CAD_BUDGET=5`, `cad_verify --smoke --only
   leg-0` unchanged plus its total time (a total over 40 s is a WARN until checks are fast); a «Time budget» paragraph
   in `cad/README.md`. cad-fixer, Sonnet.
2. Phase 1: the shells' clearances designed, not computed: each leg's window a slot (neck over 24 poses + slide + 0.4),
   legs 0/4 relief a rounded box and the bulge a smooth simple shape, the body's rim and lift cuts one notch per leg,
   the power pockets boxes (no `grow()` offsets). Sized in numpy from the measured motion, proved with `min_gap`.
   Target: base and body ≤ 40 s each (aim 10). The windows' look changes: judge and Morante see it. cad-designer, Opus
   (200–400k), Morante already agreed.
3. Phase 2 only if phase 1 is over 40 s: carve in manifold3d (STL only; STEP of the shells lost: Morante decides).
4. Phase 3: checks ≤ 40 s on light meshes (`min_gap`), `fitcheck/check.py` (19 min) and the assembly paths (44 s).
5. Then `verify.py --quick` 0 FAIL, `rounds.py round cad/robot 0`, the looks judge, Morante's «se parece».

**Known issues**

- The leg snap's radial engagement is 0.08-0.18 mm (`fits.PRESS`); a coupon is planned in the robot batch.
- The r00 build-log entry is updated when r00 closes.
