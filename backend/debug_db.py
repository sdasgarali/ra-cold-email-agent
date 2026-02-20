"""Debug database state."""
import sys
sys.path.insert(0, '.')

from app.db.base import SessionLocal
from app.db.models.contact import ContactDetails
from app.db.models.lead import LeadDetails
from app.schemas.contact import ContactResponse
from app.schemas.lead import LeadResponse

db = SessionLocal()

print("="*60)
print("DATABASE DEBUG")
print("="*60)

# Check leads
leads = db.query(LeadDetails).limit(3).all()
print(f"\nLeads count: {db.query(LeadDetails).count()}")
print("\nSample leads:")
for lead in leads:
    print(f"  ID:{lead.lead_id} | {lead.client_name} | {lead.job_title}")
    print(f"    - Has contacts attr: {hasattr(lead, 'contacts')}")
    if hasattr(lead, 'contacts'):
        print(f"    - Contacts via relationship: {len(lead.contacts)}")

# Check contacts
contacts = db.query(ContactDetails).limit(3).all()
print(f"\nContacts count: {db.query(ContactDetails).count()}")
print("\nSample contacts:")
for contact in contacts:
    print(f"  ID:{contact.contact_id} | {contact.first_name} {contact.last_name} | lead_id: {contact.lead_id}")

# Test ContactResponse validation
print("\n--- Testing ContactResponse validation ---")
if contacts:
    try:
        c = contacts[0]
        print(f"Contact attrs: {[a for a in dir(c) if not a.startswith('_')]}")
        response = ContactResponse.model_validate(c)
        print(f"ContactResponse validation succeeded: {response}")
    except Exception as e:
        print(f"ContactResponse validation failed: {e}")

# Test LeadResponse validation and contact_count
print("\n--- Testing LeadResponse with contact_count ---")
if leads:
    try:
        lead = leads[0]
        print(f"Lead attrs: {[a for a in dir(lead) if not a.startswith('_')]}")

        # Try model_validate
        lead_response = LeadResponse.model_validate(lead)
        print(f"LeadResponse.contact_count after model_validate: {lead_response.contact_count}")

        # Try model_dump
        lead_dict = lead_response.model_dump()
        print(f"lead_dict keys: {lead_dict.keys()}")
        print(f"lead_dict['contact_count']: {lead_dict.get('contact_count', 'NOT FOUND')}")

        # Add custom contact_count
        from sqlalchemy import func
        contact_count = db.query(func.count(ContactDetails.contact_id)).filter(
            ContactDetails.lead_id == lead.lead_id
        ).scalar() or 0
        lead_dict['contact_count'] = contact_count
        print(f"After manual addition, contact_count: {lead_dict['contact_count']}")

    except Exception as e:
        import traceback
        print(f"LeadResponse validation failed: {e}")
        traceback.print_exc()

# Check contacts for lead_id=14
print("\n--- Contacts for lead_id=14 ---")
lead_14_contacts = db.query(ContactDetails).filter(ContactDetails.lead_id == 14).all()
print(f"Count: {len(lead_14_contacts)}")
for c in lead_14_contacts[:3]:
    print(f"  - {c.first_name} {c.last_name} | {c.email} | lead_id: {c.lead_id}")

db.close()
print("\n[DEBUG COMPLETE]")
