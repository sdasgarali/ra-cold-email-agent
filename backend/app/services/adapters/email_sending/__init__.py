"""Email sending adapters package."""
from app.services.adapters.email_sending.mock import MockEmailSendAdapter
from app.services.adapters.email_sending.smtp import SMTPAdapter

__all__ = ["MockEmailSendAdapter", "SMTPAdapter"]
