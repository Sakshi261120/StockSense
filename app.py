import streamlit as st
import os
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import requests
from sklearn.linear_model import LinearRegression
import joblib
from email.message import EmailMessage
import smtplib

# POS receipt integration
try:
    from pos_generator import generate_pos_receipt
    POS_AVAILABLE = True
except ModuleNotFoundError:
    POS_AVAILABLE = False

# ================= CONFIG =================
DB_PATH = os.path.abspath("retail_data.db")  # SQLite DB path

# Pushover API keys
PUSHOVER_USER_KEY = "umqpi3kryezvwo9mjpqju5qc5j59kx"
PUSHOVER_API_TOKEN = "aue6x29a79caihi7pt4g27yoef4vv3"

# ================= Helper Functions =================
def load_data():
    if not os.path.exists(DB_PATH):
        st.error(f"Database file not found at {DB_PATH}")
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM sales_data", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load data from DB: {e}")
        return pd.DataFrame()

def send_pushover_notification(user_key, api_token, message):
    url = "https://api.pushover.net/1/messages.json"
    data = {"token": api_token, "user": user_key, "message": message}
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Pushover notification failed: {e}")
        return False

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

# ================= Streamlit UI =================
st.set_page_config(page_title="StockSense - Retail Optimizer", layout="wide", page_icon="📊")
st.title("Welcome to StockSense")
st.write(f"Current working directory: {os.getcwd()}")

# ================= Load Data =================
uploaded_file = st.file_uploader("Upload your sales data CSV file", type=["csv"])
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    required_cols = ["Product_Name", "Revenue", "Quantity_Sold", "Stock_Remaining", "Unit_Price", "Expiry_Date"]
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        st.stop()
    data['Expiry_Date'] = pd.to_datetime(data['Expiry_Date'], errors='coerce')
else:
    data = load_data()
    if not data.empty:
        data['Expiry_Date'] = pd.to_datetime(data['Expiry_Date'], errors='coerce')

today = pd.to_datetime(datetime.today().date())
if not data.empty:
    data['Days_To_Expiry'] = (data['Expiry_Date'] - today).dt.days

# ================= Sidebar =================
st.sidebar.header("Settings")
stock_threshold = st.sidebar.slider("Stock Alert Threshold", 1, 100, 20)
expiry_days = st.sidebar.slider("Expiry Alert Days", 1, 30, 7)

# --- Real-Time Sale Demo ---
st.sidebar.markdown("## 🛒 Real-Time Sale ")
if not data.empty:
    product_list = data["Product_Name"].unique().tolist()
    sold_product = st.sidebar.selectbox("Select Product Sold", product_list)
    sold_qty = st.sidebar.number_input("Quantity Sold", min_value=1, max_value=100, value=1)
    if st.sidebar.button("Complete Sale"):
        idx = data[data["Product_Name"] == sold_product].index[0]
        data.at[idx, "Quantity_Sold"] += sold_qty
        data.at[idx, "Stock_Remaining"] -= sold_qty
        data.at[idx, "Revenue"] += data.at[idx, "Unit_Price"] * sold_qty
        data['Days_To_Expiry'] = (data['Expiry_Date'] - today).dt.days
        st.sidebar.success(f"Sale completed: {sold_qty} x {sold_product}")

        # Generate POS receipt only for this transaction
        if POS_AVAILABLE:
            sale_record = [{
                "Product_Name": sold_product,
                "Quantity_Sold": sold_qty,
                "Unit_Price": data.at[idx, "Unit_Price"],
                "Revenue": data.at[idx, "Unit_Price"] * sold_qty
            }]
            receipt_path = generate_pos_receipt(sale_record)
            st.sidebar.success("POS receipt generated!")
            st.session_state['latest_receipt'] = receipt_path

# ================= Alerts =================
stock_alerts = generate_stock_alerts(data, stock_threshold) if not data.empty else []
expiry_alerts = generate_expiry_alerts(data, expiry_days) if not data.empty else []

# ================= Navigation =================
menu_items = ["Dashboard", "Price Optimization", "Stock Alerts", "Expiry Alerts", "Raw Data"]
if POS_AVAILABLE:
    menu_items.append("🧾 POS Receipts")
menu_items.append(f"🔔 Notifications ({len(stock_alerts) + len(expiry_alerts)})")
menu = st.sidebar.radio("📌 Navigation", menu_items)

st.sidebar.markdown("---")
st.sidebar.markdown("Developed by: **GROUP 1**")

# ================= Dashboard =================
if menu == "Dashboard":
    if data.empty:
        st.warning("No data to display")
    else:
        st.subheader("💹 Dashboard Overview")
        total_revenue = data["Revenue"].sum()
        total_items = data["Quantity_Sold"].sum()
        unique_products = data["Product_Name"].nunique()
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
        col2.metric("🛒 Items Sold", total_items)
        col3.metric("📦 Unique Products", unique_products)

        top_products = data.groupby("Product_Name")["Revenue"].sum().sort_values(ascending=False).head(10)
        fig = px.bar(top_products, x=top_products.index, y=top_products.values,
                     labels={"x": "Product", "y": "Revenue (₹)"},
                     title="💰 Top 10 Products by Revenue",
                     color_discrete_sequence=["#3498db"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

# ================= Price Optimization =================
elif menu == "Price Optimization":
    st.subheader("🔧 Train Model & 📊 Predict Prices")
    train_file = st.file_uploader("Upload CSV for training", type=["csv"], key="train")
    if train_file:
        df_train = pd.read_csv(train_file)
        if "Quantity_Sold" in df_train.columns and "Unit_Price" in df_train.columns:
            X = df_train[["Quantity_Sold"]]
            y = df_train["Unit_Price"]
            model = LinearRegression()
            model.fit(X, y)
            joblib.dump(model, "price_model.pkl")
            st.success("Model trained and saved as 'price_model.pkl'")
    pred_file = st.file_uploader("Upload CSV for prediction", type=["csv"], key="predict")
    if pred_file:
        model = joblib.load("price_model.pkl")
        df_pred = pd.read_csv(pred_file)
        if "Quantity_Sold" in df_pred.columns:
            df_pred["Predicted_Price"] = model.predict(df_pred[["Quantity_Sold"]]).round(2)
            st.dataframe(df_pred)
            csv_data = df_pred.to_csv(index=False).encode("utf-8")
            st.download_button("Download Predictions CSV", csv_data, "predictions.csv", "text/csv")

# ================= Stock Alerts =================
elif menu == "Stock Alerts":
    st.header("Stock Refill Alerts")
    if data.empty:
        st.warning("No data to analyze")
    else:
        low_stock = data[data["Stock_Remaining"] < stock_threshold]
        if low_stock.empty:
            st.success("All products are well stocked")
        else:
            st.warning(f"{len(low_stock)} products below threshold")
            st.dataframe(low_stock[["Product_Name", "Stock_Remaining", "Quantity_Sold"]])
            csv_low_stock = low_stock.to_csv(index=False).encode("utf-8")
            st.download_button("Download Low Stock Report", csv_low_stock, "low_stock.csv", "text/csv")

# ================= Expiry Alerts =================
elif menu == "Expiry Alerts":
    st.header("Expiry Date Alerts")
    if data.empty:
        st.warning("No data to analyze")
    else:
        expiring_soon = data[data["Days_To_Expiry"] <= expiry_days]
        if expiring_soon.empty:
            st.success(f"No products expiring in next {expiry_days} days")
        else:
            st.warning(f"{len(expiring_soon)} products expiring soon")
            st.dataframe(expiring_soon[["Product_Name", "Expiry_Date", "Days_To_Expiry", "Stock_Remaining"]])
            csv_expiry = expiring_soon.to_csv(index=False).encode("utf-8")
            st.download_button("Download Expiry Report", csv_expiry, "expiry_report.csv", "text/csv")

# ================= Notifications =================
elif menu.startswith("🔔 Notifications"):
    st.header("Notifications Center")
    if stock_alerts:
        st.subheader("Stock Alerts")
        for alert in stock_alerts:
            st.error(alert)
            send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Stock Alert: {alert}")

    if expiry_alerts:
        st.subheader("Expiry Alerts")
        for alert in expiry_alerts:
            st.warning(alert)
            send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Expiry Alert: {alert}")

# ================= Raw Data =================
elif menu == "Raw Data":
    st.header("Raw Dataset")
    if data.empty:
        st.warning("No data loaded")
    else:
        st.dataframe(data)
        csv_raw = data.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv_raw, "sales_data.csv", "text/csv")

# ================= POS Receipts =================
elif menu == "🧾 POS Receipts":
    st.header("POS Receipt Generation")
    if not POS_AVAILABLE:
        st.error("POS feature unavailable. Install 'reportlab'.")
    elif data.empty:
        st.warning("No data available")
    else:
        st.subheader("Preview Sales Data")
        st.dataframe(data[["Product_Name", "Quantity_Sold", "Unit_Price"]])
        if 'latest_receipt' in st.session_state:
            receipt_path = st.session_state['latest_receipt']
            st.success(f"Latest POS receipt: {receipt_path}")
            with open(receipt_path, "rb") as f:
                st.download_button("Download Receipt", f, file_name=os.path.basename(receipt_path))
        else:
            if st.button("Generate Full POS Receipt"):
                receipt_path = generate_pos_receipt(data.to_dict(orient="records"))
                st.session_state['latest_receipt'] = receipt_path
                st.success(f"Receipt generated: {receipt_path}")
                with open(receipt_path, "rb") as f:
                    st.download_button("Download Receipt", f, file_name=os.path.basename(receipt_path))

# ================= Footer =================
st.markdown("---")
st.markdown("<div style='text-align: center;'>Made with ❤️ using Streamlit | Project: MSIT405</div>", unsafe_allow_html=True)











