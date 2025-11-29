# app.py → FINAL VERSION: Clean CSS + Edit Feature + Last 5 Logs on Home
import streamlit as st
import pandas as pd
import pymongo
from datetime import datetime, timedelta
import hashlib
import io
import time

# ==================== CONFIG ====================
st.set_page_config(page_title="টিকেট বিতরণ", layout="centered")
MAX_TICKETS_PER_EMPLOYEE = 10
TOTAL_TICKETS = 20000
SESSION_TIMEOUT = timedelta(hours=2)

# ==================== MONGO CONNECTION ====================
client = pymongo.MongoClient(st.secrets["MONGO_URI"])
db = client.ticketdb
employees = db.employees
admins = db.admins
tickets = db.tickets
sales = db.sales

# ==================== BEAUTIFUL & ORGANIZED CSS ====================
st.markdown("""
<style>
/* ================================================
   1. GLOBAL & BODY
   ================================================ */
html, body, .stApp {
    background: #f1f5f9 !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #1e293b;
}

/* ================================================
   2. MAIN CONTAINER – Glassmorphism
   ================================================ */
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
    margin: 1rem auto;
}

/* ================================================
   3. HEADINGS
   ================================================ */
h1, h2, h3, h4, h5, h6 {
    color: #0f172a !important;
    font-weight: 600 !important;
    text-align: center;
    margin: 0 !important;
}

/* ================================================
   4. PRIMARY BUTTONS
   ================================================ */
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

/* ================================================
   5. HEADER CARD (Welcome)
   ================================================ */
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

/* ================================================
   6. SIDE BUTTONS
   ================================================ */
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

/* ================================================
   7. METRIC CARDS (Summary)
   ================================================ */
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
.metric-card:hover { transform: translateY(-4px); }
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

/* ================================================
   8. SELLER BADGE
   ================================================ */
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

/* ================================================
   9. RECENT LOGS & EDIT BOX
   ================================================ */
.edit-box {
    background: #f0f9ff;
    border-left: 5px solid #0ea5e9;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    font-size: 0.95rem;
}

/* ================================================
   10. WARNING & FOOTER
   ================================================ */
.warning-box {
    background: rgba(254,249,195,0.95) !important;
    border-left: 5px solid #facc15 !important;
    padding: 1.1rem !important;
    border-radius: 10px !important;
    margin: 1.2rem 0 !important;
    box-shadow: 0 4px 12px rgba(250,204,21,0.15);
}
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

/* ================================================
   11. ALERTS (Success, Error, etc.)
   ================================================ */
.stAlert { border-radius: 10px !important; padding: 0.9rem !important; }
.stSuccess { background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important; }
.stError   { background: #fef2f2 !important; border: 1px solid #fecaca !important; }

/* ================================================
   12. MOBILE RESPONSIVE
   ================================================ */
@media (max-width: 600px) {
    .block-container { padding: 1.2rem !important; }
    .stButton > button { font-size: 0.95rem !important; padding: 0.7rem !important; }
    .header-card h2 { font-size: 1.4rem; }
    .metric-card h3 { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE FUNCTIONS ====================
def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def ensure_default_admin():
    admins.update_one({"username": "admin"}, {"$set": {"password": hash_password("admin123")}}, upsert=True)

def check_login(u, p): return admins.find_one({"username": u, "password": hash_password(p)}) is not None

def get_employee(eid):
    doc = employees.find_one({"employee_id": str(eid)})
    return doc["employee_name"] if doc else None

def get_total_tickets(eid):
    doc = tickets.find_one({"employee_id": str(eid)})
    return doc["total_quantity"] if doc else 0

def add_sale(emp_id, name, qty, seller, remark=""):
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    sales.insert_one({
        "employee_id": str(emp_id), "employee_name": name, "quantity": qty,
        "seller": seller, "remark": remark, "timestamp": ts, "edited": False
    })
    current = get_total_tickets(emp_id)
    tickets.update_one(
        {"employee_id": str(emp_id)},
        {"$set": {"total_quantity": current + qty}},
        upsert=True
    )

def edit_sale(sale_id, new_emp_id, new_name, new_qty, editor, edit_remark):
    old_sale = sales.find_one({"_id": sale_id})
    if not old_sale:
        return False

    old_qty = old_sale["quantity"]
    old_emp_id = old_sale["employee_id"]

    # Reverse old quantity
    old_total = get_total_tickets(old_emp_id)
    tickets.update_one(
        {"employee_id": old_emp_id},
        {"$set": {"total_quantity": old_total - old_qty}}
    )
    if old_total - old_qty <= 0:
        tickets.delete_one({"employee_id": old_emp_id})

    # Apply new quantity
    new_total = get_total_tickets(new_emp_id)
    tickets.update_one(
        {"employee_id": new_emp_id},
        {"$set": {"total_quantity": new_total + new_qty}},
        upsert=True
    )

    # Update sale record
    sales.update_one(
        {"_id": sale_id},
        {"$set": {
            "employee_id": str(new_emp_id),
            "employee_name": new_name,
            "quantity": new_qty,
            "edited": True,
            "edit_remark": f"Edited by {editor}: {edit_remark}",
            "edit_timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }}
    )
    return True

def get_stats():
    total_emp = employees.count_documents({})
    buyers = tickets.count_documents({})
    sold = next(tickets.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total_quantity"}}}]), {"total": 0})["total"]
    remaining = max(0, TOTAL_TICKETS - sold)
    return total_emp, buyers, sold, remaining

ensure_default_admin()

# ==================== SESSION STATE ====================
for key in ['logged_in', 'username', 'page', 'login_time']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logged_in' else "" if key in ['username', 'page'] else None

if st.session_state.logged_in and st.session_state.login_time:
    if datetime.now() - st.session_state.login_time > SESSION_TIMEOUT:
        st.session_state.clear()
        st.rerun()

page = st.session_state.page or "login"

# ==================== LOGIN ====================
if page == "login":
    st.markdown("<h1>টিকেট বিক্রয় বুথ</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if check_login(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.login_time = datetime.now()
                st.session_state.page = "home"
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("ভুল তথ্য")

# ==================== HOME PAGE WITH LAST 5 LOGS + EDIT FEATURE ====================
elif page == "home" and st.session_state.logged_in:
    st.markdown(f'<div class="header-card"><h2>Welcome, <strong>{st.session_state.username}</strong>!</h2></div>', unsafe_allow_html=True)

    col_main, col_side = st.columns([3, 1])
    with col_side:
        st.markdown("<div class='side-btn'>", unsafe_allow_html=True)
        if st.button("Report"): st.session_state.page = "report"; st.rerun()
        if st.button("Admin"): st.session_state.page = "admin"; st.rerun()
        if st.button("Logout"): st.session_state.clear(); st.session_state.page = "login"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_main:
        st.subheader("টিকেট বিক্রয় বুথ")
        emp_id = st.text_input("Employee ID *", placeholder="21....")
        qty = st.number_input("Ticket Quantity *", min_value=1, max_value=10, step=1, value=1)

        if st.button("সাবমিট করুন", type="primary"):
            name = get_employee(emp_id)
            if not name:
                st.error("Employee not found!")
            elif get_total_tickets(emp_id) + qty > MAX_TICKETS_PER_EMPLOYEE:
                st.error(f"Max {MAX_TICKETS_PER_EMPLOYEE} tickets allowed!")
            else:
                add_sale(emp_id, name, qty, st.session_state.username)
                st.success(f"Success: {qty} tickets → {name} ({emp_id})")
                st.rerun()

        # === LAST 5 SALES + EDIT BUTTON ===
        st.markdown("### সর্বশেষ ৫টি এন্ট্রি")
        recent = list(sales.find().sort("timestamp", -1).limit(5))
        if recent:
            for s in recent:
                badge = "✏️" if s.get("edited") else "✅"
                st.markdown(f"""
                <div class="edit-box">
                    <strong>{badge} {s['timestamp']}</strong><br>
                    <b>{s['employee_name']} ({s['employee_id']})</b> → {s['quantity']} টি → {s['seller']}<br>
                    {f"<i>{s.get('edit_remark','')}</i>" if s.get("edited") else ""}
                    <br><small>{s.get('remark', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Edit this entry", key=str(s["_id"])):
                    st.session_state.edit_sale = s
                    st.rerun()
        else:
            st.info("No sales yet")

        # === EDIT SALE FORM ===
        if "edit_sale" in st.session_state:
            s = st.session_state.edit_sale
            st.markdown("### ✏️ ভুল এন্ট্রি সংশোধন করুন")
            new_id = st.text_input("নতুন Employee ID", value=s["employee_id"])
            new_qty = st.number_input("নতুন পরিমাণ", min_value=1, max_value=10, value=s["quantity"])
            remark = st.text_area("সংশোধনের কারণ (আবশ্যক)", placeholder="ভুল আইডি/পরিমাণ দিয়েছি")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("সংশোধন করুন", type="primary"):
                    if not remark.strip():
                        st.error("কারণ লিখুন!")
                    else:
                        new_name = get_employee(new_id) or "Unknown"
                        if edit_sale(s["_id"], new_id, new_name, new_qty, st.session_state.username, remark):
                            st.success("সংশোধন সফল!")
                            del st.session_state.edit_sale
                            st.rerun()
            with col2:
                if st.button("বাতিল"):
                    del st.session_state.edit_sale
                    st.rerun()

# ==================== REPORT & ADMIN (same as before) ====================
elif page == "report":
    st.markdown("<h2>Report</h2>", unsafe_allow_html=True)
    # ... (your full report code)

elif page == "admin":
    st.markdown("<h2>Admin Panel</h2>", unsafe_allow_html=True)
    # ... (your admin code)

# ==================== FOOTER ====================
st.markdown("<div class='footer'>© 2025 | Max 10 tickets per employee | Edit feature added</div>", unsafe_allow_html=True)