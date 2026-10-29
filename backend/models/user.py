"""
ImmunoGrid — User Model + RBAC Definitions
Defines all 13 government user roles and their permissions.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRole(str, Enum):
    """
    13 Government-Grade User Roles.
    Each role has specific permissions and dashboard access.
    """
    SUPER_ADMIN = "super_admin"
    NATIONAL_SECURITY_OFFICER = "national_security_officer"
    CITY_IT_MANAGER = "city_it_manager"
    TRAFFIC_MINISTRY = "traffic_ministry"
    HEALTH_MINISTRY = "health_ministry"
    WATER_AUTHORITY = "water_authority"
    ENERGY_MINISTRY = "energy_ministry"
    BLOCKCHAIN_AUDITOR = "blockchain_auditor"
    AI_ML_ENGINEER = "ai_ml_engineer"
    QUANTUM_ANALYST = "quantum_analyst"
    DEVOPS_ENGINEER = "devops_engineer"
    FIELD_TECHNICIAN = "field_technician"
    GOVERNMENT_AUDITOR = "government_auditor"


# ─── Role Permissions ─────────────────────────────────────────────────────────

ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        "can_view_all": True,
        "can_edit_all": True,
        "can_delete": True,
        "can_manage_users": True,
        "sectors": ["traffic", "hospital", "water", "power", "surveillance", "government"],
        "dashboards": ["command_center", "all"],
        "can_trigger_morphogenesis": True,
        "can_view_blockchain": True,
        "can_view_quantum": True,
        "can_view_ai": True,
        "can_view_infra": True,
    },
    UserRole.NATIONAL_SECURITY_OFFICER: {
        "can_view_all": True,
        "can_edit_all": False,
        "can_delete": False,
        "can_manage_users": False,
        "sectors": ["traffic", "hospital", "water", "power", "surveillance", "government"],
        "dashboards": ["command_center", "threats", "blockchain"],
        "can_trigger_morphogenesis": True,
        "can_view_blockchain": True,
        "can_view_quantum": True,
        "can_view_ai": True,
        "can_view_infra": False,
    },
    UserRole.CITY_IT_MANAGER: {
        "can_view_all": True,
        "can_edit_all": True,
        "can_delete": False,
        "can_manage_users": True,
        "sectors": ["traffic", "hospital", "water", "power", "surveillance"],
        "dashboards": ["command_center", "devices", "threats"],
        "can_trigger_morphogenesis": False,
        "can_view_blockchain": True,
        "can_view_quantum": True,
        "can_view_ai": True,
        "can_view_infra": True,
    },
    UserRole.TRAFFIC_MINISTRY: {
        "can_view_all": False,
        "sectors": ["traffic"],
        "dashboards": ["traffic_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
    },
    UserRole.HEALTH_MINISTRY: {
        "can_view_all": False,
        "sectors": ["hospital"],
        "dashboards": ["hospital_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
    },
    UserRole.WATER_AUTHORITY: {
        "can_view_all": False,
        "sectors": ["water"],
        "dashboards": ["water_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
    },
    UserRole.ENERGY_MINISTRY: {
        "can_view_all": False,
        "sectors": ["power"],
        "dashboards": ["power_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
    },
    UserRole.BLOCKCHAIN_AUDITOR: {
        "can_view_all": False,
        "sectors": [],
        "dashboards": ["blockchain_ledger"],
        "can_view_blockchain": True,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
        "read_only": True,
    },
    UserRole.AI_ML_ENGINEER: {
        "can_view_all": False,
        "sectors": [],
        "dashboards": ["ai_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": True,
        "can_view_infra": False,
    },
    UserRole.QUANTUM_ANALYST: {
        "can_view_all": False,
        "sectors": [],
        "dashboards": ["quantum_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": True,
        "can_view_ai": False,
        "can_view_infra": False,
    },
    UserRole.DEVOPS_ENGINEER: {
        "can_view_all": False,
        "sectors": [],
        "dashboards": ["devops_dashboard"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": True,
    },
    UserRole.FIELD_TECHNICIAN: {
        "can_view_all": False,
        "sectors": [],           # Assigned at login
        "dashboards": ["mobile_view"],
        "can_view_blockchain": False,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
        "mobile_only": True,
    },
    UserRole.GOVERNMENT_AUDITOR: {
        "can_view_all": True,
        "sectors": ["traffic", "hospital", "water", "power"],
        "dashboards": ["compliance_dashboard"],
        "can_view_blockchain": True,
        "can_view_quantum": False,
        "can_view_ai": False,
        "can_view_infra": False,
        "read_only": True,
    },
}


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    ministry: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    permissions: dict
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenData(BaseModel):
    user_id: str
    role: UserRole
    email: str
