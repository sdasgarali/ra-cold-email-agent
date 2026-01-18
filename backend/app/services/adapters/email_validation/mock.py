"""Mock email validation adapter for testing."""
from typing import List, Dict, Any
import random
from app.services.adapters.base import EmailValidationAdapter
from app.db.models.email_validation import ValidationStatus


class MockEmailValidationAdapter(EmailValidationAdapter):
    """Mock adapter that generates sample validation results for testing."""

    def test_connection(self) -> bool:
        """Mock always returns successful connection."""
        return True

    def validate_email(self, email: str) -> Dict[str, Any]:
        """Generate mock validation result for a single email."""
        # Simulate realistic validation distribution
        # ~85% valid, ~8% invalid, ~5% catch-all, ~2% unknown
        rand = random.random()

        if rand < 0.85:
            status = ValidationStatus.VALID
            sub_status = "verified"
        elif rand < 0.93:
            status = ValidationStatus.INVALID
            sub_status = random.choice(["mailbox_not_found", "domain_invalid", "syntax_error"])
        elif rand < 0.98:
            status = ValidationStatus.CATCH_ALL
            sub_status = "accept_all"
        else:
            status = ValidationStatus.UNKNOWN
            sub_status = "timeout"

        return {
            "email": email.lower(),
            "status": status,
            "sub_status": sub_status,
            "raw_response": {
                "provider": "mock",
                "email": email,
                "result": status.value
            }
        }

    def validate_bulk(self, emails: List[str]) -> List[Dict[str, Any]]:
        """Validate multiple emails."""
        return [self.validate_email(email) for email in emails]
