# Model metadata for Claude (Part D)

Exported from `hw06.pbix` in DAX query view with the three INFO.VIEW queries from guide §2 (run 2026-11-04).

Things worth knowing from this export:
- 11 fact → dimension relationships, all many-to-one, single direction, plus `dim_security[benchmark_id]` → `dim_benchmark` active in this posted model
- The two `LocalDateTable_*` rows are Power BI's auto date/time tables (hidden), not part of the star
- `dim_date` columns are `Date`, `Year`, `Month`; DAX names are case-insensitive, so `dim_date[date]` resolves
- `fact_portfolio_snapshot` also has its own `Year` and `Month` columns; visuals use `dim_date[Year]` instead so time intelligence works

## INFO.VIEW.COLUMNS

| Table | Column | DataType | DAX formula | IsHidden |
|---|---|---|---|---|
| _Measures | Value | Text |  | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | Date | Date |  | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | Day | Integer | DAY([Date]) | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | Quarter | Text | Qtr  & [QuarterNo] | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | QuarterNo | Integer | INT(([MonthNo] + 2) / 3) | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | Month | Text | FORMAT([Date], "MMMM") | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | MonthNo | Integer | MONTH([Date]) | true |
| DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa | Year | Integer | YEAR([Date]) | true |
| dim_advisor | advisor_id | Integer |  | false |
| dim_advisor | certifications | Text |  | false |
| dim_advisor | aum_target_mm | Integer |  | false |
| dim_advisor | years_experience | Integer |  | false |
| dim_advisor | region | Text |  | false |
| dim_advisor | last_name | Text |  | false |
| dim_advisor | first_name | Text |  | false |
| dim_benchmark | name | Text |  | false |
| dim_benchmark | benchmark_id | Integer |  | false |
| dim_benchmark | ticker_proxy | Text |  | false |
| dim_benchmark | asset_class | Text |  | false |
| dim_client | age | Integer |  | false |
| dim_client | last_name | Text |  | false |
| dim_client | first_name | Text |  | false |
| dim_client | client_id | Integer |  | false |
| dim_client | zip_code | Text |  | false |
| dim_client | risk_profile | Text |  | false |
| dim_client | client_tier | Text |  | false |
| dim_client | primary_account_type | Text |  | false |
| dim_client | initial_aum | Number |  | false |
| dim_client | client_since | Date |  | false |
| dim_client | advisor_id | Integer |  | false |
| dim_client | is_active | True/False |  | false |
| dim_client | state | Text |  | false |
| dim_client | city | Text |  | false |
| dim_date | Quarter | Integer |  | false |
| dim_date | date_id | Integer |  | false |
| dim_date | Date | Date |  | false |
| dim_date | Year | Integer |  | false |
| dim_date | Month | Integer |  | false |
| dim_date | month_name | Text |  | false |
| dim_date | week_of_year | Integer |  | false |
| dim_date | day_of_week | Text |  | false |
| dim_date | is_month_end | Integer |  | false |
| dim_date | is_quarter_end | Integer |  | false |
| dim_date | is_year_end | Integer |  | false |
| dim_date | is_trading_day | Integer |  | false |
| dim_security | name | Text |  | false |
| dim_security | ticker | Text |  | false |
| dim_security | security_id | Integer |  | false |
| dim_security | expense_ratio_bps | Integer |  | false |
| dim_security | is_etf | True/False |  | false |
| dim_security | benchmark_id | Integer |  | false |
| dim_security | sector | Text |  | false |
| dim_security | asset_class | Text |  | false |
| fact_fees | aum_basis | Number |  | false |
| fact_fees | fee_type | Text |  | false |
| fact_fees | fee_date | Date |  | false |
| fact_fees | fee_id | Integer |  | false |
| fact_fees | client_id | Integer |  | false |
| fact_fees | advisor_id | Integer |  | false |
| fact_fees | amount | Number |  | false |
| fact_fees | bps_charged | Number |  | false |
| fact_portfolio_snapshot | cash_pct | Number |  | false |
| fact_portfolio_snapshot | benchmark_return_ytd | Number |  | false |
| fact_portfolio_snapshot | return_ytd | Number |  | false |
| fact_portfolio_snapshot | aum | Number |  | false |
| fact_portfolio_snapshot | Month | Integer |  | false |
| fact_portfolio_snapshot | Year | Integer |  | false |
| fact_portfolio_snapshot | snapshot_date | Date |  | false |
| fact_portfolio_snapshot | benchmark_id | Integer |  | false |
| fact_portfolio_snapshot | advisor_id | Integer |  | false |
| fact_portfolio_snapshot | client_id | Integer |  | false |
| fact_portfolio_snapshot | snapshot_id | Integer |  | false |
| fact_portfolio_snapshot | is_return_suspect | Integer |  | false |
| fact_portfolio_snapshot | account_type | Text |  | false |
| fact_portfolio_snapshot | active_alpha_ytd | Number |  | false |
| fact_transactions | shares | Number |  | false |
| fact_transactions | price | Number |  | false |
| fact_transactions | txn_date | Date |  | false |
| fact_transactions | advisor_id | Integer |  | false |
| fact_transactions | security_id | Integer |  | false |
| fact_transactions | amount | Number |  | false |
| fact_transactions | txn_type | Text |  | false |
| fact_transactions | client_id | Integer |  | false |
| fact_transactions | txn_id | Integer |  | false |
| fact_transactions | is_post_departure_txn | Integer |  | false |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | QuarterNo | Integer | INT(([MonthNo] + 2) / 3) | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | Date | Date |  | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | Year | Integer | YEAR([Date]) | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | MonthNo | Integer | MONTH([Date]) | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | Month | Text | FORMAT([Date], "MMMM") | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | Day | Integer | DAY([Date]) | true |
| LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7 | Quarter | Text | Qtr  & [QuarterNo] | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | Year | Integer | YEAR([Date]) | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | MonthNo | Integer | MONTH([Date]) | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | Month | Text | FORMAT([Date], "MMMM") | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | QuarterNo | Integer | INT(([MonthNo] + 2) / 3) | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | Quarter | Text | Qtr  & [QuarterNo] | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | Day | Integer | DAY([Date]) | true |
| LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8 | Date | Date |  | true |

## INFO.VIEW.RELATIONSHIPS

| Relationship | IsActive | CrossFilteringBehavior | FromCardinality | ToCardinality | State |
|---|---|---|---|---|---|
| 'fact_transactions'[advisor_id] *[<-]1 'dim_advisor'[advisor_id] | true | OneDirection | Many | One | Ready |
| 'fact_transactions'[client_id] *[<-]1 'dim_client'[client_id] | true | OneDirection | Many | One | Ready |
| 'fact_transactions'[security_id] *[<-]1 'dim_security'[security_id] | true | OneDirection | Many | One | Ready |
| 'fact_transactions'[txn_date] *[<-]1 'dim_date'[date] | true | OneDirection | Many | One | Ready |
| 'fact_portfolio_snapshot'[advisor_id] *[<-]1 'dim_advisor'[advisor_id] | true | OneDirection | Many | One | Ready |
| 'fact_portfolio_snapshot'[benchmark_id] *[<-]1 'dim_benchmark'[benchmark_id] | true | OneDirection | Many | One | Ready |
| 'fact_portfolio_snapshot'[client_id] *[<-]1 'dim_client'[client_id] | true | OneDirection | Many | One | Ready |
| 'fact_portfolio_snapshot'[snapshot_date] *[<-]1 'dim_date'[date] | true | OneDirection | Many | One | Ready |
| 'fact_fees'[advisor_id] *[<-]1 'dim_advisor'[advisor_id] | true | OneDirection | Many | One | Ready |
| 'fact_fees'[client_id] *[<-]1 'dim_client'[client_id] | true | OneDirection | Many | One | Ready |
| 'fact_fees'[fee_date] *[<-]1 'dim_date'[date] | true | OneDirection | Many | One | Ready |
| 'dim_client'[client_since] *[<-]1 'LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8'[Date] | true | OneDirection | Many | One | Ready |
| 'dim_date'[date] *[<-]1 'LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7'[Date] | true | OneDirection | Many | One | Ready |
| 'dim_security'[benchmark_id] *[<-]1 'dim_benchmark'[benchmark_id] | true | OneDirection | Many | One | Ready |

## INFO.VIEW.MEASURES

All 16 measures returned `State = Valid`. The DAX formula column matches `../powerbi/measures.md` exactly. The export's FormatString column came back empty; the formats are set on the measures (Measure tools shows them) and are listed here.

| Table | Measure | FormatString | State |
|---|---|---|---|
| _Measures | Total Fees | `\$#,0.00` | Valid |
| _Measures | Net Flows | `\$#,0.00` | Valid |
| _Measures | AUM (naive SUM) | `\$#,0.00` | Valid |
| _Measures | Ending AUM | `\$#,0.00` | Valid |
| _Measures | Ending Clients | `#,0` | Valid |
| _Measures | Avg AUM per Client | `\$#,0.00` | Valid |
| _Measures | Ending AUM LY | `\$#,0.00` | Valid |
| _Measures | AUM YoY % | `0.00%` | Valid |
| _Measures | Ending AUM PM | `\$#,0.00` | Valid |
| _Measures | AUM MoM % | `0.00%` | Valid |
| _Measures | Avg Monthly AUM | `\$#,0.00` | Valid |
| _Measures | Fee Yield (bps) | `0.00` | Valid |
| _Measures | Organic Growth Rate | `0.00%` | Valid |
| _Measures | AUM-Weighted Alpha | `0.00%` | Valid |
| _Measures | Alpha Signal | `(text)` | Valid |
| _Measures | Top 10 Client Share | `0.00%` | Valid |
