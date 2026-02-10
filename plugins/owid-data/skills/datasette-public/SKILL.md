---
name: "datasette-public"
description: "Query the OWID public Datasette database to explore metadata about indicators, datasets, charts, entities, and articles. Use this for flexible data exploration, custom joins, filtering, and accessing the underlying variables, datasets, charts, and entities tables directly."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
---

OWID provides a public Datasette instance at `https://datasette-public.owid.io/` that allows read-only SQL queries against a single database called `owid`.

## Executing SQL Queries

Always use `curl -s -G` with `--data-urlencode` to safely pass SQL — this avoids manual URL-encoding:

```bash
# JSON output — use _shape=array for a clean JSON array of objects
curl -s -G "https://datasette-public.owid.io/owid.json" \
  --data-urlencode "sql=SELECT id, name FROM variables WHERE name LIKE '%population%' LIMIT 10" \
  --data-urlencode "_shape=array" | jq

# CSV output
curl -s -G "https://datasette-public.owid.io/owid.csv" \
  --data-urlencode "sql=SELECT id, name FROM variables WHERE name LIKE '%population%' LIMIT 10"
```

## Important Constraints

1. **SELECT only** — only SELECT statements are allowed.
2. **Row limit is 1000** — the server caps results at 1000 rows regardless of your LIMIT. If the response includes `"truncated": true`, your results were cut off. Use more specific WHERE clauses to narrow results.

## JSON Shape Options

The `_shape` parameter controls how rows are formatted in JSON responses:

| Value        | Effect                                                    |
| ------------ | --------------------------------------------------------- |
| `array`      | Flat JSON array of objects, no wrapper metadata (recommended) |
| `objects`    | Rows as key/value objects with wrapper metadata            |
| `arrays`     | Rows as arrays of values, no column keys                  |
| `arrayfirst` | Flat array of just the first column's values              |
| `object`     | Objects keyed by primary key                              |

## Useful Query Parameters

| Parameter     | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `sql`         | The SQL query (use `--data-urlencode` to pass it safely)   |
| `_shape`      | JSON response shape (see above)                            |
| `_size`       | Rows per page (use `_size=max` for up to 1000)             |
| `_sort`       | Sort ascending by column                                   |
| `_sort_desc`  | Sort descending by column                                  |
| `_col`        | Include only this column (repeatable)                      |
| `_nocol`      | Exclude this column (repeatable)                           |
| `_where`      | Add a WHERE clause fragment                                |
| `_stream=on`  | Stream all rows (CSV only, up to 100MB)                    |

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
curl -s -G "https://datasette-public.owid.io/owid.json" \
  --data-urlencode "sql=SELECT * FROM variables LIMIT 1" \
  --data-urlencode "_shape=array" | jq '.[0] | keys'
```
