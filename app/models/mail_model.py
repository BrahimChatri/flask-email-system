from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from typing import Optional, Dict, Any


class MailModel:
    def __init__(self, db_uri: str, db_name: str):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection: Collection = self.db['mails']

    def create_mail(self, mail_data: Dict[str, Any]) -> ObjectId:
        result = self.collection.insert_one(mail_data)
        return result.inserted_id

    def get_mail(self, mail_id: ObjectId) -> Optional[Dict[str, Any]]:
        mail = self.collection.find_one({"_id": mail_id})
        return mail

    def update_mail(self, mail_id: ObjectId, update_data: Dict[str, Any]) -> bool:
        result = self.collection.update_one({"_id": mail_id}, {"$set": update_data})
        return result.modified_count > 0

    def delete_mail(self, mail_id: ObjectId) -> bool:
        result = self.collection.delete_one({"_id": mail_id})
        return result.deleted_count > 0
    
    def list_mails(self) -> list:
        mails = list(self.collection.find())
        return mails
    
    def find_mail_by_subject(self, subject: str) -> Optional[Dict[str, Any]]:
        mail = self.collection.find_one({"subject": subject})
        return mail
    
    def find_mail_by_recipient(self, recipient: str) -> Optional[Dict[str, Any]]:
        mail = self.collection.find_one({"recipient": recipient})
        return mail
    
    def find_mail_by_sender(self, sender: str) -> Optional[Dict[str, Any]]:
        mail = self.collection.find_one({"sender": sender})
        return mail
    
    def find_mail_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        mail = self.collection.find_one({"date": date})
        return mail
    
