# HW6: DAX Measure Library — AUM & Performance

MIS3060 Business Intelligence with AI | Brandon Le

A library of DAX measures (#0 to #11 plus the two base measures, 16 in all) on the Wildcat Capital star model (balances, growth, fee yield, alpha, concentration), each built with the pattern that matches its additivity class and reconciled to an independent pandas calculation.

## Structure

```
hw06/
├── README.md                          this file
├── powerbi/
│   ├── hw06.pbix                      posted model + _Measures table + "Measures" page
│   ├── measures.md                    Part A documentation, Part C answers
│   ├── measures.tmdl                  all measures with formats (TMDL view → Apply)
│   ├── measures_define.dax            same measures for DAX query view (fallback)
│   └── export_values.dax              query that produces reports/powerbi_values.csv
├── scripts/
│   ├── 01_reconcile_measures.py       Part B: pandas vs Power BI
│   └── 02_design_questions.py         Part C: pandas evidence
├── reports/
│   ├── powerbi_values.csv             Power BI numbers (measure, slice, value)
│   ├── pandas_values.csv              pandas numbers alone, for reference
│   ├── measure_reconciliation.csv     Part B result
│   └── design_questions.txt           Part C output
└── claude/
    ├── model_metadata.md              INFO.VIEW exports
    ├── dax_session.md                 Part D prompt and response (Top 10 Client Share)
    └── verification.md                Part D verification
```

## How to run

From the repo root, with the clean folder (the eight CSVs) as the argument:

```bash
pip install pandas
python hw06/scripts/01_reconcile_measures.py "Wildcat Capital Clean"
python hw06/scripts/02_design_questions.py "Wildcat Capital Clean"
```

With no argument both scripts look for `Wildcat Capital Clean/` in the repo root. If `reports/powerbi_values.csv` is missing, script 01 writes only `reports/pandas_values.csv`.

## Power BI steps

1. Open `Wildcat_Star_Model.pbix`, **File → Save as** `hw06/powerbi/hw06.pbix`
2. **TMDL view** → new tab → paste `measures.tmdl` → **Apply**. This creates `_Measures` with all 16 measures and their formats. If Apply fails, create `_Measures` with **Enter data** (guide §0) and run `measures_define.dax` in DAX query view, clicking **Update model with changes**
3. Build the **Measures** page (see `measures.md`) and save with it open
4. **DAX query view** → run `export_values.dax` → copy the grid with headers → paste into `reports/powerbi_values.csv`
5. Run script 01. Every row of `measure_reconciliation.csv` should say `True`

## Results

91 measure/slice rows: every measure at the grand total, measures 1, 4, 6-10 and the naive SUM by year, measures 1, 3, 4, 7-11 by tier for 2024, and measure 5 for December 2024.

- Ending AUM at 2024-12-01: **$12,729,572,078.86** across 2,325 clients. `AUM (naive SUM)` over the same filter: $566.7B, about 45 times larger, and pandas makes the identical mistake
- AUM grew 19.58% in 2024 but organic growth was 0.73%: growth is market-driven, and the new money comes from Retail
- Fee Yield 43.15 bps in 2024 vs a 45.53 bps Effective Fee Rate, because 1,684 client-months hold assets but have no fee row
- AUM-weighted alpha 1.45% in 2024 (In line); 2022 is the only Outperforming year at 2.85%

## Mismatches

None so far on the pandas side. Fill in after step 5: list any row that did not match at first, which side was wrong, and the fix.

## Claude Code findings

Claude drafted the DAX and both scripts; Claude Code reviewed them before the commit.

| What Claude Code flagged | What I did |
|---|---|
| The grid copied from DAX query view pastes as tab-separated with `[measure]` headers; the script read commas only and would crash | Separator is sniffed, brackets stripped; tested with a tab-separated paste |
| A required row missing from `powerbi_values.csv` counted as a match when the pandas value was blank (the three 2020 rows) | Missing rows are now always `False`; Power BI rows with unknown labels are listed too |
| `AUM (naive SUM)` sums 129,547 floats to $566.7B; a different summation order can drift close to the $0.01 tolerance | Currency tolerance is `max(0.01, 1e-13 × value)`, which only widens for that row |
| Net Flows and the growth % helpers did not copy DAX blank handling in edge cases | Net Flows is blank only when there are no deposits or withdrawals; YoY/MoM return -100% when only the current balance is blank |
| Several Part C and Part D numbers (top-10 list, 2022 share, tie check, unbilled first/last months) were not produced by any committed script | Added to `02_design_questions.py`; fixed two wording errors it exposed (tier counts were client-months, not clients) |
| `FORMAT` in the export query is locale-dependent | Kept; a comma-decimal export would fail loudly in the reconciliation, not silently |
