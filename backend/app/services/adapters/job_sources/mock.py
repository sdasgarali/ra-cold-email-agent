"""Mock job source adapter for testing."""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import random
from app.services.adapters.base import JobSourceAdapter


class MockJobSourceAdapter(JobSourceAdapter):
    """Mock adapter that generates sample job data for testing."""

    SAMPLE_COMPANIES = [
        "Acme Healthcare Corp", "MediCare Solutions", "HealthFirst Systems",
        "TechManufacturing Inc", "Industrial Logistics LLC", "Retail Giants Co",
        "AutoParts Manufacturing", "Construction Builders Inc", "Energy Solutions Ltd",
        "Food Processing Corp", "Hospitality Group LLC", "Real Estate Holdings",
        "Legal Associates LLP", "Insurance Partners Inc", "Financial Services Group"
    ]

    SAMPLE_TITLES = [
        "Warehouse Manager", "Production Supervisor", "HR Coordinator",
        "Operations Manager", "Plant Manager", "Logistics Coordinator",
        "Sales Representative", "Customer Service Manager", "Quality Assurance Lead",
        "Maintenance Technician", "Forklift Operator", "Shipping Clerk"
    ]

    STATES = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"]

    def test_connection(self) -> bool:
        """Mock always returns successful connection."""
        return True

    def fetch_jobs(
        self,
        location: str = "United States",
        posted_within_days: int = 1,
        industries: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate mock job postings."""
        jobs = []
        num_jobs = random.randint(10, 25)

        for i in range(num_jobs):
            company = random.choice(self.SAMPLE_COMPANIES)
            title = random.choice(self.SAMPLE_TITLES)
            state = random.choice(self.STATES)

            job = {
                "client_name": company,
                "job_title": title,
                "state": state,
                "posting_date": date.today() - timedelta(days=random.randint(0, posted_within_days)),
                "job_link": f"https://jobs.example.com/{i + 1000}",
                "salary_min": random.randint(40000, 60000),
                "salary_max": random.randint(65000, 120000),
                "source": "mock"
            }

            # Apply exclude keywords filter
            if exclude_keywords:
                should_exclude = False
                for keyword in exclude_keywords:
                    if keyword.lower() in title.lower() or keyword.lower() in company.lower():
                        should_exclude = True
                        break
                if should_exclude:
                    continue

            jobs.append(job)

        return jobs

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data (mock data is already normalized)."""
        return raw_data
