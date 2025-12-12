from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")  # change if your MongoDB URL is different
    return client["your_database_name"]  # replace with your DB name
