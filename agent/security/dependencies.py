"""FastAPI dependencies for authentication."""

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request

from config import Config
from database import DatabaseManager
from security.auth import (
    AnonymousUser,
    AuthenticatedUser,
    AuthManager,
    AuthError,
)
from security.tokens import TokenError
from services.auth_service import AuthService


@dataclass
class AuthDependencies:
    """Container for lazily-evaluated dependency callables."""
    require_user: callable
    optional_user: callable


def build_auth_dependencies(
    config: Config,
    db_manager: Optional[DatabaseManager],
    auth_manager: Optional[AuthManager],
) -> AuthDependencies:
    """Factory returning dependency callables bound to runtime state."""

    async def require_user_dependency(request: Request) -> AuthenticatedUser:
        user = await _resolve_user(request, config, db_manager, auth_manager, require=True)
        if not isinstance(user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")
        return user

    async def optional_user_dependency(request: Request):
        resolved = await _resolve_user(request, config, db_manager, auth_manager, require=False)
        return resolved

    return AuthDependencies(
        require_user=require_user_dependency,
        optional_user=optional_user_dependency,
    )


def get_auth_dependency(app_state, *, require: bool):
    """Return a dependency callable bound to the application state."""

    async def dependency(request: Request):
        config = app_state.config or Config.from_env()
        if not config.auth_enabled:
            return AnonymousUser()

        if not app_state.auth_dependencies:
            raise HTTPException(status_code=500, detail="Authentication not initialized")

        handler = app_state.auth_dependencies.require_user if require else app_state.auth_dependencies.optional_user
        return await handler(request)  # type: ignore[func-returns-value]

    return dependency


async def _resolve_user(
    request: Request,
    config: Config,
    db_manager: Optional[DatabaseManager],
    auth_manager: Optional[AuthManager],
    require: bool,
):
    """Resolve the current user context."""
    if not config.auth_enabled:
        return AnonymousUser()

    if not auth_manager or not db_manager:
        raise HTTPException(status_code=500, detail="Authentication not initialized")

    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :].strip()

    if not token:
        if require:
            raise auth_manager.auth_required_exception()
        return AnonymousUser()

    try:
        with db_manager.get_session() as session:
            auth_service = AuthService(session, auth_manager)
            auth_user = auth_service.authenticate_access_token(token)
            request.state.auth = auth_user
            return auth_user
    except (AuthError, TokenError) as exc:
        if require:
            raise auth_manager.auth_required_exception(str(exc)) from exc
        return AnonymousUser()
