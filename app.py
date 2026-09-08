#    ┌─────────────────────────────────────────────────────────┐
#    │                   YouTube Summarizer                    │
#    │                                                         │
#    │    This is an app that will produce a summary of the    │
#    │ transcript of a YouTube video.  It provides options for │
#    │          adjusting the length of the summary.           │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
import os
import secrets
import socket
from datetime import timedelta

from dotenv import load_dotenv
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_wtf.csrf import CSRFProtect

# Read .env before anything reads os.getenv() at import time
load_dotenv()

import llm
import summarizer
import youtuber
import userauth

app = Flask(__name__)

# A generated key logs everyone out on restart, which beats shipping a
# well-known default that lets anyone forge a session cookie.
app.secret_key = os.getenv('SESSION_KEY') or secrets.token_hex(32)
if not os.getenv('SESSION_KEY'):
    print('WARNING: SESSION_KEY is not set; sessions will not survive a restart.', flush=True)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    # Only send the cookie over TLS when we're actually served over TLS
    SESSION_COOKIE_SECURE=os.getenv('HTTPS_ONLY', '').lower() == 'true',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    MAX_CONTENT_LENGTH=64 * 1024,
)

csrf = CSRFProtect(app)

# On a LAN-only host the login screen is mostly ceremony. Setting DISABLE_AUTH
# turns it off entirely -- everyone who can reach the app is let straight in.
AUTH_DISABLED = os.getenv('DISABLE_AUTH', '').lower() in ('1', 'true', 'yes')
if AUTH_DISABLED:
    print('WARNING: DISABLE_AUTH is set. Anyone who can reach this app can use it.', flush=True)

PUBLIC_ENDPOINTS = {'login', 'static'}


@app.context_processor
def inject_auth_state():
    # Templates use this to decide whether to offer a Log out button
    return {'auth_disabled': AUTH_DISABLED}


@app.before_request
def before_request():
    # We're going to log every request, so we can see what's going on
    print(f'{request.method} {request.path} from {request.remote_addr}', flush=True)

    if AUTH_DISABLED or request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if not session.get('authenticated'):
        return redirect(url_for('login'))

    return None


#    ┌─────────────────────────────────────────────────────────┐
#    │                         /login                          │
#    │                                                         │
#    │          Validate their user id and password.           │
#    └─────────────────────────────────────────────────────────┘
@app.route('/login', methods=['GET', 'POST'])
def login():
    if AUTH_DISABLED or session.get('authenticated'):
        return redirect(url_for('index_page'))

    if request.method == 'POST':
        user_id = request.form.get('user_id', '')
        password = request.form.get('password', '')

        try:
            authenticated = userauth.authenticate(user_id, password, request.remote_addr)
        except userauth.ConfigError as e:
            return render_template('login.html', title='Login', error=str(e)), 500

        if authenticated:
            session.clear()
            session['authenticated'] = True
            session['user'] = user_id
            session.permanent = True
            return redirect(url_for('index_page'))

        return render_template('login.html', title='Login',
                               error='Invalid credentials, please try again.'), 401

    return render_template('login.html', title='Login')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


#    ┌─────────────────────────────────────────────────────────┐
#    │                    /  and /summarizer                   │
#    │                                                         │
#    │       Solicit the YouTube URL and summary options       │
#    └─────────────────────────────────────────────────────────┘
@app.route('/')
@app.route('/summarizer')
def index_page():
    return render_template('index.html',
                           variable_list=summarizer.summary_types,
                           models=llm.MODELS,
                           default_model=llm.DEFAULT_MODEL,
                           title='Which video to summarize?')


#    ┌─────────────────────────────────────────────────────────┐
#    │                         /result                         │
#    │                                                         │
#    │               Perform the summarization.                │
#    │        (or not if they want a full transcript).         │
#    └─────────────────────────────────────────────────────────┘
@app.route('/result', methods=['POST'])
def result():
    video = request.form.get('youtube_video_id', '')
    selected_option = request.form.get('options', '')
    model = request.form.get('model') or None
    add_prompt = request.form.get('additional_prompt', '')

    try:
        title = youtuber.get_title(video)
        transcript = youtuber.get_transcript(video, title=title)
    except youtuber.YouTubeError as e:
        return render_template('error.html',
                               title='Error',
                               subtitle='Cannot retrieve transcript',
                               reason=str(e)), 400

    video_id = youtuber.get_id(video)

    if selected_option == summarizer.FULL_TRANSCRIPT:
        return render_template('result.html',
                               transcript=transcript,
                               title=title,
                               video_id=video_id,
                               model=model or llm.DEFAULT_MODEL,
                               subtitle='Full transcript')

    try:
        summary = summarizer.get_summary(transcript, selected_option, add_prompt, model=model)
    except (llm.LLMError, ValueError) as e:
        return render_template('error.html',
                               title='Error',
                               subtitle='Could not generate a summary',
                               reason=str(e)), 502

    return render_template('result.html',
                           summary=summary,
                           title=title,
                           video_id=video_id,
                           model=model or llm.DEFAULT_MODEL,
                           subtitle='Transcript Summary')


#    ┌─────────────────────────────────────────────────────────┐
#    │                          /chat                          │
#    │                                                         │
#    │      Answer a follow-up question about a video's        │
#    │        transcript. Called by JavaScript, so it          │
#    │              speaks JSON in both directions.            │
#    └─────────────────────────────────────────────────────────┘
@app.route('/chat', methods=['POST'])
def chat():
    payload = request.get_json(silent=True) or {}
    video_id = payload.get('video_id', '')
    question = payload.get('question', '')
    history = payload.get('history') or []
    model = payload.get('model') or None

    if not isinstance(history, list):
        return jsonify({'error': 'Malformed conversation history.'}), 400

    try:
        transcript = youtuber.get_transcript(video_id)
    except youtuber.YouTubeError as e:
        return jsonify({'error': str(e)}), 400

    try:
        answer = summarizer.answer_question(transcript, question, history, model=model)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except llm.LLMError as e:
        return jsonify({'error': str(e)}), 502

    return jsonify({'answer': answer})


#    ┌────────────────────────────────────────────────────────────────────┐
#    │    Find a free port                                                │
#    │                                                                    │
#    │    Flask apps usually start themselves on port 5000, but it's      │
#    │    not always free.  This code finds a free port we can use.       │
#    └────────────────────────────────────────────────────────────────────┘
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to an available port provided by the host.
        return s.getsockname()[1]  # Return the port number assigned.


#    ┌──────────────────────────────────────────────────────────┐
#    │    This version of the Flask launch code will            │
#    │    automatically open a browser, saving you from         │
#    │    having to click.                                      │
#    └──────────────────────────────────────────────────────────┘
if __name__ == '__main__':
    port = int(os.getenv('PORT') or find_free_port())
    if os.getenv('NO_BROWSER', '').lower() != 'true':
        if os.name == 'nt':
            os.system(f'explorer "http://127.0.0.1:{port}"')
        else:
            os.system(f'open http://127.0.0.1:{port}')
    app.run(port=port, debug=False)
