"""
HW6 - Reconcile the Power BI measure library to pandas.
MIS3060 Business Intelligence with AI

1. Recomputes every measure in pandas straight from the Wildcat Capital Clean CSVs.
   Nothing here reads from Power BI.
2. Reads the Power BI numbers from reports/powerbi_values.csv (measure, slice, value),
   exported with powerbi/export_values.dax in DAX query view.
3. Writes reports/measure_reconciliation.csv
   (measure, slice, powerbi_value, pandas_value, abs_diff, match).
   Tolerance: 0.01 for currency and counts, 0.0001 for ratios and bps, exact for text.

Run from the repo root:
    python hw06/scripts/01_reconcile_measures.py "Wildcat Capital Clean"
With no argument it looks for "Wildcat Capital Clean/" in the repo root.
If reports/powerbi_values.csv does not exist yet, it writes the pandas side only
(reports/pandas_values.csv) so you can see the expected numbers.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HW_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HW_DIR.parent / "Wildcat Capital Clean"
REPORTS = HW_DIR / "reports"
PBI_FILE = REPORTS / "powerbi_values.csv"
OUT_FILE = REPORTS / "measure_reconciliation.csv"

CURRENCY_TOL = 0.01
RATIO_TOL = 0.0001

# measure -> kind (decides the tolerance)
MEASURES = {
    "AUM (naive SUM)": "currency",
    "Total Fees": "currency",
    "Net Flows": "currency",
    "Ending AUM": "currency",
    "Ending Clients": "count",
    "Avg AUM per Client": "currency",
    "Ending AUM LY": "currency",
    "AUM YoY %": "ratio",
    "Ending AUM PM": "currency",
    "AUM MoM %": "ratio",
    "Avg Monthly AUM": "currency",
    "Fee Yield (bps)": "ratio",
    "Organic Growth Rate": "ratio",
    "AUM-Weighted Alpha": "ratio",
    "Alpha Signal": "text",
    "Top 10 Client Share": "ratio",
}

# Required slices (assignment Part B) plus the naive SUM by year
TOTAL_MEASURES = list(MEASURES)
YEAR_MEASURES = ["AUM (naive SUM)", "Ending AUM", "Ending AUM LY", "AUM YoY %", "Avg Monthly AUM",
                 "Fee Yield (bps)", "Organic Growth Rate", "AUM-Weighted Alpha", "Alpha Signal"]
TIER_MEASURES = ["Ending AUM", "Avg AUM per Client", "Ending AUM LY", "AUM YoY %", "Fee Yield (bps)",
                 "Organic Growth Rate", "AUM-Weighted Alpha", "Alpha Signal", "Top 10 Client Share"]
MONTH_MEASURES = ["Ending AUM", "Ending AUM PM", "AUM MoM %"]


# ---------------------------------------------------------------- load
def load(data_dir: Path):
    snap = pd.read_csv(data_dir / "fact_portfolio_snapshot.csv", parse_dates=["snapshot_date"])
    fees = pd.read_csv(data_dir / "fact_fees.csv", parse_dates=["fee_date"])
    txns = pd.read_csv(data_dir / "fact_transactions.csv", parse_dates=["txn_date"])
    clients = pd.read_csv(data_dir / "dim_client.csv", usecols=["client_id", "client_tier"])
    dates = pd.read_csv(data_dir / "dim_date.csv", parse_dates=["date"])
    # Tier comes from dim_client, the same path Power BI filters through
    snap = snap.merge(clients, on="client_id", how="left", validate="many_to_one")
    fees = fees.merge(clients, on="client_id", how="left", validate="many_to_one")
    txns = txns.merge(clients, on="client_id", how="left", validate="many_to_one")
    return snap, fees, txns, dates


# ---------------------------------------------------------------- slices
# A slice is a date window [start, end] plus an optional tier, the same filter
# context Power BI gets from dim_date and dim_client.
class Slice:
    def __init__(self, label, start, end, tier=None):
        self.label, self.start, self.end, self.tier = label, pd.Timestamp(start), pd.Timestamp(end), tier

    def shifted(self, months):
        # SAMEPERIODLASTYEAR = -12 months, DATEADD(..., -1, MONTH) = -1 month.
        # The shifted window is clipped to dim_date (2020-2024), which is what the time
        # intelligence functions return; the facts start 2020-01-01 anyway.
        start = self.start + pd.DateOffset(months=months)
        end = (self.end + pd.offsets.MonthEnd(0) + pd.DateOffset(months=months)) + pd.offsets.MonthEnd(0)
        return Slice(self.label, start, end, self.tier)


def rows(df, date_col, s: Slice):
    m = (df[date_col] >= s.start) & (df[date_col] <= s.end)
    if s.tier is not None:
        m &= df["client_tier"] == s.tier
    return df[m]


# ---------------------------------------------------------------- measures in pandas
def div(a, b):
    """DIVIDE(a, b): blank when b is blank or 0."""
    if a is None or b is None or b == 0 or pd.isna(b):
        return None
    return a / b


def last_snapshot(snap, s):
    r = rows(snap, "snapshot_date", s)
    if r.empty:
        return None, r
    last = r["snapshot_date"].max()           # LASTNONBLANK over dim_date[date]
    return last, r[r["snapshot_date"] == last]


def ending_aum(snap, s):
    last, r = last_snapshot(snap, s)
    return None if last is None else r["aum"].sum()


def compute(snap, fees, txns, s: Slice):
    out = {}
    r = rows(snap, "snapshot_date", s)
    last, at_last = last_snapshot(snap, s)

    out["AUM (naive SUM)"] = r["aum"].sum() if not r.empty else None
    f = rows(fees, "fee_date", s)
    out["Total Fees"] = f["amount"].sum() if not f.empty else None
    t = rows(txns, "txn_date", s)
    dep = t.loc[t["txn_type"] == "Deposit", "amount"].sum()
    wd = t.loc[t["txn_type"] == "Withdrawal", "amount"].sum()
    out["Net Flows"] = dep - wd if not t.empty else None

    out["Ending AUM"] = ending_aum(snap, s)
    out["Ending Clients"] = at_last["client_id"].nunique() if last is not None else None
    out["Avg AUM per Client"] = div(out["Ending AUM"], out["Ending Clients"])

    out["Ending AUM LY"] = ending_aum(snap, s.shifted(-12))
    out["AUM YoY %"] = None if out["Ending AUM LY"] is None else div(out["Ending AUM"] - out["Ending AUM LY"], out["Ending AUM LY"])
    out["Ending AUM PM"] = ending_aum(snap, s.shifted(-1))
    out["AUM MoM %"] = None if out["Ending AUM PM"] is None else div(out["Ending AUM"] - out["Ending AUM PM"], out["Ending AUM PM"])

    out["Avg Monthly AUM"] = div(r["aum"].sum(), r["snapshot_date"].nunique()) if not r.empty else None
    out["Fee Yield (bps)"] = div(out["Total Fees"] * 12 * 10000, r["aum"].sum()) if out["Total Fees"] is not None and not r.empty else None
    out["Organic Growth Rate"] = div(out["Net Flows"], out["Ending AUM LY"])

    # AUM-weighted alpha at the last snapshot, suspect returns excluded
    if last is None:
        out["AUM-Weighted Alpha"] = None
    else:
        ok = at_last[at_last["is_return_suspect"] != 1]
        out["AUM-Weighted Alpha"] = div((ok["aum"] * ok["active_alpha_ytd"]).sum(), ok["aum"].sum()) if not ok.empty else None
    a = out["AUM-Weighted Alpha"]
    out["Alpha Signal"] = None if a is None else ("Outperforming" if a >= 0.02 else "Lagging" if a <= -0.02 else "In line")

    # Top 10 clients by balance at the last snapshot in the filter
    if last is None:
        out["Top 10 Client Share"] = None
    else:
        by_client = at_last.groupby("client_id")["aum"].sum().sort_values(ascending=False)
        out["Top 10 Client Share"] = div(by_client.head(10).sum(), by_client.sum())
    return out


def pandas_values(snap, fees, txns):
    recs = []

    def add(s, names):
        vals = compute(snap, fees, txns, s)
        for n in names:
            recs.append({"measure": n, "slice": s.label, "pandas_value": vals[n]})

    add(Slice("Total", "2020-01-01", "2024-12-31"), TOTAL_MEASURES)
    for y in range(2020, 2025):
        add(Slice(f"year={y}", f"{y}-01-01", f"{y}-12-31"), YEAR_MEASURES)
    for tier in sorted(snap["client_tier"].dropna().unique()):
        add(Slice(f"tier={tier}|year=2024", "2024-01-01", "2024-12-31", tier), TIER_MEASURES)
    add(Slice("month=2024-12", "2024-12-01", "2024-12-31"), MONTH_MEASURES)
    return pd.DataFrame(recs)


# ---------------------------------------------------------------- compare
def to_number(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip().replace(",", "").replace("$", "")
    if s == "":
        return None
    pct = s.endswith("%")
    s = s.rstrip("%")
    try:
        x = float(s)
    except ValueError:
        return None
    return x / 100 if pct else x


def compare(row):
    kind = MEASURES[row["measure"]]
    pbi, pdv = row["powerbi_value"], row["pandas_value"]
    if kind == "text":
        p = None if pd.isna(pbi) or str(pbi).strip() == "" else str(pbi).strip()
        q = None if pdv is None or (isinstance(pdv, float) and np.isnan(pdv)) else str(pdv)
        return pd.Series({"abs_diff": None, "match": p == q})
    p, q = to_number(pbi), to_number(pdv)
    if p is None and q is None:
        return pd.Series({"abs_diff": None, "match": True})       # both blank
    if p is None or q is None:
        return pd.Series({"abs_diff": None, "match": False})      # one side blank
    tol = RATIO_TOL if kind == "ratio" else CURRENCY_TOL
    d = abs(p - q)
    return pd.Series({"abs_diff": d, "match": d <= tol})


def main():
    if not DATA_DIR.exists():
        sys.exit(f"Data folder not found: {DATA_DIR}")
    REPORTS.mkdir(exist_ok=True)
    snap, fees, txns, _ = load(DATA_DIR)
    pdv = pandas_values(snap, fees, txns)

    if not PBI_FILE.exists():
        pdv.to_csv(REPORTS / "pandas_values.csv", index=False)
        print(f"{PBI_FILE.name} not found. Wrote pandas side only: reports/pandas_values.csv ({len(pdv)} rows)")
        return

    pbi = pd.read_csv(PBI_FILE, dtype=str, keep_default_na=False)
    pbi.columns = [c.strip().strip("[]") for c in pbi.columns]
    pbi = pbi.rename(columns={"value": "powerbi_value"})
    pbi["measure"] = pbi["measure"].str.strip()
    pbi["slice"] = pbi["slice"].str.strip()

    rec = pdv.merge(pbi[["measure", "slice", "powerbi_value"]], on=["measure", "slice"], how="left", indicator=True)
    missing = rec[rec["_merge"] == "left_only"]
    rec = rec.drop(columns="_merge")
    rec[["abs_diff", "match"]] = rec.apply(compare, axis=1)
    rec = rec[["measure", "slice", "powerbi_value", "pandas_value", "abs_diff", "match"]]
    rec.to_csv(OUT_FILE, index=False)

    n_ok = int(rec["match"].sum())
    print(f"Wrote {OUT_FILE.relative_to(HW_DIR.parent)}: {n_ok} of {len(rec)} rows match")
    if not missing.empty:
        print(f"{len(missing)} required rows are missing from powerbi_values.csv:")
        print(missing[["measure", "slice"]].to_string(index=False))
    bad = rec[~rec["match"]]
    if not bad.empty:
        print("Mismatches:")
        print(bad.to_string(index=False))


if __name__ == "__main__":
    main()
