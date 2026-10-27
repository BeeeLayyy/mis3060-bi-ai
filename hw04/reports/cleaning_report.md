# Wildcat Capital Data Cleaning Report
**To:** Portfolio Committee  **From:** Brandon Le  **Re:** Data warehouse extract, 8 tables, 2020–2024

## Executive summary

The extract is usable after cleaning. Every relationship between the eight tables now joins at 100% (raw: the security join matched 0% of trades and 200 transactions pointed to clients that do not exist). Type validity and business-rule pass rates are 100% on all clean tables. No data was invented: 225 rows were quarantined with a traceable reason (25 duplicate clients, 200 orphan transactions), every value change is logged (199,222 cell changes, 98.9% of them a format-only fix to one join key), and raw rows = clean rows + quarantined rows for every table.

The main caution for the committee: **1,397 monthly snapshots (1.1%) carry implausible YTD returns** (above ±100%, up to 9,467%) or an AUM stuck at $1,000. They are flagged, not changed, and should be excluded from any return or alpha average.

## Cleaning summary

| Table | Issue found | Action | Rows |
|---|---|---|---:|
| dim_client | Same client entered twice, last name typo, no activity | Quarantine | 25 |
| dim_client | State written out ("Pennsylvania") | Standardize to 2-letter code | 77 |
| dim_client | Blank risk profile | Fill from snapshot benchmark, flagged | 75 |
| dim_client | Tier disagrees with initial AUM | Flag only | 126 |
| fact_transactions | Client ID not in client table | Quarantine | 200 |
| fact_transactions | security_id stored as "45.0" | Convert to whole number | 197,044 |
| fact_transactions | Negative shares on Buy | Absolute value, confirmed by amount | 835 |
| fact_portfolio_snapshot | Return stored as "9.28%" | Divide by 100, confirmed by benchmark + alpha | 300 |
| fact_portfolio_snapshot | Scientific notation (return, alpha) | Rewrite as decimal, value unchanged | 891 |
| fact_portfolio_snapshot | Implausible return or $1,000 AUM floor | Flag only | 1,397 |
| fact_fees | None found (amount and AUM basis reconcile on all 122,197 rows) | None | 0 |

### Data quality scorecard (raw → clean)

| Table | Completeness | Type validity | Rule pass | Referential match |
|---|---|---|---|---|
| dim_client | 99.785% → 100% | 100% → 100% | 99.388% → 100% | 100% → 100% |
| fact_transactions | 88.665% → 88.665% | 91.730% → 100% | 99.944% → 100% | 81.95% → 100% |
| fact_portfolio_snapshot | 100% → 100% | 99.982% → 100% | 99.961% → 100% | 100% → 100% |
| fact_fees, dim_advisor, dim_benchmark, dim_date | 100% → 100% | 100% → 100% | 100% → 100% | 100% → 100% |
| dim_security | 87.5% → 87.5% | 100% → 100% | 100% → 100% | 100% → 100% |

Completeness below 100% on transactions and securities is by design (see judgment call 3).

## Key judgment calls

**1. Filling 75 blank risk profiles with "Balanced."** Each risk profile maps to exactly one benchmark in the snapshot table, and benchmark 3 (60/40 Blend) is used only by Balanced clients. All 75 blank-profile clients are benchmarked to 3 in every snapshot, so the firm's own data already says they are Balanced. *Risk:* if benchmark 3 was a default given to unprofiled clients, these 75 are mislabeled. Every filled row carries `risk_profile_imputed = 1` so it can be excluded.

**2. Quarantining 200 orphan transactions instead of keeping them.** The client IDs (2702–3192) are beyond the client table (max 2525) and nothing else in the row identifies the client. Kept, they would show up as a "(Blank)" client in every advisor and client report. *Risk:* 0.07% of transactions leave the totals; they are kept in `quarantine_fact_transactions_orphan_client.csv` if the source system can resolve them.

**3. Leaving 101,528 blank security/share/price cells alone.** They line up exactly with Deposit, Withdrawal and Advisory Fee rows, which have no security. The same is true for blank sectors (all 219 ETFs) and blank expense ratios (all 281 single stocks). Filling them would invent trades. *Risk:* a "(Blank)" value in a security slicer; documented in `README_clean.md`.

**4. Flagging, not fixing, extreme returns.** The pattern (e.g., an account at $1,000 with -97.7% that later shows +287%) suggests returns were computed from AUM change including deposits and withdrawals. A true time-weighted return cannot be rebuilt from this extract. *Risk:* averages are distorted unless `flag_extreme_return = 1` rows are filtered out.

## Limitations

- Extreme YTD returns (1,397 rows) and tier-vs-AUM disagreements (126 clients) are flagged, not corrected.
- `is_trading_day` marks weekdays only; market holidays count as trading days.
- Three security names repeat with different tickers; ticker is treated as the business key.
- IQR flags 2–10% of values in transaction amount, fee amount, AUM and return. These columns are right-skewed, so flagged does not mean wrong; large accounts and trades are real.

---
AI-assisted report — reviewed for factual accuracy on Oct 27, 2026 by Brandon Le
