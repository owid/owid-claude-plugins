---
name: "create-chart"
description: "Create interactive Our World In Data style charts using the owid-grapher-py Python library. Use this skill when the user wants to visualize data as charts (line charts, bar charts, scatter plots, maps, etc.) in a Jupyter notebook, standalone HTML, or export charts to PNG/SVG."
allowed-tools:
- "Bash(uv:*)"
- "Bash(python:*)"
- "Bash(curl:*)"
- "Bash(open:*)"
- "WebFetch"
- "Write"
- "Read"
---

The `owid-grapher-py` library creates interactive charts that look and behave like Our World In Data charts. Charts render in Jupyter notebooks and can be exported to PNG, SVG, or standalone HTML.

## Installation

```bash
uv pip install owid-grapher-py
```

For PNG/SVG export, install Playwright and its browser **as two separate steps**:
```bash
uv pip install playwright
playwright install chromium
```

## IMPORTANT: Before Writing Code

The library is under active development. **Always fetch the latest documentation first:**

```bash
curl -sL "https://raw.githubusercontent.com/owid/owid-grapher-py/master/llms-full.txt"
```

This provides comprehensive API documentation including all functions, parameters, and examples. Do not rely on cached knowledge about this library.

## Quick Start: Standalone Script (No Jupyter)

For quick visualizations without Jupyter, create a Python script with inline uv dependencies:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "owid-grapher-py",
#     "pandas",
#     "requests",
# ]
# ///

import io
import pandas as pd
import requests
from owid.grapher import plot

# Fetch data from an OWID chart URL
url = "https://ourworldindata.org/grapher/life-expectancy"
resp = requests.get(f"{url}.csv?useColumnShortNames=true", headers={"User-Agent": "owid-grapher-py"})
resp.raise_for_status()
df = pd.read_csv(io.StringIO(resp.text))
df = df.rename(columns={"Entity": "entity", "Year": "year"})

# Always print columns — names aren't predictable from the URL
print(f"Columns: {list(df.columns)}")

# Create chart — plot() is the simplest way
chart = plot(
    df,
    y="life_expectancy",
    title="Life Expectancy",
    types=["line", "map"],
    entities=["France", "Brazil", "Japan"],
)

# Save and display
html = chart.to_html()
with open("chart.html", "w") as f:
    f.write(html)
print("Chart saved to chart.html")
```

Run with:
```bash
uv run --no-project script.py && open chart.html
```

The `--no-project` flag ensures uv uses an isolated environment with only the script's inline dependencies.

## Loading OWID Data

Do NOT use `pd.read_csv(url)` directly — it will get a 403 error. You need a User-Agent header:

```python
import io, pandas as pd, requests

url = "https://ourworldindata.org/grapher/annual-co2-emissions-per-country"
resp = requests.get(f"{url}.csv?useColumnShortNames=true", headers={"User-Agent": "owid-grapher-py"})
resp.raise_for_status()
df = pd.read_csv(io.StringIO(resp.text))
df = df.rename(columns={"Entity": "entity", "Year": "year"})
```

**Always print columns after loading** — the value column names are not predictable from the chart URL (e.g. the chart `annual-co2-emissions-per-country` has a column called `emissions_total`, not `annual_co2`).

## Data Requirements

The DataFrame must have:
- **entity column**: Groups data into separate lines/series (e.g., country names)
- **year column**: Time dimension for the x-axis
- **value column(s)**: Numeric data to plot

## Creating Charts

**Use `plot()` by default** — it handles most cases in a single call:

```python
from owid.grapher import plot
plot(df, y="value", title="My Chart", entities=["France", "Japan"], types=["line", "map"])
```

`plot()` accepts chart type, entity selection, color scheme, units, and more as parameters. See `llms-full.txt` for the full signature.

**Use `Chart()` when you need finer control** (e.g. multiple mark types with different options, axis configuration, transforms):

## Exporting to PNG / SVG

Requires Playwright (see installation above). Use `save_png()` or `save_svg()` on the chart object returned by `plot()`:

```python
chart = plot(df, y="value", title="My Chart", types=["map", "line"])

chart.save_png("chart.png")
chart.save_svg("chart.svg")
```

**Important:** The exported image renders the **first tab** in `types=[]`. So if you want a map PNG, put `"map"` first: `types=["map", "line"]`. For a line chart PNG, use `types=["line", "map"]`.
