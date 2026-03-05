import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import time

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Society Management", layout="wide", page_icon="🏠")

# 2. CSS STYLING
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    .login-card {background: rgba(255,255,255,0.98); border-radius: 25px; padding: 3rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);}
    .stButton > button {background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white !important; border-radius: 30px; font-weight: 600;}
    .paid-members {background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 1rem; border-radius: 15px; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

DB_FILE = 'society.db'

# 3. DATABASE FUNCTIONS
def init_database():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS residents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, flat_number TEXT UNIQUE, phone TEXT, family_members INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS parking_slots (id INTEGER PRIMARY KEY AUTOINCREMENT, slot_number TEXT UNIQUE, assigned_to_flat TEXT, vehicle_number TEXT, status TEXT DEFAULT 'available')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS maintenance_payments (id INTEGER PRIMARY KEY AUTOINCREMENT, flat_number TEXT, amount_paid REAL DEFAULT 0, amount_due REAL DEFAULT 5000, paid_date TEXT, status TEXT DEFAULT 'pending', transaction_id TEXT, month_year TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, date_posted TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS complaints (id INTEGER PRIMARY KEY AUTOINCREMENT, resident_flat TEXT, subject TEXT, description TEXT, date_submitted TEXT, status TEXT DEFAULT 'open')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS polls (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, option1 TEXT, option2 TEXT, option3 TEXT, votes1 INTEGER DEFAULT 0, votes2 INTEGER DEFAULT 0, votes3 INTEGER DEFAULT 0, date_posted TEXT, flat_number_voted TEXT DEFAULT NULL)''')
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    # Using 'residents.name' as a fallback if join is needed later
    residents = pd.read_sql("SELECT * FROM residents", conn)
    parking = pd.read_sql("SELECT * FROM parking_slots", conn)
    payments = pd.read_sql("SELECT * FROM maintenance_payments", conn)
    notices = pd.read_sql("SELECT * FROM notices ORDER BY date_posted DESC", conn)
    complaints = pd.read_sql("SELECT * FROM complaints ORDER BY date_submitted DESC", conn)
    polls = pd.read_sql("SELECT * FROM polls ORDER BY date_posted DESC", conn)
    conn.close()
    return residents, parking, payments, notices, complaints, polls

# Initialize
init_database()

# 4. LOGIN LOGIC
def check_login(username, password):
    users = {"secretary": "admin123", "member": "pass123"}
    return username if username in users and users[username] == password else None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'role' not in st.session_state: st.session_state.role = None
if 'current_flat' not in st.session_state: st.session_state.current_flat = None

# 5. UI - LOGIN PAGE
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card' style='max-width:450px; margin:0 auto;'><h2 style='color:#2c3e50;text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🚀 Dashboard"):
            role = check_login(username, password)
            if role:
                st.session_state.logged_in, st.session_state.role, st.session_state.username = True, role, role
                st.rerun()
            else: st.error("❌ Wrong credentials!")
        st.markdown("<div style='text-align:center;color:#666;'>Secretary: secretary/admin123<br>Member: member/pass123</div></div>", unsafe_allow_html=True)

# 6. UI - MAIN DASHBOARD
else:
    residents, parking, payments, notices, complaints, polls = load_data()
    
    # Header & Logout
    col1, col2 = st.columns([3,1])
    with col1: st.title(f"🏢 Society Dashboard - {st.session_state.role.title()}")
    with col2: 
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Sidebar Stats
    with st.sidebar:
        st.header("📊 Quick Stats")
        st.metric("👥 Residents", len(residents))
        st.metric("🚗 Parking Used", len(parking[parking['status']=='occupied']))
        
        st.markdown("<div class='paid-members'><h4>✅ Recently Paid</h4></div>", unsafe_allow_html=True)
        # FIXED: Using correct column names 'amount_paid' and 'paid_date'
        recent_paid = payments[payments['status']=='paid'].head(5)
        if not recent_paid.empty:
            for _, row in recent_paid.iterrows():
                st.success(f"🏠 Flat {row['flat_number']}")
                st.caption(f"₹{row['amount_paid']} | {row['paid_date']}")
        else: st.info("No recent payments")

    # TABS
    tabs = st.tabs(["👥 Residents", "🚗 Parking", "💰 Payments", "💳 Maintenance", "📢 Notices", "⚠️ Complaints", "📊 Polls"])

    # Tab 0: Residents
    with tabs[0]:
        st.subheader("Resident Directory")
        st.dataframe(residents, use_container_width=True)

    # Tab 1: Parking
    with tabs[1]:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig = px.pie(values=[len(parking[parking['status']=='available']), len(parking[parking['status']=='occupied'])], 
                         names=['Available', 'Occupied'], hole=0.4, title="Parking Status")
            st.plotly_chart(fig)
        with col_p2:
            st.dataframe(parking)

    # Tab 2: Payments List
    with tabs[2]:
        st.subheader("All Transaction History")
        st.dataframe(payments, use_container_width=True)

    # Tab 3: Maintenance Payment (QR Code)
    with tabs[3]:
        col_m1, col_m2 = st.columns([1,2])
        with col_m1:
            st.markdown("### Scan to Pay")
            upi_link = "upi://pay?pa=jambhalemanali13@okicici&pn=Society&cu=INR"
            qr = qrcode.make(upi_link)
            buf = BytesIO()
            qr.save(buf, format='PNG')
            st.image(buf.getvalue(), width=250)
            
            f_no = st.text_input("Confirm Flat Number")
            amt = st.number_input("Amount", min_value=100.0)
            if st.button("Confirm Payment"):
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                txn = f"TXN{int(time.time())}"
                cur.execute("INSERT INTO maintenance_payments (flat_number, amount_paid, paid_date, status, transaction_id) VALUES (?,?,?,?,?)",
                            (f_no, amt, now, 'paid', txn))
                conn.commit()
                conn.close()
                st.success("Payment Recorded!")
                st.rerun()

    # Tab 4: Notices
    with tabs[4]:
        if st.session_state.role == "secretary":
            with st.expander("Post New Notice"):
                t = st.text_input("Title")
                d = st.text_area("Content")
                if st.button("Publish"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("INSERT INTO notices (title, description, date_posted) VALUES (?,?,?)", (t, d, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.rerun()
        for n in notices.itertuples():
            st.info(f"**{n.title}** ({n.date_posted})\n\n{n.description}")

    # Tab 5: Complaints
    with tabs[5]:
        with st.expander("File a Complaint"):
            subj = st.text_input("Subject")
            desc = st.text_area("Details")
            if st.button("Submit Complaint"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO complaints (resident_flat, subject, description, date_submitted) VALUES (?,?,?,?)",
                             (st.session_state.current_flat or "Admin", subj, desc, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Submitted!")
        st.dataframe(complaints)

    # Tab 6: Polls
    with tabs[6]:
        if st.session_state.role == "secretary":
            with st.expander("Create Poll"):
                q = st.text_input("Question")
                o1 = st.text_input("Opt 1")
                o2 = st.text_input("Opt 2")
                if st.button("Create"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("INSERT INTO polls (question, option1, option2, date_posted) VALUES (?,?,?,?)", (q, o1, o2, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.rerun()
        for p in polls.itertuples():
            st.write(f"📊 **{p.question}**")
            # Simple voting logic would go here
