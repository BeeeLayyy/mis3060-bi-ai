"""
=====================================================================
Script:   01_profile.py  (HW4 Part A - Audit)
Purpose:  Profile every column of every Wildcat Capital table and run
          data quality checks in four groups:
            1 column level   2 single-table   3 referential integrity
            4 cross-table business rules
Output:   reports/profile_raw.csv, reports/dq_summary_raw.csv
Run:      python hw04/scripts/01_profile.py "path/to/Wildcat Capital"
Author:   Brandon Le, MIS3060 (drafted with Claude)
=====================================================================
"""
import os
import re

import pandas as pd

from common import (ALLOWED, EXPECTED_SHAPE, PRIMARY_KEY, RELATIONSHIPS, REPORT_DIR,
                    TABLES, TYPES, US_STATES, ensure_dirs, parse_ok, raw_dir,
                    read_all, to_num)


# ---------------------------------------------------------------
# Generic column profiler (works on ANY table)
# ---------------------------------------------------------------
def value_shape(v):
    """'Moderately Aggressive' -> 'A A', '03897' -> '9', '9.28%' -> '9.9%'."""
    v = re.sub(r"[A-Za-z]+", "A", v)
    return re.sub(r"\d+", "9", v)


def infer_type(col):
    s = col[col.str.strip() != ""]
    if s.empty:
        return "text"
    for typ in ("int", "float", "date", "bool"):
        if parse_ok(s, typ).mean() >= 0.95:
            return typ
    return "text"


def profile_table(name, df, expected_types=None):
    rows = []
    for c in df.columns:
        col = df[c].astype(str)
        blank = col.str.strip() == ""
        nonblank = col[~blank]
        exp = (expected_types or {}).get(c) or infer_type(col)
        fails = (~parse_ok(nonblank, exp)).sum() if len(nonblank) else 0
        shapes = nonblank.map(value_shape).value_counts()
        num = to_num(nonblank) if exp in ("int", "float") else pd.Series(dtype=float)
        rows.append({
            "table": name, "column": c, "rows": len(df), "expected_type": exp,
            "null_or_blank": int(blank.sum()),
            "literal_none_nan": int(col.str.strip().isin(["None", "NaN", "nan", "NULL", "null"]).sum()),
            "distinct": int(col.nunique()),
            "top_shapes": "; ".join(f"[{k}] {v}" for k, v in shapes.head(4).items()),
            "n_shapes": int(len(shapes)),
            "pct_type_fail": round(100 * fails / max(len(nonblank), 1), 3),
            "whitespace_issues": int((col != col.str.strip()).sum()),
            "mixed_formats": int(len(shapes) > 1 and exp in ("int", "float", "date")),
            "min": num.min() if len(num) else "",
            "max": num.max() if len(num) else "",
            "example_values": " | ".join(col.drop_duplicates().head(5)),
        })
    return rows


# ---------------------------------------------------------------
# Data quality checks
# ---------------------------------------------------------------
findings = []


def add(table, column, group, check, severity, n, example="", note=""):
    findings.append({"table": table, "column": column, "check_group": group,
                     "check": check, "severity": severity, "rows_affected": int(n),
                     "example": str(example)[:200], "note": note})


def column_checks(T):
    for name, df in T.items():
        exp_shape = EXPECTED_SHAPE[name]
        if df.shape != exp_shape:
            add(name, "*", "1 column", "shape vs data dictionary", "ERROR", 0,
                f"{df.shape} vs {exp_shape}")
        for c, typ in TYPES[name].items():
            col = df[c].astype(str)
            nb = col[col.str.strip() != ""]
            bad = nb[~parse_ok(nb, typ)]
            if len(bad):
                add(name, c, "1 column", f"type {typ} parse failure", "ERROR", len(bad),
                    bad.head(3).tolist())
            if typ in ("int",) and nb.str.fullmatch(r"\d+\.0").any():
                n = nb.str.fullmatch(r"\d+\.0").sum()
                add(name, c, "1 column", "integer key stored as float text (45.0)", "ERROR", n,
                    nb[nb.str.fullmatch(r"\d+\.0")].head(3).tolist())
            if typ == "float" and nb.str.contains("%").any():
                n = nb.str.contains("%").sum()
                add(name, c, "1 column", "percent strings mixed with decimals", "ERROR", n,
                    nb[nb.str.contains("%")].head(3).tolist())
            if typ == "float" and nb.str.contains(r"[eE]-?\d").any():
                n = nb.str.contains(r"[eE]-?\d").sum()
                add(name, c, "1 column", "scientific notation", "INFO", n,
                    nb[nb.str.contains(r"[eE]-?\d")].head(3).tolist(),
                    "parses fine as float; only a display/format issue")
            blanks = (col.str.strip() == "").sum()
            if blanks:
                add(name, c, "1 column", "blank values", "WARN", blanks)
            ws = (col != col.str.strip()).sum()
            if ws:
                add(name, c, "1 column", "leading/trailing whitespace", "WARN", ws)
            if (name, c) in ALLOWED:
                bad = nb[~nb.isin(ALLOWED[(name, c)])]
                if len(bad):
                    add(name, c, "1 column", "value outside allowed list", "ERROR", len(bad),
                        bad.value_counts().head(5).to_dict())
        pk = PRIMARY_KEY[name]
        dup = df[pk].duplicated().sum()
        add(name, pk, "1 column", "primary key unique", "ERROR" if dup else "INFO", dup)

    c = T["dim_client"]
    st = c["state"][c["state"].str.len() != 2]
    if len(st):
        add("dim_client", "state", "1 column", "state spelled out instead of 2-letter code",
            "ERROR", len(st), st.value_counts().to_dict())
    lz = c["zip_code"].str.startswith("0").sum()
    add("dim_client", "zip_code", "1 column", "zip with leading zero (lost if read as number)",
        "INFO", lz, c.loc[c["zip_code"].str.startswith("0"), "zip_code"].head(3).tolist())
    age = to_num(c["age"])
    add("dim_client", "age", "1 column", "age outside 18-110", "ERROR",
        ((age < 18) | (age > 110)).sum(), f"range {age.min()}-{age.max()}")
    a = T["dim_advisor"]
    add("dim_advisor", "certifications", "1 column", "literal 'None' = no certification",
        "INFO", (a["certifications"] == "None").sum(),
        note="legitimate value, not a missing value; must not be read as NaN")
    s = T["dim_security"]
    add("dim_security", "sector", "1 column", "blank sector", "INFO",
        (s["sector"] == "").sum(), note="check vs is_etf below")
    snap = T["fact_portfolio_snapshot"]
    cp = to_num(snap["cash_pct"])
    add("fact_portfolio_snapshot", "cash_pct", "1 column", "cash_pct outside 0-1", "ERROR",
        ((cp < 0) | (cp > 1)).sum(), f"range {cp.min()}-{cp.max()}")
    r = to_num(snap["return_ytd"])
    add("fact_portfolio_snapshot", "return_ytd", "1 column", "|return_ytd| > 100%", "WARN",
        (r.abs() > 1).sum(), f"range {r.min():.4f} to {r.max():.4f}")
    aum = to_num(snap["aum"])
    add("fact_portfolio_snapshot", "aum", "1 column", "aum <= 0", "ERROR", (aum <= 0).sum())
    add("fact_portfolio_snapshot", "aum", "1 column", "aum exactly 1000.00 (floor value)",
        "WARN", (aum == 1000).sum())
    tx = T["fact_transactions"]
    for col in ("price", "amount"):
        v = to_num(tx[col])
        add("fact_transactions", col, "1 column", f"{col} <= 0", "ERROR", (v <= 0).sum())
    f = T["fact_fees"]
    bps = to_num(f["bps_charged"])
    add("fact_fees", "bps_charged", "1 column", "bps outside 0-200", "ERROR",
        ((bps < 0) | (bps > 200)).sum(), f"range {bps.min()}-{bps.max()}")


def single_table_checks(T):
    for name, df in T.items():
        pk = PRIMARY_KEY[name]
        d = df.drop(columns=[pk]).duplicated().sum()
        add(name, "*", "2 single-table", "exact duplicate rows (ignoring PK)",
            "ERROR" if d else "INFO", d)

    c = T["dim_client"]
    key = ["first_name", "age", "city", "state", "zip_code", "initial_aum", "client_since",
           "advisor_id"]
    g = c[c.duplicated(key, keep=False)]
    pairs = g.groupby(key)["client_id"].apply(list)
    n_near = int((g.groupby(key).size() - 1).sum())
    add("dim_client", "last_name", "2 single-table",
        "near-duplicate client (same person, last name differs)", "ERROR", n_near,
        pairs.head(3).tolist())
    add("dim_client", "client_tier", "2 single-table",
        "tier inconsistent with initial_aum (HNW < $1M or UHNW < $10M)", "WARN",
        (((c["client_tier"] == "HNW") & (to_num(c["initial_aum"]) < 1e6)) |
         ((c["client_tier"] == "UHNW") & (to_num(c["initial_aum"]) < 1e7))).sum())

    s = T["dim_security"]
    etf = s["is_etf"] == "True"
    add("dim_security", "sector", "2 single-table", "blank sector on a non-ETF", "ERROR",
        ((s["sector"] == "") & ~etf).sum())
    add("dim_security", "expense_ratio_bps", "2 single-table",
        "blank expense ratio on an ETF", "ERROR", ((s["expense_ratio_bps"] == "") & etf).sum())
    add("dim_security", "name", "2 single-table", "duplicate security name (distinct tickers)",
        "INFO", s["name"].duplicated().sum(), s.loc[s["name"].duplicated(), "name"].tolist())

    d = T["dim_date"]
    dt = pd.to_datetime(d["date"])
    add("dim_date", "day_of_week", "2 single-table", "day_of_week disagrees with date",
        "ERROR", (dt.dt.day_name() != d["day_of_week"]).sum())
    add("dim_date", "is_month_end", "2 single-table", "is_month_end disagrees with date",
        "ERROR", (dt.dt.is_month_end.astype(int).astype(str) != d["is_month_end"]).sum())
    add("dim_date", "is_trading_day", "2 single-table",
        "is_trading_day = weekday only (market holidays not excluded)", "INFO",
        ((dt.dt.dayofweek < 5).astype(int).astype(str) == d["is_trading_day"]).sum(),
        note="rows where flag equals a pure weekday rule")

    tx = T["fact_transactions"]
    sh, pr, am = to_num(tx["shares"]), to_num(tx["price"]), to_num(tx["amount"])
    trade = tx["security_id"] != ""
    add("fact_transactions", "shares", "2 single-table", "negative shares", "ERROR",
        (sh < 0).sum(), tx.loc[sh < 0, "txn_type"].value_counts().to_dict())
    add("fact_transactions", "amount", "2 single-table", "amount != |shares| x price",
        "ERROR", (trade & ((sh.abs() * pr - am).abs() > 0.02)).sum())
    cash = tx["txn_type"].isin(["Deposit", "Withdrawal", "Advisory Fee"])
    add("fact_transactions", "security_id", "2 single-table",
        "blank security/shares/price on cash-flow types", "INFO", (cash & ~trade).sum(),
        note="legitimate structure: deposits, withdrawals, fees have no security")
    add("fact_transactions", "security_id", "2 single-table",
        "blank security on a trade/dividend type", "ERROR", (~cash & ~trade).sum())

    f = T["fact_fees"]
    rec = (to_num(f["aum_basis"]) * to_num(f["bps_charged"]) / 10000 / 12).round(2)
    add("fact_fees", "amount", "2 single-table", "amount != aum_basis x bps / 10000 / 12",
        "ERROR", ((rec - to_num(f["amount"])).abs() > 0.011).sum())
    add("fact_fees", "*", "2 single-table", "duplicate client + fee_date + fee_type", "ERROR",
        f.duplicated(["client_id", "fee_date", "fee_type"]).sum())

    sn = T["fact_portfolio_snapshot"]
    gap = to_num(sn["return_ytd"]) - to_num(sn["benchmark_return_ytd"]) - to_num(sn["active_alpha_ytd"])
    pct = sn["return_ytd"].str.endswith("%")
    add("fact_portfolio_snapshot", "active_alpha_ytd", "2 single-table",
        "alpha != return - benchmark (decimal rows)", "ERROR", ((gap.abs() > 2e-6) & ~pct).sum())
    add("fact_portfolio_snapshot", "return_ytd", "2 single-table",
        "percent-string rows that reconcile after /100 (rounding tol 5e-5)", "INFO",
        (pct & (gap.abs() <= 6e-5)).sum())
    sdt = pd.to_datetime(sn["snapshot_date"])
    add("fact_portfolio_snapshot", "year", "2 single-table", "year/month disagree with date",
        "ERROR", ((sdt.dt.year.astype(str) != sn["year"]) |
                  (sdt.dt.month.astype(str) != sn["month"])).sum())
    add("fact_portfolio_snapshot", "*", "2 single-table", "duplicate client + snapshot_date",
        "ERROR", sn.duplicated(["client_id", "snapshot_date"]).sum())


def ri_checks(T):
    for fact, fk, dim, pk in RELATIONSHIPS:
        fv = T[fact][fk].str.replace(r"\.0$", "", regex=True)
        nonblank = fv != ""
        orphan = nonblank & ~fv.isin(set(T[dim][pk]))
        add(fact, fk, "3 referential", f"{fk} -> {dim}.{pk} orphans",
            "ERROR" if orphan.sum() else "INFO", orphan.sum(),
            sorted(fv[orphan].unique(), key=lambda x: (len(x), x))[:10])


def business_checks(T):
    c = T["dim_client"].set_index("client_id")
    for fact in ("fact_fees", "fact_portfolio_snapshot", "fact_transactions"):
        df = T[fact]
        known = df["client_id"].isin(c.index)
        mism = known & (df["client_id"].map(c["advisor_id"]) != df["advisor_id"])
        add(fact, "advisor_id", "4 cross-table", "advisor differs from dim_client.advisor_id",
            "ERROR" if mism.sum() else "INFO", mism.sum())
        dcol = {"fact_fees": "fee_date", "fact_portfolio_snapshot": "snapshot_date",
                "fact_transactions": "txn_date"}[fact]
        since = df["client_id"].map(c["client_since"]).str[:8] + "01"
        add(fact, dcol, "4 cross-table", "activity before client_since month", "ERROR",
            (known & (df[dcol] < since)).sum())

    sn = T["fact_portfolio_snapshot"]
    add("fact_portfolio_snapshot", "account_type", "4 cross-table",
        "account_type differs from dim_client.primary_account_type", "ERROR",
        (sn["account_type"] != sn["client_id"].map(c["primary_account_type"])).sum())
    rp = sn["client_id"].map(c["risk_profile"])
    combo = pd.crosstab(rp.replace("", "(blank)"), sn["benchmark_id"])
    add("fact_portfolio_snapshot", "benchmark_id", "4 cross-table",
        "benchmark by risk profile", "INFO", len(sn),
        combo.to_dict(), "each risk profile maps to exactly one benchmark")
    blank_rp = c.index[c["risk_profile"] == ""]
    add("dim_client", "risk_profile", "4 cross-table",
        "blank risk_profile clients that have snapshots (benchmark known)", "WARN",
        sn.loc[sn["client_id"].isin(blank_rp), "client_id"].nunique())

    f = T["fact_fees"]
    key = sn["client_id"] + "|" + sn["snapshot_date"]
    aum = pd.Series(sn["aum"].values, index=key)
    fk = f["client_id"] + "|" + f["fee_date"]
    add("fact_fees", "aum_basis", "4 cross-table", "aum_basis != snapshot aum same client-month",
        "ERROR", (fk.map(aum) != f["aum_basis"]).sum())
    with_facts = set(f["client_id"]) | set(sn["client_id"]) | set(T["fact_transactions"]["client_id"])
    add("dim_client", "client_id", "4 cross-table", "clients with no fact rows at all", "WARN",
        (~c.index.isin(with_facts)).sum(),
        [i for i in c.index if i not in with_facts][:10])


def main():
    ensure_dirs()
    folder = raw_dir()
    print(f"Reading raw tables from: {folder}")
    T = read_all(folder)
    profile = []
    for name in TABLES:
        print(f"  {name:<26} {T[name].shape}")
        profile += profile_table(name, T[name], TYPES[name])
    pd.DataFrame(profile).to_csv(os.path.join(REPORT_DIR, "profile_raw.csv"), index=False)

    column_checks(T)
    single_table_checks(T)
    ri_checks(T)
    business_checks(T)
    dq = pd.DataFrame(findings)
    dq.to_csv(os.path.join(REPORT_DIR, "dq_summary_raw.csv"), index=False)

    hits = dq[(dq["rows_affected"] > 0) & (dq["severity"] != "INFO")]
    print(f"\nprofile_raw.csv: {len(profile)} columns profiled")
    print(f"dq_summary_raw.csv: {len(dq)} checks, {len(hits)} ERROR/WARN with rows affected\n")
    print(hits[["severity", "table", "column", "check", "rows_affected"]].to_string(index=False))


if __name__ == "__main__":
    main()
