from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


class EntryPopupTests(unittest.TestCase):
    def test_homepage_loads_entry_popup_asset(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("./assets/entry-popup.js", homepage)

    def test_entry_popup_uses_clear_cta_copy_and_accessible_dialog(self) -> None:
        script = (ROOT / "assets" / "entry-popup.js").read_text(encoding="utf-8")

        for expected in (
            "Web Siteniz Teklif Getirsin",
            "Ücretsiz Ön Görüşme Al",
            "20.000 TL'den başlayan web sitesi sprinti",
            "aria-modal",
            "aria-describedby",
            "Escape",
            "previousFocus",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, script)


if __name__ == "__main__":
    unittest.main()
