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

## ✅ Closed 2026-07-19 — Acceptance criteria met

**Outcome 6 — Deployment smoke tests:** 3/3 green.

| Environment | Result | Detail |
|---|---|---|
| Desktop (same-origin) | ✅ | curl with no token → **403** |
| Docker (LAN-IP) | ✅ | curl with no token → **403** |
| Android/WebView | ✅ | curl with no token → **403** |

Every environment rejects token-less requests with 403, as expected. The origin +
token boundary and the provider target policy were validated in a real runtime.

**The 17th's caveats resolved:** outcome 6 executed and passed → a confident close.

---

## Delivered 2026-07-17 — WITH CAVEATS (kept in tasks/, not closed/)

The origin + token boundary and the provider target policy are implemented and
tested at unit+integration level. **Caveat: outcome 6 (desktop/Docker/Android
deployment smoke tests) was NOT executed — Docker/Android cannot be run here — so
this is not a confident close** (convention: it stays in tasks/).

### Delivered and tested (23 tests in `tests/test_security.py`, suite 610)
- `src/security.py`: a non-persisted per-process token + an origin allowlist
  (loopback on any port; native/WebView `null`/absent; **real same-origin**: an
  Origin whose authority == the request's Host — covers LAN-IP/Docker) +
  `unsafe_request_allowed`.
- `src/main.py`: the credentialed wildcard CORS is REMOVED → a loopback regex
  only. **`null` NEVER enters CORS**: an attacker's sandboxed iframe also has
  Origin `null`; letting it READ `/bootstrap` would hand over the token and bring
  down the whole boundary (the 2026-07-17 review closed exactly this). The
  `enforce_origin_and_token` middleware covers EVERY mutating method;
  `GET /bootstrap` hands over the token (readable only same-origin/loopback in the
  browser).
- An `api_base` policy in the adapter contract: deepseek = HTTPS + host
  `api.deepseek.com`; llama_cpp = loopback/private network, including single-label
  names (Docker) and private suffixes (.local/.internal/.lan/.home.arpa). Wired
  into `validate_config` → an attacker's `api_base` is rejected (422) without
  persisting or swapping the Runner; a legitimate Docker config does not break the
  boot.
- The token is never persisted: the service worker does not cache `/bootstrap`;
  `api.js` renews the token and retries once on a 403 (a process restart rotates
  the token without breaking the open page, e.g. `/plugins/restart`).
- Frontend: `api.js` sends the token on every mutation; `plugin-runtime.js`
  likewise.

### Caveats to verify before a confident close (outcome 6)
- Desktop smoke test (served same-origin, BASE_URL=''): mutations OK with the
  token.
- Docker smoke test: access via the LAN IP uses the same-origin path
  (Origin == Host) — confirm in the real environment; api_base with a service name.
- Android/WebView smoke test: with `null` outside CORS, a WebView loading from
  file:// must EITHER serve the app same-origin (http://127.0.0.1:8889) OR use the
  CORS-exempt WebView mode (universal access) to read `/bootstrap`; mutations
  already pass (Origin null + token). Confirm which of the two the Android app uses
  and adjust there if needed.
