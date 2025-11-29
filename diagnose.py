# diagnose.py → Run this and paste the full output
import pymongo
from datetime import datetime

URI = "mongodb+srv://nazmulrony2_db_user:hoiwdZF32VUZMInc@cluster0.29kh8wl.mongodb.net/"
client = pymongo.MongoClient(URI)
db = client.ticketdb

print("=== MONGODB DIAGNOSTIC REPORT ===")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for collection_name in ["employees", "sales", "tickets", "admins"]:
    col = db[collection_name]
    count = col.count_documents({})
    print(f"{collection_name.upper():8} → {count:,} documents")
    
    if count > 0:
        sample = col.find_one()
        print(f"   Sample keys: {list(sample.keys())}\n")
    else:
        print("   → EMPTY\n")