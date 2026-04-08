#!/usr/bin/env python3
import os
import sys
from datetime import datetime

def main():
    print("="*50)
    print(" Veridia Ajans | Otomatik Blog Ekleme Aracı")
    print("="*50)

    title = input("1. Makale Başlığı (Örn: Dijital Pazarlama Nedir?): ").strip()
    if not title:
        print("Hata: Başlık boş olamaz!")
        sys.exit(1)

    summary = input("2. Makalenin Kısa Özeti (Listede görünecek): ").strip()
    
    url_name = input("3. URL Adı (Sadece küçük harf ve tire kullanın, örn: dijital-pazarlama): ").strip()
    if not url_name:
        print("Hata: URL adı boş olamaz!")
        sys.exit(1)
        
    date_str = datetime.now().strftime("%d %B %Y").replace("January", "Ocak").replace("February", "Şubat").replace("March", "Mart").replace("April", "Nisan").replace("May", "Mayıs").replace("June", "Haziran").replace("July", "Temmuz").replace("August", "Ağustos").replace("September", "Eylül").replace("October", "Ekim").replace("November", "Kasım").replace("December", "Aralık")
    date_iso = datetime.now().strftime("%Y-%m-%d")

    file_path = f"blog/{url_name}.html"

    # HTML Şablonu
    template = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Veridia Blog</title>
    <meta name="description" content="{summary}">
    <!-- JSON-LD SEO için -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "author": {{
        "@type": "Organization",
        "name": "Veridia Ajans"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "Veridia"
      }},
      "datePublished": "{date_iso}",
      "description": "{summary}"
    }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Cormorant+Garamond:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/shared.css">
    <style>
        body {{ padding-top: 8rem; }}
        .article-container {{ max-width: 800px; margin: 0 auto; padding: 0 2rem 6rem; position: relative; z-index: 2; }}
        .article-container::before {{ content: ''; position: absolute; left: -10vw; right: -10vw; top: 0; bottom: 0; background: radial-gradient(ellipse 40% 60% at 20% 10%, rgba(26,92,58,0.08) 0%, transparent 60%); z-index: -1; pointer-events: none; }}
        h1 {{ font-family: 'Cormorant Garamond', serif; font-size: clamp(2.5rem, 6vw, 4rem); margin-bottom: 1.5rem; line-height: 1.1; color: var(--off-white); }}
        .meta-info {{ font-size: 0.72rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 3rem; padding-bottom: 1.5rem; border-bottom: 1px solid rgba(201,168,76,0.15); display: flex; gap: 1.5rem; }}
        h2 {{ font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; margin-top: 4rem; margin-bottom: 1.2rem; color: var(--off-white); border-left: 2px solid var(--gold); padding-left: 1rem; }}
        p {{ color: var(--text-muted); margin-bottom: 1.8rem; font-size: 1.05rem; line-height: 1.9; }}
        @media (max-width: 768px) {{ body {{ padding-top: 6rem; }} .meta-info {{ flex-direction: column; gap: 0.5rem; }} }}
        strong {{ color: var(--gold); font-weight: 500; }}
    </style>
</head>
<body>

<!-- KURSOR -->
<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>
<div class="scroll-bar" id="scrollBar"></div>

<!-- NAV -->
<nav id="navbar">
  <a href="/veridia-ajans.html" class="nav-logo">Veridia</a>
  <a href="/blog.html" style="color:var(--off-white); font-size:0.8rem; text-decoration:none; text-transform:uppercase; letter-spacing:0.1em; transition:color 0.2s;">← Blog'a Dön</a>
</nav>

<main class="article-container">
    <article>
        <h1>{title}</h1>
        <div class="meta-info">
            <span>Yazar: Veridia Strateji Ekibi</span> 
            <span>{date_str}</span>
        </div>

        <p><em>Özet: {summary}</em></p>
        
        <h2>Ana Başlık 1</h2>
        <p>Buraya makalenin ilk parçasını girebilirsiniz. HTML etiketlerini kullanmak paragraf ayırmak için faydalıdır.</p>
        
        <h2>Ana Başlık 2</h2>
        <p>Bu dosya otomatik oluşturuldu. İçeriğini dilediğiniz gibi düzenleyebilirsiniz.</p>
    </article>
</main>
<script>
  window.addEventListener('scroll', () => {{
    const wScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    if(document.getElementById('scrollBar')) document.getElementById('scrollBar').style.width = (wScroll / height) * 100 + '%';
  }});
  const cursor = document.getElementById('cursor'); const cursorRing = document.getElementById('cursorRing');
  document.addEventListener('mousemove', e => {{
    if(cursor) {{ cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px'; }}
    setTimeout(() => {{ if(cursorRing) {{ cursorRing.style.left = e.clientX + 'px'; cursorRing.style.top = e.clientY + 'px'; }} }}, 40);
  }});
</script>
</body>
</html>
"""

    if not os.path.exists('blog'):
        os.makedirs('blog')

    # 1. Makale dosyasını oluştur
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"\n✅ {file_path} dosyası oluşturuldu! (İçini manuel doldurabilirsiniz)")

    # 2. blog.html içerisine link ekle
    blog_file = "blog.html"
    if os.path.exists(blog_file):
        with open(blog_file, "r", encoding="utf-8") as f:
            content = f.read()

        card_html = f"""
    <article class="blog-card">
        <h2>{title}</h2>
        <p>{summary}</p>
        <a href="/blog/{url_name}.html" class="read-more">Makaleyi Oku</a>
    </article>"""
        
        if '<div class="blog-grid">' in content:
            content = content.replace('<div class="blog-grid">', f'<div class="blog-grid">{card_html}')
            with open(blog_file, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ blog.html listesine yeni makale eklendi!")

    # 3. sitemap.xml içerisine ekle
    sitemap_file = "sitemap.xml"
    if os.path.exists(sitemap_file):
        with open(sitemap_file, "r", encoding="utf-8") as f:
            content = f.read()

        sitemap_node = f"""
   <url>
      <loc>http://127.0.0.1:8000/blog/{url_name}.html</loc>
      <changefreq>monthly</changefreq>
      <priority>0.6</priority>
   </url>
</urlset>"""
        if '</urlset>' in content:
            content = content.replace('</urlset>', sitemap_node)
            with open(sitemap_file, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ sitemap.xml (SEO) güncellendi!")

    print("\n🎉 İşlem tamam! Artik olusturulan dosyayı kod editöründe açıp asıl paragraflarını yazabilirsiniz.")

if __name__ == "__main__":
    main()
