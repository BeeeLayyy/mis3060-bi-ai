# Wildcat Capital - clean tables

Produced by `scripts/02_clean.py` from the raw extract. Raw files are never modified.
Same file names and columns as raw; flag columns added are listed below.

| File | Raw rows | Clean rows | Quarantined |
|---|---:|---:|---:|
| `dim_advisor.csv` | 25 | 25 | 0 |
| `dim_benchmark.csv` | 8 | 8 | 0 |
| `dim_client.csv` | 2,525 | 2,500 | 25 |
| `dim_date.csv` | 1,827 | 1,827 | 0 |
| `dim_security.csv` | 500 | 500 | 0 |
| `fact_fees.csv` | 122,197 | 122,197 | 0 |
| `fact_portfolio_snapshot.csv` | 129,547 | 129,547 | 0 |
| `fact_transactions.csv` | 298,772 | 298,572 | 200 |

## Relationships (star schema)

| Fact / child | Key | Dimension |
|---|---|---|
| dim_client | advisor_id | dim_advisor.advisor_id |
| dim_security | benchmark_id | dim_benchmark.benchmark_id |
| fact_fees | client_id, advisor_id, fee_date | dim_client, dim_advisor, dim_date.date |
| fact_portfolio_snapshot | client_id, advisor_id, benchmark_id, snapshot_date | dim_client, dim_advisor, dim_benchmark, dim_date.date |
| fact_transactions | client_id, advisor_id, security_id, txn_date | dim_client, dim_advisor, dim_security, dim_date.date |

All relationships are many-to-one, single direction (dimension filters fact).
`fact_transactions.security_id` is blank for Deposit, Withdrawal and Advisory Fee rows by design.

## Column types for a BI tool

- **Text (not numbers):** `zip_code` (keeps leading zeros), `primary_account_type` / `account_type` (`529` is a plan name), `certifications` (`None` = no certification, do not convert to null), `ticker`, all name columns.
- **Whole numbers:** all `*_id` keys, `age`, `years_experience`, `aum_target_mm`, `year`, `quarter`, `month`, `week_of_year`, all 0/1 flags.
- **Decimal / currency:** `initial_aum`, `aum`, `aum_basis`, `amount`, `price`, `shares`, `bps_charged`, `expense_ratio_bps`.
- **Decimal ratios (0.05 = 5%):** `return_ytd`, `benchmark_return_ytd`, `active_alpha_ytd`, `cash_pct`. Format as percent in the BI tool.
- **Date (YYYY-MM-DD):** `date`, `client_since`, `fee_date`, `snapshot_date`, `txn_date`.
- **Boolean text:** `is_active`, `is_etf` (`True`/`False`).

## Flag columns added

| Table | Column | Meaning |
|---|---|---|
| dim_client | `risk_profile_imputed` | 1 = risk_profile was blank and was filled from the client's snapshot benchmark |
| dim_client | `flag_tier_aum_mismatch` | 1 = HNW with initial AUM under $1M or UHNW under $10M |
| fact_portfolio_snapshot | `flag_extreme_return` | 1 = abs(return_ytd) above 100% or AUM at the 1,000 floor |

## Known limitations (not fixed, on purpose)

- **Extreme YTD returns** are flagged, not changed: they look like AUM change including deposits/withdrawals, and the true time-weighted return cannot be rebuilt from this extract.
- **Client tier vs initial AUM** disagreements are flagged, not changed: tier may be set on household or current AUM, which we do not have.
- **is_trading_day** in dim_date marks weekdays only; market holidays are counted as trading days.
- **Duplicate security names** (3 names, each with distinct tickers) are left as is; ticker is the business key.
- Blank `sector` (ETFs) and blank `expense_ratio_bps` (single stocks) are legitimate and left blank.
