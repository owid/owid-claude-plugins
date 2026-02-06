---
name: "sql-queries"
description: "Execute read-only SQL queries against the OWID public Datasette database. Use this for flexible data exploration, custom joins, filtering, and accessing the underlying variables, datasets, and entities tables directly."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
---

OWID provides a public Datasette instance that allows read-only SQL queries against the database. This gives you flexible access to:
- `variables` - All indicator/variable definitions
- `datasets` - Dataset metadata
- `entities` - Countries, regions, and other entities
- `posts_gdocs` - Article content and metadata

## Executing SQL Queries

Use the Datasette JSON API:

```bash
# Basic query
curl -s "https://owid.cloud/owid.json?sql=SELECT+id,name+FROM+variables+WHERE+name+LIKE+'%25population%25'+LIMIT+10" | jq

# URL-encode complex queries
curl -s "https://owid.cloud/owid.json?sql=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("SELECT id, name FROM variables WHERE name LIKE \"%coal%\" LIMIT 10"))')" | jq
```

## Important Constraints

1. **SELECT only** - Only SELECT statements are allowed. No INSERT, UPDATE, DELETE.
2. **Row limits** - Queries are capped at 5000 rows max. Always include LIMIT.
3. **Column names** - OWID column names often use double underscores (`__`), not single (`_`).

## Useful Tables

### variables
Contains indicator definitions:
```sql
SELECT id, name, description, unit, shortUnit, datasetId
FROM variables
WHERE name LIKE '%GDP%'
LIMIT 20
```

### datasets
Contains dataset metadata:
```sql
SELECT id, name, description, namespace, createdAt
FROM datasets
WHERE name LIKE '%World Bank%'
LIMIT 10
```

### entities
Contains countries and regions:
```sql
SELECT id, name, code
FROM entities
WHERE code IS NOT NULL
LIMIT 50
```

### posts_gdocs
Contains article content:
```sql
SELECT slug, content -> '$.title' as title, type
FROM posts_gdocs
WHERE type NOT IN ('fragment', 'about-page')
LIMIT 20
```

## Example Queries

Find indicators related to a concept:
```sql
SELECT id, name, description
FROM variables
WHERE name LIKE '%renewable energy%'
ORDER BY id DESC
LIMIT 10
```

Get dataset info for an indicator:
```sql
SELECT v.id, v.name, d.name as dataset_name
FROM variables v
JOIN datasets d ON v.datasetId = d.id
WHERE v.name LIKE '%emissions%'
LIMIT 10
```

List entities with ISO codes:
```sql
SELECT name, code
FROM entities
WHERE code IS NOT NULL AND LENGTH(code) = 3
LIMIT 100
```

## Error Handling

If a column doesn't exist, the API returns an error. Check available columns with:
```sql
SELECT * FROM variables LIMIT 1
```

Then inspect the returned column names before building complex queries.
