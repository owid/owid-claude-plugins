---
name: "owid-catalog"
description: "Access Our World In Data's published datasets using the owid-catalog Python library. Provides a unified Python API for searching and fetching chart data, catalog tables, and indicators — returning enhanced pandas DataFrames with metadata. Use this as a Python-native alternative to the HTTP-based search-charts and fetch-chart-data skills."
allowed-tools:
- "Bash(uv:*)"
- "Read"
---

The `owid-catalog` library provides a unified Python API for discovering and loading OWID datasets. It supports three search kinds: **charts** (published visualizations), **tables** (catalog datasets), and **indicators** (semantic search via embeddings).

Charts have the benefit that they are the most curated and well-documented uses of data - for answering questions about data, these are therefore often better than indicators. One chart can use a single indicator or multiple indicators.

Indicators gives access to our full catalog of timeseries data, with varying levels of curation. Indicators and tables are both structured according to our ETL paths, for example "garden/un/2024-07-12/un_wpp/population#population". The path fragments are:
- channel: top-level grouping / stage of curation
- namespace: often the data provider (who, un, wb), but sometimes a topic area when that’s more useful.
- version: the dataset “release” identifier. This is the date we released the dataset, not the source
- dataset: the dataset short name
- table: name of the table the indicator is part of
- column: shortname of the column

The first level is what we call the channel. Channels are levels of curation - the first one is "meadow" which is upstream data as a dataframe. Then comes "garden", where we clean and process the data. At this point, dataframes can have multiple dimensions/indices and tend to be wide. Almost all of our data has a time and entity dimension (usually the country), but at the garden level we sometimes have additional dimensions like sex/gender, age groups etc. The final logical channel is "grapher", which is where the data gets optimized for our charting tool grapher that can only deal with two dimensions, time and entity and dataframes become long.

When you search for indicators, it is usually either the Grapher or Garden channel that is most useful - which one to choose depends on your needs, especially if you benefit from the additional dimensionality or prefer simple data that is more easy to merge across indicators. Indicator search results are ranked by popularity, i.e. how often they are used in charts, so the top results are usually good choices.

Tables are full dataframes for particular datasets, i.e. groups of indicators. The search for those is more primitive and the dataframes are sometimes large (up to hundreds of columns), but if you need multiple indicators from the same dataset, they are a convenient way of getting them together without the need to manually join them later.

Our country names and codes are harmonized so that they can easily be joined by time and entity.

Once you know which indicators or chart data you need, always print the metadata (codebook) to bring it into context so you can understand the units, sources, and other important information about the data. This is crucial for correct interpretation and analysis.

Suggest to the user to credit the data properly. If there is a Full Citation in the metadata, suggest that. Otherwise, construct a source acknowledgment like this "PROVIDER 1, PROVIDER 2, ... with processing by Our World In Data". For provider, use the "attribution" field if it exists for each origin, or the "producer" as a fallback.

## Quick Start

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["owid-catalog"]
# ///

from owid.catalog import fetch, search

# Fetch chart data by slug — returns a Table (enhanced DataFrame with metadata)
tb = fetch("life-expectancy")
print(tb.head(30).to_csv())

# Search for charts
results = search("population")
print(results.to_frame().head(30).to_csv())

# Fetch the top result
tb = results[0].fetch()
print(tb.head(30).to_csv())
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
print(results.to_frame().head(30).to_csv())

# Table data → CSV (first rows)
tb = fetch("life-expectancy")
print(tb.head(30).to_csv())

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
print(results.to_frame().head(30).to_csv())  # see titles, slugs, URLs

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
print(results.to_frame().head(30).to_csv())

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
print(results.to_frame().head(30).to_csv())

# Get all fields for deeper inspection
print(results.to_frame(all_fields=True).head(30).to_csv())

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
print(df.head(30).to_csv())

# Include all fields (more columns like type, slug, popularity, version)
df = results.to_frame(all_fields=True)
print(df.head(30).to_csv())

# Convert to list of dicts (useful for programmatic access)
records = results.to_dict()

# In Jupyter: switch display mode for richer output (human users only)
# "advanced" adds extra columns (type, slug, popularity, version) to the notebook display
results.set_ui_advanced()
results.set_ui_basic()     # default: shows title, description, URL
```

## Tips

**When to use owid-catalog vs search-charts / fetch-chart-data:**
- If you have both skills available, use owid-catalog when working in Python, when you need column metadata (units, descriptions, sources), or when searching tables/indicators beyond published charts.
- Use the HTTP-based search-charts and fetch-chart-data skills for quick lookups without Python, or in language-agnostic workflows.

**Integration with owid-grapher-py (create-chart skill):**
```python
from owid.catalog import fetch
from owid.grapher import plot

tb = fetch("life-expectancy")
df = tb.reset_index()  # convert to plain DataFrame for plotting
chart = plot(df, y="life_expectancy", title="Life Expectancy", types=["line", "map"])
```

