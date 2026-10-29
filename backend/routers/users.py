"""
ImmunoGrid — User Management Router
CRUD operations for government user accounts.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from routers.auth import get_current_user, require_roles, _hash_password, DEMO_USERS
from models.user import UserRole, ROLE_PERMISSIONS, UserResponse

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    ministry: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    password: str


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    ministry: Optional[str] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    ministry: str
    is_active: bool
    created_at: str


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.CITY_IT_MANAGER
    )),
):
    """List all government users — Admin only."""
    return [
        UserListResponse(
            id=u["id"],
            email=u["email"],
            full_name=u["full_name"],
            role=u["role"].value,
            ministry=u.get("ministry", ""),
            is_active=u["is_active"],
            created_at=u["created_at"].isoformat()
                       if hasattr(u["created_at"], 'isoformat')
                       else str(u["created_at"]),
        )
        for u in DEMO_USERS.values()
    ]


@router.get("/me/permissions")
async def my_permissions(current_user: dict = Depends(get_current_user)):
    """Return current user's full permission set."""
    role = current_user["role"]
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": role.value,
        "permissions": ROLE_PERMISSIONS.get(role, {}),
        "accessible_sectors": ROLE_PERMISSIONS.get(role, {}).get("sectors", []),
        "accessible_dashboards": ROLE_PERMISSIONS.get(role, {}).get("dashboards", []),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    """Create a new government user — Super Admin only."""
    if request.email in DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    new_user = {
        "id": f"usr-{uuid.uuid4().hex[:8]}",
        "email": request.email,
        "full_name": request.full_name,
        "role": request.role,
        "hashed_password": _hash_password(request.password),
        "ministry": request.ministry or "",
        "department": request.department or "",
        "employee_id": request.employee_id or "",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "created_by": current_user["email"],
    }
    DEMO_USERS[request.email] = new_user

    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "full_name": new_user["full_name"],
        "role": request.role.value,
        "created_by": current_user["email"],
        "created_at": new_user["created_at"].isoformat(),
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: dict = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.CITY_IT_MANAGER
    )),
):
    """Update a user's role or status."""
    target = next((u for u in DEMO_USERS.values() if u["id"] == user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if request.full_name is not None:
        target["full_name"] = request.full_name
    if request.role is not None:
        target["role"] = request.role
    if request.ministry is not None:
        target["ministry"] = request.ministry
    if request.is_active is not None:
        target["is_active"] = request.is_active

    return {
        "id": target["id"],
        "email": target["email"],
        "full_name": target["full_name"],
        "role": target["role"].value,
        "is_active": target["is_active"],
        "updated_by": current_user["email"],
    }


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    """Deactivate a user account — Super Admin only."""
    target = next((u for u in DEMO_USERS.values() if u["id"] == user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    target["is_active"] = False
    return {"message": f"User {target['email']} deactivated", "deactivated_by": current_user["email"]}


@router.get("/roles/all")
async def list_roles(current_user: dict = Depends(get_current_user)):
    """Return all available roles with their permissions."""
    return {
        "roles": [
            {
                "role": role.value,
                "label": role.value.replace("_", " ").title(),
                "permissions": ROLE_PERMISSIONS.get(role, {}),
            }
            for role in UserRole
        ]
    }
