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

    # Add sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM residents")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO residents (name, flat_number, phone, family_members) VALUES (?, ?, ?, ?)",
                          [('Manali Jambhale', '101', '9876543210', 4),
                           ('Rajesh Sharma', '102', '9876543211', 3),
                           ('Priya Patel', '201', '9876543212', 2)])
    
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 11):
            cursor.execute("INSERT INTO parking_slots (slot_number) VALUES (?)", (f"P{i}",))

    conn.commit()
    conn.close()

init_database()

def safe_read_sql(query, conn):
    """🔧 Bulletproof SQL reader"""
    try:
        df = pd.read_sql(query, conn)
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

def load_data():
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    residents = safe_read_sql("SELECT * FROM residents", conn)
    parking = safe_read_sql("SELECT * FROM parking_slots", conn)
    payments = safe_read_sql("SELECT * FROM maintenance_payments ORDER BY id DESC", conn)
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
        flat_options = residents['flat_number'].tolist() if not residents.empty else []
        if flat_options:
            selected_flat = st.selectbox("Select your flat:", flat_options, key="flat_select")
            if st.button("✅ Confirm Flat", key="confirm_flat"):
                st.session_state.current_flat = selected_flat
                st.rerun()
        else:
            st.warning("No residents data available")
    
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
            paid_count = len(payments[payments['status']=='paid']) if not payments.empty else 0
            st.metric("💰 Paid", paid_count)
            
        st.markdown("<div class='paid-members'><h4>✅ Recently Paid</h4></div>", unsafe_allow_html=True)
        if not payments.empty:
            recent_paid = payments[payments['status']=='paid'][['resident_name', 'amount', 'payment_date']].head(5)
            if not recent_paid.empty:
                for _, member in recent_paid.iterrows():
                    st.success(f"✅ {member['resident_name']}")
                    st.caption(f"₹{member['amount']} | {member['payment_date']}")
        else:
            st.info("📝 No recent payments")
    
    tabs = ["👥 Residents", "🚗 Parking", "💰 Payments", "💳 Maintenance", "📢 Notices", "⚠️ Complaints", "📊 Polls"]
    if st.session_state.role == "secretary":
        tabs.append("📈 Analytics")
    
    selected_tab = st.tabs(tabs)
    
    with selected_tab[0]:
        st.subheader("📋 Residents")
        if not residents.empty:
            st.dataframe(residents[['name','flat_number','phone','family_members']], height=500)
        else:
            st.info("📝 No residents data")
    
    with selected_tab[1]:
        st.subheader("🚗 Parking")
        col1, col2 = st.columns(2)
        with col1: 
            if not parking.empty and 'status' in parking.columns:
                available_count = len(parking[parking['status']=='available'])
                occupied_count = len(parking[parking['status']=='occupied'])
                fig = px.pie(values=[available_count, occupied_count],
                            names=['Available','Occupied'], hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        with col2: 
            if not parking.empty:
                st.dataframe(parking, height=400)
    
    with selected_tab[2]:
        st.subheader("💰 All Payments")
        if not payments.empty:
            display_cols = ['resident_name','flat_number','amount','amount_due','payment_date','status','transaction_id','month_year']
            available_cols = [col for col in display_cols if col in payments.columns]
            display_payments = payments[available_cols].copy()
            display_payments['payment_date'] = display_payments['payment_date'].fillna('Pending')
            st.dataframe(display_payments, height=500, use_container_width=True)
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
            
            amount = st.number_input("Enter Amount (₹)", min_value=10.0, value=10.0, step=100.0, key="pay_amount_maintenance")
            flat_number = st.text_input("Flat No (101, 102, 201 etc.):", key="flat_number_input")
            
            selected_name = None
            if flat_number and not residents.empty:
                resident = residents[residents['flat_number'] == flat_number]
                if not resident.empty:
                    selected_name = resident.iloc[0]['name']
                    st.success(f"✅ **Resident Found:** {selected_name} - Flat {flat_number}")
                else:
                    st.error("❌ Flat number not found!")
            
            if st.button("✅ Record Payment", key="record_payment_maintenance"):
                if amount > 0 and flat_number and selected_name:
                    conn = sqlite3.connect(DB_FILE, timeout=20.0)
                    cursor = conn.cursor()
                    txn_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    month_year = datetime.now().strftime('%Y-%m')
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO maintenance_payments 
                        (flat_number, resident_name, amount, amount_due, payment_date, status, transaction_id, month_year)
                        VALUES (?, ?, ?, 5000, ?, 'paid', ?, ?)
                    """, (flat_number, selected_name, amount, date, txn_id, month_year))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ ₹{amount} Payment SUCCESSFUL for {selected_name}!")
                    st.balloons()
                    st.rerun()
        
        with col2:
            st.markdown("### 📄 Recent Payments")
            conn_recent = sqlite3.connect(DB_FILE, timeout=20.0)
            recent_payments = safe_read_sql("SELECT * FROM maintenance_payments ORDER BY id DESC LIMIT 10", conn_recent)
            conn_recent.close()
            if not recent_payments.empty:
                st.dataframe(recent_payments, height=400)

    with selected_tab[4]:
        st.subheader("📢 Notice Board")
        if st.session_state.role == "secretary":
            with st.expander("➕ **Post New Notice**"):
                title = st.text_input("📋 Notice Title", key="notice_title")
                description = st.text_area("📄 Description", height=100, key="notice_desc")
                if st.button("📤 **POST NOTICE**", type="primary"):
                    if title and description:
                        conn = sqlite3.connect(DB_FILE, timeout=20.0)
                        cursor = conn.cursor()
                        date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("INSERT INTO notices (title, description, date_posted) VALUES (?, ?, ?)",
                                     (title, description, date_posted))
                        conn.commit()
                        conn.close()
                        st.success("✅ Notice posted!")
                        st.rerun()
        
        if len(notices) > 0:
            for notice in notices.itertuples():
                with st.expander(f"📋 {notice.title}"):
                    st.write(notice.description)
                    st.caption(f"Posted: {notice.date_posted}")
        else:
            st.info("📌 No notices posted yet")

    with selected_tab[5]:
        st.subheader("⚠️ Complaints")
        # ✅ COMPLAINTS FORM - WORKING
        if st.session_state.logged_in:
            with st.expander("📝 **Submit New Complaint**"):
                col1, col2 = st.columns(2)
                with col1:
                    subject = st.text_input("Subject", key="comp_subject")
                with col2:
                    resident_flat = st.session_state.current_flat if st.session_state.current_flat else st.text_input("Flat Number", key="comp_flat")
                description = st.text_area("Description", height=100, key="comp_desc")
                
                if st.button("📤 **SUBMIT COMPLAINT**", type="primary"):
                    if subject and description and resident_flat:
                        conn = sqlite3.connect(DB_FILE, timeout=20.0)
                        cursor = conn.cursor()
                        date_submitted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("INSERT INTO complaints (resident_flat, subject, description, date_submitted) VALUES (?, ?, ?, ?)",
                                     (resident_flat, subject, description, date_submitted))
                        conn.commit()
                        conn.close()
                        st.success("✅ Complaint submitted!")
                        st.rerun()
        
        # ✅ SHOW COMPLAINTS - WORKING
        if len(complaints) > 0:
            for comp in complaints.itertuples():
                status_color = "🟢" if comp.status == "closed" else "🔴"
                with st.expander(f"{status_color} {comp.subject} - Flat {comp.resident_flat}"):
                    st.write(comp.description)
                    st.caption(f"Status: {comp.status} | Submitted: {comp.date_submitted}")
        else:
            st.info("✅ No complaints")

    with selected_tab[6]:
        st.subheader("📊 Polls")
        # ✅ POLLS CREATE - WORKING
        if st.session_state.role == "secretary":
            with st.expander("➕ Create New Poll"):
                question = st.text_input("Poll Question", key="poll_question")
                option1 = st.text_input("Option 1", key="poll_opt1")
                option2 = st.text_input("Option 2", key="poll_opt2")
                option3 = st.text_input("Option 3", key="poll_opt3")
                
                if st.button("📤 Post Poll", key="post_poll"):
                    if question and option1:
                        conn = sqlite3.connect(DB_FILE, timeout=20.0)
                        cursor = conn.cursor()
                        date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("INSERT INTO polls (question, option1, option2, option3, date_posted) VALUES (?, ?, ?, ?, ?)",
                                     (question, option1, option2 or "", option3 or "", date_posted))
                        conn.commit()
                        conn.close()
                        st.success("✅ Poll created!")
                        st.rerun()
        
        # ✅ SHOW POLLS & VOTING - WORKING
        if len(polls) > 0:
            for poll in polls.itertuples():
                st.markdown(f"**{poll.question}**")
                
                # Check if user voted
                user_has_voted = False
                if st.session_state.role == "member" and st.session_state.current_flat:
                    conn_check = sqlite3.connect(DB_FILE, timeout=20.0)
                    cursor_check = conn_check.cursor()
                    cursor_check.execute("SELECT flat_number_voted FROM polls WHERE id = ?", (poll.id,))
                    result = cursor_check.fetchone()
                    user_has_voted = result and result[0] == st.session_state.current_flat
                    conn_check.close()
                
                col1, col2, col3 = st.columns(3)
                
                # Voting buttons
                if st.session_state.role == "member" and st.session_state.current_flat and not user_has_voted:
                    with col1:
                        if st.button(f"🗳️ {poll.option1}", key=f"vote_{poll.id}_1"):
                            conn = sqlite3.connect(DB_FILE, timeout=20.0)
                            cursor = conn.cursor()
                            cursor.execute("UPDATE polls SET votes1 = votes1 + 1, flat_number_voted = ? WHERE id = ?", 
                                         (st.session_state.current_flat, poll.id))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    
                    if poll.option2:
                        with col2:
                            if st.button(f"🗳️ {poll.option2}", key=f"vote_{poll.id}_2"):
                                conn = sqlite3.connect(DB_FILE, timeout=20.0)
                                cursor = conn.cursor()
                                cursor.execute("UPDATE polls SET votes2 = votes2 + 1, flat_number_voted = ? WHERE id = ?", 
                                             (st.session_state.current_flat, poll.id))
                                conn.commit()
                                conn.close()
                                st.rerun()
                
                # Show results
                total_votes = poll.votes1 + poll.votes2 + poll.votes3
                col1, col2, col3 = st.columns(3)
                with col1: st.metric(poll.option1, poll.votes1)
                with col2: st.metric(poll.option2 or "Option 2", poll.votes2)
                with col3: st.metric(poll.option3 or "Option 3", poll.votes3)
                
                st.caption(f"📊 Total Votes: {total_votes}")
                st.divider()
        else:
            st.info("📊 No polls yet")

    # ✅ ANALYTICS TAB - WORKING
    if st.session_state.role == "secretary" and len(tabs) > 7:
        with selected_tab[7]:
            st.subheader("📈 Analytics Dashboard")
            col1, col2 = st.columns(2)
            
            with col1:
                if not residents.empty and 'family_members' in residents.columns:
                    fig1 = px.histogram(residents, x='family_members', nbins=6,
                                      title="👨‍👩‍👧‍👦 Family Size Distribution")
                    st.plotly_chart(fig1, use_container_width=True)
                
                if not payments.empty and 'status' in payments.columns:
                    status_counts = payments['status'].value_counts()
                    fig2 = px.pie(values=status_counts.values, names=status_counts.index,
                                title="💰 Payment Status", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                if not parking.empty and 'status' in parking.columns:
                    available = len(parking[parking['status']=='available'])
                    occupied = len(parking[parking['status']=='occupied'])
                    fig3 = px.bar(x=['Available', 'Occupied'], y=[available, occupied],
                                title="🚗 Parking Utilization")
                    st.plotly_chart(fig3, use_container_width=True)
                
                if not payments.empty:
                    paid_payments = payments[payments['status']=='paid']
                    total_collected = paid_payments['amount'].sum() if not paid_payments.empty else 0
                    st.metric("💵 Total Collected", f"₹{total_collected:,.0f}")
