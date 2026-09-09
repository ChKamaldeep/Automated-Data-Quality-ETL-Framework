# Verification record

Reviewed baseline: `f1c120c7d90acc1774598a62eb521189a8488397`.

## Full source execution

On 9 September 2026, the v2 CSV pipeline was run against the complete bundled workbook with `--as-of 2011-12-09`.

| Measure | Observed value |
|---|---:|
| Raw rows | 541,909 |
| Raw columns | 8 |
| Accepted rows | 392,692 |
| Excluded rows | 149,217 |
| Output columns | 20 |
| Sum of rounded line amounts (GBP) | 8,887,208.89 |
| Zero rounded amount lines with positive prices | 4 |

Input SHA-256: `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`.

Output SHA-256: `1b976c64c7aaba683f18dbbf891abeebd1799c75bef3211af800d2d38bced285`.

The accepted count agrees with the earlier automation. The v2 output adds source lineage, uses shared canonical fields, normalizes descriptions consistently, and makes currency rounding explicit. Identical row counts alone do not imply identical values or schema; hashes and validation cover those distinctions.

## Automated checks

The initial local run passed 15 tests with 3 MySQL integration tests skipped because no local MySQL server was installed. The passing checks include execution of every code cell in all five notebooks on sample data, schema/order checks, price precision, malformed records, source row reconciliation, repeated-input output hashes, and failure logging without changing the latest successful output pointer.

The repository includes GitHub Actions jobs for Python 3.11, 3.12, 3.13 and MySQL 8.0. A workflow definition alone is not evidence that those jobs passed. Refer to the branch/PR workflow results for the final execution status. Full-source MySQL loading is separate from the local full-source CSV check.

## Review fixes

1. One schema replaces the mismatched CSV/SQL field ordering.
2. All notebooks call shared cleaning/feature logic; exploratory notebooks do not overwrite exports.
3. Staging and atomic publication replace destructive setup and duplicate-appending loads.
4. Shared validation, rejection reasons, source lineage, and final publication checks replace count-only validation.
5. Exact decimal pricing and distinct definitions of invoice total/AOV resolve metric ambiguity.
6. The pipeline now owns logging, failure manifests, portable paths, and a nonzero CLI failure status.
7. Tests, CI definitions, dependency constraints, and accurate documentation replace unsupported completion claims and stale tracked outputs.

## Remaining scope

This is a bounded local batch project, not a deployed scheduled service. The whole workbook is processed in memory. Incremental ingestion, cloud operation, automatic backup expiry, and Power BI schema migration are not implemented. External database configuration is required before connecting to a user's MySQL server.
