import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
PRODUCTION_URL = "https://www.veridiareklam.com.tr"


def read_json_ld(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    return [
        json.loads(block)
        for block in re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            content,
            flags=re.DOTALL,
        )
    ]


def json_ld_types(path: Path) -> set[str]:
    found: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            schema_type = value.get("@type")
            if isinstance(schema_type, str):
                found.add(schema_type)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for document in read_json_ld(path):
        visit(document)
    return found


class SeoSmokeTests(unittest.TestCase):
    def test_robots_points_to_production_sitemap(self) -> None:
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {PRODUCTION_URL}/sitemap.xml", robots)
        self.assertNotIn("127.0.0.1", robots)
        self.assertNotIn("Crawl-delay", robots)

    def test_sitemap_uses_production_urls(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"{PRODUCTION_URL}/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/hizmetler/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/calismalarimiz", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/seo/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/reklam/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/yazilim/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/seo/teknik-seo-denetimi/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/seo/google-gorunurlugu/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/reklam/sosyal-medya-yonetimi/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/reklam/google-ads-yonetimi/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/yazilim/web-sitesi-ve-donusum-yuzeyleri/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/avukatlar-icin-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/estetik-klinikleri-icin-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/dis-klinikleri-icin-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/kuaforler-icin-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/guzellik-merkezleri-icin-dijital-pazarlama", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/dijital-pazarlama-stratejisi", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/guzellik-klinik-dijital-pazarlama.html", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/kafe-restoran-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/moda-e-ticaret-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/teknoloji-b2b-dijital-pazarlama/", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/sektorler/yasam-ev-markalari-dijital-pazarlama/", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/kafe-restoran-dijital-pazarlama", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/moda-e-ticaret-dijital-pazarlama", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/teknoloji-b2b-dijital-pazarlama", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/yasam-ev-markalari-dijital-pazarlama", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/blog/instagram-algoritmasi-2026", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/blog/b2b-donusum-hunisi", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/blog/teknik-seo-ve-web-performansi", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/blog/guzellik-merkezi-web-sitesi-nasil-olmali", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/blog/guzellik-merkezleri-icin-dijital-pazarlama", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/blog/guzellik-merkezi-dijital-pazarlama", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/blog/guzellik-merkezleri-icin-seo-nedir", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/gizlilik-politikasi", sitemap)
        self.assertIn(f"{PRODUCTION_URL}/kvkk-aydinlatma-metni", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/web-tasarim.html", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/seo-danismanligi.html", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/google-ads-yonetimi.html", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/sosyal-medya-yonetimi.html", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/blog/b2b-pazarlamada-donusum-hunisi.html", sitemap)
        self.assertNotIn("https://veridiareklam.com.tr/", sitemap)
        self.assertNotIn("127.0.0.1", sitemap)

    def test_sitemap_includes_public_company_and_conversion_pages(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for path in (
            "/hakkimizda",
            "/calisma-surecimiz",
            "/iletisim",
            "/hizli-teklif",
        ):
            with self.subTest(path=path):
                self.assertIn(f"{PRODUCTION_URL}{path}", sitemap)

    def test_sitemap_uses_real_homepage_image_extension(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"{PRODUCTION_URL}/assets/about-visual.jpg", sitemap)
        self.assertNotIn(f"{PRODUCTION_URL}/assets/about-visual.png", sitemap)

    def test_restaurant_page_targets_restaurant_and_cafe_queries(self) -> None:
        page = (ROOT / "kafe-restoran-dijital-pazarlama.html").read_text(encoding="utf-8")
        self.assertIn("<title>Restoran Dijital Pazarlama ve Kafe Pazarlama | Veridia</title>", page)
        self.assertIn(
            '<meta name="description" content="Restoran ve kafeler için yerel SEO, Google Maps, '
            'reklam ve rezervasyon otomasyonu. Mekanınıza özel büyüme planı için ücretsiz ön analiz isteyin.">',
            page,
        )
        self.assertIn("<h1", page)
        self.assertIn("Kafe Pazarlama ve Restoranlar İçin Dijital Sistem</h1>", page)
        self.assertIn(
            'href="https://wa.me/905055174654?text=Merhaba%20Veridia%2C%20restoran%20veya%20kafem%20i%C3%A7in%20dijital%20pazarlama%20%C3%B6n%20analizi%20istiyorum."',
            page,
        )
        self.assertNotIn('href="#"', page)
        self.assertIn("restaurant-google-profile-mock.webp", page)
        self.assertIn("restaurant-kpi-dashboard-mock.webp", page)

    def test_restaurant_page_has_schema_automation_kpis_and_analytics(self) -> None:
        page = (ROOT / "kafe-restoran-dijital-pazarlama.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "Service"', page)
        self.assertIn('"@type": "BreadcrumbList"', page)
        self.assertNotIn("FAQPage", json_ld_types(ROOT / "kafe-restoran-dijital-pazarlama.html"))
        self.assertIn('aria-label="Breadcrumb"', page)
        self.assertIn("n8n ile Rezervasyon ve Takip Otomasyonu", page)
        self.assertIn("Rezervasyon formu", page)
        self.assertIn("Google Sheets veya CRM", page)
        self.assertIn("Ölçüm Planı", page)
        self.assertIn("restaurant_quote_click", page)
        self.assertIn("restaurant_whatsapp_click", page)
        self.assertIn("restaurant_phone_click", page)
        self.assertIn("restaurant_form_submit", page)
        self.assertIn("./assets/analytics.js", page)
        self.assertNotIn("Google My Business", page)
        self.assertNotIn("Kullanıcıların %80'i", page)

    def test_priority_service_pages_link_to_restaurant_landing_page(self) -> None:
        paths = [
            ROOT / "seo" / "google-gorunurlugu" / "index.html",
            ROOT / "reklam" / "google-ads-yonetimi" / "index.html",
            ROOT / "reklam" / "sosyal-medya-yonetimi" / "index.html",
            ROOT / "yazilim" / "web-sitesi-ve-donusum-yuzeyleri" / "index.html",
            ROOT / "dijital-pazarlama-stratejisi.html",
        ]
        for path in paths:
            with self.subTest(path=path):
                page = path.read_text(encoding="utf-8")
                self.assertIn("/sektorler/kafe-restoran-dijital-pazarlama/", page)

    def test_strategy_page_links_to_each_sector_landing_page(self) -> None:
        page = (ROOT / "dijital-pazarlama-stratejisi.html").read_text(encoding="utf-8")
        for href in (
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/",
            "/sektorler/kafe-restoran-dijital-pazarlama/",
            "/sektorler/moda-e-ticaret-dijital-pazarlama/",
            "/sektorler/teknoloji-b2b-dijital-pazarlama/",
            "/sektorler/yasam-ev-markalari-dijital-pazarlama/",
        ):
            with self.subTest(href=href):
                self.assertIn(f'href="{href}"', page)

    def test_analytics_supports_declarative_cta_events(self) -> None:
        analytics = (ROOT / "assets" / "analytics.js").read_text(encoding="utf-8")
        self.assertIn("data-analytics-event", analytics)
        self.assertIn("dataset?.analyticsEvent", analytics)
        self.assertIn("gtag", analytics)

    def test_blog_index_has_no_dead_placeholder_links(self) -> None:
        blog_index = (ROOT / "blog.html").read_text(encoding="utf-8")
        self.assertNotIn('href="#"', blog_index)
        self.assertIn("<!-- BLOG_CARDS -->", blog_index)
        self.assertIn("canonical", blog_index)
        self.assertIn("Veridia Strateji Ekibi", blog_index)
        self.assertNotIn("#analyze", blog_index)

    def test_blog_index_uses_revision_hero_copy_and_card_ctas(self) -> None:
        blog_index = (ROOT / "blog.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Blog</h1>", blog_index)
        self.assertIn(
            "Veridia Reklam Ajansı blogunda web tasarım, SEO, Google reklamları, sosyal medya yönetimi ve sektörlere özel dijital pazarlama stratejileri üzerine rehber içerikler bulabilirsiniz.",
            blog_index,
        )
        self.assertIn("Devamını Oku", blog_index)
        self.assertIn('data-category="guzellik-merkezleri"', blog_index)

    def test_homepage_routes_primary_service_ctas_to_clean_hub_urls(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/yazilim/" class="need-card"', homepage)
        self.assertIn('href="/seo/" class="need-card"', homepage)
        self.assertIn('href="/reklam/" class="need-card"', homepage)
        self.assertIn('href="/yazilim/" class="btn-outline"', homepage)
        self.assertIn('href="/seo/" class="btn-outline"', homepage)
        self.assertIn('href="/reklam/" class="btn-outline"', homepage)

    def test_service_hubs_emit_service_schema(self) -> None:
        for path in (
            ROOT / "seo" / "index.html",
            ROOT / "reklam" / "index.html",
            ROOT / "yazilim" / "index.html",
        ):
            with self.subTest(path=path):
                self.assertIn("Service", json_ld_types(path))

    def test_vercel_deploy_excludes_legacy_service_html_files(self) -> None:
        ignore = (ROOT / ".vercelignore").read_text(encoding="utf-8")
        for path in (
            "/web-tasarim.html",
            "/seo-danismanligi.html",
            "/google-ads-yonetimi.html",
            "/sosyal-medya-yonetimi.html",
        ):
            with self.subTest(path=path):
                self.assertIn(path, ignore)

    def test_article_pages_have_canonical_and_schema(self) -> None:
        article_paths = [
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for article_path in article_paths:
            content = article_path.read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical"', content)
            self.assertIn('"@type": "Article"', content)
            self.assertIn('meta property="og:type" content="article"', content)
            self.assertIn('meta property="og:image"', content)
            self.assertIn("/assets/blog/", content)
            self.assertIn('rel="icon"', content)

    def test_homepage_has_service_catalog_and_visible_service_copy(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "ItemList"', homepage)
        self.assertIn("Web Tasarım", homepage)
        self.assertIn('id="services"', homepage)
        self.assertIn(f'rel="canonical" href="{PRODUCTION_URL}"', homepage)
        self.assertIn("veridia-social-cover.png", homepage)
        self.assertIn("assets/config.js", homepage)
        self.assertIn("assets/home-loader.js", homepage)
        self.assertIn("/hizli-teklif", homepage)
        self.assertIn('id="contactForm"', homepage)
        self.assertIn('action="/api/contact"', homepage)
        self.assertIn('rel="icon"', homepage)
        self.assertNotIn("Marka e-postası bu aşamada doğrulanmadı", homepage)
        self.assertNotIn("APIFY_TOKEN", homepage)
        self.assertNotIn("python3 server.py", homepage)
        self.assertNotIn('href="#contact">Instagram</a>', homepage)

    def test_homepage_does_not_preload_non_critical_social_cover_or_eager_home_scripts(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('<link rel="preload" href="./assets/veridia-social-cover.png" as="image">', homepage)
        self.assertNotIn('<script defer src="./assets/home.js"></script>', homepage)
        self.assertNotIn('<script defer src="./assets/site-data.js"></script>', homepage)
        self.assertNotIn('<script defer src="./assets/quote-pricing.js"></script>', homepage)
        self.assertIn('<link data-deferred-style data-href="./assets/shared.css?v=12" data-style-media="all">', homepage)
        self.assertIn('<link data-deferred-style data-href="./assets/home-mobile-tune.css?v=6" data-style-media="all">', homepage)
        self.assertIn('<link rel="stylesheet" href="./assets/fonts.css?v=5">', homepage)
        self.assertNotIn('<link data-deferred-style data-href="./assets/fonts.css?v=4" data-style-media="all">', homepage)
        self.assertNotIn('\n<link rel="stylesheet" href="./assets/shared.css?v=12">', homepage)
        self.assertNotIn('\n<link rel="stylesheet" href="./assets/home-mobile-tune.css?v=6">', homepage)

    def test_homepage_source_is_canonical_root_document(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('http-equiv="refresh"', index)
        self.assertNotIn("window.location.replace", index)
        self.assertIn(f'rel="canonical" href="{PRODUCTION_URL}"', index)
        self.assertIn("<title>Veridia Reklam", index)

    def test_homepage_schema_uses_verifiable_organization_signals(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@id": "https://www.veridiareklam.com.tr/#organization"', homepage)
        self.assertIn('"@type": "Organization"', homepage)
        self.assertIn("assets/veridia-icon.png", homepage)
        self.assertNotIn('"LocalBusiness"', homepage)
        self.assertNotIn('"SearchAction"', homepage)
        self.assertNotIn('"FAQPage"', homepage)
        self.assertNotIn('"streetAddress"', homepage)
        self.assertNotIn('"postalCode"', homepage)
        self.assertNotIn('<meta name="geo.', homepage)
        self.assertNotIn('<meta name="ICBM"', homepage)
        self.assertNotIn("https://x.com/veridia", homepage)
        self.assertNotIn("https://www.facebook.com/veridia", homepage)
        self.assertNotIn("https://www.linkedin.com/company/veridia", homepage)

    def test_contact_and_service_ctas_point_to_real_targets(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('action="/api/contact"', homepage)
        self.assertNotIn('/iletisim', homepage)
        self.assertIn('/hizli-teklif', homepage)

        for page_name in (
            "hakkimizda.html",
            "calisma-surecimiz.html",
            "seo/google-gorunurlugu/index.html",
            "reklam/google-ads-yonetimi/index.html",
            "reklam/sosyal-medya-yonetimi/index.html",
        ):
            with self.subTest(page_name=page_name):
                content = (ROOT / page_name).read_text(encoding="utf-8")
                self.assertNotIn('/iletisim', content)

    def test_body_internal_links_do_not_hardcode_production_domain(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "hizmetler/index.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "gizlilik-politikasi.html",
            ROOT / "kvkk-aydinlatma-metni.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                body = content.split("<body", 1)[1]
                self.assertNotIn('href="https://www.veridiareklam.com.tr', body)
                self.assertNotIn('href="https://veridiareklam.com.tr', body)

    def test_legal_pages_exist_and_link_back_to_site(self) -> None:
        for page_name in ("gizlilik-politikasi.html", "kvkk-aydinlatma-metni.html"):
            with self.subTest(page_name=page_name):
                page = (ROOT / page_name).read_text(encoding="utf-8")
                self.assertIn("Veridia", page)
                self.assertIn('rel="canonical"', page)
                self.assertIn("veridia-social-cover.png", page)

    def test_pages_use_local_font_manifest_and_no_google_fonts(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "hizmetler/index.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "gizlilik-politikasi.html",
            ROOT / "kvkk-aydinlatma-metni.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("assets/fonts.css", content)
                self.assertNotIn("fonts.googleapis.com", content)
                self.assertNotIn("fonts.gstatic.com", content)

    def test_pages_do_not_use_inline_script_handlers(self) -> None:
        paths = [
            ROOT / "index.html",
            ROOT / "hizmetler/index.html",
            ROOT / "calismalarimiz.html",
            ROOT / "blog.html",
            ROOT / "404.html",
            ROOT / "blog" / "instagram-algoritmasi-2026.html",
            ROOT / "blog" / "b2b-donusum-hunisi.html",
            ROOT / "blog" / "teknik-seo-ve-web-performansi.html",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("onclick=", content)
                self.assertNotIn("onload=", content)
                self.assertNotIn("window.dataLayer", content)

    def test_work_pages_have_canonical_schema_and_local_assets(self) -> None:
        work_pages = [
            ROOT / "calismalarimiz.html",
        ]
        for page_path in work_pages:
            with self.subTest(page=page_path.name):
                content = page_path.read_text(encoding="utf-8")
                self.assertIn('<link rel="canonical"', content)
                self.assertIn('"@type": "CollectionPage"', content)
                self.assertIn("assets/work-pages.css", content)
                self.assertIn("assets/work-pages.js", content)
                self.assertIn("data-whatsapp-message", content)
                self.assertIn("veridia-social-cover.png", content)
                self.assertNotIn('href="#"', content)

    def test_silo_hub_pages_exist_with_collection_schema_and_local_assets(self) -> None:
        hub_pages = [
            ROOT / "hizmetler" / "index.html",
            ROOT / "seo" / "index.html",
            ROOT / "reklam" / "index.html",
            ROOT / "yazilim" / "index.html",
        ]
        for page_path in hub_pages:
            with self.subTest(page=page_path):
                content = page_path.read_text(encoding="utf-8")
                self.assertIn('<link rel="canonical"', content)
                self.assertIn("CollectionPage", json_ld_types(page_path))
                self.assertIn("/assets/silo-pages.css", content)
                self.assertTrue('href="/#contact"' in content or 'href="/#quote"' in content)
                self.assertNotIn('href="#"', content)

    def test_silo_service_pages_use_service_schema_and_local_assets(self) -> None:
        service_pages = [
            ROOT / "seo" / "teknik-seo-denetimi" / "index.html",
            ROOT / "seo" / "google-gorunurlugu" / "index.html",
            ROOT / "reklam" / "sosyal-medya-yonetimi" / "index.html",
            ROOT / "reklam" / "google-ads-yonetimi" / "index.html",
            ROOT / "reklam" / "meta-reklam-yonetimi" / "index.html",
            ROOT / "yazilim" / "web-sitesi-ve-donusum-yuzeyleri" / "index.html",
        ]
        for page_path in service_pages:
            with self.subTest(page=page_path):
                content = page_path.read_text(encoding="utf-8")
                self.assertIn('<link rel="canonical"', content)
                types = json_ld_types(page_path)
                self.assertIn("Service", types)
                self.assertNotIn("CollectionPage", types)
                self.assertIn("/assets/silo-pages.css", content)
                self.assertTrue('href="/#contact"' in content or 'href="/#quote"' in content)
                self.assertNotIn('href="#"', content)

    def test_sector_landing_pages_have_service_and_breadcrumb_schema(self) -> None:
        for page_name in (
            "sektorler/kafe-restoran-dijital-pazarlama/index.html",
            "sektorler/moda-e-ticaret-dijital-pazarlama/index.html",
            "sektorler/teknoloji-b2b-dijital-pazarlama/index.html",
            "sektorler/yasam-ev-markalari-dijital-pazarlama/index.html",
        ):
            with self.subTest(page=page_name):
                types = json_ld_types(ROOT / page_name)
                self.assertIn("Service", types)
                self.assertIn("BreadcrumbList", types)

    def test_blog_schema_lists_every_published_graph_post(self) -> None:
        graph = json.loads((ROOT / "content" / "site_graph.json").read_text(encoding="utf-8"))
        schema = json.dumps(read_json_ld(ROOT / "blog.html"), ensure_ascii=False)
        for post in graph["blog_posts"]:
            with self.subTest(post=post["slug"]):
                self.assertIn(f'{PRODUCTION_URL}{post["url"]}', schema)

    def test_article_json_ld_avoids_deprecated_faq_and_ineligible_speakable_markup(self) -> None:
        for article_name in (
            "instagram-algoritmasi-2026.html",
            "b2b-donusum-hunisi.html",
            "teknik-seo-ve-web-performansi.html",
        ):
            with self.subTest(article=article_name):
                types = json_ld_types(ROOT / "blog" / article_name)
                self.assertNotIn("FAQPage", types)
                self.assertNotIn("SpeakableSpecification", types)

    def test_public_marketing_pages_have_social_share_metadata(self) -> None:
        for page_name in (
            "hakkimizda.html",
            "calisma-surecimiz.html",
            "hizli-teklif.html",
            "dijital-pazarlama-stratejisi.html",
            "kafe-restoran-dijital-pazarlama.html",
            "moda-e-ticaret-dijital-pazarlama.html",
            "teknoloji-b2b-dijital-pazarlama.html",
            "yasam-ev-markalari-dijital-pazarlama.html",
        ):
            with self.subTest(page=page_name):
                content = (ROOT / page_name).read_text(encoding="utf-8")
                self.assertIn('meta property="og:title"', content)
                self.assertIn('meta property="og:description"', content)
                self.assertIn('meta property="og:image"', content)
                self.assertIn('meta name="twitter:card"', content)

    def test_content_images_reserve_intrinsic_dimensions(self) -> None:
        contact = (ROOT / "iletisim.html").read_text(encoding="utf-8")
        self.assertIn(
            '<img src="./assets/about-visual.jpg" alt="Veridia\'nın dijital büyüme odaklı çalışma yaklaşımını temsil eden görsel" width="1024" height="1024">',
            contact,
        )
        article = (ROOT / "blog" / "web-siteniz-neden-musteri-getirmiyor.html").read_text(encoding="utf-8")
        for src in (
            "/assets/web-conversion-speed-curve.svg",
            "/assets/web-conversion-trust-stack.svg",
            "/assets/web-conversion-funnel.svg",
        ):
            with self.subTest(src=src):
                self.assertRegex(
                    article,
                    rf'<img src="{re.escape(src)}"[^>]* width="1600" height="900"',
                )

    def test_legacy_html_service_duplicates_are_removed(self) -> None:
        legacy_pages = (
            "web-tasarim.html",
            "seo-danismanligi.html",
            "google-ads-yonetimi.html",
            "sosyal-medya-yonetimi.html",
        )
        for page_name in legacy_pages:
            with self.subTest(page=page_name):
                self.assertFalse((ROOT / page_name).exists())

    def test_case_studies_page_positions_scenarios_transparently(self) -> None:
        content = (ROOT / "calismalarimiz.html").read_text(encoding="utf-8")
        self.assertIn("<title>Örnek Çalışma Senaryoları | Veridia</title>", content)
        self.assertIn("örnek çalışma senaryoları", content)
        self.assertIn("anonimleştirilmiş vaka notları", content)
        self.assertIn("müşteri yorumu değil", content)

    def test_vercel_config_has_no_site_host_redirect_rules(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = config.get("redirects", [])
        blocked_hosts = {"veridiareklam.com.tr", "www.veridiareklam.com.tr"}
        for redirect in redirects:
            host_values = {
                condition.get("value")
                for condition in redirect.get("has", [])
                if condition.get("type") == "host"
            }
            self.assertFalse(blocked_hosts & host_values)

    def test_vercel_config_redirects_legacy_google_ads_page(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = config.get("redirects", [])
        self.assertIn(
            {
                "source": "/google-ads-yonetimi.html",
                "destination": "/hizmetler/google-ads-yonetimi/",
                "permanent": True,
            },
            redirects,
        )

    def test_vercel_config_redirects_consolidated_beauty_article(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = config.get("redirects", [])
        actual = {(redirect["source"], redirect["destination"]) for redirect in redirects}
        expected = {
            (
                "/blog/guzellik-merkezi-dijital-pazarlama",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-merkezi-dijital-pazarlama.html",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-merkezleri-icin-seo-nedir",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-merkezleri-icin-seo-nedir.html",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama-nedir.html",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/guzellik-klinik-dijital-pazarlama",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/guzellik-klinik-dijital-pazarlama.html",
                "/blog/guzellik-merkezleri-icin-dijital-pazarlama",
            ),
            (
                "/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar",
                "/blog/guzellik-merkezi-web-sitesi-nasil-olmali",
            ),
            (
                "/blog/guzellik-salonu-web-sitesinde-olmasi-gereken-zorunlu-sayfalar.html",
                "/blog/guzellik-merkezi-web-sitesi-nasil-olmali",
            ),
        }
        self.assertTrue(expected.issubset(actual))

    def test_vercel_config_redirects_all_legacy_and_slashless_silo_paths(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = config.get("redirects", [])
        expected = {
            ("/index.html", "/"),
            ("/asdfadsf.html", "/"),
            ("/veridia-ajans.html", "/"),
            ("/blog/b2b-pazarlamada-donusum-hunisi.html", "/blog/b2b-donusum-hunisi"),
            ("/web-tasarim.html", "/hizmetler/web-tasarim/"),
            ("/seo-danismanligi.html", "/hizmetler/seo-danismanligi/"),
            ("/google-ads-yonetimi.html", "/hizmetler/google-ads-yonetimi/"),
            ("/sosyal-medya-yonetimi.html", "/hizmetler/sosyal-medya-yonetimi/"),
            ("/seo", "/seo/"),
            ("/seo/teknik-seo-denetimi", "/seo/teknik-seo-denetimi/"),
            ("/seo/google-gorunurlugu", "/seo/google-gorunurlugu/"),
            ("/reklam", "/reklam/"),
            ("/reklam/sosyal-medya-yonetimi", "/reklam/sosyal-medya-yonetimi/"),
            ("/reklam/google-ads-yonetimi", "/reklam/google-ads-yonetimi/"),
            ("/reklam/meta-reklam-yonetimi", "/reklam/meta-reklam-yonetimi/"),
            ("/yazilim", "/yazilim/"),
            ("/yazilim/web-sitesi-ve-donusum-yuzeyleri", "/yazilim/web-sitesi-ve-donusum-yuzeyleri/"),
            ("/sektorler", "/sektorler/"),
            ("/sektorler/guzellik-merkezleri-icin-dijital-pazarlama", "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/"),
            ("/sektorler/avukatlar-icin-dijital-pazarlama", "/sektorler/avukatlar-icin-dijital-pazarlama/"),
            ("/sektorler/estetik-klinikleri-icin-dijital-pazarlama", "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/"),
            ("/sektorler/dis-klinikleri-icin-dijital-pazarlama", "/sektorler/dis-klinikleri-icin-dijital-pazarlama/"),
            ("/sektorler/kuaforler-icin-dijital-pazarlama", "/sektorler/kuaforler-icin-dijital-pazarlama/"),
            ("/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama", "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/"),
            ("/guzellik-klinik-dijital-pazarlama.html", "/blog/guzellik-merkezleri-icin-dijital-pazarlama"),
            ("/guzellik-merkezleri-icin-dijital-pazarlama", "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/"),
        }
        actual = {(redirect["source"], redirect["destination"]) for redirect in redirects}
        self.assertTrue(expected <= actual)

    def test_htaccess_redirects_non_www_to_www_before_path_redirects(self) -> None:
        htaccess = (ROOT / ".htaccess").read_text(encoding="utf-8")
        self.assertIn("RewriteCond %{HTTP_HOST} ^veridiareklam\\.com\\.tr$", htaccess)
        self.assertIn("RewriteRule ^(.*)$ https://www.veridiareklam.com.tr/$1 [R=301,L]", htaccess)
        self.assertLess(htaccess.index("RewriteCond %{HTTP_HOST}"), htaccess.index("Redirect 301"))

    def test_root_sector_urls_are_legacy_only_after_sektorler_standard(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        redirects = {(redirect["source"], redirect["destination"]) for redirect in config.get("redirects", [])}
        expected = {
            ("/kafe-restoran-dijital-pazarlama", "/sektorler/kafe-restoran-dijital-pazarlama/"),
            ("/kafe-restoran-dijital-pazarlama.html", "/sektorler/kafe-restoran-dijital-pazarlama/"),
            ("/moda-e-ticaret-dijital-pazarlama", "/sektorler/moda-e-ticaret-dijital-pazarlama/"),
            ("/moda-e-ticaret-dijital-pazarlama.html", "/sektorler/moda-e-ticaret-dijital-pazarlama/"),
            ("/teknoloji-b2b-dijital-pazarlama", "/sektorler/teknoloji-b2b-dijital-pazarlama/"),
            ("/teknoloji-b2b-dijital-pazarlama.html", "/sektorler/teknoloji-b2b-dijital-pazarlama/"),
            ("/yasam-ev-markalari-dijital-pazarlama", "/sektorler/yasam-ev-markalari-dijital-pazarlama/"),
            ("/yasam-ev-markalari-dijital-pazarlama.html", "/sektorler/yasam-ev-markalari-dijital-pazarlama/"),
        }
        self.assertTrue(expected <= redirects)
        rewrite_sources = {rewrite["source"] for rewrite in config.get("rewrites", [])}
        for source, _ in expected:
            self.assertNotIn(source, rewrite_sources)

    def test_vercel_config_sets_browser_cache_headers_for_assets(self) -> None:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        headers = config.get("headers", [])
        self.assertIn(
            {
                "source": "/assets/fonts/(.*)",
                "headers": [
                    {
                        "key": "Cache-Control",
                        "value": "public, max-age=31536000, immutable",
                    }
                ],
            },
            headers,
        )
        self.assertIn(
            {
                "source": "/assets/(.*)",
                "headers": [
                    {
                        "key": "Cache-Control",
                        "value": "public, max-age=86400, stale-while-revalidate=604800",
                    }
                ],
            },
            headers,
        )

    def test_public_html_canonical_and_og_urls_use_single_www_host(self) -> None:
        public_pages = list(ROOT.glob("*.html")) + list((ROOT / "blog").glob("*.html"))
        for path in public_pages:
            content = path.read_text(encoding="utf-8")
            head = content.split("</head>", 1)[0]
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("https://veridiareklam.com.tr", head)
                self.assertNotIn("http://veridiareklam.com.tr", head)

    def test_about_page_exposes_founder_identity_without_fake_portrait_claim(self) -> None:
        page = (ROOT / "hakkimizda.html").read_text(encoding="utf-8")
        self.assertIn("Kurucu: Yaşar İshak Topçu", page)
        self.assertIn("SEO, web performansı, reklam ölçümü ve dönüşüm odaklı web yüzeyleri", page)
        self.assertIn("Kurucu portresi eklenecek", page)

    def test_every_blog_article_has_visible_author_box(self) -> None:
        article_paths = list((ROOT / "blog").glob("*.html")) + list((ROOT / "blog").glob("*/index.html"))
        self.assertGreater(len(article_paths), 0)
        for path in article_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                content = path.read_text(encoding="utf-8")
                self.assertIn('class="author-box"', content)
                self.assertIn("Yazar", content)

    def test_vercelignore_allowlists_only_public_static_surfaces(self) -> None:
        patterns = (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("/*", patterns)
        for pattern in (
            "!assets",
            "!blog",
            "!seo",
            "!reklam",
            "!yazilim",
            "!sektorler",
            "!*.html",
            "!robots.txt",
            "!sitemap.xml",
            "!vercel.json",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, patterns)
        for private_pattern in ("!automation", "!content", "!scripts", "!tests", "!server.py"):
            with self.subTest(private_pattern=private_pattern):
                self.assertNotIn(private_pattern, patterns)

    def test_blog_articles_do_not_link_to_legacy_service_pages(self) -> None:
        legacy_urls = (
            "/web-tasarim.html",
            "/seo-danismanligi.html",
            "/google-ads-yonetimi.html",
            "/sosyal-medya-yonetimi.html",
        )
        for article_path in (ROOT / "blog").glob("*.html"):
            content = article_path.read_text(encoding="utf-8")
            for legacy_url in legacy_urls:
                with self.subTest(article=article_path.name, legacy_url=legacy_url):
                    self.assertNotIn(f'href="{legacy_url}"', content)

    def test_sector_pages_have_metadata_schema_and_single_h1(self) -> None:
        pages = [
            (
                ROOT / "sektorler" / "index.html",
                "Sektörlere Özel Dijital Pazarlama Çözümleri | Veridia Reklam Ajansı",
                f"{PRODUCTION_URL}/sektorler/",
            ),
            (
                ROOT / "sektorler" / "guzellik-merkezleri-icin-dijital-pazarlama" / "index.html",
                "Güzellik Merkezi Dijital Pazarlama Hizmeti | Veridia",
                f"{PRODUCTION_URL}/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/",
            ),
            (
                ROOT / "sektorler" / "avukatlar-icin-dijital-pazarlama" / "index.html",
                "Avukatlar İçin Dijital Pazarlama | Veridia Reklam Ajansı",
                f"{PRODUCTION_URL}/sektorler/avukatlar-icin-dijital-pazarlama/",
            ),
            (
                ROOT / "sektorler" / "estetik-klinikleri-icin-dijital-pazarlama" / "index.html",
                "Estetik Klinikleri İçin Dijital Pazarlama | Veridia",
                f"{PRODUCTION_URL}/sektorler/estetik-klinikleri-icin-dijital-pazarlama/",
            ),
            (
                ROOT / "sektorler" / "dis-klinikleri-icin-dijital-pazarlama" / "index.html",
                "Diş Klinikleri İçin Dijital Pazarlama | Veridia",
                f"{PRODUCTION_URL}/sektorler/dis-klinikleri-icin-dijital-pazarlama/",
            ),
            (
                ROOT / "sektorler" / "kuaforler-icin-dijital-pazarlama" / "index.html",
                "Kuaförler İçin Dijital Pazarlama | Veridia",
                f"{PRODUCTION_URL}/sektorler/kuaforler-icin-dijital-pazarlama/",
            ),
            (
                ROOT / "sektorler" / "yerel-servis-isletmeleri-icin-dijital-pazarlama" / "index.html",
                "Yerel Servis İşletmeleri İçin Dijital Pazarlama | Veridia",
                f"{PRODUCTION_URL}/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/",
            ),
        ]

        for path, title, canonical in pages:
            with self.subTest(path=path):
                page = path.read_text(encoding="utf-8")
                self.assertIn(f"<title>{title}</title>", page)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', page)
                self.assertEqual(len(re.findall(r"<h1\b", page)), 1)
                types = json_ld_types(path)
                self.assertIn("BreadcrumbList", types)
                self.assertIn("FAQPage", types)
                self.assertIn('aria-label="Breadcrumb"', page)

    def test_beauty_pillar_article_has_consolidated_seo_sections_and_clean_canonical(self) -> None:
        page = (ROOT / "blog" / "guzellik-merkezleri-icin-dijital-pazarlama.html").read_text(encoding="utf-8")
        self.assertIn(
            '<link rel="canonical" href="https://www.veridiareklam.com.tr/blog/guzellik-merkezleri-icin-dijital-pazarlama">',
            page,
        )
        self.assertIn(
            "Güzellik Merkezi SEO: Google'da Nasıl Üst Sıralara Çıkarsınız",
            page,
        )
        self.assertIn("Güzellik Merkezi Web Sitesi Nasıl Olmalı", page)
        self.assertIn("Google Business Profile ve Yorum Yönetimi ile Lokal SEO", page)
        self.assertIn("Instagram Yönetimi: Güven ve Talep Üretimi", page)
        self.assertIn("FAQPage", page)
        self.assertIn("/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/", page)
        self.assertIn("/blog/guzellik-merkezi-web-sitesi-nasil-olmali", page)

    def test_sector_hub_links_all_active_sector_landings_and_tracks_ctas(self) -> None:
        page = (ROOT / "sektorler" / "index.html").read_text(encoding="utf-8")
        for href in (
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/",
            "/sektorler/avukatlar-icin-dijital-pazarlama/",
            "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/dis-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/kuaforler-icin-dijital-pazarlama/",
            "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/",
        ):
            with self.subTest(href=href):
                self.assertIn(href, page)
        self.assertIn("sectors_page_free_analysis_click", page)
        self.assertIn("sectors_beauty_card_click", page)
        self.assertNotIn("Yakında", page)

    def test_revision_mobile_menu_links_directly_to_sector_landings(self) -> None:
        script = (ROOT / "assets" / "revision.js").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('href: "/sektorler/", label: "Sektörler"', script)
        self.assertIn("revision-mobile-sector-group", script)
        self.assertIn("<p class=\"revision-mobile-section-label\">Sektörler</p>", script)
        for href in (
            "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/",
            "/sektorler/avukatlar-icin-dijital-pazarlama/",
            "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/dis-klinikleri-icin-dijital-pazarlama/",
            "/sektorler/kuaforler-icin-dijital-pazarlama/",
            "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/",
        ):
            with self.subTest(href=href):
                self.assertIn(f'href: "{href}"', script)
        self.assertRegex(homepage, r'/assets/revision\.js\?v=\d+')
        self.assertRegex(homepage, r'/assets/revision\.css\?v=\d+')

    def test_beauty_sector_page_marks_missing_service_pages_without_links(self) -> None:
        page = (ROOT / "sektorler" / "guzellik-merkezleri-icin-dijital-pazarlama" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("beauty_sector_free_analysis_click", page)
        self.assertIn("beauty_sector_service_card_click", page)
        for href in (
            "/guzellik-merkezi-web-tasarim",
            "/guzellik-merkezi-seo",
            "/guzellik-merkezi-google-reklamlari",
            "/guzellik-merkezi-sosyal-medya-yonetimi",
        ):
            with self.subTest(href=href):
                self.assertNotIn(f'href="{href}"', page)

if __name__ == "__main__":
    unittest.main()
