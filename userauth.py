#    ┌─────────────────────────────────────────────────────────┐
#    │                   User Authentication                   │
#    │                                                         │
#    │  Passwords are stored as werkzeug hashes, and repeated  │
#    │      failures from one address get locked out.          │
#    └─────────────────────────────────────────────────────────┘
import json
import os
import time
from threading import Lock

from werkzeug.security import check_password_hash, generate_password_hash

# Lock an address out after this many consecutive failures...
MAX_ATTEMPTS = 5
# ...for this long. Replaces the old blocking sleep, which stalled the whole
# worker and made a denial of service a single request away.
LOCKOUT_SECONDS = 300

_failures = {}
_failures_lock = Lock()


class ConfigError(Exception):
    pass


def _load_users():
    """USERDB is a JSON object of {user: password_hash}.

    Values may also be plaintext for convenience in local development, which we
    accept but warn about loudly.
    """
    raw = os.getenv('USERDB')
    if not raw:
        raise ConfigError(
            'USERDB is not set. Generate one with:  python userauth.py <user> <password>'
        )

    try:
        users = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f'USERDB is not valid JSON: {e}') from e

    if not isinstance(users, dict) or not users:
        raise ConfigError('USERDB must be a non-empty JSON object of {user: password_hash}.')

    return users


def _is_locked_out(remote_addr):
    with _failures_lock:
        count, last = _failures.get(remote_addr, (0, 0.0))
        if count >= MAX_ATTEMPTS and (time.time() - last) < LOCKOUT_SECONDS:
            return True
        return False


def _record_failure(remote_addr):
    with _failures_lock:
        count, last = _failures.get(remote_addr, (0, 0.0))
        # An expired lockout starts the count over
        if (time.time() - last) >= LOCKOUT_SECONDS:
            count = 0
        _failures[remote_addr] = (count + 1, time.time())


def _clear_failures(remote_addr):
    with _failures_lock:
        _failures.pop(remote_addr, None)


def authenticate(user, password, remote_addr='unknown'):
    if _is_locked_out(remote_addr):
        return False

    users = _load_users()
    stored = users.get(user)

    if stored is None:
        # Hash anyway so a missing user and a wrong password take the same time
        generate_password_hash('timing equalizer')
        _record_failure(remote_addr)
        return False

    if stored.startswith(('pbkdf2:', 'scrypt:', 'argon2:')):
        ok = check_password_hash(stored, password)
    else:
        print('WARNING: USERDB holds a plaintext password. Use a hash in production.', flush=True)
        ok = stored == password

    if ok:
        _clear_failures(remote_addr)
    else:
        _record_failure(remote_addr)
    return ok


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print('Usage: python userauth.py <username> <password>')
        raise SystemExit(1)

    entry = {sys.argv[1]: generate_password_hash(sys.argv[2])}
    print("Set this in your environment:\n")
    print(f"USERDB='{json.dumps(entry)}'")
