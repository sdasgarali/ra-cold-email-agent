"""Quick API test script."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin@exzelon.com", "password": "Admin@123"}
)
print(f"Login status: {login_response.status_code}")

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get leads
print("\nFetching leads...")
leads_response = requests.get(f"{BASE_URL}/leads?page_size=5", headers=headers)
print(f"Leads status: {leads_response.status_code}")

if leads_response.status_code == 200:
    data = leads_response.json()
    print(f"\nTotal leads: {data['total']}")
    print(f"Page: {data['page']}")

    # Print first lead's full structure
    if data['items']:
        print(f"\nFirst lead full JSON:")
        print(json.dumps(data['items'][0], indent=2, default=str))

    print("\nAll leads with contact_count:")
    for lead in data['items']:
        contact_count = lead.get('contact_count', 'NOT PRESENT')
        print(f"  - ID:{lead['lead_id']} | {lead['client_name'][:30]} | Contacts: {contact_count}")
else:
    print(f"Failed: {leads_response.text}")

# Get contacts for first lead
if leads_response.status_code == 200 and data['items']:
    first_lead_id = data['items'][0]['lead_id']
    print(f"\n\nFetching contacts for lead {first_lead_id}...")
    contacts_response = requests.get(f"{BASE_URL}/contacts?lead_id={first_lead_id}", headers=headers)

    print(f"Contacts status: {contacts_response.status_code}")
    if contacts_response.status_code == 200:
        contacts_data = contacts_response.json()
        print(f"Total contacts for lead {first_lead_id}: {contacts_data['total']}")
        for contact in contacts_data['items'][:3]:
            print(f"  - {contact['first_name']} {contact['last_name']} | {contact['email']} | lead_id: {contact.get('lead_id', 'N/A')}")
    else:
        print(f"Failed: {contacts_response.text}")

# Also test contacts/by-lead endpoint
if leads_response.status_code == 200 and data['items']:
    first_lead_id = data['items'][0]['lead_id']
    print(f"\n\nFetching contacts via /contacts/by-lead/{first_lead_id}...")
    contacts_response = requests.get(f"{BASE_URL}/contacts/by-lead/{first_lead_id}", headers=headers)

    print(f"Contacts by-lead status: {contacts_response.status_code}")
    if contacts_response.status_code == 200:
        contacts_data = contacts_response.json()
        print(f"Total contacts: {contacts_data['total']}")
        for contact in contacts_data['contacts'][:3]:
            print(f"  - {contact['first_name']} {contact['last_name']} | {contact['email']}")
    else:
        print(f"Failed: {contacts_response.text}")

print("\n[TEST COMPLETE]")
