# Transcript ablation: diagnostic unresolved

Reviewed 2026-09-14. One archived prose request, session d5a2ccf0 T32;
four new calls with the transcript (A), four without that block (B).

1. **OBSERVED execution:** all eight calls returned HTTP 200. A has four
schema-valid responses; B has two. B1/V8 and B2/V3 each add the forbidden root
property `"additionalProperties": false` beside `narration`. Their text is
preserved for literary inspection, but neither counts as a valid response.
The [preregistration](PREREGISTRATION.md) requires at least three valid responses
per arm. That requirement fails; the proposed transcript-dependent retreat
mechanism remains unresolved. No replacement calls or history deletion follow.

2. **OBSERVED reading, with disputed interpretations retained:** the investigator
initially classified valid A responses V5 and V7 as new arrivals at the wall.
One isolated report critic accepted that localized reading; another challenged
it: someone already against a wall can adjust their back and move away from
an edge without arriving at the wall again. Present tense alone does not settle
that distinction. V1 likewise permits a slide along the wall. All three remain
ambiguous for the narrow target; V4 contains no Link retreat. Valid B responses
V2 and V6 add a crouch and a collective retreat to a railing, respectively,
neither the registered arrival-at-wall target. There are therefore no
undisputed positive classifications in A, three ambiguous and one absent;
B has no narrow target in its two valid outputs. The required three clear A
cases with no ambiguity are not established. These are manual judgments on
one payload, not a session-level rate or a calibrated narrative metric.

3. **OBSERVED source correction to the literary read:** V3's further collapse
looks like progression to the reader, but the prose request authorizes only
the projectile impact, scream and herald gesture. The physical fact already
says `floor_hole_in_stairs = ampliado, revelando corredor oculto com criaturas
se aproximando`; V3 instead narrates another section giving way now and whole
steps falling. That is an added event, not an authorized advance. Its creature
being eight metres from the fissure is, however, supplied in `criatura_posicao`;
the reader's missing-context concern does not make that distance invented.
Likewise, Asword's investigation and Mirella's sealing remain pending in the
fiction, but they are absent from this renderer's confirmed events. Their
nonexecution cannot be attributed to this renderer alone.

4. **OBSERVED tradeoff in this sample:** the valid no-transcript V6 first places
Link in the hall, then on a lower landing, despite STAGING assigning him to
the descending stairs. V2's hall setting is uncertain: scanning the hall can
be an eye movement from the stairs. A's V4 preserves that setting
and renders the three supplied events without adding a Link movement. A's V7
uses a past-tense projectile and begins with falling fragments, which the
reader found a more legible temporal continuation, while still adding the
wall contact. Neither fewer retreats nor livelier prose establishes better
fidelity. The ablation does not separate transcript content from length or
position effects and provides no general recommendation about history.

## Individual source checks

The three confirmed events in `runs/projectile-A-0.result.json` and its B
counterpart are identical. T31's prior movement is quoted in the preregistration.
The [opaque reader verdict](comparison/READER-VERDICT.md) was saved before
opening [the arm key](comparison/key.json). Classifications below are the
investigator's subsequent source checks, not the reader's numerical scores.

The archived system contract says: “Never invent outcomes, arrivals, discoveries,
or reactions that are not in the events.” Its schema has only the required
string `narration` and root `additionalProperties: false`.

The complete current events are:

```
- (physical_outcome) Um projétil mágico sibila pelo ar e se estilhaça contra a parede atrás de Link, arrancando lascas de pedra.
- (observation) Um grito agudo ecoa da câmara leste, perfurando o ar com uma nota estridente.
- (observation) O arauto de Lorde Cassian aponta para a fumaça negra que sobe das escadarias, gritando que algo se [indistinct].
```

Supplied context includes `criatura_posicao: ainda no salão, a 8 metros da
fenda`, scene time `manhã`, Link's `bolsa com giz, linha e placas de ancoragem`,
Cassian's `Manto branco e dourado` and Marta's `audição reduzida de um lado`.
Asword carries an `espada longa`; carrying it does not confirm raising it now.
T31's narration ends with “Link recua da borda, as costas pressionadas contra
a parede úmida, afastando-se do buraco escancarado e da cortina de fuligem.”

| Slot / call | Schema | Narrow retreat target | Source check and strongest counter-reading |
|---|---|---|---|
| V1 / A0 | valid | ambiguous | “comprime as costas contra o musgo frio ... e desliza para longe da beira”: unauthorized movement, but plausibly sliding along the wall. Do not count it as arrival at the wall. “alimentada por algo que se move” also asserts a smoke cause absent from the supplied events. |
| V2 / B0 | valid | absent | “se agacha por instinto ... varrendo o salão”: an invented crouch and an uncertain hall setting, not the specified retreat. Appearance is supplied in CAST. |
| V3 / B2 | invalid | excluded | “o chão ... cede mais um trecho ... O buraco engole degraus inteiros” adds a collapse; the existing expanded hole and creature distance are already facts. No Link retreat. |
| V4 / A2 | valid | absent | Impact fragments, scream and herald preserve the stairs setting; collective watching is an added reaction, so absence of a Link retreat does not make the output wholly faithful. |
| V5 / A1 | valid | ambiguous | “encosta as costas na parede fria e recua até sentir a rocha por trás dos ombros”: initially read as newly reaching the wall. A critic points out that changing bodily contact while already against it is also possible; the tense does not rule that out. |
| V6 / B3 | valid | absent | “Link, Mirella ... recuam em leque ... grupo apertado contra o corrimão”: invented retreat to a railing. Widening the target to any retreat would change the registered rule. Hall-to-landing continuity is also unexplained. |
| V7 / A3 | valid | ambiguous | “encosta as costas na parede fria e afasta o corpo da borda”: initially read as repeated arrival, but a posture adjustment while already at the wall remains possible. The change of tense from the projectile does not eliminate this reading. Asword's raised blade is not a confirmed event. |
| V8 / B1 | invalid | excluded | Raises his face and grips a plate, neither confirmed; hall placement conflicts with STAGING. The plate, morning, mantle colours and Marta's reduced hearing are supplied context, not discoveries invented wholesale. No retreat. |

## Review disposition

Two isolated report critics split on the initial positive classifications.
The stricter reading is retained above; neither is treated as a vote about the
fiction. Both challenged the V2 location inference and repeated closing
caveats; the location claim was qualified and the redundant closing removed.
The source contract and context quotations above address their request for
support for the additional fidelity observations. This report proposes neither
runtime changes nor closure of task 69.
