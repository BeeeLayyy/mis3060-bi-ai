"""Cross-validation A: count Buy transactions by direct filtering."""
import pandas as pd

df = pd.read_csv("data/raw/fact_transactions.csv")
buy_count = (df["txn_type"] == "Buy").sum()
print(f"Buy transactions (direct filter): {buy_count:,}")
