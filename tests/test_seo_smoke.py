from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class SeoSmokeTests(unittest.TestCase):
    def test_robots_points_to_production_sitemap(self) -> None:
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://veridia.com.tr/sitemap.xml", robots)
        self.assertNotIn("127.0.0.1", robots)

    def test_sitemap_uses_production_urls(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://veridia.com.tr/", sitemap)
        self.assertIn("https://veridia.com.tr/blog/b2b-pazarlamada-donusum-hunisi.html", sitemap)
        self.assertIn("https://veridia.com.tr/gizlilik-politikasi.html", sitemap)
        self.assertIn("https://veridia.com.tr/kvkk-aydinlatma-metni.html", sitemap)
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
            ROOT / "blog" / "instagram-algoritmasi.html",
            ROOT / "blog" / "b2b-pazarlamada-donusum-hunisi.html",
        ]
        for article_path in article_paths:
            content = article_path.read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical"', content)
            self.assertIn('"@type": "BlogPosting"', content)
            self.assertIn('meta property="og:type" content="article"', content)
            self.assertIn("veridia-social-cover.png", content)
            self.assertIn('rel="icon"', content)

    def test_homepage_has_service_catalog_and_visible_service_copy(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "OfferCatalog"', homepage)
        self.assertIn("Marka Stratejisi ve Konumlandırma", homepage)
        self.assertIn('class="services-detail-grid"', homepage)
        self.assertIn('href="https://veridia.com.tr/"', homepage)
        self.assertIn("veridia-social-cover.png", homepage)
        self.assertIn('rel="icon"', homepage)
        self.assertNotIn("Marka e-postası bu aşamada doğrulanmadı", homepage)
        self.assertNotIn("APIFY_TOKEN", homepage)
        self.assertNotIn("python3 server.py", homepage)
        self.assertNotIn('href="#contact">Instagram</a>', homepage)

    def test_index_redirect_is_single_path_and_root_canonical(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh"', index)
        self.assertNotIn("window.location.replace", index)
        self.assertIn('rel="canonical" href="https://veridia.com.tr/"', index)

    def test_legal_pages_exist_and_link_back_to_site(self) -> None:
        for page_name in ("gizlilik-politikasi.html", "kvkk-aydinlatma-metni.html"):
            with self.subTest(page_name=page_name):
                page = (ROOT / page_name).read_text(encoding="utf-8")
                self.assertIn("Veridia", page)
                self.assertIn('rel="canonical"', page)
                self.assertIn("veridia-social-cover.png", page)


if __name__ == "__main__":
    unittest.main()
