#    ┌─────────────────────────────────────────────────────────┐
#    │                   YouTube Summarizer                    │
#    │                                                         │
#    │    This is an app that will produce a summary of the    │
#    │ transcript of a YouTube video.  It provides options for │
#    │          adjusting the length of the summary.           │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘

from flask import Flask, render_template, request, session
import socket
import os
import time
import youtuber
import summarizer
import userauth

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
# You should change this from my default!!!
app.secret_key = 'The Rain in Spain falls Mainly on the Plain!'

# Options we present for summary lengths
variable_list = ["Full Transcript",  "250 Word", "500 Word", "1000 Word", "2500 Word"]

#    ┌─────────────────────────────────────────────────────────┐
#    │                            /                            │
#    │                                                         │
#    │          If logged in, present the start page.          │
#    │            If not, ask them to authenticate.            │
#    └─────────────────────────────────────────────────────────┘
@app.route("/")
def get_login_page():
    if 'authenticated' in session:
        return index_page()

    return render_template('login.html', title='Login Please')


#    ┌─────────────────────────────────────────────────────────┐
#    │                         /login                          │
#    │                                                         │
#    │          Validate their user id and password.           │
#    │     Sleep for a while on failure to slow down bots.     │
#    └─────────────────────────────────────────────────────────┘
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        if userauth.authenticate(user_id, password):
            session['authenticated'] = True
            return index_page()
    time.sleep(5)
    return render_template('login.html', title='Invalid credentials, please try again')

#    ┌─────────────────────────────────────────────────────────┐
#    │                       /summarizer                       │
#    │                                                         │
#    │       Solicit the YouTube URL and summary options       │
#    └─────────────────────────────────────────────────────────┘
@app.route('/summarizer')
def index_page():
    if 'authenticated' not in session:
        return get_login_page()
    return render_template('index.html', variable_list=variable_list, title='Select your video')


#    ┌─────────────────────────────────────────────────────────┐
#    │                         /result                         │
#    │                                                         │
#    │               Perform the summarization.                │
#    │        (or not if they want a full transcript).         │
#    └─────────────────────────────────────────────────────────┘
@app.route('/result', methods=['POST'])
def result():
    if 'authenticated' not in session:
        return get_login_page()
    youtube_video_id = request.form['youtube_video_id']
    selected_option = request.form['options']
    add_prompt = ''

    # You have to enable the form in the HTML for this to be present
    if 'additional_prompt' in request.form:
        add_prompt = request.form['additional_prompt']

    try:
        full_text = youtuber.get_transcript(youtube_video_id)
        title = youtuber.get_title(youtube_video_id)
    except youtuber.YouTubeError:
        return render_template('result.html', dynamic_text=f'Video {youtube_video_id} not found', title='Error', subtitle=f'Cannot find video')

    if selected_option == "Full Transcript":
        full_text = '<pre>\n' + full_text + "\n</pre>\n"
        return render_template('result.html', dynamic_text=full_text, title=title, subtitle='Full transcript')

    summary = summarizer.get_summary(full_text, selected_option, add_prompt)
    return render_template('result.html', dynamic_text=summary, title=title, subtitle=f'{selected_option} Summary')


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
    port = find_free_port()
    if os.name == 'nt':
        os.system(f'explorer "http:/127.0.0.1:{port}"')
    else:
        os.system(f'open http://127.0.0.1:{port}')
    app.run(port=port, debug=False)
