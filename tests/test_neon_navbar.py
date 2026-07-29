from pathlib import Path
import re
import unittest


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
