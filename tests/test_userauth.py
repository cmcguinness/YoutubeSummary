import json

import pytest
from werkzeug.security import generate_password_hash

import userauth


@pytest.fixture(autouse=True)
def clear_failures():
    userauth._failures.clear()
    yield
    userauth._failures.clear()


@pytest.fixture
def hashed_db(monkeypatch):
    monkeypatch.setenv('USERDB', json.dumps({'alice': generate_password_hash('hunter2')}))


def test_correct_password_authenticates(hashed_db):
    assert userauth.authenticate('alice', 'hunter2', '1.1.1.1')


def test_wrong_password_rejected(hashed_db):
    assert not userauth.authenticate('alice', 'nope', '1.1.1.1')


def test_unknown_user_rejected(hashed_db):
    assert not userauth.authenticate('mallory', 'hunter2', '1.1.1.1')


def test_lockout_after_repeated_failures(hashed_db):
    for _ in range(userauth.MAX_ATTEMPTS):
        userauth.authenticate('alice', 'wrong', '2.2.2.2')
    # Even the correct password is refused while locked out
    assert not userauth.authenticate('alice', 'hunter2', '2.2.2.2')


def test_lockout_is_per_address(hashed_db):
    for _ in range(userauth.MAX_ATTEMPTS):
        userauth.authenticate('alice', 'wrong', '2.2.2.2')
    assert userauth.authenticate('alice', 'hunter2', '3.3.3.3')


def test_success_clears_the_failure_count(hashed_db):
    userauth.authenticate('alice', 'wrong', '4.4.4.4')
    userauth.authenticate('alice', 'hunter2', '4.4.4.4')
    assert '4.4.4.4' not in userauth._failures


def test_missing_userdb_is_a_config_error(monkeypatch):
    monkeypatch.delenv('USERDB', raising=False)
    with pytest.raises(userauth.ConfigError):
        userauth.authenticate('alice', 'hunter2', '1.1.1.1')


def test_malformed_userdb_is_a_config_error(monkeypatch):
    monkeypatch.setenv('USERDB', 'not json')
    with pytest.raises(userauth.ConfigError):
        userauth.authenticate('alice', 'hunter2', '1.1.1.1')
