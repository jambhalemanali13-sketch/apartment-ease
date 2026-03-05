import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import time
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Society Management", layout="wide", page_icon="🏠")

# --- STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    .login-card {background: rgba(255,255,255,0.98); border-radius: 25px; padding: 3rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);}
    .stButton > button {background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white !important; border-radius: 30px; font-weight: 600;}
    .receipt-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 20px; padding: 2rem;}
    .paid-members {background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 1rem; border-radius: 15px; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

DB_FILE = 'society.db'

# --- DATABASE FUNCTIONS ---
def init_database():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    cursor = conn.cursor()
    
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

    conn.commit()
    conn.close()

# IMPORTANT: Re-initializing to ensure the cloud DB matches the code
init_database()

def load_data():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    # Using try-except to handle cases where tables might be empty or missing columns
    try:
        residents = pd.read_sql("SELECT * FROM residents", conn)
        parking = pd.read_sql("SELECT * FROM parking_slots", conn)
        payments = pd.read_sql("SELECT * FROM maintenance_payments ORDER BY payment_date DESC", conn)
        notices = pd.read_sql("SELECT * FROM notices ORDER BY date_posted DESC", conn)
        complaints = pd.read_sql("SELECT * FROM complaints ORDER BY date_submitted DESC", conn)
        polls = pd.read_sql("SELECT * FROM polls ORDER BY date_posted DESC", conn)
    except Exception:
        # If DB is corrupt or outdated, return empty DataFrames to prevent crash
        residents = pd.DataFrame(columns=['id','name','flat_number','phone','family_members'])
        parking = pd.DataFrame(columns=['id','slot_number','status'])
        payments = pd.DataFrame(columns=['id','flat_number','resident_name','amount','amount_due','payment_date','status','transaction_id','month_year'])
        notices = pd.DataFrame(columns=['id','title','description','date_posted'])
        complaints = pd.DataFrame(columns=['id','resident_flat','subject','description','date_submitted','status'])
        polls = pd.DataFrame(columns=['id','question','option1','option2','option3','votes1','votes2','votes3','date_posted','flat_number_voted'])
    finally:
        conn.close()
    return residents, parking, payments, notices, complaints, polls

def check_login(username, password):
    users = {"secretary": "admin123", "member": "pass123"}
    return username if username in users and users[username] == password else None

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'role' not in st.session_state: 
    st.session_state.role = None
if 'current_flat' not in st.session_state:
    st.session_state.current_flat = None

# --- LOGIN PAGE ---
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

# --- LOGGED IN DASHBOARD ---
else:
    residents, parking, payments, notices, complaints, polls = load_data()
    
    if st.session_state.role == "member" and not st.session_state.current_flat:
        st.info("👤 **Please select your flat to continue**")
        flat_options = residents['flat_number'].tolist() if not residents.empty else []
        if flat_options:
            selected_flat = st.selectbox("Select your flat:", flat_options, key="flat_select")
            if st.button("✅ Confirm Flat"):
                st.session_state.current_flat = selected_flat
                st.rerun()
        else:
            st.warning("No residents data available. Please ask Secretary to add residents.")
    
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
        col_s1, col_s2 = st.columns(2)
        with col_s1: 
            st.metric("👥 Residents", len(residents))
            st.metric("📢 Notices", len(notices))
            st.metric("📊 Polls", len(polls))
        with col_s2:
            st.metric("🚗 Parking Used", len(parking[parking['status']=='occupied']))
            st.metric("⚠️ Complaints", len(complaints))
            st.metric("💰 Paid", len(payments[payments['status']=='paid']))
            
        st.markdown("<div class='paid-members'><h4>✅ Recently Paid</h4></div>", unsafe_allow_html=True)
        recent_paid = payments[payments['status']=='paid'].head(5)
        if not recent_paid.empty:
            for _, member in recent_paid.iterrows():
                st.success(f"✅ {member['resident_name']}")
                st.caption(f"₹{member['amount']} | {member['payment_date']}")
        else:
            st.info("📝 No recent payments")

    tabs = st.tabs(["👥 Residents", "🚗 Parking", "💰 Payments", "💳 Maintenance", "📢 Notices", "⚠️ Complaints", "📊 Polls", "📈 Analytics"])
    
    with tabs[0]:
        st.subheader("📋 Residents")
        st.dataframe(residents, use_container_width=True)
    
    with tabs[1]:
        st.subheader("🚗 Parking Status")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if not parking.empty:
                fig_p = px.pie(values=[len(parking[parking['status']=='available']), len(parking[parking['status']=='occupied'])],
                            names=['Available','Occupied'], hole=0.4, color_discrete_sequence=['#4CAF50', '#FF6B6B'])
                st.plotly_chart(fig_p, use_container_width=True)
        with col_p2:
            st.dataframe(parking, use_container_width=True)

    with tabs[2]:
        st.subheader("💰 Payment History")
        st.dataframe(payments, use_container_width=True)

    with tabs[3]:
        st.subheader("💳 Maintenance Payment")
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
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
            st.image(f"data:image/png;base64,{img_str}", caption=f"🏦 {upi_id}", width=250)
            
            amount = st.number_input("Enter Amount (₹)", min_value=1.0, value=5000.0)
            flat_number = st.text_input("Enter Flat No:")
            
            if st.button("✅ Record Payment"):
                resident = residents[residents['flat_number'] == flat_number]
                if not resident.empty:
                    name = resident.iloc[0]['name']
                    txn_id = f"TXN{int(time.time())}"
                    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO maintenance_payments (flat_number, resident_name, amount, payment_date, status, transaction_id, month_year) VALUES (?,?,?,?,?,?,?)",
                               (flat_number, name, amount, date, 'paid', txn_id, date[:7]))
                    conn.commit()
                    conn.close()
                    st.success("Payment Recorded!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Flat not found!")

    with tabs[4]:
        st.subheader("📢 Notice Board")
        if st.session_state.role == "secretary":
            with st.expander("➕ Add Notice"):
                t = st.text_input("Title")
                d = st.text_area("Content")
                if st.button("Post"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.cursor().execute("INSERT INTO notices (title, description, date_posted) VALUES (?,?,?)", (t, d, datetime.now().strftime('%Y-%m-%d')))
                    conn.commit()
                    conn.close()
                    st.rerun()
        for _, n in notices.iterrows():
            st.info(f"**{n['title']}** ({n['date_posted']})\n\n{n['description']}")

    with tabs[5]:
        st.subheader("⚠️ Complaints")
        with st.expander("📝 File a Complaint"):
            sub = st.text_input("Subject")
            desc = st.text_area("Details")
            if st.button("Submit"):
                f_no = st.session_state.current_flat if st.session_state.current_flat else "Admin"
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute("INSERT INTO complaints (resident_flat, subject, description, date_submitted) VALUES (?,?,?,?)", (f_no, sub, desc, datetime.now().strftime('%Y-%m-%d')))
                conn.commit()
                conn.close()
                st.success("Submitted!")
                st.rerun()
        st.dataframe(complaints, use_container_width=True)

    with tabs[6]:
        st.subheader("📊 Polls")
        if st.session_state.role == "secretary":
            with st.expander("➕ Create Poll"):
                q = st.text_input("Question")
                o1 = st.text_input("Opt 1")
                o2 = st.text_input("Opt 2")
                if st.button("Create"):
                    conn = sqlite3.connect(DB_FILE)
                    conn.cursor().execute("INSERT INTO polls (question, option1, option2, date_posted) VALUES (?,?,?,?)", (q, o1, o2, datetime.now().strftime('%Y-%m-%d')))
                    conn.commit()
                    conn.close()
                    st.rerun()
        for _, p in polls.iterrows():
            st.write(f"**{p['question']}**")
            col_v1, col_v2 = st.columns(2)
            col_v1.metric(str(p['option1']), p['votes1'])
            col_v2.metric(str(p['option2']), p['votes2'])

    with tabs[7]:
        st.subheader("📈 Analytics")
        if not payments.empty:
            fig_a = px.bar(payments, x='month_year', y='amount', title="Collections over Time")
            st.plotly_chart(fig_a, use_container_width=True)
        else:
            st.info("No payment data to analyze.")
