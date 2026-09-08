import json

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('USERDB', json.dumps({'alice': generate_password_hash('hunter2')}))
    monkeypatch.setenv('SESSION_KEY', 'test-key-not-a-secret')

    import app as app_module
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    app_module.userauth._failures.clear()
    with app_module.app.test_client() as c:
        yield c


def login(client):
    return client.post('/login', data={'user_id': 'alice', 'password': 'hunter2'})


@pytest.mark.parametrize('path', ['/', '/summarizer'])
def test_pages_require_authentication(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_result_requires_authentication(client):
    assert client.post('/result', data={}).status_code == 302


def test_static_files_are_public(client):
    assert client.get('/static/css/styles.css').status_code == 200


def test_login_page_is_public(client):
    assert client.get('/login').status_code == 200


def test_bad_credentials_return_401(client):
    response = client.post('/login', data={'user_id': 'alice', 'password': 'wrong'})
    assert response.status_code == 401


def test_successful_login_reaches_the_form(client):
    assert login(client).status_code == 302
    page = client.get('/summarizer')
    assert page.status_code == 200
    assert b'Which video to summarize?' in page.data


def test_logout_clears_the_session(client):
    login(client)
    client.post('/logout')
    assert client.get('/summarizer').status_code == 302


def test_bad_video_url_renders_the_error_page(client):
    login(client)
    response = client.post('/result', data={
        'youtube_video_id': 'https://example.com/nope', 'options': '500'})
    assert response.status_code == 400
    assert b'Cannot retrieve transcript' in response.data
