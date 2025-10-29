"""
Role-Based Access Control for EnvCLI teams.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from .config import CONFIG_DIR

RBAC_FILE = CONFIG_DIR / "rbac.json"

class Role(Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class Permission(Enum):
    """Available permissions."""
    READ_PROFILE = "read_profile"
    WRITE_PROFILE = "write_profile"
    DELETE_PROFILE = "delete_profile"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT = "view_audit"
    MANAGE_POLICIES = "manage_policies"
    SYNC_REMOTE = "sync_remote"
    MANAGE_HOOKS = "manage_hooks"

class RBACManager:
    """Manage role-based access control."""

    def __init__(self):
        self.rbac_data = self._load_rbac()

    def _load_rbac(self) -> Dict[str, Any]:
        """Load RBAC configuration."""
        if RBAC_FILE.exists():
            with open(RBAC_FILE, 'r') as f:
                return json.load(f)
        return {
            "enabled": False,
            "users": {},
            "role_permissions": self._get_default_permissions(),
            "audit_log": []
        }

    def _save_rbac(self):
        """Save RBAC configuration."""
        RBAC_FILE.parent.mkdir(exist_ok=True)
        with open(RBAC_FILE, 'w') as f:
            json.dump(self.rbac_data, f, indent=2)

    def _get_default_permissions(self) -> Dict[str, List[str]]:
        """Get default role permissions."""
        return {
            "admin": [
                "read_profile", "write_profile", "delete_profile",
                "manage_users", "view_audit", "manage_policies",
                "sync_remote", "manage_hooks"
            ],
            "member": [
                "read_profile", "write_profile", "sync_remote"
            ],
            "guest": [
                "read_profile"
            ]
        }

    def enable_rbac(self):
        """Enable RBAC system."""
        self.rbac_data["enabled"] = True
        self._save_rbac()

    def disable_rbac(self):
        """Disable RBAC system."""
        self.rbac_data["enabled"] = False
        self._save_rbac()

    def add_user(self, username: str, role: Role, added_by: str):
        """Add a user with a specific role."""
        if not self.rbac_data["enabled"]:
            return

        self.rbac_data["users"][username] = {
            "role": role.value,
            "added_by": added_by,
            "added_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
        self._save_rbac()
        self._audit_log("user_added", {"username": username, "role": role.value}, added_by)

    def remove_user(self, username: str, removed_by: str):
        """Remove a user."""
        if username in self.rbac_data["users"]:
            del self.rbac_data["users"][username]
            self._save_rbac()
            self._audit_log("user_removed", {"username": username}, removed_by)

    def change_user_role(self, username: str, new_role: Role, changed_by: str):
        """Change a user's role."""
        if username in self.rbac_data["users"]:
            old_role = self.rbac_data["users"][username]["role"]
            self.rbac_data["users"][username]["role"] = new_role.value
            self.rbac_data["users"][username]["role_changed_at"] = datetime.now().isoformat()
            self.rbac_data["users"][username]["role_changed_by"] = changed_by
            self._save_rbac()
            self._audit_log("role_changed", {
                "username": username,
                "old_role": old_role,
                "new_role": new_role.value
            }, changed_by)

    def check_permission(self, username: str, permission: Permission,
                        resource: Optional[str] = None) -> bool:
        """Check if a user has a specific permission."""
        if not self.rbac_data["enabled"]:
            return True  # Allow all if RBAC disabled

        if username not in self.rbac_data["users"]:
            return False

        user_role = self.rbac_data["users"][username]["role"]
        role_permissions = self.rbac_data["role_permissions"].get(user_role, [])

        # Update last active
        self.rbac_data["users"][username]["last_active"] = datetime.now().isoformat()
        self._save_rbac()

        return permission.value in role_permissions

    def authorize_operation(self, username: str, operation: str,
                          resource: Optional[str] = None) -> Dict[str, Any]:
        """Authorize an operation and return result."""
        # Map operations to permissions
        operation_permissions = {
            "read_profile": Permission.READ_PROFILE,
            "write_profile": Permission.WRITE_PROFILE,
            "delete_profile": Permission.DELETE_PROFILE,
            "manage_users": Permission.MANAGE_USERS,
            "view_audit": Permission.VIEW_AUDIT,
            "manage_policies": Permission.MANAGE_POLICIES,
            "sync_remote": Permission.SYNC_REMOTE,
            "manage_hooks": Permission.MANAGE_HOOKS
        }

        permission = operation_permissions.get(operation)
        if not permission:
            return {"authorized": False, "reason": f"Unknown operation: {operation}"}

        authorized = self.check_permission(username, permission, resource)

        result = {
            "authorized": authorized,
            "operation": operation,
            "username": username,
            "resource": resource,
            "timestamp": datetime.now().isoformat()
        }

        if not authorized:
            result["reason"] = "Insufficient permissions"
            self._audit_log("access_denied", result, "system")

        return result

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a user."""
        return self.rbac_data["users"].get(username)

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users with their roles."""
        users = []
        for username, info in self.rbac_data["users"].items():
            user_info = info.copy()
            user_info["username"] = username
            users.append(user_info)
        return users

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        return self.rbac_data["audit_log"][-limit:]

    def _audit_log(self, action: str, details: Dict[str, Any], performed_by: str):
        """Add an entry to the audit log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "performed_by": performed_by,
            "details": details
        }
        self.rbac_data["audit_log"].append(entry)

        # Keep only last 1000 entries
        self.rbac_data["audit_log"] = self.rbac_data["audit_log"][-1000:]
        self._save_rbac()

    def customize_role_permissions(self, role: Role, permissions: List[str]):
        """Customize permissions for a role."""
        self.rbac_data["role_permissions"][role.value] = permissions
        self._save_rbac()
        self._audit_log("role_permissions_changed", {
            "role": role.value,
            "permissions": permissions
        }, "system")

    def get_role_permissions(self, role: Role) -> List[str]:
        """Get permissions for a role."""
        return self.rbac_data["role_permissions"].get(role.value, [])

    def is_enabled(self) -> bool:
        """Check if RBAC is enabled."""
        return self.rbac_data.get("enabled", False)

# Global RBAC manager instance
rbac_manager = RBACManager()

def require_permission(permission: Permission):
    """Decorator to require a permission for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not rbac_manager.is_enabled():
                return func(*args, **kwargs)

            # Get current user (this would need to be implemented based on your auth system)
            current_user = kwargs.get("current_user") or "unknown"

            if rbac_manager.check_permission(current_user, permission):
                return func(*args, **kwargs)
            else:
                raise PermissionError(f"Permission denied: {permission.value}")
        return wrapper
    return decorator
