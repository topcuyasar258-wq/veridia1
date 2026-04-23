#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "content" / "site_graph.json"


def load_graph() -> dict:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def canonical(base_url: str, url: str) -> str:
    if url == "/":
        return base_url
    return f"{base_url}{url}"


def lookup_by_slug(items: list[dict], slug: str) -> dict:
    for item in items:
        if item["slug"] == slug:
            return item
    raise KeyError(slug)


def posts_for_service(graph: dict, service_slug: str) -> list[dict]:
    return [post for post in graph["blog_posts"] if post["service_slug"] == service_slug]


def posts_for_hub(graph: dict, hub_slug: str) -> list[dict]:
    service_slugs = {service["slug"] for service in graph["services"] if service["parent"] == hub_slug}
    return [post for post in graph["blog_posts"] if post["service_slug"] in service_slugs]


def render_mobile_menu() -> str:
    return """<div class="mobile-menu" id="mobileMenu" aria-hidden="true">
  <button class="menu-close" type="button" data-mobile-close aria-label="Menüyü kapat">✕</button>
  <a href="/blog.html">Blog</a>
  <a href="/seo/">SEO</a>
  <a href="/reklam/">Reklam</a>
  <a href="/yazilim/">Yazılım</a>
  <a href="/#quote" data-mobile-close>Hızlı Teklif</a>
  <a href="/#contact" data-mobile-close>İletişim</a>
</div>"""


def render_nav(active_label: str) -> str:
    links = [
        ("/blog.html", "Blog"),
        ("/seo/", "SEO"),
        ("/reklam/", "Reklam"),
        ("/yazilim/", "Yazılım"),
        ("/#quote", "Hızlı Teklif"),
        ("/#contact", "İletişim"),
    ]
    nav_links = "\n".join(
        f'    <li><a href="{href}"{" aria-current=\"page\"" if label == active_label else ""}>{label}</a></li>'
        for href, label in links
    )
    return f"""<nav id="navbar">
  <a href="/" class="nav-logo">Veridia</a>
  <ul class="nav-links">
{nav_links}
  </ul>
  <button class="hamburger" id="hamburger" type="button" data-mobile-toggle aria-label="Menü" aria-controls="mobileMenu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
</nav>"""


def render_breadcrumb(items: list[tuple[str, str | None]]) -> str:
    parts: list[str] = ['<nav class="breadcrumb" aria-label="Breadcrumb">']
    for index, (label, href) in enumerate(items):
        if href:
            parts.append(f'  <a href="{href}">{escape(label)}</a>')
        else:
            parts.append(f'  <span aria-current="page">{escape(label)}</span>')
        if index < len(items) - 1:
            parts.append('  <span aria-hidden="true">→</span>')
    parts.append("</nav>")
    return "\n".join(parts)


def breadcrumb_json_ld(base_url: str, items: list[tuple[str, str | None]]) -> str:
    elements = []
    for position, (label, href) in enumerate(items, start=1):
        if href is None:
            continue
        elements.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": label,
                "item": canonical(base_url, href),
            }
        )
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": elements,
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def render_service_cards(services: list[dict]) -> str:
    cards = []
    for service in services:
        cards.append(
            f"""<article class="surface-card">
  <p class="surface-card-kicker">{escape(service["eyebrow"])}</p>
  <h2><a href="{service["url"]}">{escape(service["title"])}</a></h2>
  <p>{escape(service["description"])}</p>
  <a href="{service["url"]}" class="surface-link">{escape(service["title"])} sayfasına git</a>
</article>"""
        )
    return "\n".join(cards)


def render_highlights(highlights: list[dict]) -> str:
    return "\n".join(
        f"""<article class="signal-card">
  <h2>{escape(item["title"])}</h2>
  <p>{escape(item["copy"])}</p>
</article>"""
        for item in highlights
    )


def render_post_cards(posts: list[dict], graph: dict) -> str:
    if not posts:
        return '<p class="empty-state">Bu yüzey için henüz yayımlanmış editoryal rehber yok. Yeni yazılar bu cluster içinde yer alacak.</p>'

    services = {service["slug"]: service for service in graph["services"]}
    cards = []
    for post in posts:
        service = services[post["service_slug"]]
        cards.append(
            f"""<article class="resource-card">
  <p class="resource-meta">{escape(service["blog_label"])} · {escape(post["date_label"])}</p>
  <h2><a href="{post["url"]}">{escape(post["title"])}</a></h2>
  <p>{escape(post["summary"])}</p>
  <div class="resource-actions">
    <a href="{post["url"]}" class="surface-link">Yazıyı oku</a>
    <a href="{service["url"]}" class="surface-link surface-link--muted">{escape(service["title"])}</a>
  </div>
</article>"""
        )
    return "\n".join(cards)


def render_route_map(label: str, links: list[tuple[str, str]]) -> str:
    items = "\n".join(
        f"""<li><a href="{href}">{escape(text)}</a></li>"""
        for href, text in links
    )
    return f"""<section class="route-map" aria-label="{escape(label)}">
  <h2>Bu sayfadan nereye gidilir?</h2>
  <ul class="route-list">
{items}
  </ul>
</section>"""


def render_page(entity: dict, graph: dict, kind: str) -> str:
    site = graph["site"]
    base_url = site["base_url"]
    canonical_url = canonical(base_url, entity["url"])
    image_url = canonical(base_url, site["default_image"])

    if kind == "hub":
        child_services = [lookup_by_slug(graph["services"], slug) for slug in entity["children"]]
        related_posts = [lookup_by_slug(graph["blog_posts"], slug) for slug in entity["featured_posts"]]
        breadcrumbs = [("Ana Sayfa", "/"), (entity["title"], entity["url"])]
        route_links = [(service["url"], service["title"]) for service in child_services]
        route_links.extend(
            [
                ("/blog.html", "Editoryal rehberlerin tamamını gör"),
                (entity["secondary_cta_href"], entity["secondary_cta_label"]),
            ]
        )
        primary_content = f"""<section class="surface-grid" aria-label="{escape(entity["title"])} alt yüzeyleri">
{render_service_cards(child_services)}
</section>

<section class="resources-grid" aria-label="İlgili rehberler">
  <div class="section-heading">
    <p class="section-label">İlgili Yazılar</p>
    <h2>Bu siloyu besleyen editoryal içerikler</h2>
  </div>
{render_post_cards(related_posts, graph)}
</section>"""
    else:
        parent = lookup_by_slug(graph["hubs"], entity["parent"])
        related_services = [lookup_by_slug(graph["services"], slug) for slug in entity.get("related_services", [])]
        related_posts = posts_for_service(graph, entity["slug"])
        breadcrumbs = [
            ("Ana Sayfa", "/"),
            (parent["title"], parent["url"]),
            (entity["title"], entity["url"]),
        ]
        route_links = [
            (parent["url"], parent["title"]),
            (entity["secondary_cta_href"], entity["secondary_cta_label"]),
            ("/blog.html", "Tüm yazılar"),
        ]
        for sibling in related_services:
            route_links.insert(1, (sibling["url"], sibling["title"]))
        primary_content = f"""<section class="signal-grid" aria-label="{escape(entity["title"])} odakları">
{render_highlights(entity["highlights"])}
</section>

<section class="surface-grid" aria-label="Yakın hizmet yüzeyleri">
{render_service_cards(related_services) if related_services else '<p class="empty-state">Bu hizmet yüzeyi kendi cluster bağlantılarıyla çalışır.</p>'}
</section>

<section class="resources-grid" aria-label="İlgili rehberler">
  <div class="section-heading">
    <p class="section-label">İlgili Yazılar</p>
    <h2>Bu hizmete otorite taşıyan içerikler</h2>
  </div>
{render_post_cards(related_posts, graph)}
</section>"""

    breadcrumb_markup = render_breadcrumb(breadcrumbs)
    breadcrumb_schema = breadcrumb_json_ld(base_url, breadcrumbs)
    active_label = "SEO" if entity["url"].startswith("/seo/") else "Reklam" if entity["url"].startswith("/reklam/") else "Yazılım"
    legacy_href = entity.get("legacy_href", entity["secondary_cta_href"])
    legacy_label = entity.get("legacy_label", entity["secondary_cta_label"])

    page_schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "CollectionPage",
                    "name": entity["title"],
                    "description": entity["description"],
                    "url": canonical_url,
                    "inLanguage": "tr",
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(entity["meta_title"])}</title>
  <meta name="description" content="{escape(entity["description"])}">
  <meta name="theme-color" content="#0a0a0f">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{escape(entity["meta_title"])}">
  <meta property="og:description" content="{escape(entity["description"])}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:site_name" content="{escape(site["name"])}">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:image" content="{image_url}">
  <meta property="og:image:alt" content="{escape(entity["title"])} için Veridia kapak görseli">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(entity["meta_title"])}">
  <meta name="twitter:description" content="{escape(entity["description"])}">
  <meta name="twitter:image" content="{image_url}">
  <link rel="stylesheet" href="/assets/fonts.css">
  <link rel="stylesheet" href="/assets/page-shell.css">
  <link rel="stylesheet" href="/assets/silo-pages.css">
  <script type="application/ld+json">
{page_schema}
  </script>
  <script type="application/ld+json">
{breadcrumb_schema}
  </script>
  <script defer src="/assets/config.js"></script>
  <script defer src="/assets/analytics.js"></script>
  <script defer src="/assets/page-shell.js"></script>
</head>
<body data-custom-cursor="true">

<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<div class="scroll-bar" id="scrollBar"></div>

{render_mobile_menu()}
{render_nav(active_label)}

<main class="silo-shell">
  {breadcrumb_markup}
  <header class="silo-hero">
    <p class="section-label">{escape(entity["eyebrow"])}</p>
    <h1>{escape(entity["hero_title"])}</h1>
    <p class="silo-copy">{escape(entity["hero_body"])}</p>
    <div class="silo-actions">
      <a href="{entity["primary_cta_href"]}" class="btn-gold">{escape(entity["primary_cta_label"])}</a>
      <a href="{entity["secondary_cta_href"]}" class="btn-outline">{escape(entity["secondary_cta_label"])}</a>
    </div>
  </header>

  {primary_content}

  <section class="bridge-panel" aria-label="Kontekst">
    <p class="section-label">Bağlantı Mantığı</p>
    <h2>Bu yüzey kendi başına değil, ağın içinde çalışır.</h2>
    <p>{escape(entity["description"])} Bu nedenle hizmet sayfaları yalnızca menüden değil; blog girişlerinde, ilgili içerik bloklarında ve vaka akışlarında da bağlamsal olarak birbirine bağlanır.</p>
    <div class="bridge-actions">
      <a href="{entity["primary_cta_href"]}" class="surface-link">{escape(entity["primary_cta_label"])}</a>
      <a href="{legacy_href}" class="surface-link surface-link--muted">{escape(legacy_label)}</a>
    </div>
  </section>

  {render_route_map("Yol Haritası", route_links)}
</main>

</body>
</html>
"""


def lastmod_for(path: Path) -> str:
    timestamp = path.stat().st_mtime
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def build_sitemap(graph: dict) -> str:
    base_url = graph["site"]["base_url"]
    items: list[dict] = []
    items.extend(graph["static_pages"])
    items.extend(graph["hubs"])
    items.extend(graph["services"])
    items.extend(graph["blog_posts"])

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for item in items:
        file_path = ROOT / item["file"]
        if not file_path.exists():
            continue
        lines.append("  <url>")
        lines.append(f"    <loc>{canonical(base_url, item['url'])}</loc>")
        lines.append(f"    <lastmod>{lastmod_for(file_path)}</lastmod>")
        lines.append(f"    <changefreq>{item.get('changefreq', 'monthly')}</changefreq>")
        lines.append(f"    <priority>{item.get('priority', '0.6')}</priority>")
        for image in item.get("images", []):
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{canonical(base_url, image['path'])}</image:loc>")
            lines.append(f"      <image:title>{escape(image['title'])}</image:title>")
            lines.append("    </image:image>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> None:
    graph = load_graph()
    for hub in graph["hubs"]:
        output_path = ROOT / hub["file"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_page(hub, graph, "hub"), encoding="utf-8")

    for service in graph["services"]:
        output_path = ROOT / service["file"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_page(service, graph, "service"), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(build_sitemap(graph), encoding="utf-8")


if __name__ == "__main__":
    main()
