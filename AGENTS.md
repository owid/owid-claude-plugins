# Repository guide for agents

This repository publishes **agent skills for working with Our World in Data** (see [README.md](README.md)). It doubles as a Claude Code plugin marketplace: `.claude-plugin/marketplace.json` defines a single plugin, `owid`, that bundles all skills under `skills/`.

## Structure

```
FAQ.md                          # common user and contributor questions
Makefile                        # entry points: make validate / test / triggers
skills/<skill-name>/SKILL.md    # one directory per skill, and nothing else
.claude-plugin/marketplace.json # marketplace + plugin definition
evals/skills/<skill-name>/      # that skill's test cases and fixtures
evals/                          # shared eval harness + playbook (evals/README.md)
install-prerequisites-macos.sh  # helper to install CLI tools skills rely on
```

**Keep `skills/<skill-name>/` to just `SKILL.md`** unless a skill genuinely needs
bundled `scripts/`, `references/` or `assets/`. A skill directory is copied
recursively into users' projects by the cross-agent installer, which has no
ignore mechanism — anything you put there ships to everyone. Evals live in a
sibling `evals/skills/<skill-name>/` for exactly this reason; see
[evals/README.md](evals/README.md).

## Adding or changing a skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter. The `name` field **must** match the directory name; the `description` field determines when agents trigger the skill, so make it precise about *what it does and when to use it*.
2. **Register the skill** in the `skills` array of the `owid` plugin in `.claude-plugin/marketplace.json`. Without this, the skill will not be installable via the marketplace.
3. Keep skills self-contained and token-efficient: prefer instructing agents to filter/aggregate with `jq`/`duckdb` rather than pulling large responses into context.
4. Skills must only rely on public OWID endpoints and common CLI tools (`curl`, `jq`, `duckdb`, `uv`). If a new tool is genuinely needed, add it to `install-prerequisites-macos.sh`.
5. Do **not** add skills that require OWID-internal infrastructure or credentials — this repository is public.

## Versioning

Plugins here are intentionally **versionless**: `.claude-plugin/marketplace.json` and the plugin entries carry no `version` field, so every commit to `main` is a new release and update mechanisms pick it up automatically. Do not add version fields back.

## Testing

Run `make` for the full list. The two you need most:

- `make validate` — three checks with distinct jobs: spec conformance via
  `skills-ref`, the reference validator the [Agent Skills
  spec](https://agentskills.io/specification) recommends (agent-agnostic, so it
  covers Codex/Gemini/Cursor users too); the marketplace manifest via
  `claude plugin validate`; and that every skill is registered in
  `.claude-plugin/marketplace.json`, which neither validator knows about. Run the
  make target rather than any single CLI — none of the three subsumes another.
- `make test` — the contract tests. These check that the OWID endpoints and
  response shapes each `SKILL.md` documents still match what the API returns —
  the way these skills are most likely to break. Add `SKILL=<name>` for one
  skill. This is what CI runs.

For end-to-end testing, load the plugin directly in a live session:
`claude --debug --plugin-dir .`

## Evals

Each skill has an `evals/skills/<skill-name>/` directory holding its test inputs; the
shared harness and the playbook live in [evals/README.md](evals/README.md). Two
rules, both enforced by `make validate`:

- **Commit inputs, not outputs.** Test cases and fixtures are source. Everything
  a run produces goes to `evals/results/`, which is gitignored.
- **Never reference eval files from a `SKILL.md`.** Skills that route to their
  own evals spend the user's context budget on test prose. This is the only path
  by which eval content could reach an agent's context, so it is a hard check
  rather than a convention.

When you change a skill's `description`, re-run its trigger eval
(`make triggers SKILL=<name>`) — the four skills cover adjacent ground, so a
description change can quietly steal a sibling's traffic.
