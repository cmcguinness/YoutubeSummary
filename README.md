# YouTube Summarizer

Ever get tired of watching long YouTube videos? Wish they'd just get to the point?

Yeah, me too.

So I wrote this app to demonstrate how AI can "solve" this problem for me. It will take a
transcript from a video and ask AI to summarize it to whatever length I choose.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill it in, see below
python app.py             # picks a free port and opens a browser
```

### Configuration

Settings are read from the environment, or from a `.env` file in the project root.
**`.env` is git-ignored — never commit it.**

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes | Your OpenAI API key |
| `USERDB` | yes | JSON object of `{username: password_hash}` |
| `SESSION_KEY` | yes in production | Flask session secret. If unset, each worker generates its own and logins break across workers |
| `OPENAI_MODEL` | no | Overrides the default model (`gpt-5.6-luna`) |
| `HTTPS_ONLY` | no | Set to `true` when served over TLS, to mark the session cookie `Secure` |
| `PORT` / `NO_BROWSER` | no | Useful when running headless |

Generate a `USERDB` entry with:

```bash
python userauth.py alice hunter2
```

## Models

The app uses OpenAI's Responses API. All of the offered models carry a ~1.05M token context
window, so even a very long transcript is sent in one piece — there is no chunking.

| Choice | Model | $/M in | $/M out |
|---|---|---|---|
| Luna — fast and cheap (default) | `gpt-5.6-luna` | 0.20 | 1.20 |
| Terra — balanced | `gpt-5.6-terra` | 2.00 | 12.00 |
| Sol — most capable | `gpt-5.6-sol` | 4.00 | 20.00 |

A typical summary costs well under a cent on Luna. Token counts and an estimated cost are
logged to stdout for each request.

## Running the tests

```bash
python -m pytest
```

## Deployment

```bash
gunicorn --timeout 300 -w 1 app:app
```

Note the long timeout: a large summary can take a couple of minutes to generate.

## Caveats

* It uses a python library called `youtube-transcript-api` to retrieve the transcript. It works,
  but it's clearly not using documented interfaces. So don't be surprised if it gets broken at
  some point. YouTube also blocks many datacenter IP ranges, so this may work from your desktop
  and fail from a cloud host.
* Only videos with an English transcript are supported.

## Authentication

There is no default account — set `USERDB` before first run. Passwords are stored as
werkzeug hashes, sessions are cookie-based, forms are CSRF-protected, and an address is locked
out for 5 minutes after 5 consecutive failed logins.

It is still a simple single-tenant login intended to keep a personal deployment private, not a
real identity system.
