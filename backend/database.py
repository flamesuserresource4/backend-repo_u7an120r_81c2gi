import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "vibe_db")

_client: Optional[AsyncIOMotorClient] = None
_db = None

async def get_db():
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(DATABASE_URL)
        _db = _client[DATABASE_NAME]
    return _db

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = await get_db()
    now = datetime.utcnow()
    data["created_at"] = now
    data["updated_at"] = now
    res = await db[collection_name].insert_one(data)
    inserted = await db[collection_name].find_one({"_id": res.inserted_id})
    if inserted and "_id" in inserted:
        inserted["_id"] = str(inserted["_id"])  # make JSON friendly
    return inserted or {}

async def get_documents(collection_name: str, filter_dict: Dict[str, Any] | None = None, limit: int = 50) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db[collection_name].find(filter_dict or {}).limit(limit)
    results: List[Dict[str, Any]] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # make JSON friendly
        results.append(doc)
    return results
