"""
02_red_flags.py

Applies five transaction-monitoring rules to the cleaned IBM AML dataset
and evaluates each rule against the laundering labels.

For each rule:
- Hit rate (precision): share of flagged transactions that are real laundering
- Catch rate (recall): share of all laundering transactions the rule detects

Outputs (for Power BI):
- output/rule_summary.csv: one row per rule with its performance
- output/rule5_alerts.csv: all transactions flagged by Rule 5
"""

import pandas as pd

# Load cleaned data from 01_data_quality.py
df = pd.read_csv("data/transactions_clean.csv", parse_dates=["timestamp"])

total_laundering = df["is_laundering"].sum()
print("Total laundering transactions:", total_laundering)

results = []


def evaluate(rule_name, flags):
    """
    Score a monitoring rule against the laundering labels.

    rule_name: label used in the printout and the summary table
    flags:     boolean mask, True for every transaction the rule flags
    """
    flagged = flags.sum()
    real_hits = (flags & (df["is_laundering"] == 1)).sum()
    hit_rate = real_hits / flagged
    catch_rate = real_hits / total_laundering

    print(f"\n{rule_name}")
    print("  Flagged transactions:", flagged)
    print("  Real laundering among them:", real_hits)
    print(f"  Hit rate:   {hit_rate:.2%}")
    print(f"  Catch rate: {catch_rate:.2%}")

    results.append({"rule": rule_name, "flagged": flagged, "real_hits": real_hits,
                    "hit_rate": hit_rate, "catch_rate": catch_rate})


# Rule 1: Structuring
# USD payments just below a 10,000 reporting threshold.
# Restricted to USD because amounts are not comparable across currencies.
is_usd = df["payment_currency"] == "US Dollar"
just_under_10k = (df["amount_paid"] >= 9000) & (df["amount_paid"] < 10000)

rule_structuring = is_usd & just_under_10k
evaluate("Rule 1: Structuring (9,000 to 9,999 USD)", rule_structuring)


# Rule 2: High daily activity
# Accounts sending an unusually high number of transactions in a single day.
df["date"] = df["timestamp"].dt.date

# Per-transaction value: the sending account's transaction count that day
tx_per_day = df.groupby(["from_account", "date"])[
    "from_account"].transform("count")

# Threshold is set on account-days, not transactions, so that a few
# very large accounts do not distort the 99th percentile.
daily_counts = df.groupby(["from_account", "date"]).size()
limit_activity = daily_counts.quantile(0.99)
print("\nRule 2 limit (top 1% busiest account-days):", limit_activity)

rule_activity = tx_per_day >= limit_activity
evaluate("Rule 2: High daily activity", rule_activity)


# Rule 3: Fan-out
# Accounts sending funds to an unusually large number of distinct receivers.
receivers_per_account = df.groupby("from_account")[
    "to_account"].transform("nunique")

# Threshold set per account (same reasoning as Rule 2)
receivers = df.groupby("from_account")["to_account"].nunique()
limit_fanout = receivers.quantile(0.99)
print("\nRule 3 limit (top 1% of accounts by number of receivers):", limit_fanout)

rule_fanout = receivers_per_account >= limit_fanout
evaluate("Rule 3: Fan-out", rule_fanout)


# Rule 4: All ACH payments (baseline)
# 01_data_quality.py showed ACH carries ~7x the average laundering rate.
is_ach = df["payment_format"] == "ACH"
evaluate("Rule 4: All ACH payments", is_ach)


# Rule 5: Fan-out on ACH payments
# Combines two weak signals to reduce alert volume and raise the hit rate,
# at the cost of a lower catch rate.
rule_fanout_ach = rule_fanout & is_ach
evaluate("Rule 5: Fan-out on ACH payments", rule_fanout_ach)


# Export results for Power BI
summary = pd.DataFrame(results)
summary.to_csv("output/rule_summary.csv", index=False)

alerts = df[rule_fanout_ach][["timestamp", "date", "from_account", "to_account",
                              "amount_paid", "payment_currency", "is_laundering"]]
alerts.to_csv("output/rule5_alerts.csv", index=False)

print("\nSaved output files.")
