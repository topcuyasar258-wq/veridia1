#!/usr/bin/env python3
from __future__ import annotations

import json
import ipaddress
import logging
import math
import os
import posixpath
import sqlite3
import ssl
import statistics
import threading
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib import error, request
from instagram_utils import (
    Metrics, compute_metrics, safe_int, parse_timestamp, 
    PROFILE_TYPE_LABELS, ARCHETYPE_LABELS, ACCOUNT_TIER_LABELS
)


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"
DB_PATH = ROOT / "analysis_snapshots.sqlite3"


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

PORT = int(os.environ.get("PORT", "8000"))
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
APIFY_ACTOR = os.environ.get("APIFY_ACTOR", "apify~instagram-profile-scraper").strip()
APIFY_TIMEOUT_SECS = int(os.environ.get("APIFY_TIMEOUT_SECS", "120"))
APIFY_MEMORY_MB = int(os.environ.get("APIFY_MEMORY_MB", "256"))
APIFY_INPUT_FIELD = os.environ.get("APIFY_INPUT_FIELD", "").strip()
APIFY_ALLOW_INSECURE_SSL = os.environ.get("APIFY_ALLOW_INSECURE_SSL", "0").strip() == "1"
INSTAGRAM_ANALYSIS_ENABLED = os.environ.get("INSTAGRAM_ANALYSIS_ENABLED", "0").strip() == "1"
MAX_REQUEST_BODY_BYTES = int(os.environ.get("MAX_REQUEST_BODY_BYTES", "4096"))
RATE_LIMIT_WINDOW_SECS = int(os.environ.get("RATE_LIMIT_WINDOW_SECS", "300"))
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "5"))
MAX_PROXY_IMAGE_BYTES = int(os.environ.get("MAX_PROXY_IMAGE_BYTES", "5242880"))
CONTACT_FORWARD_URL = os.environ.get("CONTACT_FORWARD_URL", "").strip()

DEFAULT_ALLOWED_ORIGINS = (
    f"http://127.0.0.1:{PORT}",
    f"http://localhost:{PORT}",
    "https://veridiareklam.com.tr",
    "https://www.veridiareklam.com.tr",
)
PUBLIC_FILE_PATHS = frozenset(
    {
        "/index.html",
        "/404.html",
        "/blog.html",
        "/neler-yapiyoruz.html",
        "/calismalarimiz.html",
        "/hakkimizda.html",
        "/calisma-surecimiz.html",
        "/hizli-teklif.html",
        "/iletisim.html",
        "/web-tasarim.html",
        "/seo-danismanligi.html",
        "/google-ads-yonetimi.html",
        "/sosyal-medya-yonetimi.html",
        "/dijital-pazarlama-stratejisi.html",
        "/guzellik-klinik-dijital-pazarlama.html",
        "/kafe-restoran-dijital-pazarlama.html",
        "/moda-e-ticaret-dijital-pazarlama.html",
        "/teknoloji-b2b-dijital-pazarlama.html",
        "/yasam-ev-markalari-dijital-pazarlama.html",
        "/gizlilik-politikasi.html",
        "/kvkk-aydinlatma-metni.html",
        "/robots.txt",
        "/sitemap.xml",
    }
)
PUBLIC_DIR_PREFIXES = ("/assets/", "/blog/", "/seo/", "/reklam/", "/yazilim/", "/automation/forms/")
LEGACY_REDIRECTS = {
    "/index.html": "/",
    "/asdfadsf.html": "/",
    "/veridia-ajans.html": "/",
    "/blog/b2b-pazarlamada-donusum-hunisi.html": "/blog/b2b-donusum-hunisi.html",
    "/web-tasarim.html": "/yazilim/web-sitesi-ve-donusum-yuzeyleri/",
    "/seo-danismanligi.html": "/seo/google-gorunurlugu/",
    "/google-ads-yonetimi.html": "/reklam/google-ads-yonetimi/",
    "/sosyal-medya-yonetimi.html": "/reklam/sosyal-medya-yonetimi/",
}
IMAGE_PROXY_ALLOWED_HOSTS = ("cdninstagram.com", "fbcdn.net")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'self'; "
    "script-src 'self' https://www.googletagmanager.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https://formspree.io https://www.google-analytics.com https://region1.google-analytics.com https://stats.g.doubleclick.net; "
    "form-action 'self' https://wa.me https://formspree.io"
)
ALLOWED_ORIGINS = frozenset(
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", ",".join(DEFAULT_ALLOWED_ORIGINS)).split(",")
    if origin.strip()
)
TRUSTED_PROXY_IPS = frozenset(
    origin.strip()
    for origin in os.environ.get("TRUSTED_PROXY_IPS", "").split(",")
    if origin.strip()
)

logger = logging.getLogger("veridia.server")
_rate_limit_lock = threading.Lock()
_rate_limit_events: dict[str, list[float]] = {}

# Metrics and Benchmarks moved to instagram_utils.py


class AnalyzeError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# Utility functions moved to instagram_utils.py


class NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req: request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def parse_ip_literal(value: str) -> str | None:
    raw = value.strip().strip('"').strip("'")
    if not raw or raw.lower() == "unknown":
        return None

    if raw.startswith("[") and "]" in raw:
        candidate = raw[1:].split("]", 1)[0]
    else:
        parts = raw.rsplit(":", 1)
        candidate = parts[0] if len(parts) == 2 and raw.count(":") == 1 else raw

    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def detect_input_field() -> str:
    if APIFY_INPUT_FIELD:
        return APIFY_INPUT_FIELD
    if APIFY_ACTOR == "instagram-scraper~instagram-profile-scraper":
        return "instagramUsernames"
    return "usernames"


def build_apify_input(username: str) -> dict[str, Any]:
    field = detect_input_field()
    payload: dict[str, Any] = {field: [username]}
    if field == "instagramUsernames":
        payload["retries"] = 1
    return payload


def build_opener(*, allow_redirects: bool, insecure_ssl: bool) -> request.OpenerDirector:
    handlers: list[Any] = []
    if not allow_redirects:
        handlers.append(NoRedirectHandler())
    context = ssl._create_unverified_context() if insecure_ssl else ssl.create_default_context()
    handlers.append(request.HTTPSHandler(context=context))
    return request.build_opener(*handlers)


def run_request(req: request.Request) -> str:
    try:
        opener = build_opener(allow_redirects=True, insecure_ssl=False)
        with opener.open(req, timeout=APIFY_TIMEOUT_SECS + 10) as response:
            return response.read().decode("utf-8")
    except error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError) and APIFY_ALLOW_INSECURE_SSL:
            opener = build_opener(allow_redirects=True, insecure_ssl=True)
            with opener.open(req, timeout=APIFY_TIMEOUT_SECS + 10) as response:
                return response.read().decode("utf-8")
        raise


def fetch_binary_url(url: str) -> tuple[bytes, str]:
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*"})
    opener = build_opener(allow_redirects=False, insecure_ssl=False)
    with opener.open(req, timeout=APIFY_TIMEOUT_SECS + 10) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and safe_int(content_length, default=MAX_PROXY_IMAGE_BYTES + 1) > MAX_PROXY_IMAGE_BYTES:
            raise AnalyzeError(HTTPStatus.BAD_GATEWAY, "Profil görseli çok büyük.")

        body = response.read(MAX_PROXY_IMAGE_BYTES + 1)
        if len(body) > MAX_PROXY_IMAGE_BYTES:
            raise AnalyzeError(HTTPStatus.BAD_GATEWAY, "Profil görseli çok büyük.")

        content_type = response.headers.get_content_type() or "application/octet-stream"
        if not content_type.startswith("image/"):
            raise AnalyzeError(HTTPStatus.BAD_GATEWAY, "Upstream içerik görsel değil.")
        return body, content_type


def normalize_request_path(raw_path: str) -> str | None:
    decoded = unquote(urlparse(raw_path).path or "/")
    if "\x00" in decoded:
        return None

    normalized = posixpath.normpath(decoded)
    if decoded.endswith("/") and normalized != "/":
        normalized = f"{normalized}/"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"

    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." or part.startswith(".") for part in parts):
        return None
    return "/" + "/".join(parts) if parts else "/"


def is_public_path(path: str) -> bool:
    if path in PUBLIC_FILE_PATHS:
        return True
    return any(
        path == prefix[:-1] or (path.startswith(prefix) and path != prefix)
        for prefix in PUBLIC_DIR_PREFIXES
    )


def resolve_public_path(path: str) -> str | None:
    if path == "/":
        return "/index.html"
    if path in LEGACY_REDIRECTS:
        return path
    if not is_public_path(path):
        return None

    candidate = ROOT / path.lstrip("/")
    if candidate.is_dir():
        index_path = candidate / "index.html"
        if not index_path.exists():
            return None
        return f"{path.rstrip('/')}/index.html"

    return path


def is_origin_allowed(origin: str) -> bool:
    return origin in ALLOWED_ORIGINS


def get_allowed_origin_header(origin: str | None) -> str | None:
    if not origin:
        return None
    if is_origin_allowed(origin):
        return origin
    return None


def get_rate_limit_key(handler: "AppHandler") -> str:
    client_ip = parse_ip_literal(handler.client_address[0]) or handler.client_address[0]
    if client_ip not in TRUSTED_PROXY_IPS:
        return client_ip

    forwarded_chain = get_forwarded_ip_chain(handler)
    return forwarded_chain[0] if forwarded_chain else client_ip


def get_forwarded_ip_chain(handler: "AppHandler") -> list[str]:
    forwarded_header = handler.headers.get("Forwarded", "")
    forwarded_ips: list[str] = []

    if forwarded_header:
        for entry in forwarded_header.split(","):
            for segment in entry.split(";"):
                key, _, raw_value = segment.strip().partition("=")
                if key.lower() != "for" or not raw_value:
                    continue
                parsed = parse_ip_literal(raw_value)
                if parsed:
                    forwarded_ips.append(parsed)

    if forwarded_ips:
        return forwarded_ips

    x_forwarded_for = handler.headers.get("X-Forwarded-For", "")
    if not x_forwarded_for:
        return []

    return [parsed for parsed in (parse_ip_literal(part) for part in x_forwarded_for.split(",")) if parsed]


def consume_rate_limit(handler: "AppHandler") -> int | None:
    now = time.time()
    key = get_rate_limit_key(handler)

    with _rate_limit_lock:
        active = [ts for ts in _rate_limit_events.get(key, []) if now - ts < RATE_LIMIT_WINDOW_SECS]
        if len(active) >= RATE_LIMIT_MAX_REQUESTS:
            retry_after = max(1, int(RATE_LIMIT_WINDOW_SECS - (now - active[0])))
            _rate_limit_events[key] = active
            return retry_after
        active.append(now)
        _rate_limit_events[key] = active
        return None


def clear_rate_limit_state() -> None:
    with _rate_limit_lock:
        _rate_limit_events.clear()


def is_allowed_image_host(host: str) -> bool:
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in IMAGE_PROXY_ALLOWED_HOSTS)


def apify_request(username: str) -> dict[str, Any]:
    if not APIFY_TOKEN:
        raise AnalyzeError(HTTPStatus.SERVICE_UNAVAILABLE, "Instagram analizi icin APIFY_TOKEN tanimlanmali.")

    url = (
        f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"
        f"?token={APIFY_TOKEN}&timeout={APIFY_TIMEOUT_SECS}&memory={APIFY_MEMORY_MB}&format=json&clean=true"
    )
    req = request.Request(
        url,
        data=json.dumps(build_apify_input(username)).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        payload = run_request(req)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail or str(exc)
        raise AnalyzeError(HTTPStatus.BAD_GATEWAY, f"Apify hatasi: {message}") from exc
    except error.URLError as exc:
        raise AnalyzeError(HTTPStatus.BAD_GATEWAY, f"Apify baglantisi kurulamadi: {exc.reason}") from exc

    try:
        items = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AnalyzeError(HTTPStatus.BAD_GATEWAY, "Apify gecersiz JSON dondurdu.") from exc

    if not isinstance(items, list) or not items:
        raise AnalyzeError(HTTPStatus.NOT_FOUND, "Bu kullanici icin sonuc bulunamadi.")

    item = items[0]
    if item.get("ig_status") == "not_found":
        raise AnalyzeError(HTTPStatus.NOT_FOUND, "Instagram profili bulunamadi.")
    return item


def normalize_profile(raw: dict[str, Any], requested_username: str) -> dict[str, Any]:
    latest_posts = raw.get("latest_posts") or raw.get("latestPosts") or []
    if not isinstance(latest_posts, list):
        latest_posts = []

    return {
        "username": raw.get("username") or requested_username,
        "full_name": raw.get("full_name") or raw.get("fullName") or requested_username,
        "biography": raw.get("biography") or "",
        "category_name": raw.get("category_name") or raw.get("categoryName") or "",
        "external_url": raw.get("external_url") or raw.get("externalUrl") or "",
        "profile_pic_url": raw.get("profile_pic_url") or raw.get("profilePicUrl") or "",
        "followers": safe_int(raw.get("followers", raw.get("followersCount"))),
        "following": safe_int(raw.get("following", raw.get("followingCount"))),
        "post_count": safe_int(raw.get("post_count", raw.get("postsCount"))),
        "is_verified": bool(raw.get("is_verified") or raw.get("verified")),
        "is_private": bool(raw.get("is_private") or raw.get("private")),
        "is_business_account": bool(raw.get("is_business_account") or raw.get("businessAccount")),
        "is_professional_account": bool(raw.get("is_professional_account") or raw.get("professionalAccount")),
        "latest_posts": latest_posts,
        "crawled_at": raw.get("crawled_at") or raw.get("scrapedAt") or formatdate(usegmt=True),
    }


# Archetype and tier logic moved to instagram_utils.py


def ensure_snapshot_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                followers INTEGER NOT NULL,
                following INTEGER NOT NULL,
                post_count INTEGER NOT NULL,
                overall_score INTEGER NOT NULL,
                representative_er REAL NOT NULL,
                median_er REAL NOT NULL,
                trimmed_er REAL NOT NULL,
                audience_quality INTEGER NOT NULL,
                authenticity_risk INTEGER NOT NULL,
                consistency INTEGER NOT NULL,
                confidence INTEGER NOT NULL,
                posting_frequency REAL NOT NULL,
                benchmark_er REAL NOT NULL,
                profile_type TEXT NOT NULL,
                profile_archetype TEXT NOT NULL,
                account_tier TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_username_captured_at
            ON analysis_snapshots(username, captured_at DESC)
            """
        )


def load_snapshots(username: str, limit: int = 6) -> list[dict[str, Any]]:
    ensure_snapshot_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT username, captured_at, followers, following, post_count, overall_score,
                   representative_er, median_er, trimmed_er, audience_quality,
                   authenticity_risk, consistency, confidence, posting_frequency,
                   benchmark_er, profile_type, profile_archetype, account_tier
            FROM analysis_snapshots
            WHERE lower(username) = lower(?)
            ORDER BY captured_at DESC
            LIMIT ?
            """,
            (username, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def save_snapshot(profile: dict[str, Any], metrics: Metrics) -> None:
    ensure_snapshot_db()
    captured_at = datetime.now(timezone.utc).isoformat()
    recent = load_snapshots(profile["username"], limit=1)
    if recent:
        prev = recent[0]
        prev_time = parse_timestamp(prev["captured_at"])
        if prev_time:
            minutes_since = abs((datetime.now(timezone.utc) - prev_time).total_seconds()) / 60
            if (
                minutes_since < 20
                and prev["followers"] == profile["followers"]
                and prev["post_count"] == profile["post_count"]
                and prev["overall_score"] == metrics.overall_score
            ):
                return

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analysis_snapshots (
                username, captured_at, followers, following, post_count, overall_score,
                representative_er, median_er, trimmed_er, audience_quality,
                authenticity_risk, consistency, confidence, posting_frequency,
                benchmark_er, profile_type, profile_archetype, account_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile["username"],
                captured_at,
                profile["followers"],
                profile["following"],
                profile["post_count"],
                metrics.overall_score,
                metrics.representative_engagement_rate,
                metrics.median_engagement_rate,
                metrics.trimmed_engagement_rate,
                metrics.audience_quality,
                metrics.authenticity_risk,
                metrics.consistency,
                metrics.confidence,
                metrics.posting_frequency_per_week,
                metrics.benchmark_er,
                metrics.profile_type,
                metrics.profile_archetype,
                metrics.account_tier,
            ),
        )


# Metrics computation moved to instagram_utils.py
    image_share = round((content_counts["image"] / total_posts) * 100)

    return Metrics(
        representative_engagement_rate=representative_er,
        median_engagement_rate=median_er,
        trimmed_engagement_rate=trimmed_er,
        weighted_recent_engagement_rate=weighted_recent_er,
        audience_quality=audience_quality,
        authenticity_risk=authenticity_risk,
        consistency=consistency,
        overall_score=overall_score,
        confidence=confidence,
        posting_frequency_per_week=posting_frequency_per_week,
        recent_posts_used=recent_posts_used,
        avg_likes=avg_likes,
        avg_comments=avg_comments,
        avg_views=avg_views,
        benchmark_er=benchmark_er,
        benchmark_ratio=benchmark_ratio,
        profile_type=PROFILE_TYPE_LABELS[archetype],
        profile_archetype=archetype,
        profile_archetype_label=ARCHETYPE_LABELS[archetype],
        account_tier=account_tier,
        account_tier_label=ACCOUNT_TIER_LABELS[account_tier],
        reels_share=reels_share,
        carousel_share=carousel_share,
        image_share=image_share,
        comment_rate=comment_rate,
    )


def build_history_summary(previous_snapshots: list[dict[str, Any]], profile: dict[str, Any], metrics: Metrics) -> dict[str, Any]:
    summary = {
        "snapshotCount": len(previous_snapshots) + 1,
        "hasPreviousSnapshot": False,
        "previousCapturedAt": None,
        "followerDelta": None,
        "scoreDelta": None,
        "engagementDelta": None,
        "hoursSincePrevious": None,
        "direction": "fresh",
        "note": "İlk snapshot kaydedildi. Trend çıkarmak için yeni analizler birikmeli.",
    }

    if not previous_snapshots:
        return summary

    previous = previous_snapshots[0]
    previous_captured_at = parse_timestamp(previous["captured_at"])
    hours_since_previous = None
    if previous_captured_at:
        hours_since_previous = round((datetime.now(timezone.utc) - previous_captured_at).total_seconds() / 3600, 1)

    follower_delta = profile["followers"] - safe_int(previous["followers"])
    score_delta = metrics.overall_score - safe_int(previous["overall_score"])
    engagement_delta = round(metrics.representative_engagement_rate - float(previous["representative_er"]), 2)

    if follower_delta > 0 and score_delta >= 0:
        direction = "up"
        note = "Son snapshot'a göre profil ivmesi yukarı. Yeni içerikler benchmarkta daha sağlam duruyor."
    elif score_delta >= 3:
        direction = "up"
        note = "Takipçi sabit olsa da kalite ve etkileşim sinyalleri bir önceki snapshot'a göre iyileşmiş."
    elif score_delta <= -3:
        direction = "down"
        note = "Bir önceki snapshot'a göre skor geri çekilmiş. İçerik ritmi veya etkileşim derinliği zayıflamış olabilir."
    else:
        direction = "stable"
        note = "Skor son snapshot'a göre stabil. Trend okuması için daha fazla veri noktası faydalı olacak."

    summary.update(
        {
            "snapshotCount": len(previous_snapshots) + 1,
            "hasPreviousSnapshot": True,
            "previousCapturedAt": previous["captured_at"],
            "followerDelta": follower_delta,
            "scoreDelta": score_delta,
            "engagementDelta": engagement_delta,
            "hoursSincePrevious": hours_since_previous,
            "direction": direction,
            "note": note,
        }
    )
    return summary


def build_insights(profile: dict[str, Any], metrics: Metrics, history: dict[str, Any]) -> list[str]:
    insights: list[str] = []

    benchmark_delta_pct = round((metrics.benchmark_ratio - 1) * 100)
    if metrics.benchmark_ratio >= 1.15:
        insights.append(
            f"Temsilci etkileşim oranı {metrics.representative_engagement_rate:.2f}% ile {metrics.account_tier_label} segment benchmarkının {benchmark_delta_pct:+d}% üstünde."
        )
    elif metrics.benchmark_ratio >= 0.9:
        insights.append(
            f"Etkileşim benchmark'a yakın. Temsilci oran {metrics.representative_engagement_rate:.2f}% ve baz alınmış benchmark {metrics.benchmark_er:.2f}%."
        )
    else:
        insights.append(
            f"Etkileşim benchmark'ın gerisinde. Temsilci oran {metrics.representative_engagement_rate:.2f}% ve hedef segment baz çizgisi {metrics.benchmark_er:.2f}%."
        )

    if metrics.authenticity_risk >= 60:
        insights.append(
            f"Otantiklik riski yüksek görünüyor. Yorum derinliği %{metrics.comment_rate:.2f} ve post oynaklığı nedeniyle sinyal kalitesi zayıf."
        )
    elif metrics.authenticity_risk >= 40:
        insights.append(
            f"Otantiklik sinyalleri karışık. Yorum oranı ve postlar arası oynaklık daha dengeli hale gelirse risk aşağı iner."
        )
    else:
        insights.append(
            f"Otantiklik riski düşük. Yorum davranışı ve hesap yapısı organik profile daha yakın sinyal veriyor."
        )

    if metrics.consistency >= 75:
        insights.append(
            f"İçerik ritmi güçlü. Haftalık yayın hızı {metrics.posting_frequency_per_week:.2f} ve tutarlılık skoru {metrics.consistency}/100."
        )
    elif metrics.consistency >= 55:
        insights.append(
            f"İçerik ritmi orta seviyede. Haftalık yayın hızı {metrics.posting_frequency_per_week:.2f}; düzenli seri formatlar tutarlılığı güçlendirebilir."
        )
    else:
        insights.append(
            f"Paylaşım ritmi dağınık. Haftalık yayın hızı {metrics.posting_frequency_per_week:.2f}; sabit seri ve takvim kullanmak kritik."
        )

    if metrics.reels_share >= 60:
        insights.append(
            f"İçerik karması ağırlıkla reels odaklı (%{metrics.reels_share}). Reels güçlü ama carousel/tek görsel ile yorum derinliği desteklenebilir."
        )
    elif metrics.carousel_share >= 35:
        insights.append(
            f"Carousel kullanımı sağlıklı (%{metrics.carousel_share}). Bu format mesaj derinliği ve save potansiyeli için iyi sinyal."
        )
    else:
        insights.append(
            f"İçerik karması dengeli değil. Reels %{metrics.reels_share}, carousel %{metrics.carousel_share}, görsel %{metrics.image_share} seviyesinde."
        )

    if history["hasPreviousSnapshot"]:
        insights.append(history["note"])
    else:
        insights.append("Bu analiz ilk snapshot olarak kaydedildi. Birkaç tekrar sonrasında 30/90 günlük trend okuması anlamlı hale gelecek.")

    return insights[:5]


def build_summary(metrics: Metrics, history: dict[str, Any]) -> tuple[dict[str, str], str]:
    if metrics.overall_score >= 74 and metrics.authenticity_risk < 45:
        badge = {"label": "Güçlü Profil", "tone": "ok"}
        summary = "Profil benchmark'a göre sağlam sinyaller veriyor. İçerik ritmi korunursa bir sonraki odak alan dönüşüm ve kampanya verimi olmalı."
    elif metrics.overall_score >= 56:
        badge = {"label": "Geliştirme Potansiyeli", "tone": "warn"}
        summary = "Temel sinyaller umut verici, ancak benchmark üstü performans için etkileşim derinliği ve format dengesi daha bilinçli yönetilmeli."
    else:
        badge = {"label": "Aksiyon Gerekli", "tone": "low"}
        summary = "Profilde görünürlük var ama kalite sinyalleri benchmark'ın gerisinde. İçerik yapısı, otantiklik sinyalleri ve düzenli yayın ritmi birlikte ele alınmalı."

    if metrics.confidence < 55:
        summary += " Veri güven seviyesi henüz orta-alt; daha fazla snapshot biriktikçe trend yorumu daha isabetli olacak."
    elif history["hasPreviousSnapshot"]:
        summary += " Geçmiş snapshot ile karşılaştırma aktif olduğu için yorum güveni önceki versiyona göre daha yüksek."

    return badge, summary


def build_public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    latest_post_dates = [
        parse_timestamp(post.get("taken_at_timestamp", post.get("timestamp")))
        for post in profile["latest_posts"][:12]
    ]
    latest_post_dates = [dt for dt in latest_post_dates if dt]
    latest_post_at = max(latest_post_dates).isoformat() if latest_post_dates else None

    return {
        "username": profile["username"],
        "fullName": profile["full_name"],
        "biography": profile["biography"],
        "categoryName": profile["category_name"],
        "externalUrl": profile["external_url"],
        "profilePicUrl": profile["profile_pic_url"],
        "profilePicProxyUrl": f"/api/profile-image?src={quote(profile['profile_pic_url'], safe='')}" if profile["profile_pic_url"] else "",
        "followers": profile["followers"],
        "following": profile["following"],
        "postCount": profile["post_count"],
        "isVerified": profile["is_verified"],
        "isPrivate": profile["is_private"],
        "latestPostAt": latest_post_at,
        "crawledAt": profile["crawled_at"],
    }


def build_analysis(username: str) -> dict[str, Any]:
    raw = apify_request(username)
    profile = normalize_profile(raw, username)
    previous_snapshots = load_snapshots(profile["username"])
    metrics = compute_metrics(profile, history_depth=len(previous_snapshots))
    history = build_history_summary(previous_snapshots, profile, metrics)
    badge, summary = build_summary(metrics, history)
    insights = build_insights(profile, metrics, history)

    steps = [
        {
            "label": "Profil verisi doğrulandı",
            "subLabel": f"@{profile['username']} için follower, post ve profil sinyalleri alındı",
        },
        {
            "label": "Temsilci etkileşim hesaplandı",
            "subLabel": f"Median {metrics.median_engagement_rate:.2f}% · trimmed {metrics.trimmed_engagement_rate:.2f}%",
        },
        {
            "label": "Kitle kalitesi yorumlandı",
            "subLabel": f"Kitle kalitesi {metrics.audience_quality}/100 · otantiklik riski {metrics.authenticity_risk}%",
        },
        {
            "label": "İçerik ritmi ve format karması ölçüldü",
            "subLabel": f"Haftalık hız {metrics.posting_frequency_per_week:.2f} · reels payı %{metrics.reels_share}",
        },
        {
            "label": "Benchmark ve güven seviyesi oluşturuldu",
            "subLabel": f"{metrics.account_tier_label} · {metrics.profile_archetype_label} · güven {metrics.confidence}/100",
        },
    ]

    save_snapshot(profile, metrics)

    return {
        "profile": build_public_profile(profile),
        "metrics": {
            "engagementRate": metrics.representative_engagement_rate,
            "medianEngagementRate": metrics.median_engagement_rate,
            "trimmedEngagementRate": metrics.trimmed_engagement_rate,
            "weightedRecentEngagementRate": metrics.weighted_recent_engagement_rate,
            "audienceQuality": metrics.audience_quality,
            "followerQuality": metrics.audience_quality,
            "authenticityRisk": metrics.authenticity_risk,
            "botRisk": metrics.authenticity_risk,
            "consistency": metrics.consistency,
            "overallScore": metrics.overall_score,
            "confidenceScore": metrics.confidence,
            "postingFrequencyPerWeek": metrics.posting_frequency_per_week,
            "recentPostsUsed": metrics.recent_posts_used,
            "avgLikes": metrics.avg_likes,
            "avgComments": metrics.avg_comments,
            "avgViews": metrics.avg_views,
            "benchmarkEr": metrics.benchmark_er,
            "benchmarkRatio": metrics.benchmark_ratio,
            "profileType": metrics.profile_type,
            "profileArchetype": metrics.profile_archetype_label,
            "accountTier": metrics.account_tier_label,
            "commentRate": metrics.comment_rate,
        },
        "benchmark": {
            "erBaseline": metrics.benchmark_er,
            "ratio": metrics.benchmark_ratio,
            "deltaPercent": round((metrics.benchmark_ratio - 1) * 100),
            "accountTierLabel": metrics.account_tier_label,
            "profileArchetypeLabel": metrics.profile_archetype_label,
        },
        "contentMix": {
            "reels": metrics.reels_share,
            "carousels": metrics.carousel_share,
            "images": metrics.image_share,
        },
        "history": history,
        "badge": badge,
        "summary": summary,
        "steps": steps,
        "insights": insights,
        "provider": {
            "name": "Apify",
            "actor": APIFY_ACTOR,
        },
    }


def ensure_contact_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                source_path TEXT NOT NULL
            )
            """
        )


def save_contact_submission(
    *,
    name: str,
    email: str,
    phone: str,
    message: str,
    source_path: str,
) -> None:
    ensure_contact_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO contact_submissions (
                submitted_at, name, email, phone, message, source_path
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                name,
                email,
                phone,
                message,
                source_path,
            ),
        )


def validate_contact_payload(payload: dict[str, Any]) -> dict[str, str]:
    name = " ".join(str(payload.get("isim", "")).split())
    email = str(payload.get("email", "")).strip()
    phone = " ".join(str(payload.get("telefon", "")).split())
    message = str(payload.get("mesaj", "")).strip()
    source_path = str(payload.get("kaynak", "/")).strip() or "/"

    if not name or len(name) < 2:
        raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Ad soyad bilgisi gerekli.")
    if not email or "@" not in email or len(email) > 254:
        raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Gecerli bir e-posta adresi gerekli.")
    if not message or len(message) < 10:
        raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Mesaj en az 10 karakter olmali.")
    if len(name) > 120 or len(phone) > 40 or len(message) > 4000 or len(source_path) > 200:
        raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Gonderilen bilgiler beklenenden uzun.")

    return {
        "isim": name,
        "email": email,
        "telefon": phone,
        "mesaj": message,
        "kaynak": source_path,
    }


def forward_contact_submission(payload: dict[str, str]) -> None:
    if not CONTACT_FORWARD_URL:
        return

    req = request.Request(
        CONTACT_FORWARD_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        run_request(req)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to forward contact submission")
        raise AnalyzeError(HTTPStatus.BAD_GATEWAY, "Form iletisi ileri aktarilamadi.") from exc


def json_response(
    handler: "AppHandler",
    status: int,
    payload: dict[str, Any],
    *,
    extra_headers: dict[str, str] | None = None,
) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    for header, value in (extra_headers or {}).items():
        handler.send_header(header, value)
    origin = get_allowed_origin_header(handler.headers.get("Origin"))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.end_headers()
    handler.wfile.write(raw)


class AppHandler(SimpleHTTPRequestHandler):
    server_version = "Veridia"
    sys_version = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        request_path = getattr(self, "path", "") or ""
        path = urlparse(request_path).path
        if path.startswith("/api/") and not path.startswith("/api/profile-image"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        elif path in ("/robots.txt", "/sitemap.xml"):
            self.send_header("Cache-Control", "public, max-age=3600")
        elif path.endswith(".html") or path == "/" or not path:
            self.send_header("Cache-Control", "no-cache, must-revalidate")

        self.send_header("Vary", "Accept-Encoding")
        for header, value in self.get_security_headers().items():
            self.send_header(header, value)
        if self.is_secure_request():
            self.send_header("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        super().end_headers()

    def get_security_headers(self) -> dict[str, str]:
        headers = dict(SECURITY_HEADERS)
        content_security_policy = CONTENT_SECURITY_POLICY
        if self.is_secure_request():
            content_security_policy = f"{content_security_policy}; upgrade-insecure-requests"
        headers["Content-Security-Policy"] = content_security_policy
        return headers

    def is_secure_request(self) -> bool:
        forwarded_proto = self.headers.get("X-Forwarded-Proto", "").split(",", 1)[0].strip().lower()
        if forwarded_proto == "https":
            return True

        return getattr(self.connection, "cipher", None) is not None

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        if code == HTTPStatus.NOT_FOUND:
            self.send_not_found_page()
            return
        super().send_error(code, message, explain)

    def send_not_found_page(self) -> None:
        error_page = ROOT / "404.html"
        try:
            body = error_page.read_bytes()
        except OSError:
            super().send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        normalized_path = normalize_request_path(self.path)
        if normalized_path not in {"/api/analyze-instagram", "/api/contact"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        origin = self.headers.get("Origin")
        if origin and not is_origin_allowed(origin):
            self.send_error(HTTPStatus.FORBIDDEN, "Bu origin icin izin yok.")
            return

        self.send_response(HTTPStatus.NO_CONTENT)
        allowed_origin = get_allowed_origin_header(origin)
        if allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        normalized_path = normalize_request_path(self.path)
        if normalized_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if normalized_path == "/api/profile-image":
            self.handle_profile_image_proxy(parsed.query)
            return

        if normalized_path == "/":
            self.path = "/index.html"
            super().do_GET()
            return

        resolved_path = resolve_public_path(normalized_path)
        if resolved_path in LEGACY_REDIRECTS:
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", LEGACY_REDIRECTS[resolved_path])
            self.end_headers()
            return

        if resolved_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.path = resolved_path
        super().do_GET()

    def handle_profile_image_proxy(self, query: str) -> None:
        params = parse_qs(query)
        src = (params.get("src") or [""])[0]
        if not src:
            self.send_error(HTTPStatus.BAD_REQUEST, "Image source is required.")
            return

        parsed = urlparse(src)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            self.send_error(HTTPStatus.BAD_REQUEST, "Gecersiz gorsel kaynagi.")
            return

        host = parsed.hostname.lower()
        if not is_allowed_image_host(host):
            self.send_error(HTTPStatus.BAD_REQUEST, "Desteklenmeyen gorsel kaynagi.")
            return

        try:
            body, content_type = fetch_binary_url(src)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
        except AnalyzeError as exc:
            self.send_error(exc.status, "Image proxy rejected upstream response.")
        except error.HTTPError as exc:
            self.send_error(exc.code, "Upstream image fetch failed.")
        except error.URLError as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, "Image proxy failed.")

    def do_POST(self) -> None:
        normalized_path = normalize_request_path(self.path)
        if normalized_path == "/api/contact":
            self.handle_contact_submission()
            return

        if normalized_path != "/api/analyze-instagram":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            if not INSTAGRAM_ANALYSIS_ENABLED:
                raise AnalyzeError(HTTPStatus.SERVICE_UNAVAILABLE, "Instagram analiz araci su an kapali.")

            origin = self.headers.get("Origin")
            if origin and not is_origin_allowed(origin):
                raise AnalyzeError(HTTPStatus.FORBIDDEN, "Bu origin icin izin yok.")

            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise AnalyzeError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Istek JSON olmalidir.")

            length = safe_int(self.headers.get("Content-Length", "0"), default=0)
            if length > MAX_REQUEST_BODY_BYTES:
                raise AnalyzeError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Istek govdesi cok buyuk.")

            retry_after = consume_rate_limit(self)
            if retry_after is not None:
                json_response(
                    self,
                    HTTPStatus.TOO_MANY_REQUESTS,
                    {"ok": False, "error": "Cok fazla istek gonderildi. Lutfen daha sonra tekrar deneyin."},
                    extra_headers={"Retry-After": str(retry_after)},
                )
                return

            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            username = str(payload.get("username", "")).strip().lstrip("@")
            if not username:
                raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Instagram kullanici adi gerekli.")
            if len(username) > 30 or not username.replace(".", "").replace("_", "").isalnum():
                raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Gecersiz Instagram kullanici adi.")
            result = build_analysis(username)
            json_response(self, HTTPStatus.OK, {"ok": True, "data": result})
        except AnalyzeError as exc:
            json_response(self, exc.status, {"ok": False, "error": exc.message})
        except json.JSONDecodeError:
            json_response(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Geçersiz JSON gönderildi."})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error while handling Instagram analysis")
            json_response(
                self,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": "Beklenmeyen bir sunucu hatasi olustu."},
            )

    def handle_contact_submission(self) -> None:
        try:
            origin = self.headers.get("Origin")
            if origin and not is_origin_allowed(origin):
                raise AnalyzeError(HTTPStatus.FORBIDDEN, "Bu origin icin izin yok.")

            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise AnalyzeError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Istek JSON olmalidir.")

            length = safe_int(self.headers.get("Content-Length", "0"), default=0)
            if length > MAX_REQUEST_BODY_BYTES * 2:
                raise AnalyzeError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Istek govdesi cok buyuk.")

            retry_after = consume_rate_limit(self)
            if retry_after is not None:
                json_response(
                    self,
                    HTTPStatus.TOO_MANY_REQUESTS,
                    {"ok": False, "error": "Cok fazla istek gonderildi. Lutfen daha sonra tekrar deneyin."},
                    extra_headers={"Retry-After": str(retry_after)},
                )
                return

            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            validated = validate_contact_payload(payload)
            save_contact_submission(
                name=validated["isim"],
                email=validated["email"],
                phone=validated["telefon"],
                message=validated["mesaj"],
                source_path=validated["kaynak"],
            )
            forward_contact_submission(validated)
            json_response(
                self,
                HTTPStatus.OK,
                {"ok": True, "message": "Mesajiniz alindi. En kisa surede size donus yapacagiz."},
            )
        except AnalyzeError as exc:
            json_response(self, exc.status, {"ok": False, "error": exc.message})
        except json.JSONDecodeError:
            json_response(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Geçersiz JSON gönderildi."})
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error while handling contact submission")
            json_response(
                self,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": "Beklenmeyen bir sunucu hatasi olustu."},
            )

    def do_HEAD(self) -> None:
        normalized_path = normalize_request_path(self.path)
        if normalized_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if normalized_path == "/":
            self.path = "/index.html"
            super().do_HEAD()
            return

        resolved_path = resolve_public_path(normalized_path)
        if resolved_path in LEGACY_REDIRECTS:
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", LEGACY_REDIRECTS[resolved_path])
            self.end_headers()
            return

        if resolved_path is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.path = resolved_path
        super().do_HEAD()

    def list_directory(self, path: str) -> Any:
        self.send_error(HTTPStatus.NOT_FOUND)
        return None

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Serving {ROOT} at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
