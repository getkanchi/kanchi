import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from config import Config
from ui_routes import FrontendAssets, FrontendIndexRenderer, collect_frontend_env


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


def test_collect_frontend_env_normalizes_forwarded_host(monkeypatch):
    monkeypatch.delenv("NUXT_PUBLIC_API_URL", raising=False)
    monkeypatch.delenv("NUXT_PUBLIC_WS_URL", raising=False)

    request = make_request(
        {
            "host": "internal:8765",
            "x-forwarded-host": "kanchi.example.com, proxy.local",
            "x-forwarded-proto": "https, http",
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


def test_collect_frontend_env_uses_public_env_allowlist(monkeypatch):
    monkeypatch.setenv("NUXT_PUBLIC_API_URL", "https://api.example.com")
    monkeypatch.setenv("NUXT_PUBLIC_NOT_FOR_CLIENT", "secret-ish")

    env = collect_frontend_env(Config(), make_request({"host": "kanchi.example.com"}))

    assert env["NUXT_PUBLIC_API_URL"] == "https://api.example.com"
    assert "NUXT_PUBLIC_NOT_FOR_CLIENT" not in env


def test_frontend_index_renderer_injects_env_before_head(tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html><head></head><body></body></html>")
    renderer = FrontendIndexRenderer(
        index_path,
        lambda request: {"NUXT_PUBLIC_API_URL": "https://api.example.com"},
    )

    html = renderer.render(make_request())

    assert (
        '<script>window.__KANCHI_UI_ENV__={"NUXT_PUBLIC_API_URL":"https://api.example.com"};'
        "</script>\n</head>"
    ) in html


def test_frontend_index_renderer_escapes_script_close(tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html><body></body></html>")
    renderer = FrontendIndexRenderer(
        index_path,
        lambda request: {"NUXT_PUBLIC_KANCHI_VERSION": "</script><script>alert(1)</script>"},
    )

    html = renderer.render(make_request())

    assert "<\\/script>" in html
    assert '"</script><script>alert(1)</script>"' not in html


def test_frontend_index_renderer_appends_env_without_head_or_body(tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<main></main>")
    renderer = FrontendIndexRenderer(
        index_path,
        lambda request: {"NUXT_PUBLIC_API_URL": "https://api.example.com"},
    )

    html = renderer.render(make_request())

    assert html.startswith("<main></main>\n<script>")


def test_frontend_assets_resolves_agent_prefixed_dist_path():
    assets = FrontendAssets(Config(frontend_dist_path="agent/ui"))

    assert assets.dist_dir == Path(__file__).resolve().parents[2] / "ui"


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
