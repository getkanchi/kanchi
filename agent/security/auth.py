"""Authentication utilities including Basic and OAuth helpers."""

import base64
import fnmatch
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from config import Config
from .tokens import TokenManager, TokenPayload, TokenError


class AuthError(Exception):
    """Raised for authentication-related issues."""


@dataclass
class AnonymousUser:
    """Represents an unauthenticated requester."""
    id: Optional[str] = None
    email: Optional[str] = None
    provider: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return False


@dataclass
class AuthenticatedUser:
    """Minimal authenticated user context."""
    id: str
    email: str
    provider: str
    session_id: str
    name: Optional[str] = None
    scopes: Tuple[str, ...] = ()

    @property
    def is_authenticated(self) -> bool:
        return True


@dataclass
class OAuthProviderConfig:
    """Configuration for an OAuth provider."""
    name: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: List[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    enabled: bool

    def is_available(self) -> bool:
        return self.enabled and bool(self.client_id and self.client_secret)


def _verify_pbkdf2_sha256(encoded: str, password: str) -> bool:
    """Validate pbkdf2_sha256 password hash (Django-compatible)."""
    try:
        algorithm, iterations_str, salt, hashed = encoded.split("$", 3)
    except ValueError:
        raise AuthError("Invalid password hash format")

    if algorithm != "pbkdf2_sha256":
        raise AuthError("Unsupported password hash algorithm")

    iterations = int(iterations_str)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    encoded_derived = base64.b64encode(derived).decode("ascii").strip()
    return hmac.compare_digest(encoded_derived, hashed)


class AuthManager:
    """High-level authentication helper wrapping configuration and token utilities."""

    def __init__(self, config: Config):
        self.config = config
        self.token_manager = TokenManager(config.token_secret_key)
        self._state_token_manager = TokenManager(config.session_secret_key)

    # Basic authentication
    def verify_basic_credentials(self, username: str, password: str) -> bool:
        if not self.config.auth_basic_enabled:
            raise AuthError("Basic authentication is disabled")

        configured_username = self.config.basic_auth_username
        if not configured_username:
            raise AuthError("Basic authentication username not configured")

        if username != configured_username:
            return False

        if self.config.basic_auth_password_hash:
            return _verify_pbkdf2_sha256(self.config.basic_auth_password_hash, password)

        if self.config.basic_auth_password:
            return hmac.compare_digest(self.config.basic_auth_password, password)

        raise AuthError("Basic authentication password not configured")

    def parse_basic_authorization(self, header: str) -> Tuple[str, str]:
        """Extract username/password from HTTP Basic Authorization header."""
        if not header or not header.startswith("Basic "):
            raise AuthError("Invalid basic authorization header")
        try:
            decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception as exc:  # pylint: disable=broad-except
            raise AuthError("Failed to decode basic credentials") from exc
        return username, password

    # OAuth helpers
    def get_oauth_provider(self, provider: str) -> OAuthProviderConfig:
        provider = provider.lower()
        if provider == "google":
            return OAuthProviderConfig(
                name="google",
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
                scope=self.config.oauth_scope_google or ["openid", "email", "profile"],
                client_id=self.config.google_client_id,
                client_secret=self.config.google_client_secret,
                enabled=self.config.auth_google_enabled,
            )
        if provider == "github":
            return OAuthProviderConfig(
                name="github",
                authorize_url="https://github.com/login/oauth/authorize",
                token_url="https://github.com/login/oauth/access_token",
                userinfo_url="https://api.github.com/user",
                scope=self.config.oauth_scope_github or ["read:user", "user:email"],
                client_id=self.config.github_client_id,
                client_secret=self.config.github_client_secret,
                enabled=self.config.auth_github_enabled,
            )
        raise AuthError(f"Unsupported provider: {provider}")

    def list_enabled_oauth_providers(self) -> List[str]:
        providers = []
        for provider in ("google", "github"):
            cfg = self.get_oauth_provider(provider)
            if cfg.is_available():
                providers.append(provider)
        return providers

    def build_oauth_redirect_uri(self, provider: str) -> str:
        if not self.config.oauth_redirect_base_url:
            raise AuthError("OAUTH_REDIRECT_BASE_URL must be configured for OAuth")
        base = self.config.oauth_redirect_base_url.rstrip("/")
        return f"{base}/api/auth/oauth/{provider}/callback"

    def create_oauth_state(
        self,
        provider: str,
        redirect_to: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        ttl = timedelta(minutes=self.config.oauth_state_ttl_minutes or 5)
        nonce = secrets.token_urlsafe(16)
        extra: Dict[str, str] = {"prv": provider}
        if redirect_to:
            extra["redirect_to"] = redirect_to
        if session_id:
            extra["session_id"] = session_id
        state_token, _ = self._state_token_manager.create_token(
            token_type="oauth_state",
            user_id=provider,
            session_id=nonce,
            expires_in=ttl,
            scopes=(),
            extra=extra,
        )
        return state_token

    def verify_oauth_state(self, provider: str, state: str) -> Dict[str, str]:
        try:
            payload = self._state_token_manager.decode(state, expected_type="oauth_state")
        except TokenError as exc:
            raise AuthError("Invalid OAuth state token") from exc

        if payload.user_id != provider:
            raise AuthError("OAuth state provider mismatch")

        resolved: Dict[str, str] = {"nonce": payload.session_id}
        for key, value in payload.raw.items():
            if key in {"nonce", "sid"}:
                continue
            resolved[key] = str(value)
        return resolved

    # Token helpers
    def create_access_token(self, user_id: str, session_id: str, scopes: Tuple[str, ...] = ()) -> Tuple[str, datetime]:
        return self.token_manager.create_token(
            token_type="access",
            user_id=user_id,
            session_id=session_id,
            expires_in=timedelta(minutes=self.config.access_token_lifetime_minutes or 30),
            scopes=scopes,
        )

    def create_refresh_token(self, user_id: str, session_id: str) -> Tuple[str, datetime]:
        return self.token_manager.create_token(
            token_type="refresh",
            user_id=user_id,
            session_id=session_id,
            expires_in=timedelta(hours=self.config.refresh_token_lifetime_hours or 24),
            scopes=(),
        )

    def decode_access_token(self, token: str) -> TokenPayload:
        return self.token_manager.decode(token, expected_type="access")

    def decode_refresh_token(self, token: str) -> TokenPayload:
        return self.token_manager.decode(token, expected_type="refresh")

    # Email validation
    def is_email_allowed(self, email: str) -> bool:
        patterns = self.config.allowed_email_patterns
        if not patterns:
            return True  # Allow all if no patterns supplied
        return any(fnmatch.fnmatch(email.lower(), pattern.lower()) for pattern in patterns)

    # HTTP helpers
    @staticmethod
    def auth_required_exception(detail: str = "Authentication required") -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def forbidden_exception(detail: str = "Not allowed") -> HTTPException:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
