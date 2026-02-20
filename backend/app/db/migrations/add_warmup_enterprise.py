"""Database migration for enterprise warmup engine tables and columns."""
import sqlite3
import json
import os


def run_migration():
    # Try backend/data/ path first (3 levels up from this file), then project root data/
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    db_path = os.path.join(base, 'data', 'ra_agent.db')
    if not os.path.exists(db_path):
        # Try one more level up (project root/data/)
        db_path = os.path.join(os.path.dirname(base), 'data', 'ra_agent.db')
    if not os.path.exists(db_path):
        print(f'Database not found - tables will be created on startup via create_all')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if sender_mailboxes table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sender_mailboxes'")
    if not cursor.fetchone():
        print('sender_mailboxes table does not exist yet - will be created with all columns on startup')
        conn.close()
        return

    # Add new columns to sender_mailboxes
    new_columns = [
        ('warmup_profile_id', 'INTEGER'),
        ('connection_status', 'VARCHAR(20) DEFAULT "untested"'),
        ('last_connection_test_at', 'DATETIME'),
        ('warmup_emails_sent', 'INTEGER DEFAULT 0'),
        ('warmup_emails_received', 'INTEGER DEFAULT 0'),
        ('warmup_opens', 'INTEGER DEFAULT 0'),
        ('warmup_replies', 'INTEGER DEFAULT 0'),
        ('last_dns_check_at', 'DATETIME'),
        ('last_blacklist_check_at', 'DATETIME'),
        ('dns_score', 'INTEGER DEFAULT 0'),
        ('is_blacklisted', 'BOOLEAN DEFAULT 0'),
        ('auto_recovery_started_at', 'DATETIME'),
    ]

    cursor.execute('PRAGMA table_info(sender_mailboxes)')
    existing_cols = {row[1] for row in cursor.fetchall()}

    added = 0
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f'ALTER TABLE sender_mailboxes ADD COLUMN {col_name} {col_type}')
                print(f'Added column sender_mailboxes.{col_name}')
                added += 1
            except Exception as e:
                print(f'Skipping {col_name}: {e}')

    if added > 0:
        cursor.execute('UPDATE sender_mailboxes SET connection_status = "untested" WHERE connection_status IS NULL')
        conn.commit()

    conn.close()
    print(f'Migration complete - {added} columns added')


if __name__ == '__main__':
    run_migration()
