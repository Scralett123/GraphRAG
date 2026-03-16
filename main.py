"""
Modular RAG MCP Server - Main Entry Point

This module currently provides two entry points:

1. ``main()`` – CLI entry used by the ``mcp-server`` console script. It
   validates configuration and logging, and will host the MCP server in a
   future phase.
2. ``run_health_server()`` – a tiny HTTP server that exposes ``GET /health``
   for container health checks. When the environment variable
   ``RUN_HEALTH_SERVER=1`` is set and the module is executed as ``__main__``,
   this health server is started instead of the CLI entrypoint.
"""

from __future__ import annotations

import http.server
import json
import os
import socketserver
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict

from src.core.settings import SettingsError, load_settings
from src.observability.logger import get_logger


def main() -> int:
    """
    Main entry point for the MCP Server.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    print("Modular RAG MCP Server - Starting...")

    settings_path = Path("config/settings.yaml")
    try:
        settings = load_settings(settings_path)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = get_logger(log_level=settings.observability.log_level)
    logger.info("Settings loaded successfully.")
    logger.info("MCP Server will be implemented in Phase E.")
    return 0


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler serving GET /health for container probes."""

    server_start_time = time.time()
    settings_ok = False
    last_error: str | None = None

    def _build_payload(self) -> Dict[str, Any]:
        uptime = time.time() - self.server_start_time
        status = "ok" if self.settings_ok else "degraded"
        data: Dict[str, Any] = {
            "status": status,
            "uptime_seconds": round(uptime, 2),
        }
        if self.last_error:
            data["error"] = self.last_error
        return data

    def do_GET(self) -> None:  # type: ignore[override]
        if self.path not in ("/health", "/healthz"):
            self.send_response(404)
            self.end_headers()
            return

        payload = self._build_payload()
        body = json.dumps(payload).encode("utf-8")

        self.send_response(200 if payload["status"] == "ok" else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Silence default request logging to keep stderr clean.
        return


def run_health_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Run a minimal HTTP server exposing GET /health.

    The handler attempts to load settings once at startup to validate that
    configuration and basic paths are sound. This is intentionally simple
    and is only meant for container-level liveness/readiness checks.
    """
    # Try to load settings once; stash result on the handler class
    try:
        settings = load_settings()
        _HealthHandler.settings_ok = True
        _HealthHandler.last_error = None
        # Optionally, we could check that the vector_store path exists
        persist_dir = Path(settings.vector_store.persist_directory)
        if not persist_dir.is_absolute():
            from src.core.settings import resolve_path

            persist_dir = resolve_path(persist_dir)
        persist_dir.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        _HealthHandler.settings_ok = False
        _HealthHandler.last_error = str(exc)

    with socketserver.TCPServer((host, port), _HealthHandler) as httpd:
        print(f"Health server listening on http://{host}:{port}/health")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    if os.getenv("RUN_HEALTH_SERVER") == "1":
        # In container mode we start the health server instead of the CLI.
        run_health_server()
    else:
        sys.exit(main())

