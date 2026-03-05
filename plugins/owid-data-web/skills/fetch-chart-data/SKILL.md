---
description: "This skill describes how to fetch data for an Our World In Data chart, once the relevant chart URL has been identified. Consult this skill to understand the possible query params to get the best results and to understand the response. Use it you need to fetch data and have already identified the relevant chart URL."
allowed-tools:
- "Bash(curl:*)"
- "Bash(cat:*)"
- "Bash(jq:*)"
---

Once you have identified a chart url like `https://ourworldindata.org/grapher/literate-and-illiterate-world-population`, there are two key artifacts you can retrieve: the metadata json file, and the data csv file. The urls for both are `$CHARTURL.metadata.json` and `$CHARTURL.csv` respectively.

Always fetch the metadata first before fetching the data as it gives important context. Pay special attention to the descriptionKey field if it is given.

## Query Parameters

Both endpoints support these query parameters to filter data and reduce response size:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `useColumnShortNames` | Use short column names without spaces | `true` |
| `csvType` | Use `filtered` to respect country/time filters | `filtered` |
| `country` | Filter to specific countries (ISO3 codes joined with `~`) | `USA~GBR~CHN` |
| `time` | Filter to time range | `2000..2020` or `2015` |
| `tab` | Chart visualization type | `map`, `line`, `table` |

**Recommended base parameters:** `?useColumnShortNames=true&csvType=filtered`

Example with filters:
```
https://ourworldindata.org/grapher/life-expectancy.csv?useColumnShortNames=true&csvType=filtered&country=USA~GBR&time=2000..2020
```

## Token Optimization

To reduce token usage when working with the data:

1. **Remove the Entity column** - The CSV has both "Entity" (country name) and "Code" (ISO3). The Code column is sufficient for analysis and joining. Remove Entity to save tokens:
   ```bash
   curl -s "$URL" | cut -d',' -f2-
   ```

2. **Filter metadata** - The full metadata is verbose. Key fields to extract:
   - `chart.title`, `chart.subtitle`, `chart.note`, `chart.citation`
   - `columns.*.titleShort`, `columns.*.descriptionShort`, `columns.*.unit`, `columns.*.shortUnit`

   Skip these verbose fields: `titleLong`, `citationLong`, `fullMetadata`, `owidVariableId`, `lastUpdated`, `nextUpdate`

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

The other columns are the data columns, which are the time series that power the chart.

Prefer to download the CSV and metadata into a file and process it from there.
