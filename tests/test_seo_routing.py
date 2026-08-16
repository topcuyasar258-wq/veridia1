"""Teknik SEO regresyon testleri.

`test_seo_smoke.py` tek tek sayfalarin icerigini dogrular. Bu modul ise
`vercel.json` yonlendirme katmanini modelleyip su sorulari sorar:

- Bir dosya birden fazla URL'de 200 donuyor mu? (kopya icerik)
- Canonical, kendi sayfasina isaret ediyor ve kendisi yonlenmiyor mu?
- Ic linkler 404 veya gereksiz redirect uretiyor mu?
- Sitemap girdileri canonical ve 200 mu?
- Redirect zinciri veya kirik redirect var mi?
- Referans verilen gorseller ve JSON-LD URL'leri gercekten var mi?

Vercel davranisi (canli sitede dogrulandi):
- `cleanUrls: false` -> uzantisiz URL'ler yalnizca dizin `index.html`
  varsa ya da acik bir rewrite tanimliysa cozulur.
- `/dizin` <-> `/dizin/` ve `/dizin/index.html` normalizasyonunu Vercel
  kendisi 301 ile yapar.
- Redirect'ler rewrite'lardan once calisir; rewrite hedefi dogrudan
  dosya sisteminden servis edilir, redirect asamasina geri girmez.
"""

from __future__ import annotations

import json
import re
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.veridiareklam.com.tr"
SITE_HOSTS = {"www.veridiareklam.com.tr", "veridiareklam.com.tr"}

# Yalnizca public olarak servis edilen yuzeyler taranir.
SKIP_DIRS = {"node_modules", ".git", "automation", "site_src", "content", "tests"}

_CONFIG = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
CLEAN_URLS = _CONFIG.get("cleanUrls", False)

# Host bazli (apex -> www) ve pattern iceren kurallar bu statik modelin
# disinda kalir; onlari `test_seo_smoke` ve canli kontrol kapsar.
REDIRECTS: dict[str, tuple[str, int]] = {}
for _rule in _CONFIG.get("redirects", []):
    _src = _rule["source"]
    if _rule.get("has") or ":" in _src or "*" in _src:
        continue
    REDIRECTS[_src] = (_rule["destination"], _rule.get("statusCode", 308))

REWRITES = {r["source"]: r["destination"] for r in _CONFIG.get("rewrites", [])}


def fs_lookup(path: str) -> Path | None:
    """URL yolunu Vercel'in statik dosya katmani gibi cozer."""
    rel = path.lstrip("/").rstrip("/")
    if rel == "":
        candidate = ROOT / "index.html"
        return candidate if candidate.is_file() else None
    if not path.endswith("/"):
        candidate = ROOT / rel
        if candidate.is_file():
            return candidate
    candidate = ROOT / rel / "index.html"
    if candidate.is_file():
        return candidate
    if CLEAN_URLS:
        candidate = ROOT / (rel + ".html")
        if candidate.is_file():
            return candidate
    return None


def settle(path: str) -> str:
    """Redirect zinciri bittikten sonra tarayicinin kaldigi URL yolu."""
    current = path
    for _ in range(10):
        if current in REDIRECTS:
            current = urlparse(REDIRECTS[current][0]).path or "/"
            continue
        break
    return current


def resolve(path: str) -> tuple[str, Path | str]:
    """(durum, deger) dondurur; durum: file | redirect-loop | 404 | external."""
    current = path
    for _ in range(10):
        if current in REDIRECTS:
            parsed = urlparse(REDIRECTS[current][0])
            if parsed.netloc and parsed.netloc not in SITE_HOSTS:
                return ("external", REDIRECTS[current][0])
            current = parsed.path or "/"
            continue
        hit = fs_lookup(current)
        if hit is not None:
            return ("file", hit)
        if current in REWRITES:
            # Rewrite hedefi dogrudan dosya sisteminden servis edilir.
            hit = fs_lookup(REWRITES[current])
            return ("file", hit) if hit else ("404", REWRITES[current])
        return ("404", current)
    return ("redirect-loop", path)


def public_url(file: Path) -> str:
    """Bir repo dosyasinin redirect sonrasi public URL yolu."""
    rel = "/" + str(file.relative_to(ROOT))
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return settle(rel)


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.canonicals: list[str] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False
        self.lang: str | None = None
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "html":
            self.lang = attr.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attr.get("name") or attr.get("property")
            if key:
                self.meta[key.lower()] = attr.get("content", "")
        elif tag == "link" and "canonical" in (attr.get("rel") or "").lower().split():
            self.canonicals.append(attr.get("href", ""))
        elif tag == "a":
            self.links.append(attr)
        elif tag == "img":
            self.images.append(attr)
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "script" and attr.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data
        if self._in_jsonld and self.jsonld:
            self.jsonld[-1] += data


def _html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not any(part in SKIP_DIRS for part in path.parts)
    )


HTML_FILES = _html_files()
PAGES: dict[Path, _Page] = {}
for _file in HTML_FILES:
    _parser = _Page()
    _parser.feed(_file.read_text(encoding="utf-8", errors="replace"))
    PAGES[_file] = _parser


def _live_urls() -> dict[Path, list[str]]:
    """Her dosya icin redirect'siz 200 donen URL'ler."""
    candidates: set[str] = {"/"}
    for file in HTML_FILES:
        rel = "/" + str(file.relative_to(ROOT))
        candidates.add(rel)
        if rel.endswith("/index.html"):
            directory = rel[: -len("index.html")]
            candidates.add(directory)
            candidates.add(directory.rstrip("/"))
        else:
            candidates.add(rel[: -len(".html")])
    candidates.update(REWRITES)
    candidates.update(urlparse(dest).path or "/" for dest, _ in REDIRECTS.values())

    live: dict[Path, list[str]] = defaultdict(list)
    for url in sorted(candidates):
        if not url or settle(url) != url:
            continue  # 301 veriyor, canli kopya degil
        kind, value = resolve(url)
        if kind == "file":
            live[value].append(url)  # type: ignore[index]
    return live


LIVE_URLS = _live_urls()
# Tamamen yonlendirilmis (hicbir URL'in servis etmedigi) arsiv dosyalari.
UNREACHABLE = {file for file in HTML_FILES if not LIVE_URLS.get(file)}
SERVED = [file for file in HTML_FILES if file not in UNREACHABLE]
NOT_FOUND_PAGE = ROOT / "404.html"


class RoutingTests(unittest.TestCase):
    def test_each_page_is_served_by_exactly_one_url(self) -> None:
        """Ayni dosya birden fazla URL'de 200 donerse kopya icerik olusur."""
        duplicates = {
            "/" + str(file.relative_to(ROOT)): urls
            for file, urls in LIVE_URLS.items()
            if len(urls) > 1
        }
        self.assertEqual(duplicates, {}, f"Kopya URL'ler: {duplicates}")

    def test_redirects_do_not_chain_or_break(self) -> None:
        for source, (destination, status) in REDIRECTS.items():
            with self.subTest(source=source):
                target = urlparse(destination).path or "/"
                self.assertNotEqual(target, source, "redirect kendine isaret ediyor")
                self.assertEqual(
                    settle(target), target, f"redirect zinciri: {source} -> {target} -> {settle(target)}"
                )
                self.assertEqual(resolve(target)[0], "file", f"redirect hedefi 200 donmuyor: {target}")
                self.assertIn(status, (301, 308), "kalici olmayan redirect")

    def test_rewrite_targets_exist(self) -> None:
        for source, destination in REWRITES.items():
            with self.subTest(source=source):
                self.assertTrue(
                    (ROOT / destination.lstrip("/")).is_file(),
                    f"rewrite hedefi yok: {destination}",
                )


class CanonicalTests(unittest.TestCase):
    def test_every_served_page_has_one_absolute_canonical(self) -> None:
        for file in SERVED:
            if file == NOT_FOUND_PAGE:
                continue
            with self.subTest(page=str(file.relative_to(ROOT))):
                canonicals = PAGES[file].canonicals
                self.assertEqual(len(canonicals), 1, "tam olarak bir canonical bekleniyor")
                self.assertTrue(canonicals[0].startswith(f"{SITE}/") or canonicals[0] == SITE)

    def test_canonical_points_at_its_own_page_and_does_not_redirect(self) -> None:
        for file in SERVED:
            if file == NOT_FOUND_PAGE or not PAGES[file].canonicals:
                continue
            with self.subTest(page=str(file.relative_to(ROOT))):
                path = urlparse(PAGES[file].canonicals[0]).path or "/"
                self.assertEqual(settle(path), path, "canonical kendisi yonleniyor")
                kind, value = resolve(path)
                self.assertEqual(kind, "file", f"canonical 200 donmuyor: {path}")
                self.assertEqual(value, file, f"canonical baska bir dosyayi servis ediyor: {path}")

    def test_canonicals_are_unique_across_served_pages(self) -> None:
        seen: dict[str, list[str]] = defaultdict(list)
        for file in SERVED:
            for href in PAGES[file].canonicals:
                seen[href].append(str(file.relative_to(ROOT)))
        clashes = {href: pages for href, pages in seen.items() if len(pages) > 1}
        self.assertEqual(clashes, {}, f"Ayni canonical birden fazla sayfada: {clashes}")

    def test_served_pages_are_indexable(self) -> None:
        for file in SERVED:
            if file == NOT_FOUND_PAGE:
                continue
            with self.subTest(page=str(file.relative_to(ROOT))):
                self.assertNotIn("noindex", PAGES[file].meta.get("robots", "").lower())


class HeadTests(unittest.TestCase):
    def test_core_head_tags_present(self) -> None:
        for file in SERVED:
            page = PAGES[file]
            with self.subTest(page=str(file.relative_to(ROOT))):
                self.assertTrue((page.title or "").strip(), "title yok")
                self.assertTrue((page.lang or "").lower().startswith("tr"), "html lang tr degil")
                self.assertIn("viewport", page.meta, "viewport meta yok")
                if file != NOT_FOUND_PAGE:
                    self.assertTrue(page.meta.get("description", "").strip(), "meta description yok")
                    self.assertEqual(page.h1_count, 1, f"{page.h1_count} adet h1")

    def test_titles_and_descriptions_are_unique(self) -> None:
        titles: dict[str, list[str]] = defaultdict(list)
        descriptions: dict[str, list[str]] = defaultdict(list)
        for file in SERVED:
            name = str(file.relative_to(ROOT))
            page = PAGES[file]
            if page.title:
                titles[page.title.strip()].append(name)
            if page.meta.get("description"):
                descriptions[page.meta["description"].strip()].append(name)
        self.assertEqual(
            {t: p for t, p in titles.items() if len(p) > 1}, {}, "ayni title birden fazla sayfada"
        )
        self.assertEqual(
            {d: p for d, p in descriptions.items() if len(p) > 1},
            {},
            "ayni meta description birden fazla sayfada",
        )

    def test_open_graph_image_is_absolute_and_exists(self) -> None:
        for file in SERVED:
            image = PAGES[file].meta.get("og:image", "")
            if not image:
                continue
            with self.subTest(page=str(file.relative_to(ROOT))):
                self.assertTrue(image.startswith("http"), "og:image mutlak URL olmali")
                self.assertTrue(
                    (ROOT / urlparse(image).path.lstrip("/")).is_file(),
                    f"og:image dosyasi yok: {image}",
                )


class InternalLinkTests(unittest.TestCase):
    def test_internal_links_resolve_without_404_or_redirect(self) -> None:
        for file in SERVED:
            base = public_url(file)
            for anchor in PAGES[file].links:
                href = anchor.get("href", "").strip()
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                    continue
                parsed = urlparse(href)
                if parsed.scheme in ("http", "https"):
                    if parsed.netloc not in SITE_HOSTS:
                        continue
                    target = parsed.path or "/"
                else:
                    target = urlparse(urljoin(base, href)).path
                if not target.startswith("/"):
                    continue
                with self.subTest(page=str(file.relative_to(ROOT)), href=href):
                    self.assertEqual(
                        settle(target), target, f"ic link redirect'ten geciyor: {target}"
                    )
                    self.assertEqual(resolve(target)[0], "file", f"ic link 404: {target}")

    def test_referenced_images_exist(self) -> None:
        for file in SERVED:
            base = public_url(file)
            for image in PAGES[file].images:
                src = image.get("src", "")
                if not src or src.startswith(("http", "data:", "//")):
                    continue
                with self.subTest(page=str(file.relative_to(ROOT)), src=src):
                    path = urlparse(urljoin(base, src)).path
                    self.assertTrue((ROOT / path.lstrip("/")).is_file(), f"gorsel yok: {src}")

    def test_images_have_alt_attribute(self) -> None:
        for file in SERVED:
            for image in PAGES[file].images:
                with self.subTest(page=str(file.relative_to(ROOT)), src=image.get("src", "?")):
                    self.assertIn("alt", image)


class StructuredDataTests(unittest.TestCase):
    def _site_urls(self, node: object, found: list[tuple[str, str]]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("url", "@id", "mainEntityOfPage", "item", "image") and isinstance(value, str):
                    if value.startswith(SITE):
                        found.append((key, value))
                self._site_urls(value, found)
        elif isinstance(node, list):
            for value in node:
                self._site_urls(value, found)

    def test_json_ld_parses_and_urls_resolve(self) -> None:
        for file in SERVED:
            name = str(file.relative_to(ROOT))
            for index, block in enumerate(PAGES[file].jsonld):
                with self.subTest(page=name, block=index):
                    data = json.loads(block)  # gecersiz JSON burada patlar
                found: list[tuple[str, str]] = []
                self._site_urls(data, found)
                for key, value in found:
                    path = urlparse(value.split("#")[0]).path or "/"
                    with self.subTest(page=name, key=key, url=value):
                        if re.search(r"\.(png|jpe?g|webp|svg|gif|ico)$", path, re.IGNORECASE):
                            self.assertTrue((ROOT / path.lstrip("/")).is_file(), "schema gorseli yok")
                        else:
                            self.assertEqual(settle(path), path, "schema URL'i yonleniyor")
                            self.assertEqual(resolve(path)[0], "file", "schema URL'i 404")


class SitemapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.locs = re.findall(r"<url>\s*<loc>(.*?)</loc>", self.sitemap, flags=re.DOTALL)

    def test_entries_are_unique_canonical_and_return_200(self) -> None:
        self.assertEqual(len(self.locs), len(set(self.locs)), "sitemap'te tekrar eden URL var")
        for loc in self.locs:
            with self.subTest(loc=loc):
                self.assertTrue(loc.startswith(SITE), "sitemap URL'i production host kullanmali")
                path = urlparse(loc).path or "/"
                self.assertEqual(settle(path), path, "sitemap URL'i yonleniyor")
                kind, value = resolve(path)
                self.assertEqual(kind, "file", "sitemap URL'i 200 donmuyor")
                canonicals = PAGES[value].canonicals  # type: ignore[index]
                if canonicals:
                    self.assertEqual(
                        urlparse(canonicals[0]).path or "/",
                        path,
                        "sitemap URL'i sayfanin canonical'i degil",
                    )

    def test_every_served_page_is_listed(self) -> None:
        listed = {urlparse(loc).path or "/" for loc in self.locs}
        for file in SERVED:
            if file == NOT_FOUND_PAGE or not PAGES[file].canonicals:
                continue
            path = urlparse(PAGES[file].canonicals[0]).path or "/"
            with self.subTest(page=str(file.relative_to(ROOT))):
                self.assertIn(path, listed, "sayfa sitemap'te yok")

    def test_lastmod_and_images_are_valid(self) -> None:
        for lastmod in re.findall(r"<lastmod>(.*?)</lastmod>", self.sitemap):
            with self.subTest(lastmod=lastmod):
                self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z))?$")
        for image in re.findall(r"<image:loc>(.*?)</image:loc>", self.sitemap):
            with self.subTest(image=image):
                self.assertTrue((ROOT / urlparse(image).path.lstrip("/")).is_file())


if __name__ == "__main__":
    unittest.main()
