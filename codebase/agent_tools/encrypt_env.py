"""Encrypt .env placeholders into .env.enc using a password.

Usage:
  python encrypt_env.py          # prompts for each empty key in .env
  python encrypt_env.py --full   # prompts for all keys (even non-empty)
"""

from __future__ import annotations

import os
import sys
import getpass
import json
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ENV_FILE = ".env"
ENCRYPTED_FILE = ".env.enc"


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt(secrets: dict[str, str], password: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    payload = json.dumps(secrets).encode()
    return salt + Fernet(key).encrypt(payload)


def parse_env(path: str) -> dict[str, str]:
    secrets: dict[str, str] = {}
    if not os.path.exists(path):
        return secrets
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            secrets[k.strip()] = v.strip()
    return secrets

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _try_unlock_env(encrypt_env_file) -> None:
    if not os.path.exists(encrypt_env_file):
        return
    password = getpass.getpass("Enter password to unlock API keys: ")
    with open(encrypt_env_file, "rb") as f:
        salt = f.read(16)
        encrypted_data = f.read()
    key = _derive_key(password, salt)
    try:
        payload = json.loads(Fernet(key).decrypt(encrypted_data))
    except InvalidToken:
        print("Invalid password.")
        sys.exit(1)
    for k, v in payload.items():
        os.environ.setdefault(k, v)
    print("API keys unlocked.")


def main() -> None:
    full_mode = "--full" in sys.argv
    existing = parse_env(ENV_FILE)

    keys_to_fill = [
        k for k, v in existing.items() if full_mode or not v
    ]

    if not keys_to_fill:
        print("All keys in .env already have values (use --full to override).")
        return

    secrets: dict[str, str] = {}
    for key in keys_to_fill:
        val = getpass.getpass(f"{key}: ")
        secrets[key] = val

    password = getpass.getpass("Encryption password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    with open(ENCRYPTED_FILE, "wb") as f:
        f.write(encrypt(secrets, password))

    print(f"Encrypted {len(secrets)} key(s) to {ENCRYPTED_FILE}")


if __name__ == "__main__":
    main()
