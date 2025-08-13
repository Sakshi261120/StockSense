# pos_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_pos_receipt(data, output_dir="receipts"):
    """
    Generates a PDF POS receipt from sales data.
    
    Parameters:
    - data: list of dicts containing 'Product_Name', 'Quantity_Sold', 'Unit_Price'
    - output_dir: folder to store the generated PDF receipt
    """

    # Ensure output folder exists
    os.makedirs(output_dir, exist_ok=True)

    # File name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_path = os.path.join(output_dir, f"receipt_{timestamp}.pdf")

    # Create PDF
    c = canvas.Canvas(receipt_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 750, "POS RECEIPT")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Table Header
    c.drawString(50, 700, "Product")
    c.drawString(250, 700, "Quantity")
    c.drawString(350, 700, "Unit Price")
    c.drawString(450, 700, "Total")

    y = 680
    total_amount = 0

    # Loop through products
    for item in data:
        product = item["Product_Name"]
        qty = int(item["Quantity_Sold"])
        price = float(item["Unit_Price"])
        total = qty * price
        total_amount += total

        c.drawString(50, y, str(product))
        c.drawString(250, y, str(qty))
        c.drawString(350, y, f"${price:.2f}")
        c.drawString(450, y, f"${total:.2f}")
        y -= 20

    # Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y - 10, "TOTAL:")
    c.drawString(450, y - 10, f"${total_amount:.2f}")

    c.showPage()
    c.save()

    return receipt_path

