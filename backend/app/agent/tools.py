"""Read-only MongoDB tools exposed to the LLM agent.

The LLM produces MongoDB queries as JSON strings; these tools parse them
(supporting Extended JSON, e.g. {"$date": "2014-01-01"}), enforce read-only
access and result caps, and return results as JSON text.
"""
from __future__ import annotations

import json
from typing import Any

from bson import json_util
from langchain_core.tools import tool

from app.db.mongo import get_collection

MAX_RESULTS = 50
MAX_DISTINCT = 200

# Aggregation stages that can write / are otherwise disallowed.
FORBIDDEN_STAGES = {"$out", "$merge", "$function", "$accumulator", "$where"}


def _dumps(data: Any) -> str:
    """Serialize BSON-containing results to readable JSON."""
    return json.dumps(json.loads(json_util.dumps(data)), default=str, indent=1)


def _parse(json_str: str, what: str) -> Any:
    try:
        return json_util.loads(json_str)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid JSON for {what}: {exc}") from exc


@tool
def aggregate(pipeline_json: str) -> str:
    """Run a MongoDB aggregation pipeline on the purchase_orders collection.

    `pipeline_json` must be a JSON array of pipeline stages. Extended JSON is
    supported for typed values, e.g. dates as {"$date": "2014-01-01T00:00:00Z"}.
    Read-only: $out/$merge/$function/$where are rejected. At most 50 result
    documents are returned. Prefer this for grouping, sums, counts, and top-N.
    """
    pipeline = _parse(pipeline_json, "pipeline")
    if not isinstance(pipeline, list):
        return "Error: pipeline must be a JSON array of stages."
    for stage in pipeline:
        if isinstance(stage, dict):
            bad = FORBIDDEN_STAGES.intersection(stage.keys())
            if bad:
                return f"Error: disallowed stage(s): {', '.join(sorted(bad))}."

    # Cap results unless the pipeline already limits them.
    has_limit = any(isinstance(s, dict) and "$limit" in s for s in pipeline)
    effective = pipeline if has_limit else pipeline + [{"$limit": MAX_RESULTS}]
    try:
        docs = list(get_collection().aggregate(effective))
    except Exception as exc:  # noqa: BLE001
        return f"Error running aggregation: {exc}"
    return _dumps(docs[:MAX_RESULTS])


@tool
def find(query_json: str) -> str:
    """Find documents in purchase_orders.

    `query_json` is a JSON object with optional keys:
      - "filter":     query document (default {})
      - "projection": fields to include/exclude
      - "sort":       array of [field, 1|-1] pairs
      - "limit":      max docs (capped at 50)
    Extended JSON is supported (e.g. {"$date": "..."}). Read-only.
    """
    spec = _parse(query_json, "query")
    if not isinstance(spec, dict):
        return "Error: query must be a JSON object."
    filt = spec.get("filter", {})
    projection = spec.get("projection")
    sort = spec.get("sort")
    limit = min(int(spec.get("limit", MAX_RESULTS)), MAX_RESULTS)
    try:
        cursor = get_collection().find(filt, projection)
        if sort:
            cursor = cursor.sort([(f, int(d)) for f, d in sort])
        docs = list(cursor.limit(limit))
    except Exception as exc:  # noqa: BLE001
        return f"Error running find: {exc}"
    return _dumps(docs)


@tool
def count(filter_json: str = "{}") -> str:
    """Count documents in purchase_orders matching a JSON filter (default all)."""
    filt = _parse(filter_json, "filter")
    if not isinstance(filt, dict):
        return "Error: filter must be a JSON object."
    try:
        n = get_collection().count_documents(filt)
    except Exception as exc:  # noqa: BLE001
        return f"Error running count: {exc}"
    return json.dumps({"count": n})


@tool
def distinct(field: str, filter_json: str = "{}") -> str:
    """List distinct values of a field (helps discover category names).

    Returns up to 200 values. `filter_json` optionally narrows the scope.
    """
    filt = _parse(filter_json, "filter")
    if not isinstance(filt, dict):
        return "Error: filter must be a JSON object."
    try:
        values = get_collection().distinct(field, filt)
    except Exception as exc:  # noqa: BLE001
        return f"Error running distinct: {exc}"
    values = [v for v in values if v is not None][:MAX_DISTINCT]
    return _dumps(values)


TOOLS = [aggregate, find, count, distinct]
