# Model metadata for Claude (Part D)

> **Replace this file's tables with the three INFO.VIEW result grids from `hw06.pbix`** (guide §2) before you submit. The tables below were built from the HW5 TMDL (same eight tables and the same 11 active fact→dimension relationships) so the Part D prompt could be drafted; the posted `Wildcat_Star_Model.pbix` is the source of truth.

## Columns (INFO.VIEW.COLUMNS)

| Table | Column | DataType |
|---|---|---|
| dim_advisor | advisor_id | int64 |
| dim_advisor | first_name | string |
| dim_advisor | last_name | string |
| dim_advisor | region | string |
| dim_advisor | years_experience | int64 |
| dim_advisor | aum_target_mm | double |
| dim_advisor | certifications | string |
| dim_benchmark | benchmark_id | int64 |
| dim_benchmark | name | string |
| dim_benchmark | asset_class | string |
| dim_benchmark | ticker_proxy | string |
| dim_client | client_id | int64 |
| dim_client | first_name | string |
| dim_client | last_name | string |
| dim_client | age | int64 |
| dim_client | city | string |
| dim_client | state | string |
| dim_client | zip_code | string |
| dim_client | risk_profile | string |
| dim_client | client_tier | string |
| dim_client | primary_account_type | string |
| dim_client | initial_aum | double |
| dim_client | client_since | dateTime |
| dim_client | advisor_id | int64 |
| dim_client | is_active | boolean |
| dim_date | date_id | int64 |
| dim_date | date | dateTime |
| dim_date | year | int64 |
| dim_date | quarter | int64 |
| dim_date | month | int64 |
| dim_date | month_name | string |
| dim_date | week_of_year | int64 |
| dim_date | day_of_week | string |
| dim_date | is_month_end | int64 |
| dim_date | is_quarter_end | int64 |
| dim_date | is_year_end | int64 |
| dim_date | is_trading_day | int64 |
| dim_security | security_id | int64 |
| dim_security | ticker | string |
| dim_security | name | string |
| dim_security | asset_class | string |
| dim_security | sector | string |
| dim_security | benchmark_id | int64 |
| dim_security | is_etf | boolean |
| dim_security | expense_ratio_bps | double |
| fact_fees | fee_id | int64 |
| fact_fees | client_id | int64 |
| fact_fees | advisor_id | int64 |
| fact_fees | fee_date | dateTime |
| fact_fees | fee_type | string |
| fact_fees | aum_basis | double |
| fact_fees | bps_charged | double |
| fact_fees | amount | double |
| fact_portfolio_snapshot | snapshot_id | int64 |
| fact_portfolio_snapshot | client_id | int64 |
| fact_portfolio_snapshot | advisor_id | int64 |
| fact_portfolio_snapshot | benchmark_id | int64 |
| fact_portfolio_snapshot | snapshot_date | dateTime |
| fact_portfolio_snapshot | year | int64 |
| fact_portfolio_snapshot | month | int64 |
| fact_portfolio_snapshot | aum | double |
| fact_portfolio_snapshot | return_ytd | double |
| fact_portfolio_snapshot | benchmark_return_ytd | double |
| fact_portfolio_snapshot | active_alpha_ytd | double |
| fact_portfolio_snapshot | cash_pct | double |
| fact_portfolio_snapshot | account_type | string |
| fact_portfolio_snapshot | is_return_suspect | int64 |
| fact_transactions | txn_id | int64 |
| fact_transactions | client_id | int64 |
| fact_transactions | advisor_id | int64 |
| fact_transactions | security_id | int64 |
| fact_transactions | txn_date | dateTime |
| fact_transactions | txn_type | string |
| fact_transactions | shares | double |
| fact_transactions | price | double |
| fact_transactions | amount | double |
| fact_transactions | is_post_departure_txn | int64 |

## Relationships (INFO.VIEW.RELATIONSHIPS)

All many-to-one, single cross-filter direction, active.

| From (many) | To (one) |
|---|---|
| fact_fees.client_id | dim_client.client_id |
| fact_fees.advisor_id | dim_advisor.advisor_id |
| fact_fees.fee_date | dim_date.date |
| fact_portfolio_snapshot.client_id | dim_client.client_id |
| fact_portfolio_snapshot.advisor_id | dim_advisor.advisor_id |
| fact_portfolio_snapshot.benchmark_id | dim_benchmark.benchmark_id |
| fact_portfolio_snapshot.snapshot_date | dim_date.date |
| fact_transactions.client_id | dim_client.client_id |
| fact_transactions.advisor_id | dim_advisor.advisor_id |
| fact_transactions.security_id | dim_security.security_id |
| fact_transactions.txn_date | dim_date.date |

`dim_date` is marked as the date table on `dim_date[date]`.

## Measures (INFO.VIEW.MEASURES)

All in `_Measures`; DAX and format strings are in `../powerbi/measures.md`.
