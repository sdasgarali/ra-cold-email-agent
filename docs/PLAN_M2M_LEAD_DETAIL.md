# Plan: Many-to-Many Lead-Contact, Lead Detail Page, Email Threads

## Context
Contacts and Leads currently have a one-to-many relationship (each contact belongs to one lead via `lead_id` FK). The user needs:
- **Many-to-many**: A contact can be associated with multiple leads, and a lead with multiple contacts
- **Lead detail page**: `/dashboard/leads/[id]` showing contacts, outreach history, and email threads
- **Per-lead outreach**: Send emails to contacts of a specific lead only
- **Email thread storage**: Store sent email body + reply content in OutreachEvent
- **Bug fixes**: Lead ID visible in tables, contacts page links to lead detail page

## Files to Modify/Create

### Backend - New Files
1. `backend/app/db/models/lead_contact.py` - Junction table model (LeadContactAssociation)
2. `scripts/migrate_lead_contact_m2m.py` - Migration: create junction table, add outreach columns, copy existing FK data

### Backend - Modified Files
3. `backend/app/db/models/__init__.py` - Register LeadContactAssociation
4. `backend/app/db/models/outreach.py` - Add body_html, body_text, reply_body, reply_subject columns
5. `backend/app/db/models/lead.py` - Add many-to-many relationship via junction table
6. `backend/app/schemas/contact.py` - Add lead_ids field to response
7. `backend/app/schemas/outreach.py` - Add body/reply fields
8. `backend/app/schemas/lead.py` - Add LeadDetailResponse with contacts + outreach_events
9. `backend/app/api/endpoints/contacts.py` - Query via junction table, return lead_ids, add/remove lead associations
10. `backend/app/api/endpoints/leads.py` - Add `GET /leads/{id}/detail`, `POST /leads/{id}/contacts`, contact_count via junction table
11. `backend/app/services/pipelines/outreach.py` - Store email body in OutreachEvent, new `run_outreach_for_lead()` function
12. `backend/app/services/pipelines/contact_enrichment.py` - Also insert into junction table when creating contacts

### Frontend - New Files
13. `frontend/src/app/dashboard/leads/[id]/page.tsx` - Lead detail page with contacts table, outreach events, expandable email threads

### Frontend - Modified Files
14. `frontend/src/lib/api.ts` - Add leadsApi.getDetail(), leadsApi.manageContacts(), outreach endpoints
15. `frontend/src/app/dashboard/leads/page.tsx` - Add Lead ID column, link to detail page
16. `frontend/src/app/dashboard/contacts/page.tsx` - Show multiple lead_ids as badges, link to lead detail page

## Implementation Order

### Phase 1: Database Schema (Steps 1-5)
1. Create `backend/app/db/models/lead_contact.py` with LeadContactAssociation (id, lead_id FK, contact_id FK, unique constraint)
2. Register in `backend/app/db/models/__init__.py`
3. Add columns to OutreachEvent model: body_html, body_text, reply_body, reply_subject
4. Add `associated_contacts` relationship to LeadDetails model (secondary=junction table)
5. Run migration script: create junction table + ALTER TABLE outreach_events + copy existing lead_id FK data

### Phase 2: Backend APIs (Steps 6-11)
6. Update schemas: ContactResponse adds `lead_ids: List[int]`, OutreachEventResponse adds body/reply fields, new LeadDetailResponse
7. Update contacts API: query via junction table, enrich response with lead_ids, new endpoint to manage lead associations
8. Update leads API: contact_count via junction table, new `GET /{id}/detail` endpoint returning contacts + outreach events, new `POST /{id}/contacts` to add/remove contact associations
9. Update outreach pipeline: store body_html/body_text in OutreachEvent, new `run_outreach_for_lead()` function
10. Update contact enrichment: insert into junction table when creating contacts

### Phase 3: Frontend (Steps 12-16)
11. Update API client with new endpoints
12. Fix leads page: add Lead ID column, link company name and ID to detail page
13. Fix contacts page: show lead_ids as multiple badges, link to lead detail page
14. Create lead detail page with:
    - Lead info card (company, job, status, dates, salary, source)
    - Contacts table (name, email, priority, validation status) with remove button
    - Outreach section with "Send Outreach" button (dry-run toggle)
    - Outreach events table with expandable rows showing email body + reply

## Verification
1. Start backend, confirm junction table auto-created
2. Run migration script, verify existing 2 contacts migrated to junction table
3. API test: `GET /leads/1/detail` returns lead + contacts + outreach events
4. API test: `POST /leads/1/contacts` with `{"add_contact_ids": [2]}` links contact 2 to lead 1
5. API test: `GET /contacts` returns contacts with `lead_ids` array
6. Frontend: leads page shows Lead ID column, clicking opens detail page
7. Frontend: contacts page shows multiple lead badges linking to detail pages
8. Frontend: lead detail page shows contacts, outreach events, expandable email threads
9. Trigger outreach for lead 1, verify OutreachEvent has body_html stored
