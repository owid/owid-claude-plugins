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
- OWID data uses harmonized country names and region codes (ISO alpha-3 for standard countries, custom codes for unusual regions like OWID_WRL for World)
- If external data has ISO alpha-3 codes, use those for joining
- If external data uses other identifiers (e.g. ISO alpha-2), map them to ISO alpha-3 first
- OWID uses modern country borders for historical data (e.g. Italy population in 1 CE uses modern Italian borders)
- Regional aggregates like "Europe" or "Sub-saharan Africa" usually differ between sources - do not join these by name
- When external data lacks a year column, determine the correct year from documentation or ask the user, then join on that year
## OWID data that is commonly used for joins

Some data that OWID provides, like population, is especially useful, for example to convert metrics into per-capita data. Recommendations for these are given below. To understand how to download data given a chart url, consult the fetch-chart-data skill.

For population there are two relevant time series.
- the long-run population numbers, used in the chart https://ourworldindata.org/grapher/population that merges several data sources to provide data from 10.000 BCE to the present (up to one to three years ago). The precise temporal extent can be quickly queried by fetching the metadata for this chart, and reading `$.columns.[0].timespan`
- the UN population data from 1950 with projections up to 2100 (medium scenario) used in the chart https://ourworldindata.org/grapher/population-with-un-projections . Use this if you need years more recent than what is available in the long-run population dataset or for the current or future years.

For GDP per capita, there are similarly two time series:
- the long-run gdp data, used in the chart https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database that has data for many countries from 1820, but does not have data for the last few years
- data from the World Bank, used in the chart https://ourworldindata.org/grapher/gdp-per-capita-worldbank that has data from 1990 to the present (up to one or two years ago)