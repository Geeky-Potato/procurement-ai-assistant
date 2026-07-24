"""Human-readable schema of the purchase_orders collection.

Injected into the agent's system prompt so the LLM can write correct MongoDB
queries without guessing field names or types.
"""

COLLECTION_SCHEMA = """\
Collection: purchase_orders
Each document is one line item of a State of California purchase order
(2012-2015). Fields (snake_case), with type and notes:

Dates (BSON datetime; may be null):
  - creation_date            When the record was created.
  - purchase_date            When the purchase was made (often null).

Identifiers / categories (string; may be null):
  - fiscal_year              e.g. "2012-2013", "2013-2014", "2014-2015".
  - lpa_number               Leveraged Procurement Agreement number.
  - purchase_order_number
  - requisition_number
  - acquisition_type         e.g. "IT Goods", "NON-IT Goods",
                             "IT Services", "NON-IT Services".
  - sub_acquisition_type
  - acquisition_method       e.g. "WSCA/Coop", "Statewide Contract",
                             "Informal Competitive", "Formal Competitive",
                             "SB/DVBE Option", "Fair and Reasonable".
  - sub_acquisition_method
  - department_name          Purchasing department, e.g.
                             "Consumer Affairs, Department of".
  - supplier_code
  - supplier_name
  - supplier_qualifications  e.g. "SB" (Small Business), "DVBE".
  - supplier_zip_code
  - location                 Free-text location string.

Booleans (may be null):
  - calcard                  true if purchased with a CalCard.

Numbers (float; may be null):
  - quantity
  - unit_price               In US dollars.
  - total_price              In US dollars (quantity * unit_price).

UNSPSC classification (string; may be null):
  - classification_codes
  - normalized_unspsc
  - commodity_title
  - unspsc_class, class_title
  - unspsc_family, family_title
  - unspsc_segment, segment_title

Notes:
  - Prefer `fiscal_year` for year-based analysis (dates are frequently null).
  - Monetary totals should sum `total_price`.
  - Many text fields are null; account for that in filters/aggregations.
  - String matches are case-sensitive; use case-insensitive regex when the
    user's wording may not match exactly (e.g. department or supplier names).
"""
