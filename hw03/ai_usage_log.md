# HW3 AI Usage Log

## Prompt 1: Specification A (Earnings pipeline)
See `specifications.md`, Specification A (sent in full as the prompt).

## Prompt 2: Specification B (Executive events pipeline)
See `specifications.md`, Specification B (sent in full as the prompt).

## Prompt 3: Timeline
> Write a Python script that reads `hw03/earnings_history.csv` and `hw03/executive_events.csv`. Do the following:
> 1. For each executive event in the events table, calculate the number of days between the executive event's `filing_date` and the nearest earnings filing date for the same company in the earnings table. Call this `days_to_nearest_earnings`.
> 2. Add a column `event_timing` that categorizes each executive event as: `'before earnings'` if the event came before the nearest earnings filing, `'after earnings'` if it came after, or `'same week'` if within 7 days of an earnings filing.
> 3. Save the combined table to `hw03/corporate_events_timeline.csv` with all columns from both source tables plus `days_to_nearest_earnings` and `event_timing`.
> 4. Print a summary: for each company, list any executive events and whether they occurred before or after the nearest earnings announcement.
> 5. Print a final count: how many events occurred before vs. after an earnings announcement across all five companies.

## Iterations
Earnings pipeline (first run: 20 rows, no `NOT_FOUND`, but two companies had wrong values):
- **JPM:** EPS was $1.50 in every quarter, which was the dividend ("or $1.50 per share"). Added a pattern for the headline form "( $7.70 PER SHARE)", made the old "or $X per share" pattern skip "billion or", and added a table fallback for "Earnings per share - diluted". Fixed.
- **MSFT:** net income for the Dec 2025 and Sep 2025 quarters came from the OpenAI adjustment row in the reconciliation table ($939M, $523M). The prose reads "Net income, on a GAAP basis, was $38.5 billion", so I allowed an optional "on a GAAP basis" phrase in the pattern. Fixed.
- AAPL, NVDA and WMT were correct on the first run. AAPL matched the official figures and yfinance (see `validation.md`).

Executive events pipeline (first run: 43 rows, many of them not people):
- Capitalized phrases were read as names: "Transition Date", "Certain Officers", "Compensatory Arrangements", "Investment Bank", "Worldwide Field Operations", "MY PSUs", "Covenant Not". The bad "name" also stole the event verb from the real person. "Worldwide Field Operations" got Ajay K. Puri's retirement, and "Investment Bank" got the Co-President appointment.
  - Fixes: drop a candidate name if any of its words also appears in lowercase in the filing (so it's an ordinary word), add business words to the stop list, and strip the Item 5.02 heading when it starts with "(e)" (two JPM filings).
- Some events are only stated in later sentences ("Ms. Adams will remain ... until her retirement", "Mr. Petno will become sole CEO"). The script now also reads sentences that start with "Mr./Ms. [last name]".
- Cases that needed specific rules:
  - "reporting to CEO Tim Cook" made Tim Cook an appointment, so the script now skips anyone named right after "reporting to".
  - "Mr. Borders succeeds Chris Kondo" made Kondo an appointment. A name right after "succeeds"/"replaces" is now a departure.
  - "C. Douglas McMillon" was dropped because of the single-letter initial; names with an initial are now allowed when they have 3+ words.
  - Lowercase titles ("president and chief executive officer", "general counsel") are now matched.
- Final run: 32 rows, all real people except 4 `NOT_FOUND` rows for compensation-only 5.02 filings (MSFT, NVDA, JPM ×2).

## Something the script did that I didn't specify
The timeline script prefixed the earnings columns with `earnings_` (`earnings_filing_date`, `earnings_period`, ...) so the two `filing_date` columns didn't collide in the join. That was correct; without it pandas would have produced `filing_date_x` / `filing_date_y`, and the summary couldn't say which earnings release each event was matched to.
