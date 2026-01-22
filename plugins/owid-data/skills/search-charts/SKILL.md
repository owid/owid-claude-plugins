---
description: "Our World In Data offers thousands of charts and related data on many important topics - from global population data, energy and electricity, economic data like GDP or poverty, health data like causes of death or prevalence of diseases, to data on democracy, violence and war. This skill describes how to effectively search for charts to either show visually or download the data for."
allowed-tools:
- "Bash(curl:*)"
- "Bash(cat:*)"
- "Bash(jq:*)"
---

Searching for charts is done via an http request to
https://ourworldindata.org/api/search

The result is a json that adheres to this schema:
```typescript
export enum ChartRecordType {
    Chart = "chart",
    ExplorerView = "explorerView",
    MultiDimView = "multiDimView",
}

export enum ExplorerType {
    Grapher = "grapher",
    Indicator = "indicator",
    Csv = "csv",
}

type GrapherTabName = "LineChart" | "ScatterPlot" | "StackedArea" | "DiscreteBar" | "StackedDiscreteBar" | "SlopeChart" | "StackedBar" | "Marimekko" | "Table" | "WorldMap"

interface BaseSearchChartHit {
    url: string
    title: string
    slug: string
    availableEntities: string[]
    originalAvailableEntities?: string[]
    objectID: string
    variantName?: string
    subtitle?: string
    availableTabs: GrapherTabName[]
}

type SearchChartViewHit = BaseSearchChartHit & {
    type: ChartRecordType.Chart
}

type SearchExplorerViewHit = BaseSearchChartHit & {
    type: ChartRecordType.ExplorerView
    explorerType: ExplorerType
    queryParams: string
}

type SearchMultiDimViewHit = BaseSearchChartHit & {
    type: ChartRecordType.MultiDimView
    queryParams: string
    chartConfigId: string
}

export type SearchChartHit =
    | SearchChartViewHit
    | SearchExplorerViewHit
    | SearchMultiDimViewHit

interface SearchResult {
    query: string
    results: SearchChartHit[]
    nbHits: number
    page: number
    nbPages: number
    hitsPerPage: number
}
```

The response json can be quite verbose, so don't pull the search results into your context window but instead use `jq` or a programming language to extract the information you need (often title, subtitle and url are the most relevant fields for any given hit).

The search is a keyword based search operated by Algolia. The query param `q` is used to submit the search string. The vocabulary used at OWID is often following that of topic specialists, so search for "death rate malaria" instead of "people who died from malaria", or "literacy" instead of "people who can read".

Results are sorted by relevance - usually the first page of hits will contain the best results. If you get a large number of charts back, and the top charts don't seem to be ideal matches, try refining the search with additional terms. If you don't get any results, try a search with slightly different terms or synonyms.

It is often a good idea to communicate the top hits back to the user and either ask them which chart/data to proceed with or to pick the best but let them know the title of a few others that were also considered.

To fetch either the visual chart or the data, use the url property as is verbatim, including all query params. Consult the fetch-chart-image or fetch-chart-data skills for more details on how best to request either one.