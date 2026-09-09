from decimal import Decimal
import pandas as pd
import pytest

from retail_etl.schema import OUTPUT_COLUMNS
from retail_etl.transform import prepare_data, feature_engineering, validate_output


def run(source):
    prepared = prepare_data(source, as_of="2011-12-09")
    return prepared, feature_engineering(prepared.cleaned)


def test_sales_values_and_lineage(source):
    prepared, final = run(source)
    assert tuple(final.columns) == OUTPUT_COLUMNS
    assert final.source_row_number.tolist() == [2, 3]
    assert final.total_amount.tolist() == [Decimal("15.30"), Decimal("6.78")]
    assert final.invoice_month_name.tolist() == ["December", "December"]
    assert final.quantity_category.tolist() == ["Medium", "Low"]
    assert validate_output(final)["total_amount"] == "22.08"
    assert prepared.validation["source_columns"] == 8


def test_exclusion_reasons_and_row_reconciliation(source):
    cases = [
        {"InvoiceNo": None}, {"StockCode": "  "}, {"CustomerID": None},
        {"CustomerID": "17850.5"}, {"InvoiceDate": "bad"},
        {"InvoiceDate": "2011-12-10"}, {"Quantity": -1, "InvoiceNo": "c123"},
        {"UnitPrice": "Infinity"}, {"UnitPrice": "-1"}, {"Quantity": 1.5},
        {"Country": " "}, {"UnitPrice": "0.0000001"},
    ]
    base = source.iloc[0].to_dict()
    data = pd.DataFrame([base, base, *[base | case for case in cases]])
    prepared, _ = run(data)
    assert len(prepared.cleaned) == 1
    assert len(prepared.rejected) == len(data) - 1
    assert prepared.validation["accepted_rows"] + prepared.validation["rejected_rows"] == len(data)
    assert prepared.rejected.source_row_number.is_unique
    assert "duplicate_source_row" in prepared.rejected.iloc[0].rejection_reasons
    returns = prepared.rejected[prepared.rejected.invoice_no.eq("c123")].iloc[0]
    assert "cancelled_invoice" in returns.rejection_reasons
    assert "invalid_quantity" in returns.rejection_reasons


def test_precision_and_half_up_rounding(source):
    source["Quantity"] = [1, 3]
    source["UnitPrice"] = ["0.001", "0.005"]
    _, final = run(source)
    assert final.unit_price.tolist() == [Decimal("0.001"), Decimal("0.005")]
    assert final.total_amount.tolist() == [Decimal("0.00"), Decimal("0.02")]
    assert validate_output(final)["zero_rounded_amount_rows"] == 1


def test_missing_descriptions_are_filled_and_leading_zero_ids_preserved(source):
    source["Description"] = [None, "  "]
    source["CustomerID"] = ["00123", "17850.0"]
    _, final = run(source)
    assert final.description.tolist() == ["UNKNOWN", "UNKNOWN"]
    assert final.customer_id.tolist() == ["00123", "17850"]


def test_cutoff_includes_whole_day_and_rejects_timezones(source):
    source["InvoiceDate"] = ["2011-12-09 23:59:59", "2011-12-10 00:00:00"]
    prepared, _ = run(source)
    assert len(prepared.cleaned) == 1
    source["InvoiceDate"] = ["2011-12-01T00:00:00+00:00"] * 2
    with pytest.raises(ValueError, match="timezone"):
        run(source)


def test_bad_schema_fails_before_transform(source):
    with pytest.raises(ValueError, match="Unexpected schema"):
        run(source.drop(columns="StockCode"))
    source["invoice_no"] = source.InvoiceNo
    with pytest.raises(ValueError, match="duplicate"):
        run(source)


def test_empty_output_cannot_publish(source):
    source["UnitPrice"] = "bad"
    prepared, final = run(source)
    assert len(prepared.rejected) == len(source)
    with pytest.raises(ValueError, match="empty"):
        validate_output(final)


def test_column_order_and_corrupt_derived_values_fail(source):
    _, final = run(source)
    with pytest.raises(ValueError, match="columns/order"):
        validate_output(final[list(reversed(final.columns))])
    final.loc[0, "invoice_month"] = 1
    with pytest.raises(ValueError, match="inconsistent"):
        validate_output(final)


def test_repeated_product_lines_with_different_quantities_are_preserved(source):
    source.loc[1, ["InvoiceNo", "StockCode", "InvoiceDate"]] = source.loc[0, ["InvoiceNo", "StockCode", "InvoiceDate"]]
    prepared, final = run(source)
    assert len(prepared.cleaned) == len(final) == 2
