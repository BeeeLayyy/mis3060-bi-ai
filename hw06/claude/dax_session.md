# Part D: Claude-assisted measure — `Top 10 Client Share` (measure 11)

Workflow: Draft → Test → Debug → Review. The metadata pasted into the prompt is `model_metadata.md`.

> This session was drafted with Claude. If you rerun the prompt in Claude Desktop, paste that transcript under **Response** instead.

---

## Prompt

I'm building a DAX measure in Power BI Desktop. Use only the tables and columns in the metadata below; do not invent names.

**Model metadata** (INFO.VIEW.COLUMNS, INFO.VIEW.RELATIONSHIPS, INFO.VIEW.MEASURES): *[pasted from `model_metadata.md`]*

**What the metadata cannot tell you:**
- `fact_portfolio_snapshot` grain: one row per client per month. `snapshot_date` is always the **first** of the month (2020-01-01 to 2024-12-01)
- `aum` is a **balance** (semi-additive). Summing it across months is wrong; the firm's AUM is the sum at the last snapshot date in the filter
- `active_alpha_ytd` is year-to-date (not needed here)
- Clients leave: 175 clients have no snapshot after 2023, so a client's own last snapshot can be earlier than the filter's last snapshot
- `dim_date` is marked as the date table; all relationships are many-to-one, single direction, dimension → fact
- Existing measure: `Ending AUM = CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) ) )`

**Business definition:** `Top 10 Client Share` = share of Ending AUM held by the 10 largest clients **within the current filter**. On a table by `dim_client[client_tier]` filtered to 2024, each row must be the top 10 of that tier, and the share must never exceed 100%.

Please give me:
1. The measure
2. A plain explanation of its filter context: what is filtered at the grand total, in a year row, and in a tier row
3. A DAX test query I can run in DAX query view to check it

---

## Response

### 1. Measure

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

Format: `0.00%`.

### 2. Filter context

- **`LastSnapshot`** is computed once, in the visual's filter context, before any iteration. It is the single date the whole calculation is pinned to: 2024-12-01 at the grand total and in the 2024 tier rows, the December snapshot in each year row.
- **`VALUES ( dim_client[client_id] )`** is the set of clients visible in the current filter. In a tier row the tier filter is on `dim_client`, so only that tier's clients are listed; this is why the share cannot exceed 100%. `ALL ( dim_client )` would rank the whole firm's top 10 against one tier's total and break that. In a year row `dim_client` is not filtered, so all 2,500 clients are listed, and clients with no row on `LastSnapshot` get a blank `@aum` and sort to the bottom.
- **`CALCULATE ( SUM ( aum ), LastSnapshot )`** runs once per client. Context transition adds that client's `client_id`; `LastSnapshot` replaces the date filter. Each client is measured on the same date as the denominator.
- Why not rank on `[Ending AUM]` per client: `[Ending AUM]` inside the iteration would run `LASTNONBLANK` for that one client, i.e. on the client's *own* last date. A client who left in 2023 would be ranked on a stale balance that is not in today's book.
- **`TOPN`** keeps the 10 rows with the largest `@aum` (more than 10 only if there is a tie at 10th place).
- **Denominator** `[Ending AUM]` is the sum at the same last snapshot, in the same filter.

### 3. Test query

```DAX
// a) The measure at the grand total, by year, and by tier for 2024
EVALUATE
UNION (
    ROW ( "slice", "Total", "Top 10 Client Share", [Top 10 Client Share], "Ending AUM", [Ending AUM] ),
    SELECTCOLUMNS ( VALUES ( dim_date[year] ), "slice", "year=" & dim_date[year],
        "Top 10 Client Share", [Top 10 Client Share], "Ending AUM", [Ending AUM] ),
    CALCULATETABLE (
        SELECTCOLUMNS ( VALUES ( dim_client[client_tier] ), "slice", "tier=" & dim_client[client_tier],
            "Top 10 Client Share", [Top 10 Client Share], "Ending AUM", [Ending AUM] ),
        dim_date[year] = 2024
    )
)

// b) Who the top 10 are at the last snapshot, so the numerator can be checked by hand
EVALUATE
VAR LastSnapshot = LASTNONBLANK ( dim_date[date], CALCULATE ( COUNTROWS ( fact_portfolio_snapshot ) ) )
RETURN
    TOPN (
        10,
        ADDCOLUMNS (
            VALUES ( dim_client[client_id] ),
            "@aum", CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), LastSnapshot )
        ),
        [@aum], DESC
    )
ORDER BY [@aum] DESC
```

Expect every share between 0% and 100%, the tier shares to differ from each other and from the total, and the sum of `@aum` in (b) divided by Ending AUM to equal the total share in (a).
