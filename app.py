import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

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
    df = pd.read_csv("easyday_sales_dataset.csv")  # Ensure CSV is in the same folder
    df["Date"] = pd.to_datetime(df["Date"])
    df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"])
    df["Days_To_Expiry"] = (df["Expiry_Date"] - pd.to_datetime("today")).dt.days
    return df

data = load_data()

if menu == "Dashboard":
    st.header("📊 Retail Sales Dashboard")
    st.markdown(
        """
        This dashboard shows key metrics on total revenue, units sold, and product variety.  
        Explore the top-selling products by revenue below.
        """
    )
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
    fig.update_layout(xaxis_tickangle=-45)  # Tilt x-axis labels for readability
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Price Optimization":
    st.header("💸 Price Optimization (Coming Soon)")
    st.write("This section will have ML-based price suggestions soon.")

elif menu == "Stock Alerts":
    st.header("📦 Stock Refill Alerts")
    threshold = st.slider("Set stock threshold", 0, 100, 20)
    low_stock = data[data["Stock_Remaining"] < threshold]
    st.dataframe(low_stock[["Product_Name", "Stock_Remaining", "Quantity_Sold"]])

elif menu == "Expiry Alerts":
    st.header("⏰ Expiry Date Alerts")
    days = st.slider("Days to expiry", 1, 30, 7)
    expiring_soon = data[data["Days_To_Expiry"] <= days]
    st.dataframe(expiring_soon[["Product_Name", "Expiry_Date", "Days_To_Expiry", "Stock_Remaining"]])

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
