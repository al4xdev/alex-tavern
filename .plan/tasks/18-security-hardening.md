# Task: Security hardening (CORS restriction and API Base validation)

**Status:** Explicit future work  
**README evidence:** N/A (Requested by User / Security Audit)

## Stated behavior

- Address the critical security vulnerability identified in the backend: **API Key Exfiltration and Chat Context Leakage via CORS/CSRF configuration manipulation**.
- **The Vulnerability:**
  1. The FastAPI backend has no authentication and is run on `0.0.0.0` or local loopback.
  2. CORS allows any origin (`*`), exposing the local server to cross-origin requests from any website running in the user's browser.
  3. An attacker's website can make a silent cross-origin `PUT /config` request to change the `api_base` of the DeepSeek (or other cloud) provider to a malicious server.
  4. The next time the user triggers an LLM turn, the backend sends a request to the attacker's server containing the **stored DeepSeek API Key** in the `Authorization` header, along with the full chat history, prompts, and thoughts.

## Mitigation Plan

1. **Restrict CORS policy:**
   - Remove wildcard (`*`) origins for write endpoints (`POST`, `PUT`, `DELETE`).
   - Restrict origin matching to local loopback domains/ports or the host's own origin.
2. **Implement API base domain validation:**
   - Enforce strict whitelisting of allowed domain patterns for cloud provider `api_base` settings (e.g., only allow `api.deepseek.com` or custom local network IPs).
   - Prevent setting arbitrary non-SSL or unverified URLs for cloud adapters unless an explicit command-line override flag (e.g., `--allow-arbitrary-api-base`) is passed.
3. **Verify Origin / Referer headers:**
   - Block any state-changing requests (`POST`, `PUT`, `DELETE`) where the `Origin` or `Referer` header indicates an external internet domain.
4. **Local Access Token (Optional but robust):**
   - Generate a single-use random session token when the server boots.
   - Inject this token into the index page and require it in an `X-Access-Token` header for all API calls, preventing CSRF requests from unauthorized browser tabs.

## Current repository state

- `src/main.py` registers the standard FastAPI CORS middleware with `allow_origins=["*"]`.
- The configuration schemas accept any arbitrary string for `api_base` without domain verification.

## Open questions

- **Android loopback compatibility:** When running on Android via loopback, does the webview origin require wildcard CORS permission, or can we restrict it to specific local schemes/ports?
