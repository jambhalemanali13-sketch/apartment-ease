import sqlite3
from datetime import datetime

# Create/connect to database
conn = sqlite3.connect('society.db')
cur = conn.cursor()

# Residents table
cur.execute('''
CREATE TABLE IF NOT EXISTS residents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    flat_number TEXT UNIQUE NOT NULL,
    phone TEXT,
    email TEXT,
    family_members INTEGER DEFAULT 1
)
''')

# Parking slots
cur.execute('''
CREATE TABLE IF NOT EXISTS parking_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number TEXT UNIQUE NOT NULL,
    assigned_to_flat TEXT,
    vehicle_number TEXT,
    status TEXT DEFAULT 'available'
)
''')

# Maintenance payments
cur.execute('''
CREATE TABLE IF NOT EXISTS maintenance_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flat_number TEXT NOT NULL,
    month_year TEXT NOT NULL,
    amount_due REAL NOT NULL,
    amount_paid REAL DEFAULT 0,
    due_date DATE,
    paid_date DATE,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (flat_number) REFERENCES residents (flat_number)
)
''')

# Notices
cur.execute('''
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    date_posted DATE NOT NULL,
    expiry_date DATE
)
''')

# Complaints
cur.execute('''
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_flat TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    date_submitted DATE NOT NULL,
    status TEXT DEFAULT 'open',
    resolution TEXT,
    resolved_date DATE,
    FOREIGN KEY (resident_flat) REFERENCES residents (flat_number)
)
''')

conn.commit()
conn.close()
print("✅ Database 'society.db' created successfully!")
