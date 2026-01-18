"""ZeroBounce email validation adapter."""
from typing import List, Dict, Any
import httpx
from app.services.adapters.base import EmailValidationAdapter
from app.core.config import settings
from app.db.models.email_validation import ValidationStatus


class ZeroBounceAdapter(EmailValidationAdapter):
    """Adapter for ZeroBounce email validation API."""

    BASE_URL = "https://api.zerobounce.net/v2"

    STATUS_MAP = {
        "valid": ValidationStatus.VALID,
        "invalid": ValidationStatus.INVALID,
        "catch-all": ValidationStatus.CATCH_ALL,
        "unknown": ValidationStatus.UNKNOWN,
        "spamtrap": ValidationStatus.INVALID,
        "abuse": ValidationStatus.INVALID,
        "do_not_mail": ValidationStatus.INVALID
    }

    def __init__(self):
        self.api_key = settings.ZEROBOUNCE_API_KEY

    def test_connection(self) -> bool:
        """Test connection to ZeroBounce API."""
        if not self.api_key:
            return False

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/getcredits",
                    params={"api_key": self.api_key},
                    timeout=10
                )
                return response.status_code == 200
        except Exception:
            return False

    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate a single email using ZeroBounce API."""
        if not self.api_key:
            raise ValueError("ZeroBounce API key not configured")

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/validate",
                    params={
                        "api_key": self.api_key,
                        "email": email
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                result_status = data.get("status", "unknown").lower()
                status = self.STATUS_MAP.get(result_status, ValidationStatus.UNKNOWN)

                return {
                    "email": email.lower(),
                    "status": status,
                    "sub_status": data.get("sub_status"),
                    "raw_response": data
                }

        except Exception as e:
            return {
                "email": email.lower(),
                "status": ValidationStatus.UNKNOWN,
                "sub_status": f"error: {str(e)}",
                "raw_response": {"error": str(e)}
            }

    def validate_bulk(self, emails: List[str]) -> List[Dict[str, Any]]:
        """Validate multiple emails using ZeroBounce bulk API."""
        if not self.api_key:
            raise ValueError("ZeroBounce API key not configured")

        # For simplicity, validate individually
        # In production, implement proper bulk file submission
        return [self.validate_email(email) for email in emails]
