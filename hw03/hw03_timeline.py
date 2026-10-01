"""
HW3 Part 4: Corporate events timeline
Joins executive events to the nearest earnings filing for the same company.

Run from the repo root:  python hw03/hw03_timeline.py
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
EARNINGS_CSV = HERE / "earnings_history.csv"
EVENTS_CSV = HERE / "executive_events.csv"
OUT_CSV = HERE / "corporate_events_timeline.csv"
TICKERS = ["AAPL", "MSFT", "NVDA", "JPM", "WMT"]

earn = pd.read_csv(EARNINGS_CSV, dtype=str, keep_default_na=False)
events = pd.read_csv(EVENTS_CSV, dtype=str, keep_default_na=False)
earn["filing_date"] = pd.to_datetime(earn["filing_date"])

# earnings columns get an "earnings_" prefix so they don't collide with event columns
EARN_COLS = ["filing_date", "period", "revenue_reported", "eps_diluted", "net_income"]

rows = []
for _, ev in events.iterrows():
    row = ev.to_dict()
    ev_date = pd.to_datetime(ev["filing_date"])
    same_co = earn[earn["ticker"] == ev["ticker"]]

    if same_co.empty:
        row.update({f"earnings_{c}": "NOT_FOUND" for c in EARN_COLS})
        row["days_to_nearest_earnings"] = "NOT_FOUND"
        row["event_timing"] = "no earnings data"
    else:
        signed = (ev_date - same_co["filing_date"]).dt.days   # negative = event came first
        idx = signed.abs().idxmin()
        nearest = same_co.loc[idx]
        days = int(signed[idx])
        row.update({f"earnings_{c}": nearest[c] for c in EARN_COLS})
        row["earnings_filing_date"] = nearest["filing_date"].date().isoformat()
        row["days_to_nearest_earnings"] = abs(days)
        if abs(days) <= 7:
            row["event_timing"] = "same week"
        elif days < 0:
            row["event_timing"] = "before earnings"
        else:
            row["event_timing"] = "after earnings"
    rows.append(row)

columns = list(events.columns) + [f"earnings_{c}" for c in EARN_COLS] + \
          ["days_to_nearest_earnings", "event_timing"]
timeline = pd.DataFrame(rows, columns=columns)
timeline.to_csv(OUT_CSV, index=False)

# ---------------------------------------------------------------- summary
print("CORPORATE EVENTS TIMELINE\n" + "=" * 60)
for ticker in TICKERS:
    co = timeline[timeline["ticker"] == ticker]
    print(f"\n{ticker}")
    if co.empty:
        print("  No executive events in past 12 months")
        continue
    for _, r in co.sort_values("filing_date").iterrows():
        print(f"  {r['filing_date']} | {r['event_type']:<11} | {r['person_name']} ({r['title']}) "
              f"-> {r['event_timing']}, {r['days_to_nearest_earnings']} days from "
              f"earnings filed {r['earnings_filing_date']}")

counts = timeline["event_timing"].value_counts()
print("\n" + "=" * 60)
print(f"Before earnings: {counts.get('before earnings', 0)}")
print(f"After earnings:  {counts.get('after earnings', 0)}")
print(f"Same week:       {counts.get('same week', 0)}")
print(f"Total events:    {len(timeline)}")
print(f"\nSaved {len(timeline)} rows to {OUT_CSV}")
