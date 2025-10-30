"""Token utilities for authentication."""

import base64
import json
import hmac
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple


class TokenError(Exception):
    """Raised when token validation fails."""


def _b64_encode(data: bytes) -> str:
    """Base64-url encode bytes without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> bytes:
    """Base64-url decode a string handling missing padding."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


@dataclass
class TokenPayload:
    """Decoded token payload."""
    token_type: str
    user_id: str
    session_id: str
    issued_at: datetime
    expires_at: datetime
    scopes: Tuple[str, ...]
    raw: Dict[str, Any]


class TokenManager:
    """Minimal JWT-like token manager using HMAC SHA256."""

    def __init__(self, secret: str):
        if not secret:
            raise ValueError("Token secret must not be empty")
        self._secret = secret.encode("utf-8")

    def _sign(self, signing_input: bytes) -> str:
        digest = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        return _b64_encode(digest)

    def _encode(self, header: Dict[str, Any], payload: Dict[str, Any]) -> str:
        header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signing_input = b".".join([_b64_encode(header_json).encode("ascii"), _b64_encode(payload_json).encode("ascii")])
        signature = self._sign(signing_input)
        return f"{signing_input.decode('ascii')}.{signature}"

    def _decode(self, token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        try:
            header_b64, payload_b64, signature = token.split(".")
        except ValueError as exc:
            raise TokenError("Invalid token structure") from exc

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = self._sign(signing_input)
        if not hmac.compare_digest(signature, expected_sig):
            raise TokenError("Invalid token signature")

        try:
            header = json.loads(_b64_decode(header_b64))
            payload = json.loads(_b64_decode(payload_b64))
        except (json.JSONDecodeError, ValueError) as exc:
            raise TokenError("Malformed token payload") from exc

        return header, payload

    def create_token(
        self,
        token_type: str,
        user_id: str,
        session_id: str,
        expires_in: timedelta,
        scopes: Tuple[str, ...] = (),
        extra: Dict[str, Any] | None = None,
    ) -> Tuple[str, datetime]:
        """Create a signed token and return it with the expiry datetime."""
        now = datetime.now(timezone.utc)
        exp = now + expires_in
        header = {"alg": "HS256", "typ": "JWT"}
        payload: Dict[str, Any] = {
            "typ": token_type,
            "uid": user_id,
            "sid": session_id,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "scp": list(scopes),
        }
        if extra:
            payload.update(extra)

        token = self._encode(header, payload)
        return token, exp

    def decode(self, token: str, expected_type: str | None = None) -> TokenPayload:
        """Decode and validate a token returning a TokenPayload."""
        if not token:
            raise TokenError("Token not provided")

        header, payload = self._decode(token)

        if header.get("alg") != "HS256":
            raise TokenError("Unsupported token algorithm")

        token_type = payload.get("typ")
        if expected_type and token_type != expected_type:
            raise TokenError("Invalid token type")

        user_id = payload.get("uid")
        session_id = payload.get("sid")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")

        if not all([token_type, user_id, session_id, issued_at, expires_at]):
            raise TokenError("Incomplete token payload")

        issued_at_dt = datetime.fromtimestamp(int(issued_at), tz=timezone.utc)
        expires_at_dt = datetime.fromtimestamp(int(expires_at), tz=timezone.utc)

        if expires_at_dt <= datetime.now(timezone.utc):
            raise TokenError("Token expired")

        scopes_raw = payload.get("scp") or []
        scopes = tuple(str(scope) for scope in scopes_raw)

        return TokenPayload(
            token_type=str(token_type),
            user_id=str(user_id),
            session_id=str(session_id),
            issued_at=issued_at_dt,
            expires_at=expires_at_dt,
            scopes=scopes,
            raw=payload,
        )

    @staticmethod
    def hash_token(token: str) -> str:
        """Return a stable hash of the token for storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
