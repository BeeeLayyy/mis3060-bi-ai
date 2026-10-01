# HW3 Specifications

## Specification A: Earnings Pipeline (Item 2.02)

Write a Python script saved as `hw03/hw03_earnings.py` that builds an earnings history table from SEC 8-K earnings press releases. Use only `requests`, `beautifulsoup4`, and the Python standard library.

1. **User-Agent.** Set the HTTP header `User-Agent: MIS3060 Villanova ble02@villanova.edu` on every request. Route all HTTP calls through one helper function so no `requests.get()` call can skip the header. Pause about 0.15 seconds between requests to stay under the SEC's 10 requests/second limit.
2. **Companies.** Process these five companies using exactly these CIKs: Apple (AAPL, 0000320193), Microsoft (MSFT, 0000789019), NVIDIA (NVDA, 0001045810), JPMorgan Chase (JPM, 0000019617), Walmart (WMT, 0000104169).
3. **Find filings.** For each company, request `https://data.sec.gov/submissions/CIK{cik}.json`. In `filings.recent`, keep rows where `form` is `8-K` and the comma-separated `items` field contains `2.02` (Results of Operations). If fewer than four are found, also check the older submission files listed under `filings.files`.
4. **Most recent four.** Keep the four most recent Item 2.02 filings per company (one per quarter).
5. **Get the press release.** For each filing, build the filing index URL `https://www.sec.gov/Archives/edgar/data/{cik without leading zeros}/{accession without dashes}/{accession}-index.htm`, parse the document table, and pick the `.htm` exhibit whose Type is `EX-99.1` (fall back to any `EX-99*`, then any file name containing `ex99`). Download it and strip the HTML to plain text (remove scripts/styles, replace non-breaking spaces, collapse whitespace). If no press release exhibit is found or a download fails, print a warning and continue to the next filing. Never crash.
6. **Extract fields** from the plain text using regular expressions, trying several patterns per field because each company words its release differently. Prefer the earliest prose match (e.g. "revenue was $65.6 billion", "quarterly revenue of $94.9 billion") and fall back to income statement table rows (e.g. "Total net sales $ 94,930", which are in millions):
   - quarterly revenue, converted to a number in millions
   - diluted EPS (e.g. "diluted earnings per share was $3.30", "earnings per diluted share were $0.78", "or $4.37 per share", "GAAP EPS of $0.57")
   - net income, converted to millions (exclude non-GAAP and adjusted figures, and prefer "attributable to [company]" over amounts that include noncontrolling interest)
   - reporting period text as written (e.g. "fiscal 2024 fourth quarter", "third-quarter 2024", "Q3 FY25")
7. **Print** one line per filing as it is processed: `[Ticker] | [Period] | Revenue: $X | EPS: $X | Net Income: $X`.
8. **Save** all rows to `hw03/earnings_history.csv` with columns `company, ticker, cik, filing_date, period, revenue_reported, eps_diluted, net_income`. Revenue and net income are in millions of USD.
9. **Missing values.** If a regex finds no match, store the string `NOT_FOUND`. Never store blanks or `None`. Blank and missing are different things.
10. Print a confirmation with the row count and file path when the CSV is saved.

## Specification B: Executive Events Pipeline (Item 5.02)

Write a Python script saved as `hw03/hw03_executives.py` that builds a table of executive departures and appointments from SEC 8-K filings. Use only `requests`, `beautifulsoup4`, and the standard library.

1. **User-Agent.** Same `User-Agent: MIS3060 Villanova ble02@villanova.edu` header on every request, through one shared helper with a short pause between requests.
2. **Find filings.** For the same five companies and CIKs, query `https://data.sec.gov/submissions/CIK{cik}.json` and keep 8-K filings whose `items` field contains `5.02` (Departure of Directors or Certain Officers) and whose `filingDate` is within the past 12 months of today.
3. **Download and parse.** For each matching filing, download the main 8-K document (`primaryDocument` under `https://www.sec.gov/Archives/edgar/data/{cik}/{accession without dashes}/`), strip HTML to plain text, and isolate the Item 5.02 section (from "Item 5.02" to the next "Item X.XX" heading or "SIGNATURES"). Remove the boilerplate item title so its words are not mistaken for events.
4. **Extract events.** In that section, find each person named with a full name. For each person, look at the words right after the name (then right before it) for:
   - departure verbs: resign, retire, step down, depart, terminate, not stand for re-election, cease to serve, transition from
   - appointment verbs: appoint, elect, name, promote, hire, will become/join/serve, succeed
   Classify as `departure`, `appointment`, or `both` (same person leaving one role and taking another). Ignore people mentioned without an event verb. Also extract the person's title (e.g. "Chief Financial Officer", "Senior Vice President", "Director") and the effective date ("effective January 1, 2025"; "effective immediately" means the filing date). Use `NOT_FOUND` for any field that cannot be extracted.
5. **Multiple events.** If one filing reports multiple people (e.g. one departure and one appointment), write a separate row for each.
6. **Print** each event as it is processed: `[Ticker] | [Date] | [Event Type] | [Name] | [Title]`. If a 5.02 filing yields no parseable person (e.g. a compensation-only 5.02), write one row with `NOT_FOUND` fields and print a warning so the filing is not silently lost.
7. **No events.** If a company has no Item 5.02 filings in the past 12 months, print `[Ticker]: No executive events in past 12 months` and continue. This is valid data, not an error.
8. **Save** all events to `hw03/executive_events.csv` with columns `company, ticker, cik, filing_date, event_type, person_name, title, effective_date`. Always write the header, even if there are zero events.
9. Handle any download or parsing failure with a warning and continue; the script must not crash.
