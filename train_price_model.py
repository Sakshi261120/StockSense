import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import sys
import datetime
import numpy as np

# --- Step 1: Load CSV file from argument ---
if len(sys.argv) < 2:
    print("❌ Please provide the CSV file path.")
    sys.exit()

file_path = sys.argv[1]
df = pd.read_csv(file_path)

# --- Step 2: Validate required columns ---
required = {"Quantity_Sold", "Revenue"}
missing = required - set(df.columns)
if missing:
    print(f"❌ Missing columns: {missing}")
    sys.exit()

# --- Step 3: Create 'Unit_Price' & Keep Product Name if present ---
df = df[df["Quantity_Sold"] != 0]
df["Unit_Price"] = df["Revenue"] / df["Quantity_Sold"]
df = df.replace([np.inf, -np.inf], pd.NA).dropna(subset=["Unit_Price"])

# Optional: Keep 'Product_Name' for later use
has_product_name = "Product_Name" in df.columns
if has_product_name:
    df = df[["Product_Name", "Quantity_Sold", "Unit_Price"]]
else:
    df = df[["Quantity_Sold", "Unit_Price"]]

# --- Step 4: Train Linear Regression Model ---
X = df[["Quantity_Sold"]]
y = df["Unit_Price"]
model = LinearRegression()
model.fit(X, y)

# --- Step 5: Save model with timestamp ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = f"price_model_{timestamp}.pkl"
joblib.dump(model, model_path)

# --- Step 6: Save processed training data (optional for inspection/prediction) ---
df.to_csv(f"training_data_{timestamp}.csv", index=False)

print(f"✅ Model trained and saved as {model_path}")
if has_product_name:
    print(f"🗂️ Product-linked training data saved as training_data_{timestamp}.csv")


