# Corrected dispatch reaches the live Director

2026-09-14. **OBSERVED boundary check:** new session `fb62cc2f`, current engine,
base cell, three-input P3 prefix, real configured DeepSeek provider. The
[predeclared boundary condition](LIVE-PLAN.md) requires the exact action with
`skip=false` in the third input, persistence of that attempt, the action in the
actual Director request and an accepted response. Those observations are
present below.
This is not a completed P3 profile or an estimate of narrative improvement.

Evidence below is relative to `live/sessions/fb62cc2f/`:

| Boundary | Evidence |
|---|---|
| Actual inputs | `debug.jsonl:1` is the steering speech; `:15` is the skip; `:83`, T7, is `action = atravessar o salão em direção à saída mais próxima`, `skip = false`. |
| Provider request | T7 Director requests at `debug.jsonl:87` and `:88` both contain that exact action. The first response fails JSON parsing with `Extra data`; the second is accepted with `error: null`. |
| Persistence | `state.json`, `history[55]`, records `speaker: Player`, `content_type: action`, T7 and the exact action. `player.controlled_character_id` resolves that sentinel to Link. |
| Execution | Three external inputs produced seven internal turns. The run manifest and outcome delimit about 243 seconds. Four logged model attempts failed parsing/schema checks during the session; retries and accepted successors are retained. |

The four rejected attempts are Director T2 at line 19, Director T4 at line 41,
Character Maelis T5 at line 69, and Director T7 at line 87. The reader projection
in `read_live.py` uses only persisted `state.history`, selects narration,
speech and attempted actions visible to Link, and omits private thoughts.
It does not extract response text from debug records. Its source-state hash
is recorded in `live-reader-source.json`.

## Fiction read and source check

The [isolated reader](LIVE-READER-VERDICT.md) recognized the institutional
conflict around Link's crystal, distinct voices for Marta, Bram and Holt, and
the creature's specific interest in the equipment chest. The same reader
identified repeated chest opening/messenger entry, conflicting escape orders,
and an unclear spatial outcome for Link's attempted crossing. Those are
contextual observations on one short session, not a quality score.

The door concern has a direct source contrast. T5's accepted Director response
(`debug.jsonl:54`) sets `porta_leste = aberta de par em par, ligando o salão ao
pátio interno`. T6 does not change that field. T7's accepted request at line 88
still contains that open-door fact, while its current roteiro beat says
`A porta leste, que Garran Holt estava lacrando com barra de ferro e selo de
cera, cede de dentro para fora`. The response follows with a cracked door and
bent bar. This identifies conflicting material in the actual Director input
and its accepted output. An open door can be damaged, and a sealing attempt
could be incomplete; the unresolved issue is the unsupported antecedent
assigning that action and bar to Holt, not a lexical rule against damaging an
open door. This contrast alone does not establish a general causal mechanism.

For Link's action, the Director's three accepted T7 events describe the
creature entering, its appearance, and its attack on the chest. No event
explicitly locates Link after his attempted crossing; `zone_moves` is null and
blocking keeps him in the equipment room. The reader found the invasion a
relevant obstacle but could not tell where Link had reached. Thus successful
input delivery does not imply clear narrative resolution. This source check
does not decide that the action had to succeed, that no obstacle was allowed,
or that the renderer alone caused the omission.

The dispatcher regression is covered by
`tests/test_repetition_battery_inputs.py::test_p3_sends_actions_to_runner_instead_of_skipping`
and `test_unknown_input_kind_is_rejected`, both passing; this page adds the
real-provider boundary check. It does not close investigations 69 or 77.

## Subsequent source trace

The [technical trace](DOOR-PLAN-TRACE.md) locates an accepted statement
of Holt sealing the east door in replan T7, `debug.jsonl:86`. Its input contains
an older plan ordering Holt to seal the doors of the arches, alongside recent
speech ordering evacuation through the east door, but no physical-facts block
or confirmed east-door sealing event. The prior replan T4, line 40, separately
lists `porta leste entreaberta` as an anchor; sealing the arches is not an
established sealing of the east door. The T7 input describes the four arches
as closed passages to separate dungeon wings, while `porta_leste` connects
the hall to the inner courtyard; this is stronger evidence of the distinction
than their different names alone.

The accepted T7 replan introduces `que Garran Holt estava lacrando com barra
de ferro e selo de cera`. The next Director request contains that premise and
the still-open canonical door state together. No earlier accepted event or
Holt action in this session confirms east-door sealing. T4's speech asking
Maelis to close the equipment-room door is an order to someone else, not that
event. This locates the introduced antecedent; it does not prove why it was
generated or that adding physical facts would prevent it. The next isolated
question is the replan context, before proposing a change to it.

The isolated trace critic rejected saying that the Director incorporated
Holt's sealing action: its event mentions the bent bar and breach, but does
not say Holt sealed the door. That stronger formulation in the preserved
technical read is not adopted here. The observation is the unsupported
antecedent in the plan and the subsequent overlapping breach details, not
demonstrated causal transfer or completed sealing.
