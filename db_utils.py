import sqlite3
from datetime import datetime

DB_FILE = 'society.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# RESIDENTS
def add_resident(name, flat_number, phone='', email='', family_members=1):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO residents (name, flat_number, phone, email, family_members) VALUES (?, ?, ?, ?, ?)',
                    (name, flat_number, phone, email, family_members))
        conn.commit()
        print(f"✅ Added: {name} (Flat {flat_number})")
        return True
    except sqlite3.IntegrityError:
        print("❌ Flat number already exists!")
        return False
    finally:
        conn.close()

def view_residents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM residents')
    residents = cur.fetchall()
    conn.close()
    if not residents:
        print("No residents found.")
        return
    print("\n📋 RESIDENTS:")
    for res in residents:
        print(f"ID:{res['id']} | {res['name']} | Flat:{res['flat_number']} | Phone:{res['phone']}")

# PARKING (basic)
def add_parking_slot(slot_number, assigned_to_flat=None, vehicle_number=''):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO parking_slots (slot_number, assigned_to_flat, vehicle_number) VALUES (?, ?, ?)',
                    (slot_number, assigned_to_flat, vehicle_number))
        conn.commit()
        print(f"✅ Added parking slot: {slot_number}")
    except sqlite3.IntegrityError:
        print("❌ Slot number already exists!")
    finally:
        conn.close()

def view_parking():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM parking_slots')
    slots = cur.fetchall()
    conn.close()
    print("\n🚗 PARKING SLOTS:")
    for slot in slots:
        print(f"Slot:{slot['slot_number']} | Status:{slot['status']} | Flat:{slot['assigned_to_flat']}")

# Add more functions later...
