#    ┌─────────────────────────────────────────────────────────┐
#    │                     YouTube Scraper                     │
#    │                                                         │
#    │           This code will extract a transcript           │
#    │            and format it for LLM digestion.             │
#    │                                                         │
#    │        It will also get the title of the video.         │
#    └─────────────────────────────────────────────────────────┘
import youtube_transcript_api
import requests


#   A common error code for different usages
class YouTubeError(Exception):
    pass

# Format a floating seconds value into HH:MM:SS format
def secs2string(s):
    hours = int(s / (60 * 60))
    s = s - hours * 60 * 60
    mins = int(s / 60)
    s = s - mins * 60
    secs = int(s)
    return f'{hours:02d}:{mins:02d}:{secs:02d}'


# Get the video id from a variety of URL formats YouTube uses
def get_id(l):
    prefixes = [
        'www.youtube.com/watch?feature=player_embedded&v=',
        'youtube.com/watch?feature=player_embedded&v=',
        'm.youtube.com/watch?feature=player_embedded&v=',
        'http://youtu.be/'
        'm.youtube.com/watch?v=',
        'www.youtube.com/watch?v=',
        'www.youtube.com/live/',
        'www.youtube.com/embed/',
    ]

    protocols = ['http://', 'https://']
    for p in protocols:
        if l.startswith(p):
            l = l[len(p):]
            break

    for p in prefixes:
        if l.startswith(p):
            l = l[len(p):]
            break

    if l.find('?') != -1:
        l = l[:l.find('?')]

    if l.find('&') != -1:
        l = l[:l.find('&')]

    return l

#    ┌─────────────────────────────────────────────────────────┐
#    │                        Get Title                        │
#    │                                                         │
#    │  Retrieve the page with the YouTube video and fish the  │
#    │                    title out of it.                     │
#    └─────────────────────────────────────────────────────────┘
def get_title(video_id):
    video_id = get_id(video_id)

    try:
        r = requests.request('GET', f"http://www.youtube.com/watch?v={video_id}")
    except requests.HTTPError:
        raise YouTubeError

    if r.status_code != 200:
        raise YouTubeError

    page = r.text
    title_start = page.find('<title>')
    title_end = page.find('</title>')
    title = page[title_start + 7:title_end]
    if title.endswith(' - YouTube'):
        title = title[:-10].strip()
    return title

#    ┌─────────────────────────────────────────────────────────┐
#    │                     Get Transcript                      │
#    │                                                         │
#    │ Retrieve the transcript from YouTube and then format it │
#    │          into a single string with timestamps.          │
#    └─────────────────────────────────────────────────────────┘
def get_transcript(video_id):
    video_id = get_id(video_id)

    try:
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
    except youtube_transcript_api.NoTranscriptFound:
        raise YouTubeError

    full_text = f'# Transcript of "{get_title(video_id)}"\n\n'
    for t in transcript:
        full_text += f"[{secs2string(t['start'])}] - {t['text']} <br>\n"

    return full_text
