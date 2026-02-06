---
name: "indicators"
description: "Access OWID indicators directly by ID, bypassing charts. Use this when you need raw indicator data with full metadata, or when searching for specific data concepts rather than visualizations. Indicators provide more granular access than chart-based queries."
allowed-tools:
- "Bash(curl:*)"
- "Bash(jq:*)"
---

OWID indicators are the underlying data variables that power charts. Accessing indicators directly gives you:
- Raw data without chart configuration overhead
- Full metadata including descriptions and sources
- Efficient grouped format (entity → years[] + values[])

## Searching for Indicators

Use the OWID API to search for indicators by concept. **Do NOT include country names in the search** - those are specified when fetching data.

```bash
# Search by concept - use simple terms
curl -s "https://owid.cloud/v1/indicators?q=coal+production&limit=5" | jq '.results[] | {id, title, description}'
```

**Good search terms:** `coal`, `temperature`, `population`, `gdp`, `renewable energy`
**Bad search terms:** `coal production in China` (don't include countries)

## Fetching Indicator Data

Once you have an indicator ID, fetch data and metadata:

```bash
# Fetch data - returns {entities, years, values} arrays
curl -s "https://api.ourworldindata.org/v1/indicators/2118.data.json" | jq

# Fetch metadata
curl -s "https://api.ourworldindata.org/v1/indicators/2118.metadata.json" | jq '{name, description, unit, source}'
```

## Efficient Data Format

Indicator data comes in a compact grouped format that saves tokens:

```json
{
  "entity": "United States",
  "years": [2000, 2001, 2002, 2003],
  "values": [10.5, 11.2, 12.1, 12.8]
}
```

This is more efficient than row-per-observation CSV format.

## Smart Rounding

To reduce token usage, apply smart rounding based on magnitude:
- Very small (<0.001): 4 significant digits
- Small (0.001-1): 3 decimal places
- Medium (1-1000): 2 decimal places
- Large (1000-10000): 1 decimal place
- Very large (>10000): integers

## When to Use Indicators vs Charts

| Use Indicators | Use Charts |
|----------------|------------|
| Need raw data with full metadata | Need visualization context |
| Searching by data concept | Searching for specific visualizations |
| Programmatic data analysis | Want pre-configured chart settings |
| Need efficient grouped format | Need CSV format |

## Common Indicator IDs

Some frequently used indicators:
- Population: Check search results for current IDs
- GDP per capita: Check search results for current IDs

Note: Indicator IDs can change over time. Always search first rather than hardcoding IDs.
