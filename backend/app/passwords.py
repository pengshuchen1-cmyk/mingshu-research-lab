"""Memory-hard password hashing with a self-describing storage format."""

from __future__ import annotations

import base64
import hashlib
import secrets

SCHEME = "scrypt"
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 3
SCRYPT_MAXMEM = 128 * 1024 * 1024
SALT_BYTES = 16
KEY_BYTES = 32


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _derive(password: str, salt: bytes, *, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=KEY_BYTES,
        maxmem=SCRYPT_MAXMEM,
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    derived = _derive(password, salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return "$".join(
        (SCHEME, str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P), _encode(salt), _encode(derived))
    )


def _parts(encoded: str) -> tuple[int, int, int, bytes, bytes] | None:
    try:
        scheme, n_text, r_text, p_text, salt_text, digest_text = encoded.split("$")
        n, r, p = int(n_text), int(r_text), int(p_text)
        if scheme != SCHEME or not 2**14 <= n <= 2**18 or not 1 <= r <= 16 or not 1 <= p <= 10:
            return None
        salt, expected = _decode(salt_text), _decode(digest_text)
        if len(salt) < SALT_BYTES or len(expected) != KEY_BYTES:
            return None
        return n, r, p, salt, expected
    except (TypeError, ValueError):
        return None


def verify_password(password: str, encoded: str) -> bool:
    parsed = _parts(encoded)
    if parsed is None:
        return False
    n, r, p, salt, expected = parsed
    try:
        actual = _derive(password, salt, n=n, r=r, p=p)
    except ValueError:
        return False
    return secrets.compare_digest(actual, expected)


def password_needs_rehash(encoded: str) -> bool:
    parsed = _parts(encoded)
    return parsed is None or parsed[:3] != (SCRYPT_N, SCRYPT_R, SCRYPT_P)


# A missing account or unset password still performs one real password hash
# verification, reducing the timing difference from an ordinary failed login.
DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")
