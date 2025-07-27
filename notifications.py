import pandas as pd
from datetime import datetime

def generate_stock_alerts(df, threshold=5):
    alerts = []
    for _, row in df.iterrows():
        if row['quantity'] < threshold:
            alerts.append(f"Restock {row['product_name']} – only {row['quantity']} left.")
    return alerts

def generate_expiry_alerts(df):
    alerts = []
    today = datetime.today().date()
    for _, row in df.iterrows():
        expiry_date = pd.to_datetime(row['expiry_date']).date()
        if expiry_date < today:
            alerts.append(f"Remove {row['product_name']} – expired on {expiry_date}.")
    return alerts

