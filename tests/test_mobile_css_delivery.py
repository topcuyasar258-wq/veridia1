from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class MobileCssDeliveryTests(unittest.TestCase):
    def test_homepage_styles_do_not_depend_on_user_scroll_or_javascript(self) -> None:
        for relative_path in (
            "index.html",
            "site_src/homepage/index.template.html",
        ):
            homepage = (ROOT / relative_path).read_text(encoding="utf-8")

            with self.subTest(path=relative_path):
                self.assertNotIn("data-deferred-style", homepage)
                for asset in (
                    "./assets/shared.css",
                    "./assets/home-contact.css",
                    "./assets/home-mobile-tune.css",
                ):
                    self.assertRegex(
                        homepage,
                        rf'<link rel="stylesheet" href="{asset}\?v=\d+">',
                    )

    def test_home_mobile_overrides_load_after_the_shared_revision_layer(self) -> None:
        for relative_path in (
            "index.html",
            "site_src/homepage/index.template.html",
        ):
            homepage = (ROOT / relative_path).read_text(encoding="utf-8")

            with self.subTest(path=relative_path):
                revision_position = homepage.index("/assets/revision.css")
                mobile_position = homepage.index("./assets/home-mobile-tune.css")
                self.assertGreater(mobile_position, revision_position)

    def test_home_interactions_begin_loading_without_the_first_tap(self) -> None:
        loader = (ROOT / "assets" / "home-loader.js").read_text(encoding="utf-8")

        self.assertIn("DOMContentLoaded", loader)

    def test_every_home_loader_consumer_uses_the_current_cache_version(self) -> None:
        consumers = {}
        for path in ROOT.rglob("*.html"):
            relative_path = path.relative_to(ROOT)
            if any(part.startswith(".") for part in relative_path.parts):
                continue
            source = path.read_text(encoding="utf-8")
            if "home-loader.js" in source:
                consumers[relative_path] = source

        self.assertTrue(consumers)
        for relative_path, source in consumers.items():
            with self.subTest(path=relative_path):
                self.assertIn("assets/home-loader.js?v=8", source)

    def test_mobile_controls_meet_minimum_touch_target_size(self) -> None:
        shared_css = (ROOT / "assets" / "revision.css").read_text(encoding="utf-8")
        blog_css = (ROOT / "assets" / "blog-index.css").read_text(encoding="utf-8")

        for selector in (
            "body .revision-nav-theme",
            "body .hamburger",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, shared_css)
        for selector in ("body .topic-pill", "body .blog-arrow"):
            with self.subTest(selector=selector):
                self.assertIn(selector, blog_css)
        self.assertIn("min-height: 44px", shared_css)
        self.assertIn("min-width: 44px", shared_css)
        self.assertIn("min-height: 44px", blog_css)
        self.assertIn("min-width: 44px", blog_css)

    def test_mobile_blog_filters_remain_a_compact_horizontal_control(self) -> None:
        css = (ROOT / "assets" / "blog-index.css").read_text(encoding="utf-8")

        self.assertIn("body .topic-strip", css)
        self.assertIn("flex-wrap: nowrap", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("scroll-snap-type: x proximity", css)

    def test_blog_filter_can_override_the_card_display_rule(self) -> None:
        css = (ROOT / "assets" / "blog-index.css").read_text(encoding="utf-8")

        self.assertIn('.blog-card[data-visibility="hidden"]', css)
        self.assertIn("display: none !important", css)

    def test_mobile_menu_keeps_keyboard_focus_inside_and_returns_it_on_close(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")

        self.assertIn("previousFocus", script)
        self.assertIn("event.key === \"Tab\"", script)
        self.assertIn("previousFocus?.focus", script)


if __name__ == "__main__":
    unittest.main()
