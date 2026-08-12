"""Minimal SMTP adapter for account-verification and password-reset mail."""

import smtplib
from email.message import EmailMessage

from app.core.config import settings


class AuthEmailService:
    @staticmethod
    def send(to_email: str, subject: str, body: str) -> bool:
        """Send a security email when SMTP is configured; never log token contents."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return False

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
