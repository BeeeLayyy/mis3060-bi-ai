"""
=====================================================================
Script:   02_clean.py  (HW4 Part C - Cleaning program)
Purpose:  Read the 8 raw Wildcat Capital tables (never modified) and
          write a clean copy of all 8 plus an audit trail.
          One transformation at a time; each prints rows affected and
          a before/after check, and asserts the after-state.
Output:   data/clean/*.csv, data/clean/README_clean.md
          data/audit/cleaning_log.csv, value_changes.csv, quarantine_*.csv
Run:      python hw04/scripts/02_clean.py "path/to/Wildcat Capital"
Author:   Brandon Le, MIS3060 (drafted with Claude)
=====================================================================
"""
import os

import pandas as pd

from common import (AUDIT_DIR, CLEAN_DIR, TABLES, US_STATES, ensure_dirs, raw_dir,
                    read_all, to_num)

LOG, CHANGES, QUAR = [], [], {}


def log(table, issue, action, rows, note=""):
    LOG.append({"table": table, "issue": issue, "action": action,
                "rows_affected": int(rows), "note": note})
    print(f"  [{table}] {issue}: {action} -> {rows:,} rows. {note}")


def record_changes(table, key_col, df, mask, col, new_values):
    """Log every changed cell, then apply."""
    old = df.loc[mask, col]
    new = new_values[mask] if isinstance(new_values, pd.Series) else new_values
    CHANGES.append(pd.DataFrame({
        "table": table, "key_column": key_col, "key": df.loc[mask, key_col].values,
        "column": col, "old_value": old.values,
        "new_value": pd.Series(new, index=old.index).values}))
    df.loc[mask, col] = new


def quarantine(table, df, mask, reason, name):
    q = df[mask].copy()
    q.insert(0, "quarantine_reason", reason)
    QUAR.setdefault(table, []).append((name, q))
    return df[~mask].copy()


def fmt6(x):
    s = f"{x:.6f}"
    return "0.000000" if s == "-0.000000" else s


def main():
    ensure_dirs()
    folder = raw_dir()
    print(f"Reading raw tables from: {folder}\n")
    T = read_all(folder)
    raw_rows = {t: len(df) for t, df in T.items()}

    # ============================================================
    # dim_client
    # ============================================================
    c = T["dim_client"]

    # C1. Near-duplicate clients: same person, typo in last name, no facts
    key = ["first_name", "age", "city", "state", "zip_code", "initial_aum",
           "client_since", "advisor_id", "risk_profile", "client_tier",
           "primary_account_type", "is_active"]
    c["_id"] = c["client_id"].astype(int)
    c = c.sort_values("_id")
    dup = c.duplicated(key, keep="first")
    survivor = {tuple(r[key]): r["client_id"] for _, r in c[~dup].iterrows()}
    matched = [survivor[tuple(r[key])] for _, r in c[dup].iterrows()]
    used = set(T["fact_fees"]["client_id"]) | set(T["fact_portfolio_snapshot"]["client_id"]) \
        | set(T["fact_transactions"]["client_id"])
    # verify before acting: the duplicates carry no fact rows, and the survivor
    # last name starts with the duplicate's (truncated / typo'd) last name or differs by 1-2 chars
    assert not c.loc[dup, "client_id"].isin(used).any(), "a duplicate client has facts"
    last = c.set_index("client_id")["last_name"]
    for d_id, s_id in zip(c.loc[dup, "client_id"], matched):
        a, b = last[d_id], last[s_id]
        assert b.startswith(a) or a.startswith(b) or abs(len(a) - len(b)) <= 2, (d_id, a, b)
    before = len(c)
    c.loc[dup, "matched_client_id"] = list(matched)
    c = quarantine("dim_client", c, dup, "near-duplicate of matched_client_id (last-name typo, no fact rows)",
                   "dim_client_near_duplicates")
    c = c.drop(columns=["matched_client_id"])
    log("dim_client", "near-duplicate client records", "quarantine", before - len(c),
        f"{before} -> {len(c)}; every duplicate has 0 fees/snapshots/transactions")
    assert not c.duplicated(key).any()

    # C2. State spelled out -> USPS code
    m = c["state"].str.len() != 2
    print(f"  before: {m.sum()} non-2-letter states {c.loc[m, 'state'].unique().tolist()}")
    record_changes("dim_client", "client_id", c, m, "state", c["state"].map(US_STATES))
    assert c["state"].str.fullmatch(r"[A-Z]{2}").all(), "state not standardized"
    log("dim_client", "state spelled out", "standardize to 2-letter code", m.sum())

    # C3. Blank risk_profile -> fill only where snapshot benchmark proves it
    snap = T["fact_portfolio_snapshot"]
    known = c[c["risk_profile"] != ""].set_index("client_id")["risk_profile"]
    s = snap[snap["client_id"].isin(known.index)]
    pair = pd.crosstab(s["client_id"].map(known), s["benchmark_id"])
    bench_to_risk = {}
    for b in pair.columns:
        profiles = pair.index[pair[b] > 0].tolist()
        if len(profiles) == 1:            # benchmark identifies exactly one profile
            bench_to_risk[b] = profiles[0]
    print(f"  benchmark -> unique risk profile: {bench_to_risk}")
    client_bench = snap.groupby("client_id")["benchmark_id"].agg(lambda x: set(x))
    blank = c["risk_profile"] == ""
    fill = c.loc[blank, "client_id"].map(
        lambda i: bench_to_risk.get(next(iter(client_bench[i])), "")
        if i in client_bench.index and len(client_bench[i]) == 1 else "")
    c["risk_profile_imputed"] = "0"
    fm = blank & (pd.Series(fill, index=c.index).reindex(c.index).fillna("") != "")
    record_changes("dim_client", "client_id", c, fm, "risk_profile", fill.reindex(c.index))
    c.loc[fm, "risk_profile_imputed"] = "1"
    still = (c["risk_profile"] == "").sum()
    assert c.loc[fm, "risk_profile"].ne("").all()
    log("dim_client", "blank risk_profile", "fill from snapshot benchmark_id (1:1 mapping)",
        fm.sum(), f"{blank.sum()} blank before, {still} left blank (no snapshot evidence); "
        f"flag column risk_profile_imputed=1")

    # C4. Flag tier vs initial AUM disagreement (cannot be corrected without inventing data)
    aum = to_num(c["initial_aum"])
    flag = ((c["client_tier"] == "HNW") & (aum < 1e6)) | ((c["client_tier"] == "UHNW") & (aum < 1e7))
    c["flag_tier_aum_mismatch"] = flag.astype(int).astype(str)
    log("dim_client", "tier inconsistent with initial_aum", "flag (leave value)", flag.sum(),
        "flag_tier_aum_mismatch=1; tier may reflect household or current AUM")
    T["dim_client"] = c.drop(columns=["_id"])

    # ============================================================
    # fact_transactions
    # ============================================================
    tx = T["fact_transactions"]

    # T1. security_id stored as float text ("45.0") -> integer text
    m = tx["security_id"].str.fullmatch(r"\d+\.0")
    record_changes("fact_transactions", "txn_id", tx, m, "security_id",
                   tx["security_id"].str.replace(r"\.0$", "", regex=True))
    nb = tx["security_id"] != ""
    assert tx.loc[nb, "security_id"].str.fullmatch(r"\d+").all()
    log("fact_transactions", "security_id stored as 45.0", "convert to integer text", m.sum(),
        "format only; join key now matches dim_security.security_id")

    # T2. Negative shares on Buy rows -> absolute value, verified by amount = shares x price
    sh, pr, am = to_num(tx["shares"]), to_num(tx["price"]), to_num(tx["amount"])
    m = sh < 0
    print(f"  before: {m.sum()} negative shares, types {tx.loc[m, 'txn_type'].value_counts().to_dict()}")
    assert ((sh[m].abs() * pr[m] - am[m]).abs() <= 0.02).all(), "amount does not confirm |shares|"
    record_changes("fact_transactions", "txn_id", tx, m, "shares", tx["shares"].str.lstrip("-"))
    sh2 = to_num(tx["shares"])
    assert (sh2.dropna() >= 0).all()
    assert ((sh2 * pr - am).abs().dropna() <= 0.02).all()
    log("fact_transactions", "negative shares", "absolute value (sign error)", m.sum(),
        "amount = |shares| x price on every row confirms the magnitude")

    # T3. Orphan client_ids -> quarantine
    valid = set(T["dim_client"]["client_id"])
    m = ~tx["client_id"].isin(valid)
    n = m.sum()
    tx = quarantine("fact_transactions", tx, m, "client_id not in dim_client",
                    "fact_transactions_orphan_client")
    assert tx["client_id"].isin(valid).all()
    log("fact_transactions", "orphan client_id", "quarantine", n,
        "IDs cannot be mapped to any client; no evidence to repair")
    T["fact_transactions"] = tx

    # ============================================================
    # fact_portfolio_snapshot
    # ============================================================
    sn = T["fact_portfolio_snapshot"]

    # S1. return_ytd stored as "9.28%" -> decimal, verified vs benchmark + alpha
    m = sn["return_ytd"].str.endswith("%")
    conv = to_num(sn["return_ytd"])
    recon = to_num(sn["benchmark_return_ytd"]) + to_num(sn["active_alpha_ytd"])
    gap = (conv[m] - recon[m]).abs()
    print(f"  before: {m.sum()} percent strings, max gap after /100 = {gap.max():.2e}")
    assert (gap <= 6e-5).all(), "a percent row does not reconcile after /100"
    record_changes("fact_portfolio_snapshot", "snapshot_id", sn, m, "return_ytd",
                   conv.map(fmt6))
    assert not sn["return_ytd"].str.contains("%").any()
    log("fact_portfolio_snapshot", "return_ytd percent strings", "divide by 100", m.sum(),
        f"each row reconciles to benchmark + alpha within rounding (max gap {gap.max():.1e})")

    # S2. active_alpha_ytd in scientific notation -> fixed decimal
    m = sn["active_alpha_ytd"].str.contains(r"[eE]")
    newv = to_num(sn["active_alpha_ytd"]).map(fmt6)
    assert (to_num(newv[m]) - to_num(sn.loc[m, "active_alpha_ytd"])).abs().max() < 5e-7
    record_changes("fact_portfolio_snapshot", "snapshot_id", sn, m, "active_alpha_ytd", newv)
    assert not sn["active_alpha_ytd"].str.contains(r"[eE]").any()
    log("fact_portfolio_snapshot", "scientific notation in active_alpha_ytd",
        "rewrite as fixed decimal", m.sum(), "value unchanged")

    # S3. After S1, every row: return = benchmark + alpha
    gap = (to_num(sn["return_ytd"]) - to_num(sn["benchmark_return_ytd"]) - to_num(sn["active_alpha_ytd"])).abs()
    assert (gap <= 6e-5).all()

    # S4. Extreme YTD returns -> flag only
    r = to_num(sn["return_ytd"])
    flag = (r.abs() > 1) | (to_num(sn["aum"]) == 1000)
    sn["flag_extreme_return"] = flag.astype(int).astype(str)
    log("fact_portfolio_snapshot", "|return_ytd| > 100% or AUM at 1,000 floor",
        "flag (leave value)", flag.sum(),
        "return appears computed from AUM including deposits/withdrawals; cannot recompute without inventing data")
    T["fact_portfolio_snapshot"] = sn

    # ============================================================
    # Tables reviewed and left as is (logged so the decision is visible)
    # ============================================================
    log("dim_advisor", "certifications = 'None'", "leave as is",
        (T["dim_advisor"]["certifications"] == "None").sum(), "means no certification, not missing")
    s = T["dim_security"]
    log("dim_security", "blank sector (ETFs) / blank expense ratio (stocks)", "leave as is",
        ((s["sector"] == "") | (s["expense_ratio_bps"] == "")).sum(),
        "legitimate structure: blanks line up exactly with is_etf")
    tx = T["fact_transactions"]
    log("fact_transactions", "blank security/shares/price on cash flows", "leave as is",
        (tx["security_id"] == "").sum(), "deposits, withdrawals and fee debits have no security")
    log("dim_date", "is_trading_day ignores market holidays", "leave as is", 0,
        "documented as a known limitation")
    log("fact_fees", "no defects found", "none", 0, "amount, aum_basis, keys all reconcile")

    # ============================================================
    # Write outputs + row reconciliation
    # ============================================================
    print("\nRow reconciliation (raw = clean + quarantined):")
    for t in TABLES:
        q = sum(len(x) for _, x in QUAR.get(t, []))
        clean = len(T[t])
        print(f"  {t:<26} raw {raw_rows[t]:>7,} = clean {clean:>7,} + quarantined {q:>4,}")
        assert raw_rows[t] == clean + q, f"{t}: rows lost"
        T[t].to_csv(os.path.join(CLEAN_DIR, f"{t}.csv"), index=False)
    for t, items in QUAR.items():
        for name, q in items:
            q.to_csv(os.path.join(AUDIT_DIR, f"quarantine_{name}.csv"), index=False)

    pd.DataFrame(LOG).to_csv(os.path.join(AUDIT_DIR, "cleaning_log.csv"), index=False)
    ch = pd.concat(CHANGES, ignore_index=True)
    ch.to_csv(os.path.join(AUDIT_DIR, "value_changes.csv"), index=False)
    print(f"\ncleaning_log.csv: {len(LOG)} entries | value_changes.csv: {len(ch):,} cell changes")
    print(ch.groupby(["table", "column"]).size().to_string())
    write_readme(T, raw_rows)


def write_readme(T, raw_rows):
    q = {t: sum(len(x) for _, x in QUAR.get(t, [])) for t in TABLES}
    rows = "\n".join(f"| `{t}.csv` | {raw_rows[t]:,} | {len(T[t]):,} | {q[t]:,} |" for t in TABLES)
    text = f"""# Wildcat Capital - clean tables

Produced by `scripts/02_clean.py` from the raw extract. Raw files are never modified.
Same file names and columns as raw; flag columns added are listed below.

| File | Raw rows | Clean rows | Quarantined |
|---|---:|---:|---:|
{rows}

## Relationships (star schema)

| Fact / child | Key | Dimension |
|---|---|---|
| dim_client | advisor_id | dim_advisor.advisor_id |
| dim_security | benchmark_id | dim_benchmark.benchmark_id |
| fact_fees | client_id, advisor_id, fee_date | dim_client, dim_advisor, dim_date.date |
| fact_portfolio_snapshot | client_id, advisor_id, benchmark_id, snapshot_date | dim_client, dim_advisor, dim_benchmark, dim_date.date |
| fact_transactions | client_id, advisor_id, security_id, txn_date | dim_client, dim_advisor, dim_security, dim_date.date |

All relationships are many-to-one, single direction (dimension filters fact).
`fact_transactions.security_id` is blank for Deposit, Withdrawal and Advisory Fee rows by design.

## Column types for a BI tool

- **Text (not numbers):** `zip_code` (keeps leading zeros), `primary_account_type` / `account_type` (`529` is a plan name), `certifications` (`None` = no certification, do not convert to null), `ticker`, all name columns.
- **Whole numbers:** all `*_id` keys, `age`, `years_experience`, `aum_target_mm`, `year`, `quarter`, `month`, `week_of_year`, all 0/1 flags.
- **Decimal / currency:** `initial_aum`, `aum`, `aum_basis`, `amount`, `price`, `shares`, `bps_charged`, `expense_ratio_bps`.
- **Decimal ratios (0.05 = 5%):** `return_ytd`, `benchmark_return_ytd`, `active_alpha_ytd`, `cash_pct`. Format as percent in the BI tool.
- **Date (YYYY-MM-DD):** `date`, `client_since`, `fee_date`, `snapshot_date`, `txn_date`.
- **Boolean text:** `is_active`, `is_etf` (`True`/`False`).

## Flag columns added

| Table | Column | Meaning |
|---|---|---|
| dim_client | `risk_profile_imputed` | 1 = risk_profile was blank and was filled from the client's snapshot benchmark |
| dim_client | `flag_tier_aum_mismatch` | 1 = HNW with initial AUM under $1M or UHNW under $10M |
| fact_portfolio_snapshot | `flag_extreme_return` | 1 = abs(return_ytd) above 100% or AUM at the 1,000 floor |

## Known limitations (not fixed, on purpose)

- **Extreme YTD returns** are flagged, not changed: they look like AUM change including deposits/withdrawals, and the true time-weighted return cannot be rebuilt from this extract.
- **Client tier vs initial AUM** disagreements are flagged, not changed: tier may be set on household or current AUM, which we do not have.
- **is_trading_day** in dim_date marks weekdays only; market holidays are counted as trading days.
- **Duplicate security names** (3 names, each with distinct tickers) are left as is; ticker is the business key.
- Blank `sector` (ETFs) and blank `expense_ratio_bps` (single stocks) are legitimate and left blank.
"""
    with open(os.path.join(CLEAN_DIR, "README_clean.md"), "w") as f:
        f.write(text)


if __name__ == "__main__":
    main()
