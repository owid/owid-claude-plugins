---
description: "This skill describes how to fetch data for an Our World In Data chart, once the relevant chart URL has been identified. Consult this skill to understand the possible query params to get the best results and to understand the response. Use it when the user asks for data."
allowed-tools:
- "Bash(curl:*)"
- "Bash(cat:*)"
- "Bash(jq:*)"
---

Once you have identified a chart url like `https://ourworldindata.org/grapher/literate-and-illiterate-world-population`, there are two key artifacts you can retrieve: the metadata json file, and the data csv file. The urls for both are `$CHARTURL.metadata.json` and `$CHARTURL.csv` respectively. Set the query parameter `useColumnShortNames` to `true` so that columns in the csv don't contain whitespaces and are easier to work with in code.

Always fetch the metadata first before fetching the data as it gives important context. Pay special attention to the desciptionKey field if it is given.

## Metadata

The metadata outlines key information about the chart, as well as information on each time series used in the chart, each of which will be one column in the data file.

The typescript type of the metadata json file is as follows:
```typescript

export type MetadataColumn = {
    titleShort: string
    titleLong: string
    descriptionShort?: string
    descriptionKey?: string[] // curated by experts at Our World In Data to collect important information or caveats about this data. If they are given, it might make sense to surface this information to the user.
    descriptionProcessing?: string // notes about how this data was processed by Our World In Data in case it is not a straightforward republishing from the original source
    shortUnit?: string
    unit?: string
    timespan?: string // timespan of the data covered in the form `YYYY-YYYY`
    tolerance?: number // default tolerance for this time series. Data from Our World In Data is sometime sparse for some countries. In these cases, OWID charts use this tolerance threshold to display values on charts from neighboring years up to this limit
    type?: string // Numeric, Categorical, Ordinal, Integer
    conversionFactor?: number // Conversion factor that was used internally. This is already applied for the data in the csv, don't apply it again
    shortName?: string // short column name that matches the csv column names when the useColumnShortNames query param is set to true
    lastUpdated?: string
    nextUpdate?: string
    citationShort: string
    citationLong: string
    fullMetadata: string // URL of the expanded metadata for this time series
}

export type ChartMetadata = {
    title?: string
    subtitle?: string
    note?: string
    xAxisLabel?: string
    yAxisLabel?: string
    citation: string
    originalChartUrl?: string
    selection: string[]
}

export type GrapherMetadataResponse = {
    chart: ChartMetadata
    columns: Record<string, MetadataColumn>
    /** Date in YYYY-MM-DD format */
    dateDownloaded: string
    /** Filtered grapher query params, or undefined if no params */
    activeFilters?: Record<string, string>
}
```

## CSV Structure

The high level structure of the CSV file is that each row is an observation for an entity (usually a country or region) and a timepoint (usually a year).

The first two columns in the CSV file are "Entity" and "Code". "Entity" is the name of the entity (e.g. "United States"). "Code" is the OWID internal entity code that we use if the entity is a country or region. For normal countries, this is the same as the [iso alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) code of the entity (e.g. "USA") - for non-standard countries like historical countries these are custom codes.

The third column is either "Year" or "Day". If the data is annual, this is "Year" and contains only the year as an integer. If the column is "Day", the column contains a date string in the form "YYYY-MM-DD".

The other columns are the data column, which are the time series that power the chart.

Prefer to download the CSV and metadata into a file and process it from there.