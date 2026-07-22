# Repository guide for agents

This repository publishes **agent skills for working with Our World in Data** (see [README.md](README.md)). It doubles as a Claude Code plugin marketplace: `.claude-plugin/marketplace.json` defines a single plugin, `owid`, that bundles all skills under `skills/`.

## Structure

```
skills/<skill-name>/SKILL.md    # one directory per skill (Agent Skills format)
.claude-plugin/marketplace.json # marketplace + plugin definition
install-prerequisites-macos.sh  # helper to install CLI tools skills rely on
```

## Adding or changing a skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter. The `name` field **must** match the directory name; the `description` field determines when agents trigger the skill, so make it precise about *what it does and when to use it*.
2. **Register the skill** in the `skills` array of the `owid` plugin in `.claude-plugin/marketplace.json`. Without this, the skill will not be installable via the marketplace.
3. Keep skills self-contained and token-efficient: prefer instructing agents to filter/aggregate with `jq`/`duckdb` rather than pulling large responses into context.
4. Skills must only rely on public OWID endpoints and common CLI tools (`curl`, `jq`, `duckdb`, `uv`). If a new tool is genuinely needed, add it to `install-prerequisites-macos.sh`.
5. Do **not** add skills that require OWID-internal infrastructure or credentials here — those belong in the private staff repository.

## Versioning

Plugins here are intentionally **versionless**: `.claude-plugin/marketplace.json` and the plugin entries carry no `version` field, so every commit to `main` is a new release and update mechanisms pick it up automatically. Do not add version fields back.

## Testing

- Validate the marketplace: `claude plugin validate .`
- Load the plugin directly in a live session for end-to-end testing: `claude --debug --plugin-dir .`
- Sanity-check that each skill's frontmatter `name` matches its directory name.
