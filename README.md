# Capstone 1 · Spider-Bot

Replica of the Spider-Bot from Avengers Campus: 8 legs moved by a single motor, LED eyes, and it walks as soon
as it is switched on (no remote control).

**Hardware plan:** no microcontroller. A gear motor drives the leg mechanism and the LED eyes (on their own perfboard)
light up, both powered by 4×AA NiMH batteries in a holder with a built-in switch. 3D-printed in PLA.

**To replicate it:** follow the [build log](build-log.md) step by step. The [AI log](ai-log.md) records what was
designed with AI help and how it was checked.

## Phases

| # | Phase | Status |
|---|---|---|
| 0 | Workshop | In progress |
| 1 | Soldering and measuring | Pending |
| 2 | CAD and 3D printing | In progress |
| 3 | Mechanisms and legs | Pending |
| 4 | Motors, power and lights | Pending |
| 5 | Final build | Pending |

## Contents

| Folder | What |
|---|---|
| [cad/carcass-jenscolt/](cad/carcass-jenscolt/) | Carcass base model by jenscolt, unmodified (CC BY-NC-SA) |
| [tools/](tools/) | Helper scripts: [`stl_preview.py`](tools/stl_preview.py) renders and measures STL files, [`stl_turntable.py`](tools/stl_turntable.py) makes turntable GIFs |

## License

Same as the repo (MIT for code, CC BY-SA 4.0 for the rest), except the carcass files based on
[Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), which are CC BY-NC-SA like the original.
