# Evaluating the skills in this repo

Three layers, cheapest and most deterministic first. They answer different
questions, and only the third one needs a model in the loop grading output.

| Layer | Question | Model in the loop? | Cost | Where |
|---|---|---|---|---|
| 1. Contract tests | Do the endpoints and response shapes documented in `SKILL.md` still match reality? | no | seconds | `evals/skills/<skill>/contract.sh` |
| 2. Trigger evals | Does the skill fire when it should, stay quiet when it shouldn't, and not steal a sibling's job? | yes (routing only) | minutes | `evals/skills/<skill>/triggers.json` |
| 3. Output evals | Is the output any good, and better than no skill at all? | yes (plus a human) | tens of minutes | `evals/skills/<skill>/evals.json` |

Layer 1 catches the failure mode that will actually bite this repo: these skills
are thin documentation over live public OWID endpoints, so they rot when the API
changes, not when the prose gets worse. Layer 2 is next most valuable because
all four skills describe overlapping subject matter — misrouting between them is
a likelier defect than a bad answer. Layer 3 is the expensive one; it earns its
keep for `joining-data` and `owid-catalog`, where the agent does real reasoning.

## Layout

```
Makefile                                # entry points — what you actually run
evals/
├── README.md                           # you are here
├── lib/assert.sh                       # assertion helpers for contract tests
├── run-contract-tests.sh               # layer 1 runner
├── run-trigger-eval.py                 # layer 2 runner
├── results/                            # gitignored — every run writes here
└── skills/<skill>/                     # mirrors skills/, one directory per skill
    ├── contract.sh                     # layer 1
    ├── triggers.json                   # layer 2
    ├── evals.json                      # layer 3
    └── fixtures/                       # input files layer 3 cases need

skills/<skill>/SKILL.md                 # the skill, and nothing else
```

Everything directly under `evals/` is harness; everything under `evals/skills/` is
per-skill input, named exactly as the skill it tests. The runners glob
`evals/skills/*/`, so they cannot mistake `lib/` or `results/` for a skill.

## Why evals live here and not inside the skill directory

`skills/<skill>/` contains exactly one file, on purpose. A skill directory is the
unit of distribution, and it is copied **recursively** into users' projects. The
[`skills` CLI](https://github.com/vercel-labs/skills) that the README recommends
for Codex, Gemini CLI and Cursor excludes only `metadata.json`, `.git`,
`__pycache__` and `__pypackages__` — there is no ignore file and no opt-out. So
anything under `skills/<skill>/` lands in someone else's repo.

That matters less for tokens than for confusion. Fixture CSVs are realistic by
design; once they sit in a user's `.agents/skills/`, a `find . -name '*.csv'` or a
project-wide grep returns them alongside the user's real data. Keeping evals in a
sibling top-level directory removes the possibility entirely rather than
mitigating it: the installer never sees them.

The same reasoning is why no `SKILL.md` may reference an eval file — that is the
one remaining path by which this content could reach an agent's context, and
`make validate` now enforces it rather than trusting the convention.

**The rule that keeps this from becoming clutter: commit inputs, never outputs.**
Test cases, assertions and fixtures are source. Run outputs, gradings,
benchmarks and transcripts go to `evals/results/`, which is gitignored. The
noisy 90% of an eval workflow is never checked in.

Nothing under `evals/` is referenced from any `SKILL.md`, and `make validate`
fails if that ever changes. Skills must not route to their own eval files — that
would put eval prose into the context budget of every user who triggers the skill.

## Layer 1 — contract tests

```bash
make test                                      # all skills
make test SKILL=search-charts                  # one skill
SKIP_SLOW=1 make test                          # skip the slow owid-catalog checks
```

Exits non-zero if any check fails, so it works as a CI gate; it runs on every PR
and nightly via `.github/workflows/contract-tests.yml`. Downloaded responses stay
in `evals/results/contract/<skill>/` so you can inspect a failure without
re-running.

Checks come in two flavours. Most assert that the API behaves as documented. A
few assert the reverse — that `SKILL.md` still documents everything the API
returns. The tab-mapping check in `search-charts` is the clearest example: if
OWID adds a new chart type, the check fails because an agent reading the skill
would have no way to build a `?tab=` URL for it.

**A check that did not run must never look like a check that passed.** This bit
us three ways: jq's `all` is `true` for an empty array, so a per-type assertion
passes vacuously when the sample holds none of that type; a `[[ -s "$FILE" ]]`
guard falls through silently when an earlier request failed; and a Python gate
that returns early drops its dependent checks from the summary entirely. Each is
now reported with `skip` and a reason. When you add a check that depends on the
sample containing something, assert that it does, or `skip` loudly.

Writing a new check: `source "$EVALS_LIB/assert.sh"` and reach for a helper
rather than raw shell. The vocabulary exists so that a check reads as a claim
about the API instead of as plumbing — if you find yourself writing `bash -c`
with nested quoting, the helper is missing and worth adding.

| Helper | Use |
|---|---|
| `fetch <url> <out>` | GET, assert 200, save the body. Returns non-zero so you can guard |
| `all_match <name> <file> <selector> <predicate>` | every selected element satisfies the predicate |
| `none_match <name> <file> <selector> <predicate>` | no selected element satisfies it |
| `jq_true` / `jq_eq` / `jq_type` / `has_keys` | single-value assertions on JSON |
| `csv_column <file> <col>` | print a column's values, by name, quote-aware |
| `csv_has_columns` / `csv_min_rows` | CSV preconditions |
| `csv_column_set` / `csv_column_range` / `csv_column_matches` | assertions on a column's values |
| `csv_header` | the header line starts with a literal prefix (case-sensitive on purpose) |
| `skill_md_contains` / `skill_md_table_covers` | documentation-drift checks against SKILL.md |
| `ok <name> <cmd...>` | last resort: the command exits 0 |
| `note` / `skip` / `section` / `finish` | output and control |

`all_match` and `none_match` take the selector and the predicate separately. That
keeps quoting sane, and it lets them insist the selector matched something before
judging the predicate — `[] | all` is `true` in jq, so a fused filter silently
passes when the sample contains none of the thing being described.

CSV columns are addressed **by name**, resolved case-insensitively, because
`useColumnShortNames=true` lowercases the first three headers: an index-based or
case-sensitive check only works against one of the two documented forms. The
splitter is quote-aware, which matters for entities like
`"Bonaire, Sint Eustatius and Saba"` — `cut -d,` returns the wrong field there.

Guard dependent checks on `fetch` succeeding, so one dead endpoint doesn't
cascade into a wall of failures:

```bash
if fetch "$API?q=energy" "$WORK/search.json"; then
    jq_true "a common query returns hits" "$WORK/search.json" '.nbHits > 0'
fi
```

Run `make lint` before committing: shellcheck for the shell, ruff for the Python.

## Layer 2 — trigger evals

```bash
make triggers SKILL=search-charts                            # one skill
make triggers                                                # every skill
make triggers SKILL=owid-catalog RUNS=1                      # cheapest useful loop
make triggers MODEL=claude-sonnet-5 EFFORT=medium            # override the defaults

./evals/run-trigger-eval.py --skill joining-data --dry-run   # print the plan only
./evals/run-trigger-eval.py --all --max-budget-usd 0.05      # hard per-run spend cap
```

**This layer is the expensive one, so size it deliberately.** Cost is
`queries x RUNS x skills` full `claude -p` sessions — the default `make triggers`
is 4 x 10 x 3 = 120 of them, each carrying a full system prompt, and a query that
fires nothing lets the model answer it in full before exiting.

| Knob | Default | Effect |
|---|---|---|
| `SKILL=<name>` | all four | 4x fewer runs |
| `RUNS=<n>` | 3 | 3 runs stabilises a fire rate; 1 is enough while iterating on wording |
| `EFFORT=<level>` | `low` | routing is decided before any real work, so thinking tokens are waste |
| `MODEL=<id>` | your session model | see the caveat below |
| `--max-budget-usd` | unset | hard per-run cap; a cut-off run is reported as an error, not as a negative |

Routing is model-dependent, so a cheaper `MODEL` measures that model's routing,
not the one your users get. Use it to iterate on description wording quickly, then
re-measure on the model you actually ship before recording a result.

**Exit status is not a verdict on accuracy.** This is a measurement, not a gate:
the runner exits non-zero only when runs failed (the numbers are untrustworthy),
or when you opt into a floor with `--min-accuracy`.

Each query runs through `claude -p` with this repo loaded via `--plugin-dir`, so
**all four skills are registered at once** — the same situation a real user is
in. The runner records *which* skill fired, which makes four outcomes possible:

| Outcome | Meaning |
|---|---|
| `correct` | the expected skill fired (or, for a negative, nothing did) |
| `miss` | no skill fired but one should have |
| `misroute` | a different skill fired than the one expected |
| `false_positive` | the skill under test fired when it should not have |
| `error` | the run never produced a routing decision, so it says nothing either way |

`error` exists because "no skill fired" and "the run never happened" look
identical from the outside. Conflating them is dangerous: an unauthenticated CLI
would score every negative case as `correct` and report respectable accuracy on
nothing at all. Only runs that observed a decision or exited cleanly are allowed
to vote, failed runs are reported with their cause, and any failed run makes the
whole invocation exit non-zero.

`triggers.json` is a list of `{query, should_trigger}` objects, compatible with
the eval-set format that `anthropics/skills`' `skill-creator` uses. Two
extensions: an optional `note` for human context, and an optional
`expected_skill` naming the sibling that *should* win instead. That third case is
the one worth investing in here:

```json
{
  "query": "grab the csv behind https://ourworldindata.org/grapher/life-expectancy for the USA",
  "should_trigger": false,
  "expected_skill": "fetch-chart-data",
  "note": "url already known — discovery is not needed"
}
```

Each set currently holds 10 queries (5 positive, 5 near-miss). Twenty is the
target once the format has proven itself. The negatives that earn their keep are
the near-misses — a query that shares vocabulary with the skill but needs
something else. `"write a fibonacci function"` tests nothing.

Only the `Skill` tool is permitted during a run, and the run is killed the
moment a skill fires: we are measuring the routing decision, not letting the
skill run `curl` for real.

## Layer 3 — output evals

Not automated yet. `evals.json` holds the case definitions in the format
described at <https://agentskills.io/skill-creation/evaluating-skills> — `prompt`,
`expected_output`, optional `files`, and draft `assertions`. Each skill has three
cases: a happy path, a case that tests a specific piece of guidance in the skill,
and an edge case.

To run one by hand, spawn a subagent with a clean context for each configuration
and give it the skill path, the prompt, any fixtures, and an output directory
under `evals/results/output/iteration-N/<case>/{with_skill,without_skill}/`. Then
grade each assertion PASS/FAIL with quoted evidence, and review the outputs
yourself — assertions only catch what you thought to write down.

The baseline matters more than the score. A case where with-skill and
without-skill both pass is telling you the skill added nothing there; drop the
assertion or make the case harder.

## Iterating

1. Run the layers. Layer 1 tells you whether the docs are still true; layer 2
   whether the description routes correctly; layer 3 whether the output is good.
2. Read the failures alongside the current `SKILL.md`.
3. Change one thing. Prefer explaining *why* over adding a rule — models follow
   reasoning more reliably than directives.
4. Re-run. Keep the change only if a target measure improves and nothing else
   regresses.

Adopt a skill change when: contract tests pass; trigger accuracy does not drop;
no output-eval assertion that previously passed now fails; and no eval file
ended up referenced from `SKILL.md`.

## Caveats

- The exact way `claude -p` reports skill invocations is not a stable contract.
  `run-trigger-eval.py` parses `tool_use` blocks with a raw substring fallback;
  if results look implausible, run `--dry-run`, execute the printed command by
  hand, and check the `stream-json` against `skills_in_line()`.
- Layer 1 hits the live public API, so a network outage looks like a failure.
  That is deliberate — a red nightly run because OWID is down is information.
- Layer 2 costs real tokens: 10 queries × 3 runs × 4 skills is 120 `claude -p`
  invocations. Run it when a description changes, not on every PR.
