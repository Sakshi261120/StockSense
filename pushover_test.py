# stock_alerts.py

import pandas as pd
import requests
import os
from datetime import datetime

def send_pushover_notification(message):
    response = requests.post("https://api.pushover.net/1/messages.json", data={
        "token": "aue6x29a79caihi7pt4g27yoef4vv3",
        "user": "umqpi3kryezvwo9mjpqju5qc5j59kx",
        "message": message
    })
    print(response.status_code, response.text)

def generate_stock_alerts(df, threshold=5):
    for _, row in df.iterrows():
        if row['quantity'] < threshold:
            msg = f"Restock alert: Only {row['quantity']} units left of {row['product_name']}!"
            send_pushover_notification(msg)

def generate_expiry_alerts(df):
    for _, row in df.iterrows():
        expiry_date = pd.to_datetime(row['expiry_date'])
        if expiry_date <= pd.Timestamp.now():
            msg = f"Expiry alert: {row['product_name']} expired on {row['expiry_date']}"
            send_pushover_notification(msg)

# Sample data to test
data = [
    {"product_name": "Milk", "quantity": 2, "expiry_date": "2025-08-01"},
    {"product_name": "Bread", "quantity": 10, "expiry_date": "2025-08-20"},
    {"product_name": "Eggs", "quantity": 1, "expiry_date": "2025-07-30"},
]
df = pd.DataFrame(data)

generate_stock_alerts(df)
generate_expiry_alerts(df)
