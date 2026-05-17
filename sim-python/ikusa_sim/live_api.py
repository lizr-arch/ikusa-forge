"""Local HTTP API for step-capable Ikusa Forge battles.

The API layer is intentionally thin: it owns JSON/HTTP concerns and delegates
all combat behavior to BattleSession. It uses only Python standard-library
server primitives so future hosts can test the contract without adding a web
framework dependency.
"""

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from ikusa_sim.battle_session import (
    BattleSession,
    build_battle_snapshot,
    create_battle_session,
    get_events_since,
    initialize_battle_session,
    step_battle_session,
)
from ikusa_sim.config_loader import ConfigLoadError, load_config
from ikusa_sim.events import event_to_dict
from ikusa_sim.models import ConfigBundle


class LiveApiServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class LiveApiError(Exception):
    """Raised for expected API failures that should become JSON errors."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class BattleSessionManager:
    """Owns live BattleSession instances for the local HTTP API."""

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = Path(config_dir)
        self.config = self._load_config(self.config_dir)
        self.sessions = {}  # type: Dict[str, BattleSession]
        self._lock = threading.RLock()

    def create_session(
        self,
        battle_id: str,
        seed: int,
        config_dir: Optional[Path] = None,
    ) -> str:
        if not isinstance(battle_id, str) or not battle_id:
            raise LiveApiError("missing battle_id", 400)
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise LiveApiError("invalid seed", 400)

        with self._lock:
            config = self.config
            if config_dir is not None:
                self.config_dir = Path(config_dir)
                self.config = self._load_config(self.config_dir)
                config = self.config

            try:
                session = create_battle_session(config, battle_id, seed)
            except ValueError as exc:
                raise LiveApiError(str(exc), 400) from exc

            initialize_battle_session(session)
            session_id = uuid.uuid4().hex
            self.sessions[session_id] = session
            return session_id

    def get_session(self, session_id: str) -> BattleSession:
        if not isinstance(session_id, str) or not session_id:
            raise LiveApiError("missing session_id", 400)
        with self._lock:
            session = self.sessions.get(session_id)
        if session is None:
            raise LiveApiError(f"unknown session_id: {session_id}", 404)
        return session

    def step_session(self, session_id: str, ticks: int) -> Dict[str, Any]:
        ticks = _validate_ticks(ticks)
        with self._lock:
            session = self.get_session(session_id)
            events = step_battle_session(session, ticks=ticks)
            return {
                "events": [event_to_dict(event) for event in events],
                "next_event_index": len(session.events),
            }

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            session = self.get_session(session_id)
            return build_battle_snapshot(session)

    def events_since(self, session_id: str, event_index: int) -> Dict[str, Any]:
        event_index = _validate_event_index(event_index)
        with self._lock:
            session = self.get_session(session_id)
            return get_events_since(session, event_index)

    def reset_session(self, session_id: str) -> None:
        if not isinstance(session_id, str) or not session_id:
            raise LiveApiError("missing session_id", 400)
        with self._lock:
            if session_id not in self.sessions:
                raise LiveApiError(f"unknown session_id: {session_id}", 404)
            del self.sessions[session_id]

    def _load_config(self, config_dir: Path) -> ConfigBundle:
        try:
            return load_config(Path(config_dir))
        except ConfigLoadError as exc:
            raise LiveApiError(str(exc), 400) from exc


def create_live_api_server(
    host: str,
    port: int,
    manager: BattleSessionManager,
) -> LiveApiServer:
    handler_class = build_live_api_handler(manager)
    return LiveApiServer((host, port), handler_class)


def build_live_api_handler(manager: BattleSessionManager):
    class LiveApiHandler(BaseHTTPRequestHandler):
        server_version = "IkusaLiveApi/0.1"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/health":
                    self._send_json(200, {"ok": True, "service": "ikusa-live-api"})
                    return
                if parsed.path == "/api/battle/snapshot":
                    query = parse_qs(parsed.query)
                    session_id = _query_value(query, "session_id")
                    self._send_json(200, {"ok": True, "snapshot": manager.snapshot(session_id)})
                    return
                if parsed.path == "/api/battle/events":
                    query = parse_qs(parsed.query)
                    session_id = _query_value(query, "session_id")
                    since = _parse_int(_query_value(query, "since", default="0"), "since")
                    payload = manager.events_since(session_id, since)
                    self._send_json(200, {"ok": True, **payload})
                    return
                raise LiveApiError(f"unsupported route: GET {parsed.path}", 404)
            except LiveApiError as exc:
                self._send_error(exc)
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                self._send_error(LiveApiError(str(exc), 500))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                body = self._read_json_body()
                if parsed.path == "/api/battle/start":
                    self._handle_start(body)
                    return
                if parsed.path == "/api/battle/step":
                    self._handle_step(body)
                    return
                if parsed.path == "/api/battle/reset":
                    session_id = _required_str(body, "session_id")
                    manager.reset_session(session_id)
                    self._send_json(200, {"ok": True})
                    return
                raise LiveApiError(f"unsupported route: POST {parsed.path}", 404)
            except LiveApiError as exc:
                self._send_error(exc)
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                self._send_error(LiveApiError(str(exc), 500))

        def _handle_start(self, body: Dict[str, Any]) -> None:
            battle_id = _required_str(body, "battle_id")
            seed = _required_int(body, "seed")
            config_dir = _optional_path(body, "config")
            session_id = manager.create_session(battle_id, seed, config_dir=config_dir)
            events_payload = manager.events_since(session_id, 0)
            self._send_json(
                200,
                {
                    "ok": True,
                    "session_id": session_id,
                    "snapshot": manager.snapshot(session_id),
                    **events_payload,
                },
            )

        def _handle_step(self, body: Dict[str, Any]) -> None:
            session_id = _required_str(body, "session_id")
            ticks = _required_int(body, "ticks")
            events_payload = manager.step_session(session_id, ticks)
            self._send_json(
                200,
                {
                    "ok": True,
                    "snapshot": manager.snapshot(session_id),
                    **events_payload,
                },
            )

        def _read_json_body(self) -> Dict[str, Any]:
            raw_length = self.headers.get("Content-Length", "0")
            length = _parse_int(raw_length, "Content-Length")
            if length < 0:
                raise LiveApiError("invalid Content-Length", 400)
            raw_body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(raw_body.decode("utf-8") or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise LiveApiError(f"bad JSON: {exc}", 400) from exc
            if not isinstance(data, dict):
                raise LiveApiError("request body must be a JSON object", 400)
            return data

        def _send_error(self, error: LiveApiError) -> None:
            self._send_json(error.status, {"ok": False, "error": error.message})

        def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
            encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return LiveApiHandler


def _query_value(query: Dict[str, Any], name: str, default: Optional[str] = None) -> str:
    values = query.get(name)
    if values:
        value = values[0]
        if isinstance(value, str) and value:
            return value
    if default is not None:
        return default
    raise LiveApiError(f"missing {name}", 400)


def _required_str(data: Dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise LiveApiError(f"missing {field}", 400)
    return value


def _required_int(data: Dict[str, Any], field: str) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise LiveApiError(f"invalid {field}", 400)
    return value


def _optional_path(data: Dict[str, Any], field: str) -> Optional[Path]:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise LiveApiError(f"invalid {field}", 400)
    return Path(value)


def _parse_int(value: str, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise LiveApiError(f"invalid {field}", 400) from exc


def _validate_ticks(ticks: int) -> int:
    if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks <= 0:
        raise LiveApiError("invalid ticks", 400)
    return ticks


def _validate_event_index(event_index: int) -> int:
    if not isinstance(event_index, int) or isinstance(event_index, bool) or event_index < 0:
        raise LiveApiError("invalid event_index", 400)
    return event_index
