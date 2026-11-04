# Part D verification: `Top 10 Client Share`

> Items marked **[PBI]** need the Power BI result filled in from DAX query view. Everything else is checked in pandas: the reconciliation rows come from `scripts/01_reconcile_measures.py`, and the 2022 share, top-10 list, tie check and naive-version comparison come from the Part D section of `scripts/02_design_questions.py` (`reports/design_questions.txt`).

## Did it run as written?

**[PBI]** Pasted the measure into `_Measures` unchanged: ran / errored (record which). Test query (a) returned:

| slice | Top 10 Client Share (Power BI) | pandas |
|---|---:|---:|
| Total | | 6.1589% |
| year=2022 | | 5.5309% |
| tier=HNW (2024) | | 3.1397% |
| tier=Retail (2024) | | 1.8348% |
| tier=UHNW (2024) | | 8.1264% |

Test query (b) should list clients 1001, 2361, 1331, 2281, 2183, 1245, 1885, 679, 1855, 796, summing to $784,005,019.49. $784,005,019.49 ÷ $12,729,572,078.86 = 6.1589%.

## Rows of `measure_reconciliation.csv` that prove it

- `Top 10 Client Share, Total`
- `Top 10 Client Share, tier=HNW|year=2024`
- `Top 10 Client Share, tier=Retail|year=2024`
- `Top 10 Client Share, tier=UHNW|year=2024`

The pandas side ranks clients by `aum` on the last `snapshot_date` in the slice, takes the top 10, and divides by the total on that date. It never reads anything from Power BI.

## Edge cases checked

1. **Grand total.** No filter, so `VALUES ( dim_client[client_id] )` returns all 2,500 clients, including the 175 who left. They get a blank `@aum` on 2024-12-01 and fall out of the top 10. pandas: 6.1589%.
2. **`dim_date[year] = 2022`.** `LastSnapshot` is 2022-12-01. pandas: 5.5309%, lower than 2024, so concentration rose over the period.
3. **2024 tier table.** Each tier is ranked within itself: UHNW 8.13%, HNW 3.14%, Retail 1.83%. All below 100%, and none equal to the firm-wide 6.16%, which shows the tier filter reaches `VALUES ( dim_client[client_id] )`. The tier shares are not additive (they do not sum to the total), as expected for a ratio.
4. **Ties at 10th place.** None in any slice: at the total the 10th largest balance is $74,424,366.68 and the 11th $72,106,567.72, so `TOPN` returns exactly 10 rows.

## What changed and why

**[PBI]** Fill in after running. If nothing failed: nothing changed. The draft already pinned every client to `LastSnapshot`, which is the version I kept.

## A claim I confirmed or refuted

**Claim:** ranking clients on `[Ending AUM]` inside the iteration would rank a departed client on a stale balance and give a different answer.

**Result in pandas: refuted for this data, true in principle.** I computed the `[Ending AUM]`-ranked version (each client ranked on their own last balance, numerator taken with `CALCULATE ( [Ending AUM], Top10 )`) at the grand total, 2022, and each 2024 tier. It picked the same 10 clients and the same share every time, because the largest departed client's last balance was $43.4M, well below the $74.4M needed for 10th place. The pinned version stays, because it is correct by construction and the naive one would break if a large client left.

**[PBI]** Optional: confirm in Power BI by creating the naive version as a temporary measure and comparing it on the tier table.
