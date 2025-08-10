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
DB_PATH = "reatil_data.db"  # path to your SQLite database

PUSHOVER_USER_KEY = "umqpi3kryezvwo9mjpqju5qc5j59kx"
PUSHOVER_API_TOKEN = "aue6x29a79caihi7pt4g27yoef4vv3"

# =================== DATABASE LOADER ===================
def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM sales_table"
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
expiry_alerts = generate_expiry_alerts(data, days_threshold=expiry_days)
total_alerts_count = len(stock_alerts) + len(expiry_alerts)

# =================== SIDEBAR MENU ===================
menu_labels = [
    "Dashboard",
    "Price Optimization",
    "Stock Alerts",
    "Expiry Alerts",
    "Raw Data",
    f"🔔 Notifications ({total_alerts_count})" if total_alerts_count > 0 else "🔔 Notifications"
]

st.sidebar.markdown("## 📌 Navigation")
menu = st.sidebar.radio("Go to", menu_labels)
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by: **GROUP 1**")

# =================== PAGES ===================
if menu == "Dashboard":
    if data.empty:
        st.warning("⚠️ No data available to display. Please check your data source.")
    else:
        total_revenue = data["Revenue"].sum()
        total_items = data["Quantity_Sold"].sum()
        unique_products = data["Product_Name"].nunique()

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
        col2.metric("🛒 Items Sold", total_items)
        col3.metric("📦 Unique Products", unique_products)

        top_products = data.groupby("Product_Name")["Revenue"].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            top_products,
            x=top_products.index,
            y=top_products.values,
            labels={"x": "Product", "y": "Revenue (₹)"},
            title="💰 Top 10 Products by Revenue",
            color_discrete_sequence=["#3498db"]
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

elif menu == "Price Optimization":
    st.subheader("🔧 Train Model & 📊 Predict Prices (End-to-End ML)")

    train_file = st.file_uploader("📁 Upload CSV to train model (must have 'Quantity_Sold' and 'Unit_Price')", type=["csv"], key="train")

    if train_file is not None:
        try:
            df_train = pd.read_csv(train_file)
            if "Quantity_Sold" in df_train.columns and "Unit_Price" in df_train.columns:
                X = df_train[["Quantity_Sold"]]
                y = df_train["Unit_Price"]
                model = LinearRegression()
                model.fit(X, y)
                joblib.dump(model, "price_model.pkl")
                st.success("✅ Model trained and saved as 'price_model.pkl'")
            else:
                st.error("❌ CSV must contain both 'Quantity_Sold' and 'Unit_Price' columns.")
        except Exception as e:
            st.error(f"❌ Training failed: {e}")

    pred_file = st.file_uploader("📁 Upload CSV with 'Quantity_Sold' to predict price", type=["csv"], key="predict")

    try:
        model = joblib.load("price_model.pkl")
        if pred_file is not None:
            df_pred = pd.read_csv(pred_file)
            if "Quantity_Sold" in df_pred.columns:
                df_pred["predicted_price"] = model.predict(df_pred[["Quantity_Sold"]]).round(2)
                st.success("✅ Predictions generated:")
                st.dataframe(df_pred)
                csv = df_pred.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Results as CSV", data=csv, file_name="predicted_prices.csv", mime="text/csv")
            else:
                st.error("❌ The uploaded CSV must contain a 'Quantity_Sold' column.")
    except FileNotFoundError:
        st.info("ℹ️ No trained model found yet. Please upload training data above first.")
    except Exception as e:
        st.error(f"❌ Prediction failed: {e}")

elif menu == "Stock Alerts":
    st.header("📦 Stock Refill Alerts")
    threshold = st.slider("Set stock threshold", 0, 100, stock_threshold)
    low_stock = data[data["Stock_Remaining"] < threshold]

    if low_stock.empty:
        st.success("🎉 All products are well stocked.")
    else:
        st.warning(f"⚠️ {len(low_stock)} products are below the stock threshold of {threshold}. Please consider restocking.")
        st.dataframe(low_stock[["Product_Name", "Stock_Remaining", "Quantity_Sold"]])

        csv_low_stock = low_stock.to_csv(index=False)
        st.download_button("📥 Download Low Stock Report", data=csv_low_stock, file_name="low_stock_report.csv", mime="text/csv")

        st.subheader("📧 Send Low Stock Report to Email")
        recipient = st.text_input("Enter recipient email address")
        send_email = st.button("Send Email")

        if send_email:
            if recipient:
                try:
                    gmail_user = '6120sakshi@gmail.com'
                    gmail_password = 'scnbsvbajhaltwus'  # Your app password here

                    msg = EmailMessage()
                    msg['Subject'] = '⚠️ Low Stock Alert'
                    msg['From'] = gmail_user
                    msg['To'] = recipient
                    msg.set_content(f"""
Hi,

Please find attached the low stock report.

{len(low_stock)} products are below the threshold of {threshold}.

Best,
StockSense App
                    """)

                    msg.add_attachment(csv_low_stock, filename="low_stock_report.csv")

                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(gmail_user, gmail_password)
                        smtp.send_message(msg)

                    st.success("✅ Email sent successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to send email: {e}")
            else:
                st.warning("⚠️ Please enter a valid recipient email address.")

elif menu == "Expiry Alerts":
    st.header("⏰ Expiry Date Alerts")
    days = st.slider("Days to expiry", 1, 30, expiry_days)
    expiring_soon = data[data["Days_To_Expiry"] <= days]

    if expiring_soon.empty:
        st.success(f"🎉 No products expiring in the next {days} days.")
    else:
        st.warning(f"⚠️ {len(expiring_soon)} products expiring in the next {days} days!")
        st.dataframe(expiring_soon[["Product_Name", "Expiry_Date", "Days_To_Expiry", "Stock_Remaining"]])

        csv_expiry = expiring_soon.to_csv(index=False)
        st.download_button("📥 Download Expiry Report", data=csv_expiry, file_name="expiry_report.csv", mime="text/csv")

elif menu.startswith("🔔 Notifications"):
    st.subheader("🔔 Notifications Center")

    if data is not None and not data.empty:
        if not all(col in data.columns for col in ["Product_Name", "Stock_Remaining", "Expiry_Date"]):
            st.error("Data is missing required columns for alerts.")
        else:
            # Generate alerts
            stock_alerts = generate_stock_alerts(data, threshold=stock_threshold)
            expiry_alerts = generate_expiry_alerts(data, days_threshold=expiry_days)

            for alert in stock_alerts:
                st.error(f"📦 {alert}")
                send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Stock Alert: {alert}")

            for alert in expiry_alerts:
                st.warning(f"⏰ {alert}")
                send_pushover_notification(PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, f"Expiry Alert: {alert}")

            total_alerts = len(stock_alerts) + len(expiry_alerts)

            if total_alerts == 0:
                st.success("✅ No active alerts. All inventory looks good.")
    else:
        st.warning("⚠️ Please upload or load data to view alerts.")

elif menu == "Raw Data":
    st.header("📋 Raw Dataset")
    st.dataframe(data)
    csv = data.to_csv(index=False)
    st.download_button("Download CSV", csv, "sales_data.csv")

# =================== FOOTER ===================
st.markdown("---")
st.markdown("<div style='text-align: center;'>Made with ❤️ using Streamlit | Project: MSIT405</div>", unsafe_allow_html=True)













