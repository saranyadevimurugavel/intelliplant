"""Authentication API routes."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.auth import authenticate_user, create_token, require_auth, ROLE_PERMISSIONS

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict
    permissions: dict


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate and return a token."""
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(user)
    permissions = ROLE_PERMISSIONS.get(user["role"], {})

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "area": user["area"],
        },
        "permissions": permissions,
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(require_auth)):
    """Get current user profile and permissions."""
    return {
        "user": current_user,
        "permissions": ROLE_PERMISSIONS.get(current_user["role"], {}),
    }


@router.get("/users")
async def list_demo_users():
    """List demo users for the hackathon login screen."""
    return [
        {"email": "admin@intelliplant.com",      "password": "admin123", "role": "admin",             "name": "Admin User",  "description": "Full access to all modules"},
        {"email": "engineer@intelliplant.com",   "password": "eng123",   "role": "engineer",          "name": "R. Sharma",   "description": "Documents, maintenance, copilot"},
        {"email": "tech@intelliplant.com",       "password": "tech123",  "role": "technician",        "name": "A. Kumar",    "description": "Copilot and read-only access (mobile)"},
        {"email": "compliance@intelliplant.com", "password": "comp123",  "role": "compliance_officer","name": "J. Patel",    "description": "Compliance and audit package access"},
    ]
