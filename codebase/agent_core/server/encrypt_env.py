"""Encrypt .env placeholders into .env.enc using a password.

Usage:
  python encrypt_env.py          # prompts for each empty key in .env
  python encrypt_env.py --full   # prompts for all keys (even non-empty)

On server start, an existing .env.enc is unlocked; any known key not yet
set is offered for addition and the file is re-encrypted when it changes.
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
DEFAULT_ENV_PLACEHOLDERS = {"GEMINI_API_KEY": "", "OPENROUTER_API_KEY": ""}


def _write_env_template(env_file: str) -> None:
    """Create .env with empty placeholder keys if it doesn't exist."""
    if os.path.exists(env_file):
        return
    with open(env_file, "w", encoding="utf-8") as f:
        for k, v in DEFAULT_ENV_PLACEHOLDERS.items():
            f.write(f"{k}={v}\n")
    print(f"Created {env_file} with placeholder keys.")


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

def _decrypt_env(encrypt_env_file: str, password: str) -> dict[str, str] | None:
    """Decrypt .env.enc with a password, or return None on wrong password."""
    try:
        with open(encrypt_env_file, "rb") as f:
            salt = f.read(16)
            encrypted_data = f.read()
        key = derive_key(password, salt)
        return json.loads(Fernet(key).decrypt(encrypted_data))
    except (InvalidToken, OSError):
        return None


def _unlock_with_password(encrypt_env_file: str, password: str) -> bool:
    """Load decrypted keys into os.environ. Returns False on wrong password."""
    payload = _decrypt_env(encrypt_env_file, password)
    if payload is None:
        return False
    for k, v in payload.items():
        os.environ.setdefault(k, v)
    return True


def _try_unlock_env(encrypt_env_file) -> None:
    if not os.path.exists(encrypt_env_file):
        return
    password = getpass.getpass("Enter password to unlock API keys: ")
    if not _unlock_with_password(encrypt_env_file, password):
        print("Invalid password.")
        sys.exit(1)
    print("API keys unlocked.")


def _prompt_missing_keys(payload: dict[str, str]) -> dict[str, str]:
    """Offer to add any known key missing from the decrypted payload."""
    for key in DEFAULT_ENV_PLACEHOLDERS:
        if payload.get(key):
            continue
        ans = input(f"  {key} is not set. Add it now? [y/N]: ").strip().lower()
        if ans in ("y", "yes"):
            val = getpass.getpass(f"    {key}: ")
            if val:
                payload[key] = val
    return payload


def _load_into_env(payload: dict[str, str]) -> None:
    for k, v in payload.items():
        if v:
            os.environ.setdefault(k, v)


def setup_or_unlock_env(
    env_file: str = ENV_FILE, encrypted_file: str = ENCRYPTED_FILE
) -> None:
    """Unlock existing .env.enc, or guide a first-time user through setup."""
    if os.path.exists(encrypted_file):
        password = getpass.getpass("Enter password to unlock API keys: ")
        raw = _decrypt_env(encrypted_file, password)
        if raw is None:
            print("Invalid password.")
            sys.exit(1)
        clean = {k: v for k, v in raw.items() if v}
        clean = _prompt_missing_keys(clean)
        if clean != raw:
            with open(encrypted_file, "wb") as f:
                f.write(encrypt(clean, password))
            print(f"Updated {encrypted_file}.")
        _load_into_env(clean)
        print("API keys unlocked.")
        return

    if not os.path.exists(env_file):
        print(f"{env_file} file not found.")
        _write_env_template(env_file)

    empty_keys = [k for k, v in parse_env(env_file).items() if not v]
    if not empty_keys:
        return

    print("First-time setup: no encrypted keys found.")
    print("Enter your API keys below (input is hidden):")
    secrets = {k: v for k, v in ((k, getpass.getpass(f"  {k}: ")) for k in empty_keys) if v}
    if not secrets:
        print("No values entered; skipping encryption setup.")
        sys.exit(1)

    password = getpass.getpass("Choose a password to encrypt your keys: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    with open(encrypted_file, "wb") as f:
        f.write(encrypt(secrets, password))

    print(f"Saved {len(secrets)} key(s) to {encrypted_file}")
    _unlock_with_password(encrypted_file, password)
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

    secrets = {k: v for k, v in ((k, getpass.getpass(f"{k}: ")) for k in keys_to_fill) if v}
    if not secrets:
        print("No values entered; nothing to encrypt.")
        return

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
