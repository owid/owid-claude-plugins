---
name: "dataviz-best-practices"
description: "Data visualization best practices for creating clear, effective, and accessible charts. Use this skill when creating, reviewing, or improving any data visualization — charts, maps, scatter plots, or any graphical representation of data. Apply these principles when generating chart code, suggesting chart types, or giving feedback on visualizations."
---

# Data Visualization Best Practices

Principles for effective data visualization, based on the "How to Visualize Data Effectively" framework by Max Roser and Marwa Boukarim (Oxford Blavatnik School of Government). Apply these when creating or reviewing any chart.

## I. Audience & Purpose

Before making any design decisions, answer two questions:

1. **Why are you making this visualization?** Have a clear insight or message. Purpose ranges from **explanatory** (providing evidence for a point) to **exploratory** (letting readers discover patterns).
2. **Who is your audience?** Their prior knowledge determines how much context, labeling, and explanation you need.

## II. Choosing the Right Chart Type

The chart type should be driven by (1) your purpose and (2) the nature of the data. Different chart types have different strengths:

| Chart Type | Best For | Limitations |
|---|---|---|
| **Connected dot plot** | Showing change/range between two time points; many entities; compact height | No rank changes; no intermediate data points; no anomaly detection |
| **Slope chart** | Showing rank changes; visual slope encodes magnitude | Limited to two time points; gets messy with many entities |
| **Bar chart** (paired/grouped) | Comparing entities; showing rank changes | Limited time points; messy with many entities |
| **Line chart** | Change over time; rank comparison; revealing anomalies, drops, peaks; comparing trends | Difficult with many overlapping lines |
| **Stacked area chart** | Showing changes to totals and composition | Hard to compare individual entities |
| **Choropleth map** | Showing many entities; geographic/continental patterns | Poor for precise comparisons; small countries hard to see; no temporal detail |
| **Scatter plot** | Correlation between two variables; comparing entities on two dimensions | Can get overcrowded with many data points |

**Line charts are the most versatile** — they uniquely reveal trends, anomalies, and rank changes over continuous time.

### When to use pie charts

Pie charts are generally poor for multiple categories. They work well in only two cases:
- Showing a roughly **50/50 split** between two categories
- Emphasizing how **extremely small** one fraction is relative to the whole

For multiple categories, use a **bar chart** instead.

### Reference tools for chart type selection

- **FT Visual Vocabulary** (ft.com/vocabulary) — maps analytical purpose to chart types
- **ChartCatalogue.com** and **DataVizProject.com** — examples of each chart type done well

## III. Process

1. **Sketch first** on paper — it's faster than any software
2. Get it into a shareable format
3. **Get feedback** from readers, colleagues, peers
4. **Iterate** — redo visualizations again and again

The workflow is: Sketch → Feedback → Sketch → ... → Final output. Don't jump straight into code or design software.

## IV. Visualizing the Data

### Axes

- **Y-axis at zero:** Starting above zero is acceptable when highlighting small differences, but you **must use a dashed baseline** to signal the truncation. A solid baseline at a non-zero start is deceptive.
- Choose between starting at zero (showing overall magnitude) or above zero (showing relative change) based on your purpose.

### Precision

- **Round numbers** to an appropriate level in chart labels (e.g., "5.95M" not "5,952,156"). Exact figures belong in tables, not chart annotations.
- Remove unnecessary decimal places.

### Avoid distortions

- **Never use 3D charts.** 3D perspective effects distort perception of values. Always use flat, 2D representations.
- Avoid decorative elements that distort data perception.

### Icons and illustrations

- Simple, widely recognizable icons **can** help readers quickly identify categories.
- Excessive or complex illustrations distract. Use sparingly.

### Grid lines

- Keep grid lines **faint gray**, never black.
- Always use a **solid line for zero**.
- Remove grid lines entirely when numeric labels appear on every data point.
- Ask: "Are these grid lines helpful to the reader but muted and not distracting?"

### Avoiding overcrowding

- **Too many lines?** Use **small multiples** (one panel per entity) or reduce to a smaller sample of entities.
- **Too many scatter plot points?** Reduce **dot opacity** so overlapping points reveal density patterns naturally.
- **Dual y-axes: avoid them.** The scales are arbitrary and can mislead readers about relationships between series. Use two side-by-side charts or a connected scatter plot instead.

## V. Making the Visualization Understandable

### Titles

Two valid approaches:
- **Descriptive:** "Day of the year with peak cherry tree blossom in Kyoto, Japan"
- **Takeaway:** "Cherry trees have been blossoming earlier due to warmer spring temperatures"

Both are correct. Choose based on whether you want to describe the data or communicate the insight.

### Subtitles

- Keep brief. Don't cram methodology into the subtitle.
- Let axis labels and annotations carry explanatory weight.

### Text orientation

- **Horizontal text is always easier to read.** When labels are long or rotated, switch from vertical to horizontal bar charts.
- Avoid diagonal or vertical text labels.

### Annotations

Use annotations for two purposes:
1. **Context:** Mark events that affected the data (e.g., "Global financial crisis", "COVID pandemic")
2. **Key values:** Highlight specific data points with their values directly on the chart

### Reading examples

For unfamiliar chart types (e.g., scatter plots with reference lines), add explicit **reading examples** that walk the reader through interpreting specific data points.

### Direct labeling vs. legends

- **Label lines/bars directly** rather than using a separate legend. This eliminates back-and-forth eye movement.
- If a legend is needed, consider integrating it into the subtitle.
- **Legends can be charts themselves** — e.g., a legend for a map can show a distribution bar chart.

### Annotate values on maps

Place values directly on the map rather than forcing readers to cross-reference with the legend.

### Declutter

- Remove unnecessary labels, axes, annotations, and graphic elements.
- Integrate legends into subtitles where possible.
- Only include grid lines that genuinely help reading.

### Typography

- Use **sans-serif** fonts on the web (regular weight, sentence case)
- Font size **>12px** for readability
- Use **(almost) black text** — avoid low-contrast gray on white
- Don't use excessively thin, narrow, or condensed fonts
- Avoid excessive uppercase and excessive bold
- Create clear **information hierarchy** through font size, weight, and color

## VI. Colors

### Choosing palettes

- Use **ColorBrewer 2.0** for sequential and diverging palettes (especially maps)
- Use **Viz Palette** to test your palette across different chart types and check if colors are too similar

### Strategic use of color

- **Do not use bold colors for every data series.** This makes nothing stand out.
- Use **gray for context/background data** and reserve color only for what you want to emphasize.
- Color controls where readers look — use it intentionally.

### Accessibility

- **Contrast:** Use the WebAIM Contrast Checker (webaim.org/resources/contrastchecker) to ensure text and chart elements meet WCAG standards against their background.
- **Color blindness:** Simulate how your chart looks with deuteranomaly (red-green color blindness). **Direct labeling** of lines sidesteps color blindness issues entirely.
- **Grayscale:** Design so the chart remains legible when printed in black and white. Ensure sufficient tonal contrast between colors. Direct labeling helps here too.

## VII. Final Review Checklist

Before publishing, ask:

1. **Can it be simplified?** Remove any unnecessary information or graphic elements.
2. **Can it be more focused?** Does color direct attention to what matters?
3. **Fresh eyes:** You suffer from the **curse of knowledge** — after working on a chart, you can no longer see how confusing it may be for a first-time reader. Ask a colleague, friend, or post on social media to check if others understand your visualization.
4. **Edit down:** Ruthlessly remove anything that doesn't serve the reader.
