"""
HW6 - pandas evidence for the Part C design questions.
MIS3060 Business Intelligence with AI

Prints the numbers used in powerbi/measures.md, Part C, and saves them to
reports/design_questions.txt.

Run from the repo root:
    python hw06/scripts/02_design_questions.py "Wildcat Capital Clean"
"""

import sys
from pathlib import Path

import pandas as pd

HW_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HW_DIR.parent / "Wildcat Capital Clean"
OUT = HW_DIR / "reports" / "design_questions.txt"

lines = []


def say(text=""):
    print(text)
    lines.append(str(text))


def money(x):
    return f"${x:,.2f}"


snap = pd.read_csv(DATA_DIR / "fact_portfolio_snapshot.csv", parse_dates=["snapshot_date"])
fees = pd.read_csv(DATA_DIR / "fact_fees.csv", parse_dates=["fee_date"])
txns = pd.read_csv(DATA_DIR / "fact_transactions.csv", parse_dates=["txn_date"])
clients = pd.read_csv(DATA_DIR / "dim_client.csv")
snap = snap.merge(clients[["client_id", "client_tier", "is_active"]], on="client_id", how="left")
last = snap["snapshot_date"].max()

# ------------------------------------------------------------------ (a)
say("(a) Ending AUM vs SUMX ( VALUES ( dim_client[client_id] ), [Ending AUM] ), no filters")
ending = snap.loc[snap["snapshot_date"] == last, "aum"].sum()
per_client_last = snap.sort_values("snapshot_date").groupby("client_id").tail(1)
sumx = per_client_last["aum"].sum()
gone = per_client_last[per_client_last["snapshot_date"] < last]
say(f"  Last snapshot date in the model : {last.date()}")
say(f"  Ending AUM                      : {money(ending)}  ({(snap['snapshot_date'] == last).sum():,} clients)")
say(f"  SUMX over clients               : {money(sumx)}  ({len(per_client_last):,} clients)")
say(f"  Difference                      : {money(sumx - ending)}")
say(f"  Clients whose last snapshot is before {last.date()}: {len(gone):,}, holding {money(gone['aum'].sum())} at their own last snapshot")
say(f"  Their last snapshot dates range {gone['snapshot_date'].min().date()} to {gone['snapshot_date'].max().date()}")
say(f"  is_active of those clients      : {gone['is_active'].value_counts().to_dict()}")
say()

# ------------------------------------------------------------------ (b)
say("(b) 2024 Fee Yield (bps) vs ICE 9 Effective Fee Rate (bps)")
s24 = snap[snap["snapshot_date"].dt.year == 2024]
f24 = fees[fees["fee_date"].dt.year == 2024]
fee_yield = f24["amount"].sum() * 12 * 10000 / s24["aum"].sum()
eff_rate = f24["amount"].sum() * 12 * 10000 / f24["aum_basis"].sum()
say(f"  Total Fees 2024          : {money(f24['amount'].sum())}")
say(f"  SUM(aum) 2024 snapshots  : {money(s24['aum'].sum())}  ({len(s24):,} client-months)")
say(f"  SUM(aum_basis) 2024 fees : {money(f24['aum_basis'].sum())}  ({len(f24):,} client-months)")
say(f"  Fee Yield (bps)          : {fee_yield:.4f}")
say(f"  Effective Fee Rate (bps) : {eff_rate:.4f}")

key = ["client_id", "month"]
s24 = s24.assign(month=s24["snapshot_date"])
f24 = f24.assign(month=f24["fee_date"])
m = s24.merge(f24[key + ["aum_basis", "amount"]], on=key, how="outer", indicator=True)
both = m[m["_merge"] == "both"]
no_fee = m[m["_merge"] == "left_only"]
say(f"  Snapshot client-months with a fee row     : {len(both):,}")
say(f"  Snapshot client-months with NO fee row    : {len(no_fee):,}  holding {money(no_fee['aum'].sum())} of AUM")
say(f"  Fee rows with no snapshot                 : {(m['_merge'] == 'right_only').sum():,}")
say(f"  Where both exist, aum_basis == aum on     : {(abs(both['aum'] - both['aum_basis']) < 0.005).mean():.2%} of rows")
say(f"  Fee Yield on matched months only (bps)    : {both['amount'].sum() * 12 * 10000 / both['aum'].sum():.4f}")
say(f"  Unbilled client-months by tier            : {no_fee['client_tier'].value_counts().to_dict()}")
say(f"  Clients with an unbilled month, by tier   : {no_fee.groupby('client_tier')['client_id'].nunique().to_dict()}")
first = snap.groupby("client_id")["snapshot_date"].transform("min")
lastm = snap.groupby("client_id")["snapshot_date"].transform("max")
nf = no_fee.set_index(["client_id", "month"]).index
pos = snap.assign(first=first, lastm=lastm).set_index(["client_id", "snapshot_date"])
pos = pos[pos.index.isin(nf)]
say(f"  Unbilled months that are the client's first month: {(pos.index.get_level_values(1) == pos['first']).mean():.1%}; "
    f"last month: {(pos.index.get_level_values(1) == pos['lastm']).mean():.1%} "
    f"(all 2024 snapshot months that are a last month: {(s24['snapshot_date'] == lastm[s24.index]).mean():.1%})")
say(f"  Unbilled months by month                  : {no_fee['month'].dt.month.value_counts().sort_index().to_dict()}")
cl = no_fee.groupby("client_id").size()
say(f"  Clients with at least one unbilled month  : {len(cl):,}; months per client: {cl.describe()[['min', '50%', 'max']].to_dict()}")
all_months = snap.assign(month=snap["snapshot_date"]).merge(
    fees.assign(month=fees["fee_date"])[key], on=key, how="left", indicator=True)
say(f"  All years, snapshot months with no fee row: {(all_months['_merge'] == 'left_only').sum():,} of {len(all_months):,}")
say(f"  Advisory Fee rows in fact_transactions 2024: "
    f"{((txns['txn_type'] == 'Advisory Fee') & (txns['txn_date'].dt.year == 2024)).sum():,}, "
    f"{money(txns.loc[(txns['txn_type'] == 'Advisory Fee') & (txns['txn_date'].dt.year == 2024), 'amount'].sum())}")
say()

# ------------------------------------------------------------------ (c)
say(f"(c) Alpha at the last snapshot ({last.date()})")
at_last = snap[snap["snapshot_date"] == last]
ok = at_last[at_last["is_return_suspect"] != 1]
w = (ok["aum"] * ok["active_alpha_ytd"]).sum() / ok["aum"].sum()
simple = ok["active_alpha_ytd"].mean()
w_all = (at_last["aum"] * at_last["active_alpha_ytd"]).sum() / at_last["aum"].sum()
sus = at_last[at_last["is_return_suspect"] == 1]
say(f"  Rows at last snapshot: {len(at_last):,}; suspect: {len(sus):,} holding {money(sus['aum'].sum())}")
say(f"  AUM-weighted alpha, suspects excluded : {w:.4%}")
say(f"  Simple mean alpha, same rows          : {simple:.4%}")
say(f"  AUM-weighted alpha, suspects included : {w_all:.4%}")
say(f"  Suspect alpha range at last snapshot  : {sus['active_alpha_ytd'].min():.4f} to {sus['active_alpha_ytd'].max():.4f}")
say(f"  Suspect rows, all months: {int(snap['is_return_suspect'].sum()):,}; "
    f"min |alpha| among them: {snap.loc[snap['is_return_suspect'] == 1, 'active_alpha_ytd'].abs().min():.4f}")
# Why last snapshot only: YTD alpha grows through the year
dec = snap[snap["snapshot_date"].dt.year == 2024]
monthly = dec[dec["is_return_suspect"] != 1].groupby(dec["snapshot_date"].dt.month).apply(
    lambda d: (d["aum"] * d["active_alpha_ytd"]).sum() / d["aum"].sum())
say("  2024 AUM-weighted YTD alpha by month (suspects excluded): "
    + ", ".join(f"{k}: {v:.2%}" for k, v in monthly.items()))
y = dec[dec["is_return_suspect"] != 1]
say(f"  Weighted over all 12 months of 2024 (the wrong way)      : {(y['aum'] * y['active_alpha_ytd']).sum() / y['aum'].sum():.4%}")
say()

# ------------------------------------------------------------------ (d)
say("(d) 2024 Organic Growth Rate vs AUM YoY % by client tier")
t = txns.merge(clients[["client_id", "client_tier"]], on="client_id", how="left")
t24 = t[t["txn_date"].dt.year == 2024]
rows = []
for tier, g in snap.groupby("client_tier"):
    e24 = g.loc[g["snapshot_date"] == g.loc[g["snapshot_date"].dt.year == 2024, "snapshot_date"].max(), "aum"].sum()
    e23 = g.loc[g["snapshot_date"] == g.loc[g["snapshot_date"].dt.year == 2023, "snapshot_date"].max(), "aum"].sum()
    tt = t24[t24["client_tier"] == tier]
    dep = tt.loc[tt["txn_type"] == "Deposit", "amount"].sum()
    wd = tt.loc[tt["txn_type"] == "Withdrawal", "amount"].sum()
    rows.append({"tier": tier, "ending_2023": e23, "ending_2024": e24, "deposits": dep, "withdrawals": wd,
                 "net_flows": dep - wd, "organic": (dep - wd) / e23, "yoy": (e24 - e23) / e23,
                 "non_flow_growth": (e24 - e23 - (dep - wd)) / e23})
d = pd.DataFrame(rows)
say(d.to_string(index=False, formatters={
    "ending_2023": money, "ending_2024": money, "deposits": money, "withdrawals": money, "net_flows": money,
    "organic": "{:.2%}".format, "yoy": "{:.2%}".format, "non_flow_growth": "{:.2%}".format}))
say(f"  Share of firm 2024 net flows by tier: "
    + ", ".join(f"{r.tier}: {r.net_flows / d['net_flows'].sum():.1%}" for r in d.itertuples()))
say(f"  Share of firm AUM growth (2023-12 to 2024-12) by tier: "
    + ", ".join(f"{r.tier}: {(r.ending_2024 - r.ending_2023) / (d['ending_2024'] - d['ending_2023']).sum():.1%}" for r in d.itertuples()))

say()

# ------------------------------------------------------------------ Part D: Top 10 Client Share checks
say("Part D: Top 10 Client Share edge cases")


def top10(r):
    """Rank on the balance at the slice's last snapshot (the measure)."""
    lastd = r["snapshot_date"].max()
    a = r[r["snapshot_date"] == lastd].groupby("client_id")["aum"].sum().sort_values(ascending=False)
    return a, a.head(10).sum() / a.sum()


def top10_naive(r):
    """Rank on each client's own last balance, like [Ending AUM] per client inside TOPN."""
    own = r.sort_values("snapshot_date").groupby("client_id").tail(1).set_index("client_id")["aum"]
    top = own.sort_values(ascending=False).head(10).index
    rr = r[r["client_id"].isin(top)]
    num = rr.loc[rr["snapshot_date"] == rr["snapshot_date"].max(), "aum"].sum()   # CALCULATE ( [Ending AUM], Top10 )
    return set(top), num / r.loc[r["snapshot_date"] == r["snapshot_date"].max(), "aum"].sum()


slices = {"Total": snap, "year=2022": snap[snap["snapshot_date"].dt.year == 2022]}
for tier in sorted(snap["client_tier"].unique()):
    slices[f"tier={tier}|year=2024"] = snap[(snap["snapshot_date"].dt.year == 2024) & (snap["client_tier"] == tier)]
for lab, r in slices.items():
    a, share = top10(r)
    naive_set, naive_share = top10_naive(r)
    say(f"  {lab:<22} share {share:.4%} | naive {naive_share:.4%} | same top 10: {naive_set == set(a.head(10).index)} "
        f"| 10th {money(a.iloc[9])} vs 11th {money(a.iloc[10])}")
a, _ = top10(snap)
say(f"  Top 10 at {last.date()}: {list(a.head(10).index)} summing to {money(a.head(10).sum())}")
say(f"  Largest balance of a departed client at their own last snapshot: {money(gone['aum'].max())}")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("\n".join(lines) + "\n")
