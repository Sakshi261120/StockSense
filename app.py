import streamlit as st
import os
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import requests
from sklearn.linear_model import LinearRegression
import joblib
import smtplib
from email.message import EmailMessage

# =================== CONFIG ===================
DB_PATH = "retail_data.db"  # <-- Change this to your actual SQLite DB filename
DB_TABLE = "sales_table"     # <-- Change this if your table name differs

PUSHOVER_USER_KEY = "umqpi3kryezvwo9mjpqju5qc5j59kx"
PUSHOVER_API_TOKEN = "aue6x29a79caihi7pt4g27yoef4vv3"

# =================== DATABASE LOADER ===================
def load_data():
    if not os.path.exists(DB_PATH):
        st.error(f"❌ Database file '{DB_PATH}' does not exist!")
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        if DB_TABLE not in tables:
            st.error(f"❌ Table '{DB_TABLE}' does not exist in database '{DB_PATH}'. Available tables: {tables}")
            conn.close()
            return pd.DataFrame()

        query = f"SELECT * FROM {DB_TABLE}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Could not load data from database: {e}")
        return pd.DataFrame()

# =================== NOTIFICATIONS ===================
def send_pushover_notification(user_key, api_token, message):
    url = "https://api.pushover.net/1/messages.json"
    data = {"token": api_token, "user": user_key, "message": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        st.error(f"Pushover notification failed: {e}")

def generate_stock_alerts(df, threshold=5):
    alerts = []
    for _, row in df.iterrows():
        if row.get("Stock_Remaining", 0) < threshold:
            alerts.append(f"{row['Product_Name']} is low in stock ({row['Stock_Remaining']} units left). Please refill.")
    return alerts

def generate_expiry_alerts(df, days_threshold=7):
    alerts = []
    today = datetime.today()
    for _, row in df.iterrows():
        expiry_str = row.get("Expiry_Date")
        if pd.isna(expiry_str):
            continue
        try:
            expiry = pd.to_datetime(expiry_str)
        except Exception:
            continue
        days_left = (expiry - today).days
        if 0 <= days_left <= days_threshold:
            alerts.append(f"{row['Product_Name']} is expiring in {days_left} day(s).")
    return alerts

# =================== PAGE CONFIG ===================
st.set_page_config(page_title="StockSense - Retail Optimizer", layout="wide", page_icon="📊")
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    h1 { color: #2c3e50; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("Welcome to StockSense")
st.write("Current working directory:", os.getcwd())

# =================== CSV Loader with cache ===================
@st.cache_data
def load_csv(file):
    file.seek(0)
    return pd.read_csv(file, encoding='utf-8')

# =================== SETTINGS ===================
stock_threshold = 20
expiry_days = 7

# =================== LOAD DATA ===================
uploaded_file = st.file_uploader("Upload your sales data CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        data = load_csv(uploaded_file)
        st.write(f"✅ Loaded {len(data)} rows and {len(data.columns)} columns")

        required_cols = ["Product_Name", "Revenue", "Quantity_Sold", "Stock_Remaining", "Expiry_Date"]
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            st.error(f"❌ Uploaded CSV is missing required columns: {', '.join(missing_cols)}")
            st.stop()  # Stop here, no DB fallback

        data['Expiry_Date'] = pd.to_datetime(data['Expiry_Date'], errors='coerce')
        today = pd.to_datetime(datetime.today().date())
        data['Days_To_Expiry'] = (data['Expiry_Date'] - today).dt.days

        if data.empty:
            st.warning("⚠️ Uploaded file is empty.")
            st.stop()

        st.success("✅ File uploaded and processed successfully!")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

else:
    st.info("📂 No CSV uploaded, loading data from database...")
    data = load_data()
    if data.empty:
        st.warning("⚠️ No data available from database.")
        data = pd.DataFrame(columns=["Product_Name", "Revenue", "Quantity_Sold", "Stock_Remaining", "Expiry_Date", "Days_To_Expiry"])
    else:
        data['Expiry_Date'] = pd.to_datetime(data['Expiry_Date'], errors='coerce')
        today = pd.to_datetime(datetime.today().date())
        data['Days_To_Expiry'] = (data['Expiry_Date'] - today).dt.days
        st.info(f"ℹ️ Loaded {len(data)} rows from database.")

# Place sliders AFTER data load so user can adjust thresholds dynamically
stock_threshold = st.sidebar.slider("Stock Alert Threshold", 1, 100, stock_threshold)
expiry_days = st.sidebar.slider("Expiry Alert Days", 1, 30, expiry_days)

# Generate alerts
stock_alerts = generate_stock_alerts(data, threshold=stock_threshold)
expiry_alerts = generate_expiry_alerts(data_













