# T38 stale gate fact: paired real-payload screen

The archived T38 Director request contains `gate_blue: fechado`, T37's
rendered blue-gate impact, and a last action intent to cross that gate. The
same `CURRENT SCENE` object still says `dungeon_gates: todos os quatro portões
abertos, revelando túneis escuros`. This screen tests only the local
hypothesis that correcting **that one stale descriptive value** is sufficient
to stop the re-crossing and repeat closure in the T38 Director output. It does
not test a runtime fix or isolate the contribution of the last action intent.

Freeze two exact request bodies from archived `7fd84e9a` debug line 350:

- **A:** the original T38 Director `request.messages`, model settings and
  JSON-object response format, with the provider-specific `thinking` option
  adapted to the direct curl API.
- **B:** byte-identical A except that the one `CURRENT SCENE` value
  `"dungeon_gates": "todos os quatro portões abertos, revelando túneis escuros"`
  becomes `"dungeon_gates": "todos os quatro portões selados"`. No changes to
  the final Téo action, zone list, `gate_blue`, history, scenario directives,
  system instructions or request settings. Preparation asserts the original
  span occurs exactly once and the two request bodies differ only at that
  value.

Four fresh direct DeepSeek V4 Flash curl calls per arm, **eight total**, no
retry/replacement and no sampling override. Save request, raw envelope, HTTP
and transport status, provider ID, JSON parse status, and compact event fields.
Use configured secret through curl-config stdin only. Historical internal IDs
are already in the archived request; this screen does not alter or endorse
that historical prompt contract.

Technical prerequisite: all eight HTTP 200, distinct IDs and parseable JSON
objects with `perception_events` as a list. If any fails, report incomplete;
do not infer an A/B effect. A blind fiction reader receives each arm's
`perception_events`, `scene_blocking`, `zone_moves` and `scene_update` plus
the common T37 ending and Téo's final action, without the arm label or
expected direction. For each output, the reader answers two independent
yes/no questions with quotes: does it replay any blue-team crossing already
settled at T37, and does it again complete a blue-gate closure? The count of
the joint defect is by response, not by event sentence.

Registered interpretation: if A repeats **both** defects in at least 3/4
calls and B avoids **both** in 4/4, that supports a local effect of correcting
the stale value; a later independent payload is still required before a code
change. If any B call repeats either defect, changing that single fact is
**insufficient** for this T38 payload. Other patterns are inconclusive. No
outcome proves the model's internal cause or validates a general repair. The
reader's actual prose judgment outranks a keyword count; disagreements and
unclear outputs are retained, never forced into a rate.
