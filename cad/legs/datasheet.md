# legs · datasheet

N1 (not printed): jenscolt's leg rebuilt as parametric build123d code, left and right from one model (`side`), both
parts on spines so N1 lays them on N0's leg path (`leg()`, below). Source of every number: the
parameter block at the top of `build.py` (each with the probe or section it came from).

| Part | jenscolt mesh | Built from | Size (mm) | Volume | STEP | STL (coarse) |
|---|---|---|---|---|---|---|
| leg-blade | `spideybot_L_leg1.stl` | skin lofted along a spine (cubic spline through 5 points) from 6 control sections (a, bB, bT, nB, nT; a cubic spline through each along the arc length), one tilt, rounded ends (2 × 2 numbers): 50 numbers; tilted socket prism and eye boss carried rigidly in the spine's frame; side seam grooves (band lofted station by station in the spine's frame, minus an inset skin) | 30.1 × 29.6 × 90.7 | 15.8 cm³ | 2.3 MB | coarse |
| leg-arm | `spideybot_L_leg2.stl` | in the plate's 45° frame, on ARM_SPINE (cubic spline through 5 points: crank pin, neck root, pivot, middle, knee): hub = polar spline (18 radii) between two fitted planes, front step, axle hole Ø5.5, ring, 3 gears, tab tube (ellipse 6.2 × 4.2 + 3 rings) and tab 12.1 × 3.8 × 3.8, all rigid at the spine's start; neck = loft of 12 superellipse sections normal to the spine (7 control rows: 21 numbers, exponent 2.6) + a straight root tube into the hub + 3 rings; flare = ruled loft of 5 hexagons carried at their own place on the spine into the 7 × 9 × 11.9 block (rigid at the knee); back boss. Spine + neck: 39 numbers | 36.4 × 39.9 × 48.5 | 5.6 cm³ | 3.6 MB | coarse |
| leg-blade-r | `spideybot_R_leg1.stl` | leg-blade mirrored about x = 35.45 (`side="R"`; jenscolt's R meshes are the L ones mirrored there to 0.0000 mm, probe) | 30.0 × 29.5 × 90.5 | 15.8 cm³ | 2.8 MB | coarse |
| leg-arm-r | `spideybot_R_leg2.stl` | leg-arm mirrored the same way | 36.4 × 39.9 × 48.5 | 5.6 cm³ | 3.6 MB | coarse |

## Fidelity (`tools/mesh_ref.py compare`, max on p99.9)

Limits: the blade has the size-relative default (p95 ≤ 0.91, max ≤ 1.83 mm). The arm (left and right) has its own,
p95 ≤ 0.6 / max ≤ 1.25 mm: an exception Morante approved on 2026-11-20 (`spec.json` → `exceptions`), since it
misses the default 0.5 / 1.0 mm by 0.09 / 0.22 mm.

| Part | part → ref max / p99.9 / p95 | ref → part max / p99.9 / p95 |
|---|---|---|
| leg-blade | 1.16 / 0.96 / 0.53 | 1.05 / 0.95 / 0.56 |
| leg-arm (on its spine) | 1.38 / 1.21 / 0.59 | 1.10 / 0.91 / 0.48 |
| leg-blade-r (vs R_leg1) | 1.16 / 0.94 / 0.53 | 1.15 / 0.95 / 0.56 |
| leg-arm-r (vs R_leg2) | 1.38 / 1.22 / 0.59 | 1.05 / 0.92 / 0.48 |

Earlier (pilot, limits then p95 ≤ 0.6 / max ≤ 1.5): blade v1 26 sections 1.12 / 0.47 and 1.26 / 0.52 (max / p95); arm v1
(horizontal stations, no spine) 1.12 / 0.56 and 1.05 / 0.49. The arm on its spine stays within those old limits too.

## Blade fidelity vs control sections

Each row: every skin number fitted at once (scratch probe: least squares of the both-way distance to v1's skin), the
blade then built with v1's socket, eye and grooves and measured with `tools/mesh_ref.py compare` (max / p95, mm; the r00 gate, another sampling, gives 0.98 / 0.51 and 1.04 / 0.55 for 6).

| Control sections | Skin numbers | part → ref max / p95 | ref → part max / p95 | Pass (pilot limits p95 ≤ 0.6, max ≤ 1.5) |
|---|---|---|---|---|
| 4 | 40 | 1.21 / 0.61 | 1.16 / 0.64 | no (old limits; yes at the default) |
| **6 (used)** | **50** | **0.93 / 0.53** | **1.10 / 0.56** | **yes** |
| 8 | 60 | 0.99 / 0.51 | 1.37 / 0.55 | yes |
| v1: 26 planar rows | ≈ 270 | 1.12 / 0.47 | 1.26 / 0.52 | yes |

The 6 sections pass with 0.04 mm to spare on p95; 8 gain only 0.01-0.02 mm: the rest of the error is v1's
own (the section fit, the simplified grooves and tip steps), not the interpolation.

## Edit test (`build.py --edit`)

The spines' 5 points change, nothing else. Blade: sections, socket, eye and grooves sit at the same arc-length fraction in
the spine's frame (N1's warp() convention, archived at the tag n2-on-meshes-2026-11-20: side vector made normal to the tangent, offsets in that
frame, scaled by the cross-section scale). Picture: `images/edit-demo.png`.

| Variant | Spine | Result |
|---|---|---|
| (a) N0 right-front blade (n0.leg_shape, P0, imported) | its 5 points on N0's curve at u 0, ¼ … 1; within 0.000 mm of it (a cubic through 5 points of N0's quadratic) | one valid solid, 3.96 cm³, 65.6 mm long (jenscolt × S would be 57.0: stretched ×1.15 along, × 0.6 across) |
| (b) length +10 % | z stretched ×1.1 about the top end | one valid solid, length ×1.099, 17.4 cm³ |
| (c) bow +3 mm | middle moved 3 mm outward (−y), sin(πu) | one valid solid, 15.9 cm³ |
| (d) arm on N0's right-front inner arm + upper leg (n0.leg_shape, P0, imported) | A0 (crank pin), A0 + 0.555 (P − A0) (the neck root at the original's knot fraction), P (pivot), the upper curve's middle, K (knee); 2.15 mm from N0's polyline at its corner at P, which a cubic through 5 points rounds (reported, not a limit) | one valid solid, 1.96 cm³, spine 62.3 mm (jenscolt × S would be 27.5: N0's upper leg is long) |

The arm maps arc length knot to knot (n1's breakpoints): the pivot point lands on N0's pivot, each stretch stays in
its own span. The hub, gears and tab hang rigidly from the crank pin's frame; the root tube (straight, knot 0 → 1)
keeps the neck joined to the hub however far the root moves.

What limits bending (judgement, not probed): the socket and eye are rigid (carried with the frame at one point), so a sharp bend under the
socket (radius under ≈ 15 mm at S 1) would tilt them off the skin; the grooves follow the spine station by
station but their depth is constant (0.9 × S), so at S < 0.5 they become thinner than one line. A spine whose
curvature radius gets below the blade's half-thickness (≈ 7 mm) would fold the loft.

## N1's entry point: `leg()`

```python
from build import leg            # cad/legs/build.py
blade, arm = leg(side="L", blade_spine=None, arm_spine=None, S=1.0, across=None, thick=1.0, sec=1.0)
```

- `side`: `"L"` = jenscolt's L meshes (the leg at +x in jenscolt's frame, N0's right side: what n1 bends today);
  `"R"` = its mirror image. With spines, the R leg is the L one built on the spines mirrored about the plane
  through their first point normal to `across`, then mirrored back: it lies on the same spines.
- `blade_spine`: 5 points (x, y, z) in the caller's frame, foot → blade top (n0.leg_shape's blade points reversed,
  rows u = 0, ¼ … 1). Sections, socket, eye and grooves at the same arc-length fraction.
- `arm_spine`: 5 points, crank pin A0 → neck root (A0 + 0.555 (P − A0)) → pivot P → upper middle → knee K. Mapped
  knot to knot.
- `S`: the cross-section scale (every offset from the spine: N0's S); with a spine `None`, the part in jenscolt's
  frame scaled by S about the origin.
- `across`: the leg plane's normal (n1's `side_new = cross(z, radial)`); default from the blade spine, cross(z,
  horizontal(foot − top)).
- Returns two build123d Solids. Pure function of its inputs, memoised (`functools.lru_cache`, 32 entries): same
  arguments → the same objects, so place copies (`loc * blade`) and never edit them. Cost ≈ 10 s per new call
  (blade 5 s, arm 5 s), 0.0001 s cached. Probed on N0's right-front spines at S 0.6: both sides, both parts one
  valid solid each.

## Frames

- Blade: origin (109.72, -68.46, 47.53), x = (0.768, 0.640, -0.004), z = (-0.216, 0.265, 0.940) (PCA of the mesh).
- Arm: u = (x - y)/√2, w = (x + y)/√2, z; built in (u, w, z) and turned -45° about Z (the mesh's flat faces are at
  exactly 45°). ARM_SIDE = w, the section's x axis: the same direction as the blade's x and n1's cross(z, radial).
- Right leg: the left one mirrored about x = 35.45 (MIRROR_X).

## Build

`build.py`: the four parts 14.7 s of geometry + export (blade and arm ≈ 5 s each, the right ones a mirror: 0.0 s;
the left STEPs 2.9 MB each) plus ≈ 5 s Python/build123d import. `--sweep`: both sides at S 0.65, blade thickness
0.8× / 1.2×, arm section scale 0.8× / 1.2×: all one valid closed solid, volumes in order (35 s). `--edit`: 74 s.

## Decisions

- Simplified: gear teeth (9 square teeth, 0.8 mm proud), ring bands (constant 1.2 × 0.45 mm), the lower diagonal end
  of the left seam groove, the shallow side steps near the blade tip, the hub's slight edge rounding.
- The arm's neck sections now stand normal to its spine (v1: horizontal); the neck's top section, tilted with the
  spine, pokes 0.7 mm above the block (48.5 mm tall vs 47.8): inside the default fidelity.
- The reference meshes are not watertight and carry internal faces (neck inside the block); the flare is fused to
  the block from z 72.5 as a compromise between the two directions of the distance.
