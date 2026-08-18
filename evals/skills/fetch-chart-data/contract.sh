#!/usr/bin/env bash
# Contract tests for fetch-chart-data: the .metadata.json / .csv endpoints and
# the query parameters SKILL.md documents.
source "$EVALS_LIB/assert.sh"

CHART="https://ourworldindata.org/grapher/life-expectancy"
PARAMS="useColumnShortNames=true&csvType=filtered&country=USA~GBR&time=2000..2020"
META="$WORK/metadata.json"
CSV_SHORT="$WORK/data-shortnames.csv"
CSV_PLAIN="$WORK/data-plain.csv"

section "Metadata endpoint"
if fetch "$CHART.metadata.json?$PARAMS" "$META"; then
    has_keys "top level has chart, columns, dateDownloaded" "$META" "." chart columns dateDownloaded
    jq_type "columns is an object keyed by column name" "$META" '.columns' object
    jq_true "columns is non-empty" "$META" '(.columns | length) > 0'
    jq_true "chart.title is a non-empty string" "$META" '(.chart.title | type == "string") and (.chart.title | length > 0)'
    jq_true "chart.citation is present" "$META" '.chart | has("citation")'
    jq_true "dateDownloaded is YYYY-MM-DD" "$META" '.dateDownloaded | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")'
    jq_true "activeFilters echoes the query params" "$META" \
        '.activeFilters.country == "USA~GBR" and .activeFilters.time == "2000..2020"'

    section "Metadata column shape (MetadataColumn)"
    jq_true "every column has titleShort and titleLong" "$META" \
        '[.columns[] | has("titleShort") and has("titleLong")] | all'
    jq_true "every column has citationShort and citationLong" "$META" \
        '[.columns[] | has("citationShort") and has("citationLong")] | all'
    jq_true "every column has fullMetadata" "$META" '[.columns[] | has("fullMetadata")] | all'
    jq_true "shortName is present when useColumnShortNames=true" "$META" \
        '[.columns[] | has("shortName")] | all'
    jq_true "timespan looks like a year range" "$META" \
        '[.columns[] | select(has("timespan")) | .timespan | test("^-?[0-9]+-[0-9]+$")] | all'
    # SKILL.md types descriptionKey as string[], and tells agents to pay special
    # attention to it. If this fails, check what the API actually sends — a
    # markdown bullet string and an array of strings need different handling.
    jq_true "descriptionKey is an array of strings, as documented" "$META" \
        '[.columns[] | select(has("descriptionKey")) | .descriptionKey | type == "array"] | all'
    note "descriptionKey type: $(jq -r '[.columns[] | select(has("descriptionKey")) | .descriptionKey | type] | unique | join(", ")' "$META")"
    note "columns: $(jq -r '.columns | keys | join(", ")' "$META")"
fi

section "CSV endpoint with the recommended base parameters"
if fetch "$CHART.csv?$PARAMS" "$CSV_SHORT"; then
    ok "csv has more than a header row" test "$(wc -l <"$CSV_SHORT")" -gt 1
    ok "country filter is respected (only USA and GBR)" \
        bash -c "[ \"\$(tail -n +2 '$CSV_SHORT' | cut -d, -f2 | sort -u | tr '\n' ' ')\" = 'GBR USA ' ]"
    ok "time filter is respected (2000..2020)" \
        bash -c "years=\$(tail -n +2 '$CSV_SHORT' | cut -d, -f3 | sort -n); [ \"\$(echo \"\$years\" | head -1)\" -ge 2000 ] && [ \"\$(echo \"\$years\" | tail -1)\" -le 2020 ]"
    ok "column names contain no spaces when useColumnShortNames=true" \
        bash -c "! head -1 '$CSV_SHORT' | cut -d, -f4- | grep -q ' '"
    ok "the cut -d, -f2- token trick leaves Code as the first column" \
        bash -c "[ \"\$(head -1 '$CSV_SHORT' | cut -d, -f2- | cut -d, -f1 | tr 'A-Z' 'a-z')\" = 'code' ]"

    # SKILL.md documents the first three columns as "Entity", "Code", "Year".
    # With the recommended useColumnShortNames=true they come back lowercased,
    # so this check tells you whether the doc matches the recommended call.
    csv_header "header is Entity,Code,Year as documented" "$CSV_SHORT" "Entity,Code,Year"
fi

section "CSV endpoint without useColumnShortNames"
if fetch "$CHART.csv?csvType=filtered&country=USA&time=2020" "$CSV_PLAIN"; then
    csv_header "header is Entity,Code,Year" "$CSV_PLAIN" "Entity,Code,Year"
    ok "long column titles may contain spaces" \
        bash -c "head -1 '$CSV_PLAIN' | cut -d, -f4- | grep -q '[A-Za-z]'"
fi

section "Daily-resolution charts use a Day column"
if fetch "https://ourworldindata.org/grapher/daily-cases-covid-region.csv?csvType=filtered&time=2021-01-01..2021-01-31" "$WORK/daily.csv"; then
    ok "third column is Day for sub-annual data" \
        bash -c "[ \"\$(head -1 '$WORK/daily.csv' | cut -d, -f3 | tr 'A-Z' 'a-z')\" = 'day' ]"
    ok "Day values are YYYY-MM-DD" \
        bash -c "tail -n +2 '$WORK/daily.csv' | cut -d, -f3 | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'"
fi

section "Documentation drift"
skill_md_contains "SKILL.md documents the .metadata.json suffix" '\.metadata\.json'
skill_md_contains "SKILL.md documents the recommended base parameters" 'useColumnShortNames=true&csvType=filtered'

finish
