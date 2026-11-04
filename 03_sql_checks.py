"""
03_sql_checks.py

Loads the cleaned data into a local SQLite database and runs the
queries in sql/red_flags.sql, as a cross-check of the pandas results.
"""

import sqlite3
import pandas as pd

# Load cleaned data and write it into a SQLite database file
df = pd.read_csv("data/transactions_clean.csv")
conn = sqlite3.connect("data/aml.db")
df.to_sql("transactions", conn, if_exists="replace", index=False)

# Read the SQL file and run each query (queries are separated by ;)
with open("sql/red_flags.sql") as f:
    queries = f.read().split(";")

for query in queries:
    if query.strip():
        print(pd.read_sql(query, conn))
        print()

# Save the payment format summary for Power BI
formats = pd.read_sql(queries[0], conn)
formats.to_csv("output/payment_format_summary.csv", index=False)

conn.close()
