# backend/routers/tasks.py
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
import shutil
import os
import uuid
from datetime import datetime
from bson import ObjectId
from typing import List

from backend.database import tasks_collection, boards_collection, comments_collection, users_collection, attachments_collection
from backend.models import TaskResponse, TaskStatus, UserRole, TaskStatusUpdate, CommentCreate, CommentResponse, AttachmentResponse
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

# -----------------------
# Board Access (All Authenticated Users)
# -----------------------
@router.get("/my-boards")
def get_my_boards(current_user: dict = Depends(get_current_user)):
    """Get all boards the current user has access to"""
    try:
        _role = _normalize_role(current_user.get("role", ""))
        print(f"DEBUG: User role: {_role}, ID: {current_user['id']}")

        if _role == UserRole.ADMIN.value:
            boards = list(boards_collection.find())
        else:
            boards = list(boards_collection.find({"member_ids": current_user["id"]}))
        
        print(f"DEBUG: Found {len(boards)} boards")

        return [
            {
                "id": str(board["_id"]),
                "name": board.get("name", "Untitled Board"),
                "description": board.get("description"),
                "team_id": board.get("team_id", ""),
                "member_count": len(board.get("member_ids", [])),
                "created_at": board.get("created_at", datetime.min)
            }
            for board in boards
        ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in get_my_boards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}", response_model=TaskResponse)
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
@router.put("/{task_id}/status")
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
        "name": board.get("name", "Untitled Board"),
        "description": board.get("description"),
        "team_id": board.get("team_id", ""),
        "member_ids": board.get("member_ids", []),
        "created_by": board.get("created_by", ""),
        "created_at": board.get("created_at", datetime.min),
        "stats": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks
        }
    }

# -----------------------
# Comments Endpoints
# -----------------------
@router.post("/{task_id}/comments", response_model=CommentResponse)
def create_comment(
    task_id: str,
    payload: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a comment to a task"""
    # Verify task exists
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    comment_doc = {
        "task_id": task_id,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "avatar_url": current_user.get("avatar_url"),
        "content": payload.content,
        "created_at": datetime.utcnow()
    }
    
    result = comments_collection.insert_one(comment_doc)
    
    # Log activity
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="commented_on_task",
        entity_type="task",
        entity_id=task_id,
        details="Added a comment"
    )
    
    return CommentResponse(
        id=str(result.inserted_id),
        task_id=comment_doc["task_id"],
        user_id=comment_doc["user_id"],
        username=comment_doc["username"],
        avatar_url=comment_doc.get("avatar_url"),
        content=comment_doc["content"],
        created_at=comment_doc["created_at"]
    )

@router.get("/{task_id}/comments", response_model=List[CommentResponse])
def get_task_comments(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all comments for a task"""
    # Verify task exists
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
        
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    comments = list(comments_collection.find({"task_id": task_id}).sort("created_at", -1))
    
    # Enrich with latest user info (avatar) if needed, but for now use stored snapshot
    # Ideally should join with users mainly for avatar updates, but snapshot is faster
    
    return [
        CommentResponse(
            id=str(c["_id"]),
            task_id=c["task_id"],
            user_id=c["user_id"],
            username=c["username"],
            avatar_url=c.get("avatar_url"),
            content=c["content"],
            created_at=c["created_at"]
        ) for c in comments
    ]

@router.delete("/{task_id}/comments/{comment_id}")
def delete_comment(
    task_id: str,
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a comment (Author or Admin only)"""
    print(f"DEBUG: Attempting to delete comment {comment_id} for task {task_id}")
    
    # Verify task exists
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        print("DEBUG: Task not found")
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify board access
    verify_board_access(task["board_id"], current_user)

    comment = comments_collection.find_one({
        "_id": ObjectId(comment_id),
        "task_id": task_id
    })
    
    if not comment:
        print("DEBUG: Comment not found")
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check permissions: Admin or Author
    _role = _normalize_role(current_user.get("role", ""))
    print(f"DEBUG: User role: {_role}, Comment Author: {comment['user_id']}, Current User: {current_user['id']}")

    if _role != UserRole.ADMIN.value and comment["user_id"] != current_user["id"]:
        print("DEBUG: Permission denied")
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own comments"
        )
    
    comments_collection.delete_one({"_id": ObjectId(comment_id)})
    print("DEBUG: Comment deleted successfully")
    
    return {"message": "Comment deleted successfully"}

# -----------------------
# Attachment Endpoints
# -----------------------
@router.post("/{task_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    task_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file attachment to a task"""
    # Verify task exists
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/{unique_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    static_path = f"/static/uploads/{unique_filename}"
    
    attachment_doc = {
        "task_id": task_id,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "filename": file.filename,
        "file_path": static_path,
        "file_type": file.content_type,
        "file_size": os.path.getsize(file_path),
        "created_at": datetime.utcnow()
    }
    
    result = attachments_collection.insert_one(attachment_doc)
    
    # Log activity
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="uploaded_attachment",
        entity_type="task",
        entity_id=task_id,
        details=f"Uploaded {file.filename}"
    )
    
    return AttachmentResponse(
        id=str(result.inserted_id),
        task_id=attachment_doc["task_id"],
        user_id=attachment_doc["user_id"],
        username=attachment_doc["username"],
        filename=attachment_doc["filename"],
        file_path=attachment_doc["file_path"],
        file_type=attachment_doc["file_type"],
        file_size=attachment_doc["file_size"],
        created_at=attachment_doc["created_at"]
    )

@router.get("/{task_id}/attachments", response_model=List[AttachmentResponse])
def get_task_attachments(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all attachments for a task"""
    # Verify task exists
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Verify board access
    verify_board_access(task["board_id"], current_user)
    
    attachments = list(attachments_collection.find({"task_id": task_id}).sort("created_at", -1))
    
    return [
        AttachmentResponse(
            id=str(a["_id"]),
            task_id=a["task_id"],
            user_id=a["user_id"],
            username=a["username"],
            filename=a["filename"],
            file_path=a["file_path"],
            file_type=a["file_type"],
            file_size=a["file_size"],
            created_at=a["created_at"]
        ) for a in attachments
    ]