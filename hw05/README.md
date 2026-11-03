# HW5: Star Schema and Power BI

MIS3060 Business Intelligence with AI | Brandon Le

Models the eight clean Wildcat Capital tables as a star schema: keys, grain, measure types, and the Power BI model that Assignment 6 builds on.

## Structure

```
hw05/
├── README.md              this file
├── star_design.md         Parts A, B, C, E and F
├── hw05_checks.py         proves the key, grain and measure claims
└── powerbi/
    ├── hw05.pbix          Power BI model (Part D)
    ├── model_view.png     Model view screenshot
    ├── row_counts.png     Report page: COUNTROWS for every table
    └── project/           the same model as a Power BI Project (hw05.pbip), in text form
```

## How to run

From the repo root, with the clean folder (the eight CSVs) as the argument:

```bash
pip install pandas
python hw05/hw05_checks.py "Wildcat Capital Clean"
```

With no argument the script looks for `Wildcat Capital Clean/` in the repo root. It prints PASS or FAIL for row counts, primary key uniqueness, foreign key integrity, fact grain, and the supporting checks used in Parts C and E.

## Results

- All 8 tables match the handout row counts
- All 8 primary keys are unique with no blanks
- All 13 foreign keys have 0 orphans; the only blanks are 101,528 `fact_transactions[security_id]` values on Deposit, Withdrawal and Advisory Fee rows
- Each fact is unique at its stated grain
- Fact `advisor_id` matches `dim_client[advisor_id]` on 100% of rows

## Power BI model

Row counts in Power BI (report page, one `COUNTROWS` measure per table) match the handout exactly: 25 · 8 · 2,500 · 1,827 · 500 · 122,197 · 129,547 · 298,572. See `powerbi/row_counts.png`.


13 relationships, all many-to-one with single cross-filter direction. 11 active (fact to dimension), 2 inactive (`dim_client` → `dim_advisor`, `dim_security` → `dim_benchmark`), so the active model is a pure star. Facts join to `dim_date[date]`, and `dim_date` is marked as the date table. Details in `star_design.md`.

`powerbi/project/` holds the model as a Power BI Project so the design is readable in Git: column types, relationships, the date table and one `COUNTROWS` measure per table for the row-count check. To rebuild the `.pbix` from it:

1. Open `powerbi/project/hw05.pbip` in Power BI Desktop
2. **Transform data → Edit parameters** → set `DataFolder` to the clean folder, ending in `\`
3. **Refresh**, check the row-count cards against the handout, then **File → Save as** `hw05.pbix`

## Claude Code findings

Claude Desktop drafted the script; Claude Code reviewed it before the commit.

| What Claude Code flagged | What I did |
|---|---|
| Data path was hard-coded to one folder name, unlike the HW4 scripts | Script now takes the folder as an argument and falls back to `Wildcat Capital Clean/` in the repo root |
| Alpha check used a 1e-5 tolerance; run against the HW4 clean files it failed on 233 rows where returns are stored to 4 decimals (max gap 0.00005) | Tolerance raised to 1e-4 and the max gap is now printed, so a real mismatch still fails |
| Fee reconciliation passed or failed silently | Prints the max dollar gap ($0.005, i.e. rounding to the cent) |
| Fact dates are compared to `dim_date[date]` as text | Kept on purpose (same as a BI join on the raw file), but noted: a file that stored timestamps instead of dates would show false orphans |
