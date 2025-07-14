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
    st.header("💸 Price Optimization")

    st.markdown("Upload your sales data CSV with columns: **Revenue** and **Quantity_Sold** to get price suggestions.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        data_uploaded = pd.read_csv(uploaded_file)

        # Validate required columns
        if not {'Revenue', 'Quantity_Sold'}.issubset(data_uploaded.columns):
            st.error("CSV must contain 'Revenue' and 'Quantity_Sold' columns.")
        else:
            data_uploaded["Unit_Price"] = data_uploaded["Revenue"] / data_uploaded["Quantity_Sold"]
            data_uploaded = data_uploaded.dropna()

            X = data_uploaded["Quantity_Sold"].values.reshape(-1, 1)
            y = data_uploaded["Unit_Price"].values

            model = LinearRegression()
            model.fit(X, y)

            st.subheader("📊 Predict Optimal Price")
            quantity = st.slider("Expected Quantity to Sell", 1, 1000, 100)

            predicted_price = model.predict(np.array([[quantity]]))[0]
            predicted_price = round(predicted_price, 2)

            st.success(f"💰 Suggested Unit Price: ₹{predicted_price}")

    else:
        st.info("Please upload your sales data CSV file to see price suggestions.")



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

