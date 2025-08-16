import time
import random
import sqlite3
from datetime import datetime, timedelta

DB_FILE = "stocksense.db"  # Use the same DB your app uses

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_transaction():
    # Example products
    products = [
        {"name": "Milk", "price": 2.5},
        {"name": "Bread", "price": 1.8},
        {"name": "Eggs", "price": 3.0},
        {"name": "Juice", "price": 4.2}
    ]
    
    product = random.choice(products)
    qty = random.randint(1, 5)
    total = product["price"] * qty
    
    return {
        "product": product["name"],
        "quantity": qty,
        "price": product["price"],
        "total": total,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def save_transaction(txn):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into transactions table
    cursor.execute("""
        INSERT INTO sales (Product_Name, Quantity_Sold, Unit_Price, Revenue, Date)
        VALUES (?, ?, ?, ?, ?)
    """, (txn["product"], txn["quantity"], txn["price"], txn["total"], txn["time"]))

    # Update stock
    cursor.execute("""
        UPDATE inventory
        SET Stock_Remaining = Stock_Remaining - ?
        WHERE Product_Name = ?
    """, (txn["quantity"], txn["product"]))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚀 POS Simulator started... generating sales every 5 seconds")
    while True:
        txn = generate_transaction()
        save_transaction(txn)
        print(f"✅ New transaction: {txn}")
        time.sleep(5)  # wait 5 sec before next txn

