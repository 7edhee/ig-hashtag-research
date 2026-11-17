#!/usr/bin/env python3
"""Instagram hashtag research tool.

Works with a CSV containing hashtag metrics. It does not scrape Instagram.
Expected columns: hashtag, posts, engagement, trend, related_to
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Hashtag:
    hashtag: str
    posts: int
    engagement: float
    trend: float
    related_to: str = ""

    @property
    def normalized(self) -> str:
        value = self.hashtag.strip().lower()
        return value if value.startswith("#") else f"#{value}"


def parse_number(value: str) -> float:
    value = str(value).strip().lower().replace(",", "")
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    if value and value[-1] in multipliers:
        return float(value[:-1]) * multipliers[value[-1]]
    return float(value or 0)


def load_csv(path: Path) -> list[Hashtag]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"hashtag", "posts", "engagement", "trend"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        rows = []
        for row in reader:
            tag = row.get("hashtag", "").strip()
            if not tag:
                continue
            rows.append(Hashtag(tag, int(parse_number(row["posts"])), float(row["engagement"]), float(row["trend"]), row.get("related_to", "")))
        return rows


def tokens(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-z0-9]+", text.lower()) if len(x) > 2}


def score(tag: Hashtag, seed: str) -> tuple[float, str]:
    # Opportunity favors growing, engaged niches over extremely saturated tags.
    volume = min(100.0, (tag.posts / 500_000) ** 0.5 * 100) if tag.posts else 0
    saturation_penalty = min(35.0, (tag.posts / 10_000_000) ** 0.5 * 35) if tag.posts else 0
    engagement_score = min(100.0, max(0.0, tag.engagement) * 10)
    trend_score = min(100.0, max(0.0, tag.trend))
    relevance = 100.0 if seed.lower().strip("#") in tag.normalized else 0.0
    overlap = len(tokens(seed) & tokens(tag.normalized))
    relevance = max(relevance, min(100.0, overlap * 45.0))
    opportunity = 0.35 * engagement_score + 0.30 * trend_score + 0.20 * relevance + 0.15 * volume - saturation_penalty
    if opportunity >= 70:
        tier = "High opportunity"
    elif opportunity >= 45:
        tier = "Good test"
    else:
        tier = "Niche / experimental"
    return round(max(0.0, min(100.0, opportunity)), 1), tier


def research(rows: Iterable[Hashtag], seed: str, min_posts: int, max_posts: int, limit: int) -> list[dict]:
    seed_terms = tokens(seed)
    results = []
    for tag in rows:
        if not (min_posts <= tag.posts <= max_posts):
            continue
        haystack = f"{tag.normalized} {tag.related_to}".lower()
        if seed_terms and not any(term in haystack for term in seed_terms):
            continue
        opportunity, tier = score(tag, seed)
        results.append({"hashtag": tag.normalized, "posts": tag.posts, "engagement": tag.engagement, "trend": tag.trend, "related_to": tag.related_to, "opportunity": opportunity, "tier": tier})
    return sorted(results, key=lambda item: (-item["opportunity"], -item["trend"], item["posts"]))[:limit]


def write_csv(path: Path, results: list[dict]) -> None:
    fields = ["rank", "hashtag", "posts", "engagement", "trend", "opportunity", "tier", "related_to"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(results, 1):
            writer.writerow({"rank": rank, **row})


def write_html(path: Path, results: list[dict], seed: str) -> None:
    rows = "\n".join(
        f"<tr><td>{i}</td><td><strong>{html.escape(r['hashtag'])}</strong></td><td>{r['posts']:,}</td><td>{r['engagement']:.1f}%</td><td>{r['trend']:.1f}</td><td><b>{r['opportunity']:.1f}</b></td><td><span class='tier'>{html.escape(r['tier'])}</span></td></tr>"
        for i, r in enumerate(results, 1)
    )
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>Hashtag research: {html.escape(seed)}</title>
    <style>body{{font-family:system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;color:#172033;background:#f7f8fc}}.card{{background:white;border-radius:16px;padding:26px;box-shadow:0 8px 30px #17203312}}h1{{margin-top:0}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{padding:13px 10px;text-align:left;border-bottom:1px solid #e7e9ef}}th{{color:#667085;font-size:12px;text-transform:uppercase}}.tier{{background:#eef4ff;border-radius:999px;padding:5px 9px;font-size:12px}}.note{{color:#667085;font-size:14px}}</style></head>
    <body><div class='card'><h1>Instagram hashtag research</h1><p class='note'>Seed: <b>{html.escape(seed)}</b> · Ranked by opportunity score</p><table><thead><tr><th>#</th><th>Hashtag</th><th>Posts</th><th>Engagement</th><th>Trend</th><th>Score</th><th>Recommendation</th></tr></thead><tbody>{rows}</tbody></table><p class='note'>Scores are directional, not Instagram guarantees. Refresh your metrics regularly.</p></div></body></html>"""
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research and rank Instagram hashtags from a metrics CSV.")
    parser.add_argument("seed", help="Topic or seed hashtag, e.g. 'street photography'")
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("sample_hashtags.csv"), help="Input CSV with hashtag metrics")
    parser.add_argument("--min-posts", type=int, default=1_000, help="Minimum post count")
    parser.add_argument("--max-posts", type=int, default=5_000_000, help="Maximum post count")
    parser.add_argument("--limit", type=int, default=30, help="Number of results")
    parser.add_argument("--output", type=Path, default=Path("hashtag_results.csv"), help="CSV output path")
    parser.add_argument("--html", type=Path, default=Path("hashtag_results.html"), help="HTML report path")
    args = parser.parse_args()

    try:
        rows = load_csv(args.data)
        results = research(rows, args.seed, args.min_posts, args.max_posts, args.limit)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if not results:
        print("No matching hashtags. Try a broader seed or wider post-count range.")
        return 0
    write_csv(args.output, results)
    write_html(args.html, results, args.seed)
    print(f"Found {len(results)} hashtags for '{args.seed}'\n")
    print(f"{'#':>3}  {'HASHTAG':<28} {'POSTS':>12} {'ENG%':>6} {'TREND':>6} {'SCORE':>6}  TIER")
    print("-" * 80)
    for i, row in enumerate(results, 1):
        print(f"{i:>3}  {row['hashtag']:<28} {row['posts']:>12,} {row['engagement']:>6.1f} {row['trend']:>6.1f} {row['opportunity']:>6.1f}  {row['tier']}")
    print(f"\nSaved: {args.output} and {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
