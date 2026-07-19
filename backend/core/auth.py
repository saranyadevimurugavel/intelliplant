"""
RBAC — Role-Based Access Control
Roles: admin, engineer, technician, compliance_officer, viewer
"""
import hashlib
import hmac
import json
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "admin":             {"documents": ["read","write","delete"], "copilot": ["read","write"], "maintenance": ["read","write"], "compliance": ["read","write"], "lessons": ["read","write"], "users": ["read","write"]},
    "engineer":          {"documents": ["read","write"],          "copilot": ["read","write"], "maintenance": ["read","write"], "compliance": ["read"],         "lessons": ["read","write"], "users": []},
    "technician":        {"documents": ["read"],                  "copilot": ["read","write"], "maintenance": ["read"],         "compliance": [],               "lessons": ["read"],         "users": []},
    "compliance_officer":{"documents": ["read"],                  "copilot": ["read","write"], "maintenance": ["read"],         "compliance": ["read","write"],  "lessons": ["read"],         "users": []},
    "viewer":            {"documents": ["read"],                  "copilot": ["read","write"], "maintenance": ["read"],         "compliance": ["read"],          "lessons": ["read"],         "users": []},
}


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Demo users — in production these come from a database
DEMO_USERS = {
    "admin@intelliplant.com":      {"id": "usr-001", "name": "Admin User",    "email": "admin@intelliplant.com",      "role": "admin",             "password_hash": _hash_pw("admin123"), "area": "all"},
    "engineer@intelliplant.com":   {"id": "usr-002", "name": "R. Sharma",     "email": "engineer@intelliplant.com",   "role": "engineer",          "password_hash": _hash_pw("eng123"),   "area": "CDU-Unit1"},
    "tech@intelliplant.com":       {"id": "usr-003", "name": "A. Kumar",      "email": "tech@intelliplant.com",       "role": "technician",        "password_hash": _hash_pw("tech123"),  "area": "GasPlant-Unit3"},
    "compliance@intelliplant.com": {"id": "usr-004", "name": "J. Patel",      "email": "compliance@intelliplant.com", "role": "compliance_officer","password_hash": _hash_pw("comp123"),  "area": "all"},
}


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(_hash_pw(password), hashed)


def create_token(user: dict) -> str:
    """Create a simple signed token."""
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
        "area": user["area"],
        "exp": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify token. Returns None if invalid."""
    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.b64decode(payload_b64).decode())
        if datetime.fromisoformat(payload["exp"]) < datetime.now(timezone.utc):
            return None
        return payload
    except Exception:
        return None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(email.lower())
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if credentials is None:
        return None
    return decode_token(credentials.credentials)


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.", headers={"WWW-Authenticate": "Bearer"})
    return payload


def require_role(*roles: str):
    """Dependency factory — require one of the given roles."""
    def checker(user: dict = Depends(require_auth)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Required: {', '.join(roles)}. Your role: {user['role']}")
        return user
    return checker


def has_permission(user: Optional[dict], module: str, action: str) -> bool:
    if user is None:
        return False
    return action in ROLE_PERMISSIONS.get(user.get("role", "viewer"), {}).get(module, [])
