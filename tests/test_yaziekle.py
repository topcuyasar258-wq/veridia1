import importlib.util
import json
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

    def test_template_embeds_service_breadcrumbs_and_related_cluster_links(self) -> None:
        spec = importlib.util.spec_from_file_location("root_yaziekle", ROOT / "yaziekle.py")
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        graph = json.loads((ROOT / "content" / "site_graph.json").read_text(encoding="utf-8"))
        service = next(item for item in graph["services"] if item["slug"] == "sosyal-medya-yonetimi")
        hub = next(item for item in graph["hubs"] if item["slug"] == service["parent"])

        html = module.build_article_template(
            "Instagram İçerik Sistemi",
            "Instagram içerik sistemini marka hafızası ve yayın ritmiyle ele alan rehber.",
            "instagram-icerik-sistemi",
            "2026-04-23T00:00:00+03:00",
            "23 Nisan 2026",
            graph=graph,
            service=service,
            hub=hub,
            author="Veridia Strateji Ekibi",
            reading_time="8 dk okuma",
        )

        self.assertIn("/reklam/sosyal-medya-yonetimi/", html)
        self.assertIn("Reklam Hizmetleri", html)
        self.assertIn("İlginizi Çekebilir", html)
        self.assertIn("Sosyal Medya Yönetimi", html)


if __name__ == "__main__":
    unittest.main()
