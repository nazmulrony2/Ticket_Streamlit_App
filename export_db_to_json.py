# export_db_to_json.py → SQLite → JSON (Full Backup)
import sqlite3
import json
from datetime import datetime
import os

# ==================== CONFIG ====================
DB_FILE = "ticket_distribution.db"   # আপনার DB ফাইলের নাম
OUTPUT_FOLDER = "db_backup_json"     # JSON ফাইলগুলো এখানে সেভ হবে

# ফোল্ডার তৈরি করুন (যদি না থাকে)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("SQLite → JSON Export Tool")
print("="*50)
print(f"Database : {DB_FILE}")
print(f"Output   : {OUTPUT_FOLDER}/")
print("="*50)

# Connect to SQLite
try:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row   # এটা দিলে dict আকারে ডেটা পাবেন
    cur = conn.cursor()
    print("Connected to database")
except Exception as e:
    print(f"Error: {e}")
    exit()

# সব টেবিলের নাম বের করি
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]

print(f"Found tables: {tables}")

# প্রতিটি টেবিল থেকে ডেটা বের করে JSON এ সেভ করি
for table in tables:
    print(f"Exporting {table}...")
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    
    # sqlite3.Row → normal dict এ কনভার্ট
    data = [dict(row) for row in rows]
    
    # টাইমস্ট্যাম্প যদি থাকে তাহলে string করি (JSON এ datetime সাপোর্ট করে না)
    for item in data:
        for key, value in item.items():
            if isinstance(value, (datetime,)):
                item[key] = value.strftime("%Y-%m-%d %H:%M:%S")

    # JSON ফাইল লিখি
    filename = os.path.join(OUTPUT_FOLDER, f"{table}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"→ {len(data):,} records → {filename}")

# Meta info
meta = {
    "exported_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
    "source_db": DB_FILE,
    "total_tables": len(tables),
    "tables": tables
}

with open(os.path.join(OUTPUT_FOLDER, "_info.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print("\n" + "SUCCESS!" * 8)
print(f"All data exported to folder: {OUTPUT_FOLDER}/")
print("Files created:")
for t in tables:
    print(f"   • {t}.json")
print("   • _info.json")
print("SUCCESS!" * 8)