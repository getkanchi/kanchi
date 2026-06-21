import anyio
from fastapi.routing import APIRoute
from starlette.requests import Request

from app import create_app


async def request_app(app, path: str, accept: str = "text/html", root_path: str = ""):
    messages = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": root_path,
        "headers": [(b"host", b"testserver"), (b"accept", accept.encode())],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    headers = {
        key.decode().lower(): value.decode()
        for key, value in start.get("headers", [])
    }
    return start["status"], headers, body


async def websocket_app(app, path: str, root_path: str = ""):
    messages = []
    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "scheme": "ws",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": root_path,
        "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "subprotocols": [],
    }

    async def receive():
        return {"type": "websocket.connect"}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    return messages


def test_frontend_static_mount_uses_generated_ui_directory(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Kanchi UI</html>", encoding="utf-8")
    (frontend_dir / "200.html").write_text("<html>Nuxt shell</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))

    app = create_app()

    root_route = next(
        route for route in app.routes if isinstance(route, APIRoute) and route.path == "/"
    )
    assert root_route.include_in_schema is False

    status, _, body = anyio.run(request_app, app, "/ui/")

    assert status == 200
    assert b"Kanchi UI" in body


def test_frontend_static_mount_prefixes_generated_ui_assets(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        "\n".join(
            [
                "<!DOCTYPE html>",
                '<html><head><link rel="modulepreload" href="/ui/_nuxt/app.js"></head>',
                "<body>",
                '<div id="__nuxt"></div><script type="module" src="/ui/_nuxt/entry.js"></script>',
                "</body></html>",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.setenv("NUXT_PUBLIC_URL_PREFIX", "/kanchi")

    app = create_app()
    status, _, body = anyio.run(request_app, app, "/ui/")

    assert status == 200
    assert b'"/kanchi/ui/_nuxt/app.js"' in body
    assert b'"/kanchi/ui/_nuxt/entry.js"' in body
    assert b"__KANCHI_UI_ENV__" not in body


def test_frontend_static_mount_leaves_assets_unprefixed_without_url_prefix(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        '<html><head><script src="/ui/_nuxt/app.js"></script></head><body>Kanchi</body></html>',
        encoding="utf-8",
    )

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))

    app = create_app()
    status, _, body = anyio.run(request_app, app, "/ui/")

    assert status == 200
    assert b'"/ui/_nuxt/app.js"' in body


def test_frontend_static_mount_uses_asgi_root_path_for_asset_prefix(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        '<html><head><script src="/ui/_nuxt/app.js"></script></head><body>Kanchi</body></html>',
        encoding="utf-8",
    )

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.delenv("NUXT_PUBLIC_URL_PREFIX", raising=False)

    app = create_app()
    status, _, body = anyio.run(request_app, app, "/kanchi/ui/", "text/html", "/kanchi")

    assert status == 200
    assert b'"/kanchi/ui/_nuxt/app.js"' in body


def test_frontend_static_mount_falls_back_for_dynamic_routes(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Nuxt shell</html>", encoding="utf-8")
    (frontend_dir / "404.html").write_text("<html>Not found</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))

    app = create_app()

    status, _, body = anyio.run(request_app, app, "/ui/tasks/example-task")
    assert status == 200
    assert b"Nuxt shell" in body


def test_frontend_static_mount_falls_back_for_dynamic_routes_without_404(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Nuxt shell</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))

    app = create_app()

    status, _, body = anyio.run(request_app, app, "/ui/tasks/example-task")
    assert status == 200
    assert b"Nuxt shell" in body

    status, _, _ = anyio.run(request_app, app, "/ui/tasks/_payload.json")
    assert status == 404


def test_frontend_root_redirect_uses_url_prefix(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Kanchi UI</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.setenv("NUXT_PUBLIC_URL_PREFIX", "/kanchi")

    app = create_app()
    root_route = next(
        route for route in app.routes if isinstance(route, APIRoute) and route.path == "/"
    )
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = anyio.run(root_route.endpoint, request)

    assert response.headers["location"] == "/kanchi/ui/"


def test_frontend_root_redirect_uses_asgi_root_path(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Kanchi UI</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.delenv("NUXT_PUBLIC_URL_PREFIX", raising=False)

    app = create_app()
    root_route = next(
        route for route in app.routes if isinstance(route, APIRoute) and route.path == "/"
    )
    request = Request(
        {"type": "http", "method": "GET", "path": "/", "root_path": "/kanchi", "headers": []}
    )
    response = anyio.run(root_route.endpoint, request)

    assert response.headers["location"] == "/kanchi/ui/"


def test_frontend_root_redirect_prefers_configured_url_prefix(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Kanchi UI</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.setenv("NUXT_PUBLIC_URL_PREFIX", "/configured")

    app = create_app()
    root_route = next(
        route for route in app.routes if isinstance(route, APIRoute) and route.path == "/"
    )
    request = Request(
        {"type": "http", "method": "GET", "path": "/", "root_path": "/proxy", "headers": []}
    )
    response = anyio.run(root_route.endpoint, request)

    assert response.headers["location"] == "/configured/ui/"


def test_configured_root_path_serves_prefixed_ui_api_and_websocket(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        '<html><head><script src="/ui/_nuxt/app.js"></script></head><body>Kanchi</body></html>',
        encoding="utf-8",
    )

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.setenv("KANCHI_ROOT_PATH", "/kanchi")
    monkeypatch.delenv("ASGI_ROOT_PATH", raising=False)
    monkeypatch.delenv("NUXT_PUBLIC_URL_PREFIX", raising=False)

    app = create_app()

    assert app.root_path == "/kanchi"

    status, _, body = anyio.run(request_app, app, "/kanchi/ui/")
    assert status == 200
    assert b'"/kanchi/ui/_nuxt/app.js"' in body

    status, _, body = anyio.run(request_app, app, "/kanchi/api/health", "application/json")
    assert status == 200
    assert b'"status":"healthy"' in body

    messages = anyio.run(websocket_app, app, "/kanchi/ws")
    assert {
        "type": "websocket.close",
        "code": 1011,
        "reason": "Server not initialized",
    } in messages


def test_url_prefix_configures_root_path_for_backwards_compatibility(monkeypatch, tmp_path):
    frontend_dir = tmp_path / "ui"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>Kanchi UI</html>", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(frontend_dir))
    monkeypatch.delenv("KANCHI_ROOT_PATH", raising=False)
    monkeypatch.delenv("ASGI_ROOT_PATH", raising=False)
    monkeypatch.setenv("NUXT_PUBLIC_URL_PREFIX", "/kanchi")

    app = create_app()

    assert app.root_path == "/kanchi"

    status, headers, _ = anyio.run(request_app, app, "/kanchi/")
    assert status == 307
    assert headers["location"] == "/kanchi/ui/"
