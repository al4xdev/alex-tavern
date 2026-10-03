# Source read: six surviving redaction markers

**Observed in six archived records from four sessions, not a population rate.**
For each record, this read compared the persisted text with the same turn's raw
Director response and an earlier private thought. Re-running the current
`hidden_thought_tokens` function over each archived history prefix and turn
snapshot marked the replaced word as thought-only payload in all six cases.
The archived sessions predate the current session schema, so this was a focused
guard replay, not a replay of the full turn.

| session / turn | persisted channel | raw Director word → stored word | earlier private thought |
| --- | --- | --- | --- |
| `34390b86` T9 | Narrator report | Garran **grita** ordem → Garran **[indistinct]** ordem | Asword T6: “meu instinto grita para avançar” |
| `34390b86` T30 | Narrator report | Garran **grita** que a parede abriu → Garran **[indistinct]** que a parede abriu | the same Asword T6 thought |
| `34390b86` T31 | Narrator report | Asword se oferece para **segurar** a retaguarda → para **[indistinct]** a retaguarda | Asword T11: “Vou segurar a linha”; Nix T30: “Garran ficar pra segurar” |
| `00997daa` T9 | Narrator report | resolva o **problema** rapidamente → o **[indistinct]** rapidamente | Garran T5: “Esse Riven é um problema” |
| `d0cc98e5` T21 | narrated prose | sino **rachado** → sino **[indistinct]** | Maelis T3: “o sino rachado” |
| `c76037ff` T27 | narrated prose | **ainda** com o aço erguido → **[indistinct]** com o aço erguido | Asword T6: “meu pai ainda”; another thought T24: “Ainda que...” |

The first four records and the last prose record visibly lose ordinary words
that carry an action or grammatical relation. The cracked bell is different:
T3 public narration describes the *sound* of the bell as “metálico e rachado,”
while Maelis's thought calls the *bell* cracked. This read did not establish
that its physical condition was already public. Its
redaction may be a true containment catch. These examples do not establish a
general false-positive rate.

**Boundary theory.** If prior narration counted as globally known, a word
that first reached narration through a private-thought leak could become
eligible on later turns. The current known-token rule excludes narration for
that reason. These six examples support investigating token collisions, but
they do not establish that whitelisting all narrated words preserves thought
containment. Any candidate change needs a seeded private-detail control and
an explicit read of the resulting text, as well as marker counts.

Sources: `plans/artifacts/repetition-battery/{base-P2-r1,base-P1-r1,base-P1-r2}/sessions/{session_id}/{state.json,debug.jsonl}`;
`src/confidentiality.py` (`hidden_thought_tokens` and `known_tokens`);
`src/agents/narrator.py` (event redaction); `src/runner.py` (`_report_speech`).
