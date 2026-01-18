"""Email validation adapters package."""
from app.services.adapters.email_validation.mock import MockEmailValidationAdapter
from app.services.adapters.email_validation.neverbounce import NeverBounceAdapter
from app.services.adapters.email_validation.zerobounce import ZeroBounceAdapter

__all__ = ["MockEmailValidationAdapter", "NeverBounceAdapter", "ZeroBounceAdapter"]
