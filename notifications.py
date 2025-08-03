import pandas as pd
from datetime import datetime

def generate_stock_alerts(df, threshold=5):
    alerts = []
    for _, row in df.iterrows():
        if row['quantity'] < threshold:
            alerts.append({
                "type": "Stock Alert",
                "product": row['product_name'],
                "quantity": row['quantity'],
                "message": f"Only {row['quantity']} units left in stock."
            })
    return alerts

def generate_expiry_alerts(df):
    alerts = []
    today = datetime.today().date()
    for _, row in df.iterrows():
        expiry_date = pd.to_datetime(row['expiry_date']).date()
        if expiry_date < today:
            alerts.append({
                "type": "Expiry Alert",
                "product": row['product_name'],
                "expiry_date": expiry_date.strftime('%Y-%m-%d'),
                "message": f"Expired on {expiry_date}."
            })
    return alerts

def get_all_alerts(df, threshold=5):
    return generate_stock_alerts(df, threshold) + generate_expiry_alerts(df)

