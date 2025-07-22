import smtplib

def send_test_email():
    server = smtplib.SMTP("smtp.office365.com", 587)
    server.starttls()
    server.login("your_email@outlook.com", "your_password")
    message = "Subject: Test Email\n\nThis is a test email from EasyDay System."
    server.sendmail("your_email@outlook.com", "receiver_email@example.com", message)
    server.quit()
