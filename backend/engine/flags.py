"""Feature flags for recommendation surfaces that aren't ready to ship.

Each flag below gates a piece of *presentation*, never detection. The analysis
that feeds these surfaces still runs and still returns its numbers — we just
stop rendering advice we can't stand behind yet. Flip a flag back to True once
the copy behind it is derived from the business's own data.

Why these three are off:

* `ENABLE_STAFFING_REC` — the staffing line only ever interpolated the peak and
  slowest day names into a fixed sentence. No headcount, no hours, no dollars,
  so it told an owner nothing the two stat tiles above it already showed.
* `ENABLE_CLUSTER_ADVICE` — four hardcoded strings keyed on cluster name. Every
  business that uploaded a file got the same four sentences.
* `ENABLE_GROWTH_ACTIONS` — generic marketing copy selected by trend direction.
  The dollar figures inside it are real, but the actions themselves aren't
  derived from the data, and there are four of them per page.
"""
from __future__ import annotations

ENABLE_STAFFING_REC = False
ENABLE_CLUSTER_ADVICE = False
ENABLE_GROWTH_ACTIONS = False
