#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4>=4.12"]
# ///
"""Annotate an article HTML file with OWID fact-check highlights and chart previews.

Usage:
  annotate_article.py extract ARTICLE.html
      Print the article's readable text, one block per paragraph. Statement
      quotes passed to `annotate` must be exact substrings of this output.

  annotate_article.py annotate ARTICLE.html ANNOTATIONS.json -o OUTPUT.html
      Inject highlights and annotation cards into the article and write the
      result. Strips all <script> tags so the page renders statically.

Annotations JSON format:
{
  "source_url": "https://example.com/article",           // optional
  "annotations": [
    {
      "quote": "exact text from the extract output",
      "verdict": "supported" | "contradicted" | "mixed" | "context",
      "note": "1-3 sentences explaining the verdict, with concrete numbers",
      "chart_url": "https://ourworldindata.org/grapher/slug?country=~USA&time=1900..1950",
      "chart_title": "Chart title"                        // optional
    }
  ]
}
"""

import argparse
import html
import json
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

SKIP_PARENTS = {"script", "style", "noscript", "template", "head", "title", "svg", "iframe"}
BLOCK_TAGS = {"p", "li", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "figcaption"}

# Normalize typographic characters so quotes match regardless of how the
# article encodes apostrophes, dashes, and spaces.
CHAR_MAP = {
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-", "‑": "-",
    " ": " ",
    "…": "...",
}

VERDICTS = {
    "supported": ("✓ Supported by OWID data", "#1a7a3a"),
    "contradicted": ("✗ Contradicted by OWID data", "#b3261e"),
    "mixed": ("~ Partially supported", "#8a6d00"),
    "context": ("ℹ Context from OWID data", "#1a5a96"),
}


def collect_text_nodes(root):
    nodes = []
    for el in root.descendants:
        if not isinstance(el, NavigableString):
            continue
        if any(isinstance(p, Tag) and p.name in SKIP_PARENTS for p in el.parents):
            continue
        nodes.append(el)
    return nodes


def build_index(nodes):
    """Concatenate text nodes into one normalized string, collapsing whitespace.

    Returns (text, src) where src[i] = (node_index, char_index) of the source
    character that produced text[i].
    """
    chars, src = [], []
    prev_space = True
    for ni, node in enumerate(nodes):
        for ci, ch in enumerate(str(node)):
            n = CHAR_MAP.get(ch, ch)
            if ch.isspace() or n == " ":
                if prev_space:
                    continue
                chars.append(" ")
                src.append((ni, ci))
                prev_space = True
            else:
                for nc in n:
                    chars.append(nc)
                    src.append((ni, ci))
                prev_space = False
    return "".join(chars), src


def normalize_quote(q):
    chars = []
    prev_space = True
    for ch in q:
        n = CHAR_MAP.get(ch, ch)
        if ch.isspace() or n == " ":
            if not prev_space:
                chars.append(" ")
            prev_space = True
        else:
            chars.append(n)
            prev_space = False
    return "".join(chars).rstrip()


def block_ancestor(tag):
    for p in tag.parents:
        if isinstance(p, Tag) and p.name in BLOCK_TAGS:
            return p
    return tag


def extract(article_path):
    soup = BeautifulSoup(open(article_path, encoding="utf-8"), "html.parser")
    body = soup.body or soup
    blocks = body.find_all(list(BLOCK_TAGS))
    for block in blocks:
        # Only leaf-most blocks, to avoid printing nested content twice.
        if block.find(list(BLOCK_TAGS)):
            continue
        text, _ = build_index(collect_text_nodes(block))
        text = text.strip()
        if text:
            print(text)
            print()


def wrap_quote(soup, body, ann, ann_id):
    """Find the annotation's quote in the document and wrap it in <mark> tags.

    Returns the last <mark> created, or None if the quote was not found.
    Re-indexes the DOM on each call, so earlier mutations are accounted for.
    """
    nodes = collect_text_nodes(body)
    text, src = build_index(nodes)
    quote = normalize_quote(ann["quote"])
    if not quote:
        return None
    start = text.find(quote)
    if start == -1:
        start = text.lower().find(quote.lower())
    if start == -1:
        return None
    end = start + len(quote)

    # Group matched source characters by text node.
    ranges = {}
    for i in range(start, end):
        ni, ci = src[i]
        lo, hi = ranges.get(ni, (ci, ci))
        ranges[ni] = (min(lo, ci), max(hi, ci))

    last_mark = None
    first = True
    for ni in sorted(ranges):
        node = nodes[ni]
        lo, hi = ranges[ni]
        s = str(node)
        mark = soup.new_tag("mark", attrs={"class": f"owid-fc owid-fc-{ann['verdict']}"})
        if first:
            mark["id"] = f"owid-fc-{ann_id}"
            first = False
        mark.string = s[lo : hi + 1]
        parts = [p for p in (s[:lo], mark, s[hi + 1 :]) if p != ""]
        node.replace_with(*parts)
        last_mark = mark
    return last_mark


def build_card(soup, ann, ann_id):
    verdict = ann["verdict"]
    label, _ = VERDICTS[verdict]
    chart_url = ann.get("chart_url", "")
    chart_title = ann.get("chart_title") or "Interactive chart on Our World in Data"
    chart_html = ""
    if chart_url:
        chart_html = f"""
        <iframe src="{html.escape(chart_url, quote=True)}" loading="lazy"
                style="width:100%;height:600px;border:0;margin-top:0.75em;"
                allow="web-share; clipboard-write"></iframe>
        <p class="owid-fc-chart-link"><a href="{html.escape(chart_url, quote=True)}" target="_blank" rel="noopener">
            {html.escape(chart_title)} ↗</a></p>"""
    card_html = f"""
    <aside class="owid-fc-card owid-fc-card-{verdict}" id="owid-fc-card-{ann_id}">
        <p class="owid-fc-badge">{label}</p>
        <p class="owid-fc-note">{html.escape(ann["note"])}</p>
        {chart_html}
    </aside>"""
    return BeautifulSoup(card_html, "html.parser")


def build_summary(soup, annotations, matched_ids, source_url):
    counts = {}
    for ann in annotations:
        counts[ann["verdict"]] = counts.get(ann["verdict"], 0) + 1
    count_parts = ", ".join(
        f"{n} {v}" for v, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    items = ""
    for i, ann in enumerate(annotations):
        target = f"#owid-fc-card-{i}" if i in matched_ids else "#owid-fc-unmatched"
        quote = ann["quote"]
        if len(quote) > 120:
            quote = quote[:117] + "..."
        items += (
            f'<li class="owid-fc-sum-{ann["verdict"]}">'
            f'<a href="{target}">{html.escape(quote)}</a></li>\n'
        )
    src = (
        f'<p>Original article: <a href="{html.escape(source_url, quote=True)}">'
        f"{html.escape(source_url)}</a></p>"
        if source_url
        else ""
    )
    banner_html = f"""
    <section class="owid-fc-banner">
        <p class="owid-fc-banner-title">Fact-checked against Our World in Data</p>
        <p>{len(annotations)} statements checked: {count_parts}. Highlights in the text
           link to the underlying data. This annotation was generated by an AI agent —
           verify before citing.</p>
        {src}
        <ul>{items}</ul>
    </section>"""
    return BeautifulSoup(banner_html, "html.parser")


STYLE = """
<style>
mark.owid-fc { padding: 0 2px; border-radius: 2px; }
mark.owid-fc-supported { background: #d3eeda; box-shadow: inset 0 -2px 0 #1a7a3a; }
mark.owid-fc-contradicted { background: #f9dcda; box-shadow: inset 0 -2px 0 #b3261e; }
mark.owid-fc-mixed { background: #f9ecc7; box-shadow: inset 0 -2px 0 #8a6d00; }
mark.owid-fc-context { background: #d9e7f5; box-shadow: inset 0 -2px 0 #1a5a96; }
.owid-fc-card { margin: 1em 0; padding: 0.9em 1.1em; border-radius: 6px;
    background: #fafafa; border: 1px solid #ddd; border-left-width: 5px;
    font-family: system-ui, sans-serif; font-size: 0.9rem; scroll-margin-top: 2em; }
.owid-fc-card-supported { border-left-color: #1a7a3a; }
.owid-fc-card-contradicted { border-left-color: #b3261e; }
.owid-fc-card-mixed { border-left-color: #8a6d00; }
.owid-fc-card-context { border-left-color: #1a5a96; }
.owid-fc-badge { font-weight: 700; margin: 0 0 0.4em; text-transform: uppercase;
    font-size: 0.78rem; letter-spacing: 0.04em; }
.owid-fc-card-supported .owid-fc-badge { color: #1a7a3a; }
.owid-fc-card-contradicted .owid-fc-badge { color: #b3261e; }
.owid-fc-card-mixed .owid-fc-badge { color: #8a6d00; }
.owid-fc-card-context .owid-fc-badge { color: #1a5a96; }
.owid-fc-note { margin: 0; line-height: 1.45; }
.owid-fc-chart-link { margin: 0.4em 0 0; font-size: 0.82rem; }
.owid-fc-banner { margin: 1em auto; padding: 1em 1.3em; max-width: 42rem;
    background: #f2f7fb; border: 1px solid #c4d8e8; border-radius: 8px;
    font-family: system-ui, sans-serif; font-size: 0.9rem; }
.owid-fc-banner-title { font-weight: 700; font-size: 1rem; margin: 0 0 0.5em; }
.owid-fc-banner ul { margin: 0.6em 0 0; padding-left: 1.3em; }
.owid-fc-banner li { margin: 0.25em 0; }
.owid-fc-banner li::marker { font-size: 1.1em; }
.owid-fc-sum-supported::marker { content: "✓ "; color: #1a7a3a; }
.owid-fc-sum-contradicted::marker { content: "✗ "; color: #b3261e; }
.owid-fc-sum-mixed::marker { content: "~ "; color: #8a6d00; }
.owid-fc-sum-context::marker { content: "ℹ "; color: #1a5a96; }
.owid-fc-unmatched-section { max-width: 42rem; margin: 2em auto; }
</style>
"""


def annotate(article_path, annotations_path, output_path):
    soup = BeautifulSoup(open(article_path, encoding="utf-8"), "html.parser")
    spec = json.load(open(annotations_path, encoding="utf-8"))
    annotations = spec["annotations"]

    for ann in annotations:
        if ann["verdict"] not in VERDICTS:
            sys.exit(f"error: unknown verdict {ann['verdict']!r} (use one of {sorted(VERDICTS)})")

    # Scripts would re-hydrate/clobber the annotated DOM; the page must be static.
    for t in soup.find_all(["script", "noscript"]):
        t.decompose()

    body = soup.body or soup
    matched_ids = set()
    unmatched = []
    for i, ann in enumerate(annotations):
        mark = wrap_quote(soup, body, ann, i)
        card = build_card(soup, ann, i)
        if mark is not None:
            matched_ids.add(i)
            block_ancestor(mark).insert_after(card)
        else:
            unmatched.append((ann, card))
            print(f"warning: quote not found in article text: {ann['quote'][:80]!r}", file=sys.stderr)

    if unmatched:
        section = BeautifulSoup(
            '<section class="owid-fc-unmatched-section" id="owid-fc-unmatched">'
            "<h2>Statements not located in the text</h2></section>",
            "html.parser",
        )
        for _, card in unmatched:
            section.section.append(card)
        body.append(section)

    body.insert(0, build_summary(soup, annotations, matched_ids, spec.get("source_url", "")))
    (soup.head or body).append(BeautifulSoup(STYLE, "html.parser"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"wrote {output_path}: {len(matched_ids)}/{len(annotations)} quotes matched", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    p_extract = sub.add_parser("extract", help="print the article's readable text")
    p_extract.add_argument("article")
    p_annotate = sub.add_parser("annotate", help="inject annotations into the article")
    p_annotate.add_argument("article")
    p_annotate.add_argument("annotations")
    p_annotate.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    if args.mode == "extract":
        extract(args.article)
    else:
        annotate(args.article, args.annotations, args.output)


if __name__ == "__main__":
    main()
