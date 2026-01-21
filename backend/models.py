# backend/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# -----------------------
# Enums
# -----------------------
class UserRole(str, Enum):
    ADMIN = "admin"
    TEAM_MANAGER = "team_manager"
    TEAM_MEMBER = "team_member"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# -----------------------
# User Models
# -----------------------
class SignupModel(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    role: UserRole = UserRole.TEAM_MEMBER  # Default role

class LoginModel(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# -----------------------
# Team Models
# -----------------------
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime

# -----------------------
# Board Models
# -----------------------
class BoardCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    team_id: str
    member_ids: List[str] = []  # User IDs who can access this board

class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    member_ids: Optional[List[str]] = None

class BoardResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    team_id: str
    member_ids: List[str]
    created_by: str
    created_at: datetime

# -----------------------
# Task Models
# -----------------------
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    board_id: str
    assigned_to: Optional[str] = None  # User ID
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    board_id: str
    assigned_to: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime

# -----------------------
# Comment Models
# -----------------------
class CommentCreate(BaseModel):
    task_id: str
    content: str = Field(..., min_length=1, max_length=1000)

class CommentResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime

# -----------------------
# Chat Message Models
# -----------------------
class ChatMessage(BaseModel):
    board_id: str
    user_id: str
    username: str
    message: str
    timestamp: datetime

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class UserRoleUpdate(BaseModel):
    role: UserRole

class TaskAssignPayload(BaseModel):
    user_id: str

# -----------------------
# Activity Log Models
# -----------------------
class ActivityLog(BaseModel):
    user_id: str
    username: str
    action: str  # e.g., "created_task", "moved_task", "deleted_board"
    entity_type: str  # e.g., "task", "board", "team"
    entity_id: str
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ActivityLogResponse(ActivityLog):
    id: str