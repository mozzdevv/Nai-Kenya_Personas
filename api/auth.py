"""
Authentication Module
JWT-based authentication for dashboard.
Simplified for Python 3.14 compatibility (plain password comparison).
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
import os
import hashlib

# Configuration
SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "nairobi-bot-dashboard-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Default credentials (override in production via env vars)
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "nairobi2024")


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None


class User(BaseModel):
    """User model."""
    username: str


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify a password (simple comparison for testing)."""
    return plain_password == stored_password


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    if username != DASHBOARD_USERNAME:
        return None
    if not verify_password(password, DASHBOARD_PASSWORD):
        return None
    return User(username=username)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify a JWT token and return token data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None
