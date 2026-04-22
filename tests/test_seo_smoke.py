from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class SeoSmokeTests(unittest.TestCase):
    def test_robots_points_to_production_sitemap(self) -> None:
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://veridiareklam.com.tr/sitemap.xml", robots)
        self.assertNotIn("127.0.0.1", robots)

    def test_sitemap_uses_production_urls(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://veridiareklam.com.tr/", sitemap)
        self.assertIn("https://veridiareklam.com.tr/neler-yapiyoruz.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/calismalarimiz.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/blog/instagram-algoritmasi-2026.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/blog/b2b-donusum-hunisi.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/blog/teknik-seo-ve-web-performansi.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/gizlilik-politikasi.html", sitemap)
        self.assertIn("https://veridiareklam.com.tr/kvkk-aydinlatma-metni.html", sitemap)
        self.assertNotIn("https://veridiareklam.com.tr/blog/b2b-pazarlamada-donusum-hunisi.html", sitemap)
        self.assertNotIn("127.0.0.1", sitemap)

    def test_blog_index_has_no_dead_placeholder_links(self) -> None:
        blog_index = (ROOT / "blog.html").read_text(encoding="utf-8")
        self.assertNotIn('href="#"', blog_index)
        self.assertIn("<!-- BLOG_CARDS -->", blog_index)
        self.assertIn("canonical", blog_index)
        self.assertIn("Veridia Strateji Ekibi", blog_index)
        self.assertNotIn("#analyze", blog_index)

    def test_article_pages_have_canonical_and_schema(self) -> None:
        article_paths = [
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for article_path in article_paths:
            content = article_path.read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical"', content)
            self.assertIn('"@type": "Article"', content)
            self.assertIn('meta property="og:type" content="article"', content)
            self.assertIn("veridia-social-cover.png", content)
            self.assertIn('rel="icon"', content)

    def test_homepage_has_service_catalog_and_visible_service_copy(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "ItemList"', homepage)
        self.assertIn("Marka Stratejisi", homepage)
        self.assertIn('class="services-detail-grid"', homepage)
        self.assertIn('rel="canonical" href="https://veridiareklam.com.tr"', homepage)
        self.assertIn("veridia-social-cover.png", homepage)
        self.assertIn("assets/config.js", homepage)
        self.assertIn("assets/home-loader.js", homepage)
        self.assertIn("quoteValidationError", homepage)
        self.assertIn("/neler-yapiyoruz.html", homepage)
        self.assertIn("/calismalarimiz.html", homepage)
        self.assertIn('rel="icon"', homepage)
        self.assertNotIn("Marka e-postası bu aşamada doğrulanmadı", homepage)
        self.assertNotIn("APIFY_TOKEN", homepage)
        self.assertNotIn("python3 server.py", homepage)
        self.assertNotIn('href="#contact">Instagram</a>', homepage)

    def test_homepage_does_not_preload_non_critical_social_cover_or_eager_home_scripts(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('<link rel="preload" href="./assets/veridia-social-cover.png" as="image">', homepage)
        self.assertNotIn('<script defer src="./assets/home.js"></script>', homepage)
        self.assertNotIn('<script defer src="./assets/site-data.js"></script>', homepage)
        self.assertNotIn('<script defer src="./assets/quote-pricing.js"></script>', homepage)

    def test_homepage_source_is_canonical_root_document(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('http-equiv="refresh"', index)
        self.assertNotIn("window.location.replace", index)
        self.assertIn('rel="canonical" href="https://veridiareklam.com.tr"', index)
        self.assertIn("<title>Veridia Ajans", index)

    def test_body_internal_links_do_not_hardcode_production_domain(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "neler-yapiyoruz.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "gizlilik-politikasi.html",
            ROOT / "kvkk-aydinlatma-metni.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                body = content.split("<body", 1)[1]
                self.assertNotIn('href="https://veridiareklam.com.tr', body)

    def test_legal_pages_exist_and_link_back_to_site(self) -> None:
        for page_name in ("gizlilik-politikasi.html", "kvkk-aydinlatma-metni.html"):
            with self.subTest(page_name=page_name):
                page = (ROOT / page_name).read_text(encoding="utf-8")
                self.assertIn("Veridia", page)
                self.assertIn('rel="canonical"', page)
                self.assertIn("veridia-social-cover.png", page)

    def test_pages_use_local_font_manifest_and_no_google_fonts(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "neler-yapiyoruz.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "gizlilik-politikasi.html",
            ROOT / "kvkk-aydinlatma-metni.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("assets/fonts.css", content)
                self.assertNotIn("fonts.googleapis.com", content)
                self.assertNotIn("fonts.gstatic.com", content)

    def test_pages_do_not_use_inline_script_handlers(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "neler-yapiyoruz.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("onclick=", content)
                self.assertNotIn("onload=", content)
                self.assertNotIn("window.dataLayer", content)

    def test_work_pages_have_canonical_schema_and_local_assets(self) -> None:
        work_pages = [
            ROOT / "neler-yapiyoruz.html",
            ROOT / "calismalarimiz.html",
        ]
        for page_path in work_pages:
            with self.subTest(page=page_path.name):
                content = page_path.read_text(encoding="utf-8")
                self.assertIn('<link rel="canonical"', content)
                self.assertIn('"@type": "CollectionPage"', content)
                self.assertIn("assets/work-pages.css", content)
                self.assertIn("assets/work-pages.js", content)
                self.assertIn("data-whatsapp-message", content)
                self.assertIn("veridia-social-cover.png", content)
                self.assertNotIn('href="#"', content)

    def test_case_studies_page_positions_scenarios_transparently(self) -> None:
        content = (ROOT / "calismalarimiz.html").read_text(encoding="utf-8")
        self.assertIn("<title>Örnek Çalışma Senaryoları | Veridia</title>", content)
        self.assertIn("örnek çalışma senaryoları", content)
        self.assertIn("anonimleştirilmiş vaka notları", content)
        self.assertIn("müşteri yorumu değil", content)

if __name__ == "__main__":
    unittest.main()
