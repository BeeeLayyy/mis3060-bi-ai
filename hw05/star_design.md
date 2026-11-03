# HW5: Wildcat Capital Star Schema
MIS3060 Business Intelligence with AI | Brandon Le

Every claim below is checked in `hw05_checks.py`.

---

## Part A: Keys

| Table | Type | Primary key | Foreign keys (column → table[column]) |
|---|---|---|---|
| dim_advisor | Dimension | `advisor_id` | — |
| dim_benchmark | Dimension | `benchmark_id` | — |
| dim_client | Dimension | `client_id` | `advisor_id` → dim_advisor[advisor_id] |
| dim_date | Dimension | `date_id` (the facts join on `date`, which is also unique) | — |
| dim_security | Dimension | `security_id` | `benchmark_id` → dim_benchmark[benchmark_id] |
| fact_fees | Fact | `fee_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`fee_date` → dim_date[date] |
| fact_portfolio_snapshot | Fact | `snapshot_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`benchmark_id` → dim_benchmark[benchmark_id]<br>`snapshot_date` → dim_date[date] |
| fact_transactions | Fact | `txn_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`security_id` → dim_security[security_id]<br>`txn_date` → dim_date[date] |

**Proof in code:** all 8 primary keys are unique with no blanks, and `dim_date[date]` is unique across 1,827 days (2020-01-01 to 2024-12-31). All 13 foreign keys have 0 orphans.

**Key that can legitimately be blank:** `fact_transactions[security_id]` is blank on 101,528 rows. Every one is a Deposit (35,956), Withdrawal (29,830) or Advisory Fee (35,742). These are cash movements, so there is no security to point to. No Buy, Sell or Dividend row is missing a security. Every other foreign key is fully populated.

---

## Part B: Grain

- **fact_fees:** One row represents one fee charged to one client for one month (`client_id` + `fee_date` is unique, and `fee_date` is always the 1st of the month).
- **fact_portfolio_snapshot:** One row represents one client's account position at one month (`client_id` + `snapshot_date` is unique, and `snapshot_date` is always the 1st of the month).
- **fact_transactions:** One row represents one transaction event (a buy, sell, dividend, deposit, withdrawal or advisory fee debit) for one client on one date, tied to a security only when the event involves one.

---

## Part C: Measures

### Fact measures

| Table | Column | Type | How it may be summed or averaged |
|---|---|---|---|
| fact_fees | `amount` | Additive | Fee dollars can be summed across clients, advisors, fee types and months. |
| fact_fees | `aum_basis` | Semi-additive | It is the AUM balance the fee was charged on, so it sums across clients within one month but not across months (use the month-end value or an average over time). |
| fact_fees | `bps_charged` | Non-additive | A rate can't be summed, and a plain average is misleading; the correct rate is total `amount` ÷ total `aum_basis` × 12 × 10,000. |
| fact_portfolio_snapshot | `aum` | Semi-additive | Sum across clients, advisors or tiers for a single month; never add months together (12 monthly snapshots of $1M is not $12M). |
| fact_portfolio_snapshot | `return_ytd` | Non-additive | A cumulative percentage; summing is meaningless, so combine clients with an AUM-weighted average and read one month at a time. |
| fact_portfolio_snapshot | `benchmark_return_ytd` | Non-additive | Same as `return_ytd`: a YTD percentage, so take the value for a month, never a sum. |
| fact_portfolio_snapshot | `active_alpha_ytd` | Non-additive | It is `return_ytd` minus `benchmark_return_ytd` (verified on every row), so it is a difference of percentages and can only be AUM-weighted, not summed. |
| fact_portfolio_snapshot | `cash_pct` | Non-additive | A percentage of the account; to roll up, weight by `aum` (cash dollars = `cash_pct` × `aum`). |
| fact_transactions | `amount` | Additive (within `txn_type`) | Dollars sum across clients, securities and dates, but `amount` is always positive and the direction lives in `txn_type`, so a total across types mixes buys with sells and deposits with withdrawals. Always slice by `txn_type`. |
| fact_transactions | `shares` | Additive (within one security) | Shares sum across clients and dates for the same security and direction, but adding shares of different securities means nothing. Blank on cash rows. |
| fact_transactions | `price` | Non-additive | A per-share price; summing is meaningless, and an average should be weighted by `shares`. Blank on cash rows. |

### Numeric columns in fact tables that are not measures
- **Keys:** `fee_id`, `snapshot_id`, `txn_id`, `client_id`, `advisor_id`, `benchmark_id`, `security_id`
- **Date parts:** `fact_portfolio_snapshot[year]`, `fact_portfolio_snapshot[month]` (duplicates of what `dim_date` gives through `snapshot_date`)
- **Flags:** `fact_portfolio_snapshot[is_return_suspect]` (3,875 rows flagged), `fact_transactions[is_post_departure_txn]` (2,410 rows flagged). Summing a 0/1 flag only gives a count of flagged rows, so they are filters, not measures.

### Numeric attributes in dimension tables that should never be summed
- `dim_advisor`: `years_experience`, `aum_target_mm`
- `dim_client`: `age`, `initial_aum`, `zip_code` (an identifier, loaded as Text)
- `dim_security`: `expense_ratio_bps` (a rate, only populated for the 219 ETFs)
- `dim_date`: `date_id`, `year`, `quarter`, `month`, `week_of_year`, and the `is_*` flags
- Foreign keys inside dimensions: `dim_client[advisor_id]`, `dim_security[benchmark_id]`

These describe a member of the dimension. Adding them up across members (total client age) or through a fact (an advisor's `years_experience` repeated on every transaction) produces a number that represents nothing.

---

## Part D: Power BI model (summary)

Built in `powerbi/hw05.pbix`, screenshot in `powerbi/model_view.png`. All relationships are many-to-one, fact on the many side, single cross-filter direction. `dim_date` is marked as the date table on `dim_date[date]`.

| # | From (many) | To (one) | Status |
|---|---|---|---|
| 1 | fact_fees[client_id] | dim_client[client_id] | Active |
| 2 | fact_fees[advisor_id] | dim_advisor[advisor_id] | Active |
| 3 | fact_fees[fee_date] | dim_date[date] | Active |
| 4 | fact_portfolio_snapshot[client_id] | dim_client[client_id] | Active |
| 5 | fact_portfolio_snapshot[advisor_id] | dim_advisor[advisor_id] | Active |
| 6 | fact_portfolio_snapshot[benchmark_id] | dim_benchmark[benchmark_id] | Active |
| 7 | fact_portfolio_snapshot[snapshot_date] | dim_date[date] | Active |
| 8 | fact_transactions[client_id] | dim_client[client_id] | Active |
| 9 | fact_transactions[advisor_id] | dim_advisor[advisor_id] | Active |
| 10 | fact_transactions[security_id] | dim_security[security_id] | Active |
| 11 | fact_transactions[txn_date] | dim_date[date] | Active |
| 12 | dim_client[advisor_id] | dim_advisor[advisor_id] | Inactive |
| 13 | dim_security[benchmark_id] | dim_benchmark[benchmark_id] | Inactive |

---

## Part E: Relationships and design questions

**Conformed dimensions.** `dim_client`, `dim_advisor` and `dim_date` are shared by all three fact tables, so one slicer on client, advisor or date filters fees, snapshots and transactions the same way. `dim_benchmark` is used only by the snapshot fact, and `dim_security` only by the transactions fact.

**(a) Why do some transaction rows have no `security_id`, and is that a defect?**
All 101,528 blank rows are Deposits, Withdrawals or Advisory Fee debits, and `shares` and `price` are blank on exactly the same rows. Those are cash events that never touch a security, so a blank key is the correct value, not a defect. The only side effect is a `(Blank)` row when ticker is placed on a visual, which holds the cash flows. I left it rather than adding a "Cash" member, since this assignment loads the tables as they are.

**(b) `advisor_id` is in `dim_client` and on all three facts. Which relationship did I keep active, and why?**
I kept each fact's own `advisor_id` → `dim_advisor` active and made `dim_client[advisor_id]` → `dim_advisor` inactive. Power BI only allows one active path between two tables, and the direct fact link keeps the model a one-hop star. The check script shows the fact `advisor_id` matches the client's advisor on 100% of rows today, so the numbers are identical either way. The fact column is still the better choice because it records the advisor at the time of the event; if a client is reassigned, `dim_client` would move all of their history to the new advisor, while the fact keeps credit with whoever actually served them.

**(c) The date dimension has `date_id`, but the facts store calendar dates. Which column did I join on?**
`dim_date[date]`. None of the facts carry `date_id`; `fee_date`, `snapshot_date` and `txn_date` are calendar dates, and every one matches a value in `dim_date[date]` with no orphans. Both sides are typed as Date, and `date` is also the column used to mark the date table. `date_id` is just a row number inside the dimension.

**(d) Star or snowflake?**
Two links connect one dimension to another: `dim_client` → `dim_advisor` and `dim_security` → `dim_benchmark`. Both are in the model as inactive relationships, so the active model is a pure star. The advisor link is covered in (b). For benchmark, `dim_benchmark` already joins straight to the snapshot fact, where it means the portfolio's benchmark. Through `dim_security` it would mean the benchmark a security is measured against, which is a different role. Leaving that path inactive keeps one meaning per slicer, and it can still be turned on in a measure with `USERELATIONSHIP` in Assignment 6.

---

## Part F: Reflection

**1. fact_fees: "How much fee revenue did each advisor region bring in by fee type in 2024?"**
Answerable in one visual. Put `dim_advisor[region]` on rows, `fact_fees[fee_type]` on columns, Sum of `amount` as values, and filter `dim_date[year]` = 2024. Fee `amount` is fully additive, so the default sum is correct.

**2. fact_portfolio_snapshot: "What was total AUM by client tier at the end of 2024?"**
Answerable in one visual, with a catch. Sum of `aum` by `dim_client[client_tier]` is correct only when the date filter is a single month (December 2024). If someone filters to the whole year, Power BI adds 12 months of balances and overstates AUM about 12 times. The schema can't stop that; it takes a semi-additive measure in Assignment 6 (sum across clients, last value across time).

**3. fact_transactions: "What was net new money (deposits minus withdrawals) by advisor each quarter?"**
Not answerable in one visual without DAX. `amount` is always positive, so a sum lumps deposits and withdrawals together, and putting `txn_type` on columns only shows them side by side; the subtraction needs a measure. The schema fix is a signed amount (or a `flow_sign` column of +1/−1 by `txn_type`) so inflows and outflows net out with a simple sum.

**Overall:** the model answers additive questions (fee revenue, trade and dividend dollars, counts) cleanly in plain visuals. Anything involving balances over time, percentages like returns, alpha, cash % and fee rates, or netting directional flows still needs DAX, which is what Assignment 6 is for.
