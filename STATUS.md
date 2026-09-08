# YoutubeSummary — Status

**Last updated:** 2026-09-08
**Scope agreed:** Full overhaul (~1 week), OpenAI-only AI layer, transcript
fallbacks limited to free fixes.

---

## Milestone map

### M0 — Discovery & safety net ✅ DONE (2026-09-08)
- [x] `.env` (live `OPENAI_API_KEY`) was **staged for commit** — untracked via
      `git rm --cached`, added `.env` + `.claude-profile` to `.gitignore`.
      Never actually committed, so **no key rotation needed**.
- [x] Created `.venv`, installed deps (project had none installed; app could
      not run at all).
- [x] **Verified transcripts still fetch** from this machine —
      `youtube-transcript-api` 1.2.4 works on real videos. The project's
      biggest risk is retired. pi5 is a LAN/residential IP, so deploy should
      behave the same as local.
- [x] Pulled **live** model + pricing data (not training data).

### M1 — Make it run correctly ✅ DONE
Goal: a working app demoable in the browser, end-to-end, against a real video.
- [x] Fix `youtuber.get_id()` — missing comma at `youtuber.py:31-33` silently
      concatenates two prefixes, so `youtu.be/...` and `m.youtube.com` URLs
      return a garbage video ID.
- [x] Replace HTML-scraped `get_title()` with the supported **oEmbed** endpoint.
- [x] Stop double-fetching: `get_transcript()` calls `get_title()` internally.
- [x] Regenerate `requirements.txt` from reality (see version table below).
- [x] Verify in Chrome DevTools against a real video.

### M2 — AI layer (OpenAI only) ✅ DONE
- [x] Port to the **Responses API** with `reasoning.effort`.
      `max_tokens` is rejected by current models — must use
      `max_completion_tokens` (Chat) / `max_output_tokens` (Responses).
- [x] Model selection + a documented default.
- [x] Markdown-fence / stray-prose tolerant parsing of LLM output.
- [x] Replace hand-rolled `md2html.py` with the `markdown` library.
- [x] Move error markup out of `/result` and into a template.
- [x] Real error handling for API failures (currently none — a 500 is raw).

### M3 — Auth & security ✅ DONE
- [x] Hashed passwords (werkzeug) instead of plaintext in `USERDB`.
- [x] Drop the `admin/admin` default, or force a first-run change.
- [x] CSRF protection; `Secure`/`HttpOnly`/`SameSite` cookie flags.
- [x] Remove `time.sleep(5)` on failed login — with `gunicorn -w 1` it is a
      one-request denial of service.
- [x] Fix `before_request` so it doesn't gate `/static`.

### M4 — UX ◐ PARTIAL
- [x] Progress feedback — submit button shows a spinner and "Summarizing…".
- [x] Design refresh (Bootstrap 5.3), mobile layout verified at 390px.
- [ ] True token streaming (the request is still one blocking POST). Only worth
      doing if the current spinner proves insufficient in real use.

### M5 — Tests & deploy ✅ DONE
- [x] Test suite — 47 tests covering URL parsing, markdown conversion, auth,
      lockout, and route-level access control. `python -m pytest`.
- [x] Deployed to Dokku on **pi4** at http://ytsummary.pi4.mcguinness.ai
      **HTTP only — LAN-only host, no Let's Encrypt, this is correct.**

#### Deployment notes
- Git remote: `dokku` → `dokku@pi4.mcguinness.ai:ytsummary`. Deploy with
  `git push dokku main`.
- pi4 is **arm64**, where Dokku refuses the herokuish builder and falls back to
  a `pack` builder that isn't installed. Hence the `Dockerfile` and
  `dokku builder:set ytsummary selected dockerfile`. A buildpack deploy cannot
  work on this host.
- Dokku read `EXPOSE 8000` and mapped `http:8000:8000`, serving on port 8000 and
  404ing on 80. Corrected with `dokku ports:set ytsummary http:80:8000`.
- nginx proxy read/send timeouts raised to 300s to match the app's own timeout.
- Config vars set on the host: `OPENAI_API_KEY`, `SESSION_KEY`, `USERDB`,
  `PYTHONUNBUFFERED`. `HTTPS_ONLY` is deliberately unset — the session cookie
  must not be marked Secure over plain HTTP.
- Login: user `charles`. Password was generated at deploy time and given to
  Charles in-session; rotate with `python userauth.py <user> <pass>` then
  `dokku config:set ytsummary USERDB='...'`.
- Build takes several minutes on the Pi. Verified end-to-end after deploy:
  login, transcript fetch, and a real summary (~7s, $0.0005).

---

## Reference: live OpenAI data (fetched 2026-09-08)

All four current-generation models: **1.05M context, 128K max output**,
reasoning effort levels none→max.

| Model | Input $/M | Output $/M | Notes |
|---|---|---|---|
| `gpt-6-astra` | 10.00 | 50.00 | Most capable |
| `gpt-5.6-sol` | 4.00 | 20.00 | Promo pricing thru 2026-11-21 |
| `gpt-5.6-terra` | 2.00 | 12.00 | Balanced |
| `gpt-5.6-luna` | 0.20 | 1.20 | Cheapest modern; ~<1¢ per summary |

Verified empirically against the account key:
- `max_tokens` → **400 error**, use `max_completion_tokens`.
- Responses API + `reasoning={"effort": ...}` → works.

Installed versions vs. old pins in `requirements.txt`:

| Package | Old pin | Installed |
|---|---|---|
| openai | ~=1.37.0 | **3.9.0** |
| Flask | ~=3.0.3 | 3.1.3 |
| gunicorn | ~=22.0.0 | 26.2.0 |
| youtube-transcript-api | ~=1.2.3 | 1.2.4 |

---

### M6 — Follow-on features ✅ DONE (2026-09-08)
- [x] `DISABLE_AUTH=true` removes the login entirely. Set on pi4, where a login
      screen on a LAN-only box is just ceremony. Warns at startup, bounces
      `/login`, hides the log out button. `USERDB` is unused when it's on.
- [x] Chat with the transcript, on every result page. `/chat` takes JSON,
      answers from the transcript with `[HH:MM:SS]` citations, and declines to
      answer from outside knowledge.
      - Conversation is held in the browser and posted back each turn, so the
        endpoint is stateless and stays correct across both gunicorn workers.
        A cookie wouldn't fit a transcript, and an in-process cache wouldn't be
        shared between workers.
      - History is trimmed to `MAX_HISTORY_MESSAGES` and role-filtered server
        side, so a client can't inject a forged system turn.
      - `youtuber._fetch_transcript` is now memoized (chat re-asks for the same
        transcript every turn): 1.03s → 0.000s on a repeat.

## Decisions taken
- **Ollama / HuggingFace / DeepInfra providers deleted** (Charles, 2026-09-08).
  OpenAI is the only provider. `ollama.py`, `hf.py`, `deepinfra.py`,
  `open_ai.py` and `md2html.py` are gone; `llm.py` replaces them.
- **Default model: `gpt-5.6-luna`**, user-overridable per summary from a
  dropdown, or globally via `OPENAI_MODEL`.
- `md2html.py` replaced by the `markdown` library. It could not handle the
  2-space nested bullets models emit, so `summarizer.normalize_list_indents()`
  rescales list indentation to the 4 spaces Python-Markdown needs. This is the
  one piece of custom markdown handling left, and it is unit-tested.

## Open threads
- The old README referenced a railway.app deployment. If one is still running,
  it is now redundant and should be shut down — not checked.
- True streaming (M4) — deferred; the spinner may well be enough.
- No default admin account any more, so an existing deployment needs `USERDB`
  set before it will accept a login.
