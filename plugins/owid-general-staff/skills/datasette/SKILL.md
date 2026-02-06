---
description: Access Our World In Data's internal datasette instance to query data from our main MySQL database mirror and analytics data store. Use this when you need to look up or explore data from our internal infrastructure. Does not contain any timeseries data i.e. this does not help to answer questions about data like "what is the life expectancy in Nigeria?". Instead, it is useful for questions like "how many published charts do we have?" or "get the title for all views for a multidim".
allowed-tools:
  - "Bash(curl:*)"
---

# Querying OWID's internal Datasette instance

Our World In Data runs an internal [Datasette](https://datasette.io/) instance that mirrors data from two sources:

1. **Main MySQL database** — contains our catalog of charts, variables, datasets, sources, and other metadata used by the OWID website and data pipeline.
2. **Analytics data store** — contains page view and usage analytics data.

## Access

The datasette instance is available via tailscale at:

```
http://analytics/
```

No API keys or tokens are needed — access is controlled at the network level.

## Available databases

- `private` — mirror of the main MySQL database (charts, variables, datasets, entities, etc.)
- `analytics` — page view and usage analytics

## URL structure

Datasette URLs follow this hierarchy:

```
/                           -> List all databases
/{database}                 -> Database overview (list tables)
/{database}/{table}         -> Browse rows of a table
/{database}/{table}/{pk}    -> Individual row by primary key
/{database}.json?sql=...    -> Run arbitrary SQL as JSON. Our datasette instance uses duckdb, which is very similar to PostgreSQL.
/{database}.csv?sql=...     -> Run arbitrary SQL as CSV
```

### Tilde escaping

Datasette uses tilde encoding (not percent-encoding) for special characters in database/table names within URL paths. Allowed characters that need no encoding: `A-Z a-z 0-9 _ -`. Spaces are encoded as `+`. Everything else uses `~` followed by a two-digit hex code (e.g. `.` becomes `~2E`, `/` becomes `~2F`).

## IMPORTANT: Always retrieve metadata before writing queries

Before constructing any SQL query against a database, you **must** first retrieve the table and column metadata so you know what tables exist and what columns they have. Do not guess at table or column names.

### Step 1: Get the list of tables with columns, primary keys, and foreign keys

```bash
curl -s "http://analytics/private.json"
```

This returns a JSON object with a `tables` array. Each entry includes:
- `name` — table name
- `columns` — list of column names
- `primary_keys` — list of primary key columns
- `count` — row count
- `foreign_keys` — incoming and outgoing foreign key relationships

### Step 2: Get column types

To get the `CREATE TABLE` statement for a specific table, query `sqlite_master`:

```bash
curl -s -G "http://analytics/private.json" \
  --data-urlencode "sql=SELECT sql FROM sqlite_master WHERE name = 'charts'" \
  --data-urlencode "_shape=array"
```

To get all column names and types for a table, you can also use `information_schema`:

```bash
curl -s -G "http://analytics/private.json" \
  --data-urlencode "sql=SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name = 'charts'" \
  --data-urlencode "_shape=array"
```

### Step 3: Check for human-readable descriptions

```bash
curl -s "http://analytics/-/metadata.json"
```

This returns descriptions for databases, tables, and individual columns.

## Running SQL queries

### JSON output

Append `.json` to the database name:

```bash
curl -s -G "http://analytics/private.json" \
  --data-urlencode "sql=SELECT * FROM charts LIMIT 5" \
  --data-urlencode "_shape=objects"
```

### CSV output

Append `.csv` instead:

```bash
curl -s -G "http://analytics/private.csv" \
  --data-urlencode "sql=SELECT * FROM charts LIMIT 5"
```

### JSON shape options

The `_shape` parameter controls how rows are formatted in JSON responses:

| Value        | Effect                                                    |
| ------------ | --------------------------------------------------------- |
| `objects`    | Rows as key/value objects (default and recommended)       |
| `arrays`     | Rows as arrays of values, no column keys                  |
| `array`      | Flat JSON array of objects, no wrapper metadata            |
| `arrayfirst` | Flat array of just the first column's values              |
| `object`     | Objects keyed by primary key                              |

### Browsing table data (no SQL needed)

You can also browse table data directly without writing SQL. Append `.json` or `.csv` to the table path:

```bash
# JSON
curl -s "http://analytics/private/charts.json?_size=5&_shape=objects"

# CSV
curl -s "http://analytics/private/charts.csv?_size=5"
```

Table endpoints support column filtering with `?column__operator=value` syntax:

```
?state__exact=CA
?planet_int__gt=1
?name__contains=energy
?id__in=1,2,3
```

## Useful query parameters

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
| `_header=off` | Omit CSV header row                                        |

## Tips

- Always use `curl -s -G` with `--data-urlencode` to safely pass SQL queries — this avoids manual URL-encoding.
- For large result sets, use `LIMIT` and `OFFSET` in your SQL to paginate, or use `_stream=on` with CSV output to get all rows at once.
- The datasette instance mirrors data periodically — it may not reflect the very latest changes to the production database.
- Only `SELECT` statements are allowed. `INSERT`, `UPDATE`, `DELETE`, and `PRAGMA` are rejected.
- Use `_size=max` to get up to 1000 rows in a single JSON response.
