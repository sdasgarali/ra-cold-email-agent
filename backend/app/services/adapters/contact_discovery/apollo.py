"""Apollo.io contact discovery adapter."""
from typing import List, Dict, Any, Optional
import httpx
from app.services.adapters.base import ContactDiscoveryAdapter
from app.core.config import settings
from app.db.models.contact import PriorityLevel


class ApolloAdapter(ContactDiscoveryAdapter):
    """Adapter for Apollo.io contact discovery API."""

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self):
        self.api_key = settings.APOLLO_API_KEY

    def test_connection(self) -> bool:
        """Test connection to Apollo API."""
        if not self.api_key:
            return False

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/auth/health",
                    headers={"X-Api-Key": self.api_key},
                    timeout=10
                )
                return response.status_code == 200
        except Exception:
            return False

    def _determine_priority(self, title: str) -> PriorityLevel:
        """Determine priority level based on job title."""
        title_lower = title.lower()

        # P1: Job poster / Hiring Manager
        if any(kw in title_lower for kw in ["hiring manager", "talent acquisition"]):
            return PriorityLevel.P1_JOB_POSTER

        # P2: HR/TA/Recruiter
        if any(kw in title_lower for kw in ["recruiter", "hr coordinator", "talent"]):
            return PriorityLevel.P2_HR_TA_RECRUITER

        # P3: HR Manager/Director
        if any(kw in title_lower for kw in ["hr manager", "hrbp", "hr director", "vp hr", "vp human"]):
            return PriorityLevel.P3_HR_MANAGER

        # P4: Operations leaders
        if any(kw in title_lower for kw in ["operations", "plant manager", "production", "business leader"]):
            return PriorityLevel.P4_OPS_LEADER

        # P5: Functional managers
        return PriorityLevel.P5_FUNCTIONAL_MANAGER

    def search_contacts(
        self,
        company_name: str,
        job_title: Optional[str] = None,
        state: Optional[str] = None,
        titles: Optional[List[str]] = None,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """Search for contacts at a company using Apollo API."""
        if not self.api_key:
            raise ValueError("Apollo API key not configured")

        # Build search payload
        payload = {
            "q_organization_name": company_name,
            "per_page": limit * 2,  # Get extra to filter
            "page": 1
        }

        if titles:
            payload["person_titles"] = titles
        else:
            # Default decision-maker titles
            payload["person_titles"] = [
                "HR Manager", "HR Director", "Talent Acquisition",
                "Recruiter", "Operations Manager", "HRBP"
            ]

        if state:
            payload["person_locations"] = [f"{state}, US"]

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.BASE_URL}/mixed_people/search",
                    headers={
                        "Content-Type": "application/json",
                        "X-Api-Key": self.api_key
                    },
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                contacts = []
                for person in data.get("people", [])[:limit]:
                    contact = self.normalize(person)
                    if contact:
                        contacts.append(contact)

                return contacts

        except Exception as e:
            raise RuntimeError(f"Apollo API error: {str(e)}")

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Apollo API response to standard format."""
        if not raw_data:
            return None

        email = raw_data.get("email")
        if not email:
            return None

        title = raw_data.get("title", "")

        return {
            "first_name": raw_data.get("first_name", ""),
            "last_name": raw_data.get("last_name", ""),
            "title": title,
            "email": email,
            "phone": raw_data.get("phone_numbers", [{}])[0].get("sanitized_number") if raw_data.get("phone_numbers") else None,
            "location_state": raw_data.get("state"),
            "priority_level": self._determine_priority(title),
            "source": "apollo"
        }
