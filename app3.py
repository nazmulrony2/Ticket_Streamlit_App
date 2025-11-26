# app.py
# Ticket Distribution App – FINAL + SECURE ADMIN PAGE
# ----------------------------------------------------
# • Normal users:  Home → Report → (Admin button asks for password)
# • Only default admin (admin / admin123) can reach /admin
# • All other code unchanged

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
import io
import time

# === CONFIGURATION ===
st.set_page_config(page_title="টিকেট বিতরণ", layout="centered")
DB_NAME = "ticket_distribution.db"
MAX_TICKETS_PER_EMPLOYEE = 10
TOTAL_TICKETS = 20000
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}
SESSION_TIMEOUT = timedelta(hours=2)

# === CSS STYLING (ADVANCED & POLISHED) ===
st.markdown("""
<style>
    /* -------------------------------------------------
       GLOBAL SETTINGS
       ------------------------------------------------- */
    html, body, .stApp {
        background: #f1f5f9 !important;               /* soft gray-blue */
        font-family: 'Inter', 'Segoe UI', sans-serif;
        color: #1e293b;
    }

    /* -------------------------------------------------
       MAIN CONTAINER – glass-morphism + gradient
       ------------------------------------------------- */
    .block-container {
    background: linear-gradient(135deg,
                rgba(16, 185, 129, 0.14) 0%,
                rgba(34, 211, 238, 0.14) 100%);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    padding: 2rem !important;
    border-radius: 22px !important;
    border: 1px solid rgba(255,255,255,0.22);
    box-shadow: 0 14px 36px rgba(0,0,0,0.11);
}

    /* -------------------------------------------------
       HEADINGS
       ------------------------------------------------- */
    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-align: center;
    }

    /* -------------------------------------------------
       BUTTONS – primary + secondary
       ------------------------------------------------- */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #fff !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.2rem !important;
        width: 100% !important;
        font-size: 1.05rem !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.25);
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37,99,235,0.35);
    }

    /* -------------------------------------------------
       HEADER CARD (Welcome)
       ------------------------------------------------- */
    .header-card {
        background: rgba(255,255,255,0.95);
        padding: 1.2rem 1.8rem !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.8rem !important;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .header-card h2 {
        margin: 0 !important;
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 1.6rem;
    }

    /* -------------------------------------------------
       SIDE BUTTONS
       ------------------------------------------------- */
    .side-btn {
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
        margin-top: 2.2rem;
    }
    .side-btn .stButton > button {
        width: 100% !important;
        font-size: 1rem !important;
        padding: 0.8rem !important;
    }

    /* -------------------------------------------------
       METRIC CARDS (Summary)
       ------------------------------------------------- */
    .metric-card {
        background: #ffffff !important;
        padding: 1.3rem !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.07);
        text-align: center;
        margin: 0.6rem !important;
        border: 1px solid rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-4px);
    }
    .metric-card h3 {
        margin: 0.4rem 0 0 !important;
        font-size: 1.8rem;
        color: #1e40af;
    }
    .metric-card p {
        margin: 0;
        font-size: 0.95rem;
        color: #64748b;
    }

    /* -------------------------------------------------
       SELLER BADGE
       ------------------------------------------------- */
    .seller-badge {
        background: linear-gradient(135deg, #fde047, #fbbf24) !important;
        color: #1e293b !important;
        padding: 0.45rem 0.9rem !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        font-size: 0.9rem;
        display: inline-block;
        box-shadow: 0 2px 6px rgba(251,191,36,0.3);
    }

    /* -------------------------------------------------
       FOOTER
       ------------------------------------------------- */
    .footer {
        text-align: center !important;
        margin-top: 2.5rem !important;
        color: #64748b !important;
        font-size: 0.9rem !important;
        padding: 1.2rem !important;
        background: rgba(255,255,255,0.9) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* -------------------------------------------------
       WARNING BOX
       ------------------------------------------------- */
    .warning-box {
        background: rgba(254,249,195,0.95) !important;
        border-left: 5px solid #facc15 !important;
        padding: 1.1rem !important;
        border-radius: 10px !important;
        margin: 1.2rem 0 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(250,204,21,0.15);
    }

    /* -------------------------------------------------
       ALERTS (st.error, st.success, st.info, st.warning)
       ------------------------------------------------- */
    /* Error */
    .stAlert[data-testid="stAlert"] > div > div > div {
        color: #dc2626 !important;
        font-weight: 600 !important;
    }
    .stAlert[data-testid="stAlert"] {
        background: #fef2f2 !important;
        border: 1px solid #fecaca !important;
        border-radius: 10px !important;
        padding: 0.9rem !important;
        box-shadow: 0 4px 12px rgba(220,38,38,0.1);
    }

    /* Success */
    .stAlert[data-testid="stSuccess"] > div > div > div {
        color: #16a34a !important;
        font-weight: 600 !important;
    }
    .stAlert[data-testid="stSuccess"] {
        background: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
        border-radius: 10px !important;
    }

    /* Info */
    .stAlert[data-testid="stInfo"] > div > div > div {
        color: #0c4a6e !important;
    }
    .stAlert[data-testid="stInfo"] {
        background: #ecfeff !important;
        border: 1px solid #a5f3fc !important;
    }

    /* Warning */
    .stAlert[data-testid="stWarning"] > div > div > div {
        color: #d97706 !important;
    }
    .stAlert[data-testid="stWarning"] {
        background: #fffbeb !important;
        border: 1px solid #fde68a !important;
    }

    /* -------------------------------------------------
       DARK MODE (optional – toggle via CSS variable)
       ------------------------------------------------- */
    @media (prefers-color-scheme: dark) {
        html, body, .stApp { background: #0f172a !important; }
        .block-container { background: rgba(15,23,42,0.8); }
        .header-card, .metric-card, .footer { background: rgba(30,41,59,0.9) !important; color: #e2e8f0; }
        h1,h2,h3,h4 { color: #e2e8f0 !important; }
        .stButton > button { background: #1e40af !important; }
        .stButton > button:hover { background: #1e3a8a !important; }
        .seller-badge { background: #fbbf24 !important; color: #1e293b; }
    }

    /* -------------------------------------------------
       MOBILE RESPONSIVENESS
       ------------------------------------------------- */
    @media (max-width: 600px) {
        .block-container { padding: 1.2rem !important; border-radius: 14px !important; }
        .stButton > button { font-size: 0.95rem !important; padding: 0.7rem !important; }
        .header-card h2 { font-size: 1.4rem; }
        .metric-card h3 { font-size: 1.5rem; }
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_quantity FROM tickets WHERE employee_id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_sale(emp_id, name, qty, seller, remark=""):
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO sales (employee_id, employee_name, quantity, seller, remark, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (emp_id, name, qty, seller, remark, ts))
    current = get_total_tickets(emp_id)
    new_total = current + qty
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
    st.info("নিচে সঠিক ইউজার ও পাসওয়ার্ড দিয়ে লগইন করুন**")
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
                st.error("ভুল ইউজারনেম/পাসওয়ার্ড দিয়েছেন")

# === HOME PAGE (PERFECT LAYOUT) ===
elif page == "home" and st.session_state.logged_in:

    # ────── HEADER CARD ──────
    st.markdown(
        f"""
        <div class="header-card">
            <h2>Welcome, <strong>{st.session_state.username}</strong>!</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ────── TWO COLUMNS ──────
    col_main, col_side = st.columns([3, 1])

    # ────── SIDE BUTTONS ──────
    with col_side:
        st.markdown("<div class='side-btn'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

    # ────── MAIN AREA ──────
    with col_main:
        st.markdown("---")
        st.subheader("টিকেট বিক্রয় বুথ")

        # ────── INPUT FIELDS ──────
        if 'qty_value' not in st.session_state:
            st.session_state.qty_value = 0

        emp_id = st.text_input("Employee ID *", placeholder="210679", key="emp_id_input")
        qty = st.number_input("Ticket Quantity *", min_value=0, max_value=10, step=1,
                              value=st.session_state.qty_value, key="qty_input")

        # ────── SUBMIT ──────
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
                        st.error(f"সর্বোচ্চ {MAX_TICKETS_PER_EMPLOYEE} টি টিকেট দেয়া যাবে। আপনি ইতমধ্যে {current} টি টিকেট কিনেছেন")
                    elif current == 0:
                        add_sale(emp_id, name, qty, st.session_state.username)
                        success_placeholder = st.empty()
                        success_placeholder.success(
                            f"সফল: **{name}** অর্থাৎ **{emp_id}** এর জন্য {qty} টি টিকেট প্রদান করা হয়েছে। মোট: {qty}"
                        )
                        time.sleep(3)
                        success_placeholder.empty()
                        st.session_state.qty_value = 0
                        st.rerun()
                    else:
                        st.session_state.pending_sale = {
                            "emp_id": emp_id, "name": name, "qty": qty,
                            "current": current, "new_total": new_total
                        }
                        st.rerun()

        # ────── REPEAT BUYER ──────
        if "pending_sale" in st.session_state:
            sale = st.session_state.pending_sale
            st.markdown(
                f"""
                <div class='warning-box'>
                    সতর্কতা: <strong>{sale['name']}</strong> (<code>{sale['emp_id']}</code>) এর কাছে ইতিমধ্যে {sale['current']} টি টিকেট আছে। 
                    নতুন মোট হবে <strong>{sale['new_total']}</strong>।
                </div>
                """,
                unsafe_allow_html=True,
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
                        st.session_state.qty_value = 0
                        st.rerun()
            with colB:
                if st.button("Cancel"):
                    st.info("বাতিল করা হয়েছে")
                    del st.session_state.pending_sale
                    st.session_state.qty_value = 0
                    st.rerun()

# === REPORT PAGE (FULL + ALL-IN-ONE) ===
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

    # === ALL REPORTS BUTTON ===
    st.markdown("### ডাউনলোড করুন")
    col_all1, col_all2 = st.columns([1, 3])
    with col_all1:
        if st.button("**সব রিপোর্ট একসাথে (Excel)**", type="primary"):
            conn = sqlite3.connect(DB_NAME)
            df_buyers = pd.read_sql("""
                SELECT e.employee_name AS 'Employee Name', t.employee_id AS 'Employee ID', t.total_quantity AS 'Total Tickets'
                FROM tickets t JOIN employees e ON t.employee_id = e.employee_id ORDER BY t.total_quantity DESC
            """, conn)
            df_sellers = get_seller_stats()
            df_sellers.columns = ['Seller', 'Tickets Sold']
            df_log = pd.read_sql("""
                SELECT timestamp AS 'Date & Time', employee_name AS 'Employee', employee_id AS 'Employee ID',
                       quantity AS 'Quantity', seller AS 'Seller', remark AS 'Remark'
                FROM sales ORDER BY id DESC
            """, conn)
            conn.close()

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not df_buyers.empty: df_buyers.to_excel(writer, sheet_name="ক্রেতা", index=False)
                if not df_sellers.empty: df_sellers.to_excel(writer, sheet_name="বিক্রেতা", index=False)
                if not df_log.empty: df_log.to_excel(writer, sheet_name="লগ", index=False)
            output.seek(0)

            st.download_button(
                label="Downloading all_reports_*.xlsx",
                data=output,
                file_name=f"all_reports_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_all"
            )
            st.success(f"সব রিপোর্ট প্রস্তুত! ফাইল: `all_reports_{timestamp}.xlsx`")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["ক্রেতা", "বিক্রেতা", "লগ"])

    with tab1:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("SELECT e.employee_name AS 'Employee Name', t.employee_id AS 'Employee ID', t.total_quantity AS 'Total Tickets' FROM tickets t JOIN employees e ON t.employee_id = e.employee_id ORDER BY t.total_quantity DESC", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.download_button("Download Buyers", to_excel(df, "Buyers"), f"buyers_{ts}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("কোনো ক্রেতা পাওয়া যায়নি")

    with tab2:
        df = get_seller_stats()
        df.columns = ['Seller', 'Tickets Sold']
        if not df.empty:
            for _, r in df.iterrows():
                st.markdown(f"<span class='seller-badge'>{r['Seller']}</span> → {r['Tickets Sold']} টিকেট", unsafe_allow_html=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.download_button("Download Sellers", to_excel(df, "Sellers"), f"sellers_{ts}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("কোনো বিক্রয় নেই")

    with tab3:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql("SELECT timestamp AS 'Date & Time', employee_name AS 'Employee', employee_id AS 'Employee ID', quantity AS 'Quantity', seller AS 'Seller', remark AS 'Remark' FROM sales ORDER BY id DESC", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            st.download_button("Download Log", to_excel(df, "Log"), f"log_{ts}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("কোনো লগ নেই")

    # === SUMMARY ===
    st.markdown("---")
    st.markdown("### Summary")
    total_emp, buyers, sold, remaining = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>{total_emp}</h3><p>মোট কর্মী রয়েছে</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>{buyers}</h3><p>জন টিকেট কিনেছে</p></div>", unsafe_allow_html=True)


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
    # === SUMMARY ===
    st.markdown("---")
    st.markdown("### Summary")
    total_emp, buyers, sold, remaining = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>{total_emp}</h3><p>মোট কর্মী</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>{buyers}</h3><p>জন টিকেট কিনেছে</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>{sold}</h3><p>টি টিকেট বিক্রি হয়েছে</p></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>{remaining}</h3><p>টি টিকেট অবশিষ্ট রয়েছে</p></div>", unsafe_allow_html=True)

# === FOOTER ===
st.markdown("<div class='footer'>© 2025 | Max 10 tickets per employee</div>", unsafe_allow_html=True)