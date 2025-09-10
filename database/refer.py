import pymongo
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]


class UserTracker:
    def __init__(self):
        self.user_collection = mydb["referusers"]
        self.refer_collection = mydb["refers"]
        self.file_limit_collection = mydb["file_limit"]
    
    def add_user(self, user_id):
        if not self.is_user_in_list(user_id):
            self.user_collection.insert_one({'user_id': user_id})

    def remove_user(self, user_id):
        self.user_collection.delete_one({'user_id': user_id})

    def is_user_in_list(self, user_id):
        return bool(self.user_collection.find_one({'user_id': user_id}))

    def add_refer_points(self, user_id: int, points: int):
        self.refer_collection.update_one(
            {'user_id': user_id},
            {'$set': {'points': points}},
            upsert=True
        )

    def get_refer_points(self, user_id: int):
        user = self.refer_collection.find_one({'user_id': user_id})
        return user.get('points') if user else 0


referdb = UserTracker()


# ==============================
#   FILE LIMIT SYSTEM
# ==============================

        

    def increment_file_limit(self, user_id: int):
        self.file_limit_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"file_count": 1}},
            upsert=True
        )

    def get_file_limit(self, user_id: int) -> int:
        user = self.file_limit_collection.find_one({"user_id": user_id})
        return user.get("file_count", 0) if user else 0

    def reset_file_limit(self, user_id: int):
        self.file_limit_collection.update_one(
            {"user_id": user_id},
            {"$set": {"file_count": 0}},
            upsert=True
        )

    def reset_all_file_limits(self):
        self.file_limit_collection.update_many(
            {},
            {"$set": {"file_count": 0}}
        )

    def get_all_file_limits(self) -> list:
        return list(self.file_limit_collection.find({}))


filelimitdb = UserTracker()
