# Data contract and metric definitions

The authoritative ordered contract is `retail_etl/schema.py`, schema version **2**. Python exports, generated DDL, and parameterized inserts use it directly. A test checks that the SQL schema file matches the generated definition.

## Source and grain

Input contains exactly eight columns, using UCI names or their canonical equivalents:

| UCI source | Canonical name |
|---|---|
| InvoiceNo | invoice_no |
| StockCode | stock_code |
| Description | description |
| Quantity | quantity |
| InvoiceDate | invoice_date |
| UnitPrice | unit_price |
| CustomerID | customer_id |
| Country | country |

Column labels may have outer whitespace. Missing, extra, or ambiguous duplicate columns fail the run before row processing. Input may be Excel or CSV; use ISO timestamps for CSV to avoid ambiguous date interpretation. Extra columns must be explicitly incorporated into the contract rather than silently ignored.

Each record is an invoice line. Multiple lines for the same invoice and product can be legitimate. `source_row_number` refers to the source worksheet/CSV row, including the header; it is the primary key of a full snapshot. The input SHA-256 and run ID identify the source artifact that gives those row numbers meaning.

## Validation and exclusion policy

The accepted population is positive sales with known customer identifiers and non-cancelled invoices. Returns and anonymous sales remain in `rejected_rows.csv`; exclusion from this sales dataset does not imply that they are erroneous source events.

- Remove exact duplicate source rows before normalization, keeping the first occurrence. This is a documented dataset assumption, not proof that every repeated transaction is fraudulent or invalid.
- Require nonblank invoice, product, customer, and country fields. Identifiers remain strings; numeric `.0` representations are normalized without stripping leading zeros from string IDs. Customer IDs must contain digits.
- Exclude invoice IDs beginning with `C`, case-insensitively.
- Require finite, positive, integral quantities within MySQL INT range.
- Require finite, positive unit prices representable as DECIMAL(18,6), rejecting extra precision rather than silently rounding it.
- Parse invoice timestamps, reject missing/malformed dates, subsecond precision, timezone-aware timestamps, and dates beyond the explicit inclusive cutoff.
- Trim descriptions and uppercase them; missing/blank descriptions become `UNKNOWN`. Country labels are trimmed without inventing geographic mappings.
- Reject text or amounts that exceed the database column capacity.

The source is preserved unchanged. Excluded records retain their original values, a source row number, and all applicable reasons. Rule counts may overlap. Always reconcile `raw_rows = accepted_rows + rejected_rows` using distinct row counts. No accepted rows means publication fails, while the quarantine and validation report are still saved.

## Output fields

The first eight fields use canonical source names. Then come, in order:

| Field | Definition |
|---|---|
| total_amount | quantity × unit_price, decimal ROUND_HALF_UP to two places |
| invoice_year | Source calendar year |
| invoice_month | Month number, 1–12 |
| invoice_month_name | English month name |
| invoice_day | Day of month |
| invoice_day_name | English weekday name |
| invoice_hour | Hour, 0–23 |
| invoice_quarter | Quarter, 1–4 |
| year_month | YYYY-MM reporting key |
| quantity_category | (0,5] Low; (5,20] Medium; (20,100] High; above 100 Bulk |
| revenue_category | [0,20] Low Value; (20,100] Medium Value; (100,500] High Value; above 500 Premium Value |
| source_row_number | Original source row, including header |

The total is **20 columns**: 8 source, 11 analytical, and 1 lineage field. Categories are descriptive project thresholds, not externally validated customer or product classifications.

## Currency and reporting

UCI unit prices are in sterling (GBP). Preserve up to six decimal places for prices and round each line amount half up to two places. Sum those rounded line amounts for all reported revenue. Four lines in the bundled accepted dataset have price £0.001, quantity 1, and rounded amount £0.00. They remain accepted and count toward quantities and orders. This policy differs from rounding the final sum of unrounded source values and must be kept consistent across Python and MySQL.

An invoice total is the sum of its line amounts. Average order value is total rounded sales amount divided by the number of distinct invoices in the same filtered population. Never average invoice totals repeated on line-item rows. Average line value is a different metric and is labeled separately in SQL.

Customer-frequency segments describe the observed period. They do not indicate whether a customer was new at the time of an individual purchase. Product queries that group by stock code and description report a **product-description variant**, since one stock code may have multiple descriptions. Consolidate by stock code and select a separately governed display description if a product-master view is required.

The dataset ends on 9 December 2011. December 2011 is a partial month, so monthly changes should not be presented as like-for-like performance without a matching observation window. Zero or missing calendar months require a calendar scaffold for generalized month-over-month analysis.
