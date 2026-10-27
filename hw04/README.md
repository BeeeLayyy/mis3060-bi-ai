# HW4 — Cleaning the Wildcat Capital Data

Audit, clean and validate the eight Wildcat Capital tables (5 dimensions, 3 facts) without inventing data, and prove the fix worked.

## Structure

```
hw04/
├── README.md                 this file
├── decision_log.md           Part B: one entry per issue (written before the cleaning code)
├── scripts/
│   ├── common.py             shared paths, table metadata, text-only loader
│   ├── 01_profile.py         Part A: generic profiler + 4 groups of checks
│   ├── 02_clean.py           Part C: cleaning program with asserts and audit trail
│   └── 03_validate.py        Part D: RI function, rules, reconciliations, IQR, scorecard
├── data/
│   ├── clean/                8 clean tables + README_clean.md
│   └── audit/                cleaning_log.csv, value_changes.csv, quarantine_*.csv
└── reports/
    ├── profile_raw.csv, dq_summary_raw.csv          (Part A)
    ├── data_quality_scorecard.csv                   (Part D)
    ├── ri_results.csv, rule_checks.csv, reconciliations.csv, iqr_outliers.csv
    └── cleaning_report.md                           (Part E)
```

## How to run

From the repo root, with the raw folder (the eight CSVs) as the argument:

```bash
python hw04/scripts/01_profile.py "Wildcat Capital"
python hw04/scripts/02_clean.py   "Wildcat Capital"
python hw04/scripts/03_validate.py "Wildcat Capital"
```

If no argument is given the scripts look for `Wildcat Capital/` or `data/raw/` in the repo root. Raw files are read as text (`dtype=str, keep_default_na=False`) and are never modified. `02_clean.py` stops with an `AssertionError` if any fix does not do what it claims or if `raw rows != clean rows + quarantined rows`.

## Claude Code review

Claude Desktop drafted the scripts; Claude Code reviewed them before each commit.

| What Claude Code flagged | What I did |
|---|---|
| _filled in below after review_ | |
