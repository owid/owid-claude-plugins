---
name: "posts"
description: "Search and fetch full markdown content of Our World In Data articles and data insights. Use this when you need article content, want to understand how OWID explains a topic, or need to reference OWID research."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
---

Our World In Data publishes articles explaining data topics in depth. You can search and fetch these articles programmatically.

## Searching for Posts

Use Algolia to search articles by title or content:

```bash
# Search for articles about a topic
curl -s -X POST "https://nlp7bk9r6k-dsn.algolia.net/1/indexes/*/queries" \
  -H "x-algolia-api-key: 1ac7be9b68e94c7aa78e99d9c96e95d5" \
  -H "x-algolia-application-id: NLP7BK9R6K" \
  -d '{
    "requests": [{
      "indexName": "pages",
      "query": "climate change",
      "hitsPerPage": 5
    }]
  }' | jq '.results[0].hits[] | {slug, title, type, excerpt}'
```

## Fetching Post Content

Once you have a slug, fetch the full markdown content via SQL:

```bash
# Fetch by slug
curl -s "https://owid.cloud/owid.json?sql=SELECT+slug,content->>'$.title'+as+title,markdown+FROM+posts_gdocs+WHERE+slug='poverty'+LIMIT+1" | jq
```

Or by Google Doc ID for internal references:
```bash
curl -s "https://owid.cloud/owid.json?sql=SELECT+slug,markdown+FROM+posts_gdocs+WHERE+id='DOC_ID_HERE'+LIMIT+1" | jq
```

## Post Types

OWID has several content types:
- **article** - Full research articles (e.g., `/poverty`)
- **data-insight** - Short data insights (URL: `/data-insights/{slug}`)
- **topic-page** - Topic overview pages
- **fragment** - Reusable content blocks (usually skip these)
- **about-page** - About pages (usually skip these)

## URL Construction

Build URLs based on post type:
- Regular posts: `https://ourworldindata.org/{slug}`
- Data insights: `https://ourworldindata.org/data-insights/{slug}`

## Example: Find and Read an Article

1. Search for relevant articles:
```bash
curl -s -X POST "https://nlp7bk9r6k-dsn.algolia.net/1/indexes/*/queries" \
  -H "x-algolia-api-key: 1ac7be9b68e94c7aa78e99d9c96e95d5" \
  -H "x-algolia-application-id: NLP7BK9R6K" \
  -d '{"requests": [{"indexName": "pages", "query": "life expectancy", "hitsPerPage": 3}]}' \
  | jq '.results[0].hits[] | {slug, title}'
```

2. Fetch the content:
```bash
curl -s "https://owid.cloud/owid.json?sql=SELECT+markdown+FROM+posts_gdocs+WHERE+slug='life-expectancy'+LIMIT+1" | jq -r '.rows[0][0]' | head -100
```

## When to Use Posts

| Use Posts | Use Charts/Indicators |
|-----------|----------------------|
| Understanding OWID methodology | Getting raw data |
| Citing OWID research | Data analysis |
| Learning about a topic | Building visualizations |
| Finding context for data | Programmatic data access |
