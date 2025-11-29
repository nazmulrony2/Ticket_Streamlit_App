# check_mongo.py → Instant proof
import pymongo

client = pymongo.MongoClient("mongodb+srv://nazmulrony2_db_user:hoiwdZF32VUZMInc@cluster0.29kh8wl.mongodb.net/")
db = client.ticketdb

print("EMPLOYEES:", db.employees.count_documents({}))
print("SALES LOG :", db.sales.count_documents({}))
print("TICKET TOTALS:", db.tickets.count_documents({}))

print("\nLast 3 sales:")
for s in db.sales.find().sort("timestamp", -1).limit(3):
    print(f"{s['timestamp']} → {s['employee_name']} ({s['employee_id']}) → {s['quantity']} tickets by {s['seller']}")