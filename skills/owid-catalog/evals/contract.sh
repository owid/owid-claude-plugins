#!/usr/bin/env bash
# Contract tests for owid-catalog. Unlike the HTTP skills, the contract here is
# a Python API, so the checks live in contract_check.py (which needs the library
# installed) and this file just runs it and translates the output.
source "$EVALS_LIB/assert.sh"

CHECKER="$SKILL_DIR/evals/contract_check.py"
OUT="$WORK/contract_check.out"

section "Documentation drift"
skill_md_contains "SKILL.md documents the uv inline-dependency install" 'dependencies = \["owid-catalog"\]'
skill_md_contains "SKILL.md documents the three search kinds" 'kind="indicator"'
skill_md_contains "SKILL.md warns about rich display and recommends to_csv" 'to_csv'

section "Python API surface"
if ! command -v uv >/dev/null 2>&1; then
    skip "owid-catalog API checks" "uv not installed (see install-prerequisites-macos.sh)"
    finish
    exit $?
fi

# The library is installed into an ephemeral uv environment, so the first run of
# the day takes a while. Failures are reported per check by the script itself.
if uv run --no-project --script "$CHECKER" >"$OUT" 2>"$WORK/contract_check.err"; then
    :
else
    status=$?
    if [[ ! -s "$OUT" ]]; then
        _fail "contract_check.py runs" "exited $status; stderr: $(tail -3 "$WORK/contract_check.err" | tr '\n' ' ')"
        finish
        exit $?
    fi
fi

while IFS=$'\t' read -r status name detail; do
    case "$status" in
    PASS) _pass "$name" ;;
    FAIL) _fail "$name" "$detail" ;;
    SKIP) skip "$name" "$detail" ;;
    NOTE) note "$name" ;;
    esac
done <"$OUT"

finish
