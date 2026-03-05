import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import time

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    .login-card {background: rgba(255,255,255,0.98); border-radius: 25px; padding: 3rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);}
    .stButton > button {background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white !important; border-radius: 30px; font-weight: 600;}
    .receipt-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 20px; padding: 2rem;}
    .paid-members {background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 1rem; border-radius: 15px; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Society Management", layout="wide", page_icon="🏠")
DB_FILE = 'society.db'

def init_database():
    """🔧 COMPLETE DATABASE INITIALIZATION WITH MIGRATION"""
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    cursor = conn.cursor()
    
    # 1. CREATE TABLES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS residents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        flat_number TEXT UNIQUE,
        phone TEXT,
        family_members INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_number TEXT UNIQUE,
        status TEXT DEFAULT 'available'
    )
    ''')
    
    # ✅ FIXED: Complete payments table creation
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flat_number TEXT,
        resident_name TEXT,
        amount REAL DEFAULT 0,
        amount_due REAL DEFAULT 5000,
        payment_date TEXT,
        status TEXT DEFAULT 'pending',
        transaction_id TEXT,
        month_year TEXT DEFAULT '2026-03'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        date_posted TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_flat TEXT,
        subject TEXT,
        description TEXT,
        date_submitted TEXT,
        status TEXT DEFAULT 'open'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        votes1 INTEGER DEFAULT 0,
        votes2 INTEGER DEFAULT 0,
        votes3 INTEGER DEFAULT 0,
        date_posted TEXT,
        flat_number_voted TEXT DEFAULT NULL
    )
    ''')

    # 2. ✅ MIGRATE/ENSURE ALL COLUMNS EXIST
    columns_to_check = {
        'maintenance_payments': ['flat_number', 'resident_name', 'amount', 'amount_due', 'payment_date', 'status', 'transaction_id', 'month_year'],
        'complaints': ['resident_flat', 'subject', 'description', 'date_submitted', 'status'],
        'polls': ['question', 'option1', 'option2', 'option3', 'votes1', 'votes2', 'votes3', 'date_posted', 'flat_number_voted']
    }
    
    for table, cols in columns_to_check.items():
        for col in cols:
            cursor.execute(f"PRAGMA table_info({table})")
            if not any(row[1] == col for row in cursor.fetchall()):
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {'TEXT' if 'name' in col or 'date' in col or 'status' in col or 'flat' in col else 'REAL' if 'amount' in col else 'INTEGER'}")

    # 3. ADD SAMPLE DATA
    cursor.execute("SELECT COUNT(*) FROM residents")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO residents (name, flat_number, phone, family_members) VALUES (?, ?, ?, ?)",
                          [('Manali Jambhale', '101', '9876543210', 4),
                           ('Rajesh Sharma', '102', '9876543211', 3),
                           ('Priya Patel', '201', '9876543212', 2)])

    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 11):
            cursor.execute("INSERT INTO parking_slots (slot_number, status) VALUES (?, ?)", (f"P{i}", 'available'))

    conn.commit()
    conn.close()

init_database()

def safe_read_sql(query, conn):
    try:
        df = pd.read_sql(query, conn)
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

def load_data():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    residents = safe_read_sql("SELECT * FROM residents", conn)
    parking = safe_read_sql("SELECT * FROM parking_slots", conn)
    payments = safe_read_sql("SELECT * FROM maintenance_payments ORDER BY id DESC LIMIT 50", conn)
    notices = safe_read_sql("SELECT * FROM notices ORDER BY id DESC", conn)
    complaints = safe_read_sql("SELECT * FROM complaints ORDER BY id DESC", conn)
    polls = safe_read_sql("SELECT * FROM polls ORDER BY id DESC", conn)
    conn.close()
    return residents, parking, payments, notices, complaints, polls

def check_login(username, password):
    users = {"secretary": "admin123", "member": "pass123"}
    return username if username in users and users[username] == password else None

if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'role' not in st.session_state: 
    st.session_state.role = None
if 'current_flat' not in st.session_state:
    st.session_state.current_flat = None

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card' style='max-width:450px; margin:0 auto;'><h2 style='color:#2c3e50;text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🚀 Dashboard", key="login_unique"):
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = role
                st.rerun()
            else:
                st.error("❌ Wrong credentials!")
        st.markdown("<div style='text-align:center;color:#666;'>Secretary: secretary/admin123<br>Member: member/pass123</div></div>", unsafe_allow_html=True)

else:
    residents, parking, payments, notices, complaints, polls = load_data()
    
    if st.session_state.role == "member" and not st.session_state.current_flat:
        st.info("👤 **Please select your flat to vote in polls**")
        flat_options = residents['flat_number'].tolist() if not residents.empty and 'flat_number' in residents.columns else []
        if flat_options:
            selected_flat = st.selectbox("Select your flat:", flat_options, key="flat_select")
            if st.button("✅ Confirm Flat", key="confirm_flat"):
                st.session_state.current_flat = selected_flat
                st.rerun()
    
    col1, col2 = st.columns([3,1])
    with col1: 
        st.markdown(f"<h1>🏢 Society Dashboard</h1><p>Welcome, <strong>{st.session_state.username.title()}</strong>{' - Flat: ' + st.session_state.current_flat if st.session_state.current_flat else ''}</p>", unsafe_allow_html=True)
    with col2: 
        if st.button("🚪 Logout", key="logout_unique2"): 
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    
    st.image("https://images.unsplash.com/photo-1600585154340-be6161a56a0c?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80", use_container_width=True)
    
    with st.sidebar:
        st.markdown("<h3 style='color:white;'>📊 Stats</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: 
            st.metric("👥 Residents", len(residents))
            st.metric("📢 Notices", len(notices))
            st.metric("📊 Polls", len(polls))
        with col2:
            parking_used = len(parking[parking['status']=='occupied']) if not parking.empty and 'status' in parking.columns else 0
            st.metric("🚗 Parking Used", parking_used)
            st.metric("⚠️ Complaints", len(complaints))
            paid_count = len(payments[payments['status']=='paid']) if not payments.empty and 'status' in payments.columns else 0
            st.metric("💰 Paid", paid_count)
    
    tabs = ["👥 Residents", "🚗 Parking", "💰 Payments", "💳 Maintenance", "📢 Notices", "⚠️ Complaints", "📊 Polls"]
    if st.session_state.role == "secretary":
        tabs.append("📈 Analytics")
    
    selected_tab = st.tabs(tabs)
    
    with selected_tab[0]:
        st.subheader("📋 Residents")
        if not residents.empty:
            st.dataframe(residents, height=500, use_container_width=True)
    
    with selected_tab[1]:
        st.subheader("🚗 Parking")
        col1, col2 = st.columns(2)
        with col1: 
            if not parking.empty and 'status' in parking.columns:
                available = len(parking[parking['status']=='available'])
                occupied = len(parking[parking['status']=='occupied'])
                fig = px.pie(values=[available, occupied], names=['Available','Occupied'], hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        with col2: 
            if not parking.empty:
                st.dataframe(parking, height=400)
    
    with selected_tab[2]:
        st.subheader("💰 All Payments")
        if not payments.empty:
            st.dataframe(payments, height=500, use_container_width=True)
        else:
            st.info("📝 No payments recorded")
    
    with selected_tab[3]:
        st.subheader("💳 Maintenance Payment")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 📱 **Scan & Pay**")
            upi_id = "jambhalemanali13@okicici"
            payee_name = "Society Maintenance"
            upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&cu=INR"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(upi_link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            st.image(f"data:image/png;base64,{img_str}", caption=f"🏦 {upi_id}", width=300)
            
            amount = st.number_input("Enter Amount (₹)", min_value=10.0, value=5000.0, step=100.0, key="pay_amount_maintenance")
            flat_number = st.text_input("Flat No (101, 102, 201 etc.):", key="flat_number_input")
            
            selected_name = "Unknown Resident"
            if flat_number and not residents.empty and 'flat_number' in residents.columns and 'name' in residents.columns:
                resident = residents[residents['flat_number'] == flat_number]
                if not resident.empty:
                    selected_name = resident.iloc[0]['name']
                    st.success(f"✅ **Resident Found:** {selected_name}")
                else:
                    st.warning("⚠️ Flat not found - will use entered details")
            
            if st.button("✅ Record Payment", key="record_payment_maintenance"):
                if amount > 0 and flat_number:
                    try:
                        conn = sqlite3.connect(DB_FILE, timeout=20.0)
                        cursor = conn.cursor()
                        txn_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        month_year = datetime.now().strftime('%Y-%m')
                        
                        # ✅ FIXED: Safe INSERT with all columns guaranteed to exist
                        cursor.execute("""
                            INSERT INTO maintenance_payments 
                            (flat_number, resident_name, amount, amount_due, payment_date, status, transaction_id, month_year)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (flat_number, selected_name, float(amount), 5000.0, date, 'paid', txn_id, month_year))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ ₹{amount:,.0f} Payment recorded for Flat {flat_number}!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Database error: {str(e)}")
                else:
                    st.error("❌ Please enter valid amount and flat number")
        
        with col2:
            st.markdown("### 📄 Recent Payments")
            if not payments.empty:
                st.dataframe(payments.head(10), height=400)

    # Notices Tab
    with selected_tab[4]:
        st.subheader("📢 Notice Board")
        if st.session_state.role == "secretary":
            with st.expander("➕ Post New Notice"):
                title = st.text_input("Title")
                desc = st.text_area("Description", height=100)
                if st.button("Post Notice", type="primary"):
                    conn = sqlite3.connect(DB_FILE, timeout=20.0)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO notices (title, description, date_posted) VALUES (?, ?, ?)",
                                 (title, desc, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    conn.close()
                    st.success("✅ Notice posted!")
                    st.rerun()
        
        if not notices.empty:
            for notice in notices.itertuples():
                with st.expander(f"📋 {notice.title}"):
                    st.write(notice.description)
        else:
            st.info("📌 No notices")

    # Complaints Tab  
    with selected_tab[5]:
        st.subheader("⚠️ Complaints")
        with st.expander("📝 Submit Complaint"):
            col1, col2 = st.columns(2)
            with col1: subject = st.text_input("Subject")
            with col2: flat = st.session_state.current_flat or st.text_input("Flat")
            desc = st.text_area("Description")
            if st.button("Submit", type="primary"):
                if subject and desc and flat:
                    conn = sqlite3.connect(DB_FILE, timeout=20.0)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO complaints (resident_flat, subject, description, date_submitted) VALUES (?, ?, ?, ?)",
                                 (flat, subject, desc, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    conn.close()
                    st.success("✅ Complaint submitted!")
                    st.rerun()
        
        if not complaints.empty:
            for comp in complaints.itertuples():
                with st.expander(f"🔴 {comp.subject} - Flat {comp.resident_flat}"):
                    st.write(comp.description)
        else:
            st.info("✅ No complaints")

    # Polls Tab
    with selected_tab[6]:
        st.subheader("📊 Polls")
        if st.session_state.role == "secretary":
            with st.expander("➕ Create Poll"):
                q = st.text_input("Question")
                o1, o2, o3 = st.text_input("Option 1"), st.text_input("Option 2"), st.text_input("Option 3")
                if st.button("Create Poll", type="primary"):
                    if q and o1:
                        conn = sqlite3.connect(DB_FILE, timeout=20.0)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO polls (question, option1, option2, option3, date_posted) VALUES (?, ?, ?, ?, ?)",
                                     (q, o1, o2 or "", o3 or "", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                        conn.commit()
                        conn.close()
                        st.success("✅ Poll created!")
                        st.rerun()
        
        if not polls.empty:
            for poll in polls.itertuples():
                st.markdown(f"**{poll.question}**")
                col1, col2, col3 = st.columns(3)
                with col1: st.metric(poll.option1 or "Option 1", poll.votes1 or 0)
                with col2: st.metric(poll.option2 or "Option 2", poll.votes2 or 0)
                with col3: st.metric(poll.option3 or "Option 3", poll.votes3 or 0)
                st.divider()

    # Analytics (Secretary only)
    if st.session_state.role == "secretary" and len(tabs) > 7:
        with selected_tab[7]:
            st.subheader("📈 Analytics")
            col1, col2 = st.columns(2)
            with col1:
                if not residents.empty and 'family_members' in residents.columns:
                    fig = px.histogram(residents, x='family_members')
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if not parking.empty and 'status' in parking.columns:
                    fig = px.pie(values=[len(parking[parking['status']=='available']), 
                                       len(parking[parking['status']=='occupied'])],
                               names=['Available', 'Occupied'])
                    st.plotly_chart(fig, use_container_width=True)
