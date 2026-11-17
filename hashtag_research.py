#!/usr/bin/env python3
"""Standalone Instagram hashtag research tool.

Uses embedded demo data by default. For real research, pass an authorized
metrics CSV with --data. The tool does not scrape Instagram.
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hashtag:
    hashtag: str
    posts: int
    engagement: float
    trend: float
    related_to: str = ""

    @property
    def normalized(self) -> str:
        tag = self.hashtag.strip().lower()
        return tag if tag.startswith("#") else f"#{tag}"


DEMO_DATA = [
    Hashtag("streetphotography", 4_800_000, 6.2, 54, "street photography"),
    Hashtag("streetphotograph", 1_200_000, 8.1, 72, "street photography"),
    Hashtag("urbanphotography", 3_500_000, 5.9, 61, "street photography"),
    Hashtag("urbanphotographer", 420_000, 9.4, 78, "street photography"),
    Hashtag("cityphotography", 980_000, 7.8, 68, "street photography"),
    Hashtag("nightstreetphotography", 185_000, 10.2, 88, "street photography"),
    Hashtag("streetphotoart", 74_000, 12.5, 91, "street photography"),
    Hashtag("streetportrait", 215_000, 8.8, 76, "street photography"),
    Hashtag("photowalk", 390_000, 9.1, 83, "street photography"),
    Hashtag("minimalstreet", 28_000, 14.3, 95, "street photography"),
    Hashtag("travelphotography", 9_800_000, 4.2, 39, "travel photography"),
    Hashtag("mobilephotography", 2_700_000, 5.4, 48, "photography"),
]


def number(value: str) -> float:
    text = str(value).strip().lower().replace(",", "")
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    if text and text[-1] in multipliers:
        return float(text[:-1]) * multipliers[text[-1]]
    return float(text or 0)


def load_csv(path: Path) -> list[Hashtag]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"hashtag", "posts", "engagement", "trend"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
        return [
            Hashtag(row["hashtag"], int(number(row["posts"])), float(row["engagement"]), float(row["trend"]), row.get("related_to", ""))
            for row in reader if row.get("hashtag", "").strip()
        ]


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


def rank_tag(tag: Hashtag, seed: str) -> tuple[float, str]:
    volume = min(100, (tag.posts / 500_000) ** 0.5 * 100) if tag.posts else 0
    saturation = min(35, (tag.posts / 10_000_000) ** 0.5 * 35) if tag.posts else 0
    engagement = min(100, max(0, tag.engagement) * 10)
    trend = min(100, max(0, tag.trend))
    overlap = len(words(seed) & words(f"{tag.normalized} {tag.related_to}"))
    relevance = min(100, overlap * 45)
    opportunity = 0.35 * engagement + 0.30 * trend + 0.20 * relevance + 0.15 * volume - saturation
    tier = "High opportunity" if opportunity >= 70 else "Good test" if opportunity >= 45 else "Niche / experimental"
    return round(max(0, min(100, opportunity)), 1), tier


def research(data: list[Hashtag], seed: str, minimum: int, maximum: int, limit: int) -> list[dict]:
    seed_words = words(seed)
    results = []
    for tag in data:
        searchable = f"{tag.normalized} {tag.related_to}".lower()
        if minimum <= tag.posts <= maximum and (not seed_words or any(word in searchable for word in seed_words)):
            opportunity, tier = rank_tag(tag, seed)
            results.append({"hashtag": tag.normalized, "posts": tag.posts, "engagement": tag.engagement, "trend": tag.trend, "opportunity": opportunity, "tier": tier, "related_to": tag.related_to})
    return sorted(results, key=lambda row: (-row["opportunity"], -row["trend"], row["posts"]))[:limit]


def save_csv(path: Path, results: list[dict]) -> None:
    fields = ["rank", "hashtag", "posts", "engagement", "trend", "opportunity", "tier", "related_to"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(results, 1):
            writer.writerow({"rank": rank, **row})


def save_html(path: Path, results: list[dict], seed: str) -> None:
    rows = "".join(f"<tr><td>{i}</td><td><b>{html.escape(row['hashtag'])}</b></td><td>{row['posts']:,}</td><td>{row['engagement']:.1f}%</td><td>{row['trend']:.1f}</td><td>{row['opportunity']:.1f}</td><td>{html.escape(row['tier'])}</td></tr>" for i, row in enumerate(results, 1))
    page = f"<!doctype html><meta charset='utf-8'><title>Hashtag research</title><style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}th{{font-size:12px;text-transform:uppercase}}</style><h1>Hashtag research: {html.escape(seed)}</h1><table><tr><th>#</th><th>Hashtag</th><th>Posts</th><th>Engagement</th><th>Trend</th><th>Score</th><th>Tier</th></tr>{rows}</table>"
    path.write_text(page, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank Instagram hashtags by opportunity.")
    parser.add_argument("seed", help="Topic or seed hashtag, for example: street photography")
    parser.add_argument("--data", type=Path, help="Optional authorized CSV: hashtag,posts,engagement,trend,related_to")
    parser.add_argument("--min-posts", type=int, default=1_000)
    parser.add_argument("--max-posts", type=int, default=5_000_000)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--csv", "--output", dest="csv_path", type=Path, default=Path("hashtag_results.csv"), help="Export ranked results to this CSV file")
    parser.add_argument("--html", type=Path, default=Path("hashtag_results.html"))
    args = parser.parse_args()

    try:
        data = load_csv(args.data) if args.data else DEMO_DATA
        results = research(data, args.seed, args.min_posts, args.max_posts, args.limit)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if not results:
        print("No matching hashtags. Try a broader topic or wider post-count range.")
        return 0

    save_csv(args.csv_path, results)
    save_html(args.html, results, args.seed)
    print(f"Found {len(results)} hashtags for '{args.seed}'\n")
    print(f"{'#':>3}  {'HASHTAG':<28} {'POSTS':>12} {'ENG%':>6} {'TREND':>6} {'SCORE':>6}  TIER")
    print("-" * 82)
    for index, row in enumerate(results, 1):
        print(f"{index:>3}  {row['hashtag']:<28} {row['posts']:>12,} {row['engagement']:>6.1f} {row['trend']:>6.1f} {row['opportunity']:>6.1f}  {row['tier']}")
    print(f"\nCSV exported to: {args.csv_path}")
    print(f"HTML report exported to: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
