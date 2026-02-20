"""Test the leads endpoint code directly."""
import sys
sys.path.insert(0, '.')

from sqlalchemy import func, desc
from app.db.base import SessionLocal
from app.db.models.lead import LeadDetails
from app.db.models.contact import ContactDetails
from app.schemas.lead import LeadResponse

db = SessionLocal()

print("Testing leads endpoint code directly...")

# Same code as the endpoint
query = db.query(LeadDetails)
total = query.count()
leads = query.order_by(desc(LeadDetails.created_at)).limit(5).all()

print(f"\nTotal leads: {total}")

# Build response with contact counts
lead_responses = []
for lead in leads:
    lead_dict = LeadResponse.model_validate(lead).model_dump()
    # Get contact count for this lead
    contact_count = db.query(func.count(ContactDetails.contact_id)).filter(
        ContactDetails.lead_id == lead.lead_id
    ).scalar() or 0
    lead_dict['contact_count'] = contact_count
    lead_responses.append(lead_dict)

print("\nLead responses:")
for item in lead_responses:
    print(f"  - {item['client_name']}: contact_count = {item.get('contact_count', 'NOT FOUND')}")
    print(f"    All keys: {list(item.keys())[-5:]}")  # Last 5 keys

import json
print(f"\n\nFirst lead full JSON:\n{json.dumps(lead_responses[0], indent=2, default=str)}")

db.close()
