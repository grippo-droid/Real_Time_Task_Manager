# backend/routers/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query
from datetime import datetime
from bson import ObjectId
from jose import JWTError, jwt
from typing import Dict, List
import json
import os
from dotenv import load_dotenv

from backend.database import boards_collection, users_collection
from backend.models import UserRole

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# Connection manager to handle WebSocket connections
class ConnectionManager:
    def __init__(self):
        # Store connections by board_id: {board_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, board_id: str, user_id: str):
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = {}
        self.active_connections[board_id][user_id] = websocket
    
    def disconnect(self, board_id: str, user_id: str):
        if board_id in self.active_connections:
            if user_id in self.active_connections[board_id]:
                del self.active_connections[board_id][user_id]
            # Remove board entry if no connections left
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]
    
    async def broadcast(self, board_id: str, message: dict, exclude_user: str = None):
        """Broadcast message to all users in a board except exclude_user"""
        if board_id in self.active_connections:
            disconnected_users = []
            for user_id, connection in self.active_connections[board_id].items():
                if exclude_user and user_id == exclude_user:
                    continue
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(board_id, user_id)
    
    async def send_personal_message(self, board_id: str, user_id: str, message: dict):
        """Send message to a specific user"""
        if board_id in self.active_connections:
            if user_id in self.active_connections[board_id]:
                try:
                    await self.active_connections[board_id][user_id].send_json(message)
                except Exception:
                    self.disconnect(board_id, user_id)

manager = ConnectionManager()

def verify_token(token: str) -> dict:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        print(f"[DEBUG] verify_token: user_id from payload: {user_id}")
        if user_id is None:
            return None
        
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        print(f"[DEBUG] verify_token: user found: {user is not None}")
        if user is None:
            return None
        
        return {
            "id": str(user["_id"]),
            "username": user.get("username", "Unknown"),
            "email": user.get("email", ""),
            "role": user.get("role", "team_member")
        }
    except JWTError as e:
        print(f"[DEBUG] verify_token: JWTError: {e}")
        return None
    except Exception as e:
        print(f"[DEBUG] verify_token: Exception: {e}")
        return None

def verify_board_access(board_id: str, user: dict) -> bool:
    """Check if user has access to the board"""
    try:
        print(f"[DEBUG] verify_board_access: checking access for user {user.get('username')} to board {board_id}")
        board = boards_collection.find_one({"_id": ObjectId(board_id)})
        if not board:
            print(f"[DEBUG] verify_board_access: board not found")
            return False
        
        # Normalize role to handle enum/string representations
        _role = str(user.get("role", "")).lower()
        if _role.startswith("userrole."):
            _role = _role.split(".", 1)[1]
        
        print(f"[DEBUG] verify_board_access: user role: {_role}")

        # Admin has access to all boards
        if _role == UserRole.ADMIN.value:
            print(f"[DEBUG] verify_board_access: Access GRANTED (Admin)")
            return True
        
        # Team managers and members must be in the board's member list
        member_ids = board.get("member_ids", [])
        print(f"[DEBUG] verify_board_access: board members: {member_ids}")
        is_member = user["id"] in member_ids
        print(f"[DEBUG] verify_board_access: is_member: {is_member}")
        return is_member
    except Exception as e:
        print(f"[DEBUG] verify_board_access: Exception: {e}")
        return False

@router.websocket("/ws/{board_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    board_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat on a board
    Connect with: ws://localhost:8000/chat/ws/{board_id}?token={your_jwt_token}
    """
    print(f"[DEBUG] websocket_endpoint: New connection request for board {board_id}")
    # Verify authentication
    user = verify_token(token)
    if not user:
        print(f"[DEBUG] websocket_endpoint: Token verification failed")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Verify board access
    if not verify_board_access(board_id, user):
        print(f"[DEBUG] websocket_endpoint: Access denied")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
        return
    
    print(f"[DEBUG] websocket_endpoint: Connection accepted for user {user['username']}")
    # Connect user
    await manager.connect(websocket, board_id, user["id"])
    
    # Notify others that user joined
    join_message = {
        "type": "user_joined",
        "user_id": user["id"],
        "username": user["username"],
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(board_id, join_message, exclude_user=user["id"])
    
    # Send welcome message to the user
    welcome_message = {
        "type": "system",
        "message": f"Welcome to the board chat, {user['username']}!",
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_personal_message(board_id, user["id"], welcome_message)
    
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "chat")
                
                if message_type == "chat":
                    # Regular chat message
                    chat_message = {
                        "type": "chat",
                        "user_id": user["id"],
                        "username": user["username"],
                        "message": message_data.get("message", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Broadcast to all users in the board
                    await manager.broadcast(board_id, chat_message)
                
                elif message_type == "typing":
                    # Typing indicator
                    typing_message = {
                        "type": "typing",
                        "user_id": user["id"],
                        "username": user["username"],
                        "is_typing": message_data.get("is_typing", False)
                    }
                    await manager.broadcast(board_id, typing_message, exclude_user=user["id"])
                
                elif message_type == "task_update":
                    # Task update notification
                    task_update_message = {
                        "type": "task_update",
                        "user_id": user["id"],
                        "username": user["username"],
                        "task_id": message_data.get("task_id"),
                        "action": message_data.get("action"),  # created, updated, deleted
                        "details": message_data.get("details", {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.broadcast(board_id, task_update_message)
                
            except json.JSONDecodeError:
                # If not JSON, treat as plain text message
                chat_message = {
                    "type": "chat",
                    "user_id": user["id"],
                    "username": user["username"],
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.broadcast(board_id, chat_message)
    
    except WebSocketDisconnect:
        manager.disconnect(board_id, user["id"])
        
        # Notify others that user left
        leave_message = {
            "type": "user_left",
            "user_id": user["id"],
            "username": user["username"],
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(board_id, leave_message)

@router.get("/boards/{board_id}/online-users")
async def get_online_users(board_id: str):
    """Get list of users currently connected to a board"""
    if board_id in manager.active_connections:
        return {
            "board_id": board_id,
            "online_users": list(manager.active_connections[board_id].keys()),
            "count": len(manager.active_connections[board_id])
        }
    return {
        "board_id": board_id,
        "online_users": [],
        "count": 0
    }