"""Migration script: Create lead_contact_associations junction table and add outreach columns.

This script:
1. Creates the lead_contact_associations junction table
2. Adds body_html, body_text, reply_body, reply_subject columns to outreach_events (if table exists)
3. Copies existing lead_id FK data from contact_details into junction table (if data exists)
"""
import sqlite3
import os
import sys

# Find the database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ra_agent.db')

if not os.path.exists(DB_PATH):
    print(f'Database not found at {DB_PATH}')
    sys.exit(1)

print(f'Migrating database: {DB_PATH}')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check what tables exist
existing_tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f'Existing tables: {existing_tables}')

# 1. Create junction table if not exists
print('Step 1: Creating lead_contact_associations table...')
cursor.execute("""
    CREATE TABLE IF NOT EXISTS lead_contact_associations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL REFERENCES lead_details(lead_id) ON DELETE CASCADE,
        contact_id INTEGER NOT NULL REFERENCES contact_details(contact_id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        UNIQUE(lead_id, contact_id)
    )
""")
cursor.execute('CREATE INDEX IF NOT EXISTS idx_lca_lead_id ON lead_contact_associations(lead_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_lca_contact_id ON lead_contact_associations(contact_id)')
print('  Junction table ready.')

# 2. Add columns to outreach_events if table exists
if 'outreach_events' in existing_tables:
    print('Step 2: Adding columns to outreach_events...')
    existing_cols = [row[1] for row in cursor.execute('PRAGMA table_info(outreach_events)').fetchall()]

    for col_name, col_type in [
        ('body_html', 'TEXT'),
        ('body_text', 'TEXT'),
        ('reply_subject', 'VARCHAR(500)'),
        ('reply_body', 'TEXT'),
    ]:
        if col_name not in existing_cols:
            cursor.execute(f'ALTER TABLE outreach_events ADD COLUMN {col_name} {col_type}')
            print(f'  Added column: {col_name}')
        else:
            print(f'  Column already exists: {col_name}')
else:
    print('Step 2: outreach_events table not found yet (will be created on app startup). Skipping ALTER TABLE.')

# 3. Copy existing lead_id FK data into junction table
if 'contact_details' in existing_tables:
    print('Step 3: Migrating existing lead_id FK data to junction table...')
    cursor.execute("""
        INSERT OR IGNORE INTO lead_contact_associations (lead_id, contact_id, created_at, updated_at)
        SELECT lead_id, contact_id, created_at, updated_at
        FROM contact_details
        WHERE lead_id IS NOT NULL
    """)
    migrated = cursor.rowcount
    print(f'  Migrated {migrated} contact-lead associations.')
else:
    print('Step 3: contact_details table not found yet. No data to migrate.')

conn.commit()
conn.close()
print('Migration completed successfully!')
print()
print('NOTE: New columns on outreach_events will be created automatically on next app startup')
print('      via Base.metadata.create_all() since the model already has them.')
