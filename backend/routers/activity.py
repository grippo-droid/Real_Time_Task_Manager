from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..database import activity_logs_collection
from ..models import ActivityLog, ActivityLogResponse
from .auth import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter(
    tags=["activity"]
)

def log_activity(user_id: str, username: str, action: str, entity_type: str, entity_id: str, details: str = None):
    """
    Helper function to log an activity.
    """
    try:
        log_entry = {
            "user_id": user_id,
            "username": username,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "created_at": datetime.utcnow()
        }
        activity_logs_collection.insert_one(log_entry)
    except Exception as e:
        print(f"Failed to log activity: {e}")

@router.get("/", response_model=List[ActivityLogResponse])
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    """
    Get the 50 most recent activity logs.
    """
    logs = activity_logs_collection.find()
    # Sort by created_at desc in python since mock doesn't support sort
    sorted_logs = sorted(logs, key=lambda x: x["created_at"], reverse=True)[:50]
    
    response = []
    for log in sorted_logs:
        response.append(ActivityLogResponse(
            id=str(log["_id"]),
            user_id=log["user_id"],
            username=log["username"],
            action=log["action"],
            entity_type=log["entity_type"],
            entity_id=log["entity_id"],
            details=log["details"],
            created_at=log["created_at"]
        ))
    
    return response
