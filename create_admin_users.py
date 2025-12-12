# create_admin_users.py
from pymongo import MongoClient

client = MongoClient("YOUR_MASTER_DB_URI")
db = client["master_db"]

if "admin_users" not in db.list_collection_names():
    db.create_collection("admin_users")
    print("admin_users collection created!")
else:
    print("admin_users already exists.")

