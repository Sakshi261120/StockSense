import streamlit as st
import os
import pandas as pd
import sqlite3  # <-- Add this here!
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# -------------------- Step 1: Page Configuration and Styling --------------------
st.set_page_config(
    page_title="StockSense - Retail Optimizer",
    layout="wide",
    page_icon="📊"
)

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9fc;
    }
    h1 {
        color: #2c3e50;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Step 2: Sidebar Navigation --------------------
st.sidebar.markdown("## 📌 Navigation")
menu = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Price Optimization", "Stock Alerts", "Expiry Alerts", "Raw Data"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by: **Garima**")

# -------------------- Main App --------------------
st.write("Current working directory:", os.getcwd())
st.title("Welcome to StockSense")

@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect("retail_data.db")
        df = pd.read_sql_query("SELECT * FROM sales_data", conn)
        conn.close()

        # Process date columns
        df["Date"] = pd.to_datetime(df["Date"])
        df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"])
        df["Days_To_Expiry"] = (df["Expiry_Date"] - pd.to_datetime("today")).dt.days
        return df

    except Exception as e:
        st.error(f"Error loading data from DB: {e}")
        return pd.DataFrame()  # Return empty DataFrame if error
        
data = load_data()

if menu == "Dashboard":
    if data.empty:
        st.warning("⚠️ No data available to display. Please check database connection or data source.")
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
    # price optimization logic...


elif menu == "Price Optimization":
    st.subheader("🔧 Train Model & 📊 Predict Prices (End-to-End ML)")

    # Section 1: Train the ML Model
    st.markdown("### 🔧 Step 1: Train Price Model")
    train_file = st.file_uploader("📁 Upload CSV to train model (must have 'quantity' and 'price')", type=["csv"], key="train")

    if train_file is not None:
        import pandas as pd
        import numpy as np
        from sklearn.linear_model import LinearRegression
        import joblib

        try:
            df_train = pd.read_csv(train_file)

            if "quantity" in df_train.columns and "price" in df_train.columns:
                X = df_train[["quantity"]]
                y = df_train["price"]

                # Train model
                model = LinearRegression()
                model.fit(X, y)

                # Save model
                joblib.dump(model, "price_model.pkl")
                st.success("✅ Model trained and saved as 'price_model.pkl'")
            else:
                st.error("❌ CSV must contain both 'quantity' and 'price' columns.")
        except Exception as e:
            st.error(f"❌ Training failed: {e}")

    # Section 2: Predict using trained model
    st.markdown("### 📊 Step 2: Predict Optimal Prices")
    pred_file = st.file_uploader("📁 Upload CSV with 'quantity' to predict price", type=["csv"], key="predict")

    try:
        import joblib
        model = joblib.load("price_model.pkl")

        if pred_file is not None:
            df_pred = pd.read_csv(pred_file)

            if "quantity" in df_pred.columns:
                df_pred["predicted_price"] = model.predict(df_pred[["quantity"]])
                df_pred["predicted_price"] = df_pred["predicted_price"].round(2)

                st.success("✅ Predictions generated:")
                st.dataframe(df_pred)

                csv = df_pred.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Results as CSV", data=csv, file_name="predicted_prices.csv", mime="text/csv")
            else:
                st.error("❌ The uploaded CSV must contain a 'quantity' column.")
    except FileNotFoundError:
        st.info("ℹ️ No trained model found yet. Please upload training data above first.")
    except Exception as e:
        st.error(f"❌ Prediction failed: {e}")





elif menu == "Stock Alerts":
    st.header("📦 Stock Refill Alerts")
    threshold = st.slider("Set stock threshold", 0, 100, 20)
    low_stock = data[data["Stock_Remaining"] < threshold]

    if low_stock.empty:
        st.success("🎉 All products are well stocked.")
    else:
        st.warning(f"⚠️ {len(low_stock)} products are below the stock threshold of {threshold}. Please consider restocking.")
        st.dataframe(low_stock[["Product_Name", "Stock_Remaining", "Quantity_Sold"]])

        csv_low_stock = low_stock.to_csv(index=False)
        st.download_button(
            label="📥 Download Low Stock Report",
            data=csv_low_stock,
            file_name="low_stock_report.csv",
            mime="text/csv"
        )

        # ----------- Email Sending Section ------------
        st.subheader("📧 Send Low Stock Report to Email")
        recipient = st.text_input("Enter recipient email address")
        send_email = st.button("Send Email")

        if send_email:
            if recipient:
                try:
                    import smtplib
                    from email.message import EmailMessage

                    gmail_user = '6120sakshi@gmail.com'
                    gmail_password = 'scnbsvbajhaltwus'  # Paste your App Password here (no spaces)

                    # Create email
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

                    # Add CSV as attachment
                    msg.add_attachment(csv_low_stock, filename="low_stock_report.csv")

                    # Send
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
    days = st.slider("Days to expiry", 1, 30, 7)
    expiring_soon = data[data["Days_To_Expiry"] <= days]

    if expiring_soon.empty:
        st.success(f"🎉 No products expiring in the next {days} days.")
    else:
        st.warning(f"⚠️ {len(expiring_soon)} products expiring in the next {days} days!")
        st.dataframe(expiring_soon[["Product_Name", "Expiry_Date", "Days_To_Expiry", "Stock_Remaining"]])

        csv_expiry = expiring_soon.to_csv(index=False)
        st.download_button(
            label="📥 Download Expiry Report",
            data=csv_expiry,
            file_name="expiry_report.csv",
            mime="text/csv"
        )
elif menu == "Raw Data":
    st.header("📋 Raw Dataset")
    st.dataframe(data)
    csv = data.to_csv(index=False)
    st.download_button("Download CSV", csv, "easyday_sales_dataset.csv")

# -------------------- Footer --------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center;'>Made with ❤️ using Streamlit | Project: MSIT405</div>",
    unsafe_allow_html=True,
)

