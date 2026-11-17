# Instagram Hashtag Research Tool

A standalone Python program that ranks Instagram hashtags by estimated opportunity using engagement, trend, relevance, post volume, and saturation.

## Run

```bash
python3 hashtag_research.py "street photography"
```

The program creates `hashtag_results.csv` and `hashtag_results.html` in the current directory.

## Use your own data

Pass an authorized CSV file with these columns:

```text
hashtag,posts,engagement,trend,related_to
```

Example:

```bash
python3 hashtag_research.py "fitness" --data metrics.csv
```

The built-in data is only demo data. The program does not scrape Instagram. Use data from your own Insights export, an approved API, or a compliant analytics provider.

## Options

```text
--data PATH          Input metrics CSV
--min-posts NUMBER   Minimum post count
--max-posts NUMBER   Maximum post count
--limit NUMBER       Maximum number of results
--output PATH        CSV output path
--html PATH          HTML report path
```

Requires Python 3.9 or newer. No third-party packages are required.
