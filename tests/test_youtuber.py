import pytest

import youtuber

VIDEO = 'dQw4w9WgXcQ'


@pytest.mark.parametrize('given', [
    VIDEO,
    f'https://youtu.be/{VIDEO}',
    f'youtu.be/{VIDEO}?t=42',
    f'http://youtu.be/{VIDEO}',
    f'https://www.youtube.com/watch?v={VIDEO}',
    f'https://www.youtube.com/watch?v={VIDEO}&list=PLxyz&index=2',
    f'www.youtube.com/watch?v={VIDEO}',
    f'm.youtube.com/watch?v={VIDEO}',
    f'https://m.youtube.com/watch?v={VIDEO}',
    f'https://www.youtube.com/watch?feature=player_embedded&v={VIDEO}',
    f'https://www.youtube.com/live/{VIDEO}',
    f'https://www.youtube.com/embed/{VIDEO}',
    f'https://www.youtube.com/shorts/{VIDEO}',
    f'  {VIDEO}  ',
])
def test_get_id_accepts_every_url_shape(given):
    assert youtuber.get_id(given) == VIDEO


@pytest.mark.parametrize('given', ['', 'not a video', 'https://example.com/watch?v=short', 'abc'])
def test_get_id_rejects_junk(given):
    with pytest.raises(youtuber.YouTubeError):
        youtuber.get_id(given)


def test_secs2string():
    assert youtuber.secs2string(0) == '00:00:00'
    assert youtuber.secs2string(61.4) == '00:01:01'
    assert youtuber.secs2string(3725) == '01:02:05'
