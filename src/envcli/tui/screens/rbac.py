"""
RBAC & Policy Management Screen for EnvCLI TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button, DataTable, Input, Select, Label
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.message import Message
from ...rbac import RBACManager, Role, Permission
from ...policy_engine import PolicyEngine


class RBACScreen(Container):
    """RBAC & Policy management screen."""
    
    DEFAULT_CSS = """
    RBACScreen {
        background: $surface;
    }
    
    #rbac-header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }
    
    #rbac-content {
        height: 100%;
        overflow-y: auto;
    }
    
    .section-title {
        background: $panel;
        color: $text;
        height: 3;
        content-align: left middle;
        padding: 0 2;
        text-style: bold;
    }
    
    .rbac-status {
        height: 3;
        background: $panel;
        padding: 0 2;
        margin: 1 0;
    }
    
    .users-table {
        height: 15;
        margin: 1 2;
    }
    
    .add-user-form {
        height: auto;
        background: $panel;
        padding: 1 2;
        margin: 1 2;
    }
    
    .permissions-matrix {
        height: 15;
        margin: 1 2;
    }
    
    .policies-table {
        height: 12;
        margin: 1 2;
    }
    
    .button-row {
        height: 3;
        margin: 1 2;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.rbac_manager = RBACManager()
        self.policy_engine = PolicyEngine()
        self.current_user = "admin"  # In a real app, this would come from auth
    
    def compose(self) -> ComposeResult:
        """Compose the RBAC screen."""
        yield Static("@ RBAC & Policy Management", id="rbac-header")
        
        with VerticalScroll(id="rbac-content"):
            # RBAC Status
            yield Static("🔐 RBAC Status", classes="section-title")
            yield Container(
                Static(self._get_rbac_status(), id="rbac-status-text"),
                classes="rbac-status"
            )
            
            # Enable/Disable RBAC buttons
            with Horizontal(classes="button-row"):
                yield Button("+ Enable RBAC", id="enable-rbac-btn", variant="success")
                yield Button("❌ Disable RBAC", id="disable-rbac-btn", variant="error")
                yield Button("@ Refresh", id="refresh-rbac-btn", variant="primary")
            
            # Users Section
            yield Static("@ Users", classes="section-title")
            yield DataTable(id="users-table", classes="users-table")
            
            # Add User Form
            yield Static("+ Add User", classes="section-title")
            with Container(classes="add-user-form"):
                yield Label("Username:")
                yield Input(placeholder="Enter username", id="username-input")
                yield Label("Role:")
                yield Select(
                    [(role.value.title(), role.value) for role in Role],
                    id="role-select",
                    prompt="Select role"
                )
                with Horizontal(classes="button-row"):
                    yield Button("+ Add User", id="add-user-btn", variant="success")
                    yield Button("🗑️ Remove Selected User", id="remove-user-btn", variant="error")
                    yield Button("@ Change Role", id="change-role-btn", variant="primary")
            
            # Permissions Matrix
            yield Static("🔑 Permissions Matrix", classes="section-title")
            yield DataTable(id="permissions-table", classes="permissions-matrix")
            
            # Policies Section
            yield Static("- Active Policies", classes="section-title")
            yield DataTable(id="policies-table", classes="policies-table")
            
            with Horizontal(classes="button-row"):
                yield Button("- View All Policies", id="view-policies-btn", variant="primary")
                yield Button("O View Audit Log", id="view-audit-btn", variant="primary")
    
    def on_mount(self) -> None:
        """Initialize tables when screen is mounted."""
        self._setup_users_table()
        self._setup_permissions_table()
        self._setup_policies_table()
        self._load_users()
        self._load_permissions()
        self._load_policies()
    
    def _get_rbac_status(self) -> str:
        """Get RBAC status text."""
        enabled = self.rbac_manager.is_enabled()
        status = "+ Enabled" if enabled else "❌ Disabled"
        user_count = len(self.rbac_manager.list_users())
        return f"Status: {status} | Users: {user_count} | Current User: {self.current_user}"
    
    def _setup_users_table(self) -> None:
        """Setup users table columns."""
        table = self.query_one("#users-table", DataTable)
        table.add_columns("Username", "Role", "Added By", "Added At", "Last Active")
    
    def _setup_permissions_table(self) -> None:
        """Setup permissions matrix table."""
        table = self.query_one("#permissions-table", DataTable)
        table.add_columns("Permission", "Admin", "Member", "Guest")
    
    def _setup_policies_table(self) -> None:
        """Setup policies table columns."""
        table = self.query_one("#policies-table", DataTable)
        table.add_columns("Type", "Pattern/Convention", "Description")
    
    async def _load_users(self) -> None:
        """Load users into the table."""
        table = self.query_one("#users-table", DataTable)
        table.clear()
        
        users = self.rbac_manager.list_users()
        for user in users:
            table.add_row(
                user["username"],
                user["role"],
                user.get("added_by", "N/A"),
                user.get("added_at", "N/A")[:19],  # Truncate timestamp
                user.get("last_active", "N/A")[:19]
            )
    
    async def _load_permissions(self) -> None:
        """Load permissions matrix."""
        table = self.query_one("#permissions-table", DataTable)
        table.clear()

        # Get permissions for each role
        admin_perms = set(self.rbac_manager.get_role_permissions(Role.ADMIN))
        member_perms = set(self.rbac_manager.get_role_permissions(Role.MEMBER))
        guest_perms = set(self.rbac_manager.get_role_permissions(Role.GUEST))
        
        # Add row for each permission
        for perm in Permission:
            table.add_row(
                perm.value,
                "+" if perm.value in admin_perms else "❌",
                "+" if perm.value in member_perms else "❌",
                "+" if perm.value in guest_perms else "❌"
            )
    
    async def _load_policies(self) -> None:
        """Load active policies."""
        table = self.query_one("#policies-table", DataTable)
        table.clear()

        policies = self.policy_engine.policies
        
        # Add required keys
        for policy in policies.get("required_keys", []):
            table.add_row(
                "Required Key",
                policy["pattern"],
                policy.get("description", "N/A")
            )
        
        # Add prohibited patterns
        for policy in policies.get("prohibited_patterns", []):
            table.add_row(
                "Prohibited Pattern",
                policy["pattern"],
                policy.get("description", "N/A")
            )
        
        # Add naming conventions
        for policy in policies.get("naming_conventions", []):
            table.add_row(
                "Naming Convention",
                policy["convention"],
                policy.get("description", "N/A")
            )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "enable-rbac-btn":
            await self._enable_rbac()
        elif button_id == "disable-rbac-btn":
            await self._disable_rbac()
        elif button_id == "refresh-rbac-btn":
            await self._refresh_all()
        elif button_id == "add-user-btn":
            await self._add_user()
        elif button_id == "remove-user-btn":
            await self._remove_user()
        elif button_id == "change-role-btn":
            await self._change_role()
        elif button_id == "view-policies-btn":
            self.app.notify("Policy editor coming soon!", severity="information")
        elif button_id == "view-audit-btn":
            await self._view_audit_log()
    
    async def _enable_rbac(self) -> None:
        """Enable RBAC system."""
        self.rbac_manager.enable_rbac()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify("+ RBAC enabled", severity="information")
    
    async def _disable_rbac(self) -> None:
        """Disable RBAC system."""
        self.rbac_manager.disable_rbac()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify("❌ RBAC disabled", severity="warning")
    
    async def _refresh_all(self) -> None:
        """Refresh all data."""
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        await self._load_users()
        await self._load_permissions()
        await self._load_policies()
        self.app.notify("@ Data refreshed", severity="information")
    
    async def _add_user(self) -> None:
        """Add a new user."""
        username_input = self.query_one("#username-input", Input)
        role_select = self.query_one("#role-select", Select)
        
        username = username_input.value.strip()
        role_value = role_select.value
        
        if not username:
            self.app.notify("❌ Username is required", severity="error")
            return
        
        if role_value == Select.BLANK:
            self.app.notify("❌ Please select a role", severity="error")
            return
        
        try:
            role = Role(role_value)
            self.rbac_manager.add_user(username, role, self.current_user)
            await self._load_users()
            self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
            username_input.value = ""
            self.app.notify(f"+ User '{username}' added with role '{role.value}'", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Error adding user: {e}", severity="error")
    
    async def _remove_user(self) -> None:
        """Remove selected user."""
        table = self.query_one("#users-table", DataTable)
        if table.cursor_row is None:
            self.app.notify("❌ Please select a user to remove", severity="error")
            return
        
        row_key = table.cursor_row
        username = table.get_row(row_key)[0]
        
        self.rbac_manager.remove_user(username, self.current_user)
        await self._load_users()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify(f"+ User '{username}' removed", severity="information")
    
    async def _change_role(self) -> None:
        """Change role of selected user."""
        table = self.query_one("#users-table", DataTable)
        role_select = self.query_one("#role-select", Select)
        
        if table.cursor_row is None:
            self.app.notify("❌ Please select a user", severity="error")
            return
        
        role_value = role_select.value
        if role_value == Select.BLANK:
            self.app.notify("❌ Please select a new role", severity="error")
            return
        
        row_key = table.cursor_row
        username = table.get_row(row_key)[0]
        
        try:
            new_role = Role(role_value)
            self.rbac_manager.change_user_role(username, new_role, self.current_user)
            await self._load_users()
            self.app.notify(f"+ User '{username}' role changed to '{new_role.value}'", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Error changing role: {e}", severity="error")
    
    async def _view_audit_log(self) -> None:
        """View audit log."""
        log_entries = self.rbac_manager.get_audit_log(limit=10)
        if log_entries:
            message = "O Recent Audit Log:\n"
            for entry in log_entries[-5:]:  # Show last 5
                timestamp = entry['timestamp'][:19]
                message += f"\n{timestamp} | {entry['performed_by']} | {entry['action']}"
            self.app.notify(message, severity="information", timeout=10)
        else:
            self.app.notify("No audit log entries", severity="information")

