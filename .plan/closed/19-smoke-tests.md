# Task 19 — Smoke test script that ONLY YOU can run (outcome 6)

This is the only item between the task and a confident close. There are 3 environments, ~10 min
each. In all of them: success = the mutation passes WITH the normal app; an external `curl`
without a token gets a **403**. Any different result: note the step and the response body
and bring it to me — I will adjust it.

## 1. Desktop (served same-origin, BASE_URL='')

1. `uv run python -m src.main` and open `http://127.0.0.1:8889` in the browser.
2. Create a session, send 1 turn with speech, 1 undo. → Everything should work
   (the frontend fetches `/bootstrap` and sends `X-Tavern-Token` on every mutation).
3. Negative proof, in the terminal:
   `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8889/session/any/turn -H "Content-Type: application/json" -d '{"speech":"x"}'`
   → expected **403** (no token).
4. Restart the server with the tab open and send another turn → it should
   recover on its own (403 retry refetches `/bootstrap`), without F5.

## 2. Docker (access via LAN IP)

1. Start the container and access `http://<machine-ip>:8889` from ANOTHER
   LAN device.
2. Create session + 1 turn. → Should work through the same-origin path
   (Origin == Host); the token is sent along.
3. If the provider is local llama with the compose service name (e.g.,
   `http://llama:8080`): confirm that boot does NOT reject the api_base
   (single-label is allowed by the policy).
4. Negative proof: same curl as item 1.3 pointing to the LAN IP → **403**.

## 3. Android / WebView

There is a fork here that I cannot see from here — I need you
to tell me which of the two the app uses:

- **(A) WebView loads the app from `http://127.0.0.1:8889`** (same-origin):
  everything should work, just like on desktop. Just test session + turn.
- **(B) WebView loads from `file://`** (Origin `null`): `null` is outside the
  CORS on purpose (token theft). The `/bootstrap` only responds if the WebView
  is in universal-access mode. Test: if the app cannot even create a
  session, this is the case — tell me and I will send you the adjustment for the Android side
  (serving same-origin is the recommended path; exempting CORS in the WebView is plan B).

## When finished

Send me per environment: passed/did not pass + (if it failed) step and response.
3/3 green → I close 19 with confidence and migrate it to `closed/`.
