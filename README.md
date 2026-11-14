# Capstone 1 · Spider-Bot

Part of [Robotics Capstones](https://github.com/Morante-robotics/robotics-capstones), my path to learning
robotics one robot at a time.

Replica of the Spider-Bot from Avengers Campus: 8 legs moved by a single motor, LED eyes, and it walks as soon
as it is switched on (no remote control).

**Hardware plan:** no microcontroller. An N20 gear motor drives the leg mechanism and the LED eyes (on their own
perfboard) light up, both powered by 4×AAA NiMH batteries in a holder with a built-in switch. 3D-printed in PLA at
120 % of the base model's size.

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
| [cad/carcass-jenscolt/](cad/carcass-jenscolt/) | Carcass base model by jenscolt, unmodified (CC BY-NC-SA) |
| [cad/carcass-120/](cad/carcass-120/) | Carcass parts repaired (watertight) and scaled to 120 %: the base for cuts and holes (CC BY-NC-SA) |
| [cad/layout/](cad/layout/) | What fits inside the body: battery holder and motor, print scale |
| [cad/legs/](cad/legs/) | Legs and pivot forks, modelled in code (build123d), and the whole drive placed by the simulator's kinematics with a collision check over a full turn |
| [cad/crankshafts/](cad/crankshafts/) | Four crankshafts with gears and the idlers that link them, with a 2D check of every mesh |
| [cad/gear-train-test/](cad/gear-train-test/) | Gear train test: a stand-alone spine and cap for the crankshafts and idlers, with its `cad_verify` spec |
| [cad/test-frame/](cad/test-frame/) | Test frame: a desk stand for one leg, its fork and a crankshaft, and the Onshape tutorial |
| [cad/base/](cad/base/) | Base v1: the carcass base with a band that lifts the body, the spine built in, fork pockets and a cap over the crankshafts (CC BY-NC-SA) |
| [cad/chassis/](cad/chassis/) | Chassis (base v2) and robot master model: the plan for the whole robot (motor seat, battery holder in the body, coupons), with its layout and mass scripts |
| [cad/clearance-test/](cad/clearance-test/) | Block and pin to find the hole clearance this printer needs for turning and sliding fits |
| [cad/](cad/) | The rules every design follows: axes, folder layout, what is kept in git; [`_template/`](cad/_template/) to start a new design |
| [cad/fits.py](cad/fits.py) | The measured clearances (fits) every design takes its holes, slots and gaps from |
| [hardware.md](hardware.md) | Screws, pins, motor, batteries: what each design uses and what is in the workshop |
| [measurements.csv](measurements.csv) | Every caliper measurement of a printed part, the source of the fits |
| [print/](print/) | Bambu Studio projects ready to print, with time and filament |
| [sim/](sim/) | Leg simulators: 2D foot paths of three leg types, the toy leg in 3D on the whole robot, and the N20 motor sizing |
| [tools/](tools/) | Scripts: `cad_verify.py` checks a printed mechanism before it is printed (collisions, fits against the measured clearances, whether every part is held, whether a finger or tool reaches every pin and screw); `figures.py` draws assembly and measuring diagrams; `workshop_kit.py` makes the one-page assembly sheet for the bench; `bambu_plate.py` lays out and slices plates; `print_report.py` measures support per part; previews, mesh repair and figure scripts. Each explains itself in its docstring; `tools/tests/` keeps the checks honest |

## Run the code

Install [uv](https://docs.astral.sh/uv/), then run `uv sync` here: it sets up Python 3.12 and every library at the
versions in `uv.lock`. Then `uv run python tools/<script>.py --help`, or `uv run python build.py` in a CAD folder.

## License

Code is licensed under the [MIT License](LICENSE). Texts, photos, videos and designs are licensed under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/),
except the carcass files based on [Spidey-Bot by jenscolt](https://www.thingiverse.com/thing:5196618), which are
CC BY-NC-SA like the original (see the `LICENSE.txt` in their folders).
