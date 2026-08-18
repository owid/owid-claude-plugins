# OWID Skills

**Agent skills for working with [Our World in Data](https://ourworldindata.org).** Teach your AI coding agent — Claude Code, OpenAI Codex, Gemini CLI, Cursor, GitHub Copilot, and others — to search our charts, download the data behind them, and analyze it correctly.

Our World in Data publishes thousands of charts and datasets on global problems: poverty, health, energy, climate, education, and more. These skills give agents the knowledge to use that data well — the right APIs, the right query parameters, and the caveats that matter (country harmonization, citations, metadata).

> **Status:** early and experimental. Interfaces may change. Feedback and issues are welcome!

## What you can do

Once installed, you can ask your agent things like:

- *"Get life expectancy data for the US and UK since 1950 and plot the trend."*
- *"Find OWID charts about renewable energy adoption."*
- *"Download CO₂ emissions per country and compute per-capita values using OWID population data."*
- *"Make a scatter plot of child mortality against GDP per capita."*

The skills trigger automatically when relevant — you don't need to invoke them by name.

## Skills

Skills follow the open [Agent Skills](https://agentskills.io) format (`SKILL.md`), so they work with any agent that supports the standard.

| Skill | What it does | Requires |
|---|---|---|
| [`search-charts`](skills/search-charts/SKILL.md) | Search OWID's published charts by keyword | `curl`, `jq` |
| [`fetch-chart-data`](skills/fetch-chart-data/SKILL.md) | Download the data and metadata behind any chart | `curl`, `jq` |
| [`joining-data`](skills/joining-data/SKILL.md) | Join OWID data with external sources (per-capita metrics, scatter plots vs GDP, …) | `duckdb` |
| [`owid-catalog`](skills/owid-catalog/SKILL.md) | Python-native access to the full OWID catalog (charts, tables, indicators) via the [`owid-catalog`](https://pypi.org/project/owid-catalog/) library | `uv` (or `pip`) |

The HTTP-based skills are lightweight and language-agnostic. `owid-catalog` is the richer option when Python is available — it returns metadata-aware DataFrames and covers the full data catalog beyond published charts.

## Installation

### Claude Code

Install as a plugin from the marketplace:

```
/plugin marketplace add owid/skills
/plugin install owid@owid-skills
```

### Other agents (Codex, Gemini CLI, Cursor, Copilot, …)

These are standard [Agent Skills](https://agentskills.io), read as-is by Codex, Gemini CLI, Cursor, GitHub Copilot, and many other tools — no Claude-specific setup required. The [`skills`](https://github.com/vercel-labs/skills) CLI detects which of your installed agents support skills (75+ supported) and copies them into each one's directory:

```bash
npx skills add owid/skills            # into the current project
npx skills add owid/skills --global   # user-level, across all your projects
```

Add `--agent '*'` to install to every supported agent, or `--list` to preview the skills first.

### Manual

The skills are plain [Agent Skills](https://agentskills.io) folders, so you can also copy or symlink them into whatever directory your agent reads. Clone the repo:

```bash
git clone https://github.com/owid/skills owid-skills
```

Then put `owid-skills/skills/*` where your agent looks for skills:

- **Per project** — `./.agents/skills/` (the shared convention read by Codex, Cursor, OpenCode, …)
- **Per user** — your agent's own skills directory, e.g. `~/.codex/skills/`, `~/.gemini/skills/`, or `~/.claude/skills/`

### Prerequisites

The skills use a few common command-line tools: `curl`, `jq`, `duckdb`, and `uv`. Install them with your package manager (e.g. `brew install jq duckdb uv`), or on macOS run:

```bash
curl -sSL https://raw.githubusercontent.com/owid/skills/main/install-prerequisites-macos.sh | bash
```

## Using the data

Data published by Our World in Data is open: it is available under the [Creative Commons BY license](https://ourworldindata.org/faqs#can-i-use-or-reproduce-your-data), and it builds on the work of the original data providers. The skills instruct agents to surface proper citations — please keep them when you publish results.

## Development

Want to add or improve a skill? See [AGENTS.md](AGENTS.md) for repo conventions and [evals/README.md](evals/README.md) for how the skills are evaluated.

```bash
make            # list targets
make validate   # plugin manifest, skill frontmatter and registration
make test       # contract tests: do the OWID endpoints still match what the skills document?
make triggers   # trigger evals: does the right skill fire? (needs the claude CLI, costs tokens)
```

Add `SKILL=<name>` to `test` or `triggers` to run a single skill. To try the skills in a live session, load the plugin directly with `claude --debug --plugin-dir .`

Plugins here are versionless on purpose: every commit to `main` is a release.

This repository is limited to skills that rely on public OWID endpoints and common CLI tools; skills that require OWID-internal infrastructure or credentials are out of scope.

## License

[Apache-2.0](LICENSE)
