This repository contains tools to help with using Our World In Data data and tooling when using Claude Code. For ease of versioning and use across the team, these are structured as plugins containing different skills. The skills themselves might very well be useful for other coding agents as well like OpenAI Codex CLI, but the delivery format is structured around a Claude Code plugin marketplace with multiple plugins.

This project is in an early, experimental stage. Use at your own risk.

## Installing and using the plugins

### Prerequisites

Some skills or commands may need certain prerequisites installed (e.g. `uv` to run python scripts and manage dependencies). You can either install these manually when a skills fails because of a missing tool (e.g. with `brew install uv`); or you can use this command in your terminal to install all common tools required by skills in this repo:

```bash
curl -sSL https://raw.githubusercontent.com/owid/owid-claude-plugins/main/install-prerequisites-macos.sh | bash
```

### Installation

- In Claude Code, use `/plugin marketplace add owid/owid-claude-plugins`.
- Run `/plugin` and tab to marketplaces, then select `owid-claude-plugins`.
- Browse the available plugins and install the ones you want. Claude will ask you for the scope that you want to install these in:
    1. You as a user - choose this if you want claude to know about a given skill regardless of which project you are working in
    2. In the current project for all users - choose this if you work on this project with other people and the skills should be available for everyone working on this project
    3. In the current project only for you - choose this if you want the skills available only for you and only in this project
- You can verify that a plugin is loaded by running `/plugin` and checking the `installed plugins` tab, or by just asking claude something like "Which skills are currently loaded?"
- Tools should trigger automatically when they are useful (e.g. if you ask for fetching data with the `owid-data` plugin activated). You can also explicitly trigger them with as `/plugin-name:skill-name` - for example "Fetch the data for https://ourworldindata.org/grapher/life-expectancy - use /owid-data:fetch-chart-data"

## Available plugins

### owid-general

General purpose instructions that we find useful at Our World In Data across projects, regardless of programming language. For example there is a skill that tells agents to use `uv` instead of system `python` for running python code and managing dependencies or instructions to use `duckdb`.

Skills:
- **duckdb** — Use the DuckDB CLI for ad-hoc data analysis from CSV, Parquet, or NDJSON files
- **uv** — Manage Python scripts and dependencies with `uv` instead of `pip` or `python`

### owid-data

Skills for working with data from Our World In Data. Teaches Claude Code to search our collection of charts, download the data powering a given chart, create charts, query our public datasette, and join our data with other data sources.

Skills:
- **search-charts** — Search for OWID charts by keyword using Algolia
- **fetch-chart-data** — Download data and metadata for a specific chart
- **create-chart** — Create interactive OWID-style charts using `owid-grapher-py` (Jupyter notebooks, HTML, PNG, SVG)
- **datasette-public** — Query the OWID public Datasette to explore metadata about indicators, datasets, charts, and entities via SQL
- **joining-data** — Join OWID data with external sources (e.g. for per-capita metrics or scatter plots vs GDP)
- **owid-catalog** — Access OWID's published datasets via the `owid-catalog` Python library (search charts, tables, and indicators; returns metadata-rich DataFrames)

### owid-general-staff

Skills that are only useful for Our World In Data staff members because they require access to internal infrastructure or credentials.

Skills:
- **datasette** — Query OWID's internal datasette instance (MySQL database mirror and analytics data store) via SQL

## Development

When adding new skills or plugins, consider the following:
- Split plugins by use-case. `owid-general` should only contain skills etc that are useful for a wide range of team members or other users. Consider adding new plugins when the consumers of this plugin likely have specific needs (e.g. frontend engineers working on the OWID website; or data consumers who want to get data for our charts; or data scientists working on updating data in our ETL)
- Test your skills/commands/subagents before adding them here. You can start claude code with `claude --debug --plugin-dir PATH-TO-PLUGIN-DIRECTORY` to get a logfile with debugging information and directly loading a plugin without having to go through the market place.
- Bump plugin versions when you make changes so the update mechanism of Claude Code plugins work properly.
- When you add scripts, try to keep prerequisites small and use what is already available. If it makes sense to require a specific tool to be installed, add installation of it to ./install-prerequisites-macos.sh
