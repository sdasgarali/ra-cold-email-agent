"""SMTP email sending adapter."""
from typing import List, Dict, Any, Optional
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from app.services.adapters.base import EmailSendAdapter
from app.core.config import settings


class SMTPAdapter(EmailSendAdapter):
    """Adapter for sending emails via SMTP."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD

    def test_connection(self) -> bool:
        """Test SMTP connection."""
        if not all([self.host, self.user, self.password]):
            return False

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                return True
        except Exception:
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a single email via SMTP."""
        if not all([self.host, self.user, self.password]):
            return {
                "success": False,
                "message_id": None,
                "error": "SMTP not configured"
            }

        message_id = f"{uuid.uuid4()}@{self.host}"

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{self.user}>" if from_name else self.user
            msg["To"] = to_email
            msg["Message-ID"] = f"<{message_id}>"

            # Add body parts
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            # Send
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            return {
                "success": True,
                "message_id": message_id,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "message_id": None,
                "error": str(e)
            }

    def send_bulk(
        self,
        messages: List[Dict[str, Any]],
        rate_limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Send multiple emails with rate limiting."""
        results = []
        delay = 60.0 / rate_limit

        for i, msg in enumerate(messages):
            if i > 0:
                time.sleep(delay)

            result = self.send_email(
                to_email=msg["to_email"],
                subject=msg["subject"],
                body_html=msg["body_html"],
                body_text=msg.get("body_text"),
                from_name=msg.get("from_name")
            )
            results.append(result)

        return results
