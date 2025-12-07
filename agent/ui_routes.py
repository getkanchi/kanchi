"""Routes for serving the built frontend from the backend."""

import json
import logging
import os
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import Config

logger = logging.getLogger(__name__)

# Expose frontend configuration on the window object for easy consumption.
ENV_TARGET = "window.__KANCHI_UI_ENV__"


def collect_frontend_env(config: Config) -> Dict[str, str]:
    """Collect frontend environment variables with sensible defaults."""
    env: Dict[str, str] = {
        key: value for key, value in os.environ.items() if key.startswith("NUXT_PUBLIC_")
    }

    env.setdefault("NUXT_PUBLIC_API_URL", f"http://{config.ws_host}:{config.ws_port}")
    env.setdefault("NUXT_PUBLIC_WS_URL", f"ws://{config.ws_host}:{config.ws_port}/ws")
    env.setdefault("NUXT_PUBLIC_KANCHI_VERSION", "dev")

    return env


class FrontendIndexRenderer:
    """Transform and optionally cache the frontend index.html with injected env."""

    def __init__(
        self,
        index_path: Path,
        env_provider: Callable[[], Dict[str, str]],
        cache_enabled: bool = True,
    ):
        self.index_path = index_path
        self.env_provider = env_provider
        self.cache_enabled = cache_enabled
        self._cache_key: Optional[Tuple[float, str]] = None
        self._cached_html: Optional[str] = None

    def render(self) -> str:
        """Return the transformed index.html with injected env."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Frontend index file missing at {self.index_path}")

        env = self.env_provider()
        env_payload = json.dumps(
            env, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        mtime = self.index_path.stat().st_mtime
        cache_key = (mtime, env_payload)

        if self.cache_enabled and self._cache_key == cache_key and self._cached_html:
            return self._cached_html

        html = self.index_path.read_text(encoding="utf-8")
        transformed = self._inject_env(html, env_payload)

        if self.cache_enabled:
            self._cache_key = cache_key
            self._cached_html = transformed

        return transformed

    def _inject_env(self, html: str, env_payload: str) -> str:
        script_tag = f"<script>{ENV_TARGET}={env_payload};</script>"

        if "</head>" in html:
            return html.replace("</head>", f"{script_tag}\n</head>", 1)
        if "</body>" in html:
            return html.replace("</body>", f"{script_tag}\n</body>", 1)

        return f"{html}\n{script_tag}"


class FrontendAssets:
    """Helper for serving frontend assets and the transformed index page."""

    def __init__(self, config: Config):
        self.config = config
        self.dist_dir = self._resolve_dist_dir(config.frontend_dist_path)
        self.index_path = self.dist_dir / config.frontend_index_file
        self.renderer = FrontendIndexRenderer(
            self.index_path,
            lambda: collect_frontend_env(config),
            cache_enabled=config.frontend_cache_index,
        )
        self.static_files = StaticFiles(directory=self.dist_dir, check_dir=False)

    def _resolve_dist_dir(self, path_value: str) -> Path:
        base_dir = Path(path_value).expanduser()
        if base_dir.is_absolute():
            return base_dir
        return Path(__file__).resolve().parent / base_dir

    async def serve(self, request: Request, path: str) -> Response:
        if path in ("", "/", "index.html"):
            return self._index_response()

        if not self.dist_dir.exists():
            logger.warning("Frontend dist directory not found at %s", self.dist_dir)
            raise HTTPException(
                status_code=404,
                detail="Frontend build not found. Please build the UI assets.",
            )

        response = await self.static_files.get_response(path, request.scope)
        if response.status_code < 400:
            return response  # type: ignore[return-value]

        return self._index_response()

    def _index_response(self) -> HTMLResponse:
        try:
            html = self.renderer.render()
        except FileNotFoundError as exc:
            logger.warning("Frontend index file missing: %s", exc)
            raise HTTPException(
                status_code=404,
                detail="Frontend build not found. Please build the UI assets.",
            ) from exc

        return HTMLResponse(
            content=html,
            media_type="text/html",
            headers={"Cache-Control": "no-store"},
        )


def create_router(app_state) -> APIRouter:
    """Create router that serves the built frontend under /ui."""
    router = APIRouter(tags=["ui"])
    config = app_state.config or Config.from_env()

    frontend_assets = FrontendAssets(config)
    app_state.frontend_assets = frontend_assets

    @router.get("/ui", include_in_schema=False)
    async def ui_index(request: Request):
        return await frontend_assets.serve(request, "")

    @router.get("/ui/{path:path}", include_in_schema=False)
    async def ui_assets(path: str, request: Request):
        return await frontend_assets.serve(request, path)

    return router
