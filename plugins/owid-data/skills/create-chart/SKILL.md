---
name: "create-chart"
description: "Create interactive Our World In Data style charts using the owid-grapher-py Python library. Use this skill when the user wants to visualize data as charts (line charts, bar charts, scatter plots, maps, etc.) in a Jupyter notebook or export charts to PNG/SVG/HTML."
allowed-tools:
- "Bash(uv:*)"
- "Bash(python:*)"
- "Bash(curl:*)"
- "WebFetch"
- "Write"
- "Read"
---

The `owid-grapher-py` library creates interactive charts that look and behave like Our World In Data charts. Charts render in Jupyter notebooks and can be exported to PNG, SVG, or standalone HTML.

## Installation

```bash
uv pip install owid-grapher-py
```

For PNG/SVG export (requires Playwright):
```bash
uv pip install playwright && playwright install chromium
```

## IMPORTANT: Before Writing Code

The library is under active development. **Always fetch the latest documentation first:**

```bash
curl -sL "https://raw.githubusercontent.com/owid/owid-grapher-py/master/llms-full.txt"
```

This provides comprehensive API documentation including all functions, parameters, and examples. Do not rely on cached knowledge about this library.
