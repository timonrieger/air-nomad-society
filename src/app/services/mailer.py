import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.app.config import Settings


def send_email(html: str, recipient: str, subject: str, settings: Settings) -> None:
    assert settings.smtp_server and settings.smtp_email and settings.smtp_pwd, (
        "SMTP is not configured"
    )
    message = MIMEMultipart()
    message["From"] = f"Air Nomad Society <{settings.smtp_email}>"
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host=settings.smtp_server, port=settings.smtp_port) as connection:
        connection.starttls()
        connection.login(user=settings.smtp_email, password=settings.smtp_pwd)
        connection.send_message(message)
