import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_reset_email(to_email: str, reset_url: str):
    smtp_server = os.getenv("MAIL_SERVER")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    from_addr = os.getenv("MAIL_FROM")

    if not all([smtp_server, username, password, from_addr]):
        print("Email configuration missing. Skipping email send.")
        return False

    subject = "SmartPesa – Password Reset Request"
    body = f"""
    <html>
    <body>
        <h2>Reset Your Password</h2>
        <p>You requested a password reset for your SmartPesa account. Click the link below to set a new password:</p>
        <a href="{reset_url}">{reset_url}</a>
        <p>This link will expire in 1 hour.</p>
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
