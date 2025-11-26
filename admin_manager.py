# admin_manager.py
# এই স্ক্রিপ্টটি:
# 1. সবসময় 'admin' / 'admin123' ইউজার রাখে (পরিবর্তন/মুছে ফেলা যাবে না)
# 2. admins.xlsx থেকে অন্য অ্যাডমিন লোড করে
# 3. ডাটাবেসে সিঙ্ক করে

import pandas as pd
import sqlite3
import hashlib
import os
from datetime import datetime

# === কনফিগারেশন ===
DB_NAME = "ticket_distribution.db"
EXCEL_FILE = "admins.xlsx"
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}  # পরিবর্তন হবে না
REMOVE_MISSING = True  # True = এক্সেলে নেই এমন (admin ছাড়া) মুছে ফেলবে

def hash_password(password):
    """পাসওয়ার্ড SHA-256 হ্যাশ করে"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_admin_table():
    """admins টেবিল তৈরি করে"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                 username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()
    print("admins টেবিল তৈরি/প্রস্তুত।")

def ensure_default_admin():
    """সবসময় 'admin' / 'admin123' থাকবে"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        hashed = hash_password(DEFAULT_ADMIN["password"])
        c.execute("SELECT password FROM admins WHERE username=?", (DEFAULT_ADMIN["username"],))
        row = c.fetchone()
        
        if row is None:
            # যোগ করুন
            c.execute("INSERT INTO admins VALUES (?, ?)", 
                      (DEFAULT_ADMIN["username"], hashed))
            print(f"ডিফল্ট অ্যাডমিন তৈরি: {DEFAULT_ADMIN['username']}")
        elif row[0] != hashed:
            # আপডেট করুন (যদি কেউ চেঞ্জ করে)
            c.execute("UPDATE admins SET password=? WHERE username=?", 
                      (hashed, DEFAULT_ADMIN["username"]))
            print(f"ডিফল্ট অ্যাডমিন পাসওয়ার্ড রিসেট: {DEFAULT_ADMIN['username']}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ডিফল্ট অ্যাডমিন সেট করতে সমস্যা: {e}")

def load_admins_from_excel():
    """admins.xlsx থেকে অ্যাডমিন লোড করে (admin ছাড়া)"""
    if not os.path.exists(EXCEL_FILE):
        print(f"সতর্কতা: {EXCEL_FILE} পাওয়া যায়নি। শুধু ডিফল্ট অ্যাডমিন থাকবে।")
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        required = ['username', 'password']
        if not all(col in df.columns for col in required):
            print("সমস্যা: 'username' এবং 'password' কলাম দরকার।")
            return pd.DataFrame()
        
        df = df[required].dropna()
        df['username'] = df['username'].astype(str).str.strip()
        df['password'] = df['password'].astype(str).str.strip()
        
        # admin ইউজার এক্সেলে থাকলেও ইগনোর করুন
        df = df[df['username'].str.lower() != DEFAULT_ADMIN["username"].lower()]
        
        if df.empty:
            print("এক্সেলে কোনো অতিরিক্ত অ্যাডমিন নেই।")
        else:
            df['password'] = df['password'].apply(hash_password)
            print(f"লোড হয়েছে: {len(df)} জন অতিরিক্ত অ্যাডমিন।")
        
        return df
    except Exception as e:
        print(f"এক্সেল পড়তে সমস্যা: {e}")
        return pd.DataFrame()

def sync_admins_to_db(df):
    """অন্যান্য অ্যাডমিন সিঙ্ক করে (admin ছাড়া)"""
    if df.empty and not REMOVE_MISSING:
        return
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # বর্তমান অ্যাডমিন (admin ছাড়া)
    c.execute("SELECT username FROM admins WHERE username != ?", (DEFAULT_ADMIN["username"],))
    existing = set(row[0] for row in c.fetchall())
    excel_usernames = set(df['username']) if not df.empty else set()
    
    added = 0
    updated = 0
    removed = 0
    
    # যোগ / আপডেট
    for _, row in df.iterrows():
        if row['username'] in existing:
            c.execute("UPDATE admins SET password=? WHERE username=?", 
                      (row['password'], row['username']))
            updated += 1
        else:
            c.execute("INSERT INTO admins VALUES (?, ?)", 
                      (row['username'], row['password']))
            added += 1
    
    # মুছে ফেলা (শুধু admin ছাড়া)
    if REMOVE_MISSING:
        to_remove = existing - excel_usernames
        for username in to_remove:
            c.execute("DELETE FROM admins WHERE username=?", (username,))
            removed += 1
    
    conn.commit()
    conn.close()
    
    print(f"সিঙ্ক সম্পন্ন → যোগ: {added}, আপডেট: {updated}, মুছে ফেলা: {removed}")

def main():
    print("অ্যাডমিন ম্যানেজার চালু হচ্ছে...\n")
    print(f"তারিখ: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n")
    
    init_admin_table()
    ensure_default_admin()  # সবার আগে
    df = load_admins_from_excel()
    sync_admins_to_db(df)
    
    print("\nসফলভাবে সম্পন্ন!")
    print(f"লগইন: {DEFAULT_ADMIN['username']} / {DEFAULT_ADMIN['password']}")
    print("অন্য অ্যাডমিন: admins.xlsx থেকে")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"অপ্রত্যাশিত সমস্যা: {e}")
    
    input("\nEnter চাপুন বন্ধ করতে...")