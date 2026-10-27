"""
=====================================================================
Script:   03_validate.py  (HW4 Part D - Referential integrity & validation)
Purpose:  Run the same validation suite on the raw and the clean tables:
            - reusable check_referential_integrity() on all 13 relationships
            - rule-based checks for every column with a business bound
            - cross-table reconciliations
            - IQR outlier flags
Output:   reports/data_quality_scorecard.csv  (one row per table per stage)
          reports/ri_results.csv, rule_checks.csv, reconciliations.csv,
          iqr_outliers.csv
Run:      python hw04/scripts/03_validate.py "path/to/Wildcat Capital"
Author:   Brandon Le, MIS3060 (drafted with Claude)
=====================================================================
"""
import os

import pandas as pd

from common import (ALLOWED, CLEAN_DIR, PRIMARY_KEY, RELATIONSHIPS, REPORT_DIR, TABLES,
                    TYPES, ensure_dirs, parse_ok, raw_dir, read_all, to_num)


# ---------------------------------------------------------------
# Reusable RI function (kept for Assignment 5)
# ---------------------------------------------------------------
def check_referential_integrity(fact_df, fact_key, dim_df, dim_key):
    """Match rate of fact_df[fact_key] against dim_df[dim_key].

    Blank/null keys are reported separately (null_key_rate) and excluded from
    the match rate, because some FKs are legitimately blank (e.g. security_id
    on a deposit). Keys are compared as text.
    """
    fk = fact_df[fact_key].astype(str).str.strip()
    null = fk.isin(["", "nan", "None", "NaN"])
    present = fk[~null]
    valid = set(dim_df[dim_key].astype(str).str.strip())
    orphan = ~present.isin(valid)
    n = len(present)
    return {
        "rows": len(fk),
        "match_rate": round(100 * (n - orphan.sum()) / n, 4) if n else 100.0,
        "orphan_rows": int(orphan.sum()),
        "distinct_orphan_keys": int(present[orphan].nunique()),
        "null_key_rate": round(100 * null.mean(), 4),
        "orphan_examples": ", ".join(sorted(present[orphan].unique())[:5]),
    }


# ---------------------------------------------------------------
# Business rules: (table, rule, applies_mask_fn, pass_fn)
# ---------------------------------------------------------------
def rules(T):
    n = to_num
    R = []

    def r(table, rule, passed, applies=None):
        df = T[table]
        applies = pd.Series(True, index=df.index) if applies is None else applies
        R.append({"table": table, "rule": rule, "rows_checked": int(applies.sum()),
                  "rows_failed": int((applies & ~passed.fillna(False)).sum())})

    for (t, c), allowed in ALLOWED.items():
        nb = T[t][c] != ""
        r(t, f"{c} in allowed list", T[t][c].isin(allowed), nb)

    a = T["dim_advisor"]
    r("dim_advisor", "years_experience 0-50", n(a["years_experience"]).between(0, 50))
    r("dim_advisor", "aum_target_mm > 0", n(a["aum_target_mm"]) > 0)
    c = T["dim_client"]
    r("dim_client", "age 18-110", n(c["age"]).between(18, 110))
    r("dim_client", "state is 2-letter code", c["state"].str.fullmatch(r"[A-Z]{2}"))
    r("dim_client", "zip_code 5 digits", c["zip_code"].str.fullmatch(r"\d{5}"))
    r("dim_client", "initial_aum > 0", n(c["initial_aum"]) > 0)
    r("dim_client", "client_since 2010-2024",
      c["client_since"].between("2010-01-01", "2024-12-31"))
    r("dim_client", "risk_profile not blank", c["risk_profile"] != "")
    s = T["dim_security"]
    etf = s["is_etf"] == "True"
    r("dim_security", "expense_ratio_bps 0-300 (ETFs)", n(s["expense_ratio_bps"]).between(0, 300), etf)
    r("dim_security", "sector present for non-ETFs", s["sector"] != "", ~etf)
    d = T["dim_date"]
    dt = pd.to_datetime(d["date"], errors="coerce")
    r("dim_date", "day_of_week matches date", dt.dt.day_name() == d["day_of_week"])
    r("dim_date", "quarter matches month", ((n(d["month"]) - 1) // 3 + 1) == n(d["quarter"]))
    f = T["fact_fees"]
    r("fact_fees", "bps_charged 0-200", n(f["bps_charged"]).between(0, 200))
    r("fact_fees", "amount > 0", n(f["amount"]) > 0)
    r("fact_fees", "fee_date is first of month", f["fee_date"].str.endswith("-01"))
    sn = T["fact_portfolio_snapshot"]
    r("fact_portfolio_snapshot", "aum > 0", n(sn["aum"]) > 0)
    r("fact_portfolio_snapshot", "cash_pct 0-1", n(sn["cash_pct"]).between(0, 1))
    r("fact_portfolio_snapshot", "return_ytd > -100%", n(sn["return_ytd"]) > -1)
    r("fact_portfolio_snapshot", "return_ytd stored as decimal (no %)",
      ~sn["return_ytd"].str.contains("%"))
    r("fact_portfolio_snapshot", "month 1-12", n(sn["month"]).between(1, 12))
    tx = T["fact_transactions"]
    trade = tx["txn_type"].isin(["Buy", "Sell", "Dividend"])
    r("fact_transactions", "shares >= 0 (sign carried by txn_type)", n(tx["shares"]) >= 0, trade)
    r("fact_transactions", "price > 0", n(tx["price"]) > 0, trade)
    r("fact_transactions", "amount > 0", n(tx["amount"]) > 0)
    r("fact_transactions", "security present on trades", tx["security_id"] != "", trade)
    r("fact_transactions", "txn_date 2020-2024", tx["txn_date"].between("2020-01-01", "2024-12-31"))
    return pd.DataFrame(R)


def reconciliations(T):
    n = to_num
    out = []
    f = T["fact_fees"]
    rec = (n(f["aum_basis"]) * n(f["bps_charged"]) / 10000 / 12).round(2)
    out.append(("fact_fees.amount = aum_basis x bps / 10000 / 12", len(f),
                int(((rec - n(f["amount"])).abs() > 0.011).sum())))
    tx = T["fact_transactions"]
    trade = tx["security_id"] != ""
    gap = (n(tx["shares"]) * n(tx["price"]) - n(tx["amount"])).abs()
    out.append(("fact_transactions.amount = shares x price (signed shares)", int(trade.sum()),
                int((trade & (gap > 0.02)).sum())))
    sn = T["fact_portfolio_snapshot"]
    key = sn["client_id"] + "|" + sn["snapshot_date"]
    aum = pd.Series(n(sn["aum"]).values, index=key)
    aum = aum[~aum.index.duplicated()]
    fk = f["client_id"] + "|" + f["fee_date"]
    out.append(("fact_fees.aum_basis = snapshot aum (same client, month)", len(f),
                int((fk.map(aum) != n(f["aum_basis"])).sum())))
    g = (n(sn["return_ytd"]) - n(sn["benchmark_return_ytd"]) - n(sn["active_alpha_ytd"])).abs()
    out.append(("snapshot return_ytd = benchmark_return_ytd + active_alpha_ytd (tol 6e-5)",
                len(sn), int((g > 6e-5).sum())))
    c = T["dim_client"].set_index("client_id")
    out.append(("snapshot account_type = dim_client.primary_account_type", len(sn),
                int((sn["account_type"] != sn["client_id"].map(c["primary_account_type"])).sum())))
    return pd.DataFrame(out, columns=["reconciliation", "rows_checked", "rows_failed"])


def iqr(T):
    out = []
    for t, col in [("fact_transactions", "amount"), ("fact_fees", "amount"),
                   ("fact_portfolio_snapshot", "aum"), ("fact_portfolio_snapshot", "return_ytd")]:
        v = to_num(T[t][col]).dropna()
        q1, q3 = v.quantile([0.25, 0.75])
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        flagged = ((v < lo) | (v > hi)).sum()
        out.append({"table": t, "column": col, "q1": round(q1, 4), "q3": round(q3, 4),
                    "lower_fence": round(lo, 4), "upper_fence": round(hi, 4),
                    "rows_flagged": int(flagged), "pct_flagged": round(100 * flagged / len(v), 2)})
    return pd.DataFrame(out)


def scorecard(T, stage, ri, rl):
    rows = []
    for t in TABLES:
        df = T[t]
        cols = [c for c in TYPES[t]]
        cells = df[cols].astype(str)
        completeness = 100 * (cells.apply(lambda s: s.str.strip() != "")).values.mean()
        pk = PRIMARY_KEY[t]
        uniq = 100 * df[pk].nunique() / len(df)
        valid, total = 0, 0
        for c, typ in TYPES[t].items():
            nb = df[c][df[c].astype(str).str.strip() != ""]
            valid += parse_ok(nb, typ).sum()
            total += len(nb)
        sub = rl[rl["table"] == t]
        rule = 100 * (1 - sub["rows_failed"].sum() / max(sub["rows_checked"].sum(), 1))
        rsub = ri[ri["fact_table"] == t]
        ref = (100 * (rsub["rows"] * (1 - rsub["null_key_rate"] / 100) * rsub["match_rate"] / 100).sum()
               / (rsub["rows"] * (1 - rsub["null_key_rate"] / 100)).sum()) if len(rsub) else None
        rows.append({"table": t, "stage": stage, "rows": len(df),
                     "pct_completeness": round(completeness, 3),
                     "pct_key_uniqueness": round(uniq, 3),
                     "pct_type_validity": round(100 * valid / total, 3),
                     "pct_rule_pass": round(rule, 3),
                     "pct_referential_match": round(ref, 4) if ref is not None else "n/a"})
    return rows


def run(T, stage):
    ri = []
    for fact, fk, dim, pk in RELATIONSHIPS:
        res = check_referential_integrity(T[fact], fk, T[dim], pk)
        ri.append({"stage": stage, "fact_table": fact, "fact_key": fk,
                   "dim_table": dim, "dim_key": pk, **res})
    ri = pd.DataFrame(ri)
    rl = rules(T)
    rl.insert(0, "stage", stage)
    rc = reconciliations(T)
    rc.insert(0, "stage", stage)
    oq = iqr(T)
    oq.insert(0, "stage", stage)
    sc = scorecard(T, stage, ri, rl)
    return ri, rl, rc, oq, sc


def main():
    ensure_dirs()
    raw = read_all(raw_dir())
    clean = read_all(CLEAN_DIR)
    parts = [run(raw, "raw"), run(clean, "clean")]
    names = ["ri_results", "rule_checks", "reconciliations", "iqr_outliers"]
    for i, name in enumerate(names):
        df = pd.concat([p[i] for p in parts], ignore_index=True)
        df.to_csv(os.path.join(REPORT_DIR, f"{name}.csv"), index=False)
    sc = pd.DataFrame(parts[0][4] + parts[1][4]).sort_values(["table", "stage"], ascending=[True, False])
    sc.to_csv(os.path.join(REPORT_DIR, "data_quality_scorecard.csv"), index=False)

    pd.set_option("display.width", 200)
    print("Referential integrity (raw -> clean):")
    ri = pd.concat([p[0] for p in parts])
    print(ri.pivot_table(index=["fact_table", "fact_key"], columns="stage",
                         values=["match_rate", "orphan_rows"], aggfunc="first").to_string())
    print("\nReconciliations:")
    print(pd.concat([p[2] for p in parts]).to_string(index=False))
    print("\nRule failures (rows_failed > 0):")
    rl = pd.concat([p[1] for p in parts])
    print(rl[rl["rows_failed"] > 0].to_string(index=False))
    print("\nIQR outliers (clean):")
    print(parts[1][3].to_string(index=False))
    print("Flagged by IQR does not mean wrong: these columns are right-skewed (a few large "
          "accounts and trades), so the 1.5xIQR fence flags real but large values.")
    print("\nScorecard:")
    print(sc.to_string(index=False))

    # the clean stage must be at least as good as raw, and RI must be 100%
    cl = sc[sc["stage"] == "clean"]
    assert (pd.to_numeric(cl["pct_referential_match"], errors="coerce").dropna() == 100).all()
    assert (cl["pct_type_validity"] == 100).all()


if __name__ == "__main__":
    main()
