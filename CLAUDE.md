# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Summarizer is a Flask web application that extracts YouTube video transcripts and uses AI to generate summaries of varying lengths. The app supports multiple LLM providers including Ollama (local), Deep Infra, Hugging Face, and OpenAI.

## Architecture

The application follows a modular Flask architecture:

- **app.py**: Main Flask application with routes, authentication, and request handling
- **summarizer.py**: Core orchestration logic that selects LLM provider and processes prompts
- **youtuber.py**: YouTube integration for transcript extraction and video metadata
- **LLM Provider Modules**: Individual classes for each AI service
  - `ollama.py`: Local Ollama integration
  - `deepinfra.py`: Deep Infra API using OpenAI-compatible interface
  - `hf.py`: Hugging Face Inference API with custom token formatting
  - `open_ai.py`: Direct OpenAI API integration
- **userauth.py**: Simple session-based authentication system
- **md2html.py**: Markdown to HTML conversion for AI responses
- **prompts/**: Directory containing prompt templates for different summary lengths

## Environment Setup

The application selects its LLM provider based on environment variables (checked in order):
1. `USE_OLLAMA=True` - Uses local Ollama installation
2. `HF_API_KEY=<key>` - Uses Hugging Face Inference API
3. `DI_API_KEY=<key>` - Uses Deep Infra API
4. `OPENAI_API_KEY=<key>` - Uses OpenAI API (fallback)

Additional environment variables:
- `SESSION_KEY`: Flask session secret key (defaults to hardcoded value)
- `USERDB`: JSON string for custom user authentication (e.g., `{"bob": "pass1"}`)

## Development Commands

### Running the Application
```bash
python app.py  # Runs locally with auto port detection and browser opening
```

### Production Deployment
```bash
gunicorn --timeout 300 -w 1 app:app  # As specified in Procfile
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Key Implementation Details

### LLM Provider Selection
The `summarizer.py` module implements a provider hierarchy that automatically selects the first available LLM service based on environment variables. Each provider implements a common `ask(system_prompt, user_prompt)` interface.

### YouTube Integration
The `youtuber.py` module handles multiple YouTube URL formats and uses the `youtube-transcript-api` library to extract transcripts. It includes custom URL parsing logic for various YouTube link formats.

### Prompt System
Summary prompts are stored as markdown files in the `prompts/` directory, with filenames corresponding to word length targets (250.md, 500.md, 1000.md, 2500.md). The system uses template substitution to inject transcripts and additional user prompts.

### Authentication Flow
The app uses Flask sessions with a before_request hook that redirects unauthenticated users to `/login`. Authentication supports both default admin/admin credentials and custom user databases via environment variables.

## File Structure

```
├── app.py              # Main Flask application
├── summarizer.py       # Core AI orchestration
├── youtuber.py         # YouTube API integration
├── ollama.py          # Ollama provider
├── deepinfra.py       # Deep Infra provider
├── hf.py              # Hugging Face provider
├── open_ai.py         # OpenAI provider
├── userauth.py        # Authentication system
├── md2html.py         # Markdown conversion
├── prompts/           # AI prompt templates
│   ├── system_prompt.md
│   ├── 250.md
│   ├── 500.md
│   ├── 1000.md
│   └── 2500.md
├── templates/         # Jinja2 HTML templates
├── static/           # Static assets
└── requirements.txt  # Python dependencies
```

## Testing

The application includes basic error handling for YouTube API failures and LLM timeouts. Manual testing can be performed by running the Flask development server and navigating through the web interface.