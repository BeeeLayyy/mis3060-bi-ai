# HW6 Measure Library and Design Questions

MIS3060 Business Intelligence with AI | Brandon Le

Every measure lives in the `_Measures` table of `hw06.pbix`. The same DAX is in `measures.tmdl` (paste into **TMDL view → Apply** to create the whole table with formats in one step) and in `measures_define.dax` (DAX query view fallback).

## Part A: Measure library

Additivity classes from Assignment 5 Part C:

| Class | Columns | DAX pattern |
|---|---|---|
| Additive | `fact_fees[amount]`, `fact_transactions[amount]` | `SUM` |
| Semi-additive (balance) | `fact_portfolio_snapshot[aum]` | Last balance: `LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )` |
| Non-additive (rate, return) | `active_alpha_ytd`, every ratio below | Recompute from additive parts, weighted with `SUMX` where needed |

Snapshots fall on the first of each month, so `LASTDATE` or `ENDOFMONTH` would land on a day with no rows and return blank. `LASTNONBLANK` walks back to the last date that actually has snapshot rows in the current filter.

### Base `Total Fees`

```DAX
Total Fees =
SUM ( fact_fees[amount] )
```

- **Pattern:** SUM (additive)  
- **Format:** Currency, 2 decimals  
- **Meaning:** Fee revenue billed in the period.

### Base `Net Flows`

```DAX
Net Flows =
CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[txn_type] = "Deposit" )
    - CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[txn_type] = "Withdrawal" )
```

- **Pattern:** SUM (additive)  
- **Format:** Currency, 2 decimals  
- **Meaning:** New money in minus money out, before market moves.

### #0 `AUM (naive SUM)`

```DAX
AUM (naive SUM) =
SUM ( fact_portfolio_snapshot[aum] )
```

- **Pattern:** SUM, applied to a balance (wrong)  
- **Format:** Currency, 2 decimals  
- **Meaning:** Adds every month's balance together, so a year shows roughly 12 times what the firm manages. Kept only to show the mistake; never on a report.

### #1 `Ending AUM`

```DAX
Ending AUM =
CALCULATE (
    SUM ( fact_portfolio_snapshot[aum] ),
    LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )
)
```

- **Pattern:** Last balance  
- **Format:** Currency, 2 decimals  
- **Meaning:** How much Wildcat manages at the latest month in whatever is selected.

### #2 `Ending Clients`

```DAX
Ending Clients =
CALCULATE (
    DISTINCTCOUNT ( fact_portfolio_snapshot[client_id] ),
    LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )
)
```

- **Pattern:** Last balance (distinct count at the last snapshot)  
- **Format:** Whole number  
- **Meaning:** How many clients hold an account at that latest month.

### #3 `Avg AUM per Client`

```DAX
Avg AUM per Client =
DIVIDE ( [Ending AUM], [Ending Clients] )
```

- **Pattern:** Recompute: ratio of two last-balance measures  
- **Format:** Currency, 2 decimals  
- **Meaning:** Typical relationship size today, the main input for staffing and pricing by tier.

### #4 `Ending AUM LY`

```DAX
Ending AUM LY =
CALCULATE ( [Ending AUM], SAMEPERIODLASTYEAR ( dim_date[date] ) )
```

- **Pattern:** Last balance, time-shifted  
- **Format:** Currency, 2 decimals  
- **Meaning:** What the same book held twelve months earlier.

### #4 `AUM YoY %`

```DAX
AUM YoY % =
DIVIDE ( [Ending AUM] - [Ending AUM LY], [Ending AUM LY] )
```

- **Pattern:** Recompute from last balances  
- **Format:** Percent, 2 decimals  
- **Meaning:** Total one-year growth of the book, from markets and flows combined.

### #5 `Ending AUM PM`

```DAX
Ending AUM PM =
CALCULATE ( [Ending AUM], DATEADD ( dim_date[date], -1, MONTH ) )
```

- **Pattern:** Last balance, time-shifted  
- **Format:** Currency, 2 decimals  
- **Meaning:** What the book held one month earlier.

### #5 `AUM MoM %`

```DAX
AUM MoM % =
DIVIDE ( [Ending AUM] - [Ending AUM PM], [Ending AUM PM] )
```

- **Pattern:** Recompute from last balances  
- **Format:** Percent, 2 decimals  
- **Meaning:** Month-over-month change, the early warning on a bad month.

### #6 `Avg Monthly AUM`

```DAX
Avg Monthly AUM =
DIVIDE (
    SUM ( fact_portfolio_snapshot[aum] ),
    DISTINCTCOUNT ( fact_portfolio_snapshot[snapshot_date] )
)
```

- **Pattern:** Recompute: Σ balance ÷ count of snapshot dates  
- **Format:** Currency, 2 decimals  
- **Meaning:** The balance the firm carried on average through the period, which is what asset-based fees are earned on.

### #7 `Fee Yield (bps)`

```DAX
Fee Yield (bps) =
DIVIDE ( [Total Fees] * 12 * 10000, SUM ( fact_portfolio_snapshot[aum] ) )
```

- **Pattern:** Recompute: additive fees ÷ Σ balance (two fact tables)  
- **Format:** bps, 2 decimals  
- **Meaning:** Annualized fee revenue per dollar managed, the firm's real price for its book.

### #8 `Organic Growth Rate`

```DAX
Organic Growth Rate =
DIVIDE ( [Net Flows], [Ending AUM LY] )
```

- **Pattern:** Recompute: additive flows ÷ last balance a year earlier  
- **Format:** Percent, 2 decimals  
- **Meaning:** Growth that came from clients adding money, not from the market.

### #9 `AUM-Weighted Alpha`

```DAX
AUM-Weighted Alpha =
VAR LastSnapshot = LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )
RETURN
    CALCULATE (
        DIVIDE (
            SUMX ( fact_portfolio_snapshot, fact_portfolio_snapshot[aum] * fact_portfolio_snapshot[active_alpha_ytd] ),
            SUM ( fact_portfolio_snapshot[aum] )
        ),
        LastSnapshot,
        fact_portfolio_snapshot[is_return_suspect] <> 1
    )
```

- **Pattern:** Recompute and weight (SUMX aum × alpha ÷ Σ aum) at the last balance  
- **Format:** Percent, 2 decimals  
- **Meaning:** Dollar-weighted outperformance of client portfolios against their benchmarks for the year to date.

### #10 `Alpha Signal`

```DAX
Alpha Signal =
VAR Alpha = [AUM-Weighted Alpha]
RETURN
    IF (
        ISBLANK ( Alpha ),
        BLANK (),
        SWITCH ( TRUE (), Alpha >= 0.02, "Outperforming", Alpha <= -0.02, "Lagging", "In line" )
    )
```

- **Pattern:** Label on a recomputed ratio  
- **Format:** Text  
- **Meaning:** A plain-English flag a manager can scan: Outperforming, In line or Lagging.

### #11 `Top 10 Client Share`

```DAX
Top 10 Client Share =
VAR LastSnapshot = LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )
VAR ClientAUM =
    ADDCOLUMNS (
        VALUES ( dim_client[client_id] ),
        "@aum", CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), LastSnapshot )
    )
VAR Top10 = TOPN ( 10, ClientAUM, [@aum], DESC )
RETURN
    DIVIDE ( SUMX ( Top10, [@aum] ), [Ending AUM] )
```

- **Pattern:** Recompute: last balance of top 10 ÷ last balance of all  
- **Format:** Percent, 2 decimals  
- **Meaning:** Concentration risk: how much of the selected book would walk out the door if the 10 biggest clients left.

### Two design choices worth calling out

- **`Top 10 Client Share` ranks on the balance at the filter's last snapshot, not on `[Ending AUM]` per client.** `[Ending AUM]` evaluated for one client finds that client's own last date, so a client who left in 2023 would be ranked on a stale balance (see Part C (a)). Pinning every client to `LastSnapshot` keeps the numerator and the denominator on the same date. In this data the two versions give the same answer at every slice I tested, but only the pinned version is correct by construction.
- **`TOPN` iterates `VALUES ( dim_client[client_id] )`, not `ALL ( dim_client )`**, so in the tier table the top 10 are the top 10 of that tier and the share can never exceed 100%.

## Report page

`hw06.pbix` has one page named **Measures**:

- Cards: Ending AUM, Ending Clients, Avg AUM per Client, Top 10 Client Share
- Table by `dim_date[year]`: Ending AUM, AUM YoY %, Avg Monthly AUM, Fee Yield (bps), Organic Growth Rate, AUM-Weighted Alpha, Alpha Signal
- Table by `dim_client[client_tier]` with a visual-level filter `dim_date[year] = 2024`: Ending AUM, Avg AUM per Client, AUM YoY %, Fee Yield (bps), Organic Growth Rate, AUM-Weighted Alpha, Alpha Signal, Top 10 Client Share

`AUM (naive SUM)` is in the model (display folder *Trap*) but on no visual.

### Expected values (pandas, `reports/pandas_values.csv`)

| year | Ending AUM | AUM YoY % | Avg Monthly AUM | Fee Yield (bps) | Organic Growth | AUM-Wtd Alpha | Signal |
|---|---:|---:|---:|---:|---:|---:|---|
| 2020 | $8,130,190,789.37 | | $7,379,299,895.30 | 43.33 | | -0.68% | In line |
| 2021 | $10,010,301,949.11 | 23.13% | $9,135,353,821.89 | 42.96 | 0.62% | -0.16% | In line |
| 2022 | $9,308,159,286.53 | -7.01% | $9,591,147,070.37 | 44.17 | 0.75% | 2.85% | Outperforming |
| 2023 | $10,644,971,737.00 | 14.36% | $9,829,302,609.00 | 43.11 | 0.83% | 1.77% | In line |
| 2024 | $12,729,572,078.86 | 19.58% | $11,288,320,315.31 | 43.15 | 0.73% | 1.45% | In line |

Cards (no filter): Ending AUM $12,729,572,078.86 · Ending Clients 2,325 · Avg AUM per Client $5,475,084.77 · Top 10 Client Share 6.16%.

## Part C: Design questions

Numbers come from `scripts/02_design_questions.py` (output saved in `reports/design_questions.txt`).

### (a) `Ending AUM` vs `SUMX ( VALUES ( dim_client[client_id] ), [Ending AUM] )`

| | Value | Clients |
|---|---:|---:|
| `Ending AUM` | $12,729,572,078.86 | 2,325 |
| `SUMX` over clients | $13,149,297,713.80 | 2,500 |
| Difference | **$419,725,634.94** | 175 |

With no filters, `Ending AUM` takes one date for the whole firm (2024-12-01) and sums the 2,325 accounts on it. The `SUMX` version evaluates `[Ending AUM]` once per client, and context transition makes `LASTNONBLANK` find each client's *own* last snapshot. For the 175 inactive clients that is a date between Dec 2022 and Nov 2023, so their last balance before they left, $419.7M in total, gets added to today's book. That money is gone.

`Ending AUM` answers "How much do we manage today?" The `SUMX` number is the sum of every client's last known balance, which is not a figure anyone should report.

### (b) 2024 `Fee Yield (bps)` vs ICE 9 `Effective Fee Rate (bps)`

| 2024 | Numerator | Denominator | bps |
|---|---|---|---:|
| Effective Fee Rate | fees $48,714,005.93 × 12 × 10,000 | Σ `aum_basis` $128.39B (26,216 fee rows) | 45.53 |
| Fee Yield | same | Σ `aum` $135.46B (27,900 snapshot rows) | 43.15 |

Same fees, different denominator. pandas evidence:

- Where a client-month has both a snapshot and a fee row, `aum_basis = aum` on 100% of rows, so the two bases agree whenever both exist
- 1,684 snapshot client-months in 2024 have **no fee row at all**, holding $7.07B of AUM. Dropping them from the denominator gives a Fee Yield of exactly 45.53 bps, the Effective Fee Rate
- The gaps are scattered: 1,082 clients, every month, every tier (Retail 1,054, HNW 472, UHNW 158), usually one month per client and not tied to a client's first or last month. Across 2020-2024 it is 7,350 of 129,547 snapshot months (5.7%)

**Data limitation:** `fact_fees` does not cover every client-month that holds assets. Effective Fee Rate only looks at months that were billed, so it overstates what the firm earns per dollar managed; Fee Yield charges the unbilled AUM too. The data cannot say whether those months were waived, billed somewhere else, or simply not captured. (Fee revenue is also split across tables: `fact_transactions` holds 8,071 "Advisory Fee" rows worth $62.2M in 2024 that neither measure counts.)

### (c) Why `AUM-Weighted Alpha` reads the last snapshot only, and why suspects are excluded

`active_alpha_ytd` is year-to-date, so each month's row holds more of the year than the one before. The January row is the first sliver of the year; the December row is the year. Weighting across every month of 2024 averages partial years together and gives 0.32%, while the December snapshot alone gives 1.45%. By month, 2024 weighted YTD alpha climbs from -0.01% in January to 1.45% in December. Only the last snapshot in the filter is a complete reading, which is why the measure pins `LastSnapshot`. It also keeps each client's weight at one balance instead of twelve.

`is_return_suspect = 1` marks rows whose alpha is not believable: every one of the 3,875 flagged rows has |alpha| above 50%. At 2024-12-01 there are 148 of them holding only $15.5M (0.12% of AUM), but with alpha as high as 7,134%, so a tiny weight still moves the result.

| At 2024-12-01 | Value |
|---|---:|
| AUM-weighted alpha, suspects excluded (the measure) | **1.45%** (1.4480%) |
| Simple mean of `active_alpha_ytd`, same 2,177 rows | 0.88% (0.8788%) |
| AUM-weighted alpha, suspects included | 1.67% (1.6678%) |

The simple mean is lower than the weighted value, so the larger accounts beat their benchmarks by more than the small ones. Including suspects adds about 22 bps of alpha that comes from bad data, not from managers.

### (d) 2024 Organic Growth Rate vs AUM YoY % by tier

| Tier | Ending AUM 2023 | Net flows 2024 | Organic Growth | AUM YoY % | Growth not from flows |
|---|---:|---:|---:|---:|---:|
| Retail | $447.8M | $44.2M | **9.87%** | 19.13% | 9.26% |
| HNW | $2,130.2M | $25.2M | 1.18% | 19.64% | 18.46% |
| UHNW | $8,067.0M | $8.1M | 0.10% | 19.59% | 19.49% |

All three tiers grew about 19-20%, but for different reasons. Retail is the only tier where clients are adding real money: it brought in 57% of the firm's 2024 net flows and grew about half organically. UHNW grew almost entirely from the market, with net flows of 0.1%, yet it delivered 76% of the firm's dollar AUM growth because it is 76% of the book. So Wildcat's new money comes from Retail, while its dollar growth comes from market returns on UHNW balances.

What it does **not** tell you:
- **Why** the non-flow part happened. The gap between YoY and organic is a residual: market returns, plus balances that dropped out when clients left, plus anything not booked as a Deposit or Withdrawal. It is not a performance number
- **Whether flows are new clients or existing ones topping up.** Net flows also net out withdrawals, so a tier with big gross inflows and big outflows looks the same as a quiet one
- **Tier migration.** `client_tier` is the current tier in `dim_client`, so a client who grew from HNW into UHNW sits in UHNW for every year. 2023 balances are shown under today's tier
- **Profitability.** Retail's organic growth is on the smallest balances; at 82.8 bps Fee Yield it earns more per dollar, but the dollars are small
