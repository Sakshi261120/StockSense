import smtplib
from email.message import EmailMessage

def send_low_stock_email(sender_email, app_password, recipient_email, csv_content, threshold, low_stock_count):
    """
    Send an email with low stock report attached as CSV.
    
    Parameters:
    - sender_email (str): Your Gmail address
    - app_password (str): Your 16-digit Gmail App Password
    - recipient_email (str): Email of the recipient
    - csv_content (str): CSV data as string
    - threshold (int): Stock threshold used
    - low_stock_count (int): Number of low stock items
    """

    msg = EmailMessage()
    msg['Subject'] = '⚠️ Low Stock Alert'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(f"""
Hi,

Please find attached the low stock report.

{low_stock_count} products are below the threshold of {threshold}.

Best,
StockSense App
    """)

    msg.add_attachment(csv_content, filename="low_stock_report.csv")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

