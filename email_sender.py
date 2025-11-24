import smtplib
from email.mime.text import MIMEText
import os

def send_password_reset_email(email, code):
    from_addr = os.getenv("SMTP_USER")    # Set in your .env
    password = os.getenv("SMTP_PASS")     # Set in your .env
    smtp_host = os.getenv("SMTP_HOST")    # e.g., smtp.gmail.com
    smtp_port = int(os.getenv("SMTP_PORT", "465"))  # 465 for SSL

    to_addr = email
    subject = "Your Reedz Password Reset Code"
    message = f"Your Reedz password reset code is: {code}\n\nThis code will expire in 15 minutes."

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")
