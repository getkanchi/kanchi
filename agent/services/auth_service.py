"""Authentication service handling user and session lifecycle."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from uuid import uuid4
from urllib.parse import urlencode, urlparse, urljoin

import aiohttp
from sqlalchemy.orm import Session

from database import UserDB, UserSessionDB
from security.auth import (
    AuthManager,
    AuthError,
    AuthenticatedUser,
)

logger = logging.getLogger(__name__)


@dataclass
class LoginResult:
    """Result returned after a successful login/refresh."""
    user: UserDB
    session: UserSessionDB
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime


class AuthService:
    """Service encapsulating authentication and token management logic."""

    def __init__(self, session: Session, auth_manager: AuthManager):
        self.session = session
        self.auth_manager = auth_manager

    @staticmethod
    def _normalize_timestamp(value: Optional[datetime]) -> Optional[datetime]:
        """Return a timezone-aware timestamp (assumes UTC when naive)."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    def authenticate_access_token(self, token: str) -> AuthenticatedUser:
        payload = self.auth_manager.decode_access_token(token)

        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == payload.session_id
        ).first()
        if not session_db or not session_db.user_id:
            raise AuthError("Session not found for token")

        if session_db.access_token_hash != self.auth_manager.token_manager.hash_token(token):
            raise AuthError("Access token mismatch")

        access_expiry = self._normalize_timestamp(session_db.access_token_expires_at)

        if access_expiry and access_expiry <= datetime.now(timezone.utc):
            raise AuthError("Access token expired")

        user = self.session.query(UserDB).filter(UserDB.id == payload.user_id).first()
        if not user:
            raise AuthError("User not found")

        if not user.is_active:
            raise AuthError("User is inactive")

        session_db.last_active = datetime.now(timezone.utc)
        session_db.access_token_expires_at = payload.expires_at
        self.session.commit()

        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            provider=session_db.auth_provider or user.provider,
            session_id=session_db.session_id,
            name=user.name,
            scopes=tuple(session_db.token_scopes or payload.scopes),
        )

    def authenticate_refresh_token(self, token: str) -> UserSessionDB:
        payload = self.auth_manager.decode_refresh_token(token)
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == payload.session_id
        ).first()
        if not session_db or not session_db.user_id:
            raise AuthError("Session not found for refresh token")

        if session_db.refresh_token_hash != self.auth_manager.token_manager.hash_token(token):
            raise AuthError("Refresh token mismatch")

        refresh_expiry = self._normalize_timestamp(session_db.refresh_token_expires_at)

        if refresh_expiry and refresh_expiry <= datetime.now(timezone.utc):
            raise AuthError("Refresh token expired")

        return session_db

    def logout_session(self, session_id: str) -> None:
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()
        if not session_db:
            return

        session_db.access_token_hash = None
        session_db.refresh_token_hash = None
        session_db.access_token_expires_at = None
        session_db.refresh_token_expires_at = None
        session_db.token_scopes = []
        session_db.last_active = datetime.now(timezone.utc)
        self.session.commit()

    # ------------------------------------------------------------------
    # Login flows
    # ------------------------------------------------------------------
    def basic_login(self, username: str, password: str, session_id: Optional[str] = None) -> LoginResult:
        if not self.auth_manager.verify_basic_credentials(username, password):
            raise AuthError("Invalid username or password")

        email = username.lower()
        if not self.auth_manager.is_email_allowed(email):
            raise AuthError("Email not allowed")

        user = self._get_or_create_user(
            provider="basic",
            email=email,
            name=username,
            provider_account_id=email,
            avatar_url=None,
        )
        return self._create_session_for_user(user, provider="basic", scopes=(), session_id=session_id)

    async def build_oauth_authorization_url(
        self,
        provider: str,
        redirect_to: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        provider_cfg = self.auth_manager.get_oauth_provider(provider)
        if not provider_cfg.is_available():
            raise AuthError(f"{provider_cfg.name.title()} OAuth is not configured")

        sanitized_redirect = self._sanitize_redirect_target(redirect_to)

        state_token = self.auth_manager.create_oauth_state(
            provider,
            redirect_to=sanitized_redirect,
            session_id=session_id,
        )
        redirect_uri = self.auth_manager.build_oauth_redirect_uri(provider)

        params = {
            "client_id": provider_cfg.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(provider_cfg.scope),
            "state": state_token,
        }
        if provider_cfg.name == "google":
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        authorize_url = f"{provider_cfg.authorize_url}?{urlencode(params)}"
        return authorize_url, state_token

    async def complete_oauth_login(
        self,
        provider: str,
        code: str,
        state: str,
        session_id: Optional[str] = None,
    ) -> Tuple[LoginResult, Optional[str]]:
        provider_cfg = self.auth_manager.get_oauth_provider(provider)
        if not provider_cfg.is_available():
            raise AuthError(f"{provider_cfg.name.title()} OAuth is not configured")

        state_payload = self.auth_manager.verify_oauth_state(provider, state)
        redirect_uri = self.auth_manager.build_oauth_redirect_uri(provider)
        session_from_state = state_payload.get("session_id")
        redirect_to = self._sanitize_redirect_target(state_payload.get("redirect_to"))

        token_data = await self._exchange_oauth_code(provider_cfg, code, redirect_uri)
        userinfo = await self._fetch_userinfo(provider_cfg, token_data)

        email = (userinfo.get("email") or "").lower()
        if not email:
            raise AuthError("Email not available from provider")
        if not self.auth_manager.is_email_allowed(email):
            raise AuthError("Email not allowed")

        provider_account_id = str(
            userinfo.get("sub")
            or userinfo.get("id")
            or userinfo.get("user_id")
            or email
        )

        user = self._get_or_create_user(
            provider=provider_cfg.name,
            email=email,
            name=userinfo.get("name") or userinfo.get("login") or email,
            provider_account_id=provider_account_id,
            avatar_url=userinfo.get("picture") or userinfo.get("avatar_url"),
        )

        scopes = tuple(provider_cfg.scope)
        login_result = self._create_session_for_user(
            user,
            provider=provider_cfg.name,
            scopes=scopes,
            session_id=session_id or session_from_state,
        )
        return login_result, redirect_to

    # ------------------------------------------------------------------
    # Token lifecycle
    # ------------------------------------------------------------------
    def refresh_tokens(self, refresh_token: str) -> LoginResult:
        session_db = self.authenticate_refresh_token(refresh_token)
        user = self.session.query(UserDB).filter(UserDB.id == session_db.user_id).first()
        if not user:
            raise AuthError("User not found for session")

        access_token, access_exp = self.auth_manager.create_access_token(
            user_id=user.id,
            session_id=session_db.session_id,
            scopes=tuple(session_db.token_scopes or ()),
        )
        new_refresh_token, refresh_exp = self.auth_manager.create_refresh_token(
            user_id=user.id,
            session_id=session_db.session_id,
        )

        session_db.access_token_hash = self.auth_manager.token_manager.hash_token(access_token)
        session_db.refresh_token_hash = self.auth_manager.token_manager.hash_token(new_refresh_token)
        session_db.access_token_expires_at = access_exp
        session_db.refresh_token_expires_at = refresh_exp
        session_db.last_active = datetime.now(timezone.utc)
        self.session.commit()

        return LoginResult(
            user=user,
            session=session_db,
            access_token=access_token,
            refresh_token=new_refresh_token,
            access_token_expires_at=access_exp,
            refresh_token_expires_at=refresh_exp,
        )

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _create_session_for_user(
        self,
        user: UserDB,
        provider: str,
        scopes: Tuple[str, ...],
        session_id: Optional[str] = None,
    ) -> LoginResult:
        now = datetime.now(timezone.utc)
        if session_id:
            session_db = self.session.query(UserSessionDB).filter(
                UserSessionDB.session_id == session_id
            ).first()
        else:
            session_db = None

        if session_db is None:
            session_db = UserSessionDB(
                session_id=session_id or str(uuid4()),
                preferences={},
                created_at=now,
                last_active=now,
            )
            self.session.add(session_db)
        else:
            session_db.last_active = now
            if not session_db.created_at:
                session_db.created_at = now

        session_db.user_id = user.id
        session_db.auth_provider = provider
        session_db.token_scopes = list(scopes)

        access_token, access_exp = self.auth_manager.create_access_token(
            user_id=user.id,
            session_id=session_db.session_id,
            scopes=scopes,
        )
        refresh_token, refresh_exp = self.auth_manager.create_refresh_token(
            user_id=user.id,
            session_id=session_db.session_id,
        )

        session_db.access_token_hash = self.auth_manager.token_manager.hash_token(access_token)
        session_db.refresh_token_hash = self.auth_manager.token_manager.hash_token(refresh_token)
        session_db.access_token_expires_at = access_exp
        session_db.refresh_token_expires_at = refresh_exp
        session_db.last_active = now

        user.last_login_at = now
        if not user.created_at:
            user.created_at = now
        user.updated_at = now

        self.session.commit()
        self.session.refresh(session_db)
        self.session.refresh(user)

        return LoginResult(
            user=user,
            session=session_db,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_exp,
            refresh_token_expires_at=refresh_exp,
        )

    def _get_or_create_user(
        self,
        provider: str,
        email: str,
        name: Optional[str],
        provider_account_id: str,
        avatar_url: Optional[str],
    ) -> UserDB:
        user = self.session.query(UserDB).filter(
            UserDB.email == email,
            UserDB.provider == provider,
        ).first()

        now = datetime.now(timezone.utc)
        if user:
            user.name = name or user.name
            user.provider_account_id = provider_account_id
            user.avatar_url = avatar_url or user.avatar_url
            user.updated_at = now
        else:
            user = UserDB(
                id=str(uuid4()),
                email=email,
                name=name or email,
                provider=provider,
                provider_account_id=provider_account_id,
                avatar_url=avatar_url,
                created_at=now,
                updated_at=now,
                last_login_at=now,
            )
            self.session.add(user)

        self.session.commit()
        self.session.refresh(user)
        return user

    def _sanitize_redirect_target(self, redirect_to: Optional[str]) -> Optional[str]:
        """Allow only relative redirects or URLs that match an approved origin."""
        if not redirect_to:
            return None

        trimmed = redirect_to.strip()
        if not trimmed:
            return None

        if trimmed.startswith("/"):
            return trimmed

        try:
            target = urlparse(trimmed)
        except ValueError:
            return None

        if not target.scheme or not target.netloc:
            return None

        origin = f"{target.scheme}://{target.netloc}"
        if origin not in self._allowed_oauth_origins():
            return None

        sanitized = target._replace(fragment="")
        return sanitized.geturl()

    def _allowed_oauth_origins(self) -> set[str]:
        """Build the set of origins permitted for OAuth redirects/postMessage."""
        config = self.auth_manager.config
        origins: set[str] = set()

        def add_origin(candidate: Optional[str]):
            if not candidate or candidate == "*":
                return
            parsed = urlparse(candidate)
            if not parsed.scheme:
                parsed = urlparse(f"https://{candidate}")
            if parsed.scheme and parsed.netloc:
                origins.add(f"{parsed.scheme}://{parsed.netloc}")

        add_origin(config.oauth_redirect_base_url)
        for item in config.allowed_origins or []:
            add_origin(item)

        return origins

    async def _exchange_oauth_code(self, provider_cfg, code: str, redirect_uri: str) -> Dict[str, any]:
        payload = {
            "client_id": provider_cfg.client_id,
            "client_secret": provider_cfg.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        headers = {"Accept": "application/json"}
        async with aiohttp.ClientSession() as client:
            async with client.post(provider_cfg.token_url, data=payload, headers=headers) as response:
                if response.status >= 400:
                    text = await response.text()
                    logger.error("OAuth token exchange failed: %s", text)
                    raise AuthError("Failed to exchange OAuth code for token")
                token_data = await response.json()
                return token_data

    async def _fetch_userinfo(self, provider_cfg, token_data: Dict[str, any]) -> Dict[str, any]:
        access_token = token_data.get("access_token")
        if not access_token:
            raise AuthError("OAuth provider did not return an access token")

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with aiohttp.ClientSession() as client:
            async with client.get(provider_cfg.userinfo_url, headers=headers) as response:
                if response.status >= 400:
                    text = await response.text()
                    logger.error("Failed to fetch user info: %s", text)
                    raise AuthError("Failed to fetch user info from provider")
                data = await response.json()

        # Github may not return email in primary call
        if provider_cfg.name == "github" and not data.get("email"):
            async with aiohttp.ClientSession() as client:
                async with client.get("https://api.github.com/user/emails", headers=headers) as response:
                    if response.status < 400:
                        emails = await response.json()
                        primary = next((item for item in emails if item.get("primary")), None)
                        if primary and primary.get("email"):
                            data["email"] = primary["email"]
        return data
