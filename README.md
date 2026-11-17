# Instagram Hashtag Research Tool

A dependency-free Python command-line tool for ranking hashtags by **opportunity**. It filters hashtags by post volume and topic relevance, then combines engagement, trend, relevance, and saturation into a directional score.

## Important data note

The included `sample_hashtags.csv` is illustrative demo data so the program can run immediately. For real research, replace it with metrics from a source you are authorized to use, such as your own Instagram Insights export, a compliant analytics provider, or data obtained through an approved Instagram API workflow. This tool intentionally does not scrape Instagram or bypass access controls.

## Run it

```bash
cd /home/ubuntu/instagram_hashtag_research
python3 hashtag_research.py "street photography"
```

That prints a ranked table and creates:

- `hashtag_results.csv` — spreadsheet-friendly results
- `hashtag_results.html` — readable report that can be opened in a browser

Useful options:

```bash
python3 hashtag_research.py "fitness" \
  --data my_metrics.csv \
  --min-posts 5000 \
  --max-posts 1000000 \
  --limit 50 \
  --output fitness_results.csv \
  --html fitness_report.html
```

## Input CSV format

Required columns:

| Column | Meaning |
|---|---|
| `hashtag` | Tag with or without `#` |
| `posts` | Approximate number of posts; accepts values such as `1.2m` or `85k` |
| `engagement` | Engagement rate as a percentage, e.g. `8.4` |
| `trend` | Directional trend score from 0 to 100 |
| `related_to` | Optional topic/category text used for relevance filtering |

Example:

```csv
hashtag,posts,engagement,trend,related_to
portraitphotography,840000,7.6,68,portrait photography
creativeportrait,92000,11.2,84,portrait photography
```

## How the score works

The score is a prioritization aid, not a prediction of reach. It rewards engagement, trend momentum, and relevance while penalizing very large/saturated hashtags. A practical strategy is to choose a mix of high-opportunity niche tags, medium-volume tags, and a few broad tags, then compare the results against your own post Insights.

## Requirements

- Python 3.9+
- No third-party packages
