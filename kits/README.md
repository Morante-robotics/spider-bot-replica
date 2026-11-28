# Workshop kits

One kit per print-and-assemble step: what the print tests, what to print (and what not yet), every part and screw,
one picture per assembly step with what to do and how to know it is right, what to measure and what to film. It is
the page Morante has open on his phone at the bench.

| Kit | Step | Open |
|---|---|---|
| [01-batch-1-test-leg](https://github.com/Morante-robotics/spider-bot-replica/tree/batch-1-kit-2026-11-24/kits/01-batch-1-test-leg) | Batch 1 (scale 0.70, M2): the blue and yellow plates and leg-3, to test the leg snap and the M2 pilots; then the whole robot's assembly. The batch failed; the kit is archived at tag `batch-1-kit-2026-11-24` | archived |

Each folder holds `notes.json` (the text, written by hand), `kit.html` and its pictures (made by the tool). To remake
one after a design change:

    uv run python tools/workshop_kit.py cad/robot/verify.py kits/<NN-step> --notes kits/<NN-step>/notes.json

It prints `complete`, or the number of MISSING lines the notes still have to fill. `--embed` puts the pictures inside
the page, for a single file to send.
