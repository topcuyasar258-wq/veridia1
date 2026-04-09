#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error, request
import ssl

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

BENCHMARK_ERS = {
    "brand": {"nano": 4.4, "micro": 3.2, "mid": 2.4, "macro": 1.7, "mega": 1.2},
    "creator": {"nano": 5.8, "micro": 4.5, "mid": 3.3, "macro": 2.4, "mega": 1.6},
    "media": {"nano": 4.8, "micro": 3.7, "mid": 2.8, "macro": 2.0, "mega": 1.4},
}

EXPECTED_COMMENT_RATES = {"brand": 0.9, "creator": 1.2, "media": 1.0}
TARGET_WEEKLY_POSTS = {"brand": 3.5, "creator": 4.5, "media": 5.5}

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def trimmed_mean(values: list[float]) -> float:
    if not values: return 0.0
    if len(values) < 5: return statistics.mean(values)
    trim = max(1, round(len(values) * 0.15))
    sorted_values = sorted(values)
    if len(sorted_values) <= trim * 2: return statistics.mean(sorted_values)
    return statistics.mean(sorted_values[trim:-trim])

def safe_int(value: Any, default: int = 0) -> int:
    if value is None: return default
    if isinstance(value, bool): return int(value)
    if isinstance(value, (int, float)): return int(value)
    if isinstance(value, str):
        try: return int(float(value.replace(",", "").replace("_", "").strip()))
        except ValueError: return default
    return default

def parse_timestamp(value: Any) -> datetime | None:
    if value is None: return None
    if isinstance(value, (int, float)): return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try: return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except ValueError: pass
        try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError: pass
    return None

def normalize_post_type(post: dict[str, Any]) -> str:
    raw_type = str(post.get("type") or "").lower()
    product_type = str(post.get("productType") or post.get("product_type") or "").lower()
    if "sidecar" in raw_type: return "carousel"
    if "video" in raw_type or product_type == "clips": return "reel"
    return "image"

def determine_profile_archetype(profile: dict[str, Any]) -> str:
    haystack = " ".join([str(profile.get("category_name", "")), str(profile.get("biography", "")), str(profile.get("full_name", ""))]).lower()
    media_signals = ["news", "media", "magazine", "tv", "journal", "press"]
    if any(signal in haystack for signal in media_signals): return "media"
    if profile["is_business_account"] or profile["is_professional_account"] or profile.get("external_url"): return "brand"
    return "creator"

def determine_account_tier(followers: int) -> str:
    if followers < 10_000: return "nano"
    if followers < 100_000: return "micro"
    if followers < 500_000: return "mid"
    if followers < 2_000_000: return "macro"
    return "mega"

def compute_metrics(profile: dict[str, Any], history_depth: int) -> Metrics:
    # This matches the logic in server.py
    followers = max(profile["followers"], 1)
    posts = profile["latest_posts"][:12]
    engagements, likes, comments, views, post_dates = [], [], [], [], []
    content_counts: Counter[str] = Counter()

    for post in posts:
        l = safe_int(post.get("like_count", post.get("likesCount")))
        c = safe_int(post.get("comment_count", post.get("commentsCount")))
        v = safe_int(post.get("videoViewCount", post.get("video_view_count")))
        likes.append(l); comments.append(c); views.append(v)
        engagements.append(((l + c) / followers) * 100)
        content_counts[normalize_post_type(post)] += 1
        t = parse_timestamp(post.get("taken_at_timestamp", post.get("timestamp")))
        if t: post_dates.append(t)

    recent_posts_used = len(posts)
    avg_likes = round(sum(likes) / len(likes)) if likes else 0
    avg_comments = round(sum(comments) / len(comments)) if comments else 0
    avg_views = round(sum(v for v in views if v > 0) / max(1, sum(1 for v in views if v > 0))) if any(views) else 0

    median_er = round(statistics.median(engagements), 2) if engagements else 0.0
    trimmed_er = round(trimmed_mean(engagements), 2) if engagements else 0.0
    if engagements:
        weights = list(range(len(engagements), 0, -1))
        weighted_recent_er = round(sum(v * w for v, w in zip(engagements, weights)) / sum(weights), 2)
    else:
        weighted_recent_er = 0.0
    representative_er = round((median_er * 0.45) + (trimmed_er * 0.35) + (weighted_recent_er * 0.20), 2)

    archetype = determine_profile_archetype(profile)
    account_tier = determine_account_tier(profile["followers"])
    benchmark_er = BENCHMARK_ERS[archetype][account_tier]
    benchmark_ratio = round((representative_er / benchmark_er) if benchmark_er else 0.0, 2)

    now = datetime.now(timezone.utc)
    recent_posts = [dt for dt in post_dates if (now - dt).days <= 30]
    pf_per_week = round((len(recent_posts) / 30) * 7, 2) if recent_posts else 0.0
    target_frequency = TARGET_WEEKLY_POSTS[archetype]
    pf_score = clamp((pf_per_week / target_frequency) * 100, 15, 100) if post_dates else 15

    consistency_core = 40.0
    if len(post_dates) >= 3:
        sorted_dates = sorted(post_dates, reverse=True)
        gaps = [abs((f - s).total_seconds()) / 86400 for f, s in zip(sorted_dates, sorted_dates[1:])]
        if gaps:
            mean_gap = statistics.mean(gaps)
            stdev_gap = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0
            regularity = max(0.0, 100 - (stdev_gap * 12))
            cadence = max(0.0, 100 - abs(mean_gap - (7 / max(target_frequency, 1))) * 18)
            consistency_core = (regularity * 0.6) + (cadence * 0.4)
    consistency = round(clamp((consistency_core * 0.7) + (pf_score * 0.3), 0, 100))

    ratio = profile["followers"] / max(profile["following"], 1)
    ratio_score = clamp((math.log10(max(ratio, 1.2)) / math.log10(60)) * 100, 8, 100)

    total_interactions = sum(likes) + sum(comments)
    comment_rate = round((sum(comments) / max(total_interactions, 1)) * 100, 2)
    comment_score = clamp((comment_rate / EXPECTED_COMMENT_RATES[archetype]) * 100, 10, 100)

    engagement_score = clamp(benchmark_ratio * 75, 5, 100)
    mean_er = statistics.mean(engagements) if engagements else 0.0
    cv = (statistics.pstdev(engagements) / mean_er) if engagements and mean_er > 0 else 0.0
    volatility_penalty = clamp(max(0.0, cv - 0.7) * 28 + max(0.0, (max(engagements)/max(median_er,0.05) if engagements else 0) - 3.0) * 8, 0, 35)

    pc = 0
    pc += 20 if profile["biography"] else 0
    pc += 20 if profile["full_name"] and profile["full_name"] != profile["username"] else 0
    pc += 20 if profile["category_name"] else 0
    pc += 20 if profile["external_url"] else 0
    pc += 20 if profile["post_count"] > 0 else 0

    audience_quality = round(clamp((ratio_score * 0.28) + (comment_score * 0.24) + (consistency * 0.16) + (engagement_score * 0.22) + (pc * 0.10) + (6 if profile["is_verified"] else 0) + (4 if profile["is_business_account"] or profile["is_professional_account"] else 0) - (volatility_penalty * 0.35), 6, 98))
    authenticity_risk = round(clamp(100 - ((comment_score * 0.26) + (min(ratio_score, 90) * 0.14) + (consistency * 0.20) + (min(engagement_score, 100) * 0.20) + (pc * 0.12)) + volatility_penalty, 4, 96))
    confidence = round(clamp((min((recent_posts_used/12)*100, 100) * 0.35) + (min((len(post_dates)/max(recent_posts_used, 1))*100, 100) * 0.20) + (min(history_depth*20, 100) * 0.20) + (pc * 0.25), 20, 98))
    overall_score = round(clamp((engagement_score * 0.34) + (audience_quality * 0.24) + ((100 - authenticity_risk) * 0.16) + (consistency * 0.16) + (confidence * 0.10), 0, 100))

    tp = max(recent_posts_used, 1)
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
        posting_frequency_per_week=pf_per_week,
        recent_posts_used=recent_posts_used,
        avg_likes=avg_likes,
        avg_comments=avg_comments,
        avg_views=avg_views,
        benchmark_er=benchmark_er,
        benchmark_ratio=benchmark_ratio,
        profile_type="", # Will be set in server.py
        profile_archetype=archetype,
        profile_archetype_label="", # Will be set in server.py
        account_tier=account_tier,
        account_tier_label="", # Will be set in server.py
        reels_share=round((content_counts["reel"] / tp) * 100),
        carousel_share=round((content_counts["carousel"] / tp) * 100),
        image_share=round((content_counts["image"] / tp) * 100),
        comment_rate=comment_rate
    )
