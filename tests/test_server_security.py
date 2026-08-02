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
        status, _, headers = self.http_request("GET", "/blog")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(headers.get("Cache-Control"), "no-cache, must-revalidate")

    def test_legal_pages_are_served(self) -> None:
        for path in ("/gizlilik-politikasi", "/kvkk-aydinlatma-metni"):
            with self.subTest(path=path):
                status, body, _ = self.http_request("GET", path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIn("Veridia", body.decode("utf-8"))

    def test_recent_root_pages_are_public(self) -> None:
        for path in (
            "/hakkimizda",
            "/calisma-surecimiz",
            "/hizli-teklif",
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
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/": "Güzellik Merkezleri İçin Randevu Odaklı Dijital Pazarlama Hizmeti",
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

    def test_consolidated_service_routes_redirect_to_canonical_silos(self) -> None:
        redirects = {
            "/hizmetler/web-tasarim": "/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/hizmetler/seo-danismanligi": "/seo/google-gorunurlugu/",
            "/hizmetler/google-ads-yonetimi": "/reklam/google-ads-yonetimi/",
            "/hizmetler/sosyal-medya-yonetimi": "/reklam/sosyal-medya-yonetimi/",
        }

        for method in ("GET", "HEAD"):
            for source, destination in redirects.items():
                for path in (source, f"{source}/", f"{source}/index.html"):
                    with self.subTest(method=method, path=path):
                        status, _, headers = self.http_request(
                            method,
                            path,
                            follow_redirects=False,
                        )
                        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                        self.assertEqual(headers.get("Location"), destination)

        status, _, headers = self.http_request(
            "GET",
            "/hizmetler/google-ads-yonetimi/?utm_source=legacy",
            follow_redirects=False,
        )
        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(
            headers.get("Location"),
            "/reklam/google-ads-yonetimi/?utm_source=legacy",
        )

    def test_canonical_silo_service_routes_are_public(self) -> None:
        routes = {
            "/yazilim/web-sitesi-ve-donusum-yuzeyleri/": "Web Tasarım ve Landing Page",
            "/seo/google-gorunurlugu/": "SEO Danışmanlığı",
            "/reklam/google-ads-yonetimi/": "Google Ads Yönetimi",
            "/reklam/sosyal-medya-yonetimi/": "Sosyal Medya Yönetimi",
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
            "/araclar/site-analizi": "/araclar/site-analizi/",
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
        self.assertEqual(headers.get("Location"), "/blog/b2b-donusum-hunisi")

    def test_site_analysis_tool_route_is_public(self) -> None:
        status, body, _ = self.http_request("GET", "/araclar/site-analizi/")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("Site Analizi Aracı", body.decode("utf-8"))

        status, _, headers = self.http_request(
            "GET",
            "/araclar/site-analizi.html",
            follow_redirects=False,
        )
        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(headers.get("Location"), "/araclar/site-analizi/")

    def test_site_analysis_api_rejects_local_urls(self) -> None:
        status, body, _ = self.http_request(
            "POST",
            "/api/analyze",
            body=json.dumps({"url": "http://127.0.0.1:8000"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertEqual(payload["error"]["code"], "site_analysis_error")

    def test_site_analysis_api_returns_frontend_report_shape(self) -> None:
        html = """
        <!doctype html>
        <html>
          <head>
            <title>Örnek Web Sitesi Analiz Başlığı</title>
            <meta name="description" content="Bu açıklama arama sonucu için yeterli uzunlukta yazılmış örnek bir meta description metnidir ve kullanıcıya sayfanın değerini anlatır.">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="canonical" href="https://example.com/">
            <meta property="og:title" content="Örnek">
            <meta property="og:image" content="https://example.com/og.jpg">
            <script type="application/ld+json">{"@context":"https://schema.org","@type":"Service"}</script>
          </head>
          <body><h1>Örnek Başlık</h1><img src="/a.jpg" alt="Açıklayıcı görsel"></body>
        </html>
        """
        with mock.patch.object(
            server,
            "fetch_site_analysis_html",
            return_value={
                "final_url": "https://example.com/",
                "status": 200,
                "content_type": "text/html",
                "html": html,
                "elapsed_ms": 420,
                "redirects": 0,
            },
        ):
            status, body, _ = self.http_request(
                "POST",
                "/api/analyze",
                body=json.dumps({"url": "https://example.com"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, HTTPStatus.OK)
        self.assertIn("scores", payload["data"])
        self.assertIn("findings", payload["data"])
        self.assertEqual(payload["data"]["finalUrl"], "https://example.com/")

    def test_consolidated_beauty_article_redirects_to_pillar(self) -> None:
        for path in (
            "/blog/guzellik-merkezi-dijital-pazarlama",
            "/blog/guzellik-merkezi-dijital-pazarlama.html",
            "/guzellik-klinik-dijital-pazarlama",
            "/guzellik-klinik-dijital-pazarlama.html",
        ):
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), "/blog/guzellik-merkezleri-icin-dijital-pazarlama")

    def test_restored_beauty_articles_serve_clean_urls(self) -> None:
        for path in (
            "/blog/kadikoyde-guzellik-merkezi-nasil-one-cikar",
            "/blog/guzellik-merkezi-randevu-no-show-sorunu-nasil-azaltilir",
            "/blog/lazer-epilasyon-merkezi-icin-google-ads-rehberi",
            "/blog/yeni-acilan-guzellik-merkezi-dijital-kurulum-checklisti",
            "/blog/guzellik-salonu-instagramdan-musteri-nasil-bulur",
            "/blog/guzellik-merkezi-reklamlari-negatif-anahtar-kelime-listesi",
            "/blog/guzellik-merkezleri-icin-seo-nedir",
            "/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir",
            "/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar",
        ):
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIsNone(headers.get("Location"))

    def test_restored_beauty_article_html_paths_redirect_to_clean_urls(self) -> None:
        redirects = {
            "/blog/kadikoyde-guzellik-merkezi-nasil-one-cikar.html": "/blog/kadikoyde-guzellik-merkezi-nasil-one-cikar",
            "/blog/guzellik-merkezi-randevu-no-show-sorunu-nasil-azaltilir.html": "/blog/guzellik-merkezi-randevu-no-show-sorunu-nasil-azaltilir",
            "/blog/lazer-epilasyon-merkezi-icin-google-ads-rehberi.html": "/blog/lazer-epilasyon-merkezi-icin-google-ads-rehberi",
            "/blog/yeni-acilan-guzellik-merkezi-dijital-kurulum-checklisti.html": "/blog/yeni-acilan-guzellik-merkezi-dijital-kurulum-checklisti",
            "/blog/guzellik-salonu-instagramdan-musteri-nasil-bulur.html": "/blog/guzellik-salonu-instagramdan-musteri-nasil-bulur",
            "/blog/guzellik-merkezi-reklamlari-negatif-anahtar-kelime-listesi.html": "/blog/guzellik-merkezi-reklamlari-negatif-anahtar-kelime-listesi",
            "/blog/guzellik-merkezleri-icin-seo-nedir.html": "/blog/guzellik-merkezleri-icin-seo-nedir",
            "/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir.html": "/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir",
            "/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar.html": "/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar",
        }
        for path, expected_location in redirects.items():
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), expected_location)

    def test_html_page_paths_redirect_to_clean_urls(self) -> None:
        redirects = {
            "/blog.html": "/blog",
            "/blog/": "/blog",
            "/blog/avukatlar-icin-google-reklamlari/": "/blog/avukatlar-icin-google-reklamlari",
            "/calismalarimiz.html": "/calismalarimiz",
            "/hizli-teklif.html?sektor=restoran-kafe": "/hizli-teklif?sektor=restoran-kafe",
            "/blog/instagram-algoritmasi-2026.html": "/blog/instagram-algoritmasi-2026",
        }

        for path, destination in redirects.items():
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), destination)

    def test_directory_backed_blog_article_has_one_canonical_route(self) -> None:
        canonical_route = "/blog/avukatlar-icin-google-reklamlari"
        for method in ("GET", "HEAD"):
            with self.subTest(method=method, route="canonical"):
                status, _, headers = self.http_request(method, canonical_route, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertIsNone(headers.get("Location"))

            for alternate_route in (f"{canonical_route}/", f"{canonical_route}/index.html"):
                with self.subTest(method=method, route=alternate_route):
                    status, _, headers = self.http_request(
                        method,
                        alternate_route,
                        follow_redirects=False,
                    )
                    self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                    self.assertEqual(headers.get("Location"), canonical_route)

    def test_production_url_variants_redirect_directly_to_https_www_clean_url(self) -> None:
        canonical_url = "https://www.veridiareklam.com.tr/hizli-teklif?sektor=restoran-kafe"

        with mock.patch.object(server, "TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"})):
            for method in ("GET", "HEAD"):
                for scheme in ("http", "https"):
                    for host in ("veridiareklam.com.tr", "www.veridiareklam.com.tr"):
                        for route in (
                            "/hizli-teklif?sektor=restoran-kafe",
                            "/hizli-teklif.html?sektor=restoran-kafe",
                        ):
                            is_canonical = (
                                scheme == "https"
                                and host == "www.veridiareklam.com.tr"
                                and ".html" not in route
                            )
                            with self.subTest(method=method, scheme=scheme, host=host, route=route):
                                status, _, headers = self.http_request(
                                    method,
                                    route,
                                    headers={
                                        "Host": host,
                                        "X-Forwarded-Proto": scheme,
                                    },
                                    follow_redirects=False,
                                )

                                if is_canonical:
                                    self.assertEqual(status, HTTPStatus.OK)
                                    self.assertIsNone(headers.get("Location"))
                                else:
                                    self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                                    self.assertEqual(headers.get("Location"), canonical_url)

    def test_production_redirects_collapse_path_normalization_into_one_hop(self) -> None:
        redirects = {
            "/index.html?utm_source=test": "https://www.veridiareklam.com.tr/?utm_source=test",
            "/seo/index.html": "https://www.veridiareklam.com.tr/seo/",
            "/web-tasarim.html": "https://www.veridiareklam.com.tr/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/hizmetler/web-tasarim": "https://www.veridiareklam.com.tr/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/hizmetler/web-tasarim/index.html": "https://www.veridiareklam.com.tr/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/blog/b2b-pazarlamada-donusum-hunisi.html": (
                "https://www.veridiareklam.com.tr/blog/b2b-donusum-hunisi"
            ),
        }

        for route, destination in redirects.items():
            with self.subTest(route=route):
                status, _, headers = self.http_request(
                    "GET",
                    route,
                    headers={
                        "Host": "veridiareklam.com.tr",
                        "X-Forwarded-Proto": "http",
                    },
                    follow_redirects=False,
                )

                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), destination)

    def test_untrusted_forwarded_proto_cannot_bypass_https_redirect(self) -> None:
        with mock.patch.object(server, "TRUSTED_PROXY_IPS", frozenset()):
            status, _, headers = self.http_request(
                "GET",
                "/hizli-teklif",
                headers={
                    "Host": "www.veridiareklam.com.tr",
                    "X-Forwarded-Proto": "https",
                },
                follow_redirects=False,
            )

        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(
            headers.get("Location"),
            "https://www.veridiareklam.com.tr/hizli-teklif",
        )

    def test_trusted_standard_forwarded_proto_avoids_https_redirect_loop(self) -> None:
        with mock.patch.object(server, "TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"})):
            status, _, headers = self.http_request(
                "GET",
                "/hizli-teklif",
                headers={
                    "Host": "www.veridiareklam.com.tr",
                    "Forwarded": 'for=203.0.113.10;proto="https"',
                },
                follow_redirects=False,
            )

        self.assertEqual(status, HTTPStatus.OK)
        self.assertIsNone(headers.get("Location"))

    def test_redirect_location_never_reflects_an_untrusted_host_header(self) -> None:
        status, _, headers = self.http_request(
            "GET",
            "/hizli-teklif.html",
            headers={
                "Host": "attacker.example",
                "X-Forwarded-Proto": "http",
            },
            follow_redirects=False,
        )

        self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(headers.get("Location"), "/hizli-teklif")
        self.assertNotIn("attacker.example", headers.get("Location", ""))

    def test_legacy_beauty_sector_url_redirects_to_canonical_sector_landing(self) -> None:
        for path in ("/guzellik-merkezleri-icin-dijital-pazarlama",):
            with self.subTest(path=path):
                status, _, headers = self.http_request(
                    "GET",
                    path,
                    follow_redirects=False,
                )

                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/")

    def test_legacy_root_sector_urls_redirect_to_sektorler_standard(self) -> None:
        redirects = {
            "/kafe-restoran-dijital-pazarlama": "/sektorler/kafe-restoran-dijital-pazarlama/",
            "/kafe-restoran-dijital-pazarlama.html": "/sektorler/kafe-restoran-dijital-pazarlama/",
            "/moda-e-ticaret-dijital-pazarlama": "/sektorler/moda-e-ticaret-dijital-pazarlama/",
            "/moda-e-ticaret-dijital-pazarlama.html": "/sektorler/moda-e-ticaret-dijital-pazarlama/",
            "/teknoloji-b2b-dijital-pazarlama": "/sektorler/teknoloji-b2b-dijital-pazarlama/",
            "/teknoloji-b2b-dijital-pazarlama.html": "/sektorler/teknoloji-b2b-dijital-pazarlama/",
            "/yasam-ev-markalari-dijital-pazarlama": "/sektorler/yasam-ev-markalari-dijital-pazarlama/",
            "/yasam-ev-markalari-dijital-pazarlama.html": "/sektorler/yasam-ev-markalari-dijital-pazarlama/",
        }
        for path, destination in redirects.items():
            with self.subTest(path=path):
                status, _, headers = self.http_request("GET", path, follow_redirects=False)
                self.assertEqual(status, HTTPStatus.MOVED_PERMANENTLY)
                self.assertEqual(headers.get("Location"), destination)

    def test_legacy_service_pages_redirect_to_silo_urls(self) -> None:
        redirects = {
            "/web-tasarim.html": "/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
            "/seo-danismanligi.html": "/seo/google-gorunurlugu/",
            "/google-ads-yonetimi.html": "/reklam/google-ads-yonetimi/",
            "/sosyal-medya-yonetimi.html": "/reklam/sosyal-medya-yonetimi/",
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
