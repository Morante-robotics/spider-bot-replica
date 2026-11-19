# <Design> datasheet

The one page an agent reads first: status, where each topic lives (file and section), the commands. It points at
numbers in code (`../robot.py`, `../fits.py`, the build file's parameters) and never copies them. Updated by whoever
changes the design, in the same change.

## Status (<date>)

| Part | Built by | Spec | Last full check |
|---|---|---|---|

## Where to read, by task

| Task | Read | Section |
|---|---|---|

## Commands (from this folder)

```bash
(cd ../.. && uv run python tools/rounds.py validate cad/<design>)   # after every plan edit, until PASS
../../.venv/bin/python build.py --part <name>
../../.venv/bin/python ../../tools/cad_verify.py verify.py --smoke --only <part>   # after every fix (seconds)
../../.venv/bin/python ../../tools/cad_verify.py verify.py --out verify-result.txt --render images/verify   # once, at the end
(cd ../.. && uv run python tools/rounds.py round cad/<design> <n>)   # pack round n for the judge; then score
```
