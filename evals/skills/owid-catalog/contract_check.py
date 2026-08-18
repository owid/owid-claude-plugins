#!/usr/bin/env -S uv run --no-project --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["owid-catalog"]
# ///
"""Exercise the owid-catalog API surface that SKILL.md documents.

Emits one tab-separated line per check for contract.sh to parse:
    PASS<TAB>name
    FAIL<TAB>name<TAB>detail
    NOTE<TAB>text

Set SKIP_SLOW=1 to skip the semantic indicator search, which hits an external
embedding service and is the slowest check here.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from collections.abc import Callable
from typing import Any


def emit(status: str, name: str, detail: str = "") -> None:
    print(f"{status}\t{name}\t{detail}".rstrip("\t"), flush=True)


def retry(fn: Callable[[], Any], attempts: int = 3, delay: float = 2.0) -> Any:
    """Retry fn on any exception. search.owid.io returns a transient 502 often
    enough that a single attempt makes the nightly run flaky rather than
    informative."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(delay)


def check(name: str, fn: Callable[[], Any]) -> Any:
    """Run fn; PASS if it returns truthy or None, FAIL on falsy or exception."""
    try:
        result = fn()
    except Exception as exc:
        line = traceback.format_exc().strip().splitlines()[-1]
        emit("FAIL", name, f"{type(exc).__name__}: {exc or line}")
        return None
    if result is False:
        emit("FAIL", name, "check returned False")
        return None
    emit("PASS", name)
    return result


def main() -> int:
    if not check("owid.catalog imports fetch and search", _import):
        return 1
    from owid.catalog import fetch, search

    # --- Charts API -------------------------------------------------------
    tb = check("fetch('life-expectancy') returns a non-empty table", lambda: _nonempty(fetch("life-expectancy")))
    if tb is not None:
        check("the table exposes .codebook for metadata", lambda: bool(str(tb.codebook)))
        check("the table renders as CSV via .head().to_csv()", lambda: bool(tb.head(5).to_csv()))
        check(
            "columns carry metadata (unit or description)",
            lambda: any(
                getattr(tb[c].metadata, "unit", None) or getattr(tb[c].metadata, "description_short", None)
                for c in tb.columns
            ),
        )
    check(
        "fetch() accepts a full grapher URL",
        lambda: _nonempty(fetch("https://ourworldindata.org/grapher/life-expectancy")),
    )

    # --- Search: charts ---------------------------------------------------
    charts = check("search('population') returns results", lambda: _nonempty(search("population")))
    if charts is not None:
        check("chart results convert to a DataFrame", lambda: not charts.to_frame().empty)
        check("chart results convert to dicts", lambda: isinstance(charts.to_dict(), list))
        check("a chart search result can .fetch() its data", lambda: _nonempty(charts[0].fetch()))

    # --- Search: tables ---------------------------------------------------
    tables = check(
        "search(kind='table', latest=True) returns results",
        lambda: _nonempty(search("population", kind="table", latest=True)),
    )
    if tables is not None:
        check("table results expose to_frame(all_fields=True)", lambda: not tables.to_frame(all_fields=True).empty)
        check("table results support .filter()", lambda: tables.filter(lambda r: True) is not None)
        check("table results support .sort_by()", lambda: tables.sort_by("popularity", reverse=True) is not None)
        path = getattr(tables[0], "path", None) or getattr(tables[0], "table", None)
        emit("NOTE", f"first table path: {path}")
        # Fetch by catalog path rather than a hardcoded version, which rots.
        if path:
            check(f"fetch() accepts a catalog path ({path})", lambda: _nonempty(fetch(str(path))))
        check("exact match mode is accepted", lambda: search("population", kind="table", match="exact") is not None)
        check("regex match mode is accepted", lambda: search("gdp.*capita", kind="table", match="regex") is not None)

    # --- Search: indicators ----------------------------------------------
    # Name the gate and its dependents once, so all three paths — ran, gate
    # failed, deliberately skipped — report the same set of checks. A check that
    # did not run must never simply vanish from the totals: SKIP_SLOW=1 used to
    # emit a bare note, which made a reduced run look like a complete pass.
    gate = "search(kind='indicator') semantic search returns results"
    skip_slow = bool(os.environ.get("SKIP_SLOW"))
    indicators = None

    if skip_slow:
        emit("SKIP", gate, "SKIP_SLOW=1")
    else:
        indicators = check(
            gate,
            lambda: _nonempty(retry(lambda: search("share of energy from renewable sources", kind="indicator"))),
        )

    dependents: list[tuple[str, Callable[[], Any]]] = [
        ("indicator results convert to a DataFrame", lambda: not indicators.to_frame().empty),
        ("an indicator result can .fetch() a single column", lambda: _nonempty(indicators[0].fetch())),
        ("an indicator result can .fetch_table()", lambda: _nonempty(indicators[0].fetch_table())),
        (
            "sort_by='relevance' is accepted",
            lambda: search("CO2 emissions per capita", kind="indicator", sort_by="relevance") is not None,
        ),
    ]
    reason = "SKIP_SLOW=1" if skip_slow else "indicator search did not return results"
    for name, fn in dependents:
        if indicators is None:
            emit("SKIP", name, reason)
        else:
            check(name, fn)

    return 0


def _import() -> bool:
    from owid.catalog import fetch, search  # noqa: F401

    return True


def _nonempty(obj: Any) -> Any:
    """Assert the table or result set has rows, and return it so callers can
    keep using the object rather than a bool."""
    if len(obj) == 0:
        raise AssertionError("empty result")
    return obj


if __name__ == "__main__":
    sys.exit(main())
