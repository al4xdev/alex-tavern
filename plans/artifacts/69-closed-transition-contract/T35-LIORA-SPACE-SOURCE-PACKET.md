# Archived blue-gate T35/T36 space packet

Source session: `plans/artifacts/p1-archive/null-P1-r1/sessions/7fd84e9a/`.
Quotes below come from `debug.jsonl` and `state.json`, not a generated
summary of the scene.

## T35, accepted Director decision (`debug.jsonl` line 322)

Before the beat, `CURRENT SCENE` lists `gate_blue: "quase fechado, fresta
apertada"`; its salon zone includes Liora Celestria. The decision emits:

> `Liora, com o bastão rúnico erguido, atravessa a fresta do portão azul sem
> hesitar, adentrando a escuridão.`

The same Director JSON has `zone_moves: null`. Its `scene_update` still says
`gate_blue: "quase fechado, fresta apertada"`.

## T35, persisted Narrator record (`state.json`, `history`, turn 35)

> `Liora, com o bastão rúnico erguido à frente do corpo, não hesita. Dá um
> passo firme, a capa branca roçando as bordas da passagem, e atravessa a
> fresta do portão azul. O metal quase a toca, mas ela se move com precisão,
> desaparecendo na escuridão do túnel.`

This is the accepted `prose` response at `debug.jsonl` line 325 and is present
verbatim in the final saved history for turn 35.

## T36, next Director request (`debug.jsonl` line 334)

`CURRENT SCENE` lists Liora Celestria among occupants of `Academia Real do
Primeiro Sino, Salão dos Quatro Arcos`, not among occupants of `túnel da equipe
azul`. The request's character directory maps `ID=C7` to `NAME=Liora
Celestria`. T36's Director `zone_moves` is also `null`.

## T37, later state catch-up (`debug.jsonl` line 344)

The Director now says:

> `Liora, já do outro lado do portão, não é mais visível; a runa em seu bastão
> emite um pulso de luz que some na escuridão do túnel.`

Its `zone_moves` includes `"C7": "túnel da equipe azul"` alongside four other
team members. This later move does not change what T36's Director received.
