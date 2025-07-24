import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import sys
import datetime

# Check for argument
if len(sys.argv) < 2:
    print("❌ Please provide the CSV file path.")
    sys.exit()

file_path = sys.argv[1]
df = pd.read_csv(file_path)

# Validate required columns
required = {"Quantity_Sold", "Revenue"}
if not required.issubset(df.columns):
    print(f"❌ Missing columns: {required - set(df.columns)}")
    sys.exit()

# Preprocess
df = df[df["Quantity_Sold"] != 0]
df["Unit_Price"] = df["Revenue"] / df["Quantity_Sold"]
df = df.dropna(subset=["Unit_Price"])

# Train
X = df[["Quantity_Sold"]]
y = df["Unit_Price"]
model = LinearRegression()
model.fit(X, y)

# Save
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = f"price_model_{timestamp}.pkl"
joblib.dump(model, model_path)

print(f"✅ Model trained and saved as {model_path}")


