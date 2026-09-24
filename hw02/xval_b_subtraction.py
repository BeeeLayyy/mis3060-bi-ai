"""Cross-validation B: count Buy transactions as total minus all other types."""
import pandas as pd

df = pd.read_csv("data/raw/fact_transactions.csv")
total = len(df)
others = df["txn_type"].isin(["Sell", "Deposit", "Withdrawal", "Dividend", "Advisory Fee"]).sum()
print(f"Total rows:            {total:,}")
print(f"Non-Buy rows:          {others:,}")
print(f"Buy (by subtraction):  {total - others:,}")
