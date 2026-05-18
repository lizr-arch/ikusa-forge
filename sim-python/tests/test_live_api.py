import json
import threading
import sys
import unittest
from pathlib import Path
from http.server import HTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from tempfile import TemporaryDirectory
import time


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.live_api import BattleSessionManager, LiveApiError  # noqa: E402
from ikusa_sim.live_api import create_live_api_server  # noqa: E402


class LiveApiManagerTests(unittest.TestCase):
    @staticmethod
    def _start_server(manager: BattleSessionManager) -> Tuple[HTTPServer, int]:
        server = create_live_api_server("127.0.0.1", 0, manager)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        # ensure background thread has started
        time.sleep(0.01)
        return server, server.server_address[1]

    @staticmethod
    def _stop_server(server: HTTPServer) -> None:
        server.shutdown()
        server.server_close()

    @staticmethod
    def _send_request(
        method: str,
        url: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, str], Optional[Any]]:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(url=url, data=payload, method=method)
        request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=5) as response:
                status = response.getcode()
                headers = {key: value for key, value in response.headers.items()}
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            headers = {key: value for key, value in exc.headers.items()}
            raw = exc.read().decode("utf-8")
        if not raw:
            return status, headers, None
        parsed = json.loads(raw)
        return status, headers, parsed

    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def create_manager(self):
        return BattleSessionManager(self.export_sample_config())

    def test_options_preflight_returns_cors_headers(self):
        manager = self.create_manager()
        server, port = self._start_server(manager)
        self.addCleanup(lambda: self._stop_server(server))

        status, headers, payload = self._send_request("OPTIONS", f"http://127.0.0.1:{port}/api/battle/start")
        self.assertIn(status, (200, 204))
        self.assertEqual("*", headers.get("Access-Control-Allow-Origin"))
        self.assertEqual("GET, POST, OPTIONS", headers.get("Access-Control-Allow-Methods"))
        self.assertEqual("Content-Type", headers.get("Access-Control-Allow-Headers"))
        # allow both preflight bodies to return either no body or JSON error envelope.
        if payload is not None:
            self.assertIn("ok", payload)

    def test_health_response_includes_cors_headers(self):
        manager = self.create_manager()
        server, port = self._start_server(manager)
        self.addCleanup(lambda: self._stop_server(server))

        status, headers, payload = self._send_request("GET", f"http://127.0.0.1:{port}/api/health")
        self.assertEqual(200, status)
        self.assertEqual("*", headers.get("Access-Control-Allow-Origin"))
        self.assertIsInstance(payload, dict)
        self.assertEqual("ikusa-live-api", payload["service"])
        self.assertTrue(payload["ok"])

    def test_bad_route_returns_json_error_with_cors(self):
        manager = self.create_manager()
        server, port = self._start_server(manager)
        self.addCleanup(lambda: self._stop_server(server))

        status, headers, payload = self._send_request("GET", f"http://127.0.0.1:{port}/api/does_not_exist")
        self.assertEqual(404, status)
        self.assertEqual("*", headers.get("Access-Control-Allow-Origin"))
        self.assertIsInstance(payload, dict)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)

    def test_create_session_returns_initialized_snapshot_and_events(self):
        manager = self.create_manager()

        session_id = manager.create_session("demo_001", 1001)
        snapshot = manager.snapshot(session_id)
        event_payload = manager.events_since(session_id, 0)
        event_types = [event["type"] for event in event_payload["events"]]

        json.dumps(snapshot)
        self.assertEqual("battle_snapshot.v0.1", snapshot["schema_version"])
        self.assertEqual("demo_001", snapshot["battle_id"])
        self.assertEqual(1001, snapshot["seed"])
        self.assertEqual(0, snapshot["tick"])
        self.assertFalse(snapshot["finished"])
        self.assertEqual(12, len(snapshot["units"]))
        self.assertIn("battle_start", event_types)
        self.assertEqual(12, event_types.count("unit_spawn"))
        self.assertIn("status_apply", event_types)
        self.assertEqual(snapshot["event_count"], event_payload["next_event_index"])

    def test_step_until_finished_produces_battle_end(self):
        manager = self.create_manager()
        session_id = manager.create_session("demo_001", 1001)

        steps = 0
        while not manager.snapshot(session_id)["finished"]:
            manager.step_session(session_id, ticks=5)
            steps += 1
            self.assertLessEqual(steps, 100)

        snapshot = manager.snapshot(session_id)
        all_events = manager.events_since(session_id, 0)
        event_types = [event["type"] for event in all_events["events"]]

        self.assertTrue(snapshot["finished"])
        self.assertEqual("ally", snapshot["result"]["winner"])
        self.assertEqual("enemy_eliminated", snapshot["result"]["reason"])
        self.assertGreater(snapshot["result"]["end_tick"], 240)
        self.assertEqual("battle_end", all_events["events"][-1]["type"])
        self.assertEqual(1, event_types.count("battle_end"))

    def test_events_since_cursor_returns_incremental_events(self):
        manager = self.create_manager()
        session_id = manager.create_session("demo_001", 1001)
        initial = manager.events_since(session_id, 0)
        old_index = initial["next_event_index"]

        manager.step_session(session_id, ticks=20)
        delta = manager.events_since(session_id, old_index)
        event_types = [event["type"] for event in delta["events"]]

        self.assertGreater(len(delta["events"]), 0)
        self.assertIn("unit_move", event_types)
        self.assertGreater(delta["next_event_index"], old_index)

    def test_unknown_session_returns_clear_error(self):
        manager = self.create_manager()

        with self.assertRaises(LiveApiError) as context:
            manager.snapshot("missing-session")

        self.assertEqual(404, context.exception.status)
        self.assertIn("unknown session_id", context.exception.message)

    def test_multiple_sessions_are_isolated(self):
        manager = self.create_manager()
        first_id = manager.create_session("demo_001", 1001)
        second_id = manager.create_session("demo_001", 1002)

        self.assertNotEqual(first_id, second_id)
        first_before = manager.snapshot(first_id)
        second_before = manager.snapshot(second_id)
        manager.step_session(first_id, ticks=20)
        first_after = manager.snapshot(first_id)
        second_after = manager.snapshot(second_id)

        self.assertEqual(0, first_before["tick"])
        self.assertEqual(0, second_before["tick"])
        self.assertEqual(20, first_after["tick"])
        self.assertEqual(0, second_after["tick"])
        self.assertGreater(first_after["event_count"], second_after["event_count"])

    def test_reset_session_removes_session(self):
        manager = self.create_manager()
        session_id = manager.create_session("demo_001", 1001)

        manager.reset_session(session_id)

        with self.assertRaises(LiveApiError) as context:
            manager.get_session(session_id)
        self.assertEqual(404, context.exception.status)

    def test_invalid_ticks_returns_bad_request_error(self):
        manager = self.create_manager()
        session_id = manager.create_session("demo_001", 1001)

        with self.assertRaises(LiveApiError) as context:
            manager.step_session(session_id, ticks=0)

        self.assertEqual(400, context.exception.status)
        self.assertEqual("invalid ticks", context.exception.message)


if __name__ == "__main__":
    unittest.main()
