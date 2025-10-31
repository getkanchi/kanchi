"""Authentication API routes."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Iterable, List, Set
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from config import Config
from database import UserDB
from models import (
    AuthConfigResponse,
    AuthTokens,
    BasicLoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    UserInfo,
)
from security.auth import AuthError, AuthenticatedUser
from services import AuthService

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    def get_db():
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    def get_config() -> Config:
        if not app_state.config:
            app_state.config = Config.from_env()
        return app_state.config

    def require_auth_service(db_session=Depends(get_db)) -> AuthService:
        config = get_config()
        if not config.auth_enabled:
            raise HTTPException(status_code=404, detail="Authentication disabled")
        if not app_state.auth_manager:
            raise HTTPException(status_code=500, detail="Authentication not initialized")
        return AuthService(db_session, app_state.auth_manager)

    async def require_authenticated_user(request: Request):
        deps = app_state.auth_dependencies
        config = get_config()
        if not deps:
            if config.auth_enabled:
                raise HTTPException(status_code=500, detail="Authentication dependencies not initialized")
            raise HTTPException(status_code=404, detail="Authentication disabled")
        return await deps.require_user(request)  # type: ignore[func-returns-value]

    async def optional_authenticated_user(request: Request):
        deps = app_state.auth_dependencies
        if not deps:
            return None
        return await deps.optional_user(request)  # type: ignore[func-returns-value]

    @router.get("/config", response_model=AuthConfigResponse)
    async def fetch_auth_config(config: Config = Depends(get_config)):
        manager = app_state.auth_manager
        providers = manager.list_enabled_oauth_providers() if manager else []
        basic_enabled = bool(
            config.auth_enabled
            and config.auth_basic_enabled
            and config.basic_auth_username
            and (config.basic_auth_password or config.basic_auth_password_hash)
        )
        return AuthConfigResponse(
            auth_enabled=config.auth_enabled,
            basic_enabled=basic_enabled,
            oauth_providers=providers,
            allowed_email_patterns=config.allowed_email_patterns or [],
        )

    @router.post("/basic/login", response_model=LoginResponse)
    async def basic_login(
        payload: BasicLoginRequest,
        auth_service: AuthService = Depends(require_auth_service),
        config: Config = Depends(get_config),
    ):
        if not config.auth_basic_enabled:
            raise HTTPException(status_code=404, detail="Basic authentication disabled")

        try:
            result = auth_service.basic_login(
                payload.username.strip(),
                payload.password,
                session_id=payload.session_id,
            )
        except AuthError as exc:
            logger.warning("Basic login failed for user %s: %s", payload.username, exc)
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        return _login_result_to_response(result)

    @router.post("/refresh", response_model=LoginResponse)
    async def refresh_tokens(
        payload: RefreshRequest,
        auth_service: AuthService = Depends(require_auth_service),
    ):
        try:
            result = auth_service.refresh_tokens(payload.refresh_token)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        return _login_result_to_response(result)

    @router.post("/logout", status_code=204)
    async def logout(
        payload: LogoutRequest,
        auth_service: AuthService = Depends(require_auth_service),
        current_user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    ):
        session_id = payload.session_id or (current_user.session_id if isinstance(current_user, AuthenticatedUser) else None)
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required to logout")

        auth_service.logout_session(session_id)
        return Response(status_code=204)

    @router.get("/me", response_model=UserInfo)
    async def get_current_user(
        db_session=Depends(get_db),
        current_user: AuthenticatedUser = Depends(require_authenticated_user),
    ):
        if not current_user or not isinstance(current_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")

        user = db_session.query(UserDB).filter(UserDB.id == current_user.id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserInfo(
            id=user.id,
            email=user.email,
            provider=user.provider,
            name=user.name,
            avatar_url=user.avatar_url,
        )

    @router.get("/oauth/{provider}/authorize")
    async def oauth_authorize(  # type: ignore[override]
        provider: str,
        redirect_to: Optional[str] = Query(default=None),
        session_id: Optional[str] = Query(default=None),
        auth_service: AuthService = Depends(require_auth_service),
    ):
        try:
            authorization_url, state = await auth_service.build_oauth_authorization_url(
                provider,
                redirect_to=redirect_to,
                session_id=session_id,
            )
        except AuthError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"authorization_url": authorization_url, "state": state}

    @router.get("/oauth/{provider}/callback")
    async def oauth_callback(  # type: ignore[override]
        provider: str,
        request: Request,
        code: Optional[str] = Query(default=None),
        state: Optional[str] = Query(default=None),
        error: Optional[str] = Query(default=None),
        session_id: Optional[str] = Query(default=None),
        auth_service: AuthService = Depends(require_auth_service),
    ):
        config = get_config()

        if error:
            logger.error("OAuth callback error from %s: %s", provider, error)
            allowed_origins = _resolve_post_message_origins(config, None, request)
            return _oauth_error_response(error, allowed_origins)
        if not code or not state:
            allowed_origins = _resolve_post_message_origins(config, None, request)
            return _oauth_error_response("Missing OAuth response parameters", allowed_origins)

        try:
            result, redirect_to = await auth_service.complete_oauth_login(
                provider,
                code=code,
                state=state,
                session_id=session_id,
            )
        except AuthError as exc:
            logger.error("OAuth login failed for provider %s: %s", provider, exc)
            allowed_origins = _resolve_post_message_origins(config, None, request)
            return _oauth_error_response(str(exc), allowed_origins)

        login_response = _login_result_to_dict(result)
        redirect_target = _resolve_redirect_target(redirect_to, config, request)
        allowed_origins = _resolve_post_message_origins(config, redirect_target, request)

        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header.lower():
            payload = dict(login_response)
            if redirect_target:
                payload["redirect_to"] = redirect_target
            return JSONResponse(payload)

        html_content = _build_oauth_callback_html(login_response, redirect_target, allowed_origins)
        return HTMLResponse(content=html_content)

    return router


def _login_result_to_response(result) -> LoginResponse:
    payload = _login_result_to_dict(result)
    return LoginResponse(
        user=UserInfo(**payload["user"]),
        tokens=AuthTokens(**payload["tokens"]),
        provider=payload["provider"],
    )


def _login_result_to_dict(result) -> dict:
    now = datetime.now(timezone.utc)
    access_expires_in = max(0, int((result.access_token_expires_at - now).total_seconds()))
    refresh_expires_in = max(0, int((result.refresh_token_expires_at - now).total_seconds()))

    return {
        "user": {
            "id": result.user.id,
            "email": result.user.email,
            "provider": result.session.auth_provider or result.user.provider,
            "name": result.user.name,
            "avatar_url": result.user.avatar_url,
        },
        "tokens": {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "bearer",
            "expires_in": access_expires_in,
            "refresh_expires_in": refresh_expires_in,
            "session_id": result.session.session_id,
        },
        "provider": result.session.auth_provider or result.user.provider,
    }


def _oauth_error_response(message: str, allowed_origins: List[str]) -> HTMLResponse:
    html_content = _build_oauth_callback_html({"error": message}, redirect="", allowed_origins=allowed_origins)
    return HTMLResponse(status_code=400, content=html_content)


def _build_oauth_callback_html(payload: dict, redirect: str, allowed_origins: Iterable[str]) -> str:
    serialized = json.dumps(payload)
    redirect_str = json.dumps(redirect)
    origins_str = json.dumps(sorted(set(origin for origin in allowed_origins if origin)))
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>Authentication complete</title></head>
<body>
<script>
  (function() {{
    const payload = {serialized};
    const redirectTarget = {redirect_str};
    const allowedOrigins = new Set({origins_str});

    function sendToOpener() {{
      if (!window.opener || typeof window.opener.postMessage !== 'function') {{
        return false;
      }}

      let delivered = false;
      allowedOrigins.forEach((origin) => {{
        if (!origin || delivered) {{
          return;
        }}
        try {{
          window.opener.postMessage({{"type": "oauth-complete", "payload": payload}}, origin);
          delivered = true;
        }} catch (err) {{
          console.warn('Failed to send OAuth payload to origin:', origin, err);
        }}
      }});

      if (delivered) {{
        window.close();
        return true;
      }}
      return false;
    }}

    if (sendToOpener()) {{
      return;
    }}

    if (window.opener && typeof window.opener.postMessage === 'function') {{
      console.warn('No allowed origins matched for OAuth postMessage; falling back to redirect.');
    }}

    if (redirectTarget) {{
      window.location.href = redirectTarget;
      return;
    }}
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(payload, null, 2);
    document.body.textContent = '';
    document.body.appendChild(pre);
  }})();
</script>
</body>
</html>"""


def _resolve_redirect_target(redirect_to: Optional[str], config: Config, request: Request) -> str:
    """Return an absolute redirect target or empty string when unavailable."""
    if not redirect_to:
        return config.oauth_redirect_base_url or ""

    if redirect_to.startswith("/"):
        base = config.oauth_redirect_base_url or str(request.base_url)
        return urljoin(base, redirect_to.lstrip("/"))

    return redirect_to


def _resolve_post_message_origins(config: Config, redirect_target: Optional[str], request: Request) -> List[str]:
    """Build a deterministic list of origins we allow for postMessage targets."""
    origins: Set[str] = set()

    request_origin = f"{request.url.scheme}://{request.url.netloc}"
    origins.add(request_origin)

    if config.oauth_redirect_base_url:
        origin = _extract_origin(config.oauth_redirect_base_url)
        if origin:
            origins.add(origin)

    for item in config.allowed_origins or []:
        origin = _extract_origin(item)
        if origin:
            origins.add(origin)

    if redirect_target:
        origin = _extract_origin(redirect_target)
        if origin:
            origins.add(origin)

    return sorted(origins)


def _extract_origin(value: str) -> Optional[str]:
    """Extract the scheme/host pair from a URL-like string."""
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme:
        parsed = urlparse(f"https://{value}")
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return None
