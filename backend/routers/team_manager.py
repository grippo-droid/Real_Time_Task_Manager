# backend/routers/team_manager.py
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from bson import ObjectId
from typing import List

from backend.database import tasks_collection, boards_collection, users_collection
from backend.models import (
    TeamCreate, BoardCreate, BoardUpdate, TaskCreate, TaskUpdate, TaskResponse, UserRole, TaskAssignPayload
)
from backend.routers.auth import get_current_user, require_role
from backend.routers.activity import log_activity

router = APIRouter()

def verify_board_access(board_id: str, current_user: dict) -> dict:
    """Verify user has access to the board"""
    board = boards_collection.find_one({"_id": ObjectId(board_id)})
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # Admin has access to all boards
    # Normalize role to handle enum/string representations
    _role = str(current_user.get("role", "")).lower()
    if _role.startswith("userrole."):
        _role = _role.split(".", 1)[1]
    if _role == UserRole.ADMIN.value:
        return board
    
    # Team managers and members must be in the board's member list
    if current_user["id"] not in board.get("member_ids", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this board"
        )
    
    return board

# -----------------------
# Task Management (Team Manager & Admin)
# -----------------------
@router.post("/tasks", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_MANAGER]))
):
    """Team Manager/Admin: Create a new task"""
    # Verify board access
    board = verify_board_access(task.board_id, current_user)
    
    # Verify assigned user exists and has access to the board
    if task.assigned_to:
        assigned_user = users_collection.find_one({"_id": ObjectId(task.assigned_to)})
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found"
            )
        
        # Check if assigned user is a member of the board
        if task.assigned_to not in board.get("member_ids", []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user is not a member of this board"
            )
    
    task_doc = {
        "title": task.title,
        "description": task.description,
        "board_id": task.board_id,
        "assigned_to": task.assigned_to,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "created_by": current_user["id"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = tasks_collection.insert_one(task_doc)
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="created_task",
        entity_type="task",
        entity_id=str(result.inserted_id),
        details=f"Created task '{task.title}' in board"
    )
    
    return TaskResponse(
        id=str(result.inserted_id),
        title=task.title,
        description=task.description,
        board_id=task.board_id,
        assigned_to=task.assigned_to,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        created_by=current_user["id"],
        created_at=task_doc["created_at"],
        updated_at=task_doc["updated_at"]
    )

@router.get("/boards/{board_id}/tasks", response_model=List[TaskResponse])
def get_board_tasks(
    board_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_MANAGER]))
):
    """Team Manager/Admin: Get all tasks for a board"""
    # Verify board access
    verify_board_access(board_id, current_user)
    
    tasks = list(tasks_collection.find({"board_id": board_id}))
    return [
        TaskResponse(
            id=str(task["_id"]),
            title=task["title"],
            description=task.get("description"),
            board_id=task["board_id"],
            assigned_to=task.get("assigned_to"),
            status=task["status"],
            priority=task["priority"],
            due_date=task.get("due_date"),
            created_by=task["created_by"],
            created_at=task["created_at"],
            updated_at=task["updated_at"]
        )
        for task in tasks
    ]

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_MANAGER]))
):
    """Team Manager/Admin: Update a task"""
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    update_data = {"updated_at": datetime.utcnow()}
    
    if task_update.title:
        update_data["title"] = task_update.title
    if task_update.description is not None:
        update_data["description"] = task_update.description
    if task_update.status:
        update_data["status"] = task_update.status
    if task_update.priority:
        update_data["priority"] = task_update.priority
    if task_update.due_date is not None:
        update_data["due_date"] = task_update.due_date
    if task_update.assigned_to is not None:
        # Verify assigned user exists and has access
        if task_update.assigned_to:
            board = boards_collection.find_one({"_id": ObjectId(task["board_id"])})
            if task_update.assigned_to not in board.get("member_ids", []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned user is not a member of this board"
                )
        update_data["assigned_to"] = task_update.assigned_to
    
    tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": update_data}
    )
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="updated_task",
        entity_type="task",
        entity_id=task_id,
        details=f"Updated task details"
    )
    
    # Fetch updated task
    updated_task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    
    return TaskResponse(
        id=str(updated_task["_id"]),
        title=updated_task["title"],
        description=updated_task.get("description"),
        board_id=updated_task["board_id"],
        assigned_to=updated_task.get("assigned_to"),
        status=updated_task["status"],
        priority=updated_task["priority"],
        due_date=updated_task.get("due_date"),
        created_by=updated_task["created_by"],
        created_at=updated_task["created_at"],
        updated_at=updated_task["updated_at"]
    )

@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_MANAGER]))
):
    """Team Manager/Admin: Delete a task"""
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    tasks_collection.delete_one({"_id": ObjectId(task_id)})
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="deleted_task",
        entity_type="task",
        entity_id=task_id,
        details=f"Deleted task '{task['title']}'"
    )
    
    return {"message": "Task deleted successfully"}

@router.put("/tasks/{task_id}/assign")
def assign_task(
    task_id: str,
    payload: TaskAssignPayload,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_MANAGER]))
):
    """Team Manager/Admin: Assign a task to a user"""
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    board = verify_board_access(task["board_id"], current_user)
    
    # Verify user exists and has access to the board
    user_id = payload.user_id
    if user_id not in board.get("member_ids", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this board"
        )
    
    tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"assigned_to": user_id, "updated_at": datetime.utcnow()}}
    )
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="assigned_task",
        entity_type="task",
        entity_id=task_id,
        details=f"Assigned task to user {user_id}"
    )
    
    return {"message": "Task assigned successfully"}