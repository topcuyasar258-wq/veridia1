#!/usr/bin/env python3
"""IndexNow URL bildirimi.

Yeni yayinlanan veya guncellenen sayfalari Bing/Yandex/Naver gibi IndexNow
destekleyen arama motorlarina aninda bildirir.

Kullanim:
    python3 scripts/indexnow_submit.py https://www.veridiareklam.com.tr/blog/yeni-yazi
    python3 scripts/indexnow_submit.py --sitemap   # sitemap'teki tum URL'leri bildirir

Anahtar dosyasi repo kokunde {KEY}.txt olarak durur ve deploy ile birlikte
https://www.veridiareklam.com.tr/{KEY}.txt adresinde yayinlanir.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

HOST = "www.veridiareklam.com.tr"
KEY = "2aaac50ad8517e9bdfe4709305cfe07c"
ENDPOINT = "https://api.indexnow.org/indexnow"
ROOT = Path(__file__).resolve().parent.parent


def sitemap_urls():
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>(.*?)</loc>", text)


def submit(urls):
    urls = [u for u in urls if HOST in u]
    if not urls:
        print("Bildirilecek URL yok.")
        return 1
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"IndexNow yaniti: HTTP {resp.status} ({len(urls)} URL bildirildi)")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--sitemap":
        sys.exit(submit(sitemap_urls()))
    sys.exit(submit(args))
