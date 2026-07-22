---
name: "fact-check-article"
description: "Fact-check an article or blog post against Our World in Data. Given a URL, this skill downloads the article, finds statements that OWID data can verify or contextualize, checks each one against real chart data, and produces an annotated copy of the article with color-coded highlights and embedded interactive charts, opened in the user's browser. Use when the user asks to fact-check an article, asks 'what does OWID data say about this article/claim', or wants an article annotated with OWID charts."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
- "Bash(uv run:*)"
- "Bash(open:*)"
---

Fact-check an article against Our World in Data and produce an annotated HTML copy. The helper script `scripts/annotate_article.py` (referenced below as `$SKILL_DIR/scripts/annotate_article.py`, run it with `uv run`) does the deterministic HTML work — text extraction and highlight/chart injection. Your job is the judgment: picking statements and verdicts.

Work in a scratch directory. The final annotated HTML is the only output the user needs; save it wherever the user expects outputs.

## Step 1: Download the article

```bash
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" "$ARTICLE_URL" -o article.html
```

Then extract its readable text:

```bash
uv run $SKILL_DIR/scripts/annotate_article.py extract article.html > article.txt
```

Read `article.txt` and sanity-check that it contains the full article body. If it is empty or truncated (paywalled or JS-rendered site), tell the user and ask them to save the page from their browser (File → Save Page As) and give you the file.

## Step 2: Select statements to check

Read the article text and pick statements worth checking — quantitative or factual claims that OWID data could plausibly verify (population, health, demography, economy, energy, environment, technology adoption, violence, education, ...). Prefer:

- claims with concrete numbers or magnitudes ("doubled", "half of Americans", "grew by a third")
- claims central to the article's argument
- a manageable number: ~8-15 for a long article, fewer for a short one

The user may steer the selection ("check the claims about energy") — follow their prompt. Skip claims about things OWID clearly doesn't cover (individual people, single events, prices of specific goods).

For each statement record the **exact quote** — it must be a verbatim substring of the `extract` output (the annotate step locates quotes by exact match after whitespace/typography normalization, so copy from `article.txt`, not from the raw HTML). Keep quotes to one sentence or clause; don't span paragraph breaks.

## Step 3: Verify each statement (parallel subagents)

Spawn one subagent per statement, in parallel, using the Task/Agent tool. If subagents are unavailable, verify sequentially yourself. Give each subagent a self-contained prompt:

```
You are verifying a claim from an article against Our World in Data (OWID).

CLAIM: "<the quote>"
INTERPRETATION: <one sentence: what exactly to check, incl. country and time period>

How to check:
1. Search OWID charts: curl -s "https://ourworldindata.org/api/search?q=<terms>&hitsPerPage=8" | jq '.results[] | {title, subtitle, url}'
   Keyword search (Algolia) — use topic-specialist vocabulary ("homicide rate" not
   "people murdered"). Refine or try synonyms if the top hits don't match.
   Never dump the raw response into context; always filter with jq.
2. Fetch the chart's metadata, then data:
   curl -s "$CHARTURL.metadata.json" | jq '{title: .chart.title, columns: [.columns[] | {titleShort, unit, timespan}]}'
   curl -s "$CHARTURL.csv?csvType=filtered&country=USA&time=1900..1940" -o /tmp/fc.csv
   Adjust country/time filters to the claim; inspect the file with head/grep/awk.
3. Judge the claim against the actual numbers.

Verdict options: "supported" (data clearly backs it), "contradicted" (data clearly
disagrees), "mixed" (partially right, e.g. right direction wrong magnitude),
"context" (data can't directly verify the claim but adds relevant context),
"no-data" (OWID has nothing relevant).

For chart_url, use the chart page URL with query params so it opens showing the
relevant view: ?country=~USA&time=1850..1930&tab=line (single entity selection is
country=~USA; multiple joined with ~; tab: line/map/table).

Your final message must be ONLY a JSON object, no markdown fences:
{"verdict": "...", "note": "1-3 sentences citing the actual numbers from OWID data and how they compare to the claim", "chart_url": "...", "chart_title": "..."}
```

The search-charts and fetch-chart-data skills document these endpoints in more detail if you need them.

## Step 4: Build the annotations file

Collect the subagent results into `annotations.json`. Drop `no-data` results (or keep the statement out entirely). Double-check that each `note` cites concrete numbers — a verdict without numbers is not a fact-check.

```json
{
  "source_url": "https://example.com/article",
  "annotations": [
    {
      "quote": "exact text copied from article.txt",
      "verdict": "supported",
      "note": "OWID data shows X was 39.4 years in 1850 and 57.1 in 1926, a 45% increase — close to the claimed 50%.",
      "chart_url": "https://ourworldindata.org/grapher/life-expectancy?country=~USA&time=1850..1930",
      "chart_title": "Life expectancy at birth"
    }
  ]
}
```

Verdicts map to colors: `supported` green, `contradicted` red, `mixed` yellow, `context` blue.

## Step 5: Annotate and open

```bash
uv run $SKILL_DIR/scripts/annotate_article.py annotate article.html annotations.json -o article-annotated.html
```

The script strips all `<script>` tags (so the page can't re-hydrate over the annotations), highlights each quote, inserts an annotation card with the verdict, note, and an embedded interactive OWID chart after the containing paragraph, and prepends a summary banner linking to all annotations.

It prints `N/M quotes matched` to stderr and warns about quotes it could not locate — fix those quotes (re-copy them from `article.txt`) and re-run rather than shipping unmatched annotations.

Open the result in the user's browser:

```bash
open article-annotated.html          # macOS
# xdg-open on Linux
```

Finally, summarize the verdicts in chat (one line per statement) and remind the user that verdicts are AI-generated and worth spot-checking before citing.
