---
name: "joining-data"
description: "This skill describes how to join data with Our World In Data data, e.g. when you want to calculate per capita data by using the OWID population data or when you want to create a scatter plot against GDP per capita using OWID's GDP data. It also applies to other cases where several data sources that each have data for multiple countries should be joined together."
allowed-tools:
- "Bash(duckdb:*)"
---
Our World in Data supplies a lot of important data at a national level for multiple years.

## Joining data

When joining data from Our World In Data with that of other sources, the following should be taken into account:
- OWID data usually comes as a dataframe with two dimensions: time (almost always the year) and entity (almost always the country and/or geographic region like continents or World)
- OWID country data uses harmonized country names and region codes. Region codes are iso alpha-3 for "normal" countries, plus a few special codes for unusual regions (e.g. OWID_WRL for World)
- If the non-OWID data has iso alpha-3 codes available, use that to join the data.
- If other standardized identifiers are used (e.g. iso alpha-2 codes), map them to iso alpha-3 codes first
- For historical data, OWID data uses modern country borders and keeps them constant across time. For example, the long run population data contains data for population in the year 1 CE for Italy - this is the population within the borders of modern day Italy.
- Merging regional aggregates (like "Europe" or "Sub-saharan Africa") depends very much on the definition of which countries are included. Usually these are not compatible between different data sources. Do not attempt to join these by name.
- When external data is used that has data for only one year, the year may be omitted in the data. In this case, understand the year to use from the documentation or by asking the user, then join on the correct year in the OWID data.

## OWID data that is commonly used for joins

Some data that OWID provides, like population, is especially useful, for example to convert metrics into per-capita data. Recommendations for these are given below. To understand how to download data given a chart url, consult the fetch-chart-data skill.

For population there are two relevant time series.
- the long-run population numbers, used in the chart https://ourworldindata.org/grapher/population that merges several data sources to provide data from 10.000 BCE to the present (up to one to three years ago). The precise temporal extent can be quickly queried by fetching the metadata for this chart, and reading `$.columns.[0].timespan`
- the UN population data from 1950 with projections up to 2100 (medium scenario) used in the chart https://ourworldindata.org/grapher/population-with-un-projections

Pick the one that fits your use-case better (i.e. if you need estimates for the current year, future years or last year, use the UN population data).

For GDP per capita, there are similarly two time series:
- the long-run gdp data, used in the chart https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database that has data for many countries from 1820, but does not have data for the last few years
- data from the World Bank, used in the chart https://ourworldindata.org/grapher/gdp-per-capita-worldbank that has data from 1990 to the present (up to one or two years ago)