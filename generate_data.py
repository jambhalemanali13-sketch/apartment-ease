import sqlite3
import random

conn = sqlite3.connect('society.db')
cur = conn.cursor()

# Clear existing
cur.execute('DELETE FROM residents')
cur.execute('DELETE FROM parking_slots')
cur.execute('DELETE FROM maintenance_payments')

# Indian names
names = ["Rakesh Patil", "Priya Patel", "Rahul Singh", "Bhupendra Jambhale", "Vikram Desai", 
         "Sneha Joshi", "Sarthak Chaudary", "Anita Rao", "Rohit Nair", "Pooja Reddy"] * 10

flats = [f"{chr(65+i//10)}{i%10+1:02d}" for i in range(100)]  # A01-A10, B01-B10...

# 100 RANDOM RESIDENTS
for i in range(100):
    name = random.choice(names)
    flat = flats[i]
    phone = f"98{random.randint(10000000,99999999)}"
    family = random.randint(1, 6)
    cur.execute("INSERT INTO residents VALUES (NULL, ?, ?, ?, ?, ?)",
                (name, flat, phone, f"{name.lower().replace(' ','.')}@gmail.com", family))

# 50 RANDOM PARKING SLOTS
parking_slots = [f"P{i+1:02d}" for i in range(50)]
for slot in parking_slots:
    assigned = random.choice(flats) if random.random() > 0.4 else None
    vehicle = f"MH04AB{random.randint(1000,9999)}" if assigned else ''
    status = 'occupied' if assigned else 'available'
    cur.execute("INSERT INTO parking_slots VALUES (NULL, ?, ?, ?, ?)",
                (slot, assigned, vehicle, status))

# 20 SAMPLE PAYMENTS
for _ in range(20):
    flat = random.choice(flats)
    month = '2026-02'
    due = round(random.uniform(2500, 6500), 2)
    paid = round(random.uniform(0, due), 2)
    status = 'paid' if paid >= due*0.9 else ('pending' if random.random()>0.3 else 'overdue')
    cur.execute("INSERT INTO maintenance_payments (flat_number, month_year, amount_due, amount_paid, status) VALUES (?, ?, ?, ?, ?)",
                (flat, month, due, paid, status))

conn.commit()
conn.close()
print("✅ 100 RESIDENTS + 50 PARKING + PAYMENTS GENERATED!")
