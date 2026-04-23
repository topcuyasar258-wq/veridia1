#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GRAPH_PATH = ROOT / "content" / "site_graph.json"
BUILD_SCRIPT = ROOT / "scripts" / "build_site_surfaces.py"

MONTH_MAP = {
    "January": "Ocak",
    "February": "Şubat",
    "March": "Mart",
    "April": "Nisan",
    "May": "Mayıs",
    "June": "Haziran",
    "July": "Temmuz",
    "August": "Ağustos",
    "September": "Eylül",
    "October": "Ekim",
    "November": "Kasım",
    "December": "Aralık",
}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")
DEFAULT_SITE_URL = (os.environ.get("SITE_URL", "https://veridiareklam.com.tr").strip() or "https://veridiareklam.com.tr").rstrip("/")


def format_turkish_date(dt: datetime) -> str:
    date_str = dt.strftime("%d %B %Y")
    for english, turkish in MONTH_MAP.items():
        date_str = date_str.replace(english, turkish)
    return date_str


def escape_text(value: str) -> str:
    return html.escape(value, quote=True)


def load_graph() -> dict:
    if GRAPH_PATH.exists():
        return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    return {
        "site": {
            "base_url": DEFAULT_SITE_URL,
            "default_image": "/assets/veridia-social-cover.png",
        },
        "hubs": [],
        "services": [],
        "blog_posts": [],
    }


def save_graph(graph: dict) -> None:
    GRAPH_PATH.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical(site_url: str, url: str) -> str:
    return site_url if url == "/" else f"{site_url}{url}"


def get_site_url(graph: dict) -> str:
    default_url = graph["site"]["base_url"].rstrip("/")
    return (os.environ.get("SITE_URL", DEFAULT_SITE_URL or default_url).strip() or default_url).rstrip("/")


def lookup_by_slug(items: list[dict], slug: str) -> dict:
    for item in items:
        if item["slug"] == slug:
            return item
    raise KeyError(slug)


def list_services(graph: dict) -> list[dict]:
    hubs = {hub["slug"]: hub for hub in graph["hubs"]}
    services = []
    for service in graph["services"]:
        hub = hubs[service["parent"]]
        services.append(
            {
                "slug": service["slug"],
                "title": service["title"],
                "hub_title": hub["title"],
                "url": service["url"],
            }
        )
    return services


def build_breadcrumbs(hub: dict | None, service: dict | None, title: str, site_url: str, article_slug: str) -> tuple[str, str]:
    items = [
        {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": canonical(site_url, "/")},
    ]
    visual_parts = [
        '<nav class="breadcrumb" aria-label="Breadcrumb">',
        '  <a href="/">Ana Sayfa</a>',
    ]
    position = 2

    if hub:
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": hub["title"],
                "item": canonical(site_url, hub["url"]),
            }
        )
        visual_parts.extend(
            [
                '  <span aria-hidden="true">→</span>',
                f'  <a href="{hub["url"]}">{escape_text(hub["title"])}</a>',
            ]
        )
        position += 1

    if service:
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": service["title"],
                "item": canonical(site_url, service["url"]),
            }
        )
        visual_parts.extend(
            [
                '  <span aria-hidden="true">→</span>',
                f'  <a href="{service["url"]}">{escape_text(service["title"])}</a>',
            ]
        )
        position += 1
    else:
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": "Blog",
                "item": canonical(site_url, "/blog.html"),
            }
        )
        visual_parts.extend(
            [
                '  <span aria-hidden="true">→</span>',
                '  <a href="/blog.html">Blog</a>',
            ]
        )
        position += 1

    items.append(
        {
            "@type": "ListItem",
            "position": position,
            "name": title,
            "item": canonical(site_url, f"/blog/{article_slug}.html"),
        }
    )
    visual_parts.extend(
        [
            '  <span aria-hidden="true">→</span>',
            f'  <span aria-current="page">{escape_text(title)}</span>',
            "</nav>",
        ]
    )
    return json.dumps({"@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False, indent=2), "\n".join(
        visual_parts
    )


def slugify(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_related_links(graph: dict, service: dict | None, current_slug: str) -> str:
    if not service:
        return """<div class="related-panel">
  <h2>İlgili Sayfalar</h2>
  <div class="related-links">
    <a href="/blog.html" class="secondary-link">Tüm Yazılar</a>
  </div>
</div>"""

    related_posts = [
        post for post in graph["blog_posts"] if post["service_slug"] == service["slug"] and post["slug"] != current_slug
    ]

    links = [
        f'<a href="{service["url"]}" class="primary-link">{escape_text(service["title"])}</a>',
    ]
    for post in related_posts[:2]:
        links.append(f'<a href="{post["url"]}" class="secondary-link">{escape_text(post["title"])}</a>')

    return f"""<div class="related-panel">
  <h2>İlginizi Çekebilir</h2>
  <p>Bu yazı ile aynı hizmet cluster'ında çalışan sayfalara aşağıdan geçebilirsiniz.</p>
  <div class="related-links">
    {' '.join(links)}
  </div>
</div>"""


def build_article_template(
    title: str,
    summary: str,
    url_name: str,
    date_iso: str,
    date_label: str,
    *,
    graph: dict | None = None,
    service: dict | None = None,
    hub: dict | None = None,
    author: str = "Veridia Strateji Ekibi",
    reading_time: str = "6 dk okuma",
) -> str:
    graph = graph or load_graph()
    site_url = get_site_url(graph)
    article_url = f"{site_url}/blog/{url_name}.html"
    safe_title = escape_text(title)
    safe_summary = escape_text(summary)
    safe_author = escape_text(author)
    default_image = canonical(site_url, graph["site"]["default_image"])

    if service and hub:
        intro = (
            f"Bu rehber, <a href=\"{service['url']}\">{escape_text(service['title'])}</a> yüzeyinde en sık karşılaştığımız "
            f"darboğazlardan hareketle hazırlanmıştır. {safe_summary}"
        )
    else:
        intro = safe_summary

    breadcrumb_schema, breadcrumb_html = build_breadcrumbs(hub, service, title, site_url, url_name)
    related_links_html = build_related_links(graph, service, url_name)
    article_section = escape_text(service["blog_label"] if service else "Blog")

    article_schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Article",
                    "headline": title,
                    "description": summary,
                    "image": default_image,
                    "datePublished": date_iso,
                    "dateModified": date_iso,
                    "inLanguage": "tr",
                    "mainEntityOfPage": article_url,
                    "author": {
                        "@type": "Person" if author != "Veridia Strateji Ekibi" else "Organization",
                        "name": author,
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": "Veridia Ajans",
                        "logo": {
                            "@type": "ImageObject",
                            "url": f"{site_url}/assets/veridia-icon.png",
                        },
                    },
                },
                json.loads(breadcrumb_schema),
            ],
        },
        ensure_ascii=False,
        indent=2,
    )

    primary_cta_label = escape_text(service["blog_cta_label"] if service else "Blog'a Dön")
    primary_cta_href = service["url"] if service else "/blog.html"
    secondary_cta_label = escape_text(hub["title"] if hub else "Tüm Yazılar")
    secondary_cta_href = hub["url"] if hub else "/blog.html"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} | Veridia Blog</title>
    <meta name="description" content="{safe_summary}">
    <meta name="theme-color" content="#0a0a0f">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <meta name="author" content="{safe_author}">
    <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
    <link rel="canonical" href="{article_url}">
    <meta property="og:title" content="{safe_title} | Veridia Blog">
    <meta property="og:description" content="{safe_summary}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{article_url}">
    <meta property="og:site_name" content="Veridia">
    <meta property="og:locale" content="tr_TR">
    <meta property="og:image" content="{default_image}">
    <meta property="og:image:alt" content="{safe_title} için Veridia kapak görseli">
    <meta property="article:published_time" content="{date_iso}">
    <meta property="article:modified_time" content="{date_iso}">
    <meta property="article:author" content="{safe_author}">
    <meta property="article:section" content="{article_section}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title} | Veridia Blog">
    <meta name="twitter:description" content="{safe_summary}">
    <meta name="twitter:image" content="{default_image}">
    <script type="application/ld+json">
{article_schema}
    </script>
    <link rel="stylesheet" href="/assets/fonts.css">
    <link rel="stylesheet" href="/assets/page-shell.css">
    <style>
        .article-shell {{
            width: min(1120px, calc(100% - 3rem));
            margin: 0 auto;
            padding: 8.5rem 0 6rem;
            display: grid;
            gap: 1.5rem;
        }}
        .breadcrumb {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            align-items: center;
            color: rgba(231, 226, 213, 0.7);
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .breadcrumb a {{
            color: rgba(231, 226, 213, 0.78);
            text-decoration: none;
        }}
        .article-content {{
            border: 1px solid rgba(201, 168, 76, 0.12);
            border-radius: 30px;
            background:
              radial-gradient(circle at 12% 18%, rgba(201, 168, 76, 0.14), transparent 34%),
              linear-gradient(180deg, rgba(16, 19, 24, 0.96), rgba(13, 16, 20, 0.98));
            padding: clamp(1.5rem, 3vw, 2.7rem);
        }}
        .article-content h1 {{
            margin: 0.35rem 0 1rem;
            font-family: 'Cormorant Garamond', serif;
            font-size: clamp(2.9rem, 7vw, 4.8rem);
            line-height: 0.98;
            color: var(--off-white);
            max-width: 12ch;
        }}
        .article-intro,
        .article-content p,
        .article-content li {{
            color: rgba(231, 226, 213, 0.76);
            line-height: 1.9;
            font-size: 1.03rem;
        }}
        .meta-info {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem 1.2rem;
            padding-bottom: 1.25rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(201, 168, 76, 0.12);
            color: rgba(201, 168, 76, 0.9);
            font-size: 0.74rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }}
        .article-content h2 {{
            margin: 2.2rem 0 0.8rem;
            font-family: 'Cormorant Garamond', serif;
            font-size: 2rem;
            color: var(--off-white);
        }}
        .cta-panel,
        .related-panel,
        .callout {{
            margin-top: 1.6rem;
            padding: 1.25rem;
            border-radius: 24px;
            border: 1px solid rgba(201, 168, 76, 0.12);
            background: rgba(17, 21, 26, 0.84);
        }}
        .cta-actions,
        .related-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem;
            margin-top: 1rem;
        }}
        .primary-link,
        .secondary-link {{
            text-decoration: none;
            font-size: 0.94rem;
        }}
        .primary-link {{
            color: var(--gold);
        }}
        .secondary-link {{
            color: rgba(231, 226, 213, 0.78);
        }}
        @media (max-width: 768px) {{
            .article-shell {{
                width: min(100% - 1.5rem, 1120px);
                padding-top: 6.8rem;
            }}
            .article-content {{
                border-radius: 22px;
            }}
            .article-content h1 {{
                max-width: 100%;
                font-size: clamp(2.4rem, 11vw, 3.5rem);
            }}
            .meta-info {{
                flex-direction: column;
                gap: 0.4rem;
            }}
        }}
    </style>
    <script defer src="/assets/config.js"></script>
    <script defer src="/assets/analytics.js"></script>
    <script defer src="/assets/page-shell.js"></script>
</head>
<body data-custom-cursor="true">

<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<div class="scroll-bar" id="scrollBar"></div>

<div class="mobile-menu" id="mobileMenu" aria-hidden="true">
  <button class="menu-close" type="button" data-mobile-close aria-label="Menüyü kapat">✕</button>
  <a href="/blog.html">Blog</a>
  <a href="/seo/">SEO</a>
  <a href="/reklam/">Reklam</a>
  <a href="/yazilim/">Yazılım</a>
  <a href="/#quote" data-mobile-close>Hızlı Teklif</a>
  <a href="/#contact" data-mobile-close>İletişim</a>
</div>

<nav id="navbar">
  <a href="/" class="nav-logo">Veridia</a>
  <ul class="nav-links">
    <li><a href="/blog.html" aria-current="page">Blog</a></li>
    <li><a href="/seo/">SEO</a></li>
    <li><a href="/reklam/">Reklam</a></li>
    <li><a href="/yazilim/">Yazılım</a></li>
    <li><a href="/#quote">Hızlı Teklif</a></li>
    <li><a href="/#contact">İletişim</a></li>
  </ul>
  <button class="hamburger" id="hamburger" type="button" data-mobile-toggle aria-label="Menü" aria-controls="mobileMenu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
</nav>

<main class="article-shell">
  {breadcrumb_html}
  <article class="article-content">
    <p class="section-label">Editoryal Rehber</p>
    <h1>{safe_title}</h1>
    <p class="article-intro">{intro}</p>

    <div class="meta-info">
      <span>Yazar: {safe_author}</span>
      <time datetime="{date_iso}">{date_label}</time>
      <span>{escape_text(reading_time)}</span>
      <span>{article_section}</span>
    </div>

    <h2>Giriş çerçevesi</h2>
    <p>Bu bölümde problemi tek cümlede tanımlayın, sonra okuyucunun neden bunu şimdi çözmesi gerektiğini netleştirin. İlk 150 kelime içinde mümkün olduğunca birincil hizmet sayfasını doğal bağlam içinde anın.</p>

    <h2>Uygulama katmanları</h2>
    <p>Konuyu 3 ila 5 alt başlıkla ilerletin. Her bölümün sonunda küçük bir karar veya aksiyon çıkarımı bırakın ki kullanıcı sadece okuyup çıkmasın, bir sonraki sayfaya da geçsin.</p>

    <div class="callout">
      Yayın kontrolü: intro bölümünde birincil hizmet linki var mı, anchor text hedef sayfayı açıkça tarif ediyor mu, bitişte yalnızca aynı cluster sayfalarına ve ilgili hizmet sayfasına yönleniyor mu?
    </div>

    <div class="cta-panel">
      <h2>Bir sonraki adım</h2>
      <p>Bu rehberin anlattığı konuyu doğrudan hizmet yüzeyine bağlamak istiyorsanız aşağıdaki bağlantıyla devam edin.</p>
      <div class="cta-actions">
        <a href="{primary_cta_href}" class="primary-link">{primary_cta_label}</a>
        <a href="{secondary_cta_href}" class="secondary-link">{secondary_cta_label}</a>
      </div>
    </div>

    {related_links_html}
  </article>
</main>

</body>
</html>
"""


def insert_blog_card(
    blog_path: Path,
    *,
    title: str,
    summary: str,
    url_name: str,
    date_iso: str,
    date_label: str,
    author: str,
    reading_time: str,
    service: dict | None,
) -> None:
    if not blog_path.exists():
        return

    content = blog_path.read_text(encoding="utf-8")
    category = service["blog_category"] if service else "all"
    label = service["blog_label"] if service else "Yeni Yazı"
    secondary_href = service["url"] if service else "/blog.html"
    secondary_label = service["blog_cta_label"] if service else "Tüm Yazılar"

    safe_title = escape_text(title)
    safe_summary = escape_text(summary)
    safe_author = escape_text(author)

    card_html = f"""
        <article class="blog-card" data-category="{category}">
            <div class="blog-meta">
                <span>{escape_text(label)}</span>
                <time datetime="{date_iso}">{date_label}</time>
                <span>{escape_text(reading_time)}</span>
                <span>Yazar: {safe_author}</span>
            </div>
            <h2><a href="/blog/{url_name}.html">{safe_title}</a></h2>
            <p>{safe_summary}</p>
            <div class="blog-card-footer">
                <a href="/blog/{url_name}.html" class="read-more">Makaleyi Oku</a>
                <a href="{secondary_href}" class="secondary-link">{escape_text(secondary_label)}</a>
            </div>
        </article>
"""
    marker = "        <!-- /BLOG_CARDS -->"
    if marker in content:
        content = content.replace(marker, f"{card_html}{marker}")
        blog_path.write_text(content, encoding="utf-8")


def update_blog_json_ld(blog_path: Path, graph: dict) -> None:
    if not blog_path.exists():
        return

    site_url = get_site_url(graph)
    content = blog_path.read_text(encoding="utf-8")
    posts = sorted(graph["blog_posts"], key=lambda item: item["published_at"], reverse=True)
    entries = []
    for post in posts:
        entry = {
            "@type": "BlogPosting",
            "headline": post["title"],
            "url": f"{site_url}{post['url']}",
            "datePublished": post["published_at"],
            "dateModified": post["modified_at"],
        }
        entries.append(entry)

    rendered_entries = json.dumps(entries, ensure_ascii=False, indent=12)
    replacement = f'"blogPost": {rendered_entries}'
    pattern = re.compile(r'"blogPost":\s*\[(?:.|\n)*?\n\s*\]\n\s*\}\n\s*,', re.MULTILINE)
    content, count = pattern.subn(f'{replacement}\n        }},', content, count=1)
    if count:
        blog_path.write_text(content, encoding="utf-8")


def append_post_to_graph(
    graph: dict,
    *,
    slug: str,
    title: str,
    summary: str,
    description: str,
    published_at: str,
    modified_at: str,
    date_label: str,
    reading_time: str,
    author: str,
    service_slug: str | None,
) -> None:
    if any(post["slug"] == slug for post in graph["blog_posts"]):
        raise ValueError("Aynı slug ile kayıtlı bir blog yazısı zaten var.")

    graph["blog_posts"].append(
        {
            "slug": slug,
            "url": f"/blog/{slug}.html",
            "file": f"blog/{slug}.html",
            "title": title,
            "summary": summary,
            "description": description,
            "published_at": published_at,
            "modified_at": modified_at,
            "date_label": date_label,
            "reading_time": reading_time,
            "author": author,
            "service_slug": service_slug,
        }
    )


def rebuild_site_surfaces() -> None:
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=str(ROOT), check=True)


def main() -> None:
    print("=" * 58)
    print(" Veridia Ajans | Silo Mimarili Blog Ekleme Aracı")
    print("=" * 58)

    graph = load_graph()
    services = list_services(graph)

    title = input("1. Makale başlığı: ").strip()
    if not title:
        print("Hata: Başlık boş olamaz.")
        sys.exit(1)

    summary = input("2. Kısa özet / meta description: ").strip()
    if not summary:
        print("Hata: Özet boş olamaz.")
        sys.exit(1)

    default_slug = slugify(title)
    url_name = input(f"3. URL adı [{default_slug}]: ").strip() or default_slug
    if not re.fullmatch(r"[a-z0-9-]+", url_name):
        print("Hata: URL adı sadece küçük harf, rakam ve tire içermelidir.")
        sys.exit(1)

    print("\n4. Bu yazının bağlanacağı birincil hizmet yüzeyi:")
    for service in services:
        print(f"   - {service['slug']}: {service['title']} ({service['hub_title']})")
    service_slug = input("   Servis slug'ı: ").strip()

    if not service_slug:
        print("Hata: Her yazı bir hizmet yüzeyine bağlanmalı. Servis slug'ı boş bırakılamaz.")
        sys.exit(1)

    try:
        service = lookup_by_slug(graph["services"], service_slug)
        hub = lookup_by_slug(graph["hubs"], service["parent"])
    except KeyError:
        print("Hata: Tanımsız servis slug'ı girdiniz.")
        sys.exit(1)

    author = input("5. Yazar [Veridia Strateji Ekibi]: ").strip() or "Veridia Strateji Ekibi"
    reading_time = input("6. Okuma süresi [6 dk okuma]: ").strip() or "6 dk okuma"

    now = datetime.now()
    date_label = format_turkish_date(now)
    date_iso = now.strftime("%Y-%m-%dT00:00:00+03:00")
    file_path = ROOT / "blog" / f"{url_name}.html"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        print("Hata: Bu slug ile bir dosya zaten var.")
        sys.exit(1)

    html_template = build_article_template(
        title,
        summary,
        url_name,
        date_iso,
        date_label,
        graph=graph,
        service=service,
        hub=hub,
        author=author,
        reading_time=reading_time,
    )
    file_path.write_text(html_template, encoding="utf-8")

    append_post_to_graph(
        graph,
        slug=url_name,
        title=title,
        summary=summary,
        description=summary,
        published_at=date_iso,
        modified_at=date_iso,
        date_label=date_label,
        reading_time=reading_time,
        author=author,
        service_slug=service["slug"],
    )
    save_graph(graph)

    insert_blog_card(
        ROOT / "blog.html",
        title=title,
        summary=summary,
        url_name=url_name,
        date_iso=date_iso,
        date_label=date_label,
        author=author,
        reading_time=reading_time,
        service=service,
    )
    update_blog_json_ld(ROOT / "blog.html", graph)

    rebuild_site_surfaces()

    print(f"\n✅ blog/{url_name}.html oluşturuldu")
    print("✅ content/site_graph.json güncellendi")
    print("✅ blog.html kart listesi güncellendi")
    print("✅ blog.html JSON-LD listesi güncellendi")
    print("✅ hub sayfaları ve sitemap yeniden üretildi")
    print("\nNot: Yazı taslağı bilinçli olarak iskelet halinde üretilir; gerçek içeriği gönderdiğinizde aynı mimariyle birlikte doldurabiliriz.")


if __name__ == "__main__":
    main()
