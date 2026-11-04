"""
01_data_quality.py

Loads the IBM AML transactions dataset (HI-Small), standardises column names,
profiles the data and runs data-quality checks.

Checks:
- Missing values and exact duplicate rows
- Zero or negative amounts
- Paid vs received amount consistency within the same currency
- Cross-currency and self-transfer volumes
- Laundering rate per payment format

Output:
- data/transactions_clean.csv: cleaned data used by 02_red_flags.py
"""

import pandas as pd

df = pd.read_csv("data/HI-Small_Trans.csv")

# 1. Standardise column names (lowercase, no spaces, clear sender/receiver accounts)
df = df.rename(columns={
    "Timestamp": "timestamp",
    "From Bank": "from_bank",
    "Account": "from_account",
    "To Bank": "to_bank",
    "Account.1": "to_account",
    "Amount Received": "amount_received",
    "Receiving Currency": "receiving_currency",
    "Amount Paid": "amount_paid",
    "Payment Currency": "payment_currency",
    "Payment Format": "payment_format",
    "Is Laundering": "is_laundering",
})

# 2. Convert timestamp from text to datetime so time-based analysis is possible
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y/%m/%d %H:%M")

# 3. Basic profile
# Laundering share = mean of a 0/1 column
print("Rows:", len(df))
print("Date range:", df["timestamp"].min(), "to", df["timestamp"].max())
print("Laundering share:", df["is_laundering"].mean())

# 4. Data quality checks
print("\nMissing values per column:")
print(df.isna().sum())

print("\nExact duplicate rows:", df.duplicated().sum())

print("Zero or negative amounts paid:", (df["amount_paid"] <= 0).sum())

# Cross-currency payments (not an error, but worth quantifying)
cross_ccy = df["payment_currency"] != df["receiving_currency"]
print("Cross-currency transactions:", cross_ccy.sum())

# Same currency but paid and received amounts differ (would indicate a data error)
same_ccy_mismatch = (~cross_ccy) & (df["amount_paid"] != df["amount_received"])
print("Same currency but amounts differ:", same_ccy_mismatch.sum())

# Transactions where sender and receiver are the same account
self_tx = df["from_account"] == df["to_account"]
print("Self-transfers:", self_tx.sum())

# 5. Payment formats: volume and laundering rate per format
print("\nTransactions per payment format:")
print(df["payment_format"].value_counts())

print("\nLaundering share per payment format:")
print(df.groupby("payment_format")[
      "is_laundering"].mean().sort_values(ascending=False))

# 6. Remove exact duplicate rows
df = df.drop_duplicates()
print("\nRows after removing duplicates:", len(df))

# 7. Save cleaned data for 02_red_flags.py
df.to_csv("data/transactions_clean.csv", index=False)
print("Saved cleaned data.")
