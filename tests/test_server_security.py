import json
import threading
import unittest
from contextlib import ExitStack
from http import HTTPStatus
from unittest import mock
from urllib import error, request

import server


class ServerSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        server.clear_rate_limit_state()
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.AppHandler)
        self.base_url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        server.clear_rate_limit_state()

    def http_request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        req = request.Request(f"{self.base_url}{path}", data=body, headers=headers or {}, method=method)
        try:
            with request.urlopen(req, timeout=5) as response:
                return response.status, response.read(), dict(response.headers.items())
        except error.HTTPError as exc:
            body = exc.read()
            headers = dict(exc.headers.items())
            return exc.code, body, headers

    def test_public_page_is_served(self) -> None:
        status, body, _ = self.http_request("GET", "/")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("Veridia", body.decode("utf-8"))

    def test_legal_pages_are_served(self) -> None:
        for path in ("/gizlilik-politikasi.html", "/kvkk-aydinlatma-metni.html"):
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn("Veridia", body.decode("utf-8"))

    def test_sensitive_files_and_internal_paths_are_not_public(self) -> None:
        for path in ("/.env", "/.git/HEAD", "/analysis_snapshots.sqlite3", "/server.py", "/automation/README.md"):
            with self.subTest(path=path):
                status, _, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.NOT_FOUND)

    def test_analysis_endpoint_is_disabled_by_default(self) -> None:
        with mock.patch.object(server, "INSTAGRAM_ANALYSIS_ENABLED", False, create=True), mock.patch.object(
            server,
            "build_analysis",
            return_value={"ok": True},
        ):
            status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)

    def test_analysis_endpoint_rejects_disallowed_origins(self) -> None:
        with mock.patch.object(server, "INSTAGRAM_ANALYSIS_ENABLED", True, create=True), mock.patch.object(
            server,
            "build_analysis",
            return_value={"ok": True},
        ):
            status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "Origin": "https://evil.example"},
            )

        self.assertEqual(status, HTTPStatus.FORBIDDEN)

    def test_analysis_endpoint_applies_rate_limiting(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(server, "INSTAGRAM_ANALYSIS_ENABLED", True, create=True))
            stack.enter_context(mock.patch.object(server, "RATE_LIMIT_MAX_REQUESTS", 1, create=True))
            stack.enter_context(mock.patch.object(server, "RATE_LIMIT_WINDOW_SECS", 60, create=True))
            stack.enter_context(mock.patch.object(server, "build_analysis", return_value={"ok": True}))

            first_status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second_status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        self.assertEqual(first_status, HTTPStatus.OK)
        self.assertEqual(second_status, HTTPStatus.TOO_MANY_REQUESTS)

    def test_profile_image_proxy_rejects_lookalike_domains(self) -> None:
        with mock.patch.object(server, "fetch_binary_url", return_value=(b"ok", "image/png")):
            status, _, _ = self.http_request("GET", "/api/profile-image?src=https://evilfbcdn.net/image.png")

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)

    def test_internal_exceptions_do_not_leak_to_clients(self) -> None:
        with mock.patch.object(server, "INSTAGRAM_ANALYSIS_ENABLED", True, create=True), mock.patch.object(
            server,
            "build_analysis",
            side_effect=RuntimeError("top secret failure"),
        ):
            status, body, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertNotIn("top secret failure", payload["error"])


if __name__ == "__main__":
    unittest.main()
