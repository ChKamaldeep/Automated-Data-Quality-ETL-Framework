import pandas as pd
import pytest


@pytest.fixture
def source():
    return pd.DataFrame([
        ["536365", "85123A", "White heart", 6, "2011-12-01 08:26:00", "2.55", "17850", "United Kingdom"],
        ["536366", "71053", "Metal lantern", 2, "2011-12-02 09:00:00", "3.39", "17850", "United Kingdom"],
    ], columns=["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate",
                "UnitPrice", "CustomerID", "Country"])
