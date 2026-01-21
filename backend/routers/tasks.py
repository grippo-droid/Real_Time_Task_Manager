# backend/routers/tasks.py
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from bson import ObjectId
from typing import List

from backend.database import tasks_collection, boards_collection
from backend.models import TaskResponse, TaskStatus, UserRole, TaskStatusUpdate
from backend.routers.auth import get_current_user
from backend.routers.activity import log_activity

router = APIRouter()

# Normalize role helper
def _normalize_role(role):
    if isinstance(role, UserRole):
        return role.value.lower()
    s = str(role).lower()
    if s.startswith("userrole."):
        s = s.split(".", 1)[1]
    return s

def verify_board_access(board_id: str, current_user: dict) -> dict:
    """Verify user has access to the board"""
    board = boards_collection.find_one({"_id": ObjectId(board_id)})
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # Admin has access to all boards
    _role = _normalize_role(current_user.get("role", ""))
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
# Task Viewing (All Authenticated Users)
# -----------------------
@router.get("/boards/{board_id}/tasks", response_model=List[TaskResponse])
def get_my_board_tasks(
    board_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all tasks for a board (user must be a member)"""
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

@router.get("/my-tasks", response_model=List[TaskResponse])
def get_my_tasks(current_user: dict = Depends(get_current_user)):
    """Get all tasks assigned to the current user"""
    tasks = list(tasks_collection.find({"assigned_to": current_user["id"]}))
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

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific task (user must have access to the board)"""
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    return TaskResponse(
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

# -----------------------
# Task Status Update (Team Members can update their own tasks)
# -----------------------
@router.put("/tasks/{task_id}/status")
def update_my_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Team Member: Update status of tasks assigned to them"""
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    # Team members can only update their own tasks
    # Team managers and admins can update any task
    _role = _normalize_role(current_user.get("role", ""))
    if _role == UserRole.TEAM_MEMBER.value:
        if task.get("assigned_to") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tasks assigned to you"
            )
    
    tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": payload.status, "updated_at": datetime.utcnow()}}
    )
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="updated_task_status",
        entity_type="task",
        entity_id=task_id,
        details=f"Updated status to {payload.status}"
    )
    
    return {"message": "Task status updated successfully"}

# -----------------------
# Board Access (All Authenticated Users)
# -----------------------
@router.get("/my-boards")
def get_my_boards(current_user: dict = Depends(get_current_user)):
    """Get all boards the current user has access to"""
    _role = _normalize_role(current_user.get("role", ""))
    if _role == UserRole.ADMIN.value:
        # Admin can see all boards
        boards = list(boards_collection.find())
    else:
        # Team members and managers see only their boards
        boards = list(boards_collection.find({"member_ids": current_user["id"]}))
    
    return [
        {
            "id": str(board["_id"]),
            "name": board["name"],
            "description": board.get("description"),
            "team_id": board["team_id"],
            "member_count": len(board.get("member_ids", [])),
            "created_at": board["created_at"]
        }
        for board in boards
    ]

@router.get("/boards/{board_id}")
def get_board_details(
    board_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific board"""
    board = verify_board_access(board_id, current_user)
    
    # Get task statistics for the board
    total_tasks = tasks_collection.count_documents({"board_id": board_id})
    completed_tasks = tasks_collection.count_documents({
        "board_id": board_id,
        "status": TaskStatus.COMPLETED
    })
    
    return {
        "id": str(board["_id"]),
        "name": board["name"],
        "description": board.get("description"),
        "team_id": board["team_id"],
        "member_ids": board.get("member_ids", []),
        "created_by": board["created_by"],
        "created_at": board["created_at"],
        "stats": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks
        }
    }