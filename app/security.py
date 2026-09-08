"""Password hashing and minimal HS256 JWT implementation."""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

import bcrypt
from dotenv import load_dotenv


load_dotenv()
JWT_SECRET = os.environ.get("JWT_SECRET", "development-only-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 60 * 60


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _encode_part(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode_part(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode((value + padding).encode("ascii")))


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    header = _encode_part({"alg": JWT_ALGORITHM, "typ": "JWT"})
    payload = _encode_part({"sub": str(user_id), "iat": now, "exp": now + JWT_EXPIRATION_SECONDS})
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')}"


def decode_access_token(token: str) -> int:
    try:
        header, payload, signature = token.split(".")
        expected = hmac.new(JWT_SECRET.encode("utf-8"), f"{header}.{payload}".encode("ascii"), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode((signature + "=" * (-len(signature) % 4)).encode("ascii"))
        claims = _decode_part(payload)
        if not hmac.compare_digest(expected, supplied) or claims.get("exp", 0) <= int(time.time()):
            raise ValueError
        return int(claims["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError("Invalid or expired access token")

