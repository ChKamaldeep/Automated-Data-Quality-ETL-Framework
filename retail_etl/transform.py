"""Pure transformations shared by the CLI, notebooks, and tests.

The analytical population is positive sales with an identified customer.
Returns and anonymous sales are exclusions, not necessarily source errors.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
import re
import pandas as pd

from .schema import SOURCE_MAPPING, SOURCE_COLUMNS, OUTPUT_COLUMNS

PENNY = Decimal("0.01")
MAX_PRICE = Decimal("999999999999.999999")
MAX_AMOUNT = Decimal("9999999999999999.99")


@dataclass
class PreparedData:
    cleaned: pd.DataFrame
    rejected: pd.DataFrame
    validation: dict


def _identifier(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if not math.isfinite(value):
            return ""
        if float(value).is_integer():
            return str(int(value))
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".")[0]
    return text


def _price(value):
    try:
        price = Decimal(str(value))
        if not price.is_finite() or price <= 0 or price > MAX_PRICE:
            return None
        # Avoid silent rounding when inserting into DECIMAL(18,6).
        if price != price.quantize(Decimal("0.000001")):
            return None
        return price
    except (InvalidOperation, ValueError):
        return None


def standardize_columns(raw):
    """Accept source labels or canonical labels, rejecting ambiguous schemas."""
    if raw.columns.duplicated().any():
        raise ValueError("Duplicate source column names")
    mapping = {str(k).strip().lower(): v for k, v in SOURCE_MAPPING.items()}
    mapping.update({v: v for v in SOURCE_COLUMNS})
    columns = [mapping.get(str(c).strip().lower(), str(c).strip().lower())
               for c in raw.columns]
    if len(set(columns)) != len(columns):
        raise ValueError("Column normalization produced duplicate names")
    if set(columns) != set(SOURCE_COLUMNS):
        raise ValueError(f"Unexpected schema: missing={sorted(set(SOURCE_COLUMNS)-set(columns))}; "
                         f"extra={sorted(set(columns)-set(SOURCE_COLUMNS))}")
    result = raw.copy()
    result.columns = columns
    result = result.loc[:, list(SOURCE_COLUMNS)].reset_index(drop=True)
    # Excel row numbers include the header row. Never use invoice/product as a
    # primary key: the same product can legitimately appear twice in an invoice.
    result["source_row_number"] = range(2, len(result) + 2)
    return result


def prepare_data(raw, *, as_of):
    """Validate, normalize, and quarantine exclusions without losing source rows.

    as_of is an explicit inclusive source-calendar date for reproducible checks.
    Rejection counts can overlap; rejected_rows counts each source row once.
    """
    df = standardize_columns(raw)
    original = df.copy()
    issues = {}

    def flag(name, mask):
        issues[name] = pd.Series(mask, index=df.index).fillna(True).astype(bool)

    # Preserve the established exact-source-duplicate policy before normalization.
    flag("duplicate_source_row", df.duplicated(subset=list(SOURCE_COLUMNS)))
    for name, limit in [("invoice_no", 50), ("stock_code", 50),
                        ("customer_id", 50), ("country", 100)]:
        df[name] = df[name].map(_identifier)
        flag(f"missing_{name}", df[name].eq(""))
        flag(f"oversized_{name}", df[name].str.len().gt(limit))
    flag("cancelled_invoice", df.invoice_no.str.upper().str.startswith("C"))
    flag("invalid_customer_id", ~df.customer_id.str.fullmatch(r"\d+"))
    quantity = pd.to_numeric(df.quantity, errors="coerce")
    flag("invalid_quantity", quantity.isna() | ~quantity.between(1, 2147483647)
         | quantity.mod(1).ne(0))
    df["quantity"] = quantity
    df["unit_price"] = pd.Series([_price(v) for v in df.unit_price], index=df.index, dtype=object)
    flag("invalid_unit_price", df.unit_price.isna())
    # UCI dates have no timezone; preserve their source-local calendar meaning.
    dates = pd.to_datetime(df.invoice_date, errors="coerce", format="mixed")
    if not pd.api.types.is_datetime64_dtype(dates.dtype):
        raise ValueError("Invoice dates must be timezone-naive source timestamps")
    df["invoice_date"] = dates
    cutoff = pd.Timestamp(as_of).normalize()
    if pd.isna(cutoff) or cutoff.tzinfo is not None:
        raise ValueError("as_of must be a valid timezone-naive date")
    flag("invalid_invoice_date", dates.isna() | dates.dt.year.lt(1000)
         | dates.ne(dates.dt.floor("s")))
    flag("future_invoice_date", dates.ge(cutoff + pd.Timedelta(days=1)))
    df["description"] = df.description.fillna("Unknown").astype(str).str.strip().str.upper()
    df.loc[df.description.eq(""), "description"] = "UNKNOWN"
    flag("oversized_description", df.description.map(lambda s: len(s.encode("utf-8")) > 65535))
    amounts = [None if p is None or pd.isna(q) or not math.isfinite(q)
               or q <= 0 or q > 2147483647 or q % 1 else Decimal(int(q)) * p
               for q, p in zip(quantity, df.unit_price)]
    flag("amount_out_of_range", [a is not None and a > MAX_AMOUNT for a in amounts])
    flags = pd.DataFrame(issues)
    excluded = flags.any(axis=1)
    rejected = original.loc[excluded].copy()
    rejected["rejection_reasons"] = [
        "|".join(name for name, active in zip(flags.columns, values) if active)
        for values in flags.loc[excluded].itertuples(index=False, name=None)
    ]
    clean = df.loc[~excluded].copy()
    clean["quantity"] = clean.quantity.astype("int64")
    validation = {
        "raw_rows": len(df), "source_columns": len(SOURCE_COLUMNS),
        "accepted_rows": len(clean), "rejected_rows": int(excluded.sum()),
        "rule_counts": {name: int(mask.sum()) for name, mask in issues.items()},
        "as_of": cutoff.date().isoformat(),
        "population": "positive sales with identified customers; cancellations excluded",
    }
    if len(clean) + len(rejected) != len(raw):
        raise ValueError("Source row reconciliation failed")
    return PreparedData(clean.reset_index(drop=True), rejected.reset_index(drop=True), validation)


def feature_engineering(clean):
    """Create the canonical features without writing any files."""
    df = clean.copy()
    df["total_amount"] = [(Decimal(int(q)) * p).quantize(PENNY, rounding=ROUND_HALF_UP)
                          for q, p in zip(df.quantity, df.unit_price)]
    date = df.invoice_date.dt
    for name, values in {
        "invoice_year": date.year, "invoice_month": date.month,
        "invoice_month_name": date.month_name(), "invoice_day": date.day,
        "invoice_day_name": date.day_name(), "invoice_hour": date.hour,
        "invoice_quarter": date.quarter,
        "year_month": date.strftime("%Y-%m"),
    }.items():
        df[name] = values
    df["quantity_category"] = pd.cut(df.quantity, [0, 5, 20, 100, float("inf")],
                                        labels=["Low", "Medium", "High", "Bulk"]).astype("string")
    df["revenue_category"] = pd.cut(df.total_amount.map(float),
        [0, 20, 100, 500, float("inf")], include_lowest=True,
        labels=["Low Value", "Medium Value", "High Value", "Premium Value"]).astype("string")
    return df.loc[:, list(OUTPUT_COLUMNS)]


def validate_output(df):
    """Enforce the export contract before publishing a file or loading MySQL."""
    if tuple(df.columns) != OUTPUT_COLUMNS:
        raise ValueError("Output columns/order do not match the canonical schema")
    if df.empty:
        raise ValueError("No accepted rows; refusing to publish an empty dataset")
    if df.isna().any().any():
        raise ValueError("Output contains missing values")
    if (df.source_row_number.lt(2).any() or df.source_row_number.mod(1).ne(0).any()
            or df.source_row_number.duplicated().any()):
        raise ValueError("Duplicate source row identifiers")
    for name in ("invoice_no", "stock_code", "customer_id", "country"):
        if df[name].astype(str).str.strip().eq("").any():
            raise ValueError(f"Output contains blank {name}")
    if df.invoice_no.str.upper().str.startswith("C").any():
        raise ValueError("Cancellation reached the sales output")
    if (df.quantity <= 0).any() or df.quantity.mod(1).ne(0).any():
        raise ValueError("Output contains invalid quantities")
    if any(_price(p) is None for p in df.unit_price):
        raise ValueError("Output contains invalid unit prices")
    expected = feature_engineering(df.loc[:, list(SOURCE_COLUMNS) + ["source_row_number"]])
    if not df.equals(expected):
        # equals includes dtype checks: compare values so a CSV round trip is allowed.
        if not df.astype(str).equals(expected.astype(str)):
            raise ValueError("Output contains inconsistent derived values")
    return {"rows": len(df), "columns": len(df.columns),
            "total_amount": str(sum(df.total_amount, Decimal(0))),
            "zero_rounded_amount_rows": int(df.total_amount.eq(0).sum())}
