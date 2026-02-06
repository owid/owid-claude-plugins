---
name: "sql-queries"
description: "Execute read-only SQL queries against the OWID public Datasette database. Use this for flexible data exploration, custom joins, filtering, and accessing the underlying variables, datasets, charts, and entities tables directly."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
---

OWID provides a public Datasette instance at `https://datasette-public.owid.io/` that allows read-only SQL queries against the database. This gives you flexible access to metadata about indicators, datasets, charts, entities, articles, and more.

## Executing SQL Queries

Use the Datasette JSON API. Always add `_shape=array` for clean JSON output:

```bash
# Basic query — _shape=array returns a plain JSON array of objects
curl -s "https://datasette-public.owid.io/owid.json?sql=SELECT+id,name+FROM+variables+WHERE+name+LIKE+'%25population%25'+LIMIT+10&_shape=array" | jq

# URL-encode complex queries with python
curl -s "https://datasette-public.owid.io/owid.json?_shape=array&sql=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("SELECT id, name FROM variables WHERE name LIKE \"%coal%\" LIMIT 10"))')" | jq
```

## Important Constraints

1. **SELECT only** — only SELECT statements are allowed.
2. **Row limit is 1000** — the server caps results at 1000 rows regardless of your LIMIT. If the response includes `"truncated": true`, your results were cut off. Use more specific WHERE clauses to narrow results.
3. **Always use `_shape=array`** — without it, the response is a dict with `columns` and `rows` arrays (harder to parse). With `_shape=array` you get `[{col: val, ...}, ...]`.

## Key Tables

### variables (630k+ rows)
Indicator/variable definitions. This is the most important table for finding data.

Key columns: `id`, `name`, `shortName`, `catalogPath`, `description`, `descriptionShort`, `unit`, `shortUnit`, `datasetId`, `titlePublic`

```sql
SELECT id, name, shortName, unit, catalogPath
FROM variables
WHERE name LIKE '%GDP%'
LIMIT 20
```

The `catalogPath` is useful for identifying the ETL source, e.g. `grapher/wb/2024-01-22/world_bank_wdi/world_bank_wdi#ny_gdp_pcap_pp_kd`.

### datasets
Dataset metadata grouping variables.

Key columns: `id`, `name`, `namespace`, `shortName`, `catalogPath`, `version`

```sql
SELECT id, name, namespace, shortName
FROM datasets
WHERE name LIKE '%World Bank%'
LIMIT 10
```

### charts
Published chart configurations.

Key columns: `id`, `title`, `slug`, `type`, `subtitle`, `isPublished`

```sql
SELECT id, title, slug, type
FROM charts
WHERE title LIKE '%life expectancy%' AND isPublished = 1
LIMIT 10
```

The chart URL is `https://ourworldindata.org/grapher/{slug}`.

### chart_dimensions
Links charts to variables. Use this to find which charts use a given variable or which variables power a chart.

Key columns: `chartId`, `variableId`, `property`, `order`

```sql
-- Find all charts using a specific variable
SELECT c.title, c.slug, c.type
FROM charts c
JOIN chart_dimensions cd ON c.id = cd.chartId
WHERE cd.variableId = 123 AND c.isPublished = 1
```

### entities
Countries, regions, and other entities.

Key columns: `id`, `name`, `code`

```sql
SELECT id, name, code
FROM entities
WHERE code IS NOT NULL AND LENGTH(code) = 3
LIMIT 50
```

### posts_gdocs
Article content and metadata.

Key columns: `id`, `slug`, `title`, `type`, `published`, `publishedAt`, `content`

```sql
SELECT slug, title, type, publishedAt
FROM posts_gdocs
WHERE published = 1 AND type = 'topic-page'
LIMIT 20
```

Types include: `topic-page`, `data-insight`, `article`, `author`, `fragment`, `about-page`.

### tags
Topic tags used to categorize charts and articles.

Key columns: `id`, `name`, `slug`

## Example Queries

Find indicators related to a concept:
```sql
SELECT id, name, unit, catalogPath
FROM variables
WHERE name LIKE '%renewable energy%'
ORDER BY id DESC
LIMIT 10
```

Find which variables power a chart by slug:
```sql
SELECT v.id, v.name, v.unit
FROM variables v
JOIN chart_dimensions cd ON v.id = cd.variableId
JOIN charts c ON cd.chartId = c.id
WHERE c.slug = 'life-expectancy'
```

Search charts by topic and find their variables:
```sql
SELECT c.title, c.slug, v.name as indicator
FROM charts c
JOIN chart_dimensions cd ON c.id = cd.chartId
JOIN variables v ON cd.variableId = v.id
WHERE c.title LIKE '%poverty%' AND c.isPublished = 1
LIMIT 20
```

## Error Handling

If a column doesn't exist, the API returns a JSON error. Discover available columns with:
```bash
curl -s "https://datasette-public.owid.io/owid.json?sql=SELECT+*+FROM+variables+LIMIT+1&_shape=array" | jq '.[0] | keys'
```
