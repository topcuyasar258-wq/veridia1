#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sqlite3
import ssl
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse
from urllib import error, request


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0"
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
APIFY_ALLOW_INSECURE_SSL = os.environ.get("APIFY_ALLOW_INSECURE_SSL", "1").strip() == "1"

BENCHMARK_ERS = {
    "brand": {
        "nano": 4.4,
        "micro": 3.2,
        "mid": 2.4,
        "macro": 1.7,
        "mega": 1.2,
    },
    "creator": {
        "nano": 5.8,
        "micro": 4.5,
        "mid": 3.3,
        "macro": 2.4,
        "mega": 1.6,
    },
    "media": {
        "nano": 4.8,
        "micro": 3.7,
        "mid": 2.8,
        "macro": 2.0,
        "mega": 1.4,
    },
}

EXPECTED_COMMENT_RATES = {
    "brand": 0.9,
    "creator": 1.2,
    "media": 1.0,
}

TARGET_WEEKLY_POSTS = {
    "brand": 3.5,
    "creator": 4.5,
    "media": 5.5,
}

PROFILE_TYPE_LABELS = {
    "brand": "Kurumsal Profil",
    "creator": "Creator Profil",
    "media": "Medya Profili",
}

ARCHETYPE_LABELS = {
    "brand": "Brand",
    "creator": "Creator",
    "media": "Media",
}

ACCOUNT_TIER_LABELS = {
    "nano": "Nano (0-10K)",
    "micro": "Micro (10K-100K)",
    "mid": "Mid (100K-500K)",
    "macro": "Macro (500K-2M)",
    "mega": "Mega (2M+)",
}


class AnalyzeError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass
class Metrics:
    representative_engagement_rate: float
    median_engagement_rate: float
    trimmed_engagement_rate: float
    weighted_recent_engagement_rate: float
    audience_quality: int
    authenticity_risk: int
    consistency: int
    overall_score: int
    confidence: int
    posting_frequency_per_week: float
    recent_posts_used: int
    avg_likes: int
    avg_comments: int
    avg_views: int
    benchmark_er: float
    benchmark_ratio: float
    profile_type: str
    profile_archetype: str
    profile_archetype_label: str
    account_tier: str
    account_tier_label: str
    reels_share: int
    carousel_share: int
    image_share: int
    comment_rate: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def trimmed_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) < 5:
        return statistics.mean(values)
    trim = max(1, round(len(values) * 0.15))
    sorted_values = sorted(values)
    if len(sorted_values) <= trim * 2:
        return statistics.mean(sorted_values)
    return statistics.mean(sorted_values[trim:-trim])


def safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.replace(",", "").replace("_", "").strip()))
        except ValueError:
            return default
    return default


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            return None
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


def run_request(req: request.Request) -> str:
    try:
        with request.urlopen(req, timeout=APIFY_TIMEOUT_SECS + 10) as response:
            return response.read().decode("utf-8")
    except error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError) and APIFY_ALLOW_INSECURE_SSL:
            insecure_context = ssl._create_unverified_context()
            with request.urlopen(req, timeout=APIFY_TIMEOUT_SECS + 10, context=insecure_context) as response:
                return response.read().decode("utf-8")
        raise


def fetch_binary_url(url: str) -> tuple[bytes, str]:
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*"})
    try:
        with request.urlopen(req, timeout=APIFY_TIMEOUT_SECS + 10) as response:
            return response.read(), response.headers.get_content_type() or "image/jpeg"
    except error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError) and APIFY_ALLOW_INSECURE_SSL:
            insecure_context = ssl._create_unverified_context()
            with request.urlopen(req, timeout=APIFY_TIMEOUT_SECS + 10, context=insecure_context) as response:
                return response.read(), response.headers.get_content_type() or "image/jpeg"
        raise


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


def determine_profile_archetype(profile: dict[str, Any]) -> str:
    haystack = " ".join(
        [
            str(profile.get("category_name", "")),
            str(profile.get("biography", "")),
            str(profile.get("full_name", "")),
        ]
    ).lower()
    media_signals = ["news", "media", "magazine", "tv", "journal", "press"]
    if any(signal in haystack for signal in media_signals):
        return "media"
    if profile["is_business_account"] or profile["is_professional_account"] or profile.get("external_url"):
        return "brand"
    return "creator"


def determine_account_tier(followers: int) -> str:
    if followers < 10_000:
        return "nano"
    if followers < 100_000:
        return "micro"
    if followers < 500_000:
        return "mid"
    if followers < 2_000_000:
        return "macro"
    return "mega"


def normalize_post_type(post: dict[str, Any]) -> str:
    raw_type = str(post.get("type") or "").lower()
    product_type = str(post.get("productType") or post.get("product_type") or "").lower()
    if "sidecar" in raw_type:
        return "carousel"
    if "video" in raw_type or product_type == "clips":
        return "reel"
    return "image"


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


def compute_metrics(profile: dict[str, Any], history_depth: int) -> Metrics:
    followers = max(profile["followers"], 1)
    posts = profile["latest_posts"][:12]
    engagements: list[float] = []
    likes: list[int] = []
    comments: list[int] = []
    views: list[int] = []
    post_dates: list[datetime] = []
    content_counts: Counter[str] = Counter()

    for post in posts:
        like_count = safe_int(post.get("like_count", post.get("likesCount")))
        comment_count = safe_int(post.get("comment_count", post.get("commentsCount")))
        view_count = safe_int(post.get("videoViewCount", post.get("video_view_count")))
        likes.append(like_count)
        comments.append(comment_count)
        views.append(view_count)
        engagements.append(((like_count + comment_count) / followers) * 100)
        content_counts[normalize_post_type(post)] += 1
        taken_at = parse_timestamp(post.get("taken_at_timestamp", post.get("timestamp")))
        if taken_at:
            post_dates.append(taken_at)

    recent_posts_used = len(posts)
    avg_likes = round(sum(likes) / len(likes)) if likes else 0
    avg_comments = round(sum(comments) / len(comments)) if comments else 0
    avg_views = round(sum(v for v in views if v > 0) / max(1, sum(1 for v in views if v > 0))) if any(views) else 0

    median_er = round(statistics.median(engagements), 2) if engagements else 0.0
    trimmed_er = round(trimmed_mean(engagements), 2) if engagements else 0.0
    if engagements:
        weights = list(range(len(engagements), 0, -1))
        weighted_recent_er = round(sum(value * weight for value, weight in zip(engagements, weights)) / sum(weights), 2)
    else:
        weighted_recent_er = 0.0
    representative_er = round((median_er * 0.45) + (trimmed_er * 0.35) + (weighted_recent_er * 0.20), 2)

    archetype = determine_profile_archetype(profile)
    account_tier = determine_account_tier(profile["followers"])
    benchmark_er = BENCHMARK_ERS[archetype][account_tier]
    benchmark_ratio = round((representative_er / benchmark_er) if benchmark_er else 0.0, 2)

    now = datetime.now(timezone.utc)
    recent_posts = [dt for dt in post_dates if (now - dt).days <= 30]
    posting_frequency_per_week = round((len(recent_posts) / 30) * 7, 2) if recent_posts else 0.0
    target_frequency = TARGET_WEEKLY_POSTS[archetype]
    posting_frequency_score = clamp((posting_frequency_per_week / target_frequency) * 100, 15, 100) if post_dates else 15

    consistency_core = 40.0
    if len(post_dates) >= 3:
        sorted_dates = sorted(post_dates, reverse=True)
        gaps = [abs((first - second).total_seconds()) / 86400 for first, second in zip(sorted_dates, sorted_dates[1:])]
        if gaps:
            mean_gap = statistics.mean(gaps)
            stdev_gap = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0
            regularity = max(0.0, 100 - (stdev_gap * 12))
            cadence = max(0.0, 100 - abs(mean_gap - (7 / max(target_frequency, 1))) * 18)
            consistency_core = (regularity * 0.6) + (cadence * 0.4)
    consistency = round(clamp((consistency_core * 0.7) + (posting_frequency_score * 0.3), 0, 100))

    following_base = max(profile["following"], 1)
    ratio = profile["followers"] / following_base
    ratio_score = clamp((math.log10(max(ratio, 1.2)) / math.log10(60)) * 100, 8, 100)

    total_interactions = sum(likes) + sum(comments)
    comment_rate = round((sum(comments) / max(total_interactions, 1)) * 100, 2)
    expected_comment_rate = EXPECTED_COMMENT_RATES[archetype]
    comment_score = clamp((comment_rate / expected_comment_rate) * 100, 10, 100)

    engagement_score = clamp(benchmark_ratio * 75, 5, 100)
    mean_er = statistics.mean(engagements) if engagements else 0.0
    coefficient_variation = (statistics.pstdev(engagements) / mean_er) if engagements and mean_er > 0 else 0.0
    top_to_median = (max(engagements) / max(median_er, 0.05)) if engagements else 0.0
    volatility_penalty = clamp(max(0.0, coefficient_variation - 0.7) * 28 + max(0.0, top_to_median - 3.0) * 8, 0, 35)

    profile_completeness = 0
    profile_completeness += 20 if profile["biography"] else 0
    profile_completeness += 20 if profile["full_name"] and profile["full_name"] != profile["username"] else 0
    profile_completeness += 20 if profile["category_name"] else 0
    profile_completeness += 20 if profile["external_url"] else 0
    profile_completeness += 20 if profile["post_count"] > 0 else 0
    verification_bonus = 6 if profile["is_verified"] else 0
    professional_bonus = 4 if profile["is_business_account"] or profile["is_professional_account"] else 0

    audience_quality = round(
        clamp(
            (ratio_score * 0.28)
            + (comment_score * 0.24)
            + (consistency * 0.16)
            + (engagement_score * 0.22)
            + (profile_completeness * 0.10)
            + verification_bonus
            + professional_bonus
            - (volatility_penalty * 0.35),
            6,
            98,
        )
    )

    authenticity_risk = round(
        clamp(
            100
            - (
                (comment_score * 0.26)
                + (min(ratio_score, 90) * 0.14)
                + (consistency * 0.20)
                + (min(engagement_score, 100) * 0.20)
                + (profile_completeness * 0.12)
            )
            + volatility_penalty,
            4,
            96,
        )
    )

    coverage_score = min((recent_posts_used / 12) * 100, 100) if recent_posts_used else 0
    date_coverage_score = min((len(post_dates) / max(recent_posts_used, 1)) * 100, 100)
    history_score = min(history_depth * 20, 100)
    confidence = round(
        clamp(
            (coverage_score * 0.35)
            + (date_coverage_score * 0.20)
            + (history_score * 0.20)
            + (profile_completeness * 0.25),
            20,
            98,
        )
    )

    overall_score = round(
        clamp(
            (engagement_score * 0.34)
            + (audience_quality * 0.24)
            + ((100 - authenticity_risk) * 0.16)
            + (consistency * 0.16)
            + (confidence * 0.10),
            0,
            100,
        )
    )

    total_posts = max(recent_posts_used, 1)
    reels_share = round((content_counts["reel"] / total_posts) * 100)
    carousel_share = round((content_counts["carousel"] / total_posts) * 100)
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


def json_response(handler: "AppHandler", status: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(raw)


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/profile-image"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/profile-image":
            self.handle_profile_image_proxy(parsed.query)
            return

        if parsed.path in ("/", "/index.html", "/asdfadsf.html"):
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", "/veridia-ajans.html")
            self.end_headers()
            return

        super().do_GET()

    def handle_profile_image_proxy(self, query: str) -> None:
        params = parse_qs(query)
        src = (params.get("src") or [""])[0]
        if not src:
            self.send_error(HTTPStatus.BAD_REQUEST, "Image source is required.")
            return

        host = (urlparse(src).hostname or "").lower()
        allowed_hosts = ("cdninstagram.com", "fbcdn.net")
        if not any(host.endswith(allowed) for allowed in allowed_hosts):
            self.send_error(HTTPStatus.BAD_REQUEST, "Desteklenmeyen görsel kaynağı.")
            return

        try:
            body, content_type = fetch_binary_url(src)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
        except error.HTTPError as exc:
            self.send_error(exc.code, "Upstream image fetch failed.")
        except error.URLError as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, f"Image proxy failed: {exc.reason}")

    def do_POST(self) -> None:
        if self.path != "/api/analyze-instagram":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            username = str(payload.get("username", "")).strip().lstrip("@")
            if not username:
                raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Instagram kullanici adi gerekli.")
            if not username.replace(".", "").replace("_", "").isalnum():
                raise AnalyzeError(HTTPStatus.BAD_REQUEST, "Gecersiz Instagram kullanici adi.")
            result = build_analysis(username)
            json_response(self, HTTPStatus.OK, {"ok": True, "data": result})
        except AnalyzeError as exc:
            json_response(self, exc.status, {"ok": False, "error": exc.message})
        except json.JSONDecodeError:
            json_response(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Geçersiz JSON gönderildi."})
        except Exception as exc:  # noqa: BLE001
            json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"Beklenmeyen hata: {exc}"})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Serving {ROOT} at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
