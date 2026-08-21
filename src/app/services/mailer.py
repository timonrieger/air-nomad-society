import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.app.config import Settings


def send_email(
    html: str,
    recipient: str,
    subject: str,
    settings: Settings,
    unsubscribe_url: str | None = None,
) -> None:
    message = MIMEMultipart()
    message["From"] = f"Air Nomad Society <{settings.smtp_email}>"
    message["To"] = recipient
    message["Subject"] = subject
    # RFC 8058: the pair puts an Unsubscribe button in the mail client's own
    # UI and tells it to POST, which is why the endpoint takes POST. Only
    # bulk mail carries them — a confirmation email has nothing to leave.
    if unsubscribe_url:
        message["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        message["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    message.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host=settings.smtp_server, port=settings.smtp_port) as connection:
        connection.starttls()
        connection.login(user=settings.smtp_email, password=settings.smtp_pwd)
        connection.send_message(message)
