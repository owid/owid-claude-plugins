---
description: "Access Our World In Data's published datasets using the owid-catalog Python library. Provides a unified Python API for searching and fetching chart data, catalog tables, and indicators — returning enhanced pandas DataFrames with metadata. Use this as a Python-native alternative to the HTTP-based search-charts and fetch-chart-data skills."
allowed-tools:
- "Bash(uv:*)"
- "Bash(python:*)"
- "Read"
---

The `owid-catalog` library provides a unified Python API for discovering and loading OWID datasets. It supports three search kinds: **charts** (published visualizations), **tables** (catalog datasets), and **indicators** (semantic search via embeddings).

## Installation

```bash
uv pip install owid-catalog
```

## Quick Start

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["owid-catalog"]
# ///

from owid.catalog import fetch, search

# Fetch chart data by slug — returns a Table (enhanced DataFrame with metadata)
tb = fetch("life-expectancy")
print(tb.head().to_csv())

# Search for charts
results = search("population")
print(results.to_frame().to_csv())

# Fetch the top result
tb = results[0].fetch()
print(tb.head().to_csv())
```

Run with:
```bash
uv run --no-project script.py
```

## Important: LLM-Friendly Output

The default display of `ResponseSet` and `Table` objects uses rich formatting that is not readable in plain text output. Always convert to CSV or string:

```python
# Search results → CSV
results = search("gdp per capita")
print(results.to_frame().to_csv())

# Table data → CSV (first rows)
tb = fetch("life-expectancy")
print(tb.head(20).to_csv())

# Variable summary
print(tb.codebook)
```

## Charts API

Fetch data from any published OWID chart by slug or full URL:

```python
from owid.catalog import fetch, search

# By slug
tb = fetch("life-expectancy")

# By full URL
tb = fetch("https://ourworldindata.org/grapher/life-expectancy")

# Search charts (sorted by popularity)
results = search("child mortality")
print(results.to_frame().to_csv())  # see titles, slugs, URLs

# Fetch from search result
tb = results[0].fetch()
```

The `fetch()` function returns a `Table` object — an enhanced pandas DataFrame where each column carries metadata (unit, description, source, license). This is richer than the raw CSV from the fetch-chart-data skill.

## Tables API

Search the full OWID data catalog for tables by name, namespace, dataset, or version. This goes beyond published charts — it covers all datasets in the catalog.

```python
from owid.catalog import search

# Search tables with fuzzy matching (default)
results = search("population", kind="table")
print(results.to_frame().to_csv())

# Filter by data provider
results = search("wdi", kind="table", namespace="worldbank_wdi")

# Matching modes: "fuzzy" (default, typo-tolerant), "exact", "contains", "regex"
results = search("gdp.*capita", kind="table", match="regex")

# Keep only latest versions
results = search("population", kind="table", latest=True)

# Fetch by full catalog path
tb = fetch("garden/un/2024-07-12/un_wpp/population")

# Fetch a single indicator column
tb = fetch("garden/un/2024-07-12/un_wpp/population#population")
```

## Indicators API

Semantic search using vector embeddings — finds indicators by meaning, not just keywords:

```python
from owid.catalog import search

# Semantic search (uses embeddings from search.owid.io)
results = search("share of energy from renewable sources", kind="indicator")
print(results.to_frame().to_csv())

# Get all fields for deeper inspection
print(results.to_frame(all_fields=True).to_csv())

# Sort by relevance (default) or similarity
results = search("CO2 emissions per capita", kind="indicator", sort_by="relevance")

# Fetch indicator data
tb = results[0].fetch()        # single-column indicator
tb = results[0].fetch_table()  # full table containing the indicator
```

## Working with Results

### ResponseSet

Search results are returned as a `ResponseSet` container:

```python
results = search("gdp", kind="table")

# Index and iterate
first = results[0]
for r in results[:5]:
    print(r.title)

# Filter
filtered = results.filter(lambda r: "worldbank" in r.namespace)

# Sort
sorted_results = results.sort_by("popularity", reverse=True)

# Keep latest versions only
latest = results.latest()

# Convert to DataFrame for analysis
df = results.to_frame()
print(df.to_csv())

# Include all fields (more columns like type, slug, popularity, version)
df = results.to_frame(all_fields=True)
print(df.to_csv())

# Convert to list of dicts (useful for programmatic access)
records = results.to_dict()

# In Jupyter: switch display mode for richer output (human users only)
# "advanced" adds extra columns (type, slug, popularity, version) to the notebook display
results.set_ui_advanced()
results.set_ui_basic()     # default: shows title, description, URL
```

## Tips

**When to use owid-catalog vs search-charts / fetch-chart-data:**
- Use owid-catalog when working in Python, when you need column metadata (units, descriptions, sources), or when searching tables/indicators beyond published charts.
- Use the HTTP-based search-charts and fetch-chart-data skills for quick lookups without Python, or in language-agnostic workflows.

**Integration with owid-grapher-py (create-chart skill):**
```python
from owid.catalog import fetch
from owid.grapher import plot

tb = fetch("life-expectancy")
df = tb.reset_index()  # convert to plain DataFrame for plotting
chart = plot(df, y="life_expectancy", title="Life Expectancy", types=["line", "map"])
```

