# Task 56 — Debug drawer e falsos badges de whisper no frontend

> **Status (2026-07-26): FECHADA COM CONFIANÇA.**
> Corrigida na branch `refactor/pre-1.0-cleanup`, com reprodução e validação em
> browser real nos viewports desktop e mobile.

## Sintoma

Ao ligar o debug, o frontend mostrava:

```text
Could not load debug log: bindTranslation is not defined
```

Depois de desligar o debug, muitos badges `🤫 whispered to ...` continuavam
visíveis no transcript. O comportamento ocorria tanto no PC quanto no PWA
mobile.

## Reprodução pré-correção

Playwright executado contra a sessão real `1cad8c55`:

| Estado | Desktop | Mobile |
|---|---:|---:|
| Drawer ativo após ligar debug | sim | sim |
| Toast `bindTranslation is not defined` | sim | sim |
| Drawer ativo após desligar debug | não | não |
| Toggle marcado após desligar | não | não |
| `display` do drawer após desligar | `none` | `none` |
| Badges de whisper ainda no transcript | 16 | 16 |

O drawer não ficava preso. O que permanecia eram badges do transcript sem
relação com o estado de debug.

## Causas confirmadas

### Dependência perdida na extração do drawer

O commit `6319304` moveu `makeCopyBtn` para `src/static/debug-drawer.js`, mas o
módulo importava apenas `t` e `translateDocument`. A função continuou chamando
`bindTranslation`, gerando o erro somente quando uma entrada real do log era
renderizada.

### Audience de zona rotulada como whisper

`renderHistory` tratava qualquer `TurnRecord.audience != null` como whisper. O
modelo atual também usa `audience` para percepção acústica de zonas e distingue
a origem em `audience_origin`:

- `whisper`: audiência confidencial explícita;
- `zone`: audiência calculada pela posição/acústica.

Todos os 38 registros com audience no estado final da sessão `1cad8c55` tinham
`audience_origin="zone"`. Por isso o frontend produzia 16 badges enormes
listando quase todo o elenco, apesar de não haver whisper explícito.

Isso não era vazamento do drawer nem conteúdo de debug persistente. Pensamentos
de Character continuam reader-visible por contrato: o README define o
transcript como apresentação literária e as fronteiras privadas valem entre os
agentes/personagens.

## Implementação

- `src/static/debug-drawer.js`: importa `bindTranslation` explicitamente.
- `src/static/app.js`: preserva `audience_origin` no buffer e renderiza `🤫`
  somente quando a origem é `whisper`.
- `src/static/sw.js`: shell cache avançado de `rpt-shell-v24` para
  `rpt-shell-v25`.
- testes: fixam o import, incluem o drawer na varredura i18n e distinguem
  whisper explícito de audience de zona.

Não houve mudança de backend, schema persistido, agência ou fronteira narrativa.

## Validação

- Playwright Chromium real em desktop `1440x900` e mobile `393x852` com touch:
  - ligar debug carrega o log sem toast de erro;
  - desligar remove `active`, desmarca o toggle e resulta em `display:none`;
  - zero erros de console;
  - zero falsos badges de whisper na sessão real.
- `48 passed`: frontend architecture, i18n e whisper UI.
- `node --check` em todos os módulos de `src/static/` e adapters.
- parsing de `src/static/index.html`.
- `git diff --check`.

## Resultado

O modo debug abre e fecha corretamente nos dois layouts, o log volta a
renderizar, e percepção acústica de zona não aparece mais como whisper no
transcript normal.
