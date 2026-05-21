import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from config import Config
from ui_routes import FrontendAssets, collect_frontend_env


def make_request(headers=None):
    encoded_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/ui",
            "scheme": "http",
            "server": ("127.0.0.1", 8765),
            "headers": encoded_headers,
        }
    )


def test_collect_frontend_env_uses_request_host_for_defaults(monkeypatch):
    monkeypatch.delenv("NUXT_PUBLIC_API_URL", raising=False)
    monkeypatch.delenv("NUXT_PUBLIC_WS_URL", raising=False)

    request = make_request(
        {
            "host": "internal:8765",
            "x-forwarded-host": "kanchi.example.com",
            "x-forwarded-proto": "https",
        }
    )

    env = collect_frontend_env(Config(), request)

    assert env["NUXT_PUBLIC_API_URL"] == "https://kanchi.example.com"
    assert env["NUXT_PUBLIC_WS_URL"] == "wss://kanchi.example.com/ws"


def test_collect_frontend_env_keeps_explicit_public_urls(monkeypatch):
    monkeypatch.setenv("NUXT_PUBLIC_API_URL", "https://api.example.com")
    monkeypatch.setenv("NUXT_PUBLIC_WS_URL", "wss://ws.example.com/live")

    env = collect_frontend_env(Config(), make_request({"host": "kanchi.example.com"}))

    assert env["NUXT_PUBLIC_API_URL"] == "https://api.example.com"
    assert env["NUXT_PUBLIC_WS_URL"] == "wss://ws.example.com/live"


def test_frontend_assets_return_404_for_missing_asset(tmp_path):
    (tmp_path / "index.html").write_text("<html><head></head><body></body></html>")
    assets = FrontendAssets(Config(frontend_dist_path=str(tmp_path)))

    request = make_request({"accept": "text/html"})

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(assets.serve(request, "_nuxt/missing.js"))

    assert exc_info.value.status_code == 404


def test_frontend_assets_fall_back_to_index_for_html_route(tmp_path):
    (tmp_path / "index.html").write_text("<html><head></head><body></body></html>")
    assets = FrontendAssets(Config(frontend_dist_path=str(tmp_path)))

    response = asyncio.run(assets.serve(make_request({"accept": "text/html"}), "tasks/example"))

    assert response.status_code == 200
