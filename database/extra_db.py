from pymongo import MongoClient
from info import DATABASE_URI
from database.silicon import SiliconDatabase
class Database:
    def __init__(self, uri: str, db_name: str):
        client = MongoClient(uri)
        mydb = client[db_name]
        self.file_limit_collection = mydb["file_limits"] 

    def increment_silicon_limit(self, user_id: int):
        self.file_limit_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'file_count': 1}},
            upsert=True
        )

    def silicon_file_limit(self, user_id: int) -> int:
        user = self.file_limit_collection.find_one({'user_id': user_id})
        return user.get('file_count', 0) if user else 0

    def reset_file_limit(self, user_id: int):
        self.file_limit_collection.update_one(
            {'user_id': user_id},
            {'$set': {'file_count': 0}},
            upsert=True
        )

    def reset_all_file_limits(self):
        self.file_limit_collection.update_many(
            {},
            {'$set': {'file_count': 0}}
        )

    def get_all_file_limits(self) -> list:
        return list(self.file_limit_collection.find({}))

silicondb = SiliconDatabase(DATABASE_URI, "SiliconBotz")
