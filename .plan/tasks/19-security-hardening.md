# Task: Security hardening: local API origin boundary and outbound provider targets

**Status:** Explicit future work  
**Updated:** 2026-07-13

## Scope

Harden the unauthenticated FastAPI control plane when it is reachable from a browser. The priority
is preventing an untrusted web origin from changing server configuration or invoking other local
state-changing endpoints, then preventing a stored provider secret from being sent to an
attacker-controlled `api_base`.

## Current state

- `src/main.py` applies `CORSMiddleware` with `allow_origins=["*"]`, credentials, methods, and
  headers all enabled. There is no origin/referer guard or per-server access token.
- `PUT /config` accepts the complete browser-supplied configuration, preserves a blank secret from
  the existing stored configuration, persists it, and replaces the active Runner. This means a
  request can retain a configured cloud API key while replacing its `api_base`.
- `src/config.py` validates that every `api_base` is a non-empty string, but does not parse the URL,
  require HTTPS, restrict hosts, or associate a secret with a permitted endpoint.
- The shared LLM client derives the destination from that stored `api_base`; cloud adapters send
  their secret in the provider-specific authorization header.
- Provider adapters are now extensible by trusted plugins. Any final policy must be adapter-owned
  or otherwise support adapter-declared endpoint rules; a global DeepSeek-only allowlist would be
  incompatible with the current provider contract.
- Plugin, Experience, scenario, and session mutation endpoints are also unauthenticated. The
  plugin endpoints can install local ZIP paths, upload packages, activate/deactivate code, and
  request a process restart. They must be included in the state-changing boundary, not treated as
  a separate concern.

## Threat path

1. A user visits an attacker-controlled page while the Tavern server is reachable from the browser.
2. With permissive CORS, that page issues `PUT /config` and supplies an attacker URL for the active
   cloud provider while leaving its secret blank.
3. The server preserves the stored secret, accepts the new target, and the next model call sends
   the authorization header plus model request content to that target.

The same cross-origin access can mutate sessions, scenarios, plugins, Experiences, and application
configuration. CORS alone is not a complete authorization mechanism, so the server should enforce
the boundary for every unsafe method.

## Required outcomes

1. Define the supported browser origins for desktop, Docker, and Android/WebView deployments, and
   reject cross-origin unsafe requests at the server. Requests without `Origin` must have an
   explicit, documented policy for native/CLI clients.
2. Replace wildcard CORS with the minimal allowed origins/methods/headers needed by those
   deployments. Do not use credentialed wildcard CORS.
3. Require a server-generated, non-persisted access token (or equivalent same-origin proof) on all
   API mutations, including plugin and Experience administration. Deliver it only to the served
   application document/runtime configuration; never log it or persist it in browser storage.
4. Make `api_base` URL validation part of the provider adapter contract. Cloud adapters must allow
   only HTTPS targets and an explicit host policy; local adapters may declare their loopback/LAN
   policy. Any escape hatch for arbitrary targets must be explicit, off by default, and must not
   silently reuse a cloud secret.
5. Add tests for allowed local origins, rejected external origins, absent/invalid token, all unsafe
   route classes, allowed and rejected provider targets, blank-secret preservation, and assurance
   that rejected updates neither persist config nor replace the active Runner.
6. Run deployment-boundary smoke tests for the desktop server, Docker, and Android before closure.

## Non-goals

- This task does not turn the local single-user application into a multi-user authenticated service.
- Trusted in-process plugins remain trusted code once intentionally installed; the goal is to stop
  arbitrary web pages from reaching plugin-management endpoints.

## Delivered 2026-07-17 (Opus) — COM RESSALVAS (mantida em tasks/, não closed/)

Boundary de origem + token + política de alvo de provider implementados e
testados no nível unit+integração. **Ressalva: o outcome 6 (smoke tests de
deployment desktop/Docker/Android) NÃO foi executado — não dá pra rodar
Docker/Android aqui — então não é fecho confiante** (convenção: fica em tasks/).

### Entregue e testado (17 testes em `tests/test_security.py`, suíte 593)
- `src/security.py`: token por-processo não-persistido + allowlist de origem
  (loopback qualquer porta; native/WebView `null`/ausente) + `unsafe_request_allowed`.
- `src/main.py`: CORS wildcard credenciado REMOVIDO → regex loopback + `null`
  (WebView); middleware `enforce_origin_and_token` cobre TODO método de mutação
  (config/session/scenario/plugin/experience); `GET /bootstrap` entrega o token
  same-origin (cross-origin não lê → não forja).
- Política de `api_base` no contrato do adapter (`base.require_https_host` /
  `require_loopback_or_lan`): deepseek = HTTPS + host `api.deepseek.com`;
  llama_cpp = loopback/LAN. Ligada no `validate_config` → um `api_base` de
  atacante é rejeitado (422) sem persistir nem trocar o Runner. Isso fecha o
  threat path (repontar o segredo cloud) por construção — o host fica travado.
- Frontend: `api.js` busca o token do /bootstrap e o envia em toda mutação;
  `plugin-runtime.js` idem no observe.

### Ressalvas a verificar antes de fecho confiante (outcome 6)
- Smoke test desktop (served same-origin, BASE_URL=''): mutações OK com token.
- Smoke test Docker: origem/porta reais na allowlist.
- Smoke test Android/WebView (file:// → 127.0.0.1:8889, Origin null): o app
  lê respostas (CORS `null` permitido) E envia o token nas mutações. **Trade-off
  documentado**: permitir `null` no CORS deixa um iframe sandboxed atacante LER
  GETs (mutações seguem protegidas pelo token). Alternativa mais forte: servir o
  frontend do WebView same-origin (http://127.0.0.1:8889) em vez de file:// —
  aí `null` não precisa ser permitido. Decidir no smoke test.
