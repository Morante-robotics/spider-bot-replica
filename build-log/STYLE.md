# Build log style

How this repo's build log (`build-log.md` and `build-log/`) is written.

The log is outreach: a stranger (or the builder months later) must be able to follow the story by reading it top to
bottom, and to repeat any step. Write for that reader, not as a lab notebook.

## Layout of the file

1. `# <Robot> · Build log`, then a short paragraph: what the log is and how to read it (summary first in every entry,
   details folded, open items and glossary at the end), and a picture of the goal (the finished robot, or the model
   it starts from, credited).
2. `## Contents`: a numbered index. One item per topic section (link + one-line description), with its entries
   nested under it, oldest first: `- [Step](#anchor) · YYYY-MM-DD · <status>`. Then the items for Open items and
   Glossary, and a status legend: ✅ done · 🔄 in progress · ❌ ruled out · ↩️ reversed later.
3. Topic sections `## <Topic>` (e.g. Workshop, Carcass, Legs and drive), each opening with a short paragraph that
   tells the story of its entries so far (what was tried, what failed, where it stands), with one figure that sums
   it up when there were several attempts. Update it with each entry. A `[↑ Contents](#contents)` line closes every
   section.
4. Entries `### <Step name>` inside their section, oldest first. Keep step names stable: other entries link to their
   anchors.
5. `## Open items` (at the end): the **only** list of what is left on the build: `| Pending | Came up in | Phase |`,
   the second column a link to the entry. Add a row when an entry leaves something open; remove the row (never
   strike it out) when it is done, and say in the closing entry what it closed. Study, purchases and «Hecho cuando»
   stay in the private Seguimiento, not here.
6. `## Glossary` (last): `| Term | Meaning | First in |`, terms in the order they first appear, each linking to that
   entry. Add a term the first time an entry needs it. No pictures here: a reader meets the glossary before the
   parts exist, so a picture of later parts confuses; terms are illustrated in the entries themselves.

Place every figure where the reader is in the story: never show a part or result before the entry that makes it.

**Split (since 2026-11-13):** each topic lives in its own file `build-log/<n>-<topic>.md` (a `# <Robot> · <Topic>`
title, a line linking back to the index, then the `## <Topic>` section with its entries); `build-log.md` keeps the
intro, Contents (linking into the files), Open items and Glossary. A new topic is a new numbered file and a new item
in Contents. Links between files are relative (`3-legs-and-drive.md#anchor`, `../build-log.md#open-items`), and
paths to images and CAD from a topic file start with `../`. Check that no link breaks before committing.

**Keeping it small.** A topic file holds **one design**; a new design starts a new topic file. When a design or an
entry is superseded, its entries collapse to the heading, the status line, the «In short» box, at most one figure and
a `Full entry` link to the same anchor at an archive tag or commit SHA (a `blob/<tag-or-sha>/build-log/…` link, with
the anchor checked to exist there). The full text stays in git; nothing is lost. Aim for at most ~60 KB per topic
file, because agents read the latest one whole. Facts that other work needs (numbers, paths, accepted gaps) go to the
design's `datasheet.md` (e.g. `cad/robot/datasheet.md`), not into Open items, whose rows are one short line each.

## READMEs

READMEs describe what a folder holds and how to use it (files, how to rebuild, how to assemble, how to print). They
never hold status, results, dates or history, which change: link to the build log entry or to **Open items**
instead, and to generated files (e.g. `check-result.txt`) for numbers. Then a README only changes when its folder's
files or their use change.

- Root README: one row per capstone; its Status (Planned / In progress / Done) changes only when a capstone starts or
  ends.
- Capstone README: what the robot is, a goal picture, a link to the build log («Follow the build»), what each phase
  covers (no status column), and one line per folder. `tools/` is one line: each script explains itself in its
  docstring.
- No local paths (`/Users/…`) in any tracked file, including generated outputs: strip them before committing.

## Naming

- Folders, images, CAD parts, print files and Markdown: kebab-case, lowercase (`leg-front-left.step`,
  `test-leg-plate.3mf`, `drive-attempts.png`). Python files and the data they load: snake_case (importable modules
  cannot have dashes).
- Numbered items sort as text, so pad the number: `02-…`, `10-…`; build-log topic files keep a single digit (`3-legs-and-drive.md`).
- Versions as a suffix `-v2`, `-v3`; never «final», «new» or dates in a file name (dates live in the log).
- Generated files keep the name their script writes; rename the script output, not the file by hand.
- A rename fixes every link to the file in the same commit (`grep -rn old-name`).

## An entry

```
### Step name

**Phase N · Name · YYYY-MM-DD** · Status: <emoji> <a few words>

> **In short.** 2–4 plain sentences: the problem, what was done, what came out and what it means next.
> Someone who reads only these boxes must still follow the story.

<one paragraph of context if the entry needs terms or background: why this step, what came before>

#### Steps            (numbered; enough to repeat it; commands go in a <details> "How to reproduce")
#### Result           (figures + a short table + what it proves against the prediction)
#### Decisions        (what was chosen and why, in one or two lines each)
#### Next             (only in the entry in progress: the how of its open items — files, hardware;
                     the items themselves are rows in Open items)
```

Only the parts that apply. Headings `####` so they do not clutter the contents of GitHub's outline.

- **Plain words first.** Explain a variable or mode the first time (`r`, `H`, `XC`, «slides at crank»…) or leave it
  in the reproduce block. No internal jargon in the summary.
- **Tables:** at most ~5 columns in the text. Wider tables, raw search ranges, parameter dumps and command lines go
  into `<details><summary>…</summary>` (blank line after `<summary>` so Markdown renders inside).
- **Numbers** only from measurements, the simulator or the builder's notes; never invented. A failure is written as it
  is, with its likely cause.
- **Leave out** notes about how the author and the AI worked («written in Spanish, then translated», «offered and not
  picked», «(name)» attributions), caveats about the docs themselves, and «first time» remarks.
- **When a later entry reverses a decision,** set the old entry's status to ↩️ and add one line under its decision
  linking to the new one. When an entry closes an open item, remove its row from Open items and say so in the entry. When an entry stops
  being the one in progress, drop its Next section (its items stay in Open items).
- English.

## Figures

Every image or GIF has a numbered caption that says what to look at:

```html
<img src="images/x.jpg" width="480" alt="Short description">

*Fig. 3 · What it is. What to notice in it.*
```

- Numbering restarts in each entry (Fig. 1, 2…); refer to figures by number in the text.
- Widths: photos and square renders 400–480; screenshots 640; wide plots and diagrams no width (they fill the
  column). Never let a portrait photo show at full width.
- Photos of one entry go together in one gallery: an HTML table, two per row, each caption in the cell below its
  photo, numbered in reading order. Do not leave one photo of the set on its own further down:
  `<table><tr><td width="50%"><img src=…></td>…</tr><tr><td><em>Fig. 2a · …</em></td>…</tr></table>`.
- GitHub videos (`https://github.com/user-attachments/…`) cannot be resized: put a caption line before them.
- GIFs under ~3 MB; prefer fewer frames or a smaller size to a heavier file.
- Labels inside generated figures read their values from the CAD code, never hard-coded.

### Diagrams

Every entry that involves
putting things together, measuring, or a mechanism moving gets **a diagram made for it**, not just a render or a
photo. A diagram is drawn to explain one thing, with labels and arrows; a plain render is not one.

| The entry is about | Draw |
|---|---|
| An assembly | Assembly steps: one panel per step, parts already in place in grey, the incoming part in colour lifted out along its direction, an arrow for the motion, the finger or tool, each panel numbered and named. Plus an exploded view with every part and fastener labelled (name, size: «M3 × 16 pin»). |
| A measurement or a fit | A dimensioned section or view: the measured size as a dimension line with its value, the nominal value next to it, the clearance shaded; where the caliper or ruler goes. |
| A mechanism | The motion: positions overlaid or a strip of frames, arrows for the direction of travel, the input and output named, the ratio or stroke written on it. |
| A test result | Prediction against measurement in one plot or table-like figure, with the pass band shaded. |
| A print plate | The plate preview with each part's orientation and the support marked; support grams per part. |
| A failure | The part as designed beside what happened, with the problem circled and a one-line label. |

How:
- Make them with `tools/figures.py`, the house style: `draw()` renders meshes with correct depth and outlines,
  `assembly_steps()`, `exploded()` and `measure_sheet()` make the standard figures from a design's `cad_verify`
  spec (`python tools/figures.py <spec> <dir> [--lang es]`), `callout()`, `side_labels()` and `move_arrow()` add
  labels and arrows. Never matplotlib's 3D axes (`Poly3DCollection`): they sort whole parts, so a part behind another
  is drawn on top (the gear train test figure, 2026-11-12). A schematic can be a hand-drawn SVG.
- The script goes next to the CAD code (or `tools/`), so the figure can be made again when the design changes.
- One idea per diagram. Large readable labels (≥ 10 pt at the width it shows), plain names (the part names used in
  the text), consistent colours for the same part across the figures of an entry, white background.
- Look at every diagram before using it (Read the PNG): nothing overlaps, every label points at the right thing.

Check the result with GitHub's renderer before committing:
`python3 -c 'import json,sys;print(json.dumps({"text":open(sys.argv[1]).read(),"mode":"markdown"}))' build-log.md | gh api markdown --input -`
