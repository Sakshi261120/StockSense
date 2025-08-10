import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import requests
from sklearn.linear_model import LinearRegression
import joblib

# =================== CONFIG ===================
DB_PATH = "sales.db"
TABLE_NAME = "sales_table"

PUSHOVER_USER_KEY = "umqpi3kryezvwo9mjpqju5qc5j59kx"
PUSHOVER_API_TOKEN = "aue6x29a79caihi7pt4g27yoef4vv3"

REQUIRED_COLUMNS = [
    "Date", "Store_ID", "Product_Name", "Category", "Unit_Price",
    "Quantity_Sold", "Discount", "Revenue", "Stock_Remaining", "Expiry_Date"
]

# =================== DB FUNCTIONS ===================
def load_data_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM {TABLE_NAME};"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame()

# =================== ALERT FUNCTIONS ===================
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

def send_pushover_notification(user_key, api_token, message):
    url = "https://api.pushover.net/1/messages.json"
    data = {"token": api_token, "user": user_key, "message": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        st.error(f"Pushover error: {e}")

# =================== PAGE CONFIG ===================
st.set_page_config(page_title="StockSense - Retail Optimizer", layout="wide", page_icon="📊")
st.markdown("<style>.main{background-color:#f7f9fc;}</style>", unsafe_allow_html=True)
st.title("📊 StockSense - Retail Optimizer")

# =================== LOAD DATA WITH FALLBACK ===================
stock_threshold = st.sidebar.slider("Stock Alert Threshold", 1, 100, 20)
expiry_days = st.sidebar.slider("Expiry Alert Days", 1, 30, 7)

uploaded_file = st.file_uploader("Upload your sales data CSV file", type=["csv"])

data = pd.DataFrame()  # Initialize empty DataFrame

if uploaded_file is not None:
    try:
        temp_data = pd.read_csv(uploaded_file)
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in temp_data.columns]
        if missing_cols:
            st.error(f"❌ Uploaded CSV is missing required columns: {', '.join(missing_cols)}")
            st.info("Loading data from database as fallback...")
            data = load_data_from_db()
        else:
            st.success("✅ CSV file loaded successfully!")
            data = temp_data
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        st.info("Loading data from database as fallback...")
        data = load_data_from_db()
else:
    st.info("📂 No CSV uploaded, loading data from database...")
    data = load_data_from_db()

if data.empty:
    st.warning("⚠️ No data available from CSV or database.")
    st.stop()

# =================== PROCESS DATA ===================
data["Expiry_Date"] = pd.to_datetime(data["Expiry_Date"], errors="coerce")
today = pd.to_datetime(datetime.today().date())
data["Days_To_Expiry"] = (data["Expiry_Date"] - today).dt.days

stock_alerts = generate_stock_alerts(data, threshold=stock_threshold)
expiry_alerts = generate_expiry_alerts(data, days_threshold=expiry_days)
total_alerts_count = len(stock_alerts) + len(expiry_alerts)

# =================== SIDEBAR MENU ===================
menu_labels = [
    "Dashboard",
    "Price Optimization",
    "Stock Alerts",
    "Expiry Alerts",
    f"🔔 Notifications ({total_alerts_count})" if total_alerts_count > 0 else "🔔 Notifications",
    "Raw Data"
]
menu = st.sidebar.radio("Go to", menu_labels)
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by: **GROUP 1**")

# =================== DASHBOARD ===================
if menu == "Dashboard":
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

# =================== PRICE OPTIMIZATION ===================
elif menu == "Price Optimization":
    st.subheader("Train & Predict Prices")

    train_file = st.file_uploader("Upload training CSV (Quantity_Sold, Unit_Price)", type=["csv"], key="train")
    if train_file:
        try:
            df_train = pd.read_csv(train_file)
            if "Quantity_Sold" in df_train.columns and "Unit_Price" in df_train.columns:
                model = LinearRegression()
                model.fit(df_train[["Quantity_Sold"]], df_train["Unit_Price"])
                joblib.dump(model, "price_model.pkl")
                st.success("✅ Model trained and saved!")
            else:
                st.error("❌ CSV must contain Quantity_Sold and Unit_Price columns.")
        except Exception as e:
            st.error(f"Training failed: {e}")

    pred_file = st.file_uploader("Upload CSV to predict (Quantity_Sold)", type=["csv"], key="predict")
    if pred_file:
        try:
            model = joblib.load("price_model.pkl")
            df_pred = pd.read_csv(pred_file)
            if "Quantity_Sold" in df_pred.columns:
                df_pred["predicted_price"] = model.predict(df_pred[["Quantity_Sold"]]).round(2)
                st.dataframe(df_pred)
                st.download_button("Download Predictions", df_pred.to_csv(index=False), "predicted_prices.csv")
        except FileNotFoundError:
            st.info("No trained model found.")
        except Exception as e:
            st.error(f"Prediction failed: {e}")

# =================== STOCK ALERTS ===================
elif menu == "Stock Alerts":
    st.header("📦 Stock Alerts")
    low_stock = data[data["Stock_Remaining"] < stock_threshold]
    if low_stock.empty:
        st.success("🎉 All products well stocked.")
    else:
        st.warning(f"{len(low_stock)} products are below the threshold!")
        st.dataframe(low_stock[["Product_Name", "Stock_Remaining", "Quantity_Sold"]])

# =================== EXPIRY ALERTS ===================
elif menu == "Expiry Alerts":
    st.header("⏰ Expiry Alerts")
    expiring_soon = data[data["Days_To_Expiry"] <= expiry_days]
    if expiring_soon.empty:
        st.success("🎉 No products expiring soon.")
    else:
        st.warning(f"{len(expiring_soon)} products expiring soon!")
        st.dataframe(expiring_soon[["Product_Name", "Expiry_Date", "Days_To_Expiry", "Stock_Remaining"]])

# =================== NOTIFICATIONS ===================
elif menu.startswith("🔔 Notifications"):
    st.subheader("🔔 Notifications Center")
    for alert in stock_alerts:
        st.error(f"📦 {alert}")
        send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Stock Alert: {alert}")
    for alert in expiry_alerts:
        st.warning(f"⏰ {alert}")
        send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Expiry Alert: {alert}")
    if not stock_alerts and not expiry_alerts:
        st.success("✅ No active alerts.")

# =================== RAW DATA ===================
elif menu == "Raw Data":
    st.dataframe(data)
    st.download_button("Download CSV", data.to_csv(index=False), "sales_data.csv")











