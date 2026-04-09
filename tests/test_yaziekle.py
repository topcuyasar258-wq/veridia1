import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent


class BlogGeneratorTests(unittest.TestCase):
    def test_script_loads_site_url_from_local_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            script_path = temp_root / "yaziekle.py"
            shutil.copyfile(ROOT / "yaziekle.py", script_path)
            (temp_root / ".env").write_text("SITE_URL=https://demo.example\n", encoding="utf-8")

            spec = importlib.util.spec_from_file_location("temp_yaziekle", script_path)
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)

            with mock.patch.dict("os.environ", {}, clear=True):
                assert spec.loader is not None
                spec.loader.exec_module(module)

            html = module.build_article_template(
                "Deneme Baslik",
                "Kisa ozet",
                "deneme-baslik",
                "2026-04-09",
                "9 Nisan 2026",
            )

        self.assertIn("https://demo.example/blog/deneme-baslik.html", html)
        self.assertIn("https://demo.example/assets/veridia-social-cover.png", html)


if __name__ == "__main__":
    unittest.main()
