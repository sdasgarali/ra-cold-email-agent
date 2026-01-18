"""Mock email sending adapter for testing."""
from typing import List, Dict, Any, Optional
import time
import uuid
from app.services.adapters.base import EmailSendAdapter


class MockEmailSendAdapter(EmailSendAdapter):
    """Mock adapter that simulates email sending for testing."""

    def __init__(self):
        self.sent_emails = []  # Store sent emails for verification

    def test_connection(self) -> bool:
        """Mock always returns successful connection."""
        return True

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate sending a single email."""
        message_id = f"mock-{uuid.uuid4()}"

        email_record = {
            "message_id": message_id,
            "to": to_email,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "from_name": from_name,
            "sent_at": time.time()
        }
        self.sent_emails.append(email_record)

        return {
            "success": True,
            "message_id": message_id,
            "error": None
        }

    def send_bulk(
        self,
        messages: List[Dict[str, Any]],
        rate_limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Simulate sending multiple emails with rate limiting."""
        results = []
        delay = 60.0 / rate_limit  # Seconds between sends

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

    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Return all sent emails (for testing)."""
        return self.sent_emails

    def clear_sent_emails(self):
        """Clear sent emails (for testing)."""
        self.sent_emails = []
