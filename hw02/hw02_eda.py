"""
=====================================================================
Script:      hw02_eda.py
Purpose:     Exploratory data analysis of Wildcat Capital transactions
Dataset:     data/raw/fact_transactions.csv
             (client transactions, Jan 2020 - Dec 2024)
Author:      Brandon Le
Course:      MIS3060 Business Intelligence with AI, Villanova University
Generated:   2026-09-23 (with Claude)
Run from repo root:  python hw02/hw02_eda.py
=====================================================================
"""

import os

import matplotlib
matplotlib.use("Agg")  # save charts without opening windows
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------
# Paths
# ---------------------------------------------------------------
DATA_PATH = os.path.join("data", "raw", "fact_transactions.csv")
OUT_DIR = "hw02"
CHART_DIR = os.path.join(OUT_DIR, "charts")
PROFILE_PATH = os.path.join(OUT_DIR, "hw02_profile.txt")
EXPECTED_SHAPE = (298772, 9)

os.makedirs(CHART_DIR, exist_ok=True)
pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", "{:,.2f}".format)

# Everything passed to report() prints to the terminal and is saved
# to the profile text file (items 2-13).
profile_lines = []


def report(text=""):
    text = str(text)
    print(text)
    profile_lines.append(text)


def section(title):
    report("")
    report("=" * 70)
    report(title)
    report("=" * 70)


def find_col(keyword):
    """Return the first column whose name contains keyword (case-insensitive)."""
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None


# ---------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------
print(f"Loading {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH)
print("Loaded.")

# ---------------------------------------------------------------
# 2. Shape
# ---------------------------------------------------------------
section("2. SHAPE")
report(f"Rows: {df.shape[0]:,}   Columns: {df.shape[1]}   Shape: {df.shape}")

# ---------------------------------------------------------------
# 3. Column names and data types
# ---------------------------------------------------------------
section("3. COLUMN NAMES AND DATA TYPES")
report(df.dtypes.to_string())

# ---------------------------------------------------------------
# 4. Missing values
# ---------------------------------------------------------------
section("4. MISSING VALUES PER COLUMN")
missing = pd.DataFrame({
    "missing_count": df.isna().sum(),
    "missing_pct": (df.isna().mean() * 100).round(2),
})
report(missing.to_string())

# ---------------------------------------------------------------
# 5. Descriptive statistics for numeric columns
# ---------------------------------------------------------------
section("5. DESCRIPTIVE STATISTICS (NUMERIC COLUMNS)")
report(df.describe().T.to_string())

# ---------------------------------------------------------------
# 6. txn_type value counts and percentages
# ---------------------------------------------------------------
section("6. TXN_TYPE VALUE COUNTS")
vc = df["txn_type"].value_counts()
vc_table = pd.DataFrame({
    "count": vc,
    "percent": (vc / len(df) * 100).round(2),
})
report(vc_table.to_string())
report(f"Unique txn_type values: {df['txn_type'].nunique()}")

# ---------------------------------------------------------------
# 7. Unique clients, advisors, securities
# ---------------------------------------------------------------
section("7. UNIQUE ENTITIES")
for label, key in [("clients", "client"), ("advisors", "advisor"), ("securities", "security")]:
    col = find_col(key)
    if col:
        report(f"Unique {label:<11} ({col}): {df[col].nunique():,}")
    else:
        report(f"Unique {label:<11}: column not found")

# ---------------------------------------------------------------
# 8. Date range (txn_date is left as stored; ISO strings sort correctly)
# ---------------------------------------------------------------
section("8. DATE RANGE")
report(f"txn_date dtype:  {df['txn_date'].dtype}")
report(f"Earliest date:   {df['txn_date'].min()}")
report(f"Latest date:     {df['txn_date'].max()}")

# ---------------------------------------------------------------
# 9. Duplicate txn_id check
# ---------------------------------------------------------------
section("9. DUPLICATE CHECK")
dup_count = df["txn_id"].duplicated().sum()
report(f"Duplicate txn_id values: {dup_count:,}")

# ---------------------------------------------------------------
# 10. Mean, median, skewness of amount
# ---------------------------------------------------------------
section("10. AMOUNT DISTRIBUTION")
amt_mean = df["amount"].mean()
amt_median = df["amount"].median()
amt_skew = df["amount"].skew()
report(f"Mean amount:     ${amt_mean:,.2f}")
report(f"Median amount:   ${amt_median:,.2f}")
report(f"Skewness:        {amt_skew:.2f}  "
       f"({'right-skewed' if amt_skew > 0 else 'left-skewed' if amt_skew < 0 else 'symmetric'})")

# ---------------------------------------------------------------
# 11. Group by txn_type
# ---------------------------------------------------------------
section("11. AMOUNT BY TXN_TYPE (sorted by mean, descending)")
grouped = (
    df.groupby("txn_type")["amount"]
    .agg(count="count", mean_amount="mean", median_amount="median")
    .round(2)
    .sort_values("mean_amount", ascending=False)
)
report(grouped.to_string())

# ---------------------------------------------------------------
# 12. Correlation matrix and top 3 correlations
# ---------------------------------------------------------------
section("12. CORRELATION MATRIX (shares, price, amount)")
corr = df[["shares", "price", "amount"]].corr().round(2)
report(corr.to_string())

pairs = []
cols = corr.columns.tolist()
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        pairs.append((cols[i], cols[j], corr.iloc[i, j]))
pairs.sort(key=lambda p: abs(p[2]), reverse=True)
report("")
report("Strongest correlations (by absolute value, self-correlations excluded):")
for rank, (a, b, r) in enumerate(pairs[:3], start=1):
    report(f"  {rank}. {a} - {b}: {r:.2f}")

# ---------------------------------------------------------------
# 13. shares min / max / negative count by txn_type
# ---------------------------------------------------------------
section("13. SHARES BY TXN_TYPE (min, max, negative count)")
shares_check = (
    df.groupby("txn_type")["shares"]
    .agg(
        min_shares="min",
        max_shares="max",
        negative_count=lambda s: int((s < 0).sum()),
    )
)
report(shares_check.to_string())
report(f"Total negative shares rows: {int((df['shares'] < 0).sum()):,}")

# ---------------------------------------------------------------
# 14. Shape warning
# ---------------------------------------------------------------
print("\n" + "=" * 70 + "\n14. SHAPE VALIDATION\n" + "=" * 70)
if df.shape != EXPECTED_SHAPE:
    print(f"WARNING: shape is {df.shape}, expected {EXPECTED_SHAPE}. "
          "Check that the correct file was loaded.")
else:
    print(f"Shape check passed: {df.shape}")

# ---------------------------------------------------------------
# 15. Charts
# ---------------------------------------------------------------
print("\n" + "=" * 70 + "\n15. CHARTS\n" + "=" * 70)

# Histogram with mean/median lines
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df["amount"], bins=100, color="steelblue", edgecolor="white")
ax.axvline(amt_mean, color="red", linestyle="--", linewidth=2,
           label=f"Mean: ${amt_mean:,.0f}")
ax.axvline(amt_median, color="green", linestyle="-", linewidth=2,
           label=f"Median: ${amt_median:,.0f}")
ax.set_title("Distribution of Transaction Amount")
ax.set_xlabel("Amount ($)")
ax.set_ylabel("Number of transactions")
ax.legend()
fig.tight_layout()
hist_path = os.path.join(CHART_DIR, "hist_amount.png")
fig.savefig(hist_path, dpi=120)
plt.close(fig)

# Horizontal box plot by txn_type (same order as the grouped table)
order = grouped.index.tolist()
fig, ax = plt.subplots(figsize=(10, 6))
ax.boxplot(
    [df.loc[df["txn_type"] == t, "amount"] for t in order],
    vert=False,
    flierprops={"markersize": 2, "alpha": 0.3},
)
ax.set_yticklabels(order)
ax.set_title("Transaction Amount by Transaction Type")
ax.set_xlabel("Amount ($)")
ax.set_ylabel("Transaction type")
fig.tight_layout()
box_path = os.path.join(CHART_DIR, "box_amount_by_type.png")
fig.savefig(box_path, dpi=120)
plt.close(fig)

# Scatter of shares vs amount, colored by txn_type
# (rows without shares, i.e. non-trade types, have nothing to plot)
fig, ax = plt.subplots(figsize=(10, 6))
for t in sorted(df["txn_type"].dropna().unique()):
    sub = df[(df["txn_type"] == t) & df["shares"].notna()]
    if len(sub):
        ax.scatter(sub["shares"], sub["amount"], s=2, alpha=0.3, label=t)
ax.axvline(0, color="gray", linewidth=0.8)
ax.set_title("Shares vs. Amount by Transaction Type")
ax.set_xlabel("Shares")
ax.set_ylabel("Amount ($)")
ax.legend(markerscale=5)
fig.tight_layout()
scatter_path = os.path.join(CHART_DIR, "scatter_shares_amount.png")
fig.savefig(scatter_path, dpi=120)
plt.close(fig)

for p in (hist_path, box_path, scatter_path):
    print(f"Saved: {p}")

# ---------------------------------------------------------------
# 16. Save profile (items 2-13)
# ---------------------------------------------------------------
with open(PROFILE_PATH, "w", encoding="utf-8") as f:
    f.write("HW2 EDA PROFILE - fact_transactions.csv\n")
    f.write("\n".join(profile_lines))
    f.write("\n")
print(f"\nProfile saved to {PROFILE_PATH}")
print("Done.")
