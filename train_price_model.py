import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Load your dataset
df = pd.read_csv("easyday_sales_dataset.csv")
df["Unit_Price"] = df["Revenue"] / df["Quantity_Sold"]
df = df.dropna()

# Train the model
X = df[["Quantity_Sold"]]
y = df["Unit_Price"]
model = LinearRegression()
model.fit(X, y)

# Save the model
joblib.dump(model, "price_model.pkl")

print("✅ Model trained and saved as price_model.pkl")

