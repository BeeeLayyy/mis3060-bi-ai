# HW3 Validation

## 5A: Known-Answer Check (Earnings)

Company/quarter checked: **Apple, fiscal Q3 2026 (quarter ended June 27, 2026; 8-K filed 2026-07-30)**
Official source: [Apple Newsroom, "Apple reports third quarter results"](https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/) (revenue $109.4 billion, diluted EPS $2.02)

| Check | Official Source | Your CSV | Match? |
|---|---|---|---|
| Apple FQ3 2026 Revenue | $109.4 billion ($109,417M in the income statement) | 109400.0 ($ millions) | Yes (CSV takes the rounded prose figure "$109.4 billion") |
| Apple FQ3 2026 EPS Diluted | $2.02 | 2.02 | Yes |

Regex fixes: Apple matched on the first run. Two other companies needed fixes (found while checking the first run's output):
- **JPM EPS.** Every JPM quarter showed $1.50. That was the dividend ("Common dividend of $4.0 billion or $1.50 per share"), not EPS. The headline puts EPS in parentheses: "NET INCOME OF $21.2 BILLION ( $7.70 PER SHARE)".
  - Before: `or \$\s?(\d+\.\d{2}) per (?:diluted )?share`
  - After: added `\(\s?\$\s?(\d+\.\d{2}) per (?:diluted )?share\)`, and changed the old pattern to `(?<!billion )or \$...` so it skips "dividend of $X billion or $Y per share". Also added a table fallback for `Earnings per share - diluted $ 7.70`.
  - Result: fixed. JPM EPS is now $7.70 / $5.94 / $4.63 / $5.07.
- **MSFT net income.** The Dec 2025 and Sep 2025 quarters showed $939M and $523M. Those are the OpenAI investment adjustments from the GAAP-to-non-GAAP reconciliation table. The prose says "Net income, on a GAAP basis, was $27.7 billion", and the pattern did not allow the "on a GAAP basis" phrase.
  - Before: `net income (?:attributable to ...)?(?:was|of|totaled)\s+\$...`
  - After: `net income,? (?:on a GAAP basis,? )?(?:attributable to ...)?(?:was|of|totaled)\s+\$...`
  - Result: fixed. MSFT net income is now $38,500M and $27,700M.

## 5B: Known-Answer Check (Executive Events)

Event checked: **AAPL, Tim Cook (departure as CEO) and John Ternus (appointment as CEO), 8-K filed 2026-04-20**
Sources: [Apple Newsroom](https://www.apple.com/newsroom/2026/04/tim-cook-to-become-apple-executive-chairman-john-ternus-to-become-apple-ceo/), [CNBC](https://www.cnbc.com/2026/04/20/apple-names-john-ternus-ceo-replacing-tim-cook-who-becomes-chairman.html)

| Check | News Source Confirms? | Notes |
|---|---|---|
| Person name and title | Yes | Tim Cook, Chief Executive Officer; John Ternus, previously SVP Hardware Engineering, named CEO. |
| Event type (departure/appointment) | Yes, with a nuance | Cook leaves the CEO role but stays as Executive Chairman, so "both" would be more precise than "departure". The script read "transition from his role as Chief Executive Officer" as a departure. Ternus = appointment is correct. |
| Effective date | Yes | CSV says September 1, 2026; Apple's release says the change is effective September 1, 2026, and the handover happened on that date. |

## 5C: Cross-Validation via yfinance

Ran `python hw03/yfinance_check.py AAPL`. Both sources are in $ millions. yfinance labels Apple's quarter by calendar month end (2026-06-30); Apple's fiscal Q3 actually ended June 27, 2026, so these are the same quarter.

| Metric | From 8-K text extraction | From yfinance | Match? |
|---|---|---|---|
| Revenue | 109,400.0 | 109,417.0 | Yes, within rounding ($17M difference) |
| Net Income | 29,789.0 | 29,789.0 | Yes, exact |

Explanation of any difference: the $17M revenue gap is rounding. The script prefers the earliest prose match, and Apple's release states revenue as "$109.4 billion"; yfinance carries the exact income statement value ($109,417M). Net income came from the income statement table in both sources, so it matches exactly.

## 5D: Pipeline Integrity Checks

| Check | Expected | Actual | Pass/Fail |
|---|---|---|---|
| `earnings_history.csv` row count | Up to 20 (5 companies × 4 quarters) | 20 (0 `NOT_FOUND` cells) | Pass |
| `executive_events.csv` row count | At least 0 (document actual) | 32 (16 appointment, 11 departure, 1 both, 4 `NOT_FOUND`) | Pass |
| `corporate_events_timeline.csv` created | Yes | Yes, 32 rows | Pass |
| Rows with all three fields `"NOT_FOUND"` | 0 (investigate if > 0) | 0 | Pass |

The 4 `NOT_FOUND` rows in `executive_events.csv` were investigated. Each is an Item 5.02 filing that only covers compensation, so there is no departure or appointment to extract:
- MSFT 2025-12-08: shareholders approved the 2026 Stock Plan.
- NVDA 2026-03-06: Fiscal 2027 Variable Compensation Plan.
- JPM 2025-12-08 and 2026-01-22: CEO compensation (James Dimon's annual pay).

They are kept as rows so those filings are not silently dropped.

The zero-event edge case was not triggered in this run: all five companies had at least one Item 5.02 filing in the past 12 months. The script handles it by printing `[Ticker]: No executive events in past 12 months` and moving on to the next company (see the `if not filings:` branch in `main()` of `hw03_executives.py`).
