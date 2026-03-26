"""Lightweight HTTP server for the collaborative lock dashboard.

Serves the dashboard HTML file with injected Supabase configuration. Designed to be
started by the lock_client CLI or used standalone.
"""

from __future__ import annotations

import http.server
import json
import os
import sys
import webbrowser
from functools import partial

from dotenv import load_dotenv

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_COLLAB_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_PROJECT_ROOT = os.path.abspath(os.path.join(_COLLAB_ROOT, ".."))

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


def serve(port: int = 0, open_browser: bool = True) -> None:
    """Start the dashboard server and optionally open the browser.

    Args:
        port: Port to bind to (0 = OS-assigned).
        open_browser: Whether to open the dashboard in the default browser.
    """
    html_path = os.path.join(_THIS_DIR, "index.html")
    if not os.path.exists(html_path):
        print(f"Dashboard file not found: {html_path}")
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Inject Supabase config
    config = {
        "url": os.getenv("SUPABASE_URL", ""),
        "anonKey": os.getenv("SUPABASE_ANON_KEY", ""),
        "serviceKey": os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
        "user": os.getenv("USERNAME") or os.getenv("USER") or "",
    }
    inject = f"<script>window.__SUPABASE_CONFIG__ = {json.dumps(config)};</script>\n"

    import tempfile

    tmp = tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".html", encoding="utf-8"
    )
    tmp.write(inject)
    tmp.write(content)
    tmp.flush()
    tmp.close()

    tmp_dir = os.path.dirname(tmp.name)
    filename = os.path.basename(tmp.name)

    Handler = partial(http.server.SimpleHTTPRequestHandler, directory=tmp_dir)

    # Silence HTTP logging
    RequestHandler = http.server.SimpleHTTPRequestHandler
    RequestHandler.log_message = lambda *a, **k: None  # type: ignore  # noqa

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/{filename}"

    print(f"Dashboard serving at: {url}")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collaborative Lock Dashboard Server")
    parser.add_argument("--port", type=int, default=0, help="Port (default: auto)")
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )
    args = parser.parse_args()
    serve(port=args.port, open_browser=not args.no_browser)
