#    ┌─────────────────────────────────────────────────────────┐
#    │                     YouTube Scraper                     │
#    │                                                         │
#    │           This code will extract a transcript           │
#    │            and format it for LLM digestion.             │
#    │                                                         │
#    │        It will also get the title of the video.         │
#    └─────────────────────────────────────────────────────────┘
import re
from urllib.parse import urlparse, parse_qs

import requests
import youtube_transcript_api


#   A common error code for different usages
class YouTubeError(Exception):
    pass


# A YouTube video id is always 11 characters of base64url alphabet
_VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')

# Paths that carry the video id as the last path segment, e.g. /live/<id>
_PATH_PREFIXES = ('live', 'embed', 'shorts', 'v')


# Format a floating seconds value into HH:MM:SS format
def secs2string(s):
    hours = int(s / (60 * 60))
    s = s - hours * 60 * 60
    mins = int(s / 60)
    s = s - mins * 60
    secs = int(s)
    return f'{hours:02d}:{mins:02d}:{secs:02d}'


#    ┌─────────────────────────────────────────────────────────┐
#    │                        Get Id                           │
#    │                                                         │
#    │   Pull the video id out of whatever the user pasted:    │
#    │  a bare id, a watch URL, youtu.be, /live, /embed, or    │
#    │        /shorts, with or without a protocol.             │
#    └─────────────────────────────────────────────────────────┘
def get_id(text):
    text = (text or '').strip()

    # Already a bare video id? Nothing to parse.
    if _VIDEO_ID_RE.match(text):
        return text

    # urlparse needs a scheme to treat the host as a host rather than a path
    if '//' not in text:
        text = 'https://' + text

    url = urlparse(text)
    host = url.hostname.lower() if url.hostname else ''
    if host.startswith('www.'):
        host = host[4:]

    # youtu.be/<id> puts the id in the path
    if host == 'youtu.be':
        candidate = url.path.lstrip('/').split('/')[0]
    else:
        # The ?v= parameter is the canonical location on youtube.com
        candidate = parse_qs(url.query).get('v', [''])[0]

        if not candidate:
            # ...otherwise it's the segment after /live, /embed, /shorts, /v
            segments = [s for s in url.path.split('/') if s]
            if len(segments) >= 2 and segments[0] in _PATH_PREFIXES:
                candidate = segments[1]
            elif len(segments) == 1:
                candidate = segments[0]

    if not _VIDEO_ID_RE.match(candidate):
        raise YouTubeError(f'Could not find a YouTube video id in "{text}"')

    return candidate


#    ┌─────────────────────────────────────────────────────────┐
#    │                        Get Title                        │
#    │                                                         │
#    │   Ask YouTube's oEmbed endpoint, which is a supported   │
#    │  API, rather than scraping <title> out of the watch     │
#    │                    page's HTML.                         │
#    └─────────────────────────────────────────────────────────┘
def get_title(video_id):
    video_id = get_id(video_id)

    try:
        r = requests.get(
            'https://www.youtube.com/oembed',
            params={'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()['title']
    except (requests.RequestException, ValueError, KeyError) as e:
        # A missing title shouldn't sink the whole summary
        raise YouTubeError(f'Could not retrieve the title for {video_id}') from e


#    ┌─────────────────────────────────────────────────────────┐
#    │                     Get Transcript                      │
#    │                                                         │
#    │ Retrieve the transcript from YouTube and then format it │
#    │          into a single string with timestamps.          │
#    └─────────────────────────────────────────────────────────┘
def get_transcript(video_id, title=None):
    video_id = get_id(video_id)

    try:
        api = youtube_transcript_api.YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = transcript_list.find_transcript(['en'])
        transcript_data = transcript.fetch()
    except Exception as e:
        # Catch all YouTube API errors: NoTranscriptFound, XML parsing errors,
        # HTTP errors, age-restricted videos, etc.
        raise YouTubeError(f'No English transcript available for {video_id}') from e

    # The caller usually already has the title; don't fetch it a second time.
    if title is None:
        title = video_id

    lines = [f'# Transcript of "{title}"', '']
    lines += [f'[{secs2string(t.start)}] - {t.text}' for t in transcript_data]

    return '\n'.join(lines)
