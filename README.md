# Capstone 1 · Spider-Bot

Part of [Robotics Capstones](https://github.com/Morante-robotics/robotics-capstones), my path to learning
robotics one robot at a time.

Replica of the Spider-Bot from Avengers Campus: 8 legs moved by a single motor, LED eyes, and it walks as soon
as it is switched on (no remote control).

**Hardware plan:** no microcontroller. One small gear motor drives the leg mechanism and the LED eyes light up.
Since 2026-11-17 the robot is being redesigned looks-first, with the toy as the reference: a smaller motor and
smaller batteries (button cells, like the toy's) so the whole robot can shrink. The earlier design (N20 motor,
4×AAA, 120 % scale) is kept in the [archive tag](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17).

<img src="cad/carcass-jenscolt/images/jenscolt-photo-2.jpg" width="480" alt="Spidey-Bot by jenscolt, the model this replica starts from">

*The starting point: [Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), a static display model
(photo: jenscolt, CC BY-NC-SA).*

**Follow the build:** the [build log](build-log.md) tells the story step by step, dead ends included, so it can be
repeated. Its contents show where each step stands, and its **Open items** list what is left. The
[AI log](ai-log.md) records what was designed with AI help and how it was checked.

## Phases

| # | Phase | What it covers |
|---|---|---|
| 0 | Workshop | Printer and tools ready |
| 1 | Soldering and measuring | Soldering and multimeter practice |
| 2 | CAD and 3D printing | The carcass, Onshape, print settings |
| 3 | Mechanisms and legs | The legs and the drive from one motor |
| 4 | Motors, power and lights | The N20 motor and its gearing, batteries, LED eyes on perfboard |
| 5 | Final build | The whole robot walking |

## Contents

| Folder | What |
|---|---|
| [cad/carcass-jenscolt/](cad/carcass-jenscolt/) | Carcass model by jenscolt, unmodified (CC BY-NC-SA): the looks reference, legs included |
| [cad/](cad/) | The rules every design follows: axes, folder layout, what is kept in git; [`_template/`](cad/_template/) to start a new design |
| [cad/fits.py](cad/fits.py) | The measured clearances (fits) every design takes its holes, slots and gaps from |
| [hardware.md](hardware.md) | Screws, pins, motor, batteries: what each design uses and what is in the workshop |
| [measurements.csv](measurements.csv) | Every caliper measurement of a printed part, the source of the fits |
| [print/](print/) | Print settings for this printer |
| [sim/](sim/) | The toy leg in 3D (`toy_leg_3d.py`, the chosen geometry in `toy_leg_3d_rows_cad.json`), 2D foot paths and the motor sizing |
| [tools/](tools/) | Scripts: `cad_verify.py` checks a mechanism before it is printed; `figures.py` draws assembly and measuring diagrams; `workshop_kit.py` makes the assembly sheet for the bench; `bambu_plate.py` lays out and slices plates; `print_report.py` measures support per part; mesh repair and previews. `tools/tests/` keeps the checks honest |
| [Archive](https://github.com/Morante-robotics/spider-bot-replica/tree/pre-redesign-2026-11-17) | Everything up to the redesign: base v1, test rigs, gear train tests, chassis A–E, legs v1–v2, print plates. The build log links there |

## Run the code

Install [uv](https://docs.astral.sh/uv/), then run `uv sync` here: it sets up Python 3.12 and every library at the
versions in `uv.lock`. Then `uv run python tools/<script>.py --help`, or `uv run python build.py` in a CAD folder.

## License

Code is licensed under the [MIT License](LICENSE). Texts, photos, videos and designs are licensed under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/),
except the carcass files based on [Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), which are
CC BY-NC-SA like the original (see the `LICENSE.txt` in their folders).
