"""
Simple username/password authentication system to replace Linux.do OAuth.
Supports multiple users with credentials stored in environment variables.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Optional
import hashlib
import secrets

from fastapi import Depends, HTTPException, status, Cookie, Form
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# --- Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# --- Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    is_active: bool = True

class UserInDB(User):
    hashed_password: str

# --- User Management ---
def parse_auth_users() -> Dict[str, str]:
    """
    Parse AUTH_USERS environment variable.
    Format: username1:password1,username2:password2,username3:password3
    Returns dict of username -> hashed_password
    """
    users = {}
    auth_users = getattr(settings, 'AUTH_USERS', '')
    
    if not auth_users:
        # Default user if no AUTH_USERS is set
        default_password = get_password_hash("admin123")
        users["admin"] = default_password
        return users
    
    try:
        for user_pair in auth_users.split(','):
            if ':' in user_pair:
                username, password = user_pair.strip().split(':', 1)
                users[username.strip()] = get_password_hash(password.strip())
    except Exception as e:
        # Fallback to default user if parsing fails
        default_password = get_password_hash("admin123")
        users["admin"] = default_password
    
    return users

# Load users from environment
USERS_DB = parse_auth_users()

# --- Core Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """Get user from the users database."""
    if username in USERS_DB:
        return UserInDB(
            username=username,
            hashed_password=USERS_DB[username],
            is_active=True
        )
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode JWT access token and return payload."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

# --- FastAPI Dependencies ---
async def get_current_user(token: Annotated[str | None, Cookie()] = None) -> dict:
    """
    Get current user from JWT token in cookie.
    Returns user info dict for compatibility with existing code.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Verify user still exists
        user = get_user(username)
        if user is None:
            raise credentials_exception
        
        # Return user info in the same format as the old OAuth system
        return {
            "username": username,
            "id": username,  # Use username as ID for simplicity
            "name": username,
            "trust_level": 1,  # Default trust level
            "is_active": user.is_active
        }
    except JWTError:
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- Authentication Routes ---
async def login_for_access_token(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
) -> Token:
    """Authenticate user and return access token."""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# --- Utility Functions ---
def reload_users():
    """Reload users from environment variables (for runtime updates)."""
    global USERS_DB
    USERS_DB = parse_auth_users()

def add_user(username: str, password: str) -> bool:
    """Add a new user (runtime only, not persistent)."""
    if username in USERS_DB:
        return False
    USERS_DB[username] = get_password_hash(password)
    return True

def remove_user(username: str) -> bool:
    """Remove a user (runtime only, not persistent)."""
    if username in USERS_DB:
        del USERS_DB[username]
        return True
    return False

def list_users() -> list:
    """List all usernames."""
    return list(USERS_DB.keys())
