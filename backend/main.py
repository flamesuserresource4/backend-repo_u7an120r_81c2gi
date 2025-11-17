from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from database import create_document, get_documents
from schemas import AuditSession

app = FastAPI(title="AI Audit Agent Backend")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*" if frontend_url == "*" else frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QAItem(BaseModel):
    role: str
    content: str

class CreateAuditRequest(BaseModel):
    user_id: Optional[str] = None

class AppendTurnRequest(BaseModel):
    session_id: str
    role: str
    content: str

@app.get("/")
async def root():
    return {"message": "Backend running", "backend": "ok"}

@app.get("/test")
async def test():
    # Touch DB and list collections
    try:
        docs = await get_documents("audits", {}, limit=1)
        return {
            "backend": "ok",
            "database": "ok",
            "database_url": os.getenv("DATABASE_URL", "not-set"),
            "database_name": os.getenv("DATABASE_NAME", "not-set"),
            "connection_status": "connected",
            "collections": ["audits"] if docs is not None else [],
        }
    except Exception as e:
        return {
            "backend": "ok",
            "database": "error",
            "error": str(e),
        }

@app.post("/audit/create")
async def create_audit(req: CreateAuditRequest):
    payload = AuditSession(user_id=req.user_id).model_dump(exclude_none=True)
    created = await create_document("audits", payload)
    return {"session": created}

@app.get("/audit/list")
async def list_audits(limit: int = 25):
    docs = await get_documents("audits", {}, limit=limit)
    return {"sessions": docs}

@app.post("/audit/append")
async def append_turn(data: AppendTurnRequest):
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId

    # Manual small helper since we didn't add full update helpers
    client = AsyncIOMotorClient(os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DATABASE_NAME", "vibe_db")]
    try:
        _id = ObjectId(data.session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    upd = {"$push": {"transcript": {"role": data.role, "content": data.content}}, "$set": {"updated_at": __import__("datetime").datetime.utcnow()}}
    res = await db["audits"].update_one({"_id": _id}, upd)
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    doc = await db["audits"].find_one({"_id": _id})
    doc["_id"] = str(doc["_id"])  # jsonify
    return {"session": doc}
