# backend/routers/users.py
from fastapi import APIRouter
from backend.database import users_collection

router = APIRouter()

@router.get("/")
async def get_all_users():
    return list(users_collection.find({}, {"password": 0}))
