# app.py
# Ticket Distribution App - Final Working Version
# Features:
# - Max 10 tickets per employee
# - First buy → auto-save
# - Repeat buy → warning + remark + approval
# - Report: Admin only, 20 records per page + pagination
# - Excel download (Buyers & Log)
# - Login session: 2 hours

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
import io

# === CONFIGURATION ===
st.set_page_config(page_title="টিকেট বিতরণ", layout="centered")
DB_NAME = "ticket_distribution.db"
MAX_TICKETS_PER_EMPLOYEE = 10
TOTAL_TICKETS = 20000
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}
SESSION_TIMEOUT = timedelta(hours=2)
RECORDS_PER_PAGE = 20

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
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
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
    """Keep default admin (admin/admin123)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed = hash_password(DEFAULT_ADMIN["password"])
    c.execute("INSERT OR IGNORE INTO admins VALUES (?, ?)", (DEFAULT_ADMIN["username"], hashed))
    conn.commit()
    conn.close()

def load_admins_from_excel():
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
    hashed = hash_password(password)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE username=? AND password=?", (username, hashed))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_admin(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_employee(emp_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT employee_name FROM employees WHERE employee_id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_total_tickets(emp_id):
    """Safely get total tickets (returns 0 if not found)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_quantity FROM tickets WHERE employee_id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_sale(emp_id, name, qty, seller, remark=""):
    """Save sale and update total - FIXED for UNIQUE constraint"""
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Save sale log
    c.execute("INSERT INTO sales (employee_id, employee_name, quantity, seller, remark, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (emp_id, name, qty, seller, remark, ts))

    # Get current total
    current = get_total_tickets(emp_id)
    new_total = current + qty

    # INSERT OR REPLACE → fixes UNIQUE constraint error
    c.execute("INSERT OR REPLACE INTO tickets VALUES (?, ?, ?)", (emp_id, new_total, ts))

    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    total_emp = pd.read_sql("SELECT COUNT(*) FROM employees", conn).iloc[0,0]
    buyers = pd.read_sql("SELECT COUNT(*) FROM tickets", conn).iloc[0,0]
    sold = pd.read_sql("SELECT COALESCE(SUM(total_quantity),0) FROM tickets", conn).iloc[0,0]
    remaining = max(0, TOTAL_TICKETS - sold)
    conn.close()
    return total_emp, buyers, sold, remaining

def get_seller_stats():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT seller, SUM(quantity) as tickets_sold FROM sales GROUP BY seller ORDER BY tickets_sold DESC", conn)
    conn.close()
    return df

# === EXCEL DOWNLOAD ===
def to_excel(df, sheet_name="Sheet1"):
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
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'page' not in st.session_state: st.session_state.page = "login"
if 'login_time' not in st.session_state: st.session_state.login_time = None

# Session timeout
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
    st.markdown("<h1>টিকেট বিক্রয় বুথ</h1>", unsafe_allow_html=True)
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
                st.success("Logged in! Session: 2 hours")
                st.rerun()
            else:
                st.error("ভূল ইউজারনেম/পাসওয়ার্ড দিয়েছেন")

# === HOME PAGE ===
elif page == "home" and st.session_state.logged_in:
    st.markdown(f"<h2>Welcome, {st.session_state.username}!</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Report"): 
            st.session_state.page = "report"
            st.rerun()
        if st.button("Admin"): 
            st.session_state.page = "admin"
            st.rerun()
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()

    with col1:
        st.markdown("---")
        st.subheader("New Ticket Sale")

        # === INPUT FIELDS (Quantity defaults to 0) ===
        # Use a separate key for default value
        if 'qty_value' not in st.session_state:
            st.session_state.qty_value = 0

        emp_id = st.text_input(
            "Employee ID *",
            placeholder="210679",
            key="emp_id_input"
        )
        qty = st.number_input(
            "Ticket Quantity *",
            min_value=0,
            max_value=10,
            step=1,
            value=st.session_state.qty_value,  # Controlled by separate key
            key="qty_input"
        )

        # === CHECK & SELL BUTTON ===
        if st.button("সাবমিট করুন", type="primary"):
            if not emp_id.strip():
                st.error("Employee ID লিখুন")
            elif qty == 0:
                st.error("টিকেট সংখ্যা ০ হতে পারে না। ১ বা তার বেশি লিখুন।")
            else:
                name = get_employee(emp_id)
                if not name:
                    st.error("Employee লিস্টে পাওয়া যায়নি")
                else:
                    current = get_total_tickets(emp_id)
                    new_total = current + qty

                    if new_total > MAX_TICKETS_PER_EMPLOYEE:
                        st.error(f"সর্বোচ্চ {MAX_TICKETS_PER_EMPLOYEE} টি টিকেট দেয়া যাবে। বর্তমানে আছে: {current}")
                    elif current == 0:
                        # FIRST-TIME BUYER: Auto-save + 3-second success
                        add_sale(emp_id, name, qty, st.session_state.username)
                        
                        success_placeholder = st.empty()
                        success_placeholder.success(
                            f"সফল: **{name}** অর্থাৎ **{emp_id}** এর জন্য {qty} টি টিকেট প্রদান করা হয়েছে। মোট: {qty}"
                        )
                        
                        import time
                        time.sleep(3)
                        success_placeholder.empty()
                        st.session_state.qty_value = 0  # Reset default
                        st.rerun()

                    else:
                        # REPEAT BUYER
                        st.session_state.pending_sale = {
                            "emp_id": emp_id,
                            "name": name,
                            "qty": qty,
                            "current": current,
                            "new_total": new_total
                        }
                        st.rerun()

        # === REPEAT BUYER CONFIRMATION BOX ===
        if "pending_sale" in st.session_state:
            sale = st.session_state.pending_sale
            st.markdown(
                f"<div class='warning-box'>"
                f"সতর্কতা: <strong>{sale['name']}</strong> "
                f"(<code>{sale['emp_id']}</code>) এর কাছে ইতিমধ্যে {sale['current']} টি টিকেট আছে। "
                f"নতুন মোট হবে <strong>{sale['new_total']}</strong>।"
                f"</div>", 
                unsafe_allow_html=True
            )
            
            remark = st.text_input("আবার টিকেট কেনার কারন কি *", key="remark_input")
            
            colA, colB = st.columns(2)
            with colA:
                if st.button("Approve Sale", type="primary"):
                    if not remark.strip():
                        st.error("একাধিক টিকেট কেনার কারণ লিখুন")
                    else:
                        add_sale(sale["emp_id"], sale["name"], sale["qty"], st.session_state.username, remark)
                        st.success(f"অনুমোদিত: {sale['qty']} টি টিকেট যোগ করা হয়েছে।")
                        del st.session_state.pending_sale
                        st.session_state.qty_value = 0  # Reset
                        st.rerun()
            with colB:
                if st.button("Cancel"):
                    st.info("বাতিল করা হয়েছে")
                    del st.session_state.pending_sale
                    st.session_state.qty_value = 0  # Reset
                    st.rerun()

# === REPORT PAGE (Admin Only - NO PAGINATION - FULL + ALL-IN-ONE DOWNLOAD) ===
elif page == "report":
    if not st.session_state.logged_in:
        st.warning("Login required")
        if st.button("Go to Login"): 
            st.session_state.page = "login"
            st.rerun()
        st.stop()

    if not is_admin(st.session_state.username):
        st.error("Only admins can view reports")
        if st.button("Back"): 
            st.session_state.page = "home"
            st.rerun()
        st.stop()

    st.markdown("<h2>Report</h2>", unsafe_allow_html=True)
    if st.button("Home"): 
        st.session_state.page = "home"
        st.rerun()

    # === DOWNLOAD ALL REPORTS (ONE FILE) ===
    st.markdown("### ডাউনলোড করুন")
    col_all1, col_all2 = st.columns([1, 3])
    with col_all1:
        if st.button("**সব রিপোর্ট একসাথে (Excel)**", type="primary"):
            # Load all data
            conn = sqlite3.connect(DB_NAME)
            
            df_buyers = pd.read_sql("""
                SELECT e.employee_name AS 'Employee Name', 
                       t.employee_id AS 'Employee ID', 
                       t.total_quantity AS 'Total Tickets'
                FROM tickets t 
                JOIN employees e ON t.employee_id = e.employee_id 
                ORDER BY t.total_quantity DESC
            """, conn)
            
            df_sellers = get_seller_stats()
            df_sellers.columns = ['Seller', 'Tickets Sold']  # Bangla-friendly

            df_log = pd.read_sql("""
                SELECT timestamp AS 'Date & Time',
                       employee_name AS 'Employee',
                       employee_id AS 'Employee ID',
                       quantity AS 'Quantity',
                       seller AS 'Seller',
                       remark AS 'Remark'
                FROM sales 
                ORDER BY id DESC
            """, conn)
            conn.close()

            # Create Excel with 3 sheets
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not df_buyers.empty:
                    df_buyers.to_excel(writer, sheet_name="ক্রেতা", index=False)
                if not df_sellers.empty:
                    df_sellers.to_excel(writer, sheet_name="বিক্রেতা", index=False)
                if not df_log.empty:
                    df_log.to_excel(writer, sheet_name="লগ", index=False)
            output.seek(0)

            st.download_button(
                label="Downloading: all_reports_*.xlsx",
                data=output,
                file_name=f"all_reports_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_all"
            )
            st.success(f"সব রিপোর্ট প্রস্তুত! ফাইল: `all_reports_{timestamp}.xlsx`")

    st.markdown("---")

    # === TABS (Individual Views + Individual Downloads) ===
    tab1, tab2, tab3 = st.tabs(["ক্রেতা", "বিক্রেতা", "লগ"])

    # === ক্রেতা (Buyers) ===
    with tab1:
        conn = sqlite3.connect(DB_NAME)
        df_buyers = pd.read_sql("""
            SELECT e.employee_name AS 'Employee Name', 
                   t.employee_id AS 'Employee ID', 
                   t.total_quantity AS 'Total Tickets'
            FROM tickets t 
            JOIN employees e ON t.employee_id = e.employee_id 
            ORDER BY t.total_quantity DESC
        """, conn)
        conn.close()

        if not df_buyers.empty:
            st.dataframe(df_buyers, use_container_width=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            excel_data = to_excel(df_buyers, "Buyers")
            st.download_button(
                label="Download Buyers Only",
                data=excel_data,
                file_name=f"buyers_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("কোনো ক্রেতা পাওয়া যায়নি")

    # === বিক্রেতা (Sellers) ===
    with tab2:
        df_sellers = get_sellers = get_seller_stats()
        df_sellers.columns = ['Seller', 'Tickets Sold']

        if not df_sellers.empty:
            for _, r in df_sellers.iterrows():
                st.markdown(f"<span class='seller-badge'>{r['Seller']}</span> → {r['Tickets Sold']} টিকেট", unsafe_allow_html=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            excel_data = to_excel(df_sellers, "Sellers")
            st.download_button(
                label="Download Sellers Only",
                data=excel_data,
                file_name=f"sellers_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("কোনো বিক্রয় নেই")

    # === লগ (Log) ===
    with tab3:
        conn = sqlite3.connect(DB_NAME)
        df_log = pd.read_sql("""
            SELECT timestamp AS 'Date & Time',
                   employee_name AS 'Employee',
                   employee_id AS 'Employee ID',
                   quantity AS 'Quantity',
                   seller AS 'Seller',
                   remark AS 'Remark'
            FROM sales 
            ORDER BY id DESC
        """, conn)
        conn.close()

        if not df_log.empty:
            st.dataframe(df_log, use_container_width=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            excel_data = to_excel(df_log, "Log")
            st.download_button(
                label="Download Log Only",
                data=excel_data,
                file_name=f"log_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("কোনো লগ নেই")

    # === SUMMARY AT BOTTOM ===
    st.markdown("---")
    st.markdown("### Summary")
    total_emp, buyers, sold, remaining = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.markdown(f"<div class='metric-card'><h3>{total_emp}</h3><p>মোট কর্মী</p></div>", unsafe_allow_html=True)
    with c2: 
        st.markdown(f"<div class='metric-card'><h3>{buyers}</h3><p>জন টিকেট কিনেছে</p></div>", unsafe_allow_html=True)
    with c3: 
        st.markdown(f"<div class='metric-card'><h3>{sold}</h3><p>টি টিকেট বিক্রি হয়েছে</p></div>", unsafe_allow_html=True)
    with c4: 
        st.markdown(f"<div class='metric-card'><h3>{remaining}</h3><p>টি টিকেট অবশিষ্ট রয়েছে</p></div>", unsafe_allow_html=True)

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