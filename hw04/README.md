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
| Float regex rejected `1.5e+06` (no `+` in exponent), so type validity would fail on large numbers | Fixed regex to `[eE][-+]?\d+` in `common.py` and `01_profile.py` |
| Scientific-notation fix asserted with a 5e-7 tolerance and `.max()`, which returns NaN when no rows match and lets tiny values round to 0 | Now rewrites with an exact positional format and asserts the numeric value is identical; skips columns with no matches |
| Only `active_alpha_ytd` was checked for scientific notation | Loop now covers every numeric snapshot column |
| `raw = clean + quarantined` only compared counts, and orphan transactions were quarantined after other edits | Added a primary-key level check (sorted keys must match); orphans are quarantined first so the quarantine file holds raw rows |
| Near-duplicate assert (`abs(len(a)-len(b)) <= 2`) would pass for unrelated names | Replaced with `difflib` similarity >= 0.8 |
| 01 and 02 used different duplicate keys, so a duplicate with a blank risk profile could be reported but not cleaned | Both use one shared `DUP_KEY` in `common.py` |
| "Leave as is" log lines (ETF blanks, cash-flow blanks, fees clean) were stated but never checked | Each one is now asserted before it is logged |
| 01 stripped `.0` before the RI check but 03 did not, so the two reports disagreed | 01 now compares raw text, same as a BI join would |
| `pd.to_datetime` without `errors="coerce"` could crash on one bad date; AUM reconciliation could crash on duplicate keys and compared text | Added `errors="coerce"`; dedup the lookup and compare numbers |
| RI function returned 100% match when every key is blank; IQR divided by zero on an empty column | Returns NaN for all-blank keys; IQR skips empty columns |
