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
        follow_redirects: bool = True,
    ) -> tuple[int, bytes, dict[str, str]]:
        req = request.Request(f"{self.base_url}{path}", data=body, headers=headers or {}, method=method)
        opener = request.build_opener() if follow_redirects else request.build_opener(server.NoRedirectHandler())
        try:
            with opener.open(req, timeout=5) as response:
                return response.status, response.read(), dict(response.headers.items())
        except error.HTTPError as exc:
            body = exc.read()
            headers = dict(exc.headers.items())
            return exc.code, body, headers

    def test_public_page_is_served(self) -> None:
        status, body, _ = self.http_request("GET", "/")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("Veridia", body.decode("utf-8"))

    def test_public_pages_send_hardened_security_headers(self) -> None:
        status, _, headers = self.http_request("GET", "/")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        csp = headers.get("Content-Security-Policy", "")
        script_policy = next((part.strip() for part in csp.split(";") if part.strip().startswith("script-src")), "")
        self.assertIn("frame-ancestors 'self'", csp)
        self.assertNotIn("fonts.googleapis.com", csp)
        self.assertNotIn("'unsafe-inline'", script_policy)

    def test_static_assets_are_cacheable(self) -> None:
        status, _, headers = self.http_request("GET", "/assets/config.js")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(headers.get("Cache-Control"), "public, max-age=31536000, immutable")

    def test_html_pages_require_revalidation(self) -> None:
        status, _, headers = self.http_request("GET", "/blog.html")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(headers.get("Cache-Control"), "no-cache, must-revalidate")

    def test_legal_pages_are_served(self) -> None:
        for path in ("/gizlilik-politikasi.html", "/kvkk-aydinlatma-metni.html"):
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn("Veridia", body.decode("utf-8"))

    def test_recent_root_pages_are_public(self) -> None:
        for path in (
            "/hakkimizda.html",
            "/calisma-surecimiz.html",
            "/hizli-teklif.html",
        ):
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn("Veridia", body.decode("utf-8"))

    def test_public_hub_routes_serve_directory_indexes(self) -> None:
        for path in ("/seo/", "/reklam/", "/yazilim/", "/sektorler/", "/hizmetler/"):
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn("Veridia", body.decode("utf-8"))

    def test_sector_landing_routes_are_public(self) -> None:
        routes = {
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/": "Güzellik Merkezleri İçin Dijital Pazarlama",
            "/sektorler/avukatlar-icin-dijital-pazarlama/": "Avukatlar İçin Dijital Pazarlama",
            "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/": "Estetik Klinikleri İçin Dijital Pazarlama",
            "/sektorler/dis-klinikleri-icin-dijital-pazarlama/": "Diş Klinikleri İçin Dijital Pazarlama",
            "/sektorler/kuaforler-icin-dijital-pazarlama/": "Kuaförler İçin Dijital Pazarlama",
            "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/": "Yerel Servis İşletmeleri İçin Dijital Pazarlama",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn(expected, body.decode("utf-8"))

    def test_service_landing_routes_are_public(self) -> None:
        routes = {
            "/hizmetler/web-tasarim/": "Web Tasarım Hizmeti",
            "/hizmetler/seo-danismanligi/": "SEO Danışmanlığı Hizmeti",
            "/hizmetler/google-ads-yonetimi/": "Google Ads Yönetimi",
            "/hizmetler/sosyal-medya-yonetimi/": "Sosyal Medya Yönetimi",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn(expected, body.decode("utf-8"))

    def test_slashless_hub_and_service_routes_redirect_to_canonical_urls(self) -> None:
        redirects = {
            "/seo": "/seo/",
            "/seo/teknik-seo-denetimi": "/seo/teknik-seo-denetimi/",
            "/seo/google-gorunurlugu": "/seo/google-gorunurlugu/",
            "/reklam": "/reklam/",
            "/reklam/sosyal-medya-yonetimi": "/reklam/sosyal-medya-yonetimi/",
            "/reklam/google-ads-yonetimi": "/reklam/google-ads-yonetimi/",
            "/reklam/meta-reklam-yonetimi": "/reklam/meta-reklam-yonetimi/",
            "/yazilim": "/yazilim/",
            "/yazilim/web-sitesi-ve-donusum-yuzeyleri": "/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/hizmetler": "/hizmetler/",
            "/hizmetler/web-tasarim": "/hizmetler/web-tasarim/",
            "/hizmetler/seo-danismanligi": "/hizmetler/seo-danismanligi/",
            "/hizmetler/google-ads-yonetimi": "/hizmetler/google-ads-yonetimi/",
            "/hizmetler/sosyal-medya-yonetimi": "/hizmetler/sosyal-medya-yonetimi/",
            "/sektorler": "/sektorler/",
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama": "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/",
            "/sektorler/avukatlar-icin-dijital-pazarlama": "/sektorler/avukatlar-icin-dijital-pazarlama/",
            "/sektorler/estetik-klinikleri-icin-dijital-pazarlama": "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/dis-klinikleri-icin-dijital-pazarlama": "/sektorler/dis-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/kuaforler-icin-dijital-pazarlama": "/sektorler/kuaforler-icin-dijital-pazarlama/",
            "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama": "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/",
        }

        for path, destination in redirects.items():
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), destination)

    def test_legacy_homepage_paths_redirect_to_root(self) -> None:
        for path in ("/index.html", "/asdfadsf.html", "/veridia-ajans.html"):
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), "/")

    def test_legacy_blog_slug_redirects_to_current_article(self) -> None:
        status, _, headers = self.http_request(
            "GET",
            "/blog/b2b-pazarlamada-donusum-hunisi.html",
            follow_redirects=False,
        )

        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(headers.get("Location"), "/blog/b2b-donusum-hunisi.html")

    def test_legacy_beauty_sector_url_redirects_to_canonical_sector_landing(self) -> None:
        for path in (
            "/guzellik-merkezleri-icin-dijital-pazarlama",
            "/guzellik-klinik-dijital-pazarlama.html",
        ):
            with self.subTest(path=path):
                status, _, headers = self.http_request(
                    "GET",
                    path,
                    follow_redirects=False,
                )

                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/")

    def test_legacy_service_pages_redirect_to_silo_urls(self) -> None:
        redirects = {
            "/web-tasarim.html": "/hizmetler/web-tasarim/",
            "/seo-danismanligi.html": "/hizmetler/seo-danismanligi/",
            "/google-ads-yonetimi.html": "/hizmetler/google-ads-yonetimi/",
            "/sosyal-medya-yonetimi.html": "/hizmetler/sosyal-medya-yonetimi/",
        }

        for path, destination in redirects.items():
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), destination)

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

    def test_contact_endpoint_accepts_valid_submission(self) -> None:
        with mock.patch.object(server, "CONTACT_FORWARD_URL", "", create=True):
            status, body, _ = self.http_request(
                "POST",
                "/api/contact",
                body=json.dumps(
                    {
                        "isim": "Ada Test",
                        "email": "ada@example.com",
                        "telefon": "+90 555 111 22 33",
                        "mesaj": "Web sitesi ve teklif akışı için bilgi almak istiyorum.",
                        "kaynak": "/",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])

    def test_contact_endpoint_validates_payload(self) -> None:
        status, body, _ = self.http_request(
            "POST",
            "/api/contact",
            body=json.dumps(
                {
                    "isim": "A",
                    "email": "invalid",
                    "mesaj": "kısa",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertFalse(payload["ok"])

    def test_analysis_endpoint_uses_forwarded_client_ip_from_trusted_proxy(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(server, "INSTAGRAM_ANALYSIS_ENABLED", True, create=True))
            stack.enter_context(mock.patch.object(server, "RATE_LIMIT_MAX_REQUESTS", 1, create=True))
            stack.enter_context(mock.patch.object(server, "RATE_LIMIT_WINDOW_SECS", 60, create=True))
            stack.enter_context(mock.patch.object(server, "TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"}), create=True))
            stack.enter_context(mock.patch.object(server, "build_analysis", return_value={"ok": True}))

            first_status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-For": "198.51.100.10",
                },
            )
            second_status, _, _ = self.http_request(
                "POST",
                "/api/analyze-instagram",
                body=json.dumps({"username": "veridia"}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-For": "203.0.113.77",
                },
            )

        self.assertEqual(first_status, HTTPStatus.OK)
        self.assertEqual(second_status, HTTPStatus.OK)

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

    def test_save_snapshot_finishes_after_inserting_record(self) -> None:
        connection = mock.MagicMock()
        connection.__enter__.return_value = connection
        with mock.patch.object(server, "ensure_snapshot_db"), mock.patch.object(
            server,
            "load_snapshots",
            return_value=[],
        ), mock.patch.object(server.sqlite3, "connect", return_value=connection):
            server.save_snapshot(
                {
                    "username": "veridia",
                    "followers": 1000,
                    "following": 100,
                    "post_count": 24,
                },
                mock.Mock(
                    overall_score=70,
                    representative_engagement_rate=2.4,
                    median_engagement_rate=2.3,
                    trimmed_engagement_rate=2.2,
                    audience_quality=72,
                    authenticity_risk=18,
                    consistency=68,
                    confidence=74,
                    posting_frequency_per_week=3.5,
                    benchmark_er=3.2,
                    profile_type="Marka Profili",
                    profile_archetype="brand",
                    account_tier="micro",
                ),
            )

        connection.execute.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
