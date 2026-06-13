"""Serve the QuizCat TUI over the web for deployment.

``textual-serve`` runs the normal terminal app in a subprocess and bridges it
to a browser via a websocket terminal, so the exact same ``main.py`` that runs
locally is what visitors interact with. This wrapper only handles the bits a
hosting platform (e.g. render.com) cares about: bind to ``0.0.0.0`` and the
port supplied in ``$PORT``.

Run locally with::

    uv run python serve.py

then open http://localhost:8000.
"""

import os
import sys

from textual_serve.server import Server


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    # Behind a TLS proxy (render), the browser loads the page over https but
    # textual-serve would otherwise hand it a ws://0.0.0.0:$PORT websocket URL
    # built from host/port — unreachable and mixed-content blocked, so the app
    # hangs on the loading screen. render publishes the real external URL as
    # RENDER_EXTERNAL_URL; passing it makes the websocket wss://<host>/ws.
    # Unset locally → None → textual-serve falls back to host:port (fine for dev).
    public_url = os.environ.get("RENDER_EXTERNAL_URL")
    # Use this interpreter so the spawned app inherits the same environment
    # (installed deps, env vars) regardless of how PATH is set up.
    command = f"{sys.executable} main.py"
    server = Server(
        command, host="0.0.0.0", port=port, title="QuizCat", public_url=public_url
    )
    server.serve()


if __name__ == "__main__":
    main()
