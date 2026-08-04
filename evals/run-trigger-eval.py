#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Layer 2 runner: does a skill fire when it should, and stay quiet when it shouldn't?

Runs each query from a skill's evals/triggers.json through `claude -p` with this
repo loaded as a plugin, and records *which* skill (if any) the model reached
for. Because all four OWID skills are loaded together, the interesting failure
is not just "nothing triggered" but "the wrong sibling triggered" — the skills
here overlap heavily in subject matter, so misrouting is the likelier defect.

Usage:
    ./evals/run-trigger-eval.py --skill search-charts
    ./evals/run-trigger-eval.py --all --runs 3
    ./evals/run-trigger-eval.py --skill joining-data --dry-run   # print the plan

Nothing here is authoritative about how Claude Code registers plugin skills; if
detection looks wrong, run one query by hand with the command printed by
--dry-run and inspect the stream-json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
RESULTS_DIR = REPO_ROOT / "evals" / "results" / "triggers"

# Only the Skill tool is allowed: we want to observe the routing decision, not
# let the skill run curl/duckdb for real. The run is killed as soon as a skill
# fires, so the model never gets far anyway.
ALLOWED_TOOLS = "Skill"


def known_skills() -> list[str]:
    return sorted(p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


def load_queries(skill: str) -> list[dict]:
    path = SKILLS_DIR / skill / "evals" / "triggers.json"
    if not path.is_file():
        sys.exit(f"no trigger eval set at {path.relative_to(REPO_ROOT)}")
    data = json.loads(path.read_text())
    for i, item in enumerate(data):
        if "query" not in item or "should_trigger" not in item:
            sys.exit(f"{path.name}[{i}] needs both 'query' and 'should_trigger'")
    return data


def build_command(query: str, model: str | None) -> list[str]:
    cmd = [
        "claude",
        "-p",
        query,
        "--plugin-dir",
        str(REPO_ROOT),
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowed-tools",
        ALLOWED_TOOLS,
    ]
    if model:
        cmd += ["--model", model]
    return cmd


def skills_in_line(line: str, candidates: list[str]) -> set[str]:
    """Extract skill names from one stream-json line.

    Two passes, because the exact stream shape is not a stable contract: a
    structured read of `tool_use` blocks, then a narrow regex fallback.

    The fallback has to stay narrow. Every line that carries the available-skills
    listing mentions all four skill names, so a loose substring match would
    report every skill as fired on every run.
    """
    found: set[str] = set()

    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        obj = None

    if isinstance(obj, dict):
        blocks = (obj.get("message") or {}).get("content")
        if isinstance(blocks, list):
            for block in blocks:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if block.get("name") != "Skill":
                    continue
                for value in (block.get("input") or {}).values():
                    if isinstance(value, str):
                        # Plugin skills are namespaced by the plugin directory
                        # name, e.g. "owid:search-charts".
                        name = value.split(":")[-1].strip()
                        if name in candidates:
                            found.add(name)

    if not found:
        for name in candidates:
            esc = re.escape(name)
            invoked = rf'"name"\s*:\s*"Skill".{{0,200}}?"(?:[a-z-]+:)?{esc}"'
            read_skill_md = rf"skills/{esc}/SKILL\.md"
            if re.search(invoked, line) or re.search(read_skill_md, line):
                found.add(name)

    return found


def run_once(query: str, candidates: list[str], timeout: int, model: str | None) -> dict:
    """Run one query; return which skills fired plus the raw transcript."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(
        build_command(query, model),
        stdin=subprocess.DEVNULL,  # otherwise claude -p waits on stdin before starting
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
    )

    killer = threading.Timer(timeout, proc.kill)
    killer.start()

    fired: set[str] = set()
    transcript: list[str] = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            transcript.append(line)
            hits = skills_in_line(line, candidates)
            if hits:
                fired |= hits
                proc.kill()  # routing decision observed; no need to let it run
                break
    finally:
        killer.cancel()
        proc.kill()
        proc.wait()

    return {"fired": sorted(fired), "transcript": "".join(transcript)}


def classify(skill: str, row: dict, fired: list[str]) -> str:
    """One of: correct, miss, misroute, false_positive.

    Three kinds of query, distinguished by `should_trigger` and the optional
    `expected_skill` field:

    1. should_trigger: true            → `skill` must fire.
    2. should_trigger: false           → no skill in this repo may fire.
    3. should_trigger: false plus
       expected_skill: "<sibling>"     → the sibling must fire instead of
                                         `skill`. This is the case that matters
                                         most here, since the four skills cover
                                         adjacent ground.
    """
    sibling = row.get("expected_skill")

    if row["should_trigger"]:
        if skill in fired:
            return "correct"
        return "misroute" if fired else "miss"

    if sibling:
        if sibling in fired and skill not in fired:
            return "correct"
        if skill in fired:
            return "false_positive"  # this skill grabbed a sibling's job
        return "misroute" if fired else "miss"

    return "false_positive" if fired else "correct"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--skill", help="skill directory name under skills/")
    target.add_argument("--all", action="store_true", help="every skill with a triggers.json")
    parser.add_argument("--runs", type=int, default=3, help="runs per query (default: 3)")
    parser.add_argument("--workers", type=int, default=4, help="parallel runs (default: 4)")
    parser.add_argument("--timeout", type=int, default=90, help="seconds per run (default: 90)")
    parser.add_argument("--threshold", type=float, default=0.5, help="fire rate counted as a trigger (default: 0.5)")
    parser.add_argument("--model", default=None, help="model for claude -p (default: your configured model)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and one example command, run nothing")
    args = parser.parse_args()

    candidates = known_skills()
    if args.all:
        skills = [s for s in candidates if (SKILLS_DIR / s / "evals" / "triggers.json").is_file()]
    else:
        if args.skill not in candidates:
            sys.exit(f"unknown skill '{args.skill}'; known: {', '.join(candidates)}")
        skills = [args.skill]

    exit_code = 0
    for skill in skills:
        queries = load_queries(skill)
        total_runs = len(queries) * args.runs
        print(f"\n\033[1m▶ {skill}\033[0m — {len(queries)} queries × {args.runs} runs = {total_runs} runs")

        if args.dry_run:
            print("  example command:")
            print("   ", " ".join(f"'{c}'" if " " in c else c for c in build_command(queries[0]["query"], args.model)))
            continue

        if not command_exists("claude"):
            sys.exit("the `claude` CLI is not on PATH")

        results: dict[int, list[dict]] = {i: [] for i in range(len(queries))}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(run_once, q["query"], candidates, args.timeout, args.model): i
                for i, q in enumerate(queries)
                for _ in range(args.runs)
            }
            for done in as_completed(futures):
                i = futures[done]
                try:
                    results[i].append(done.result())
                except Exception as exc:  # a crashed run is a failed run, not a crashed suite
                    results[i].append({"fired": [], "transcript": f"RUNNER ERROR: {exc}"})
                print(".", end="", flush=True)
        print()

        report = summarize(skill, queries, results, args.threshold)
        write_report(skill, report, results, args)
        print_report(report)
        if report["summary"]["accuracy"] < 1.0:
            exit_code = 1

    return exit_code


def command_exists(name: str) -> bool:
    return subprocess.run(["which", name], capture_output=True).returncode == 0


def summarize(skill: str, queries: list[dict], results: dict[int, list[dict]], threshold: float) -> dict:
    rows = []
    for i, q in enumerate(queries):
        runs = results[i]
        fire_counts: dict[str, int] = {}
        for run in runs:
            for name in run["fired"]:
                fire_counts[name] = fire_counts.get(name, 0) + 1
        # A skill counts as triggered if it fired in at least `threshold` of runs.
        fired = sorted(n for n, c in fire_counts.items() if c / len(runs) >= threshold)
        rows.append(
            {
                "query": q["query"],
                "should_trigger": q["should_trigger"],
                "expected_skill": q.get("expected_skill"),
                "note": q.get("note", ""),
                "fired": fired,
                "fire_counts": fire_counts,
                "runs": len(runs),
                "outcome": classify(skill, q, fired),
            }
        )

    outcomes = [r["outcome"] for r in rows]
    positives = [r for r in rows if r["should_trigger"]]
    negatives = [r for r in rows if not r["should_trigger"]]
    return {
        "skill": skill,
        "threshold": threshold,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": rows,
        "summary": {
            "accuracy": outcomes.count("correct") / len(rows) if rows else 0.0,
            "recall": sum(r["outcome"] == "correct" for r in positives) / len(positives) if positives else None,
            "misroutes": sum(r["outcome"] == "misroute" for r in positives),
            "misses": sum(r["outcome"] == "miss" for r in positives),
            "false_positives": sum(r["outcome"] == "false_positive" for r in negatives),
        },
    }


def print_report(report: dict) -> None:
    marks = {"correct": "\033[32m✓\033[0m", "miss": "\033[31m✗ miss\033[0m",
             "misroute": "\033[33m→ misroute\033[0m", "false_positive": "\033[31m✗ false positive\033[0m"}
    for row in report["rows"]:
        detail = f" (fired: {', '.join(row['fired'])})" if row["fired"] else ""
        query = row["query"] if len(row["query"]) <= 88 else row["query"][:85] + "..."
        print(f"  {marks[row['outcome']]}{detail}\n      {query}")
    s = report["summary"]
    recall = "n/a" if s["recall"] is None else f"{s['recall']:.0%}"
    print(
        f"\n  accuracy {s['accuracy']:.0%} | recall {recall} | "
        f"{s['misses']} miss, {s['misroutes']} misroute, {s['false_positives']} false positive"
    )


def write_report(skill: str, report: dict, results: dict[int, list[dict]], args: argparse.Namespace) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / skill / stamp
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    report["config"] = {"runs": args.runs, "timeout": args.timeout, "model": args.model}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    for i, runs in results.items():
        for n, run in enumerate(runs):
            (out / "transcripts" / f"query-{i:02d}-run-{n}.jsonl").write_text(run["transcript"])
    print(f"  report: {(out / 'report.json').relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
