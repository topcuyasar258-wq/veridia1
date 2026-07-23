from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


def public_pages() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts
        and ".claude" not in path.parts
        and "automation" not in path.parts
        and "fragments" not in path.parts
        and "page-shell.js" in path.read_text(encoding="utf-8")
    )


class FloatingActionButtonTests(unittest.TestCase):
    def test_public_pages_load_fab_assets(self) -> None:
        pages = public_pages()
        self.assertGreaterEqual(len(pages), 50)
        for path in pages:
            page = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn('/assets/css/fab.css', page)
                self.assertIn('/assets/js/fab.js', page)
                self.assertIn('defer src="/assets/js/fab.js', page)

    def test_fab_css_keeps_component_fixed_and_motion_safe(self) -> None:
        css = (ROOT / "assets" / "css" / "fab.css").read_text(encoding="utf-8")
        for expected in (
            "position: fixed",
            "right: calc(16px + env(safe-area-inset-right))",
            "bottom: calc(16px + env(safe-area-inset-bottom))",
            "z-index: 9999",
            "width: 56px",
            "height: 56px",
            "min-height: 48px",
            "prefers-reduced-motion: reduce",
            "transform: scale(1.06)",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, css)

        self.assertNotIn("left:", css)
        self.assertNotIn("top:", css)
        self.assertNotIn("#", css)

    def test_fab_script_gates_ai_action_and_sends_events(self) -> None:
        script = (ROOT / "assets" / "js" / "fab.js").read_text(encoding="utf-8")
        for expected in (
            "VERIDIA_AI_ENABLED === true",
            "dataset.veridiaAiEnabled",
            "new CustomEvent('veridia:open-chat')",
            "fab_open",
            "fab_whatsapp_click",
            "fab_ai_click",
            "typeof root.gtag !== 'function'",
            "aria-expanded",
            "aria-controls",
            "Escape",
            "MutationObserver",
            "scrollable <= 0 ? 1",
            "scrollY / scrollable",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, script)


if __name__ == "__main__":
    unittest.main()
