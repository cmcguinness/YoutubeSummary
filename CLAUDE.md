# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Summarizer is a Flask web application that extracts YouTube video transcripts and uses AI to generate summaries of varying lengths. The app supports multiple LLM providers including Ollama (local), Hugging Face, Deep Infra, and OpenAI.

## Development Commands

### Running Locally
```bash
python app.py  # Auto-selects free port and opens browser
```

### Production Deployment
```bash
gunicorn --timeout 300 -w 1 app:app
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Request Flow
1. User authenticates via `/login` (session-based, checked by `@app.before_request` hook)
2. User submits YouTube URL at `/summarizer` endpoint
3. `youtuber.py` extracts transcript using `youtube-transcript-api` library
4. `summarizer.py` loads appropriate prompt template from `prompts/` directory
5. Provider hierarchy selects first available LLM service based on environment variables
6. LLM response (markdown) converted to HTML via custom `md2html.py` parser
7. Result rendered in template with video title and summary

### LLM Provider Selection Hierarchy
The `summarizer.py` module checks environment variables in this order:
1. `USE_OLLAMA=True` → `ollama.py` (local Ollama at 127.0.0.1:11434)
2. `HF_API_KEY=<key>` → `hf.py` (Hugging Face Inference API with custom token formatting)
3. `DI_API_KEY=<key>` → `deepinfra.py` (Deep Infra using OpenAI-compatible interface)
4. `OPENAI_API_KEY=<key>` → `open_ai.py` (fallback)

All providers implement `ask(system_prompt, user_prompt)` interface.

### Key Implementation Details

**YouTube URL Parsing**: `youtuber.py` handles multiple URL formats (watch, embed, live, youtu.be) by stripping protocols and known prefixes to extract video ID.

**Prompt System**: Summary templates in `prompts/` use filename convention (250.md, 500.md, 1000.md, 2500.md) where number indicates target word count. Templates use `{text}` placeholder for transcript injection.

**Hugging Face Integration**: Unlike other providers, HF requires manual token formatting with `<|begin_of_text|>`, `<|start_header_id|>system<|end_header_id|>`, etc. The response must be parsed to extract content after `<|start_header_id|>assistant<|end_header_id|>`.

**Markdown Conversion**: Custom `md2html.py` parser handles nested lists (UL/OL), bold/italic, headers, and horizontal rules. Built because standard libraries don't handle nested lists well.

**Port Selection**: `find_free_port()` dynamically binds to available port to avoid conflicts with Flask's default 5000.

**Request Logging**: All requests logged to stdout via `@app.before_request` hook showing method, path, and remote address.

## Environment Variables

Authentication:
- `SESSION_KEY`: Flask session secret (defaults to hardcoded value)
- `USERDB`: JSON string for custom users (e.g., `{"bob": "pass1"}`, defaults to admin/admin)

LLM Provider (set ONE):
- `USE_OLLAMA=True`: Use local Ollama
- `HF_API_KEY=<key>`: Use Hugging Face
- `DI_API_KEY=<key>`: Use Deep Infra
- `OPENAI_API_KEY=<key>`: Use OpenAI

## File Organization

```
├── app.py              # Flask routes, authentication, request flow
├── summarizer.py       # Provider selection and orchestration
├── youtuber.py         # Transcript extraction and URL parsing
├── ollama.py           # Ollama provider (POST to 127.0.0.1:11434/api/chat)
├── hf.py               # Hugging Face provider with custom token formatting
├── deepinfra.py        # Deep Infra provider (OpenAI-compatible)
├── open_ai.py          # OpenAI provider (gpt-4o)
├── userauth.py         # Session authentication
├── md2html.py          # Custom markdown parser for nested lists
├── prompts/            # Markdown templates with {text} placeholder
└── templates/          # Jinja2 HTML templates
```

## Testing

Manual testing via web interface after running `python app.py`. Chrome DevTools integration recommended for UI testing per user expectations.
