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


@pytest.fixture
def noauth_client(monkeypatch):
    monkeypatch.setenv('DISABLE_AUTH', 'true')
    monkeypatch.setenv('SESSION_KEY', 'test-key-not-a-secret')

    import importlib

    import app as app_module
    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app_module.app.test_client() as c:
        yield c

    monkeypatch.delenv('DISABLE_AUTH', raising=False)
    importlib.reload(app_module)


def test_disable_auth_lets_you_straight_in(noauth_client):
    response = noauth_client.get('/summarizer')
    assert response.status_code == 200
    assert b'Which video to summarize?' in response.data


def test_disable_auth_redirects_the_login_page_away(noauth_client):
    response = noauth_client.get('/login')
    assert response.status_code == 302
    assert '/summarizer' in response.headers['Location']


def test_disable_auth_hides_the_logout_button(noauth_client):
    assert b'Log out' not in noauth_client.get('/summarizer').data


def test_chat_requires_authentication(client):
    assert client.post('/chat', json={'video_id': 'x', 'question': 'y'}).status_code == 302


def test_chat_rejects_a_bad_video_id(client):
    login(client)
    response = client.post('/chat', json={'video_id': 'nonsense', 'question': 'hi'})
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_chat_rejects_malformed_history(client):
    login(client)
    response = client.post('/chat', json={
        'video_id': 'dQw4w9WgXcQ', 'question': 'hi', 'history': 'not a list'})
    assert response.status_code == 400
