# FAQ

Common questions about using and contributing to these skills. For repo
conventions see [AGENTS.md](AGENTS.md); for how the skills are evaluated see
[evals/README.md](evals/README.md).

## Using the skills

### My agent isn't using the skills at all

Work through these in order — the first two are the most common.

**1. Are the files where your agent looks?** Every agent reads a different
directory, and installing to the wrong one fails silently. The
[`skills` CLI](https://github.com/vercel-labs/skills) knows the paths for 76
agents and picks the right one:

```bash
npx skills add owid/skills            # into the current project
npx skills add owid/skills --global   # user-level, all projects
npx skills list                       # what is installed where
```

Nineteen of those agents — including Codex, Cursor and Gemini CLI — share the
project-level `.agents/skills/` convention. Claude Code is the notable exception,
using `.claude/skills/` per project and `~/.claude/skills/` globally. If you
installed by hand, check with `ls .agents/skills/ .claude/skills/ 2>/dev/null`.

**2. Is your agent's reasoning effort turned down?** Skills are invoked through a
tool call, and lowering reasoning effort makes agents make fewer tool calls — so
a setting you turned down for cost can stop skills firing at all.

We measured this on Claude Code while building the trigger evals: at
`--effort low`, five queries that reliably invoke a skill at normal effort were
answered directly instead, with no skill consulted. Nothing about the skills
changed; only the effort did.

The same class of setting exists elsewhere — Codex has `model_reasoning_effort`
(`minimal`/`low`/`medium`/`high`/`xhigh`) in `~/.codex/config.toml`, and most
agents expose something similar. **We have only measured the effect on Claude
Code**, so treat the others as a plausible first thing to check rather than a
known cause. If your agent ignores skills, raise the effort and try again before
assuming the skill is at fault.

**3. Is the task substantial enough?** Agents skip skills for work they can do
unaided. "What's the URL for OWID's CO2 chart?" may not trigger anything, while
"find the best OWID chart on CO2 per capita and pull the data for the G7" will.
This is by design — it isn't a bug you need to report.

**4. Ask for it by name.** `use the search-charts skill to find…` bypasses
routing entirely, and is the quickest way to tell "the skill is missing" apart
from "the skill wasn't selected".

### The wrong skill triggered

These four skills cover deliberately adjacent ground, so this happens. The rough
division of labour:

| You have… | You want… | Skill |
|---|---|---|
| a topic | to find a chart | `search-charts` |
| a chart URL | its data or metadata | `fetch-chart-data` |
| your own dataset | it joined to OWID data | `joining-data` |
| Python, or a need for units/metadata/indicators | a DataFrame | `owid-catalog` |

Naming the skill explicitly always wins. If a realistic request routes to the
wrong skill repeatedly, that is a bug in our `description` fields and worth
[opening an issue](https://github.com/owid/skills/issues) — please include the
prompt you used, since that becomes a trigger-eval case.

### Does installing this put files in my repo?

Yes, if you install per-project: the skill directories are copied into your
agent's skills directory inside the project. Each skill is a single `SKILL.md`
and nothing else — about 32 KB in total — and this is deliberate. Our test
fixtures and eval scripts live in a top-level `evals/` directory precisely so
they are never copied into your repository, where a fixture CSV could be mistaken
for your own data. See
[evals/README.md](evals/README.md#why-evals-live-here-and-not-inside-the-skill-directory).

To keep them out of version control, add your agent's skills directory to
`.gitignore`, or install with `--global` instead.

### Which tools do I need installed?

Per skill, so you only need what you use:

| Skill | Needs |
|---|---|
| `search-charts` | `curl`, `jq` |
| `fetch-chart-data` | `curl`, `jq` |
| `joining-data` | `duckdb` |
| `owid-catalog` | `uv` (or `pip`) |

On macOS, `./install-prerequisites-macos.sh` installs all four. Skills only use
public OWID endpoints — there are no credentials to configure.

### A skill gave me data I think is wrong

Check whether the skill or the data is at fault. The skills are documentation
over OWID's public API; they don't transform values. Fetch the same numbers
directly:

```bash
curl -s "https://ourworldindata.org/grapher/life-expectancy.csv?csvType=filtered&country=USA&time=2020"
```

If that matches what the agent told you, the skill worked and any concern belongs
with the underlying data — see the chart's own page on
[ourworldindata.org](https://ourworldindata.org). If it doesn't match, that's our
bug. Two known traps worth ruling out first:

- **`csvType=filtered` applies the chart's own default entity selection**, not
  "all countries". `population.csv?csvType=filtered&time=2020` returns seven rows
  — continents and World — with no individual countries. Pass an explicit
  `country=` filter.
- **A no-match search still returns results.** OWID's search falls back to
  low-relevance hits rather than returning nothing, so `nbHits` is never a
  reliable signal that a topic is missing. Judge the titles.

## Contributing

### `make test` fails and I didn't change anything

That is the contract tests doing their job. They check the OWID endpoints and
response shapes each `SKILL.md` documents against what the API actually returns,
so they can break when OWID ships a change and nobody has touched this repo.
They also run nightly for exactly that reason.

Read the failure before assuming it's a flake — it names the endpoint and the
mismatch, and the downloaded responses are kept under `evals/results/contract/`
so you can inspect one without re-running. Network outages also surface here,
which is intentional.

### `make triggers` costs a lot. How do I make it cheaper?

It runs `queries x RUNS x skills` full agent sessions — 120 for the default
invocation. While iterating on a description, narrow it:

```bash
make triggers SKILL=owid-catalog RUNS=1
```

Don't reach for a lower effort level to save money: as above, effort changes
whether skills fire at all, so a cheap run measures something other than what
your users experience. Same caution for `MODEL=` — routing is model-dependent, so
a cheaper model measures that model's routing. Both are fine for fast iteration
on wording, then confirm on the real model and effort before believing a number.

### Why do the skills never mention their own evals?

Because the `description` and `SKILL.md` body are loaded into the user's context
when a skill triggers, and eval prose would be pure overhead there. It's enforced
by `make validate`, not left to discipline.

### `make triggers` exits non-zero. Is that a failure?

Only if runs errored. Trigger accuracy is a measurement, not a pass/fail gate —
100% routing accuracy isn't a realistic bar. The runner exits non-zero when runs
actually failed (meaning the numbers can't be trusted) or when you set a floor
with `--min-accuracy`. `make test` is the gate.

### How do I add a skill?

See [AGENTS.md](AGENTS.md). The short version: create
`skills/<name>/SKILL.md` with `name` matching the directory, register it in
`.claude-plugin/marketplace.json`, then run `make validate`. Keep the directory
to just `SKILL.md` unless you genuinely need bundled `scripts/`, `references/` or
`assets/` — everything in there ships to every user.
