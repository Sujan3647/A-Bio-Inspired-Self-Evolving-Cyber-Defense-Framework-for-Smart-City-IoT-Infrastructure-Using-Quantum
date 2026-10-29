"""
ImmunoGrid — Authentication Router
JWT-based authentication with RBAC role assignment.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from models.user import (
    LoginRequest, Token, TokenData, UserCreate,
    UserResponse, UserRole, ROLE_PERMISSIONS,
)

router = APIRouter()
security = HTTPBearer()

# ─── Password helpers (bcrypt) ────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash_password(secret: str) -> str:
    return _pwd_context.hash(secret)

def _verify_password(secret: str, hashed: str) -> bool:
    return _pwd_context.verify(secret, hashed)

# ─── JWT config (loaded from environment) ────────────────────────────────────

SECRET_KEY: str = os.environ.get(
    "JWT_SECRET_KEY",
    "immunogrid-super-secret-jwt-key-change-in-production",  # dev fallback only
)
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

# ─── Demo Users ───────────────────────────────────────────────────────────────

DEMO_USERS = {
    "admin@immunogrid.gov": {
        "id": "usr-001",
        "email": "admin@immunogrid.gov",
        "full_name": "System Administrator",
        "role": UserRole.SUPER_ADMIN,
        "hashed_password": _hash_password("Admin@123"),
        "ministry": "National Cybersecurity Authority",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "security@immunogrid.gov": {
        "id": "usr-002",
        "email": "security@immunogrid.gov",
        "full_name": "National Security Officer",
        "role": UserRole.NATIONAL_SECURITY_OFFICER,
        "hashed_password": _hash_password("Security@123"),
        "ministry": "Ministry of Interior",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "traffic@immunogrid.gov": {
        "id": "usr-003",
        "email": "traffic@immunogrid.gov",
        "full_name": "Traffic Department Head",
        "role": UserRole.TRAFFIC_MINISTRY,
        "hashed_password": _hash_password("Traffic@123"),
        "ministry": "Ministry of Transport",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "hospital@immunogrid.gov": {
        "id": "usr-004",
        "email": "hospital@immunogrid.gov",
        "full_name": "Health Ministry Security Head",
        "role": UserRole.HEALTH_MINISTRY,
        "hashed_password": _hash_password("Health@123"),
        "ministry": "Ministry of Health",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "auditor@immunogrid.gov": {
        "id": "usr-005",
        "email": "auditor@immunogrid.gov",
        "full_name": "Government Auditor",
        "role": UserRole.GOVERNMENT_AUDITOR,
        "hashed_password": _hash_password("Audit@123"),
        "ministry": "National Audit Office",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "quantum@immunogrid.gov": {
        "id": "usr-006",
        "email": "quantum@immunogrid.gov",
        "full_name": "Quantum Security Analyst",
        "role": UserRole.QUANTUM_ANALYST,
        "hashed_password": _hash_password("Quantum@123"),
        "ministry": "Quantum Security Division",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "devops@immunogrid.gov": {
        "id": "usr-007",
        "email": "devops@immunogrid.gov",
        "full_name": "DevOps Engineer",
        "role": UserRole.DEVOPS_ENGINEER,
        "hashed_password": _hash_password("DevOps@123"),
        "ministry": "IT Infrastructure Division",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "water@immunogrid.gov": {
        "id": "usr-008",
        "email": "water@immunogrid.gov",
        "full_name": "Water Authority Officer",
        "role": UserRole.WATER_AUTHORITY,
        "hashed_password": _hash_password("Water@123"),
        "ministry": "Water & Sanitation Authority",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    "energy@immunogrid.gov": {
        "id": "usr-009",
        "email": "energy@immunogrid.gov",
        "full_name": "Energy Ministry Officer",
        "role": UserRole.ENERGY_MINISTRY,
        "hashed_password": _hash_password("Energy@123"),
        "ministry": "Ministry of Energy",
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
}

# ─── Token helpers ────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        email: str = payload.get("email")
        if not user_id or not role:
            raise credentials_exception
        return {"user_id": user_id, "role": UserRole(role), "email": email}
    except JWTError:
        raise credentials_exception


def require_roles(*roles: UserRole):
    """Dependency: checks user has one of the required roles."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker

# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate a government user and return JWT tokens."""
    user = DEMO_USERS.get(request.email)

    if not user or not _verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"].value,
        "name": user["full_name"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    permissions = ROLE_PERMISSIONS.get(user["role"], {})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user["role"],
        permissions=permissions,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return current user profile and permissions."""
    email = current_user["email"]
    user = DEMO_USERS.get(email, {})
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"].value,
        "full_name": user.get("full_name", "Unknown"),
        "ministry": user.get("ministry", ""),
        "permissions": ROLE_PERMISSIONS.get(current_user["role"], {}),
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully", "user": current_user["email"]}


@router.get("/users", dependencies=[Depends(require_roles(
    UserRole.SUPER_ADMIN, UserRole.CITY_IT_MANAGER
))])
async def list_users():
    """List all users — Admin only."""
    return [
        {
            "id": u["id"],
            "email": u["email"],
            "full_name": u["full_name"],
            "role": u["role"].value,
            "ministry": u.get("ministry", ""),
            "is_active": u["is_active"],
        }
        for u in DEMO_USERS.values()
    ]
