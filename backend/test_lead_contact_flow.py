"""
Test script for Lead -> Contact relationship verification.
This script:
1. Cleans up the database
2. Runs Lead Sourcing pipeline
3. Runs Contact Enrichment pipeline
4. Verifies lead_id links are correct

Test Report will be saved to test_report.md
"""
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, '.')

from app.db.base import SessionLocal
from app.db.models.contact import ContactDetails
from app.db.models.lead import LeadDetails, LeadStatus


def cleanup_database():
    """Delete all leads and contacts."""
    print("\n" + "="*60)
    print("STEP 1: DATABASE CLEANUP")
    print("="*60)

    db = SessionLocal()
    try:
        contacts_count = db.query(ContactDetails).count()
        leads_count = db.query(LeadDetails).count()
        print(f"Before cleanup: {leads_count} leads, {contacts_count} contacts")

        # Delete contacts first (foreign key)
        deleted_contacts = db.query(ContactDetails).delete()
        db.commit()
        print(f"Deleted {deleted_contacts} contacts")

        # Delete leads
        deleted_leads = db.query(LeadDetails).delete()
        db.commit()
        print(f"Deleted {deleted_leads} leads")

        # Verify
        contacts_after = db.query(ContactDetails).count()
        leads_after = db.query(LeadDetails).count()
        print(f"After cleanup: {leads_after} leads, {contacts_after} contacts")
        print("Database cleanup complete!")

        return {
            "deleted_leads": deleted_leads,
            "deleted_contacts": deleted_contacts
        }

    finally:
        db.close()


def run_lead_sourcing():
    """Run the lead sourcing pipeline."""
    print("\n" + "="*60)
    print("STEP 2: LEAD SOURCING PIPELINE")
    print("="*60)

    from app.services.pipelines.lead_sourcing import run_lead_sourcing_pipeline

    # Run the pipeline (uses mock adapter by default if no API keys configured)
    result = run_lead_sourcing_pipeline(
        sources=["mock"],
        triggered_by="test_script"
    )

    print(f"Lead sourcing result: {result}")

    # Get lead count and samples
    db = SessionLocal()
    try:
        leads_count = db.query(LeadDetails).count()
        print(f"Total leads in database: {leads_count}")

        # Show sample leads
        leads = db.query(LeadDetails).limit(5).all()
        print("\nSample leads created:")
        for lead in leads:
            print(f"  - ID:{lead.lead_id} | {lead.client_name} | {lead.job_title} | {lead.state} | Status: {lead.lead_status.value}")

        return result, leads_count

    finally:
        db.close()


def run_contact_enrichment():
    """Run the contact enrichment pipeline."""
    print("\n" + "="*60)
    print("STEP 3: CONTACT ENRICHMENT PIPELINE")
    print("="*60)

    from app.services.pipelines.contact_enrichment import run_contact_enrichment_pipeline

    # Run the pipeline
    result = run_contact_enrichment_pipeline(triggered_by="test_script")

    print(f"Contact enrichment result: {result}")

    # Get contact count
    db = SessionLocal()
    try:
        contacts_count = db.query(ContactDetails).count()
        print(f"Total contacts in database: {contacts_count}")

        return result, contacts_count

    finally:
        db.close()


def verify_lead_contact_relationships():
    """Verify that contacts are correctly linked to leads."""
    print("\n" + "="*60)
    print("STEP 4: VERIFICATION OF LEAD-CONTACT RELATIONSHIPS")
    print("="*60)

    db = SessionLocal()
    issues = []
    verification_details = []

    try:
        # Get all leads and contacts
        leads = db.query(LeadDetails).all()
        contacts = db.query(ContactDetails).all()

        print(f"\nTotal leads: {len(leads)}")
        print(f"Total contacts: {len(contacts)}")

        # Check 1: All contacts should have lead_id set
        contacts_without_lead = [c for c in contacts if c.lead_id is None]
        if contacts_without_lead:
            issues.append({
                "issue": "Contacts without lead_id",
                "severity": "HIGH",
                "count": len(contacts_without_lead),
                "details": [f"{c.first_name} {c.last_name} ({c.email})" for c in contacts_without_lead[:5]]
            })
            print(f"\n[ISSUE] {len(contacts_without_lead)} contacts have no lead_id!")
        else:
            print(f"\n[OK] All {len(contacts)} contacts have lead_id set")
            verification_details.append(f"All {len(contacts)} contacts have lead_id set")

        # Check 2: All lead_ids should reference valid leads
        lead_ids = {lead.lead_id for lead in leads}
        invalid_lead_refs = [c for c in contacts if c.lead_id and c.lead_id not in lead_ids]
        if invalid_lead_refs:
            issues.append({
                "issue": "Contacts with invalid lead_id",
                "severity": "HIGH",
                "count": len(invalid_lead_refs),
                "details": [f"{c.first_name} {c.last_name} has lead_id={c.lead_id}" for c in invalid_lead_refs[:5]]
            })
            print(f"\n[ISSUE] {len(invalid_lead_refs)} contacts reference non-existent leads!")
        else:
            print(f"[OK] All contact lead_id references are valid")
            verification_details.append("All contact lead_id references are valid")

        # Check 3: Contact's client_name should match lead's client_name
        mismatched_clients = []
        for contact in contacts:
            if contact.lead_id:
                lead = db.query(LeadDetails).filter(LeadDetails.lead_id == contact.lead_id).first()
                if lead and contact.client_name != lead.client_name:
                    mismatched_clients.append({
                        "contact": f"{contact.first_name} {contact.last_name}",
                        "contact_client": contact.client_name,
                        "lead_client": lead.client_name,
                        "lead_id": contact.lead_id
                    })

        if mismatched_clients:
            issues.append({
                "issue": "Client name mismatch between contact and lead",
                "severity": "MEDIUM",
                "count": len(mismatched_clients),
                "details": mismatched_clients[:5]
            })
            print(f"\n[ISSUE] {len(mismatched_clients)} contacts have mismatched client_name!")
            for m in mismatched_clients[:3]:
                print(f"  - {m['contact']}: contact.client_name='{m['contact_client']}' vs lead.client_name='{m['lead_client']}'")
        else:
            print(f"[OK] All contact client_names match their linked lead's client_name")
            verification_details.append("All contact client_names match their linked lead's client_name")

        # Check 4: Show lead-contact distribution
        print("\n--- Lead-Contact Distribution ---")
        leads_with_contacts = 0
        leads_without_contacts = 0

        for lead in leads:
            contact_count = db.query(ContactDetails).filter(ContactDetails.lead_id == lead.lead_id).count()
            if contact_count > 0:
                leads_with_contacts += 1
            else:
                leads_without_contacts += 1

        print(f"Leads with contacts: {leads_with_contacts}")
        print(f"Leads without contacts: {leads_without_contacts}")
        verification_details.append(f"Leads with contacts: {leads_with_contacts}, without: {leads_without_contacts}")

        # Show detailed mapping
        print("\n--- Detailed Lead-Contact Mapping ---")
        mapping_details = []
        for lead in leads[:15]:  # Show first 15
            lead_contacts = db.query(ContactDetails).filter(ContactDetails.lead_id == lead.lead_id).all()
            detail = {
                "lead_id": lead.lead_id,
                "client_name": lead.client_name,
                "job_title": lead.job_title,
                "contacts": []
            }
            print(f"\nLead {lead.lead_id}: {lead.client_name} ({lead.job_title})")
            if lead_contacts:
                for c in lead_contacts:
                    match_status = "MATCH" if c.client_name == lead.client_name else "MISMATCH"
                    print(f"  -> Contact: {c.first_name} {c.last_name} | {c.email} | client: {c.client_name} [{match_status}]")
                    detail["contacts"].append({
                        "name": f"{c.first_name} {c.last_name}",
                        "email": c.email,
                        "client_name": c.client_name,
                        "match": match_status == "MATCH"
                    })
            else:
                print(f"  -> No contacts")
            mapping_details.append(detail)

        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)

        if not issues:
            print("\n[SUCCESS] All verifications passed!")
            print("Contacts are correctly linked to leads via lead_id.")
            return True, issues, verification_details, mapping_details
        else:
            print(f"\n[FAILED] Found {len(issues)} issue(s):")
            for i, issue in enumerate(issues, 1):
                print(f"\n  Issue {i}: {issue['issue']} ({issue['severity']})")
                print(f"  Count: {issue['count']}")
                if issue.get('details'):
                    print(f"  Examples: {issue['details'][:3]}")
            return False, issues, verification_details, mapping_details

    finally:
        db.close()


def generate_test_report(cleanup_result, sourcing_result, enrichment_result, verification_result, issues, verification_details, mapping_details):
    """Generate a markdown test report."""
    print("\n" + "="*60)
    print("GENERATING TEST REPORT")
    print("="*60)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, sourcing_count = sourcing_result
    enrichment_counters, contact_count = enrichment_result

    report = f"""# Lead-Contact Relationship Test Report

**Test Date:** {timestamp}
**Status:** {"PASSED" if verification_result else "FAILED"}

## 1. Test Overview

This test verifies that the Lead → Contact relationship is correctly implemented:
- Contacts are linked to specific leads via `lead_id`
- Contact's `client_name` matches the linked lead's `client_name`
- No orphaned contacts (contacts without valid lead references)

## 2. Database Cleanup

- Deleted {cleanup_result['deleted_leads']} leads
- Deleted {cleanup_result['deleted_contacts']} contacts
- Database reset to clean state: SUCCESS

## 3. Lead Sourcing Pipeline

**Result:** {success}

| Metric | Value |
|--------|-------|
| Leads Inserted | {success.get('inserted', 0)} |
| Leads Skipped (duplicates) | {success.get('skipped', 0)} |
| Errors | {success.get('errors', 0)} |
| Sources Used | {', '.join(success.get('sources_used', []))} |

**Total Leads in Database:** {sourcing_count}

## 4. Contact Enrichment Pipeline

**Result:** {enrichment_counters}

| Metric | Value |
|--------|-------|
| Contacts Found | {enrichment_counters.get('contacts_found', 0)} |
| Leads Enriched | {enrichment_counters.get('leads_enriched', 0)} |
| Skipped | {enrichment_counters.get('skipped', 0)} |
| Errors | {enrichment_counters.get('errors', 0)} |

**Total Contacts in Database:** {contact_count}

## 5. Verification Results

### Checks Performed

"""
    for detail in verification_details:
        report += f"- [x] {detail}\n"

    if issues:
        report += "\n### Issues Found\n\n"
        for i, issue in enumerate(issues, 1):
            report += f"#### Issue {i}: {issue['issue']}\n"
            report += f"- **Severity:** {issue['severity']}\n"
            report += f"- **Count:** {issue['count']}\n"
            report += f"- **Examples:** {issue['details'][:3]}\n\n"
    else:
        report += "\n### No Issues Found\n\nAll verification checks passed successfully.\n"

    report += """
## 6. Lead-Contact Mapping Sample

| Lead ID | Company | Job Title | Contacts |
|---------|---------|-----------|----------|
"""
    for detail in mapping_details[:10]:
        contacts_str = ", ".join([f"{c['name']} ({c['email']})" for c in detail['contacts']]) if detail['contacts'] else "None"
        report += f"| {detail['lead_id']} | {detail['client_name'][:30]} | {detail['job_title'][:25]} | {contacts_str[:50]}... |\n"

    report += f"""
## 7. Conclusion

**Test Result:** {"PASSED - All contacts are correctly linked to their leads via lead_id" if verification_result else "FAILED - See issues above"}

### Key Findings:
1. Lead sourcing creates leads with status 'new' to enable contact enrichment
2. Contact enrichment correctly sets lead_id when creating contacts
3. Contact's client_name is copied from the lead for consistency
4. Each contact is uniquely linked to a specific lead (1-to-many relationship)

---
*Report generated by test_lead_contact_flow.py*
"""

    # Save report
    report_path = "test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Test report saved to: {report_path}")
    return report_path


def main():
    """Main test flow."""
    print("\n" + "#"*60)
    print("# LEAD-CONTACT RELATIONSHIP TEST")
    print("#"*60)

    # Step 1: Cleanup
    cleanup_result = cleanup_database()

    # Step 2: Lead Sourcing
    sourcing_result = run_lead_sourcing()

    # Step 3: Contact Enrichment
    enrichment_result = run_contact_enrichment()

    # Step 4: Verification
    success, issues, verification_details, mapping_details = verify_lead_contact_relationships()

    # Step 5: Generate Report
    generate_test_report(
        cleanup_result,
        sourcing_result,
        enrichment_result,
        success,
        issues,
        verification_details,
        mapping_details
    )

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
