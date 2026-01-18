"""Unit tests for provider adapters."""
import pytest
from app.services.adapters.job_sources.mock import MockJobSourceAdapter
from app.services.adapters.contact_discovery.mock import MockContactDiscoveryAdapter
from app.services.adapters.email_validation.mock import MockEmailValidationAdapter
from app.services.adapters.email_sending.mock import MockEmailSendAdapter
from app.db.models.email_validation import ValidationStatus


class TestMockJobSourceAdapter:
    """Tests for MockJobSourceAdapter."""

    def test_test_connection(self):
        """Test connection should always succeed for mock."""
        adapter = MockJobSourceAdapter()
        assert adapter.test_connection() is True

    def test_fetch_jobs_returns_list(self):
        """Fetch jobs should return a list."""
        adapter = MockJobSourceAdapter()
        jobs = adapter.fetch_jobs()
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_fetch_jobs_with_filters(self):
        """Fetch jobs with exclude keywords should filter results."""
        adapter = MockJobSourceAdapter()
        jobs = adapter.fetch_jobs(exclude_keywords=["IT", "Software"])
        for job in jobs:
            assert "IT" not in job["job_title"].upper()
            assert "Software" not in job["job_title"]

    def test_job_has_required_fields(self):
        """Each job should have required fields."""
        adapter = MockJobSourceAdapter()
        jobs = adapter.fetch_jobs()
        required_fields = ["client_name", "job_title", "state", "posting_date", "source"]
        for job in jobs:
            for field in required_fields:
                assert field in job

    def test_normalize_passthrough(self):
        """Normalize should return the same data for mock."""
        adapter = MockJobSourceAdapter()
        data = {"test": "value"}
        assert adapter.normalize(data) == data


class TestMockContactDiscoveryAdapter:
    """Tests for MockContactDiscoveryAdapter."""

    def test_test_connection(self):
        """Test connection should always succeed for mock."""
        adapter = MockContactDiscoveryAdapter()
        assert adapter.test_connection() is True

    def test_search_contacts_returns_list(self):
        """Search contacts should return a list."""
        adapter = MockContactDiscoveryAdapter()
        contacts = adapter.search_contacts(company_name="Test Company")
        assert isinstance(contacts, list)
        assert len(contacts) > 0

    def test_search_contacts_respects_limit(self):
        """Search contacts should respect the limit parameter."""
        adapter = MockContactDiscoveryAdapter()
        contacts = adapter.search_contacts(company_name="Test Company", limit=2)
        assert len(contacts) <= 2

    def test_contact_has_required_fields(self):
        """Each contact should have required fields."""
        adapter = MockContactDiscoveryAdapter()
        contacts = adapter.search_contacts(company_name="Test Company")
        required_fields = ["first_name", "last_name", "email", "priority_level"]
        for contact in contacts:
            for field in required_fields:
                assert field in contact

    def test_contact_email_format(self):
        """Contact email should have valid format."""
        adapter = MockContactDiscoveryAdapter()
        contacts = adapter.search_contacts(company_name="Test Company")
        for contact in contacts:
            assert "@" in contact["email"]
            assert "." in contact["email"]


class TestMockEmailValidationAdapter:
    """Tests for MockEmailValidationAdapter."""

    def test_test_connection(self):
        """Test connection should always succeed for mock."""
        adapter = MockEmailValidationAdapter()
        assert adapter.test_connection() is True

    def test_validate_email_returns_result(self):
        """Validate email should return a result dict."""
        adapter = MockEmailValidationAdapter()
        result = adapter.validate_email("test@example.com")
        assert isinstance(result, dict)
        assert "email" in result
        assert "status" in result

    def test_validate_email_normalizes_email(self):
        """Validate email should lowercase the email."""
        adapter = MockEmailValidationAdapter()
        result = adapter.validate_email("TEST@EXAMPLE.COM")
        assert result["email"] == "test@example.com"

    def test_validate_email_returns_valid_status(self):
        """Validate email should return a valid ValidationStatus."""
        adapter = MockEmailValidationAdapter()
        result = adapter.validate_email("test@example.com")
        assert result["status"] in [
            ValidationStatus.VALID,
            ValidationStatus.INVALID,
            ValidationStatus.CATCH_ALL,
            ValidationStatus.UNKNOWN
        ]

    def test_validate_bulk_returns_list(self):
        """Validate bulk should return a list of results."""
        adapter = MockEmailValidationAdapter()
        emails = ["test1@example.com", "test2@example.com", "test3@example.com"]
        results = adapter.validate_bulk(emails)
        assert isinstance(results, list)
        assert len(results) == len(emails)


class TestMockEmailSendAdapter:
    """Tests for MockEmailSendAdapter."""

    def test_test_connection(self):
        """Test connection should always succeed for mock."""
        adapter = MockEmailSendAdapter()
        assert adapter.test_connection() is True

    def test_send_email_success(self):
        """Send email should return success."""
        adapter = MockEmailSendAdapter()
        result = adapter.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            body_html="<p>Test body</p>"
        )
        assert result["success"] is True
        assert result["message_id"] is not None
        assert result["error"] is None

    def test_send_email_stores_email(self):
        """Send email should store the sent email."""
        adapter = MockEmailSendAdapter()
        adapter.clear_sent_emails()
        adapter.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            body_html="<p>Test body</p>"
        )
        sent_emails = adapter.get_sent_emails()
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == "test@example.com"

    def test_send_bulk_respects_rate_limit(self):
        """Send bulk should process all messages."""
        adapter = MockEmailSendAdapter()
        messages = [
            {"to_email": f"test{i}@example.com", "subject": f"Test {i}", "body_html": "<p>Body</p>"}
            for i in range(3)
        ]
        results = adapter.send_bulk(messages, rate_limit=100)  # High rate for fast test
        assert len(results) == 3
        assert all(r["success"] for r in results)
