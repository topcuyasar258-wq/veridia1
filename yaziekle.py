#!/usr/bin/env python3
import html
import os
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent


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

SITE_URL = (os.environ.get("SITE_URL", "https://veridia.com.tr").strip() or "https://veridia.com.tr").rstrip("/")
OG_IMAGE_URL = f"{SITE_URL}/assets/veridia-social-cover.png"
BRAND_LOGO_URL = f"{SITE_URL}/assets/veridia-icon.png"

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


def format_turkish_date(dt: datetime) -> str:
    date_str = dt.strftime("%d %B %Y")
    for english, turkish in MONTH_MAP.items():
        date_str = date_str.replace(english, turkish)
    return date_str


def escape_text(value: str) -> str:
    return html.escape(value, quote=True)


def build_article_template(title: str, summary: str, url_name: str, date_iso: str, date_label: str) -> str:
    article_url = f"{SITE_URL}/blog/{url_name}.html"
    safe_title = escape_text(title)
    safe_summary = escape_text(summary)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} | Veridia Blog</title>
    <meta name="description" content="{safe_summary}">
    <meta name="theme-color" content="#0f1714">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <meta name="author" content="Veridia Strateji Ekibi">
    <link rel="icon" href="{SITE_URL}/assets/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="{SITE_URL}/assets/apple-touch-icon.png">
    <link rel="canonical" href="{article_url}">
    <meta property="og:title" content="{safe_title}">
    <meta property="og:description" content="{safe_summary}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{article_url}">
    <meta property="og:site_name" content="Veridia">
    <meta property="og:image" content="{OG_IMAGE_URL}">
    <meta property="og:image:alt" content="{safe_title} için Veridia kapak görseli">
    <meta property="article:published_time" content="{date_iso}">
    <meta property="article:modified_time" content="{date_iso}">
    <meta property="article:author" content="Veridia Strateji Ekibi">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{safe_summary}">
    <meta name="twitter:image" content="{OG_IMAGE_URL}">
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@graph": [
        {{
          "@type": "BlogPosting",
          "headline": "{safe_title}",
          "description": "{safe_summary}",
          "image": "{OG_IMAGE_URL}",
          "datePublished": "{date_iso}",
          "dateModified": "{date_iso}",
          "mainEntityOfPage": "{article_url}",
          "author": {{
            "@type": "Organization",
            "name": "Veridia Ajans"
          }},
          "publisher": {{
            "@type": "Organization",
            "name": "Veridia Ajans",
            "logo": {{
              "@type": "ImageObject",
              "url": "{BRAND_LOGO_URL}"
            }}
          }}
        }},
        {{
          "@type": "BreadcrumbList",
          "itemListElement": [
            {{
              "@type": "ListItem",
              "position": 1,
              "name": "Ana Sayfa",
              "item": "{SITE_URL}/"
            }},
            {{
              "@type": "ListItem",
              "position": 2,
              "name": "Blog",
              "item": "{SITE_URL}/blog.html"
            }},
            {{
              "@type": "ListItem",
              "position": 3,
              "name": "{safe_title}",
              "item": "{article_url}"
            }}
          ]
        }}
      ]
    }}
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Cormorant+Garamond:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/shared.css">
    <style>
        body {{ padding-top: 8rem; }}
        .article-container {{
            max-width: 860px;
            margin: 0 auto;
            padding: 0 2rem 6rem;
            position: relative;
            z-index: 2;
        }}
        .article-container::before {{
            content: '';
            position: absolute;
            left: -10vw;
            right: -10vw;
            top: 0;
            bottom: 0;
            background: radial-gradient(ellipse 40% 60% at 20% 10%, rgba(26,92,58,0.08) 0%, transparent 60%);
            z-index: -1;
            pointer-events: none;
        }}
        .eyebrow-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            color: rgba(201,168,76,0.7);
            font-size: 0.68rem;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            text-decoration: none;
            margin-bottom: 1.2rem;
        }}
        h1 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: clamp(2.7rem, 6vw, 4.2rem);
            margin-bottom: 1.2rem;
            line-height: 1.06;
            color: var(--off-white);
            max-width: 13ch;
        }}
        .article-intro,
        p,
        li {{
            color: var(--text-muted);
            font-size: 1.03rem;
            line-height: 1.9;
        }}
        .article-intro {{ margin-bottom: 1.8rem; }}
        .meta-info {{
            font-size: 0.72rem;
            color: var(--gold);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid rgba(201,168,76,0.15);
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem 1.25rem;
        }}
        h2 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2rem;
            margin-top: 3.4rem;
            margin-bottom: 1rem;
            color: var(--off-white);
            border-left: 2px solid var(--gold);
            padding-left: 1rem;
        }}
        .callout {{
            margin-top: 2rem;
            padding: 1.4rem;
            border: 1px solid rgba(201,168,76,0.14);
            border-left: 2px solid var(--gold);
            background: rgba(201,168,76,0.05);
        }}
        @media (max-width: 768px) {{
            body {{ padding-top: 6rem; }}
            .article-container {{ padding-left: 1.5rem; padding-right: 1.5rem; }}
            .meta-info {{ flex-direction: column; gap: 0.4rem; }}
        }}
    </style>
</head>
<body>

<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<div class="scroll-bar" id="scrollBar"></div>

<nav id="navbar">
  <a href="/" class="nav-logo">Veridia</a>
  <a href="/blog.html" style="color:var(--off-white); font-size:0.8rem; text-decoration:none; text-transform:uppercase; letter-spacing:0.1em; transition:color 0.2s;">← Blog'a Dön</a>
</nav>

<main class="article-container">
    <article>
        <a class="eyebrow-link" href="/blog.html">← Blog'a Dön</a>
        <h1>{safe_title}</h1>
        <p class="article-intro">{safe_summary}</p>

        <div class="meta-info">
            <span>Yazar: Veridia Strateji Ekibi</span>
            <time datetime="{date_iso}">{date_label}</time>
            <span>6 dk okuma</span>
        </div>

        <h2>Ana başlık 1</h2>
        <p>Buraya makalenin ilk ana bölümünü ekleyin. Sorunu, okuyucunun ihtiyacını ve vermek istediğiniz çerçeveyi ilk iki paragrafta netleştirmeye çalışın.</p>

        <h2>Ana başlık 2</h2>
        <p>Bu şablon yeni yazılar için canonical, sosyal meta etiketleri, JSON-LD ve breadcrumb yapısını otomatik olarak hazırlar. İçeriği yayına almadan önce gerçek paragraflarla doldurmanız yeterlidir.</p>

        <div class="callout">
            Yayın öncesi küçük kontrol: başlık ve description birincil arama niyetiyle uyumlu mu, yazı içinde en az bir servis veya analiz akışına link var mı, blog ana sayfasındaki özet gerçekten bu yazıyı temsil ediyor mu?
        </div>
    </article>
</main>
<script>
  window.addEventListener('scroll', () => {{
    const wScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    if (document.getElementById('scrollBar')) {{
      document.getElementById('scrollBar').style.width = (wScroll / height) * 100 + '%';
    }}
  }});
  const cursor = document.getElementById('cursor');
  const cursorRing = document.getElementById('cursorRing');
  document.addEventListener('mousemove', e => {{
    if (cursor) {{
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';
    }}
    setTimeout(() => {{
      if (cursorRing) {{
        cursorRing.style.left = e.clientX + 'px';
        cursorRing.style.top = e.clientY + 'px';
      }}
    }}, 40);
  }});
</script>
</body>
</html>
"""


def main() -> None:
    print("=" * 50)
    print(" Veridia Ajans | Otomatik Blog Ekleme Aracı")
    print("=" * 50)

    title = input("1. Makale Başlığı (Örn: Dijital Pazarlama Nedir?): ").strip()
    if not title:
        print("Hata: Başlık boş olamaz!")
        sys.exit(1)

    summary = input("2. Makalenin Kısa Özeti (Listede görünecek): ").strip()
    if not summary:
        print("Hata: Özet boş olamaz!")
        sys.exit(1)

    url_name = input("3. URL Adı (Sadece küçük harf, rakam ve tire kullanın, örn: dijital-pazarlama): ").strip()
    if not url_name:
        print("Hata: URL adı boş olamaz!")
        sys.exit(1)
    if not re.fullmatch(r"[a-z0-9-]+", url_name):
        print("Hata: URL adı sadece küçük harf, rakam ve tire içermelidir.")
        sys.exit(1)

    now = datetime.now()
    date_label = format_turkish_date(now)
    date_iso = now.strftime("%Y-%m-%d")
    file_path = f"blog/{url_name}.html"

    if not os.path.exists("blog"):
        os.makedirs("blog")

    template = build_article_template(title, summary, url_name, date_iso, date_label)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(template)
    print(f"\n✅ {file_path} dosyası oluşturuldu!")

    blog_file = "blog.html"
    if os.path.exists(blog_file):
        with open(blog_file, "r", encoding="utf-8") as file:
            content = file.read()

        safe_title = escape_text(title)
        safe_summary = escape_text(summary)
        card_html = f"""
        <article class="blog-card">
            <div class="blog-meta">
                <span>Yeni Yazı</span>
                <time datetime="{date_iso}">{date_label}</time>
                <span>6 dk okuma</span>
                <span>Yazar: Veridia Strateji Ekibi</span>
            </div>
            <h2><a href="/blog/{url_name}.html">{safe_title}</a></h2>
            <p>{safe_summary}</p>
            <div class="blog-card-footer">
                <a href="/blog/{url_name}.html" class="read-more">Makaleyi Oku</a>
                <a href="/#quote" class="secondary-link">Plan Çıkaralım</a>
            </div>
        </article>
"""

        marker = "        <!-- /BLOG_CARDS -->"
        if marker in content:
            content = content.replace(marker, f"{card_html}{marker}")
        elif '<section class="blog-grid" aria-label="Blog yazıları">' in content:
            content = content.replace(
                '<section class="blog-grid" aria-label="Blog yazıları">',
                f'<section class="blog-grid" aria-label="Blog yazıları">\n{card_html}',
            )

        with open(blog_file, "w", encoding="utf-8") as file:
            file.write(content)
        print("✅ blog.html listesine yeni makale eklendi!")

    sitemap_file = "sitemap.xml"
    if os.path.exists(sitemap_file):
        with open(sitemap_file, "r", encoding="utf-8") as file:
            content = file.read()

        sitemap_node = f"""
   <url>
      <loc>{SITE_URL}/blog/{url_name}.html</loc>
      <lastmod>{date_iso}</lastmod>
      <changefreq>monthly</changefreq>
      <priority>0.7</priority>
   </url>
</urlset>"""
        if "</urlset>" in content:
            content = content.replace("</urlset>", sitemap_node)
            with open(sitemap_file, "w", encoding="utf-8") as file:
                file.write(content)
            print("✅ sitemap.xml güncellendi!")

    print("\n🎉 İşlem tamam! Yeni yazıyı açıp gerçek paragrafları doldurabilir, ardından blog kartı ve sitemap bilgisini hızlıca kontrol edebilirsiniz.")


if __name__ == "__main__":
    main()
