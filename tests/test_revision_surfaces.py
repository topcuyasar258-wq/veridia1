from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
SURFACES = (
    "index.html",
    "blog.html",
    "calismalarimiz.html",
    "hakkimizda.html",
    "hizmetler/index.html",
)
EXTENDED_SURFACES = (
    "yazilim/index.html",
    "seo/index.html",
    "reklam/index.html",
    "reklam/meta-reklam-yonetimi/index.html",
    "reklam/sosyal-medya-yonetimi/index.html",
    "calisma-surecimiz.html",
    "hizli-teklif.html",
)
PRIMARY_LINKS = (
    'href="/"',
    'href="/hizmetler/"',
    'href="/calismalarimiz.html"',
    'href="/hakkimizda.html"',
    'href="/blog.html"',
)


class RevisionSurfaceTests(unittest.TestCase):
    def test_homepage_only_exposes_the_reference_design_sections(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")

        self.assertIn('class="reference-home-page"', homepage)
        for section_class in (
            "reference-trust",
            "reference-system",
            "reference-manifesto",
            "reference-closing",
        ):
            with self.subTest(section=section_class):
                self.assertIn(f'class="{section_class}', homepage)
                self.assertIn(f".{section_class}", css)

        self.assertIn("BİZE GÜVENEN MARKALAR", homepage)
        self.assertIn("İnşa Et", homepage)
        self.assertIn("Görünür Ol", homepage)
        self.assertIn("Hızlan", homepage)
        self.assertIn("7/24 çalışan dijital satış temsilcinizi", homepage)
        self.assertIn("body.reference-home-page > #problem", css)
        self.assertIn("body.reference-home-page > #mini-analiz", css)

    def test_five_primary_surfaces_load_the_shared_revision_assets(self) -> None:
        for relative_path in SURFACES:
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("/assets/revision.css", page)
                self.assertIn("/assets/revision.js", page)

    def test_five_primary_surfaces_expose_real_page_navigation(self) -> None:
        for relative_path in SURFACES:
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                for href in PRIMARY_LINKS:
                    self.assertIn(href, page)

    def test_revision_assets_define_accessible_responsive_navigation(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("aria-expanded", script)
        self.assertIn("Escape", script)

    def test_shared_visual_system_uses_one_material_across_primary_pages(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        for token in (
            "--revision-grid",
            "--revision-panel",
            "--revision-section-space",
            "--revision-display-size",
        ):
            with self.subTest(token=token):
                self.assertIn(token, css)

        self.assertIn("body.reference-home-page::before", css)
        self.assertIn("body.reference-home-page #hero .hero-bg", css)
        self.assertIn(".work-hero::before", css)
        self.assertIn(".service-board", css)
        self.assertIn("background-image: var(--revision-grid)", css)

    def test_native_pointer_is_visible_when_custom_cursor_is_disabled(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        self.assertIn("body[data-custom-cursor=\"true\"]", css)
        self.assertIn("cursor: auto !important", css)
        self.assertIn("cursor: pointer !important", css)

    def test_primary_navigation_is_fixed_to_the_viewport(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        self.assertIn("--revision-header-height", css)
        self.assertIn("position: fixed !important", css)
        self.assertIn("padding-top: var(--revision-header-height) !important", css)
        self.assertIn("top: 0 !important", css)

    def test_primary_pages_share_one_typography_system(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        self.assertIn("--revision-font-display", css)
        self.assertIn("--revision-font-body", css)
        self.assertIn("font-family: var(--revision-font-display) !important", css)
        self.assertIn("font-family: var(--revision-font-body) !important", css)
        self.assertIn("font-style: normal !important", css)

    def test_primary_surface_canonicals_are_unchanged(self) -> None:
        expected = {
            "index.html": "https://www.veridiareklam.com.tr",
            "blog.html": "https://www.veridiareklam.com.tr/blog.html",
            "calismalarimiz.html": "https://www.veridiareklam.com.tr/calismalarimiz.html",
            "hakkimizda.html": "https://www.veridiareklam.com.tr/hakkimizda.html",
            "hizmetler/index.html": "https://www.veridiareklam.com.tr/hizmetler/",
        }
        for relative_path, canonical in expected.items():
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn(f'rel="canonical" href="{canonical}"', page)

    def test_extended_service_surfaces_load_the_shared_revision_assets(self) -> None:
        for relative_path in EXTENDED_SURFACES:
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("/assets/revision.css", page)
                self.assertIn("/assets/revision.js", page)

    def test_homepage_trust_marks_match_the_portfolio_case_names(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        portfolio = (ROOT / "calismalarimiz.html").read_text(encoding="utf-8")
        for brand in ("Nara Coffee", "Zeyra Beauty", "Atlas Sportswear", "Maison Fleur"):
            with self.subTest(brand=brand):
                self.assertIn(brand, homepage)
                self.assertIn(brand, portfolio)

    def test_project_start_uses_whatsapp_and_analysis_ctas_use_current_route(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-whatsapp-message", script)
        self.assertIn("Proje Başlat", script)
        self.assertIn('href="/hizli-teklif.html"', homepage)
        for relative_path in (
            "yazilim/index.html",
            "seo/index.html",
            "reklam/index.html",
            "reklam/meta-reklam-yonetimi/index.html",
            "reklam/sosyal-medya-yonetimi/index.html",
        ):
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn('href="/hizli-teklif.html" class="btn-gold"', page)

    def test_all_blog_articles_load_the_shared_revision_system(self) -> None:
        articles = sorted((ROOT / "blog").glob("*.html"))
        articles.extend(sorted((ROOT / "blog").glob("*/index.html")))
        self.assertGreaterEqual(len(articles), 10)
        for article in articles:
            with self.subTest(path=article.relative_to(ROOT)):
                page = article.read_text(encoding="utf-8")
                self.assertIn('class="revision-article-page"', page)
                self.assertIn("/assets/revision.css", page)
                self.assertIn("/assets/revision.js", page)
                self.assertIn('rel="canonical"', page)

    def test_mobile_blog_background_uses_stable_integer_grid(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        self.assertIn("body:has(.blog-page)", css)
        self.assertIn("background-size: 92px 92px !important", css)
        self.assertIn("background-attachment: scroll !important", css)


if __name__ == "__main__":
    unittest.main()
