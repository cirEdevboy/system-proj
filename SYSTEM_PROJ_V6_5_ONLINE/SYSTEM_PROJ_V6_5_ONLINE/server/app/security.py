from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib, secrets, uuid
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from .config import settings

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("A senha deve conter no mínimo 8 caracteres.")
    return ph.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _token(user_id: int, token_type: str, expires_delta: timedelta, session_id: str | None = None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if session_id:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_access_token(user_id: int, session_id: str):
    return _token(user_id, "access", timedelta(minutes=settings.access_token_minutes), session_id)

def create_refresh_token(user_id: int, session_id: str):
    return _token(user_id, "refresh", timedelta(days=settings.refresh_token_days), session_id)

def decode_token(token: str, expected_type: str | None = None):
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Tipo de token inválido")
    return payload

def random_reset_token() -> str:
    return secrets.token_urlsafe(48)
