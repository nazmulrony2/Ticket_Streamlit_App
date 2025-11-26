# app.py
# Ticket Distribution App
# Features:
# - Max 10 tickets per employee
# - First buy → auto-save
# - Repeat buy → warning + remark + approval
# - Report: Only admins, with Excel download
# - Login session: 2 hours max

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
import io  # For Excel in-memory download

# === CONFIGURATION ===
st.set_page_config(page_title="টিকেট বিতরণ", layout="centered")
DB_NAME = "ticket_distribution.db"
MAX_TICKETS_PER_EMPLOYEE = 10
TOTAL_TICKETS = 1000
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}
SESSION_TIMEOUT = timedelta(hours=2)  # 2-hour session

# === CSS STYLING ===
st.markdown("""
<style>
    html, body, .stApp { 
        background: #eef2f7 !important; 
        font-family: 'Arial', sans-serif; 
    }

    /* Main container gradient */
    .block-container { 
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); 
        padding: 1rem !important; 
        border-radius: 15px; 
    }

    /* Headings */
    h1, h2, h3 { 
        color: #0f172a !important; 
        text-align: center !important; 
    }

    /* Buttons */
    .stButton > button {
        background: #2563eb !important; 
        color: white !important; 
        font-weight: bold !important;
        border-radius: 12px !important; 
        padding: 0.8rem !important; 
        width: 100% !important;
        font-size: 1.1rem !important; 
        border: none !important;
        box-shadow: 0 3px 10px rgba(37, 99, 235, 0.2) !important;
    }

    .stButton > button:hover { 
        background: #1e40af !important; 
    }

    /* Cards */
    .metric-card {
        background: #ffffff !important; 
        padding: 1.2rem !important; 
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08) !important; 
        text-align: center !important; 
        margin: 0.5rem !important;
    }

    /* Badge */
    .seller-badge {
        background: #fde047 !important; 
        color: #1e293b !important; 
        padding: 0.4rem 0.8rem !important;
        border-radius: 20px !important; 
        font-weight: bold !important;
    }

    /* Footer */
    .footer {
        text-align: center !important; 
        margin-top: 2rem !important; 
        color: #64748b !important;
        font-size: 0.9rem !important; 
        padding: 1rem !important; 
        background: #ffffff !important; 
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }

    /* Warning Box */
    .warning-box {
        background: #fef9c3 !important; 
        border-left: 4px solid #facc15 !important;
        padding: 1rem !important; 
        border-radius: 8px !important; 
        margin: 1rem 0 !important;
    }

    /* Mobile Optimization */
    @media (max-width: 600px) {
        .stButton > button { 
            font-size: 1rem !important; 
            padding: 0.7rem !important; 
        }
    }
</style>
""", unsafe_allow_html=True)


# === PASSWORD & DB FUNCTIONS ===
def hash_password(pw):
    """Secure password hashing"""
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    """Create all tables"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (employee_id TEXT PRIMARY KEY, employee_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (employee_id TEXT PRIMARY KEY, total_quantity INTEGER DEFAULT 0, first_timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 employee_id TEXT, employee_name TEXT, quantity INTEGER,
                 seller TEXT, remark TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def ensure_default_admin():
    """Always have default admin"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed = hash_password(DEFAULT_ADMIN["password"])
    c.execute("INSERT OR IGNORE INTO admins VALUES (?, ?)", (DEFAULT_ADMIN["username"], hashed))
    conn.commit()
    conn.close()

def load_admins_from_excel():
    """Load extra admins from file"""
    if os.path.exists("admins.xlsx"):
        df = pd.read_excel("admins.xlsx")
        if 'username' in df.columns and 'password' in df.columns:
            df = df[['username', 'password']].dropna()
            df['username'] = df['username'].astype(str).str.strip()
            df['password'] = df['password'].astype(str).apply(hash_password)
            df = df[df['username'].str.lower() != 'admin']
            conn = sqlite3.connect(DB_NAME)
            for _, row in df.iterrows():
                conn.execute("INSERT OR REPLACE INTO admins VALUES (?, ?)", (row['username'], row['password']))
            conn.commit()
            conn.close()

def load_employees():
    """Load employees once"""
    if os.path.exists("employees.xlsx") and not os.path.exists("employees_loaded.xlsx"):
        df = pd.read_excel("employees.xlsx")
        if 'Employee ID' in df.columns and 'Employee Name' in df.columns:
            df = df[['Employee ID', 'Employee Name']].dropna()
            df.columns = ['employee_id', 'employee_name']
            df['employee_id'] = df['employee_id'].astype(str).str.strip()
            conn = sqlite3.connect(DB_NAME)
            df.to_sql('employees', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            os.rename("employees.xlsx", "employees_loaded.xlsx")

def check_login(username, password):
    """Verify login"""
    hashed = hash_password(password)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE username=? AND password=?", (username, hashed))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_admin(username):
    """Check if user is admin"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_employee(emp_id):
    """Get employee name"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT employee_name FROM employees WHERE employee_id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_total_tickets(emp_id):
    """Get total tickets bought"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_quantity FROM tickets WHERE employee_id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_sale(emp_id, name, qty, seller, remark=""):
    """Save sale and update total"""
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO sales (employee_id, employee_name, quantity, seller, remark, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (emp_id, name, qty, seller, remark, ts))
    current = get_total_tickets(emp_id)
    new_total = current + qty
    if current == 0:
        c.execute("INSERT INTO tickets VALUES (?, ?, ?)", (emp_id, new_total, ts))
    else:
        c.execute("UPDATE tickets SET total_quantity=? WHERE employee_id=?", (new_total, emp_id))
    conn.commit()
    conn.close()

def get_stats():
    """Get summary stats"""
    conn = sqlite3.connect(DB_NAME)
    total_emp = pd.read_sql("SELECT COUNT(*) FROM employees", conn).iloc[0,0]
    buyers = pd.read_sql("SELECT COUNT(*) FROM tickets", conn).iloc[0,0]
    sold = pd.read_sql("SELECT COALESCE(SUM(total_quantity),0) FROM tickets", conn).iloc[0,0]
    remaining = max(0, TOTAL_TICKETS - sold)
    conn.close()
    return total_emp, buyers, sold, remaining

def get_seller_stats():
    """Get seller leaderboard"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT seller, SUM(quantity) as tickets_sold FROM sales GROUP BY seller ORDER BY tickets_sold DESC", conn)
    conn.close()
    return df

# === EXCEL DOWNLOAD FUNCTION ===
def to_excel(df, sheet_name="Sheet1"):
    """Convert DataFrame to Excel in memory"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output

# === APP INITIALIZATION ===
init_db()
ensure_default_admin()
load_admins_from_excel()
load_employees()

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

# Check session timeout
if st.session_state.logged_in and st.session_state.login_time:
    if datetime.now() - st.session_state.login_time > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.login_time = None
        st.session_state.page = "login"
        st.rerun()

page = st.session_state.page

# === LOGIN PAGE ===
if page == "login":
    st.markdown("<h1>টিকেট বিক্রয়</h1>", unsafe_allow_html=True)
    st.info("Default: **admin / admin123**")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if check_login(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.login_time = datetime.now()
                st.session_state.page = "home"
                st.success("Login successful! Session: 2 hours")
                st.rerun()
            else:
                st.error("Wrong username or password")

# === HOME PAGE ===
elif page == "home" and st.session_state.logged_in:
    st.markdown(f"<h2>Welcome, {st.session_state.username}!</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("Report"): st.session_state.page = "report"; st.rerun()
        if st.button("Admin"): st.session_state.page = "admin"; st.rerun()
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()

    with col1:
        st.markdown("---")
        st.subheader("New Ticket Sale")

        emp_id = st.text_input("Employee ID *", placeholder="210679", key="emp_id_input")
        qty = st.number_input("Ticket Quantity *", min_value=1, max_value=10, step=1, key="qty_input")

        if st.button("Check & Sell", type="primary"):
            if not emp_id.strip():
                st.error("Enter ID")
            else:
                name = get_employee(emp_id)
                if not name:
                    st.error("Employee not found")
                else:
                    current = get_total_tickets(emp_id)
                    new_total = current + qty
                    if new_total > MAX_TICKETS_PER_EMPLOYEE:
                        st.error(f"Max {MAX_TICKETS_PER_EMPLOYEE} tickets. Current: {current}")
                    elif current == 0:
                        add_sale(emp_id, name, qty, st.session_state.username)
                        st.success(f"{name} bought {qty} ticket(s)!")
                        st.rerun()
                    else:
                        st.session_state.pending_sale = {
                            "emp_id": emp_id, "name": name, "qty": qty,
                            "current": current, "new_total": new_total
                        }
                        st.rerun()

        # Repeat purchase approval
        if "pending_sale" in st.session_state:
            sale = st.session_state.pending_sale
            st.markdown(f"<div class='warning-box'>Warning: {sale['name']} already has {sale['current']}. New total: {sale['new_total']}</div>", unsafe_allow_html=True)
            remark = st.text_input("Reason *", key="remark_input")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", type="primary"):
                    if remark.strip():
                        add_sale(sale["emp_id"], sale["name"], sale["qty"], st.session_state.username, remark)
                        st.success(f"Approved! Remark: {remark}")
                        del st.session_state.pending_sale
                        st.rerun()
                    else:
                        st.error("Enter remark")
            with col2:
                if st.button("Cancel"):
                    st.info("Canceled")
                    del st.session_state.pending_sale
                    st.rerun()

# === REPORT PAGE (Admin Only + Excel Download) ===
elif page == "report":
    if not st.session_state.logged_in:
        st.warning("Login required")
        if st.button("Go to Login"): st.session_state.page = "login"; st.rerun()
        st.stop()

    if not is_admin(st.session_state.username):
        st.error("Only admins can view reports")
        if st.button("Back"): st.session_state.page = "home"; st.rerun()
        st.stop()

    st.markdown("<h2>Report</h2>", unsafe_allow_html=True)
    if st.button("Home"): st.session_state.page = "home"; st.rerun()

    # Summary
    total_emp, buyers, sold, remaining = get_stats()
    st.markdown("### Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>{total_emp}</h3><p>মোট কর্মী</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>{buyers}</h3><p>ক্রেতা</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>{sold}</h3><p>বিক্রি</p></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>{remaining}</h3><p>অবশিষ্ট</p></div>", unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["ক্রেতা", "সেলার", "লগ"])

    # === Buyers Tab + Excel Download ===
    with tab1:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("""
            SELECT e.employee_name AS 'Employee Name', 
                   t.employee_id AS 'Employee ID', 
                   t.total_quantity AS 'Total Tickets'
            FROM tickets t 
            JOIN employees e ON t.employee_id = e.employee_id 
            ORDER BY t.total_quantity DESC
        """, conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            excel_data = to_excel(df, "Buyers")
            st.download_button(
                label="Download Buyers Excel",
                data=excel_data,
                file_name=f"buyers_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No buyers")

    # === Sellers Tab ===
    with tab2:
        df = get_seller_stats()
        if not df.empty:
            for _, r in df.iterrows():
                st.markdown(f"<span class='seller-badge'>{r['seller']}</span> → {r['tickets_sold']} tickets", unsafe_allow_html=True)
        else:
            st.info("No sales")

    # === Log Tab + Excel Download ===
    with tab3:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("""
            SELECT timestamp AS 'Date & Time',
                   employee_name AS 'Employee',
                   quantity AS 'Quantity',
                   seller AS 'Seller',
                   remark AS 'Remark'
            FROM sales 
            ORDER BY id DESC 
            LIMIT 200
        """, conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            excel_data = to_excel(df, "Sales_Log")
            st.download_button(
                label="Download Log Excel",
                data=excel_data,
                file_name=f"sales_log_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No logs")

# === ADMIN PAGE ===
elif page == "admin":
    if not st.session_state.logged_in:
        st.warning("Login required")
        st.stop()
    st.markdown("<h2>Admin Panel</h2>", unsafe_allow_html=True)
    if st.button("Home"): st.session_state.page = "home"; st.rerun()

    with st.expander("Add New Admin"):
        with st.form("add_admin"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Add"):
                if u and p and u.lower() != "admin":
                    conn = sqlite3.connect(DB_NAME)
                    try:
                        conn.execute("INSERT INTO admins VALUES (?, ?)", (u, hash_password(p)))
                        conn.commit()
                        st.success("Admin added")
                    except:
                        st.error("Username exists")
                    conn.close()

    if st.button("Download DB Backup"):
        with open(DB_NAME, "rb") as f:
            st.download_button("Download DB", f, file_name=DB_NAME)

# === FOOTER ===
st.markdown("<div class='footer'>© 2025 | Max 10 tickets per employee | Session: 2 hours</div>", unsafe_allow_html=True)