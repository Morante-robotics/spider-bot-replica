# Spider-Bot · Build log

Every step of the build in order, written so that it can be repeated: what was done, with what, the result, and what
went wrong. Newest entries at the bottom.

| Date | Phase | Step |
|---|---|---|
| 2026-10 | 0 · Workshop | [Printer calibration](#printer-calibration) |
| 2026-11-08 | 2 · CAD | [Carcass base model](#carcass-base-model) |

## Printer calibration

**Phase 0 · Workshop · 2026-10**

Bambu Lab P2S Combo (with AMS) running its automatic calibration before the first print. All Spider-Bot parts are
printed in PLA.

https://github.com/user-attachments/assets/948dd098-af7a-4972-a0bd-290c17e0126f

## Carcass base model

**Phase 2 · CAD · 2026-11-08**

**Goal:** start the carcass from an existing faithful model instead of modelling it from scratch.

**Source:** [Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), the most faithful replica found
(CC BY-NC-SA). Others looked at: a stylised low-poly game asset on Sketchfab (CC BY-ND, so no modified versions
can be published; reference only) and the MyMiniFactory «Spider BOT» (an unrelated sci-fi miniature).

**Steps:**

1. On the Thingiverse page, **Download all files** (zip with 9 STLs, photos, README and license). Scripted downloads get
   HTTP 403.
2. Check every STL is valid and measure it: [`tools/stl_preview.py`](tools/stl_preview.py) prints the size of each part
   and renders the previews.
3. Open all 9 STLs at once in Bambu Studio to check they import.
4. Files, sizes and previews: [cad/carcass-jenscolt/](cad/carcass-jenscolt/).

**Result:** 9 binary STLs. The body is a hollow shell 96 × 110 × 66 mm. The base has posts and mounts inside. The
legs are static display parts.

![Carcass turntable](cad/carcass-jenscolt/images/body-turntable.gif)

![Carcass parts](cad/carcass-jenscolt/images/parts.png)

Bambu Studio imports them, but reports mesh errors (non-manifold edges and reversed faces); every file has some.

![Bambu Studio import](cad/carcass-jenscolt/images/bambu-studio-import.png)

**Decisions:**

- Carcass = jenscolt's meshes, edited in Bambu Studio (cuts, holes). Mechanism = new parametric parts in Onshape, with
  the body STL imported only as a size reference.
- The walking legs are designed new; jenscolt's legs give their outer look.

**Open:**

- Repair the meshes before cutting or drilling them (booleans fail on non-manifold meshes).
- Print scale. The motor, gearbox and 4×AA holder have to fit inside body + base; checked when the mechanism is
laid out in Onshape.
