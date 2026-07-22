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
- Tools should trigger automatically when they are useful (e.g. if you ask for fetching data with the `owid-data-web` plugin activated). You can also explicitly trigger them with as `/plugin-name:skill-name` - for example "Fetch the data for https://ourworldindata.org/grapher/life-expectancy - use /owid-data-web:fetch-chart-data"

## Using these skills with other coding agents (pi, codex, etc.)

Some coding agents do not support Claude plugins, but they do support loading skills from:

- `~/.agents/skills/` (user-level)
- `./.agents/skills/` (project-level)

For this workflow, clone this repository locally and run:

```bash
./manage-agent-skills.py
```

The script:

- updates the repository from `origin/main` first (to pull the latest skills)
- opens a simple two-pane TUI:
  - left: plugins and their skills, with install status indicators
  - right: description of the selected plugin or skill
- installs skills by creating symlinks from this repo into either:
  - `~/.agents/skills/` (user)
  - `./.agents/skills/` (project)

Keybindings in the TUI:

- `u` → install selected skill(s) to user scope
- `p` → install selected skill(s) to project scope
- `d` → uninstall selected skill(s) from both scopes
- `q` → quit

The script uses `uv` and will auto-install Python dependencies declared in the script header when needed.

## Available plugins

### owid-data

Skills for working with Our World In Data. Requires Python tooling (`uv`, `owid-catalog`).

Skills:
- **owid-catalog** — Access OWID's published datasets via the `owid-catalog` Python library (search charts, tables, and indicators; returns metadata-rich DataFrames)

### owid-general

General purpose instructions that we find useful at Our World In Data across projects, regardless of programming language. For example there is a skill that tells agents to use `uv` instead of system `python` for running python code and managing dependencies or instructions to use `duckdb`.

Skills:
- **uv** — Manage Python scripts and dependencies with `uv` instead of `pip` or `python`
- **duckdb** — Use the DuckDB CLI for ad-hoc data analysis from CSV, Parquet, or NDJSON files

### owid-data-web

Lightweight skills for working with Our World In Data chart data directly via the web. Requires `curl`, `jq`, and `duckdb`. Useful when python is not available or to integrate owid data into webapps or non-python programming languages.

Skills:
- **search-charts** — Search for OWID charts by keyword using Algolia
- **fetch-chart-data** — Download data and metadata for a specific chart
- **joining-data** — Join OWID data with external sources (e.g. for per-capita metrics or scatter plots vs GDP)
- **fact-check-article** — Fact-check an article against OWID data: highlights checkable statements in a local copy of the article (green/red/yellow/blue verdicts) with embedded interactive charts

### owid-general-staff

Skills that are only useful for Our World In Data staff members because they require access to internal infrastructure or credentials.

Skills:
- **datasette** — Query OWID's internal datasette instance (MySQL database mirror and analytics data store) via SQL
- **create-chart** — Create interactive OWID-style charts using `owid-grapher-py` (Jupyter notebooks, HTML, PNG, SVG)

## Development

When adding new skills or plugins, consider the following:
- Split plugins by use-case. `owid-general` should only contain skills etc that are useful for a wide range of team members or other users. Consider adding new plugins when the consumers of this plugin likely have specific needs (e.g. frontend engineers working on the OWID website; or data consumers who want to get data for our charts; or data scientists working on updating data in our ETL)
- Test your skills/commands/subagents before adding them here. You can start claude code with `claude --debug --plugin-dir PATH-TO-PLUGIN-DIRECTORY` to get a logfile with debugging information and directly loading a plugin without having to go through the market place.
- Bump plugin versions when you make changes so the update mechanism of Claude Code plugins work properly.
- When you add scripts, try to keep prerequisites small and use what is already available. If it makes sense to require a specific tool to be installed, add installation of it to ./install-prerequisites-macos.sh
