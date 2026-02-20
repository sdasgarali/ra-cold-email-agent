"""NeverBounce email validation adapter."""
from typing import List, Dict, Any
import httpx
from app.services.adapters.base import EmailValidationAdapter
from app.core.config import settings
from app.db.models.email_validation import ValidationStatus


class NeverBounceAdapter(EmailValidationAdapter):
    """Adapter for NeverBounce email validation API."""

    BASE_URL = "https://api.neverbounce.com/v4"

    STATUS_MAP = {
        "valid": ValidationStatus.VALID,
        "invalid": ValidationStatus.INVALID,
        "disposable": ValidationStatus.INVALID,
        "catchall": ValidationStatus.CATCH_ALL,
        "unknown": ValidationStatus.UNKNOWN
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.NEVERBOUNCE_API_KEY

    def test_connection(self) -> bool:
        """Test connection to NeverBounce API."""
        if not self.api_key:
            return False

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/account/info",
                    params={"key": self.api_key},
                    timeout=10
                )
                return response.status_code == 200
        except Exception:
            return False

    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate a single email using NeverBounce API."""
        if not self.api_key:
            raise ValueError("NeverBounce API key not configured")

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/single/check",
                    params={
                        "key": self.api_key,
                        "email": email
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                result_code = data.get("result", "unknown")
                status = self.STATUS_MAP.get(result_code, ValidationStatus.UNKNOWN)

                return {
                    "email": email.lower(),
                    "status": status,
                    "sub_status": data.get("flags", []),
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
        """Validate multiple emails using NeverBounce bulk API."""
        if not self.api_key:
            raise ValueError("NeverBounce API key not configured")

        # For bulk, we use individual validation as NeverBounce bulk requires file upload
        # In production, implement proper bulk job submission
        return [self.validate_email(email) for email in emails]
