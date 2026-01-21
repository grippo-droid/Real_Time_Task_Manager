# backend/routers/admin.py
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from bson import ObjectId
from typing import List

from backend.database import users_collection, teams_collection, boards_collection
from backend.models import (
    TeamCreate, TeamResponse, BoardCreate, BoardUpdate, BoardResponse, UserResponse, UserRole, UserRoleUpdate
)
from backend.routers.auth import get_current_user, require_role
from backend.routers.activity import log_activity

router = APIRouter()

# -----------------------
# Team Management (Admin Only)
# -----------------------
@router.post("/teams", response_model=TeamResponse)
def create_team(
    team: TeamCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Create a new team"""
    # Check if team name already exists
    if teams_collection.find_one({"name": team.name}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists"
        )
    
    team_doc = {
        "name": team.name,
        "description": team.description,
        "created_by": current_user["id"],
        "created_at": datetime.utcnow()
    }
    
    result = teams_collection.insert_one(team_doc)
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="created_team",
        entity_type="team",
        entity_id=str(result.inserted_id),
        details=f"Created team '{team.name}'"
    )
    
    return TeamResponse(
        id=str(result.inserted_id),
        name=team.name,
        description=team.description,
        created_by=current_user["id"],
        created_at=team_doc["created_at"]
    )

@router.get("/teams", response_model=List[TeamResponse])
def get_all_teams(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Get all teams"""
    teams = list(teams_collection.find())
    return [
        TeamResponse(
            id=str(team["_id"]),
            name=team["name"],
            description=team.get("description"),
            created_by=team["created_by"],
            created_at=team["created_at"]
        )
        for team in teams
    ]

@router.delete("/teams/{team_id}")
def delete_team(
    team_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Delete a team"""
    try:
        result = teams_collection.delete_one({"_id": ObjectId(team_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Also delete all boards associated with this team
        boards_collection.delete_many({"team_id": team_id})
        
        log_activity(
            user_id=current_user["id"],
            username=current_user["username"],
            action="deleted_team",
            entity_type="team",
            entity_id=team_id,
            details=f"Deleted team"
        )
        
        return {"message": "Team deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# -----------------------
# Board Management (Admin Only)
# -----------------------
@router.post("/boards", response_model=BoardResponse)
def create_board(
    board: BoardCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Create a new board and assign team members"""
    # Verify team exists
    if not teams_collection.find_one({"_id": ObjectId(board.team_id)}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Verify all member IDs exist
    for member_id in board.member_ids:
        if not users_collection.find_one({"_id": ObjectId(member_id)}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {member_id} not found"
            )
    
    # Check if board name already exists in this team
    if boards_collection.find_one({"name": board.name, "team_id": board.team_id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board name already exists in this team"
        )
    
    board_doc = {
        "name": board.name,
        "description": board.description,
        "team_id": board.team_id,
        "member_ids": board.member_ids,
        "created_by": current_user["id"],
        "created_at": datetime.utcnow()
    }
    
    result = boards_collection.insert_one(board_doc)
    
    log_activity(
        user_id=current_user["id"],
        username=current_user["username"],
        action="created_board",
        entity_type="board",
        entity_id=str(result.inserted_id),
        details=f"Created board '{board.name}'"
    )
    
    return BoardResponse(
        id=str(result.inserted_id),
        name=board.name,
        description=board.description,
        team_id=board.team_id,
        member_ids=board.member_ids,
        created_by=current_user["id"],
        created_at=board_doc["created_at"]
    )

@router.get("/boards", response_model=List[BoardResponse])
def get_all_boards(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Get all boards"""
    boards = list(boards_collection.find())
    return [
        BoardResponse(
            id=str(board["_id"]),
            name=board["name"],
            description=board.get("description"),
            team_id=board["team_id"],
            member_ids=board.get("member_ids", []),
            created_by=board["created_by"],
            created_at=board["created_at"]
        )
        for board in boards
    ]

@router.put("/boards/{board_id}", response_model=BoardResponse)
def update_board(
    board_id: str,
    board_update: BoardUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Update board details and members"""
    board = boards_collection.find_one({"_id": ObjectId(board_id)})
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    update_data = {}
    if board_update.name:
        update_data["name"] = board_update.name
    if board_update.description is not None:
        update_data["description"] = board_update.description
    if board_update.member_ids is not None:
        # Verify all member IDs exist
        for member_id in board_update.member_ids:
            if not users_collection.find_one({"_id": ObjectId(member_id)}):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {member_id} not found"
                )
        update_data["member_ids"] = board_update.member_ids
    
    if update_data:
        boards_collection.update_one(
            {"_id": ObjectId(board_id)},
            {"$set": update_data}
        )
    
    # Fetch updated board
    updated_board = boards_collection.find_one({"_id": ObjectId(board_id)})
    
    return BoardResponse(
        id=str(updated_board["_id"]),
        name=updated_board["name"],
        description=updated_board.get("description"),
        team_id=updated_board["team_id"],
        member_ids=updated_board.get("member_ids", []),
        created_by=updated_board["created_by"],
        created_at=updated_board["created_at"]
    )

@router.delete("/boards/{board_id}")
def delete_board(
    board_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Delete a board"""
    try:
        result = boards_collection.delete_one({"_id": ObjectId(board_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found"
            )
        
        log_activity(
            user_id=current_user["id"],
            username=current_user["username"],
            action="deleted_board",
            entity_type="board",
            entity_id=board_id,
            details="Deleted board"
        )

        return {"message": "Board deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# -----------------------
# User Management (Admin Only)
# -----------------------
@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Get all users"""
    users = list(users_collection.find({}, {"password": 0}))
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=user.get("role", "team_member"),
            created_at=user.get("created_at", datetime.utcnow())
        )
        for user in users
    ]

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Update user role"""
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": payload.role.value}}
    )
    
    return {"message": f"User role updated to {payload.role.value}"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Admin: Delete a user"""
    try:
        # Check if user exists
        if not users_collection.find_one({"_id": ObjectId(user_id)}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Remove user from all teams and boards
        # 1. Remove from boards' member_ids
        boards_collection.update_many(
            {},
            {"$pull": {"member_ids": user_id}}
        )
        
        # 2. Delete the user document
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )