from pymongo import MongoClient
from info import DATABASE_URI

class SiliconDatabase:
    def __init__(self, uri: str, db_name: str):
        client = MongoClient(uri)
        mydb = client[db_name]
        self.silicon_col = mydb.silicon_users
        self.user_collection = mydb["referusers"]
        self.refer_collection = mydb["refers"]
        self.stg = mydb["bot_settings"]
        self.file_limit_collection = mydb["file_limits"]  

    def update_bot_sttgs(self, var, val):
        if not self.stg.find_one({}):
            self.stg.insert_one({var: val})
        self.stg.update_one({}, {'$set': {var: val}})

    def get_bot_sttgs(self):
        return self.stg.find_one({})

    def add_user(self, user_id):
        if not self.is_silicon_user_in_list(user_id):
            self.user_collection.insert_one({'user_id': user_id})

    def remove_user(self, user_id):
        self.user_collection.delete_one({'user_id': user_id})

    def is_silicon_user_in_list(self, user_id):
        return bool(self.user_collection.find_one({'user_id': user_id}))

    def add_refer_points(self, user_id: int, points: int):
        self.refer_collection.update_one(
            {'user_id': user_id},
            {'$set': {'points': points}},
            upsert=True
        )

    def get_silicon_refer_points(self, user_id: int):
        user = self.refer_collection.find_one({'user_id': user_id})
        return user.get('points') if user else 0

    def update_silicon_messages(self, user_id: int, message_text: str):
        if self.silicon_col.find_one({"user_id": user_id, "silicon_messages.text": message_text}):
            self.silicon_col.update_one(
                {"user_id": user_id, "silicon_messages.text": message_text},
                {"$inc": {"silicon_messages.$.count": 1}}
            )
        else:
            self.silicon_col.update_one(
                {"user_id": user_id},
                {"$push": {"silicon_messages": {"text": message_text, "count": 1}}},
                upsert=True
            )

    def get_silicon_messages(self, limit: int = 30) -> list:
        results = list(self.silicon_col.aggregate([
            {"$unwind": "$silicon_messages"},
            {"$group": {"_id": "$silicon_messages.text", "count": {"$sum": "$silicon_messages.count"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]))
        return [result['_id'] for result in results]

    def delete_all_silicon_messages(self):
        self.silicon_col.delete_many({})


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
