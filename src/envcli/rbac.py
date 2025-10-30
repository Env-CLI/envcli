"""
Role-Based Access Control for EnvCLI teams.
"""

import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from .config import CONFIG_DIR

RBAC_FILE = CONFIG_DIR / "rbac.json"
SESSION_FILE = CONFIG_DIR / "session.json"

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
        self.session_data = self._load_session()

    def _load_rbac(self) -> Dict[str, Any]:
        """Load RBAC configuration."""
        if RBAC_FILE.exists():
            try:
                with open(RBAC_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                pass
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

    def _load_session(self) -> Dict[str, Any]:
        """Load session data."""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                pass
        return {"current_user": None, "login_time": None}

    def _save_session(self):
        """Save session data."""
        SESSION_FILE.parent.mkdir(exist_ok=True)
        with open(SESSION_FILE, 'w') as f:
            json.dump(self.session_data, f, indent=2)

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

    def login(self, username: str, password: Optional[str] = None) -> bool:
        """Log in a user. If a password is set for the user, it must be provided and valid."""
        if not self.rbac_data.get("enabled", False):
            return False

        user = self.rbac_data.get("users", {}).get(username)
        if not user:
            return False

        # Enforce password if configured for the user
        password_record = user.get("password")
        if password_record is not None:
            if not password:
                return False
            if not self._verify_password(password, password_record):
                return False
        else:
            # If no password is set for the user, deny login for security
            return False

        self.session_data["current_user"] = username
        self.session_data["login_time"] = datetime.now().isoformat()
        self._save_session()

        # Update last active time
        self.rbac_data["users"][username]["last_active"] = datetime.now().isoformat()
        self._save_rbac()

        self._audit_log("user_login", {"username": username}, username)
        return True

    def logout(self) -> bool:
        """Log out current user."""
        if not self.session_data.get("current_user"):
            return False

        username = self.session_data["current_user"]
        self._audit_log("user_logout", {"username": username}, username)

        self.session_data["current_user"] = None
        self.session_data["login_time"] = None
        self._save_session()
        return True

    def _hash_password(self, password: str, salt_b64: Optional[str] = None) -> Dict[str, Any]:
        """Create a password hash with scrypt, falling back to PBKDF2.
        Returns a dict with 'algo', 'salt', 'hash' and parameters.
        """
        if salt_b64:
            salt = base64.b64decode(salt_b64)
        else:
            salt = secrets.token_bytes(16)
        # Try scrypt first
        try:
            params = {"n": 2**14, "r": 8, "p": 1}
            key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=params["n"], r=params["r"], p=params["p"], dklen=32)
            return {
                "algo": "scrypt",
                "salt": base64.b64encode(salt).decode("ascii"),
                "hash": base64.b64encode(key).decode("ascii"),
                **params,
            }
        except Exception:
            # Fallback to PBKDF2-HMAC-SHA256
            iterations = 200_000
            key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
            return {
                "algo": "pbkdf2_sha256",
                "salt": base64.b64encode(salt).decode("ascii"),
                "hash": base64.b64encode(key).decode("ascii"),
                "iterations": iterations,
            }

    def _verify_password(self, password: str, record: Dict[str, Any]) -> bool:
        """Verify a password against a stored hash record (scrypt or PBKDF2)."""
        try:
            algo = record.get("algo", "scrypt")
            salt_b64 = record.get("salt")
            expected_b64 = record.get("hash")
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(expected_b64)
            if algo == "scrypt":
                n = int(record.get("n", 2**14))
                r = int(record.get("r", 8))
                p = int(record.get("p", 1))
                actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32)
            elif algo == "pbkdf2_sha256":
                iterations = int(record.get("iterations", 200_000))
                actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
            else:
                return False
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False

    def get_current_user(self) -> Optional[str]:
        """Get currently logged in user."""
        return self.session_data.get("current_user")

    def is_logged_in(self) -> bool:
        """Check if a user is logged in."""
        return self.session_data.get("current_user") is not None

    def add_user(self, username: str, role: Role, added_by: str, password: Optional[str] = None):
        """Add a user with a specific role. Optionally set an initial password."""
        if not self.rbac_data["enabled"]:
            return

        user_record: Dict[str, Any] = {
            "role": role.value,
            "added_by": added_by,
            "added_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
        }
        if password:
            user_record["password"] = self._hash_password(password)

        self.rbac_data["users"][username] = user_record
        self._save_rbac()
        self._audit_log("user_added", {"username": username, "role": role.value}, added_by)

    def remove_user(self, username: str, removed_by: str):
        """Remove a user."""
        if username in self.rbac_data["users"]:
            del self.rbac_data["users"][username]
            self._save_rbac()
            self._audit_log("user_removed", {"username": username}, removed_by)

    def set_user_password(self, username: str, new_password: str, set_by: str) -> bool:
        """Set or reset a user's password (admin operation)."""
        user = self.rbac_data.get("users", {}).get(username)
        if not user:
            return False
        user["password"] = self._hash_password(new_password)
        user["password_set_at"] = datetime.now().isoformat()
        user["password_set_by"] = set_by
        self._save_rbac()
        self._audit_log("password_set", {"username": username}, set_by)
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user's own password after verifying the old one."""
        user = self.rbac_data.get("users", {}).get(username)
        if not user:
            return False
        record = user.get("password")
        if not record or not self._verify_password(old_password, record):
            return False
        user["password"] = self._hash_password(new_password)
        user["password_changed_at"] = datetime.now().isoformat()
        self._save_rbac()
        self._audit_log("password_changed", {"username": username}, username)
        return True

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

    def clear_old_audit_logs(self, days: int = 30) -> int:
        """Clear audit log entries older than specified days.
        
        Args:
            days: Number of days to keep logs for (default: 30)
            
        Returns:
            Number of entries cleared
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        original_length = len(self.rbac_data["audit_log"])
        
        # Filter out old entries
        self.rbac_data["audit_log"] = [
            entry for entry in self.rbac_data["audit_log"]
            if self._is_recent(entry.get("timestamp", ""), days)
        ]
        
        cleared_count = original_length - len(self.rbac_data["audit_log"])
        
        if cleared_count > 0:
            self._save_rbac()
            self._audit_log("audit_logs_cleared", {
                "days_kept": days,
                "entries_cleared": cleared_count,
                "remaining_entries": len(self.rbac_data["audit_log"])
            }, "system")
            
        return cleared_count

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

    def reset_rbac(self) -> bool:
        """Reset RBAC system to factory defaults (deletes all users, sessions, and audit logs)."""
        try:
            # Logout current user
            self.logout()

            # Reset RBAC data to defaults
            self.rbac_data = {
                "enabled": False,
                "users": {},
                "role_permissions": self._get_default_permissions(),
                "audit_log": []
            }
            self._save_rbac()

            # Reset session data
            self.session_data = {"current_user": None, "login_time": None}
            self._save_session()

            return True
        except Exception:
            return False

# Global RBAC manager instance
rbac_manager = RBACManager()

def require_permission(permission: Permission):
    """Decorator to require a permission for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not rbac_manager.is_enabled():
                return func(*args, **kwargs)

            # Get current user from session
            current_user = rbac_manager.get_current_user()
            if not current_user:
                from rich.console import Console
                console = Console()
                console.print("[red]✗ Not logged in[/red]")
                console.print("[dim]RBAC is enabled. Please log in first:[/dim]")
                console.print("[yellow]  envcli login[/yellow]")
                console.print()
                console.print("[dim]Or set up RBAC if you haven't:[/dim]")
                console.print("[yellow]  envcli rbac quick-setup[/yellow]")
                import typer
                raise typer.Exit(1)

            if rbac_manager.check_permission(current_user, permission):
                return func(*args, **kwargs)
            else:
                from rich.console import Console
                console = Console()
                console.print(f"[red]✗ Permission denied[/red]")
                console.print(f"[dim]User '{current_user}' does not have permission: {permission.value}[/dim]")
                console.print()
                console.print("[dim]Contact your administrator to grant you the required permissions.[/dim]")
                import typer
                raise typer.Exit(1)
        return wrapper
    return decorator
