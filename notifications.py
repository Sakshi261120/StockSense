import pandas as pd
from datetime import datetime

def generate_stock_alerts(df, threshold=5):
    alerts = []
    for _, row in df.iterrows():
        if row['Stock_Remaining'] < threshold:
            alerts.append(f"Only {row['Stock_Remaining']} units left of {row['Product_Name']}.")
    return alerts

def generate_expiry_alerts(df, days_threshold=7):
    alerts = []
    today = datetime.today().date()
    for _, row in df.iterrows():
        expiry_date = pd.to_datetime(row['Expiry_Date']).date()
        days_to_expiry = (expiry_date - today).days
        if days_to_expiry <= days_threshold:
            if days_to_expiry < 0:
                alerts.append(f"{row['Product_Name']} expired on {expiry_date}.")
            else:
                alerts.append(f"{row['Product_Name']} expires in {days_to_expiry} day(s) on {expiry_date}.")
    return alerts

def get_all_alerts(df, stock_threshold=5, expiry_days=7):
    return generate_stock_alerts(df, stock_threshold) + generate_expiry_alerts(df, expiry_days)


