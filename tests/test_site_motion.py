from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
MOTION_CSS = "/assets/site-motion.css?v=11"
MOTION_JS = "/assets/site-motion.js?v=10"
MOTION_STORY_JS = "/assets/site-motion-story.js?v=4"


def marketing_pages() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts
        and ".claude" not in path.parts
        and "automation" not in path.parts
        and "site_src" not in path.parts
        and "page-shell.js" in path.read_text(encoding="utf-8")
    )


class SiteMotionTests(unittest.TestCase):
    def test_every_marketing_surface_loads_versioned_motion_assets(self) -> None:
        pages = marketing_pages()
        self.assertGreaterEqual(len(pages), 50)

        for path in pages:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn(MOTION_CSS, source)
                self.assertIn(MOTION_JS, source)
                self.assertEqual(1, source.count(MOTION_CSS))
                self.assertEqual(1, source.count(MOTION_JS))
                self.assertLess(source.index(MOTION_CSS), source.index(MOTION_JS))
                self.assertRegex(
                    source,
                    rf'<script[^>]+src="{re.escape(MOTION_JS)}"[^>]*\bdefer\b[^>]*>',
                )

    def test_homepage_source_template_keeps_motion_assets(self) -> None:
        template = (
            ROOT / "site_src" / "homepage" / "index.template.html"
        ).read_text(encoding="utf-8")

        self.assertIn(MOTION_CSS, template)
        self.assertIn(MOTION_STORY_JS, template)
        self.assertIn(MOTION_JS, template)
        self.assertLess(template.index(MOTION_STORY_JS), template.index(MOTION_JS))

        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(MOTION_STORY_JS, homepage)
        self.assertLess(homepage.index(MOTION_STORY_JS), homepage.index(MOTION_JS))

    def test_content_generators_keep_motion_assets(self) -> None:
        for relative_path in (
            "scripts/build_site_surfaces.py",
            "yaziekle.py",
        ):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(path=relative_path):
                self.assertIn(MOTION_CSS, source)
                self.assertIn(MOTION_JS, source)

    def test_motion_css_is_progressive_brand_safe_and_reduced_motion_safe(
        self,
    ) -> None:
        css = (ROOT / "assets" / "site-motion.css").read_text(encoding="utf-8")

        for token in (
            "--gold",
            "--gold-light",
            "--emerald",
            ".hero-bg, .hero-grid, .hero-number",
            ".v-motion-enabled .v-motion-reveal:not(.is-visible)",
            ".v-motion-ambient",
            ".v-motion-card",
            ".v-motion-card:hover",
            ".v-motion-cta",
            ".v-scramble-word",
            ".v-scramble-glyph",
            ".v-scroll-track",
            ".v-scroll-story",
            ".v-scroll-copy",
            ".hero-content::before",
            "0 18px 44px rgba(0, 0, 0, 0.62)",
            "@keyframes v-motion-cta-shine",
            "@media (hover: hover) and (pointer: fine)",
            "@media (prefers-reduced-motion: reduce)",
        ):
            with self.subTest(token=token):
                self.assertIn(token, css)

        for prototype_color in ("#ff6a45", "#ffd23f", "#4f7cff", "#00d4b8"):
            with self.subTest(color=prototype_color):
                self.assertNotIn(prototype_color, css.lower())

    def test_motion_script_uses_one_accessible_observer_without_scroll_hijacking(
        self,
    ) -> None:
        script = (ROOT / "assets" / "site-motion.js").read_text(encoding="utf-8")

        for token in (
            "prefers-reduced-motion: reduce",
            "hover: hover",
            "pointer: fine",
            "IntersectionObserver",
            "observer.unobserve",
            "requestAnimationFrame",
            "v-motion-enabled",
            "v-motion-reveal",
            "v-motion-card",
            "v-motion-ambient",
            "v-motion-globe",
            "data-v-scramble",
            'getContext("2d")',
            "createSpherePoints",
            "selectScrambleGlyph",
            "document.visibilityState",
        ):
            with self.subTest(token=token):
                self.assertIn(token, script)

        self.assertNotIn("addEventListener('wheel'", script)
        self.assertNotIn('addEventListener("wheel"', script)
        self.assertNotIn("addEventListener('touchmove'", script)
        self.assertNotIn('addEventListener("touchmove"', script)
        self.assertNotIn("preventDefault()", script)
        self.assertNotIn("setInterval(", script)
        self.assertNotIn("scrollTo(", script)
        self.assertNotIn("getContext('webgl'", script)
        self.assertNotIn('getContext("webgl"', script)
        self.assertNotIn("three.js", script.lower())

        story_script = (
            ROOT / "assets" / "site-motion-story.js"
        ).read_text(encoding="utf-8")
        for token in (
            "calculateStickyProgress",
            "resolveStoryTimeline",
            "fractureSpherePoint",
            "createScrollStory",
            'addEventListener("scroll", queueUpdate, { passive: true })',
            "IntersectionObserver",
            "lastProgress",
            "aria-hidden",
            "inert",
        ):
            with self.subTest(story_token=token):
                self.assertIn(token, story_script)

        self.assertNotIn("preventDefault()", story_script)
        self.assertNotIn("scrollTo(", story_script)


if __name__ == "__main__":
    unittest.main()
