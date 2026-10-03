# Remaining ambiguous inputs: returned reasoning

See [the consolidated report](../69-order-versus-reasoning/RESULT.md) for
the interpretation, raw response IDs, reader objections and limitations.

Four fresh repetitions per case per mode, 16 direct curls, no retries.
Every reply was HTTP200 and schema-valid, with distinct IDs within each cell.
Every high reply returned nonempty reasoning_content.

| Confirmed case / expected act_completed | Disabled correct | High correct |
| --- | --- | --- |
| Failed attempt, portal still open / false | 4 of 4 | 4 of 4 |
| Portal closed after departure to canyon / true | 0 of 4 | 4 of 4 |

These are local observations. Canyon high-4 considered a new opening and
misordered the old plan against confirmed closure, then corrected its reading.
Its expressed reasoning supports an ambiguity hypothesis, not the hidden cause
of disabled replies. The subsequent production screen uses the new order.
