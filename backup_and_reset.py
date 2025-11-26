# backup_and_reset.py
# এই স্ক্রিপ্টটি:
# 1. পুরাতন ডাটাবেস ব্যাকআপ করে
# 2. এক্সেলে রপ্তানি করে
# 3. নতুন ডাটাবেস তৈরি করে
# 4. employees.xlsx থেকে কর্মী লোড করে
# 5. ডিফল্ট admin/admin123 রাখে

import sqlite3
import pandas as pd
import os
import shutil
from datetime import datetime
import hashlib

# === কনফিগারেশন ===
DB_NAME = "ticket_distribution.db"
EMPLOYEES_XLSX = "employees.xlsx"
BACKUP_DIR = "backups"
EXCEL_BACKUP = True
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}

# ব্যাকআপ ফোল্ডার তৈরি
os.makedirs(BACKUP_DIR, exist_ok=True)

# টাইমস্ট্যাম্প
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_db_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
backup_excel_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.xlsx")

# === হ্যাশ ফাংশন ===
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# === এক্সেলে রপ্তানি ===
def export_to_excel(db_path, excel_path):
    """সব টেবিল এক্সেলে রপ্তানি করে"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("কোনো টেবিল পাওয়া যায়নি।")
            return
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for (table_name,) in tables:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                df.to_excel(writer, sheet_name=table_name, index=False)
                print(f"টেবিল '{table_name}' → {table_name} শিটে সংরক্ষিত")
        
        print(f"সফল! এক্সেল ব্যাকআপ: {excel_path}")
        conn.close()
    except Exception as e:
        print(f"এক্সেল রপ্তানিতে সমস্যা: {e}")

# === নতুন ডাটাবেস তৈরি ===
def create_new_db():
    """নতুন ডাটাবেস + টেবিল তৈরি করে"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS employees (
                     employee_id TEXT PRIMARY KEY, employee_name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins (
                     username TEXT PRIMARY KEY, password TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tickets (
                     employee_id TEXT PRIMARY KEY, total_quantity INTEGER DEFAULT 0, first_timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sales (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     employee_id TEXT, employee_name TEXT, quantity INTEGER,
                     seller TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()
        print(f"নতুন ডাটাবেস তৈরি: {DB_NAME}")
    except Exception as e:
        print(f"ডাটাবেস তৈরিতে সমস্যা: {e}")

# === ডিফল্ট অ্যাডমিন যোগ ===
def add_default_admin():
    """সবসময় admin/admin123 থাকবে"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        hashed = hash_password(DEFAULT_ADMIN["password"])
        c.execute("INSERT OR REPLACE INTO admins VALUES (?, ?)", 
                  (DEFAULT_ADMIN["username"], hashed))
        conn.commit()
        conn.close()
        print(f"ডিফল্ট অ্যাডমিন যোগ: {DEFAULT_ADMIN['username']}")
    except Exception as e:
        print(f"ডিফল্ট অ্যাডমিন যোগে সমস্যা: {e}")

# === employees.xlsx থেকে লোড ===
def load_employees_from_excel():
    """employees.xlsx থেকে কর্মী লোড করে"""
    if not os.path.exists(EMPLOYEES_XLSX):
        print(f"সতর্কতা: {EMPLOYEES_XLSX} পাওয়া যায়নি। কর্মী লোড হবে না।")
        return
    
    try:
        df = pd.read_excel(EMPLOYEES_XLSX)
        required = ['Employee ID', 'Employee Name']
        if not all(col in df.columns for col in required):
            print(f"সমস্যা: {EMPLOYEES_XLSX}-এ 'Employee ID' এবং 'Employee Name' কলাম দরকার।")
            return
        
        df = df[required].dropna()
        df.columns = ['employee_id', 'employee_name']
        df['employee_id'] = df['employee_id'].astype(str).str.strip()
        df['employee_name'] = df['employee_name'].astype(str).str.strip()
        
        conn = sqlite3.connect(DB_NAME)
        df.to_sql('employees', conn, if_exists='replace', index=False)
        conn.close()
        
        print(f"সফল! {len(df)} জন কর্মী লোড হয়েছে: {EMPLOYEES_XLSX}")
    except Exception as e:
        print(f"কর্মী লোডে সমস্যা: {e}")

# === মেইন ফাংশন ===
def main():
    print("টিকেট ডাটাবেস ব্যাকআপ ও রিসেট শুরু হচ্ছে...\n")
    print(f"তারিখ: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n")

    # পুরাতন ডাটাবেস আছে?
    if os.path.exists(DB_NAME):
        print(f"পুরাতন ডাটাবেস পাওয়া গেছে: {DB_NAME}")
        
        # ব্যাকআপ .db
        shutil.copy2(DB_NAME, backup_db_path)
        print(f"ডাটাবেস ব্যাকআপ: {backup_db_path}")
        
        # এক্সেল ব্যাকআপ
        if EXCEL_BACKUP:
            export_to_excel(DB_NAME, backup_excel_path)
        
        # মুছে ফেলা
        os.remove(DB_NAME)
        print(f"পুরাতন ডাটাবেস মুছে ফেলা হয়েছে")
    else:
        print("পুরাতন ডাটাবেস পাওয়া যায়নি। নতুন তৈরি হচ্ছে...")

    # নতুন ডাটাবেস
    create_new_db()
    add_default_admin()
    load_employees_from_excel()

    print("\nসবকিছু সম্পন্ন!")
    print(f"ব্যাকআপ: {BACKUP_DIR}/")
    print("লগইন: admin / admin123")
    print("এখন Streamlit অ্যাপ চালান।")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nবন্ধ করা হয়েছে।")
    except Exception as e:
        print(f"অপ্রত্যাশিত সমস্যা: {e}")
    
    input("\nEnter চাপুন বন্ধ করতে...")