# _template · plan

Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.

**A 30 × 30 mm frame with a 10 mm block held in its window by a ledge and a screwed cap; nothing moves.**

Level N2 · purpose: Demo: a block held in a window of a frame · pass: the block drops into its window and lifts out by hand

## Part list

| Part | Role | Why separate | g | Print orientation |
|---|---|---|---|---|
| frame | the ground part, holds the block | prints flat, the block prints on its own | 4 | flat face down |
| example | block in the frame's window | goes in after the frame | 1 | flat face down |
| cap | stops the block lifting out | screwed on, so a fix reprints a gram | 1 | flat face down |
| screw-m3 | holds the cap |  |  |  |

## Joint table

| Joint | Parts | Type | Held | Fit | In from | Apart by |
|---|---|---|---|---|---|---|
| block-in-window | example ↔ frame | slide | +x window wall · -x window wall · +y window wall · -y window wall · +z cap · -z ledge at the window's foot | fits.WINDOW | +z | unscrew the cap, lift out |
| cap-on-frame | cap ↔ frame | screw | +x screw · -x screw · +y screw · -y screw · +z screw head · -z frame top face | fits.STEEL | +z | unscrew |

## Assembly sequence

| Step | Part | From | Hand or tool | Already in | How you know |
|---|---|---|---|---|---|
| 1 | frame | None | hand |  | flat on the table |
| 2 | example | +z | hand | frame | sits on the ledge, flush with the top |
| 3 | cap | +z | hand | frame, example | covers the block's edge |
| 4 | screw-m3 | +z | 2.5 mm hex key | cap | head flush, cap does not turn |

## Alternatives

- **what holds the block in +Z**: a cap screwed on top / a pin across → **a cap screwed on top**, a fix reprints a gram

## Acceptance

| Id | Item | How | Check | Priority |
|---|---|---|---|---|
| a1 | the block is held in every direction | verify | retention | must |
| a2 | the block fits its window with the WINDOW fit | verify | joints | must |
| a3 | the block drops into its window and lifts out by hand | print |  | must |
