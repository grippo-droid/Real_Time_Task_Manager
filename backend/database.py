import os
from typing import Any, Dict, List
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables from .env
load_dotenv()

# MongoDB URI and DB name
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "real_time_task_manager")

# -----------------------
# In-memory mock collection (fallback when MongoDB is unreachable)
# -----------------------
class _InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class _DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count

class _MockCollection:
    def __init__(self):
        self._docs: Dict[Any, Dict[str, Any]] = {}

    def _matches(self, doc: Dict[str, Any], flt: Dict[str, Any]) -> bool:
        if not flt:
            return True
        for k, v in flt.items():
            if k not in doc:
                return False
            dv = doc[k]
            # Support membership check for list fields (e.g., member_ids)
            if isinstance(dv, list):
                if v not in dv:
                    return False
            else:
                if dv != v:
                    return False
        return True

    def insert_one(self, doc: Dict[str, Any]):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self._docs[doc["_id"]] = doc
        return _InsertResult(doc["_id"])

    def find_one(self, flt: Dict[str, Any], projection: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
        for doc in self._docs.values():
            if self._matches(doc, flt):
                # Basic projection support: if projection excludes fields (0), remove them
                if projection:
                    ret_doc = doc.copy()
                    for k, v in projection.items():
                        if v == 0 and k in ret_doc:
                            del ret_doc[k]
                    return ret_doc
                return doc
        return None

    def find(self, flt: Dict[str, Any] | None = None, projection: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        flt = flt or {}
        results = [doc for doc in self._docs.values() if self._matches(doc, flt)]
        
        # Apply projection if provided
        if projection:
            clean_results = []
            for doc in results:
                new_doc = doc.copy()
                for k, v in projection.items():
                    if v == 0 and k in new_doc:
                        del new_doc[k]
                clean_results.append(new_doc)
            return clean_results
            
        return results

    def update_one(self, flt: Dict[str, Any], update: Dict[str, Any]):
        # Only support {$set: {...}}
        doc = self.find_one(flt)
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        return doc

    def delete_one(self, flt: Dict[str, Any]):
        doc = self.find_one(flt)
        if doc:
            del self._docs[doc["_id"]]
            return _DeleteResult(1)
        return _DeleteResult(0)

    def delete_many(self, flt: Dict[str, Any]):
        to_delete = [doc_id for doc_id, doc in self._docs.items() if self._matches(doc, flt)]
        for doc_id in to_delete:
            del self._docs[doc_id]
        return _DeleteResult(len(to_delete))

    def count_documents(self, flt: Dict[str, Any]):
        return len(self.find(flt))

# -----------------------
# Try real MongoDB first, fallback to in-memory mock
# -----------------------
use_mock = False
client = None
try:
    if not MONGO_URI:
        raise Exception("MONGO_URI is not set")
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client[DB_NAME]
    # Test connection
    client.admin.command('ping')
    print("[SUCCESS] Connected to MongoDB successfully!")
except Exception as e:
    print("[ERROR] MongoDB connection failed:", e)
    print("[WARNING] Using in-memory mock database for development.")
    use_mock = True
    db = None

# Collections
if use_mock:
    users_collection = _MockCollection()
    teams_collection = _MockCollection()
    boards_collection = _MockCollection()
    tasks_collection = _MockCollection()
    chats_collection = _MockCollection()
    history_collection = _MockCollection()
    activity_logs_collection = _MockCollection()
    comments_collection = _MockCollection()
    attachments_collection = _MockCollection()
else:
    users_collection = db["users"]
    teams_collection = db["teams"]
    boards_collection = db["boards"]
    tasks_collection = db["tasks"]
    chats_collection = db["chats"]
    history_collection = db["history"]
    history_collection = db["history"]
    activity_logs_collection = db["activity_logs"]
    comments_collection = db["comments"]
    attachments_collection = db["attachments"]
