"""Load the State of California large-purchases CSV into MongoDB.

Usage:
    python -m app.db.load_csv data/PURCHASE_ORDER_DATA.csv [--drop] [--limit N]

Cleans raw CSV values into typed documents:
  - currency strings ("$1,234.56", "($5.00)") -> float
  - dates ("MM/DD/YYYY", often blank)          -> datetime | None
  - "YES"/"NO"                                  -> bool | None
  - numeric quantities                          -> float | None
Column headers are mapped to snake_case field names.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Any

import pandas as pd
from pymongo import ASCENDING, TEXT

from app.core.config import get_settings
from app.db.mongo import get_collection

CHUNK_SIZE = 50_000

# Raw CSV header -> Mongo field name.
COLUMN_MAP: dict[str, str] = {
    "Creation Date": "creation_date",
    "Purchase Date": "purchase_date",
    "Fiscal Year": "fiscal_year",
    "LPA Number": "lpa_number",
    "Purchase Order Number": "purchase_order_number",
    "Requisition Number": "requisition_number",
    "Acquisition Type": "acquisition_type",
    "Sub-Acquisition Type": "sub_acquisition_type",
    "Acquisition Method": "acquisition_method",
    "Sub-Acquisition Method": "sub_acquisition_method",
    "Department Name": "department_name",
    "Supplier Code": "supplier_code",
    "Supplier Name": "supplier_name",
    "Supplier Qualifications": "supplier_qualifications",
    "Supplier Zip Code": "supplier_zip_code",
    "CalCard": "calcard",
    "Item Name": "item_name",
    "Item Description": "item_description",
    "Quantity": "quantity",
    "Unit Price": "unit_price",
    "Total Price": "total_price",
    "Classification Codes": "classification_codes",
    "Normalized UNSPSC": "normalized_unspsc",
    "Commodity Title": "commodity_title",
    "Class": "unspsc_class",
    "Class Title": "class_title",
    "Family": "unspsc_family",
    "Family Title": "family_title",
    "Segment": "unspsc_segment",
    "Segment Title": "segment_title",
    "Location": "location",
}

DATE_FIELDS = ("creation_date", "purchase_date")
CURRENCY_FIELDS = ("unit_price", "total_price")
NUMERIC_FIELDS = ("quantity",)
BOOL_FIELDS = ("calcard",)


def _parse_currency(value: Any) -> float | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "").strip()
    if not s:
        return None
    try:
        num = float(s)
    except ValueError:
        return None
    return -num if negative else num


def _parse_number(value: Any) -> float | None:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if not s or s.lower() == "nan":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ("yes", "y", "true", "1"):
        return True
    if s in ("no", "n", "false", "0"):
        return False
    return None


def _parse_date(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.to_pydatetime()
    return None


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    return s


def _clean_chunk(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = df.rename(columns=COLUMN_MAP)

    # Vectorized date parsing (blank -> NaT).
    for field in DATE_FIELDS:
        if field in df.columns:
            df[field] = pd.to_datetime(
                df[field], format="%m/%d/%Y", errors="coerce"
            )

    records: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        doc: dict[str, Any] = {}
        for field, value in row.items():
            if field in DATE_FIELDS:
                doc[field] = _parse_date(value)
            elif field in CURRENCY_FIELDS:
                doc[field] = _parse_currency(value)
            elif field in NUMERIC_FIELDS:
                doc[field] = _parse_number(value)
            elif field in BOOL_FIELDS:
                doc[field] = _parse_bool(value)
            else:
                doc[field] = _clean_str(value)
        records.append(doc)
    return records


def _create_indexes() -> None:
    col = get_collection()
    print("Creating indexes...")
    col.create_index([("fiscal_year", ASCENDING)])
    col.create_index([("department_name", ASCENDING)])
    col.create_index([("supplier_name", ASCENDING)])
    col.create_index([("acquisition_type", ASCENDING)])
    col.create_index([("acquisition_method", ASCENDING)])
    col.create_index([("purchase_date", ASCENDING)])
    col.create_index([("creation_date", ASCENDING)])
    col.create_index([("total_price", ASCENDING)])
    col.create_index(
        [("item_name", TEXT), ("item_description", TEXT), ("supplier_name", TEXT)],
        name="text_search",
    )
    print("Indexes created.")


def load(csv_path: str, drop: bool = False, limit: int | None = None) -> None:
    settings = get_settings()
    col = get_collection()

    if drop:
        print(f"Dropping existing collection '{settings.mongodb_collection}'...")
        col.drop()

    print(f"Loading {csv_path} into "
          f"{settings.mongodb_db}.{settings.mongodb_collection} ...")

    total = 0
    reader = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
        na_values=[""],
        chunksize=CHUNK_SIZE,
        nrows=limit,
    )
    for i, chunk in enumerate(reader):
        records = _clean_chunk(chunk)
        if records:
            col.insert_many(records, ordered=False)
        total += len(records)
        print(f"  chunk {i + 1}: inserted {len(records):,} (total {total:,})")

    print(f"Done. Inserted {total:,} documents.")
    _create_indexes()
    print("All done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load CA purchase-order CSV into MongoDB.")
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("--drop", action="store_true",
                        help="Drop the collection before loading")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only load the first N rows (for testing)")
    args = parser.parse_args()

    try:
        load(args.csv_path, drop=args.drop, limit=args.limit)
    except FileNotFoundError:
        print(f"Error: file not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
