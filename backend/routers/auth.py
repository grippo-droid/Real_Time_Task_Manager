# backend/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
import os
from dotenv import load_dotenv

from backend.database import users_collection
from backend.models import SignupModel, LoginModel, TokenResponse, UserResponse, UserRole

load_dotenv()

router = APIRouter()

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# -----------------------
# Helper Functions
# -----------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }

def require_role(required_roles: list):
    """Dependency to check if user has required role. Supports both Enum values and plain strings."""
    def normalize_role(role):
        # Enum -> value
        if isinstance(role, UserRole):
            return role.value.lower()
        # String/other -> lowercased string; handle "UserRole.ADMIN" style
        s = str(role).lower()
        if s.startswith("userrole."):
            s = s.split(".", 1)[1]
        return s

    required_values = [normalize_role(role) for role in required_roles]

    def role_checker(current_user: dict = Depends(get_current_user)):
        current_role = normalize_role(current_user.get("role", ""))
        if current_role not in required_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_values}"
            )
        return current_user
    return role_checker

# -----------------------
# Signup Endpoint
# -----------------------
@router.post("/signup", response_model=TokenResponse)
def signup(user: SignupModel):
    # Check if email already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user document
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role.value,
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token({"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user_doc["created_at"]
        )
    )

# -----------------------
# Login Endpoint
# -----------------------
@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginModel):
    user = users_collection.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"],
            role=user["role"],
            created_at=user["created_at"]
        )
    )

# -----------------------
# Get Current User
# -----------------------
@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        created_at=datetime.utcnow()  # You might want to store this in the token
    )