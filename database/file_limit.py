# database/file_limit.py

from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME

client = MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]
file_limit_collection = db["file_limits"]

def increment_file_limit(user_id):
    file_limit_collection.update_one(
        {'user_id': user_id},
        {'$inc': {'file_count': 1}},
        upsert=True
    )

def get_file_limit(user_id):
    user = file_limit_collection.find_one({'user_id': user_id})
    return user.get('file_count', 0) if user else 0

def reset_file_limit(user_id):
    file_limit_collection.update_one(
        {'user_id': user_id},
        {'$set': {'file_count': 0}},
        upsert=True
    )

def reset_all_file_limits():
    file_limit_collection.update_many({}, {'$set': {'file_count': 0}})
