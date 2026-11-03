"""
HW5 - Star Schema checks for the Wildcat Capital clean tables.
MIS3060 Business Intelligence with AI

Proves the key, grain and measure claims in star_design.md:
  1. Row counts match the handout
  2. Every primary key is unique and never blank
  3. Every foreign key resolves to its dimension (no orphans), and blanks are explained
  4. Each fact table's grain is unique
  5. Supporting facts for Part C and Part E (blank security_id, advisor consistency,
     first-of-month dates, fee and alpha reconciliation)

Run from the repo root:
    python hw05/hw05_checks.py "Wildcat Capital Clean"
With no argument it looks for "Wildcat Capital Clean/" in the repo root.
"""

import sys
from pathlib import Path
import pandas as pd

# Folder with the eight clean CSVs: first argument, else "Wildcat Capital Clean/" in the repo root
DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "Wildcat Capital Clean"

EXPECTED_ROWS = {
    "dim_advisor": 25,
    "dim_benchmark": 8,
    "dim_client": 2500,
    "dim_date": 1827,
    "dim_security": 500,
    "fact_fees": 122197,
    "fact_portfolio_snapshot": 129547,
    "fact_transactions": 298572,
}

PRIMARY_KEYS = {
    "dim_advisor": "advisor_id",
    "dim_benchmark": "benchmark_id",
    "dim_client": "client_id",
    "dim_date": "date_id",
    "dim_security": "security_id",
    "fact_fees": "fee_id",
    "fact_portfolio_snapshot": "snapshot_id",
    "fact_transactions": "txn_id",
}

# (child table, child column, parent table, parent column)
FOREIGN_KEYS = [
    ("dim_client", "advisor_id", "dim_advisor", "advisor_id"),
    ("dim_security", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_fees", "client_id", "dim_client", "client_id"),
    ("fact_fees", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_fees", "fee_date", "dim_date", "date"),
    ("fact_portfolio_snapshot", "client_id", "dim_client", "client_id"),
    ("fact_portfolio_snapshot", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_portfolio_snapshot", "snapshot_date", "dim_date", "date"),
    ("fact_transactions", "client_id", "dim_client", "client_id"),
    ("fact_transactions", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_transactions", "security_id", "dim_security", "security_id"),
    ("fact_transactions", "txn_date", "dim_date", "date"),
]

GRAINS = {
    "fact_fees": ["client_id", "fee_date"],
    "fact_portfolio_snapshot": ["client_id", "snapshot_date"],
    "fact_transactions": ["txn_id"],
}


def load_tables():
    tables = {}
    for name in EXPECTED_ROWS:
        # Read keys as nullable integers and dates/zip as text so nothing is silently coerced
        dtypes = {"zip_code": str, "fee_date": str, "snapshot_date": str, "txn_date": str, "date": str}
        df = pd.read_csv(DATA_DIR / f"{name}.csv", dtype=dtypes)
        for col in df.columns:
            if col.endswith("_id"):
                df[col] = df[col].astype("Int64")
        tables[name] = df
    return tables


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  ({detail})" if detail else ""))
    return ok


def main():
    t = load_tables()
    all_ok = True

    print("\n1. Row counts vs handout")
    for name, expected in EXPECTED_ROWS.items():
        n = len(t[name])
        all_ok &= check(f"{name}: {n:,} rows", n == expected, f"expected {expected:,}")

    print("\n2. Primary keys unique and not blank")
    for name, pk in PRIMARY_KEYS.items():
        s = t[name][pk]
        all_ok &= check(f"{name}[{pk}]", s.is_unique and s.notna().all(),
                        f"{s.nunique():,} distinct, {s.isna().sum()} blank")
    # dim_date[date] is the column the facts actually join to, so it must also be unique
    d = t["dim_date"]["date"]
    all_ok &= check("dim_date[date] (join column)", d.is_unique and d.notna().all(),
                    f"{d.min()} to {d.max()}")

    print("\n3. Foreign key integrity (orphans = non-blank values with no match)")
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        values = t[child][ccol]
        blanks = values.isna().sum()
        orphans = (~values.dropna().isin(t[parent][pcol])).sum()
        all_ok &= check(f"{child}[{ccol}] -> {parent}[{pcol}]", orphans == 0,
                        f"{orphans} orphans, {blanks:,} blank")

    print("\n4. Grain: each fact row is unique at its stated grain")
    for name, cols in GRAINS.items():
        dupes = t[name].duplicated(subset=cols).sum()
        all_ok &= check(f"{name} unique on {cols}", dupes == 0, f"{dupes} duplicates")

    print("\n5. Supporting checks")
    tx = t["fact_transactions"]
    blank_sec = tx[tx["security_id"].isna()]["txn_type"].value_counts()
    print(f"  Blank security_id by txn_type: {blank_sec.to_dict()}")
    trade_types = {"Buy", "Sell", "Dividend"}
    all_ok &= check("No Buy/Sell/Dividend row is missing security_id",
                    not set(blank_sec.index) & trade_types)
    all_ok &= check("shares and price blank exactly where security_id is blank",
                    (tx["shares"].isna() == tx["security_id"].isna()).all()
                    and (tx["price"].isna() == tx["security_id"].isna()).all())
    all_ok &= check("amount is never negative (direction lives in txn_type)", (tx["amount"] >= 0).all())

    client_adv = t["dim_client"].set_index("client_id")["advisor_id"]
    for name in GRAINS:
        f = t[name]
        mismatch = (f["advisor_id"] != f["client_id"].map(client_adv)).sum()
        all_ok &= check(f"{name}[advisor_id] matches dim_client[advisor_id]", mismatch == 0,
                        f"{mismatch} mismatches")

    for name, dcol in [("fact_fees", "fee_date"), ("fact_portfolio_snapshot", "snapshot_date")]:
        first = t[name][dcol].str.endswith("-01").all()
        all_ok &= check(f"{name}[{dcol}] always the 1st of the month", first)

    fees = t["fact_fees"]
    recalc = fees["aum_basis"] * fees["bps_charged"] / 10000 / 12
    fee_gap = (recalc - fees["amount"]).abs().max()
    all_ok &= check("fees amount = aum_basis x bps_charged / 10,000 / 12", fee_gap < 0.01,
                    f"max gap ${fee_gap:.4f}")

    snap = t["fact_portfolio_snapshot"]
    alpha = snap["return_ytd"] - snap["benchmark_return_ytd"]
    # 1e-4 tolerance: some returns are stored to 4 decimals, so the difference can be off by rounding
    gap = (alpha - snap["active_alpha_ytd"]).abs().max()
    all_ok &= check("active_alpha_ytd = return_ytd - benchmark_return_ytd", gap < 1e-4,
                    f"max gap {gap:.1e}")

    print("\nALL CHECKS PASSED" if all_ok else "\nSOME CHECKS FAILED - review above")


if __name__ == "__main__":
    main()
