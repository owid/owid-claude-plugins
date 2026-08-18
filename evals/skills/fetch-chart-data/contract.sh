#!/usr/bin/env bash
# Contract tests for fetch-chart-data: the .metadata.json / .csv endpoints and
# the query parameters SKILL.md documents.
source "$EVALS_LIB/assert.sh"

CHART="https://ourworldindata.org/grapher/life-expectancy"
PARAMS="useColumnShortNames=true&csvType=filtered&country=USA~GBR&time=2000..2020"

META="$WORK/metadata.json"            # metadata for the filtered request below
CSV_SHORT="$WORK/data-shortnames.csv" # the recommended base parameters
CSV_PLAIN="$WORK/data-plain.csv"      # without useColumnShortNames
DAILY="$WORK/daily.csv"               # a chart with Day rather than Year

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
    all_match "every column has titleShort and titleLong" "$META" '.columns[]' \
        'has("titleShort") and has("titleLong")'
    all_match "every column has citationShort and citationLong" "$META" '.columns[]' \
        'has("citationShort") and has("citationLong")'
    all_match "every column has fullMetadata" "$META" '.columns[]' 'has("fullMetadata")'
    all_match "shortName is present when useColumnShortNames=true" "$META" '.columns[]' \
        'has("shortName")'
    all_match "timespan looks like a year range" "$META" '.columns[] | select(has("timespan"))' \
        '.timespan | test("^-?[0-9]+-[0-9]+$")'

    # SKILL.md tells agents to pay special attention to descriptionKey, so its
    # type has to be right: a markdown bullet string and an array of strings need
    # different handling.
    all_match "descriptionKey is a string, as documented" "$META" \
        '.columns[] | select(has("descriptionKey"))' '.descriptionKey | type == "string"'
    all_match "descriptionKey is a markdown bulleted list" "$META" \
        '.columns[] | select(has("descriptionKey"))' '.descriptionKey | test("^- ")'
    note "descriptionKey type: $(jq -r '[.columns[] | select(has("descriptionKey")) | .descriptionKey | type] | unique | join(", ")' "$META")"
    note "columns: $(jq -r '.columns | keys | join(", ")' "$META")"
fi

section "CSV endpoint with the recommended base parameters"
if fetch "$CHART.csv?$PARAMS" "$CSV_SHORT"; then
    csv_min_rows "the csv has data rows" "$CSV_SHORT" 1
    csv_has_columns "the documented entity, code and year columns exist" "$CSV_SHORT" entity code year
    csv_column_set "the country filter is respected" "$CSV_SHORT" code "GBR USA"
    csv_column_range "the time filter is respected" "$CSV_SHORT" year 2000 2020

    # SKILL.md tells agents to drop the Entity column with `cut -d',' -f2-`,
    # which leaves Code first only while Code is the second column.
    ok "cut -d, -f2- leaves the Code column first" \
        test "$(head -1 "$CSV_SHORT" | cut -d, -f2- | cut -d, -f1)" = "code"

    data_columns=$(head -1 "$CSV_SHORT" | cut -d, -f4-)
    ok "short column names contain no spaces" \
        test "$data_columns" = "${data_columns// /}"

    # useColumnShortNames=true lowercases the first three headers. SKILL.md now
    # documents both forms and tells agents to match case-insensitively; these two
    # checks pin down which call produces which.
    csv_header "useColumnShortNames=true lowercases the first three headers" "$CSV_SHORT" "entity,code,year"
fi

section "CSV endpoint without useColumnShortNames"
if fetch "$CHART.csv?csvType=filtered&country=USA&time=2020" "$CSV_PLAIN"; then
    csv_header "header is Entity,Code,Year" "$CSV_PLAIN" "Entity,Code,Year"
    long_titles=$(head -1 "$CSV_PLAIN" | cut -d, -f4-)
    ok "long column titles are used instead of short names" \
        test "$long_titles" != "${long_titles// /}"
fi

section "Daily-resolution charts use a Day column"
if fetch "https://ourworldindata.org/grapher/daily-cases-covid-region.csv?csvType=filtered&time=2021-01-01..2021-01-31" "$DAILY"; then
    csv_has_columns "the third column is Day rather than Year" "$DAILY" day
    csv_column_matches "Day values are YYYY-MM-DD" "$DAILY" day '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
fi

section "Documentation drift"
skill_md_contains "SKILL.md documents the .metadata.json suffix" '\.metadata\.json'
skill_md_contains "SKILL.md documents the recommended base parameters" 'useColumnShortNames=true&csvType=filtered'

finish
