#!/usr/bin/env bash
# Contract tests for joining-data. This skill hardcodes four chart slugs and
# makes claims about their temporal coverage, so the checks below verify that
# those charts still exist and still cover the periods the skill promises.
source "$EVALS_LIB/assert.sh"

GRAPHER="https://ourworldindata.org/grapher"

# slug|claim|earliest-year-must-be-at-most|latest-year-must-be-at-least
CHARTS=(
    "population|long-run population, 10,000 BCE to present|-10000|2020"
    "population-with-un-projections|UN population, 1950 with projections to 2100|1950|2100"
    "gdp-per-capita-maddison-project-database|long-run GDP per capita from 1820|1820|2018"
    "gdp-per-capita-worldbank|World Bank GDP per capita from 1990|1990|2022"
)

# Every column that declares a timespan, as {start, end} integers. jq allows
# comments, so the filter can explain itself rather than being a 150-character
# line at the call site.
TIMESPANS='
  [ .columns[]
    | select(has("timespan"))
    | .timespan
    | capture("^(?<s>-?[0-9]+)-(?<e>[0-9]+)$")
    | { start: (.s | tonumber), end: (.e | tonumber) } ]
'

for entry in "${CHARTS[@]}"; do
    IFS='|' read -r slug claim min_start min_end <<<"$entry"
    section "$slug — $claim"
    meta="$WORK/$slug.metadata.json"
    if ! fetch "$GRAPHER/$slug.metadata.json" "$meta"; then
        continue
    fi

    # NOTE: metadata .columns is an object keyed by column name, so it must be
    # read with to_entries — not with an array index. SKILL.md currently tells
    # agents to read `$.columns.[0].timespan`, which is not a valid path.
    jq_true "metadata has at least one column with a timespan" "$meta" \
        '[.columns[] | select(has("timespan"))] | length > 0'

    # Coverage is the union across columns: population-with-un-projections
    # splits estimates (1950-2023) and the medium projection (2024-2100) into
    # separate columns, so neither column alone proves the claim.
    starts=$(jq -r "$TIMESPANS | map(.start) | min" "$meta" 2>/dev/null)
    ends=$(jq -r "$TIMESPANS | map(.end) | max" "$meta" 2>/dev/null)
    if [[ -n "$starts" && -n "$ends" && "$starts" != "null" && "$ends" != "null" ]]; then
        note "coverage across all columns: $starts to $ends"
        ok "coverage starts at or before $min_start" test "$starts" -le "$min_start"
        ok "coverage extends to at least $min_end" test "$ends" -ge "$min_end"
    else
        _fail "timespans are parseable" "could not parse timespans from $slug"
    fi

    skill_md_contains "SKILL.md still references $slug" "grapher/$slug"
done

section "Entity codes are joinable as documented"
# NOTE: csvType=filtered applies the chart's own default entity selection, not
# "every entity". For the population chart that default is continents plus World,
# so a country-level check has to pass an explicit country filter.
DEFAULTS="$WORK/population-default-2020.csv" # the chart's own entity selection
COUNTRIES="$WORK/population-2020.csv"        # an explicit country filter

if fetch "$GRAPHER/population.csv?csvType=filtered&time=2020" "$DEFAULTS"; then
    ok "custom OWID_ codes exist for non-standard regions" \
        test -n "$(csv_column "$DEFAULTS" code | grep '^OWID_')"
    ok "World is coded OWID_WRL as documented" \
        test -n "$(csv_column "$DEFAULTS" code | grep -x 'OWID_WRL')"
    note "default selection for this chart: $(csv_column "$DEFAULTS" code | sort -u | tr '\n' ' ')"
fi

if fetch "$GRAPHER/population.csv?csvType=filtered&country=USA~DEU~FRA&time=2020" "$COUNTRIES"; then
    csv_column_set "Code column holds ISO alpha-3 codes for standard countries" \
        "$COUNTRIES" code "DEU FRA USA"
    csv_column_matches "every Code is 3 uppercase letters or an OWID_ code" \
        "$COUNTRIES" code '^([A-Z]{3}|OWID_[A-Z_0-9]+)$'
fi

section "A real join works end to end"
# The skill's headline use case: join an OWID metric with OWID population to get
# a per-capita figure. If duckdb can join the two CSVs on code+year, the
# harmonisation claim holds in practice.
if command -v duckdb >/dev/null 2>&1; then
    if fetch "$GRAPHER/annual-co2-emissions-per-country.csv?csvType=filtered&country=USA~GBR~CHN&time=2020" "$WORK/co2.csv" &&
        fetch "$GRAPHER/population.csv?csvType=filtered&country=USA~GBR~CHN&time=2020" "$WORK/pop.csv"; then
        joined=$(duckdb -noheader -list -c "
            SELECT count(*) FROM read_csv_auto('$WORK/co2.csv') c
            JOIN read_csv_auto('$WORK/pop.csv') p USING (Code, Year)
            WHERE c.Code IS NOT NULL;" 2>&1)
        if [[ "$joined" == "3" ]]; then
            _pass "duckdb joins CO2 and population on Code+Year for 3 countries"
        else
            _fail "duckdb joins CO2 and population on Code+Year for 3 countries" "got: $joined"
        fi
    fi
else
    skip "duckdb join smoke test" "duckdb not installed"
fi

finish
