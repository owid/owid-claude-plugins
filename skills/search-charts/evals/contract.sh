#!/usr/bin/env bash
# Contract tests for search-charts: does /api/search still behave the way
# SKILL.md says it does? Run via ../../../evals/run-contract-tests.sh
source "$EVALS_LIB/assert.sh"

API="https://ourworldindata.org/api/search"
COMMON="$WORK/search-common.json"
BROAD="$WORK/search-broad.json"
NONCHART="$WORK/search-nonchart.json"
EMPTY="$WORK/search-empty.json"

section "Endpoint and response envelope"
if fetch "$API?q=life+expectancy&hitsPerPage=5" "$COMMON"; then
    has_keys "envelope has the documented SearchResult fields" "$COMMON" "." \
        query results nbHits page nbPages hitsPerPage
    jq_type "results is an array" "$COMMON" '.results' array
    jq_true "a common query returns hits" "$COMMON" '.nbHits > 0'
    jq_true "hitsPerPage caps the result count" "$COMMON" '(.results | length) <= 5'
    jq_eq "page is 0-indexed by default" "$COMMON" '.page' 0
    jq_eq "query is echoed back" "$COMMON" '.query' 'life expectancy'
fi

section "Pagination"
if fetch "$API?q=energy&hitsPerPage=5&page=1" "$WORK/search-page1.json"; then
    jq_eq "requesting page=1 returns page 1" "$WORK/search-page1.json" '.page' 1
fi

section "Hit shape (BaseSearchChartHit)"
if fetch "$API?q=energy&hitsPerPage=50" "$BROAD"; then
    jq_true "every hit has url, title, slug, type" "$BROAD" \
        '[.results[] | has("url") and has("title") and has("slug") and has("type")] | all'
    jq_true "every hit has availableEntities as an array" "$BROAD" \
        '[.results[] | .availableEntities | type == "array"] | all'
    jq_true "every hit has availableTabs as an array" "$BROAD" \
        '[.results[] | .availableTabs | type == "array"] | all'
    jq_true "every type is one of the documented ChartRecordType values" "$BROAD" \
        '[.results[].type] | unique | inside(["chart", "explorerView", "multiDimView"])'
    jq_true "chart urls are absolute ourworldindata.org urls" "$BROAD" \
        '[.results[].url | startswith("https://ourworldindata.org/")] | all'

    # SKILL.md's BaseSearchChartHit marks objectID as required. If this fails,
    # the schema in SKILL.md is stale — the field is not worth documenting.
    jq_true "objectID is present on every hit (documented as required)" "$BROAD" \
        '[.results[] | has("objectID")] | all'
fi

section "Non-chart record types"
# Which record types a query returns is not stable: q=energy+mix returned mostly
# explorerView hits one hour and only multiDimView hits the next. So assert each
# type's documented shape only when that type is actually present in the sample,
# and skip loudly when it is not. Without the skip, a section that tested nothing
# looks like a section that passed, because jq's `all` is true of an empty array.
if fetch "$API?q=life+expectancy&hitsPerPage=100" "$NONCHART"; then
    note "types present: $(jq -r '[.results[].type] | group_by(.) | map("\(.[0])=\(length)") | join(" ")' "$NONCHART")"
    jq_true "at least one non-chart record type is represented" "$NONCHART" \
        '[.results[] | select(.type != "chart")] | length > 0'
    jq_true "non-chart hits carry queryParams" "$NONCHART" \
        '[.results[] | select(.type != "chart") | has("queryParams")] | all'

    # SKILL.md marks explorerType required on SearchExplorerViewHit, and
    # chartConfigId required on SearchMultiDimViewHit.
    documented_field() {
        local record_type="$1" field="$2" name count
        name="$record_type hits carry $field (documented as required)"
        count=$(jq "[.results[] | select(.type == \"$record_type\")] | length" "$NONCHART")
        if [[ "$count" -eq 0 ]]; then
            skip "$name" "no $record_type hits in this sample"
            return
        fi
        jq_true "$name" "$NONCHART" \
            "[.results[] | select(.type == \"$record_type\") | has(\"$field\")] | all"
    }
    documented_field explorerView explorerType
    documented_field multiDimView chartConfigId
fi

section "Behaviour on a query with no real match"
if fetch "$API?q=zzzzqqqx+not+a+real+topic&hitsPerPage=5" "$EMPTY"; then
    jq_true "the request succeeds rather than erroring" "$EMPTY" '.results | type == "array"'
    # Algolia falls back to low-relevance hits instead of returning nothing, so
    # nbHits == 0 is NOT the signal that a topic is missing. An agent that trusts
    # hit count alone will present unrelated charts as matches.
    jq_true "a nonsense query still returns hits (relevance is not filtered)" "$EMPTY" '.nbHits > 0'
    note "top hit for a nonsense query: $(jq -r '.results[0].title // "<none>"' "$EMPTY")"
fi

section "Documentation drift: the tab → URL parameter table"
# Every tab name the API can return must appear in SKILL.md's mapping table,
# otherwise an agent cannot build a ?tab= url for it.
if [[ -s "$BROAD" && -s "$NONCHART" && -s "$COMMON" ]]; then
    documented=$(sed -n 's/^| `\([A-Za-z][A-Za-z]*\)` | `[a-z-][a-z-]*` |.*/\1/p' "$SKILL_MD" | sort -u)
    observed=$(jq -r '.results[].availableTabs[]' "$BROAD" "$NONCHART" "$COMMON" 2>/dev/null | sort -u)
    undocumented=$(comm -13 <(printf '%s\n' "$documented") <(printf '%s\n' "$observed"))
    if [[ -z "$undocumented" ]]; then
        _pass "every observed availableTabs value is in the mapping table"
    else
        _fail "every observed availableTabs value is in the mapping table" \
            "missing from the table: $(printf '%s' "$undocumented" | tr '\n' ' ')"
    fi
    note "observed tabs: $(printf '%s' "$observed" | tr '\n' ' ')"
else
    # Never fall through silently: a check that did not run must not look like a
    # check that passed.
    skip "every observed availableTabs value is in the mapping table" \
        "an earlier search request failed, so there is no sample to compare against"
fi

section "Documentation drift: example command in SKILL.md"
skill_md_contains "SKILL.md still points at /api/search" 'ourworldindata\.org/api/search'
skill_md_contains "SKILL.md documents the hitsPerPage parameter" '`hitsPerPage`'

finish
