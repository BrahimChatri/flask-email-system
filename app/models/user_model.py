from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime


class UserModel:
    def __init__(self, db_uri: str, db_name: str):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection: Collection = self.db['users']

    def create_user(self, user_data: Dict[str, Any]) -> ObjectId:
        # Add missing fields automatically
        user_data.setdefault("user_id", str(uuid4()))
        user_data.setdefault("is_admin", False)
        user_data.setdefault("date_created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        result = self.collection.insert_one(user_data)
        return result.inserted_id

    def get_user_by_id(self, mongo_id: ObjectId) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": mongo_id})

    def get_user_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"user_id": user_id})

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"email": email})

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        result = self.collection.update_one({"user_id": user_id}, {"$set": update_data})
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        result = self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    def list_users(self) -> List[Dict[str, Any]]:
        return list(self.collection.find())
