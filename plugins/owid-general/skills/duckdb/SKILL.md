---
description: The duckdb cli is installed on this system and is a good choice for ad-hoc data analysis from CSV, parquet or NDJSON files. Use it when the user asks for data values in the context of a specific data file or to join multiple files together.
globs:
  - "*.csv"
  - "*.parquet"
allowed-tools:
- "Bash(duckdb:*)"
---
---

When using duckdb for querying single files, use the `DESCRIBE SELECT` and, optionally, `SUMMARIZE SELECT` statements to understand the structure beforehand.