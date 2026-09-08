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

### M5 — Tests & deploy ◐ PARTIAL
- [x] Test suite — 47 tests covering URL parsing, markdown conversion, auth,
      lockout, and route-level access control. `python -m pytest`.
- [ ] Deploy to Dokku on pi5. **HTTP only — LAN-only host, no Let's Encrypt.**
      Not started; needs a Charles decision on whether this replaces the
      railway.app deployment referenced in the old README.

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
- Deploy target: pi5 Dokku, or leave it local? The old README mentions
  railway.app.
- True streaming (M4) — deferred; the spinner may well be enough.
- No default admin account any more, so an existing deployment needs `USERDB`
  set before it will accept a login.
