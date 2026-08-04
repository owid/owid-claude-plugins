#!/usr/bin/env bash
# Assertion helpers for skill contract tests (see ../README.md, layer 1).
#
# Contract tests check that the endpoints and response shapes a SKILL.md
# documents still match what the API actually returns. No model in the loop, so
# they are cheap and deterministic enough to run on every PR and nightly.
#
# Source this from a skill's evals/contract.sh:
#
#   source "$EVALS_LIB/assert.sh"
#
# The runner exports EVALS_LIB, SKILL_DIR, SKILL_NAME and WORK before invoking
# each contract.sh. When running a contract.sh directly, they are derived below.

# Deliberately no `set -e`: one failing check must not abort the remaining ones.
set -uo pipefail

: "${SKILL_DIR:="$(cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd)"}"
: "${SKILL_NAME:="$(basename "$SKILL_DIR")"}"
: "${WORK:="$SKILL_DIR/evals/../../../evals/results/contract/$SKILL_NAME"}"
SKILL_MD="$SKILL_DIR/SKILL.md"
mkdir -p "$WORK"

_PASS=0
_FAIL=0
_SKIP=0
_FAILURES=()

_pass() {
    _PASS=$((_PASS + 1))
    printf '  \033[32m✓\033[0m %s\n' "$1"
}

_fail() {
    _FAIL=$((_FAIL + 1))
    _FAILURES+=("$1${2:+ — $2}")
    printf '  \033[31m✗\033[0m %s\n' "$1"
    [[ -n "${2:-}" ]] && printf '      %s\n' "$2"
    return 0
}

# skip <name> <reason> — record a check that could not run (e.g. missing tool).
skip() {
    _SKIP=$((_SKIP + 1))
    printf '  \033[33m∼\033[0m %s (skipped: %s)\n' "$1" "$2"
}

# note <text> — informational output, not a check. Use to surface values a
# reviewer may want to eyeball (a timespan, a row count).
note() {
    printf '    \033[2m%s\033[0m\n' "$1"
}

# section <text> — group heading.
section() {
    printf '\n  \033[1m%s\033[0m\n' "$1"
}

# fetch <url> <outfile> — GET the url, assert HTTP 200, save the body.
# Returns non-zero on failure so callers can guard dependent checks:
#   if fetch "$url" "$WORK/x.json"; then jq_true ... ; fi
fetch() {
    local url="$1" out="$2" code
    code=$(curl -sS -L --retry 3 --retry-delay 2 --max-time 90 \
        -H 'User-Agent: owid-skills contract tests (tech@ourworldindata.org)' \
        -o "$out" -w '%{http_code}' "$url" 2>"$WORK/curl.err") || code="000"
    if [[ "$code" == "200" ]]; then
        _pass "GET $url → 200"
        return 0
    fi
    _fail "GET $url → 200" "got HTTP $code$([[ -s $WORK/curl.err ]] && printf ' (%s)' "$(tr -d '\n' <"$WORK/curl.err")")"
    return 1
}

# ok <name> <cmd...> — the command exits 0.
ok() {
    local name="$1"
    shift
    local out
    if out=$("$@" 2>&1); then
        _pass "$name"
    else
        _fail "$name" "${out:-command exited $?}"
    fi
}

# jq_true <name> <file> <filter> — the jq filter evaluates to true.
jq_true() {
    local name="$1" file="$2" filter="$3" result
    result=$(jq -r "$filter" "$file" 2>&1)
    if [[ "$result" == "true" ]]; then
        _pass "$name"
    else
        _fail "$name" "jq '$filter' → ${result:-<empty>}"
    fi
}

# jq_eq <name> <file> <filter> <expected> — the jq filter equals expected.
jq_eq() {
    local name="$1" file="$2" filter="$3" expected="$4" actual
    actual=$(jq -r "$filter" "$file" 2>&1)
    if [[ "$actual" == "$expected" ]]; then
        _pass "$name"
    else
        _fail "$name" "expected '$expected', got '${actual:-<empty>}'"
    fi
}

# jq_type <name> <file> <filter> <type> — the value at filter has this jq type
# (string, number, boolean, array, object, null).
jq_type() {
    local name="$1" file="$2" filter="$3" expected="$4" actual
    actual=$(jq -r "($filter) | type" "$file" 2>&1)
    if [[ "$actual" == "$expected" ]]; then
        _pass "$name"
    else
        _fail "$name" "expected type '$expected', got '${actual:-<empty>}'"
    fi
}

# has_keys <name> <file> <filter> <key>... — the object at filter has all keys.
has_keys() {
    local name="$1" file="$2" filter="$3"
    shift 3
    local missing=()
    for key in "$@"; do
        if [[ "$(jq -r "($filter) | has(\"$key\")" "$file" 2>&1)" != "true" ]]; then
            missing+=("$key")
        fi
    done
    if [[ ${#missing[@]} -eq 0 ]]; then
        _pass "$name"
    else
        _fail "$name" "missing key(s): ${missing[*]}"
    fi
}

# csv_header <name> <file> <expected-prefix> — the CSV header starts with this
# comma-separated prefix.
csv_header() {
    local name="$1" file="$2" expected="$3" actual
    actual=$(head -1 "$file" | tr -d '\r')
    if [[ "$actual" == "$expected"* ]]; then
        _pass "$name"
    else
        _fail "$name" "header is '$actual', expected it to start with '$expected'"
    fi
}

# skill_md_contains <name> <pattern> — the SKILL.md matches this grep -E pattern.
# Use to catch documentation drifting away from the API, in either direction.
skill_md_contains() {
    local name="$1" pattern="$2"
    if grep -qE "$pattern" "$SKILL_MD"; then
        _pass "$name"
    else
        _fail "$name" "SKILL.md has no match for /$pattern/"
    fi
}

# finish — print the summary, write summary.json, exit non-zero on any failure.
finish() {
    printf '\n  %s: %d passed, %d failed, %d skipped\n' "$SKILL_NAME" "$_PASS" "$_FAIL" "$_SKIP"
    {
        printf '{\n  "skill": "%s",\n  "passed": %d,\n  "failed": %d,\n  "skipped": %d,\n  "failures": [' \
            "$SKILL_NAME" "$_PASS" "$_FAIL" "$_SKIP"
        local first=1
        for f in ${_FAILURES+"${_FAILURES[@]}"}; do
            [[ $first -eq 0 ]] && printf ','
            printf '\n    %s' "$(printf '%s' "$f" | jq -Rs .)"
            first=0
        done
        [[ $first -eq 0 ]] && printf '\n  '
        printf ']\n}\n'
    } >"$WORK/summary.json"
    [[ $_FAIL -eq 0 ]]
}
