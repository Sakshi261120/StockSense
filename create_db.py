import pandas as pd
import sqlite3

# Load CSV
df = pd.read_csv("easyday_sales_dataset.csv")

# Connect to SQLite (creates DB file)
conn = sqlite3.connect("retail_data.db")

# Write CSV to SQLite table
df.to_sql("sales_data", conn, if_exists="replace", index=False)

# Optional: Show preview rows
cursor = conn.cursor()
cursor.execute("SELECT * FROM sales_data LIMIT 5;")
print(cursor.fetchall())

conn.close()

