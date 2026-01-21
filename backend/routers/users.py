# backend/routers/users.py
from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from backend.database import users_collection
from backend.models import UserResponse, UserUpdate
from backend.routers.auth import get_current_user, hash_password

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def get_all_users():
    users = list(users_collection.find({}, {"password": 0}))
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=user["role"],
            avatar_url=user.get("avatar_url"),
            created_at=user["created_at"]
        )
        for user in users
    ]

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile (avatar, password)"""
    update_data = {}
    
    if payload.avatar_url is not None:
        update_data["avatar_url"] = payload.avatar_url
        
    if payload.password:
        update_data["password"] = hash_password(payload.password)
        
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
        
    users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": update_data}
    )
    
    # Fetch updated user
    updated_user = users_collection.find_one({"_id": ObjectId(current_user["id"])})
    
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        avatar_url=updated_user.get("avatar_url"),
        created_at=updated_user["created_at"]
    )
