from pathlib import Path
import re
import unittest

from scripts.build_site_surfaces import load_graph, render_page


ROOT = Path(__file__).resolve().parent.parent


class NeonInspiredNavbarTests(unittest.TestCase):
    NAV_SURFACES = (
        "index.html",
        "blog.html",
        "calismalarimiz.html",
        "hakkimizda.html",
        "hizmetler/index.html",
        "iletisim.html",
        "404.html",
        "araclar/site-analizi/index.html",
    )
    CANONICAL_SERVICE_SURFACES = (
        "seo/index.html",
        "seo/google-gorunurlugu/index.html",
        "seo/teknik-seo-denetimi/index.html",
        "reklam/index.html",
        "reklam/google-ads-yonetimi/index.html",
        "reklam/meta-reklam-yonetimi/index.html",
        "reklam/sosyal-medya-yonetimi/index.html",
        "yazilim/index.html",
        "yazilim/web-sitesi-ve-donusum-yuzeyleri/index.html",
    )

    def test_shared_script_builds_the_announcement_and_desktop_mega_menus(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")

        for contract in (
            "revision-announcement",
            "data-revision-mega-trigger",
            "data-revision-mega",
            "revision-nav-overlay",
            "setMegaMenu",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, script)
        self.assertIn('<a href="/hizli-teklif">', script)

    def test_desktop_mega_menu_is_keyboard_accessible(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")

        self.assertIn('aria-haspopup="true"', script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn("aria-expanded", script)
        self.assertIn("hidden = true", script)

    def test_shared_styles_define_two_tier_header_and_full_width_panel(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")

        for selector in (
            ".revision-announcement",
            ".revision-nav-mega",
            ".revision-mega-grid",
            ".revision-nav-overlay",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)

        self.assertIn("--revision-announcement-height", css)
        self.assertIn("--revision-navbar-height", css)
        self.assertIn("max-height: calc(100svh - var(--revision-header-height))", css)

    def test_mobile_breakpoint_hides_desktop_mega_navigation(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")

        mobile_rules = css.rsplit("@media (max-width: 1000px)", maxsplit=1)[-1]
        self.assertIn(".revision-nav-mega", mobile_rules)
        self.assertIn("display: none !important", mobile_rules)

    def test_mobile_and_desktop_menu_controls_use_distinct_ids(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")

        self.assertIn('id="revision-${menuId}-trigger"', script)
        self.assertIn('id: "revision-mobile-services"', script)
        self.assertIn('id: "revision-mobile-sectors"', script)
        self.assertNotIn('renderAccordion({ id: "revision-services"', script)
        self.assertNotIn('renderAccordion({ id: "revision-sectors"', script)

    def test_all_primary_entry_points_load_the_current_shared_navigation(self) -> None:
        for relative_path in self.NAV_SURFACES:
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("/assets/revision.css?v=35", page)
                self.assertIn("/assets/revision.js?v=14", page)

    def test_canonical_service_surfaces_use_the_revision_shell(self) -> None:
        for relative_path in self.CANONICAL_SERVICE_SURFACES:
            with self.subTest(path=relative_path):
                page = (ROOT / relative_path).read_text(encoding="utf-8")

                self.assertIn("/assets/revision.css?v=35", page)
                self.assertIn("/assets/revision.js?v=14", page)
                self.assertRegex(
                    page,
                    r'<body[^>]*class="[^"]*\brevision-silo-page\b[^"]*"',
                )
                self.assertLess(
                    page.index("/assets/silo-pages.css"),
                    page.index("/assets/revision.css?v=35"),
                )
                self.assertLess(
                    page.index("/assets/page-shell.js"),
                    page.index("/assets/revision.js?v=14"),
                )

    def test_service_surface_generator_keeps_the_revision_shell(self) -> None:
        graph = load_graph()
        generated_surfaces = (
            render_page(graph["hubs"][0], graph, "hub"),
            render_page(graph["services"][0], graph, "service"),
        )

        for generated in generated_surfaces:
            with self.subTest(surface=generated):
                self.assertIn("/assets/page-shell.css?v=2", generated)
                self.assertIn("/assets/silo-pages.css?v=3", generated)
                self.assertIn("/assets/revision.css?v=35", generated)
                self.assertIn("/assets/page-shell.js?v=9", generated)
                self.assertIn("/assets/revision.js?v=14", generated)
                self.assertIn(
                    '<body class="revision-silo-page services-page"',
                    generated,
                )
                self.assertLess(
                    generated.index("/assets/silo-pages.css?v=3"),
                    generated.index("/assets/revision.css?v=35"),
                )
                self.assertLess(
                    generated.index("/assets/page-shell.js?v=9"),
                    generated.index("/assets/revision.js?v=14"),
                )

    def test_every_shared_navigation_consumer_uses_one_cache_version(self) -> None:
        css_versions = set()
        script_versions = set()

        for path in ROOT.rglob("*.html"):
            relative_path = path.relative_to(ROOT)
            if any(part.startswith(".") for part in relative_path.parts):
                continue
            source = path.read_text(encoding="utf-8")
            css_versions.update(re.findall(r"/assets/revision\.css\?v=(\d+)", source))
            script_versions.update(re.findall(r"/assets/revision\.js\?v=(\d+)", source))

        self.assertEqual(css_versions, {"35"})
        self.assertEqual(script_versions, {"14"})

    def test_anchor_offset_tracks_the_real_two_tier_header_height(self) -> None:
        css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        html_rule = css.split("html {", maxsplit=1)[1].split("}", maxsplit=1)[0]

        self.assertIn(
            "scroll-padding-top: calc(var(--revision-header-height, 100px) + 1rem)",
            html_rule,
        )


if __name__ == "__main__":
    unittest.main()
