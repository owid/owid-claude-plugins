#!/usr/bin/env bash
# Layer 1 runner: execute every skill's contract tests. See README.md.
#
#   ./evals/run-contract-tests.sh                      # all skills
#   ./evals/run-contract-tests.sh search-charts        # one or more skills
#   SKIP_SLOW=1 ./evals/run-contract-tests.sh          # skip slow checks
#
# Exits non-zero if any check fails, so it works as a CI gate.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export EVALS_LIB="$REPO_ROOT/evals/lib"
RESULTS="$REPO_ROOT/evals/results/contract"

for tool in curl jq; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'error: %s is required but not installed\n' "$tool" >&2
        exit 2
    fi
done

# Which skills to run: the arguments, or every skill that has a contract.sh.
skills=()
if [[ $# -gt 0 ]]; then
    skills=("$@")
else
    for f in "$REPO_ROOT"/skills/*/evals/contract.sh; do
        [[ -e "$f" ]] || continue
        skills+=("$(basename "$(dirname "$(dirname "$f")")")")
    done
fi

if [[ ${#skills[@]} -eq 0 ]]; then
    printf 'no contract tests found under skills/*/evals/contract.sh\n' >&2
    exit 2
fi

failed_skills=()
for skill in "${skills[@]}"; do
    contract="$REPO_ROOT/skills/$skill/evals/contract.sh"
    if [[ ! -f "$contract" ]]; then
        printf '\n\033[31mno contract.sh for skill "%s"\033[0m\n' "$skill" >&2
        failed_skills+=("$skill")
        continue
    fi

    printf '\n\033[1m▶ %s\033[0m\n' "$skill"
    SKILL_DIR="$REPO_ROOT/skills/$skill" \
        SKILL_NAME="$skill" \
        WORK="$RESULTS/$skill" \
        bash "$contract" || failed_skills+=("$skill")
done

printf '\n────────────────────────────────────────\n'
if [[ ${#failed_skills[@]} -eq 0 ]]; then
    printf '\033[32mall contract tests passed\033[0m (%d skill(s))\n' "${#skills[@]}"
    printf 'artifacts: %s\n' "${RESULTS#"$REPO_ROOT/"}"
    exit 0
fi

printf '\033[31mcontract tests failed:\033[0m %s\n' "${failed_skills[*]}"
printf 'downloaded responses kept for inspection in %s\n' "${RESULTS#"$REPO_ROOT/"}"
exit 1
