#!/usr/bin/env python3
"""sitemap.xml'i yeniden uretir.

- URL listesi mevcut sitemap.xml'den alinir; blog yazilari blog/*.html
  dosyalarindan otomatik kesfedilir (yeni yazi eklenince sitemap'e girer).
- lastmod her URL'nin kaynak dosyasinin son git commit tarihinden uretilir
  (git yoksa dosya mtime kullanilir).
- Google tarafindan yok sayilan changefreq/priority etiketleri yazilmaz.
- Mevcut image:image kayitlari korunur.

Kullanim: python3 scripts/update_sitemap.py
"""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.veridiareklam.com.tr"


def url_to_file(url: str):
    path = url[len(BASE):]
    if path in ("", "/"):
        return ROOT / "index.html"
    if path == "/blog":
        return ROOT / "blog.html"
    path = path.lstrip("/")
    if path.endswith("/"):
        return ROOT / path / "index.html"
    candidate = ROOT / (path + ".html")
    if candidate.exists():
        return candidate
    candidate = ROOT / path / "index.html"
    if candidate.exists():
        return candidate
    return ROOT / path


def git_lastmod(f: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(f.relative_to(ROOT))],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    ts = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
    return ts.isoformat(timespec="seconds")


def parse_existing():
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    entries = []
    for block in re.findall(r"<url>(.*?)</url>", text, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1).strip()
        images = re.findall(r"<image:image>.*?</image:image>", block, re.S)
        entries.append((loc, images))
    return entries


def main():
    entries = parse_existing()
    urls = {}
    for loc, images in entries:
        if loc == BASE:
            loc = BASE + "/"  # kok URL trailing slash standardi
        urls[loc] = images

    # blog yazilarini otomatik kesfet
    for f in sorted((ROOT / "blog").glob("*.html")):
        loc = f"{BASE}/blog/{f.stem}"
        urls.setdefault(loc, [])

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    skipped = []
    for loc in sorted(urls, key=lambda u: (u != BASE + "/", u)):
        f = url_to_file(loc)
        if not f.exists():
            skipped.append(loc)
            continue
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{git_lastmod(f)}</lastmod>")
        for img in urls[loc]:
            img = "\n".join("    " + l.strip() for l in img.splitlines())
            lines.append(img)
        lines.append("  </url>")
    lines.append("</urlset>")

    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(urls) - len(skipped)} URL yazildi.")
    if skipped:
        print("Atlanan (dosyasi bulunamayan) URL'ler:")
        for s in skipped:
            print("  -", s)


if __name__ == "__main__":
    main()
