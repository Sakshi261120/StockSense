import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def load_data(db_path="retail_data.db"):
    try:
        conn = sqlite3.connect(db_path)
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

